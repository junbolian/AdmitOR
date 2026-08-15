---
name: BipartiteFlowAssignment
description: |
  Model and solve bipartite flow assignment problems with supply-demand constraints, per-pair capacities, and linear costs using either LP or min-cost flow formulations.

---

# Workflow 1 (Linear Programming Formulation)

## Modeling stage

### Strategy Overview
Formulate the bipartite assignment as a continuous linear program (LP). This approach is suitable when fractional flows are acceptable and provides a direct, solver-agnostic representation of supply, demand, and capacity constraints.

### Step 1 - Define Problem Structure
- Identify two disjoint sets: supply nodes (e.g., resources) and demand nodes (e.g., tasks).
- Confirm that total supply equals total demand for feasibility; if not, adjust supplies/demands or introduce a dummy node.
- Organize data into matrices for cost and capacity, indexed by supply and demand nodes.

### Step 2 - Create Decision Variables
- Define a continuous, non-negative decision variable for each supply-demand pair, representing the flow/assignment amount.
- Directly apply per-pair capacity as the variable's upper bound during creation.

### Step 3 - Formulate Constraints
- Add a supply constraint for each supply node: the sum of outgoing flows must equal its total availability.
- Add a demand constraint for each demand node: the sum of incoming flows must equal its total requirement.

### Step 4 - Define Objective
- Formulate a linear objective to minimize the total cost, summing the product of flow and unit cost for all arcs.

### Formulation Template
```json
{
  "sets": [
    "supply_nodes",
    "demand_nodes"
  ],
  "parameters": [
    {"name": "availability", "index": "supply_nodes", "type": "float"},
    {"name": "requirement", "index": "demand_nodes", "type": "float"},
    {"name": "cost", "index": ["supply_nodes", "demand_nodes"], "type": "float"},
    {"name": "capacity", "index": ["supply_nodes", "demand_nodes"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["supply_nodes", "demand_nodes"], "type": "continuous", "bounds": [0, "capacity"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in supply_nodes, j in demand_nodes} cost[i][j] * flow[i][j]"
  },
  "constraints": [
    {"name": "supply_limit", "expression": "sum_{j in demand_nodes} flow[i][j] = availability[i]", "index": "i in supply_nodes"},
    {"name": "demand_satisfaction", "expression": "sum_{i in supply_nodes} flow[i][j] = requirement[j]", "index": "j in demand_nodes"}
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand, which can lead to infeasibility.
- Using integer variables unnecessarily when fractional assignments are acceptable, increasing solve time.
- Incorrectly indexing cost and capacity matrices, leading to mismatched constraints.

## Solving stage

### Strategy Overview
Solve the LP using a dedicated linear programming solver (e.g., GLOP, HiGHS). The workflow involves building the model, setting parameters, solving, and rigorously checking the solution status before extracting results.

### Step 1 - Initialize Solver and Model
- Instantiate a solver object suitable for linear programming (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Verify the solver backend is available; log an error if not.

### Step 2 - Build Variables and Constraints
- Create variables in nested loops, passing the per-pair capacity as the upper bound.
- Add supply and demand constraints by creating constraint objects and setting coefficients for each variable.

### Step 3 - Set Objective and Solve
- Define the minimization objective by setting the coefficient for each variable.
- Call the solver's `Solve()` method.
- Check the solution status (e.g., `OPTIMAL` or `FEASIBLE`); handle non-optimal statuses with appropriate error messages.

### Step 4 - Extract and Verify Solution
- Extract the optimal objective value.
- Retrieve the flow value for each variable.
- Implement post-solve verification: recompute totals per supply and demand node to confirm constraint satisfaction within a small tolerance.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
# Create variables with capacity bounds
flow = {}
for i in supply_nodes:
    for j in demand_nodes:
        flow[i, j] = solver.NumVar(0, capacity[i][j], f"flow_{i}_{j}")
# Add supply constraints
for i in supply_nodes:
    ct = solver.Constraint(availability[i], availability[i])
    for j in demand_nodes:
        ct.SetCoefficient(flow[i, j], 1)
# Add demand constraints
for j in demand_nodes:
    ct = solver.Constraint(requirement[j], requirement[j])
    for i in supply_nodes:
        ct.SetCoefficient(flow[i, j], 1)
# Set objective
objective = solver.Objective()
for i in supply_nodes:
    for j in demand_nodes:
        objective.SetCoefficient(flow[i, j], cost[i][j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # Extract flows and verify
    solution_flows = {(i, j): flow[i, j].solution_value() for i in supply_nodes for j in demand_nodes}
    # Verification logic here
else:
    # Handle solver failure
    raise Exception(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver status, leading to errors when trying to extract values from an infeasible or unbounded model.
- Using floating-point equality for constraint verification; use a tolerance instead.
- Overlooking thread configuration conflicts with some solvers; use default settings unless necessary.

# Workflow 2 (Min-Cost Flow Formulation)

## Modeling stage

### Strategy Overview
Leverage the specialized min-cost flow problem structure. This approach is efficient for bipartite networks, as it natively handles node supplies, arc capacities, and linear costs, often leading to faster solves.

### Step 1 - Map to Network Flow Components
- Model supply nodes as sources with positive supply values.
- Model demand nodes as sinks with negative supply values (or equivalently, positive demand).
- Model each possible assignment as a directed arc from a supply node to a demand node.

### Step 2 - Define Network Parameters
- Set the supply/demand value for each node, ensuring the total net supply is zero.
- For each arc, define a capacity (maximum flow) and a unit cost.

### Step 3 - Verify Problem Balance
- Confirm that the sum of all supplies equals the sum of all demands (negated). If not, the min-cost flow formulation is infeasible without adjustment.

### Formulation Template
```json
{
  "sets": [
    "supply_nodes",
    "demand_nodes",
    "arcs"
  ],
  "parameters": [
    {"name": "node_supply", "index": "supply_nodes", "type": "float"},
    {"name": "node_demand", "index": "demand_nodes", "type": "float"},
    {"name": "arc_capacity", "index": "arcs", "type": "float"},
    {"name": "arc_unit_cost", "index": "arcs", "type": "float"}
  ],
  "decision_variables": [
    {"name": "arc_flow", "index": "arcs", "type": "continuous", "bounds": [0, "arc_capacity"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{a in arcs} arc_unit_cost[a] * arc_flow[a]"
  },
  "constraints": [
    {"name": "flow_conservation", "expression": "sum_{a in outgoing_arcs(i)} arc_flow[a] - sum_{a in incoming_arcs(i)} arc_flow[a] = net_supply[i]", "index": "i in all_nodes"}
  ]
}
```

### Common Pitfalls
- Incorrectly setting node supplies (using positive values for demands instead of negative).
- Not offsetting demand node indices when adding arcs, leading to index collisions.
- Assuming the solver handles unbalanced problems; always balance supply and demand.

## Solving stage

### Strategy Overview
Use a dedicated min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`). The workflow involves building the network by adding arcs and setting node supplies, solving, and then extracting the flows on each arc.

### Step 1 - Initialize Min-Cost Flow Solver
- Create an instance of the min-cost flow solver.
- Ensure all node indices are consecutive integers starting from 0.

### Step 2 - Add Arcs and Set Node Supplies
- For each supply-demand pair, add an arc with its capacity and unit cost. Store the returned arc index for solution retrieval.
- Set the supply for each supply node (positive value).
- Set the supply for each demand node (negative value, i.e., `-requirement`).

### Step 3 - Solve and Check Status
- Invoke the solver's `solve()` method.
- Check that the status is `OPTIMAL` before proceeding. Provide clear error handling for other statuses (e.g., `INFEASIBLE`, `UNBALANCED`).

### Step 4 - Extract Flows and Verify
- Retrieve the optimal total cost from the solver.
- For each arc, get the flow value. Filter for positive flows to report assignments.
- Verify the solution by recalculating the net flow at each node and comparing it to the original supply/demand.

### Code Usage
```python
# build model from formulation
from ortools.graph import pywrapgraph

min_cost_flow = pywrapgraph.SimpleMinCostFlow()
arc_index = {}  # Map (supply, demand) -> arc index

# Add arcs
for i_idx, i in enumerate(supply_nodes):
    for j_idx, j in enumerate(demand_nodes):
        arc = min_cost_flow.add_arc_with_capacity_and_unit_cost(
            i_idx,  # Tail node (supply)
            len(supply_nodes) + j_idx,  # Head node (demand, offset)
            capacity[i][j],
            cost[i][j]
        )
        arc_index[(i, j)] = arc

# Set node supplies
for i_idx, i in enumerate(supply_nodes):
    min_cost_flow.set_node_supply(i_idx, availability[i])
for j_idx, j in enumerate(demand_nodes):
    min_cost_flow.set_node_supply(len(supply_nodes) + j_idx, -requirement[j])

# solve with status / termination checks
status = min_cost_flow.solve()
if status == min_cost_flow.OPTIMAL:
    total_cost = min_cost_flow.optimal_cost()
    # Extract flows
    solution_flows = {}
    for (i, j), arc in arc_index.items():
        flow_val = min_cost_flow.flow(arc)
        if flow_val > 1e-6:  # Filter near-zero flows
            solution_flows[(i, j)] = flow_val
    # Verification logic here
else:
    # Handle solver failure
    raise Exception(f"Min-cost flow solver failed with status: {status}")
```

### Common Pitfalls
- Forgetting to offset demand node indices, causing node index overlaps.
- Not storing arc indices, making it impossible to retrieve specific flow values after solving.
- Assuming the solver will automatically balance the network; it requires total net supply to be zero.
