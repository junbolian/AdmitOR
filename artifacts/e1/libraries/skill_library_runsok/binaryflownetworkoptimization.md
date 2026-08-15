---
name: BinaryFlowNetworkOptimization
description: |
  Model and solve binary network flow problems as shortest path or unit flow routing using MILP formulations or specialized min-cost flow algorithms.
---

# Workflow 1 (MILP with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the binary arc selection problem as a Mixed-Integer Linear Program (MILP) using a high-level algebraic modeling language. This approach provides clear separation of model components, is solver-agnostic, and is well-suited for problems requiring custom constraints or extensions.

### Step 1 - Define Sets and Parameters
- Define a set of nodes `N` representing all vertices in the network.
- Define a set of arcs `A` as a subset of `N × N`, typically excluding self-loops `(i,i)`.
- Create a cost parameter `c[i,j]` for each arc `(i,j) ∈ A`, stored as a dictionary or Pyomo Param.

### Step 2 - Create Binary Decision Variables
- Create binary decision variables `x[i,j] ∈ {0,1}` for each arc `(i,j) ∈ A`.
- The variable `x[i,j] = 1` indicates the arc is selected in the path/flow.

### Step 3 - Formulate Flow Conservation Constraints
- For the source node `s`, enforce net outflow: `∑_j x[s,j] - ∑_i x[i,s] = supply` (typically 1).
- For the sink node `t`, enforce net inflow: `∑_i x[i,t] - ∑_j x[t,j] = demand` (typically 1).
- For each intermediate node `k ∈ N \ {s,t}`, enforce flow balance: `∑_i x[i,k] = ∑_j x[k,j]`.

### Step 4 - Define Linear Cost Objective
- Define the objective to minimize total cost: `min ∑_{(i,j) ∈ A} c[i,j] * x[i,j]`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i ≠ j"
  ],
  "parameters": [
    "c[i,j]: unit cost for using arc (i,j)",
    "supply: net flow from source (e.g., 1)",
    "demand: net flow into sink (e.g., 1)"
  ],
  "decision_variables": [
    "x[i,j] ∈ {0,1}: binary flow variable for arc (i,j)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{ (i,j) in A } c[i,j] * x[i,j]"
  },
  "constraints": [
    "source_flow: sum_{ j in N } x[s,j] - sum_{ i in N } x[i,s] = supply",
    "sink_flow: sum_{ i in N } x[i,t] - sum_{ j in N } x[t,j] = demand",
    "flow_conservation[k] for k in N \\ {s,t}: sum_{ i in N } x[i,k] = sum_{ j in N } x[k,j]"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops from the arc set, which can create invalid variables and constraints.
- Incorrectly signing the flow balance equations for source/sink nodes (net outflow vs. net inflow).
- Using external data dictionaries directly in the objective/constraints instead of encapsulating them as model parameters, which can lead to scoping errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver (e.g., Gurobi, CBC, HiGHS). The workflow involves configuring the solver, solving the instance, rigorously checking termination status, and extracting the solution for validation and output.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver object using `SolverFactory`.
- Set key parameters: `time_limit` for runtime control, `mipgap` (or `ratio`) for optimality tolerance, `threads` for parallelism, and `seed` for reproducibility.

### Step 2 - Solve and Check Status
- Call the solver's `solve` method on the model.
- Check the high-level solver status (`SolverStatus.ok`).
- Check the detailed termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Validate Solution
- If the solve was successful, extract the objective value using `pyo.value(model.obj)`.
- Extract selected arcs by iterating over `model.x` and filtering where `pyo.value(model.x[i,j]) > 0.5`.
- Optionally, perform a post-solution validation by recomputing net flow at each node to verify all constraints.

### Step 4 - Handle Failures and Produce Output
- If the solver fails or returns infeasible, produce a structured error payload (e.g., JSON) containing the solver status and termination condition.
- For successful solves, output both a human-readable summary and a machine-readable payload with the objective value and selected arcs.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (function returning a ConcreteModel)
model, data_dict = build_binary_flow_model(node_list, arc_cost_dict, source_idx, sink_idx)

# Solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'cbc', 'highs'
solver.options['time_limit'] = 30
solver.options['mipgap'] = 0.0
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    objective_val = pyo.value(model.obj)
    selected_arcs = [(i, j, data_dict['cost'][(i,j)]) for (i,j) in model.A if pyo.value(model.x[i,j]) > 0.5]
    # Output results
else:
    error_payload = {
        "status": "failed",
        "solver_status": str(status),
        "termination_condition": str(term)
    }
    # Output error
```

### Common Pitfalls
- Assuming `SolverStatus.ok` alone indicates an optimal solution; must also check `TerminationCondition`.
- Not setting a time limit, which can cause the solver to run indefinitely on difficult instances.
- Attempting to access variable values from a failed or interrupted solve, leading to runtime errors.

# Workflow 2 (Specialized Min-Cost Flow with OR-Tools)

## Modeling stage

### Strategy Overview
Model the binary arc selection problem as a min-cost flow problem on a directed graph, leveraging specialized network flow algorithms. This approach is efficient for pure flow problems, uses capacity=1 to enforce binary usage, and is often faster than general-purpose MILP for large-scale networks.

### Step 1 - Map Problem to Min-Cost Flow Components
- Represent each node with a supply/demand value: source node supply = +1, sink node demand = +1 (or supply = -1), intermediate nodes supply = 0.
- Define each directed arc with a capacity of 1 (enforcing binary usage) and a unit cost.

### Step 2 - Structure Network Data
- Store arcs as a list of tuples `(start_node, end_node, cost)`.
- Store node supplies as a list or dictionary indexed by node ID.

### Step 3 - Enforce Binary Flow via Capacity
- Set the capacity of every arc to 1. Combined with integer node supplies, this ensures the flow on each arc is binary (0 or 1) in an optimal solution.

### Step 4 - Define Objective
- The objective is implicitly to find the feasible flow that minimizes total cost = Σ (flow[i,j] * cost[i,j]).

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs"
  ],
  "parameters": [
    "supply[i]: net supply at node i (positive for source, negative for sink, zero otherwise)",
    "capacity[i,j]: maximum flow on arc (i,j) (set to 1 for binary flow)",
    "unit_cost[i,j]: cost per unit flow on arc (i,j)"
  ],
  "decision_variables": [
    "flow[i,j] ∈ ℤ: integer flow on arc (i,j), bounded by capacity"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{ (i,j) in A } unit_cost[i,j] * flow[i,j]"
  },
  "constraints": [
    "flow_conservation[i] for i in N: sum_{ j in N } flow[i,j] - sum_{ j in N } flow[j,i] = supply[i]",
    "capacity[i,j] for (i,j) in A: 0 ≤ flow[i,j] ≤ capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Incorrectly setting total supply ≠ total demand, which makes the problem infeasible (must sum to zero).
- Using fractional costs or supplies when the solver expects integer data, potentially causing numerical issues.
- Assuming the solver will automatically produce binary flows without explicitly setting arc capacities to 1.

## Solving stage

### Strategy Overview
Use a specialized min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`). This involves building the graph, setting node supplies and arc capacities/costs, solving, and extracting the resulting flow pattern.

### Step 1 - Initialize Solver and Add Arcs
- Create an instance of the min-cost flow solver.
- For each arc `(i, j, cost)`, add it to the solver with `capacity=1` and the given unit cost.

### Step 2 - Set Node Supplies
- For each node, set its supply value (`supply[i]`). Ensure total supply sums to zero.

### Step 3 - Solve and Check Optimality
- Call the solver's `solve()` method.
- Verify the return status equals the solver's `OPTIMAL` constant.

### Step 4 - Extract Solution and Path
- Retrieve the optimal total cost from the solver.
- Iterate over all arcs, query the flow value (`> 0` indicates usage), and collect the selected arcs.
- Reconstruct the path from source to sink by following arcs with positive flow.

### Step 5 - Validate and Output
- Optionally validate the solution by checking flow conservation at each node using the extracted flows.
- Output the optimal cost, the sequence of nodes in the path, and a structured result payload.

### Code Usage
```python
from ortools.graph import pywrapgraph

# Build and solve min-cost flow model
def solve_min_cost_flow(node_supplies, arcs):
    # arcs: list of (start, end, cost)
    min_cost_flow = pywrapgraph.SimpleMinCostFlow()
    
    # Add arcs with capacity 1
    for start, end, cost in arcs:
        min_cost_flow.AddArcWithCapacityAndUnitCost(start, end, 1, cost)
    
    # Set node supplies
    for node_id, supply in enumerate(node_supplies):
        min_cost_flow.SetNodeSupply(node_id, supply)
    
    # Solve and check status
    status = min_cost_flow.Solve()
    if status == min_cost_flow.OPTIMAL:
        total_cost = min_cost_flow.OptimalCost()
        used_arcs = []
        for arc_idx in range(min_cost_flow.NumArcs()):
            if min_cost_flow.Flow(arc_idx) > 0:
                start = min_cost_flow.Tail(arc_idx)
                end = min_cost_flow.Head(arc_idx)
                cost = min_cost_flow.UnitCost(arc_idx)
                used_arcs.append((start, end, cost))
        return status, total_cost, used_arcs
    else:
        return status, None, None

# Usage
node_supplies = [1] + [0]*(num_nodes-2) + [-1]  # source supply=1, sink demand=1
status, opt_cost, solution_arcs = solve_min_cost_flow(node_supplies, arc_data_list)
if status == pywrapgraph.SimpleMinCostFlow.OPTIMAL:
    # Process solution_arcs
else:
    # Handle infeasible or error status
```

### Common Pitfalls
- Misinterpreting the solver status codes; only `OPTIMAL` guarantees a valid solution.
- Forgetting to set arc capacities to 1, which can result in fractional or non-binary flows.
- Not verifying that the extracted flows form a single continuous path from source to sink (could be multiple disjoint cycles in degenerate cases).
