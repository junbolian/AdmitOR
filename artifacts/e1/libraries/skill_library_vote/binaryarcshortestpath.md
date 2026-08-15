---
name: BinaryArcShortestPath
description: |
  Model a shortest path problem as a binary arc selection network flow with unit demand, and solve it using either a specialized min-cost flow algorithm or a general-purpose MILP solver.
---

# Workflow 1 (Specialized Min-Cost Flow)

## Modeling stage

### Strategy Overview
Recognize the shortest path problem as a unit-demand min-cost flow. Map binary arc selection to flow arcs with capacity 1, and enforce flow conservation with a supply of +1 at the source and -1 at the sink.

### Step 1 - Map Problem to Flow Network
- Identify the set of nodes and all possible directed arcs.
- Define a cost parameter for each arc.
- Designate source and sink nodes.

### Step 2 - Formulate as Unit Flow
- Conceptualize sending one unit of flow from source to sink.
- Use binary arc selection variables implicitly enforced by arc capacity of 1 in the flow solver.
- Define node supplies: +1 for source, -1 for sink, 0 for all intermediate nodes.

### Formulation Template
```json
{
  "sets": ["nodes", "arcs"],
  "parameters": ["cost[arcs]", "source_node", "sink_node"],
  "decision_variables": [],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[a] * flow[a] for a in arcs)"
  },
  "constraints": [
    "flow_conservation: for each node n, sum(flow[outgoing_arcs]) - sum(flow[incoming_arcs]) = supply[n]",
    "capacity: for each arc a, 0 <= flow[a] <= 1"
  ]
}
```

### Common Pitfalls
- Misinterpreting flow conservation sign convention (outflow - inflow vs. supply).
- Forgetting to set arc capacities to 1, which fails to enforce binary selection.
- Using non-integer costs that may lead to numerical precision issues in flow algorithms.

## Solving stage

### Strategy Overview
Leverage a dedicated min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) which efficiently handles the unit-capacity network flow structure and returns integer solutions.

### Step 1 - Initialize Solver and Add Arcs
- Instantiate the min-cost flow solver.
- Add each directed arc to the solver, specifying its tail, head, capacity (1), and unit cost.

### Step 2 - Set Node Supplies and Solve
- Set the supply value for each node (+1 for source, -1 for sink, 0 otherwise).
- Call the solver and check for an `OPTIMAL` status.

### Step 3 - Extract and Verify Solution
- Retrieve the optimal cost and the flow on each arc.
- Collect arcs with positive flow (typically 1) as the selected path.
- Optionally, verify flow conservation by recalculating net flow at each node.

### Code Usage
```python
from ortools.graph import pywrapgraph

# Initialize solver
min_cost_flow = pywrapgraph.SimpleMinCostFlow()

# Add arcs (example: arc from u to v with cost c)
for (u, v, c) in arcs:
    min_cost_flow.AddArcWithCapacityAndUnitCost(u, v, 1, c)

# Set node supplies
for node in nodes:
    supply = 1 if node == source else (-1 if node == sink else 0)
    min_cost_flow.SetNodeSupply(node, supply)

# Solve
status = min_cost_flow.Solve()
if status == min_cost_flow.OPTIMAL:
    total_cost = min_cost_flow.OptimalCost()
    # Extract selected arcs
    selected_arcs = []
    for i in range(min_cost_flow.NumArcs()):
        if min_cost_flow.Flow(i) > 0:
            tail = min_cost_flow.Tail(i)
            head = min_cost_flow.Head(i)
            selected_arcs.append((tail, head))
else:
    # Handle infeasible or error status
    pass
```

### Common Pitfalls
- Assuming the solver always returns integer flows without setting integer capacities.
- Not checking solver status before extracting the solution, leading to runtime errors.
- Incorrectly mapping node indices between the problem data and the solver's internal representation.

# Workflow 2 (General-Purpose MILP)

## Modeling stage

### Strategy Overview
Explicitly model binary decision variables for each arc and formulate flow conservation constraints as linear equations. Solve the resulting Mixed-Integer Linear Program (MILP) using a solver like HiGHS, SCIP, or Gurobi.

### Step 1 - Define Binary Decision Variables
- For each directed arc, create a binary variable `x[i,j] ∈ {0,1}` indicating selection.

### Step 2 - Formulate Flow Conservation Constraints
- For the source node: sum of outgoing variables minus sum of incoming variables equals 1.
- For the sink node: sum of incoming variables minus sum of outgoing variables equals 1.
- For each intermediate node: sum of incoming variables equals sum of outgoing variables.

### Step 3 - Define the Cost Objective
- Formulate the objective as the minimization of the sum of arc costs multiplied by their corresponding binary variables.

### Formulation Template
```json
{
  "sets": ["nodes", "arcs"],
  "parameters": ["cost[arcs]", "source_node", "sink_node"],
  "decision_variables": ["x[arcs] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[a] * x[a] for a in arcs)"
  },
  "constraints": [
    "source_flow: sum(x[source_node, j] for j) - sum(x[i, source_node] for i) == 1",
    "sink_flow: sum(x[i, sink_node] for i) - sum(x[sink_node, j] for j) == 1",
    "flow_conservation[k ≠ source,sink]: sum(x[i, k] for i) - sum(x[k, j] for j) == 0"
  ]
}
```

### Common Pitfalls
- Creating constraints for self-loop arcs (i,i), which should be fixed to 0 or excluded.
- Setting an invalid MIP relative gap (e.g., -1.0) causing solver errors; use 0.0 for exact optimality.
- Inefficiently iterating over all possible node pairs for a sparse graph; define the arc set explicitly.

## Solving stage

### Strategy Overview
Build the MILP model using a modeling library (e.g., Pyomo), configure the solver with appropriate optimality tolerances and time limits, solve, and rigorously check termination status before extracting results.

### Step 1 - Build Model with Modeling Library
- Instantiate a concrete model.
- Define sets, parameters, and binary variables.
- Add the objective and flow conservation constraints using rule functions.

### Step 2 - Configure and Run Solver
- Select a MILP solver (e.g., `highs`, `scip`, `gurobi`).
- Set key options: `time_limit`, `mip_rel_gap` (0.0 for optimal), `threads`.
- Solve the model with status output (`tee=True` for debugging).

### Step 3 - Check Status and Extract Solution
- Verify the solver status is `ok` and the termination condition is `optimal` or `feasible`.
- Retrieve the objective value.
- Collect all arcs where the variable value exceeds 0.5 (accounting for numerical tolerance).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
# Define sets and parameters
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(initialize=arcs, dimen=2)
model.cost = pyo.Param(model.A, initialize=cost_data)
model.source = source_node
model.sink = sink_node

# Binary variables
model.x = pyo.Var(model.A, domain=pyo.Binary)

# Objective
model.obj = pyo.Objective(
    expr=sum(model.cost[a] * model.x[a] for a in model.A),
    sense=pyo.minimize
)

# Flow conservation constraints
def source_rule(m):
    return (sum(m.x[(m.source, j)] for j in m.N if (m.source, j) in m.A) -
            sum(m.x[(i, m.source)] for i in m.N if (i, m.source) in m.A) == 1)
model.source_con = pyo.Constraint(rule=source_rule)

# Similar rules for sink and intermediate nodes...

# Solve
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

# Check and extract
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    total_cost = float(pyo.value(model.obj))
    selected_arcs = [a for a in model.A if pyo.value(model.x[a]) > 0.5]
else:
    # Handle non-optimal status
    pass
```

### Common Pitfalls
- Accessing solution values without checking solver status, risking `ValueError`.
- Using a loose `mip_rel_gap` when an exact optimal solution is required.
- Forgetting to filter out fixed or non-existent arcs in constraint rules, leading to `KeyError`.
