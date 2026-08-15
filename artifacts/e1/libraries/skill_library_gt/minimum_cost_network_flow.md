---
name: Minimum Cost Network Flow
description: |
  Model and solve capacitated network flow problems with supply/demand nodes and linear transportation costs using either a general LP solver or a specialized network flow algorithm.

---

# Workflow 1 (General LP Formulation)

## Modeling stage

### Strategy Overview
Model the problem as a linear program using a generic solver backend (e.g., GLOP, CBC, HiGHS). This approach is flexible, handles any linear cost structure, and is easy to implement with libraries like OR-Tools or Pyomo.

### Step 1 - Define Network Structure
- Represent the system as a directed graph. Define a set of nodes (e.g., locations) and a set of directed arcs (e.g., transportation routes).
- Use a single signed parameter `supply[node]` where positive values indicate supply/source nodes and negative values indicate demand/sink nodes. Ensure total supply equals total demand.

### Step 2 - Create Decision Variables
- Define a continuous, non-negative decision variable `flow[arc]` for each directed arc.
- Set the variable's upper bound directly to the `capacity[arc]` parameter for that arc.

### Step 3 - Formulate Flow Conservation
- For each node, enforce the constraint: `sum(outgoing flows) - sum(incoming flows) = supply[node]`.
- This ensures the net outflow equals the node's supply/demand balance.

### Step 4 - Define the Objective
- Formulate a linear objective to minimize total transportation cost: `minimize sum( cost[arc] * flow[arc] )`.

### Formulation Template
```json
{
  "sets": [
    "nodes",
    "arcs (list of (from_node, to_node) tuples)"
  ],
  "parameters": [
    "supply[node] (signed value)",
    "cost[arc] (non-negative)",
    "capacity[arc] (non-negative)"
  ],
  "decision_variables": [
    "flow[arc] >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[arc] * flow[arc] for arc in arcs )"
  },
  "constraints": [
    "flow_conservation[node]: sum(flow[i,j] for j if (i,j) in arcs) - sum(flow[j,i] for j if (j,i) in arcs) = supply[i]",
    "capacity[arc]: flow[arc] <= capacity[arc]"
  ]
}
```

### Common Pitfalls
- Incorrect sign in flow conservation: Using `inflow - outflow` instead of `outflow - inflow` will reverse the supply/demand logic.
- Forgetting to exclude self-loops (arcs from a node to itself) from variable creation and constraints, which can lead to nonsensical solutions.
- Not verifying that total supply equals total demand, which can cause infeasibility.

## Solving stage

### Strategy Overview
Build and solve the LP model using a standard solver interface. Focus on correct model construction, solver status checking, and post-solution validation of constraints.

### Step 1 - Instantiate Solver and Variables
- Create a solver instance (e.g., `solver = pywraplp.Solver.CreateSolver('GLOP')`).
- Create the `flow` variables, setting their lower bound to 0 and upper bound to the corresponding `capacity`.

### Step 2 - Add Flow Conservation Constraints
- For each node, create a constraint with right-hand side equal to `supply[node]`.
- Iterate over all arcs, adding a coefficient of +1 to the constraint for outgoing arcs and -1 for incoming arcs.

### Step 3 - Set the Objective and Solve
- Create the objective function by summing `cost[arc] * flow[arc]` and set it for minimization.
- Call `solver.Solve()` and immediately check the result status (e.g., `OPTIMAL`, `FEASIBLE`).

### Step 4 - Extract and Validate Solution
- If optimal, extract the objective value and all non-zero flow values (above a small tolerance).
- Programmatically verify that the extracted solution satisfies all flow conservation and capacity constraints.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
flow = {}
for (i, j) in arcs:
    flow[i, j] = solver.NumVar(0, capacity[i, j], f'flow_{i}_{j}')

for node in nodes:
    ct = solver.Constraint(supply[node], supply[node])
    for (i, j) in arcs:
        if i == node:
            ct.SetCoefficient(flow[i, j], 1)   # outflow
        if j == node:
            ct.SetCoefficient(flow[i, j], -1)  # inflow

objective = solver.Objective()
for (i, j) in arcs:
    objective.SetCoefficient(flow[i, j], cost[i, j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL:
    total_cost = objective.Value()
    solution_flows = {(i,j): flow[i,j].solution_value() for (i,j) in arcs if flow[i,j].solution_value() > 1e-6}
    # Add validation logic here
else:
    print(f"Solver did not find optimal solution. Status: {status}")
```

### Common Pitfalls
- Failing to check solver status before accessing solution values, which can cause runtime errors.
- Using loose tolerances when checking constraint satisfaction; use a small epsilon (e.g., 1e-6) for comparisons.
- Not leveraging solver-specific performance options (e.g., time limits, threads) for larger problems.

# Workflow 2 (Specialized Network Flow Solver)

## Modeling stage

### Strategy Overview
Use a solver specialized for min-cost flow problems (e.g., OR-Tools `SimpleMinCostFlow`). This approach is more efficient for pure network flow structures, often guarantees integrality of flows, and uses a concise, arc-based API.

### Step 1 - Structure as a Min-Cost Flow Instance
- Model the problem directly as a min-cost flow instance with supplies, demands, and capacitated arcs.
- Define all data in terms of arcs: `(start_node, end_node, capacity, unit_cost)`.

### Step 2 - Encode Node Supplies
- Define a `supply[node]` array using the same signed convention: positive for supply, negative for demand.
- The specialized solver will internally handle the flow conservation constraints.

### Step 3 - Map All Arcs and Parameters
- Create a complete list of all possible arcs with their associated cost and capacity.
- Arcs with zero capacity can be omitted, as the solver only considers arcs added to the model.

### Formulation Template
```json
{
  "sets": [
    "nodes"
  ],
  "parameters": [
    "supply[node] (signed value)",
    "arcs_data (list of (from_node, to_node, capacity, unit_cost))"
  ],
  "decision_variables": [
    "Implicit flow variables managed by the solver"
  ],
  "objective": {
    "sense": "min",
    "expression": "Implicit: sum( unit_cost * flow )"
  },
  "constraints": [
    "Implicit flow conservation enforced by solver",
    "Implicit capacity constraints enforced by solver"
  ]
}
```

### Common Pitfalls
- Adding arcs with incorrect indices (e.g., node index out of bounds) causing solver errors.
- Misunderstanding the solver's internal sign convention for supply/demand; always use the documented API method (`set_node_supply`).
- Assuming the solver handles non-network side constraints; specialized solvers only handle pure min-cost flow.

## Solving stage

### Strategy Overview
Utilize the specialized solver's API to build the model arc-by-arc, solve, and extract flows. Rely on the solver's optimized algorithms and built-in feasibility checks.

### Step 1 - Initialize Solver and Add Arcs
- Create an instance of the specialized solver (e.g., `SimpleMinCostFlow()`).
- Iterate through `arcs_data` and add each arc using the solver's `add_arc_with_capacity_and_unit_cost` method.

### Step 2 - Set Node Supplies and Solve
- Use the solver's `set_node_supply` method for each node.
- Call the `solve()` method and check the return status (e.g., `OPTIMAL`).

### Step 3 - Extract and Verify Flows
- If optimal, retrieve the total cost via `optimal_cost()`.
- Iterate over all arcs using solver methods (`tail(i)`, `head(i)`, `flow(i)`) to extract non-zero flows.
- Perform a secondary validation that extracted flows respect capacities and node balances.

### Code Usage
```python
# build model from formulation
from ortools.graph.python import min_cost_flow

mf = min_cost_flow.SimpleMinCostFlow()

# Add arcs
for start_node, end_node, cap, unit_cost in arcs_data:
    arc_index = mf.add_arc_with_capacity_and_unit_cost(start_node, end_node, cap, unit_cost)

# Set node supplies
for node_id, node_supply in enumerate(supply):
    mf.set_node_supply(node_id, node_supply)

# solve with status / termination checks
solve_status = mf.solve()
if solve_status == mf.OPTIMAL:
    total_cost = mf.optimal_cost()
    # Extract flows
    solution_flows = []
    for arc_idx in range(mf.num_arcs()):
        flow = mf.flow(arc_idx)
        if flow > 0:
            tail = mf.tail(arc_idx)
            head = mf.head(arc_idx)
            solution_flows.append((tail, head, flow))
    # Add validation logic here
else:
    print(f"Solver failed with status: {solve_status}")
```

### Common Pitfalls
- Not checking the solver status, assuming `solve()` always returns optimal.
- Misinterpreting arc indices: the `add_arc_with_capacity_and_unit_cost` method returns an internal arc index, not the node indices.
- Forgetting that the solver may return integer flows; ensure downstream logic can handle integer values if variables were modeled as continuous.
