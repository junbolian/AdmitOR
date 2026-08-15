---
name: ShortestPathAsNetworkFlow
description: |
  Model shortest path problems as min-cost network flow with binary arc selection, then solve via specialized flow solvers or integer programming.
---

# Workflow 1 (Min-Cost Flow Solver)

## Modeling stage

### Strategy Overview
Formulate the shortest path problem as a min-cost flow with unit capacities and unit supply/demand. This leverages the integrality property of network flow problems, guaranteeing binary solutions without explicit integer variables.

### Step 1 - Define Network Structure
- Identify the set of nodes `N` and the set of directed arcs `A`.
- Define a cost parameter `c_ij` for each arc `(i,j)`. For arcs without explicit cost, assign a sufficiently large penalty (e.g., `M`) to discourage selection.
- Designate a source node `s` with supply `+1` and a sink node `t` with demand `-1`.

### Step 2 - Formulate as Unit Flow Problem
- Use continuous flow variables `x_ij` representing flow on arc `(i,j)`.
- Set arc capacities to `1` to enforce the unit flow property.
- Apply flow conservation: for each node `k` in `N \ {s, t}`, sum of inflow equals sum of outflow.
- Set supply/demand constraints: total outflow from `s` equals `1`, total inflow to `t` equals `1`.

### Formulation Template
```json
{
  "sets": {
    "N": "Set of all nodes.",
    "A": "Set of directed arcs (i,j)."
  },
  "parameters": {
    "c": {"index": "A", "description": "Cost per unit flow on arc (i,j)."},
    "s": {"description": "Source node identifier."},
    "t": {"description": "Sink node identifier."}
  },
  "decision_variables": {
    "x": {"index": "A", "domain": "Continuous, [0,1]"}
  },
  "objective": {
    "sense": "min",
    "expression": "sum_{ (i,j) in A } c[i,j] * x[i,j]"
  },
  "constraints": [
    {"name": "flow_conservation", "expression": "For k in N \\ {s, t}: sum_{ (i,k) in A } x[i,k] = sum_{ (k,j) in A } x[k,j]"},
    {"name": "source_supply", "expression": "sum_{ (s,j) in A } x[s,j] = 1"},
    {"name": "sink_demand", "expression": "sum_{ (i,t) in A } x[i,t] = 1"}
  ]
}
```

### Common Pitfalls
- Using a penalty `M` that is too low, allowing suboptimal paths through "forbidden" arcs.
- Forgetting to set arc capacities, which may allow fractional flows or flows greater than one.
- Incorrectly setting node supplies/demands (e.g., using `+1` for sink), which breaks flow balance.

## Solving stage

### Strategy Overview
Use a specialized min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) that exploits the network structure for efficiency. The solver returns integer flows due to the problem's total unimodularity.

### Step 1 - Initialize Solver and Add Arcs
- Instantiate a min-cost flow solver object.
- Add each arc `(i,j)` to the solver with `capacity=1` and `unit_cost=c_ij`.

### Step 2 - Set Node Supplies and Solve
- Set the supply for node `s` to `1`, for node `t` to `-1`, and for all other nodes to `0`.
- Call the solver's `solve()` method.
- Check the solver status (`OPTIMAL`, `INFEASIBLE`, etc.) before proceeding.

### Step 3 - Extract and Validate Path
- Retrieve the flow value for each arc. With unit capacities, optimal flows will be `0` or `1`.
- Starting from the source `s`, follow the arc with flow `1` to reconstruct the path to the sink `t`.
- Verify the total cost matches the solver's objective value.

### Code Usage
```python
# Example using OR-Tools SimpleMinCostFlow
from ortools.graph import pywrapgraph

# Initialize solver
min_cost_flow = pywrapgraph.SimpleMinCostFlow()

# Add arcs (example: arc from node u to node v with cost cost_uv)
for (u, v, cost_uv) in list_of_arcs_with_costs:
    min_cost_flow.AddArcWithCapacityAndUnitCost(u, v, 1, cost_uv)

# Set node supplies
min_cost_flow.SetNodeSupply(source_node, 1)
min_cost_flow.SetNodeSupply(sink_node, -1)
# All other nodes default to supply 0

# Solve
status = min_cost_flow.Solve()

if status == min_cost_flow.OPTIMAL:
    total_cost = min_cost_flow.OptimalCost()
    # Extract path
    path = [source_node]
    current = source_node
    while current != sink_node:
        for arc_index in range(min_cost_flow.NumArcs()):
            if (min_cost_flow.Tail(arc_index) == current and
                min_cost_flow.Flow(arc_index) > 0.5):
                current = min_cost_flow.Head(arc_index)
                path.append(current)
                break
    print(f"Optimal path: {path}, Cost: {total_cost}")
else:
    print("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Assuming the solver status is `OPTIMAL` without checking, leading to errors when extracting flows.
- Not handling the case where the solver may return `FEASIBLE` but not `OPTIMAL` if time limits are set.
- Incorrectly tracing the path by not checking flow values, which can fail if multiple arcs from the same node have flow > 0.

# Workflow 2 (Integer Programming Solver)

## Modeling stage

### Strategy Overview
Explicitly model the shortest path problem as a Binary Integer Program (BIP) with binary arc selection variables. This provides maximum flexibility and direct control, suitable for integration into larger MIP models or when using general-purpose solvers.

### Step 1 - Define Binary Selection Variables
- For each directed arc `(i,j)` in set `A`, define a binary decision variable `x_ij ∈ {0,1}`. `x_ij = 1` indicates the arc is part of the chosen path.

### Step 2 - Enforce Path Structure Constraints
- Apply flow conservation at intermediate nodes: for each node `k` (excluding source `s` and sink `t`), the sum of incoming arcs equals the sum of outgoing arcs.
- Enforce unit flow from source: exactly one arc must leave `s`.
- Enforce unit flow to sink: exactly one arc must enter `t`.
- Optionally, add constraints to prevent arcs from entering the source or leaving the sink for clarity.

### Step 3 - Handle Incomplete Cost Data
- Build a complete cost matrix. For arcs with no given cost, assign a large penalty `M` to make them undesirable.
- Ensure `M` is larger than the sum of any feasible path's cost to avoid artificial optimality.

### Formulation Template
```json
{
  "sets": {
    "N": "Set of all nodes.",
    "A": "Set of directed arcs (i,j)."
  },
  "parameters": {
    "c": {"index": "A", "description": "Cost for selecting arc (i,j). Use large M for disallowed arcs."},
    "s": {"description": "Source node identifier."},
    "t": {"description": "Sink node identifier."}
  },
  "decision_variables": {
    "x": {"index": "A", "domain": "Binary"}
  },
  "objective": {
    "sense": "min",
    "expression": "sum_{ (i,j) in A } c[i,j] * x[i,j]"
  },
  "constraints": [
    {"name": "flow_conservation_intermediate", "expression": "For k in N \\ {s, t}: sum_{ (i,k) in A } x[i,k] = sum_{ (k,j) in A } x[k,j]"},
    {"name": "source_outflow", "expression": "sum_{ (s,j) in A } x[s,j] = 1"},
    {"name": "sink_inflow", "expression": "sum_{ (i,t) in A } x[i,t] = 1"}
  ]
}
```

### Common Pitfalls
- Defining the cost matrix incompletely, leading to undefined variable coefficients during model building.
- Setting the penalty `M` too small, which can result in optimal solutions using "forbidden" arcs.
- Adding redundant constraints (e.g., `x_ij <= 1`) that unnecessarily increase model size.

## Solving stage

### Strategy Overview
Use a general-purpose MILP solver (e.g., SCIP, HiGHS via Pyomo, OR-Tools MPSolver) configured for binary integer programming. This approach is robust and allows for advanced solver settings.

### Step 1 - Build the MIP Model
- Instantiate a solver object (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Create binary variables for each arc.
- Add the objective function and all constraints to the model.

### Step 2 - Configure Solver and Solve
- Set practical limits: time limit, relative MIP gap (e.g., `0.0` for exact solution), and number of threads.
- Call the solver's `Solve()` method.
- Check the result status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).

### Step 3 - Process and Verify Solution
- If status is `OPTIMAL` or `FEASIBLE`, retrieve the objective value.
- Collect all arcs where `x_ij.solution_value() > 0.5` (tolerance for numerical issues).
- Reconstruct the path by following selected arcs from source to sink.
- Validate that the solution satisfies all flow conservation constraints.

### Code Usage
```python
# Example using OR-Tools linear solver wrapper
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    raise RuntimeError("Solver not available.")

# Create binary variables
x = {}
for (i, j) in list_of_arcs:
    x[i, j] = solver.BoolVar(f"x_{i}_{j}")

# Objective: Minimize total cost
objective = solver.Objective()
for (i, j), var in x.items():
    objective.SetCoefficient(var, cost_dict[i, j])
objective.SetMinimization()

# Flow conservation for intermediate nodes
for node in intermediate_nodes:
    constraint = solver.Constraint(0, 0)
    for (i, j) in x:
        if j == node:  # Inflow
            constraint.SetCoefficient(x[i, j], 1)
        if i == node:  # Outflow
            constraint.SetCoefficient(x[i, j], -1)

# Source outflow = 1
source_constraint = solver.Constraint(1, 1)
for (i, j) in x:
    if i == source_node:
        source_constraint.SetCoefficient(x[i, j], 1)

# Sink inflow = 1
sink_constraint = solver.Constraint(1, 1)
for (i, j) in x:
    if j == sink_node:
        sink_constraint.SetCoefficient(x[i, j], 1)

# Solve
solver.SetTimeLimit(30000)  # milliseconds
solver.EnableOutput()  # Optional: see logs
result_status = solver.Solve()

if result_status == pywraplp.Solver.OPTIMAL:
    total_cost = objective.Value()
    # Extract selected arcs
    selected_arcs = [(i, j) for (i, j), var in x.items() if var.solution_value() > 0.5]
    print(f"Optimal cost: {total_cost}")
    print(f"Selected arcs: {selected_arcs}")
elif result_status == pywraplp.Solver.FEASIBLE:
    print("Feasible solution found, but may not be optimal.")
else:
    print("No optimal or feasible solution found.")
```

### Common Pitfalls
- Not setting a time limit, potentially allowing the solver to run indefinitely on large instances.
- Forgetting to check solver status, leading to attempts to access solution values from an infeasible model.
- Using a loose MIP gap (`mip_rel_gap > 0`) when an exact optimal path is required.
