---
name: BipartiteFlowAssignment
description: |
  Model and solve balanced bipartite flow problems with per-arc capacities and linear costs using either direct LP or specialized min-cost flow solvers.
---

# Workflow 1 (Linear Programming Formulation)

## Modeling stage

### Strategy Overview
Model the problem as a linear program (LP) with continuous flow variables on a bipartite graph. This approach is solver-agnostic, flexible for adding side constraints, and directly represents supply/demand balance and per-pair capacity limits.

### Step 1 - Define Sets and Parameters
- Define two distinct sets: `SUPPLY_NODES` (e.g., consultants) and `DEMAND_NODES` (e.g., projects).
- Define parameters: `availability[i]` for each supply node, `requirement[j]` for each demand node, `cost[i][j]` per unit flow, and `capacity[i][j]` as the upper bound for each arc.

### Step 2 - Create Flow Variables
- Create a continuous decision variable `x[i][j]` for each arc from supply node `i` to demand node `j`.
- Set its domain to `0 <= x[i][j] <= capacity[i][j]`.

### Step 3 - Enforce Flow Conservation
- Add a **supply constraint** for each `i` in `SUPPLY_NODES`: `sum_{j} x[i][j] = availability[i]`.
- Add a **demand constraint** for each `j` in `DEMAND_NODES`: `sum_{i} x[i][j] = requirement[j]`.

### Step 4 - Formulate Linear Objective
- Define the objective to minimize total cost: `min sum_{i} sum_{j} cost[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "SUPPLY_NODES", "description": "Indices for source nodes (e.g., i)."},
    {"name": "DEMAND_NODES", "description": "Indices for sink nodes (e.g., j)."}
  ],
  "parameters": [
    {"name": "availability", "index": "SUPPLY_NODES", "type": "float"},
    {"name": "requirement", "index": "DEMAND_NODES", "type": "float"},
    {"name": "cost", "index": ["SUPPLY_NODES", "DEMAND_NODES"], "type": "float"},
    {"name": "capacity", "index": ["SUPPLY_NODES", "DEMAND_NODES"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["SUPPLY_NODES", "DEMAND_NODES"], "type": "continuous", "bounds": "[0, capacity[i][j]]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in SUPPLY_NODES} sum_{j in DEMAND_NODES} cost[i][j] * x[i][j]"
  },
  "constraints": [
    {"name": "supply_balance", "index": "SUPPLY_NODES", "expression": "sum_{j in DEMAND_NODES} x[i][j] = availability[i]"},
    {"name": "demand_balance", "index": "DEMAND_NODES", "expression": "sum_{i in SUPPLY_NODES} x[i][j] = requirement[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand (`sum(availability) == sum(requirement)`), which is necessary for feasibility in this balanced formulation.
- Using integer variable types unnecessarily, which makes the problem harder to solve; use continuous variables for fractional flow.
- Not including the capacity upper bounds in the variable declaration, requiring separate constraints and increasing model size.

## Solving stage

### Strategy Overview
Solve the LP using a general-purpose linear programming solver. The workflow involves building the model matrix, invoking the solver, checking termination status, and extracting/verifying the solution.

### Step 1 - Initialize Solver and Model
- Instantiate an LP solver (e.g., `GLOP`, `HiGHS`).
- Implement error handling if the solver backend is unavailable.

### Step 2 - Build Model Programmatically
- Create variables with their lower and upper bounds.
- Add supply and demand constraints row by row, setting coefficients for the involved variables.
- Set the objective coefficients and sense to minimization.

### Step 3 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check for `OPTIMAL` or `FEASIBLE` status; handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error messages.

### Step 4 - Extract and Verify Solution
- Extract the objective value and all flow variable values.
- Programmatically verify that supply/demand constraints are satisfied within a small tolerance (e.g., 1e-6).
- Print a summary of non-zero assignments and the total cost.

### Code Usage
```python
# 1. Data preparation (example placeholders)
supply_nodes = range(n_supply)
demand_nodes = range(n_demand)
availability = [...]  # list length n_supply
requirement = [...]   # list length n_demand
cost = [[... for _ in demand_nodes] for _ in supply_nodes]
capacity = [[... for _ in demand_nodes] for _ in supply_nodes]

# 2. Solver initialization
solver = pywraplp.Solver.CreateSolver('GLOP')
if solver is None:
    raise RuntimeError('Solver backend not available.')

# 3. Variable creation
x = {}
for i in supply_nodes:
    for j in demand_nodes:
        x[i, j] = solver.NumVar(0.0, capacity[i][j], f'x_{i}_{j}')

# 4. Supply constraints
for i in supply_nodes:
    ct = solver.Constraint(availability[i], availability[i])
    for j in demand_nodes:
        ct.SetCoefficient(x[i, j], 1.0)

# 5. Demand constraints
for j in demand_nodes:
    ct = solver.Constraint(requirement[j], requirement[j])
    for i in supply_nodes:
        ct.SetCoefficient(x[i, j], 1.0)

# 6. Objective
objective = solver.Objective()
for i in supply_nodes:
    for j in demand_nodes:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# 7. Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # Verification loop (example)
    for i in supply_nodes:
        total_flow = sum(x[i, j].solution_value() for j in demand_nodes)
        assert abs(total_flow - availability[i]) < 1e-6, f'Supply constraint violation for node {i}'
    # Extract non-zero flows
    for i in supply_nodes:
        for j in demand_nodes:
            flow_val = x[i, j].solution_value()
            if flow_val > 1e-6:
                print(f'x[{i},{j}] = {flow_val}, cost = {cost[i][j]*flow_val}')
else:
    print('Solver did not find an optimal or feasible solution.')
```

### Common Pitfalls
- Not checking solver availability, leading to cryptic errors later.
- Forgetting to set the objective sense to minimization.
- Using exact equality (`==`) when checking floating-point solution values; always use a tolerance.
- Assuming the solver status is `OPTIMAL` without also accepting `FEASIBLE` for problems with multiple optima.

# Workflow 2 (Specialized Min-Cost Flow Solver)

## Modeling stage

### Strategy Overview
Model the problem as a min-cost flow on a bipartite network using a specialized algorithm. This approach is often more efficient for pure network flow problems and uses a compact arc-list representation.

### Step 1 - Map to Network Flow Structure
- Represent each supply node and demand node as a unique node in a directed graph.
- Create a directed arc from each supply node to each demand node.

### Step 2 - Define Arc Attributes
- For each arc `(i, j)`, assign a `capacity` (maximum flow) and a `unit_cost` (cost per unit flow).
- The flow on each arc is a non-negative continuous variable bounded by its capacity.

### Step 3 - Define Node Supplies
- Assign a `supply` value to each node: positive `availability[i]` for supply nodes, negative `-requirement[j]` for demand nodes.
- Ensure total supply equals total demand (`sum(supply) == 0`) for feasibility.

### Step 4 - Formulate Min-Cost Flow Objective
- The objective is to minimize `sum(flow(arc) * unit_cost(arc))` over all arcs, satisfying flow conservation at all nodes.

### Formulation Template
```json
{
  "sets": [
    {"name": "NODES", "description": "Union of all supply and demand node indices."},
    {"name": "ARCS", "description": "List of directed arcs from supply to demand nodes, e.g., (i, j)."}
  ],
  "parameters": [
    {"name": "node_supply", "index": "NODES", "type": "float", "description": "Positive for supply, negative for demand."},
    {"name": "arc_capacity", "index": "ARCS", "type": "float"},
    {"name": "arc_unit_cost", "index": "ARCS", "type": "float"}
  ],
  "decision_variables": [
    {"name": "flow", "index": "ARCS", "type": "continuous", "bounds": "[0, arc_capacity]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{(i,j) in ARCS} arc_unit_cost[i,j] * flow[i,j]"
  },
  "constraints": [
    {"name": "flow_conservation", "index": "NODES", "expression": "sum_{j: (i,j) in ARCS} flow[i,j] - sum_{k: (k,i) in ARCS} flow[k,i] = node_supply[i]"}
  ]
}
```

### Common Pitfalls
- Incorrectly signing node supplies (supply nodes should be positive, demand nodes negative).
- Not offsetting node indices when supply and demand sets overlap, causing node ID collisions.
- Assuming the solver handles unbalanced flows; specialized min-cost flow often requires total supply equals total demand.

## Solving stage

### Strategy Overview
Use a dedicated min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`). The workflow involves populating the network graph, setting node supplies, solving, and interpreting the flow results.

### Step 1 - Initialize Min-Cost Flow Solver
- Create an instance of the min-cost flow solver.
- Prepare mappings from problem nodes to solver node indices (offsetting if necessary).

### Step 2 - Add Arcs and Set Node Supplies
- For each arc `(i, j)`, add it to the solver with its capacity and unit cost.
- For each node, set its supply value using the solver's API.

### Step 3 - Solve and Validate Status
- Invoke the solver's `Solve()` method.
- Check that the returned status is `OPTIMAL`; handle other statuses (e.g., `INFEASIBLE`) appropriately.

### Step 4 - Extract Flows and Verify
- Retrieve the flow on each arc.
- Verify that flow conservation holds at each node and that arc capacities are respected.
- Output a summary of positive flows and the total cost.

### Code Usage
```python
# 1. Data preparation (example placeholders)
supply_nodes = range(n_supply)
demand_nodes = range(n_demand)
availability = [...]  # list length n_supply
requirement = [...]   # list length n_demand
cost = [[... for _ in demand_nodes] for _ in supply_nodes]
capacity = [[... for _ in demand_nodes] for _ in supply_nodes]

# 2. Solver initialization
from ortools.graph import pywrapgraph
smcf = pywrapgraph.SimpleMinCostFlow()

# 3. Map problem nodes to solver node indices
# Example: supply nodes 0..n_s-1, demand nodes n_s..n_s+n_d-1
node_index = {}
for i in supply_nodes:
    node_index[('supply', i)] = i
offset = len(supply_nodes)
for j in demand_nodes:
    node_index[('demand', j)] = offset + j

# 4. Add arcs
for i in supply_nodes:
    for j in demand_nodes:
        arc = smcf.AddArcWithCapacityAndUnitCost(
            node_index[('supply', i)],
            node_index[('demand', j)],
            capacity[i][j],
            cost[i][j]
        )
        # Store arc index if needed for later lookup

# 5. Set node supplies
for i in supply_nodes:
    smcf.SetNodeSupply(node_index[('supply', i)], availability[i])
for j in demand_nodes:
    smcf.SetNodeSupply(node_index[('demand', j)], -requirement[j])

# 6. Solve and check status
status = smcf.Solve()
if status == smcf.OPTIMAL:
    total_cost = smcf.OptimalCost()
    # Extract and verify flows
    for arc_idx in range(smcf.NumArcs()):
        flow = smcf.Flow(arc_idx)
        if flow > 1e-6:
            tail = smcf.Tail(arc_idx)
            head = smcf.Head(arc_idx)
            unit_cost = smcf.UnitCost(arc_idx)
            print(f'Arc {tail}->{head}: flow={flow}, cost={unit_cost*flow}')
    # Optional verification of node balances
else:
    print(f'Solver finished with non-optimal status: {status}')
```

### Common Pitfalls
- Not checking that `sum(availability) == sum(requirement)` before building the model, leading to infeasibility.
- Forgetting to set negative supply values for demand nodes.
- Misinterpreting arc indices when retrieving flows; use solver methods like `Tail(arc_idx)` to identify the arc.
- Assuming the solver modifies input data; it operates on its internal graph representation.
