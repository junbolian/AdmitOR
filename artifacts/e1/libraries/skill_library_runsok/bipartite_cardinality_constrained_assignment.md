---
name: Bipartite Cardinality-Constrained Assignment
description: |
  Model and solve bipartite assignment problems with one-to-one matching constraints and a required total number of assignments, minimizing total cost.

---

# Workflow 1 (Min-Cost Flow Network)

## Modeling stage

### Strategy Overview
Model the assignment problem as a min-cost flow on a bipartite network. The required number of assignments is set as the flow demand, and unit capacities enforce one-to-one matching.

### Step 1 - Define Network Structure
- Identify two disjoint sets: `set_A` (source side) and `set_B` (sink side).
- Create a directed graph with nodes: source, all elements in `set_A`, all elements in `set_B`, and a sink.
- Define arcs with capacities and costs: source to `set_A` (capacity 1, cost 0), `set_A` to `set_B` (capacity 1, cost = assignment cost), `set_B` to sink (capacity 1, cost 0).

### Step 2 - Set Flow Requirements
- Set the supply at the source and demand at the sink equal to the required number of assignments `K`.
- Ensure all intermediate nodes (`set_A`, `set_B`) have zero net supply.

### Formulation Template
```json
{
  "sets": ["set_A", "set_B"],
  "parameters": ["cost[set_A][set_B]", "K"],
  "decision_variables": ["flow[arc] (integer)"],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j] * flow[i,j] for i in set_A, j in set_B )"
  },
  "constraints": [
    "flow conservation at each node",
    "capacity constraints: flow[arc] <= capacity[arc]",
    "total flow from source = K"
  ]
}
```

### Common Pitfalls
- Forgetting to scale fractional costs to integers for integer-based flow solvers, which can lead to precision loss.
- Incorrectly setting node supplies/demands, which can result in infeasibility or incorrect flow values.
- Assuming the solver returns integer flows without verifying integrality guarantees for the chosen algorithm.

## Solving stage

### Strategy Overview
Use a dedicated min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) to find the optimal flow, which directly corresponds to the optimal assignment.

### Step 1 - Build and Solve the Network
- Instantiate the min-cost flow solver.
- Add all nodes (source, `set_A`, `set_B`, sink) to the solver.
- Add arcs with corresponding capacities and scaled integer costs.
- Set the supply/demand for the source and sink nodes to `K`.
- Solve the problem.

### Step 2 - Extract and Validate the Assignment
- Retrieve the flow on each arc from `set_A` to `set_B`.
- Identify assignments where the flow is greater than zero (typically 1).
- Rescale the total cost back to the original scale if costs were scaled to integers.
- For small instances, validate optimality via brute-force enumeration to build solver confidence.

### Code Usage
```python
# build model from formulation
from ortools.graph import pywrapgraph

# Instantiate solver
min_cost_flow = pywrapgraph.SimpleMinCostFlow()

# Add nodes and arcs (example for one arc)
# Set arc from node_u to node_v with capacity and cost
min_cost_flow.AddArcWithCapacityAndUnitCost(node_u, node_v, capacity, scaled_cost)

# Set node supplies (positive for source, negative for sink)
min_cost_flow.SetNodeSupply(source_node, K)
min_cost_flow.SetNodeSupply(sink_node, -K)

# solve with status / termination checks
if min_cost_flow.Solve() == min_cost_flow.OPTIMAL:
    total_flow_cost = min_cost_flow.OptimalCost()
    # Extract assignments
    for arc in range(min_cost_flow.NumArcs()):
        if min_cost_flow.Tail(arc) in set_A_indices and min_cost_flow.Head(arc) in set_B_indices:
            if min_cost_flow.Flow(arc) > 0:
                i = node_to_A_map[min_cost_flow.Tail(arc)]
                j = node_to_B_map[min_cost_flow.Head(arc)]
                # Record assignment (i, j)
else:
    # Handle infeasible or error status
    print("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Not checking the solver status (`OPTIMAL`) before extracting results, leading to runtime errors.
- Mismatching node indices when adding arcs and setting supplies, causing an incorrect network.
- Failing to rescale the integer optimal cost back to the original cost units, misreporting the objective value.

# Workflow 2 (Integer Linear Programming)

## Modeling stage

### Strategy Overview
Formulate the problem as a Binary Integer Linear Program (BILP) with explicit binary assignment variables, one-to-one matching constraints, and a cardinality constraint on the total number of assignments.

### Step 1 - Define Variables and Parameters
- Define binary decision variable `x[i][j]` for each possible assignment between `i` in `set_A` and `j` in `set_B`.
- Define parameter `cost[i][j]` for each assignment pair.
- Define parameter `K` for the required total number of assignments.

### Step 2 - Formulate Constraints and Objective
- Add row constraints: `sum(x[i][j] for j in set_B) <= 1` for each `i` in `set_A`.
- Add column constraints: `sum(x[i][j] for i in set_A) <= 1` for each `j` in `set_B`.
- Add cardinality constraint: `sum(x[i][j] for i in set_A, j in set_B) == K`.
- Set the objective to minimize `sum(cost[i][j] * x[i][j] for i in set_A, j in set_B)`.

### Formulation Template
```json
{
  "sets": ["set_A", "set_B"],
  "parameters": ["cost[set_A][set_B]", "K"],
  "decision_variables": ["x[set_A][set_B] (binary)"],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j] * x[i][j] for i in set_A, j in set_B )"
  },
  "constraints": [
    "sum_{j in set_B} x[i][j] <= 1, forall i in set_A",
    "sum_{i in set_A} x[i][j] <= 1, forall j in set_B",
    "sum_{i in set_A, j in set_B} x[i][j] == K"
  ]
}
```

### Common Pitfalls
- Creating variables for all possible `(i,j)` pairs inefficiently for very large sets; consider using sparse cost matrices.
- Formulating the cardinality constraint as `<= K` instead of `== K`, which relaxes the problem.
- Using floating-point equality (`==`) in the cardinality constraint within solvers that use integer tolerances; prefer exact integer constraints.

## Solving stage

### Strategy Overview
Use a general-purpose Mixed-Integer Programming (MIP) solver (e.g., SCIP, CBC, GLPK) via an algebraic modeling interface (e.g., OR-Tools `pywraplp`, Pyomo) to find the optimal binary assignment.

### Step 1 - Build the MIP Model
- Instantiate a solver with a MIP-capable backend (e.g., `"SCIP"`).
- Create binary variables `x[i,j]` using loops over `set_A` and `set_B`.
- Add constraints using the solver's linear expression API.
- Define the minimization objective with the given cost coefficients.

### Step 2 - Solve and Interpret Results
- Invoke the solver and check the termination status (`OPTIMAL` or `FEASIBLE`).
- Extract solution values for binary variables, using a threshold (e.g., `> 0.5`) to identify active assignments.
- For small instances, implement brute-force validation to confirm optimality and debug model formulation.
- Handle solver failures gracefully by checking status codes and having fallback solvers (e.g., GLPK if HiGHS fails).

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    # Fallback to another solver, e.g., "CBC" or "GLPK"
    solver = pywraplp.Solver.CreateSolver("CBC")

# Create variables
x = {}
for i in set_A:
    for j in set_B:
        x[i, j] = solver.IntVar(0, 1, f"x_{i}_{j}")

# Add constraints
# Row constraints
for i in set_A:
    solver.Add(solver.Sum([x[i, j] for j in set_B]) <= 1)
# Column constraints
for j in set_B:
    solver.Add(solver.Sum([x[i, j] for i in set_A]) <= 1)
# Cardinality constraint
total_assignments = solver.Sum([x[i, j] for i in set_A for j in set_B])
solver.Add(total_assignments == K)

# Set objective
objective_terms = [cost[i][j] * x[i, j] for i in set_A for j in set_B]
solver.Minimize(solver.Sum(objective_terms))

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    assignments = []
    total_cost = solver.Objective().Value()
    for i in set_A:
        for j in set_B:
            if x[i, j].solution_value() > 0.5:
                assignments.append((i, j, cost[i][j]))
else:
    # Handle no solution found
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Not verifying the solver object was created successfully before using it, leading to `None` attribute errors.
- Using `==` for floating-point comparisons when extracting binary variable solutions; always use a tolerance.
- Neglecting to check for multiple optimal solutions; the solver returns one optimal solution, but others may exist.
