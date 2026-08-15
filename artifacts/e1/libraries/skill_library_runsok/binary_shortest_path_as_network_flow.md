---
name: Binary Shortest Path as Network Flow
description: |
  Model a shortest path problem as a single-commodity flow with binary arc selection, then solve using specialized network flow or general MIP solvers.
---

# Workflow 1 (Specialized Min-Cost Flow Solver)

## Modeling stage

### Strategy Overview
Formulate the shortest path problem as a min-cost flow with unit demand, leveraging the integrality property of network flow solvers to enforce binary arc selection via capacity constraints.

### Step 1 - Map Problem to Network Components
- Identify nodes as locations and arcs as possible routes with associated costs.
- Define a unit flow demand: supply of +1 at the source node and demand of -1 at the sink node (or supply of -1).
- Set the capacity of each arc to 1 to enforce binary selection, as flow will be integer.

### Step 2 - Apply Standard Flow Conservation
- For each node `i`, enforce the flow balance constraint: Σ(flow into i) - Σ(flow out of i) = supply[i].
- Set supply[source] = 1, supply[sink] = -1, and supply[intermediate] = 0.
- Ensure sign convention matches the solver's expected input (e.g., `outgoing - incoming = supply`).

### Formulation Template
```json
{
  "sets": [
    "N": "Set of nodes",
    "A": "Set of arcs (i, j) with defined cost"
  ],
  "parameters": [
    "cost_ij": "Cost per unit flow on arc (i, j)",
    "supply_i": "Net supply at node i (+1 for source, -1 for sink, 0 otherwise)"
  ],
  "decision_variables": [
    "flow_ij": "Flow on arc (i, j), integer between 0 and capacity"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_ij * flow_ij for (i,j) in A)"
  },
  "constraints": [
    "Flow conservation: sum(flow_ji for (j,i) in A) - sum(flow_ij for (i,j) in A) = supply_i, for all i in N",
    "Capacity: 0 <= flow_ij <= 1, for all (i,j) in A"
  ]
}
```

### Common Pitfalls
- Incorrectly assigning supply/demand signs, causing infeasibility.
- Using non-integer costs or supplies, which may break integrality guarantees.
- Adding arcs with infinite cost instead of omitting them, which can cause numerical issues.

## Solving stage

### Strategy Overview
Use a dedicated min-cost flow solver that exploits network structure for efficiency, automatically returning integer flows due to integral supplies and capacities.

### Step 1 - Initialize Solver and Add Network Data
- Instantiate a min-cost flow solver (e.g., `SimpleMinCostFlow`).
- Add each arc using `add_arc_with_capacity_and_unit_cost(tail, head, capacity=1, cost)`.
- Set node supplies using `set_node_supply(node, supply_value)`.

### Step 2 - Solve and Validate Status
- Call the solver's `solve()` method.
- Check the return status equals `OPTIMAL` before proceeding. Handle `INFEASIBLE` or `UNBALANCED` statuses with appropriate error messages.

### Step 3 - Extract and Verify Solution
- Retrieve the optimal cost via `optimal_cost()`.
- Iterate through all arcs, collecting those with `flow(arc_index) > 0` as the selected path.
- Optionally, verify flow conservation by recomputing net flow at each node.

### Code Usage
```python
# Example using OR-Tools SimpleMinCostFlow
from ortools.graph.python import min_cost_flow

# 1. Initialize solver
smcf = min_cost_flow.SimpleMinCostFlow()

# 2. Add arcs (example placeholder: arcs = [(tail, head, cost)])
for tail, head, cost in arcs:
    arc_index = smcf.add_arc_with_capacity_and_unit_cost(
        tail, head, capacity=1, unit_cost=cost
    )

# 3. Set supplies (example: source_id, sink_id defined)
smcf.set_node_supply(source_id, 1)
smcf.set_node_supply(sink_id, -1)
# Other nodes default to 0 supply

# 4. Solve and check status
status = smcf.solve()
if status == smcf.OPTIMAL:
    total_cost = smcf.optimal_cost()
    selected_arcs = []
    for i in range(smcf.num_arcs()):
        if smcf.flow(i) > 0:
            selected_arcs.append((smcf.tail(i), smcf.head(i), smcf.unit_cost(i)))
    # Output results
    print(f"RESULT:{total_cost}")
else:
    print(f"ERROR:Solver returned status {status}")
```

### Common Pitfalls
- Forgetting to set supplies for all nodes, leading to an unbalanced network.
- Assuming solver status is optimal without checking, resulting in runtime errors when accessing solution values.
- Misinterpreting arc indices if the solver reorders internal data structures.

# Workflow 2 (General MIP Solver with Pyomo/OR-Tools)

## Modeling stage

### Strategy Overview
Explicitly model binary arc selection variables with flow conservation constraints, providing a flexible formulation suitable for any Mixed-Integer Programming (MIP) solver.

### Step 1 - Define Sets and Binary Variables
- Define set `N` of nodes and set `A` of arcs (e.g., as tuples `(i, j)`).
- Create binary decision variables `x[i,j] ∈ {0,1}` representing arc selection.

### Step 2 - Implement Flow Conservation per Node Type
- For the source node `s`: enforce `sum(x[s,j] for j in successors) - sum(x[i,s] for i in predecessors) = 1`.
- For the sink node `t`: enforce `sum(x[i,t] for i in predecessors) - sum(x[t,j] for j in successors) = 1`.
- For each intermediate node `k`: enforce `sum(x[i,k] for i in predecessors) = sum(x[k,j] for j in successors)`.

### Step 3 - Formulate Linear Objective
- Define the objective as minimizing total cost: `min sum(cost[i,j] * x[i,j] for (i,j) in A)`.

### Formulation Template
```json
{
  "sets": [
    "N": "Set of nodes",
    "A": "Set of directed arcs (i, j)"
  ],
  "parameters": [
    "cost_ij": "Cost of selecting arc (i, j)",
    "source_node": "Index of source node",
    "sink_node": "Index of sink node"
  ],
  "decision_variables": [
    "x_ij": "Binary, 1 if arc (i, j) is selected in the path"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_ij * x_ij for (i,j) in A)"
  },
  "constraints": [
    "Source flow: sum(x_source_j for j where (source,j) in A) - sum(x_i_source for i where (i,source) in A) = 1",
    "Sink flow: sum(x_i_sink for i where (i,sink) in A) - sum(x_sink_j for j where (sink,j) in A) = 1",
    "Flow conservation (intermediate): sum(x_i_k for i where (i,k) in A) = sum(x_k_j for j where (k,j) in A), for all k in N \\ {source, sink}"
  ]
}
```

### Common Pitfalls
- Creating variables for non-existent arcs, bloating the model unnecessarily.
- Incorrectly swapping inflow/outflow terms in conservation constraints.
- Using a single generic flow constraint for all nodes without handling source/sink differences, leading to infeasibility.

## Solving stage

### Strategy Overview
Use a general-purpose MIP solver (e.g., HiGHS, SCIP, CBC) via a modeling interface (Pyomo or OR-Tools wrapper), configuring it for exact solution of binary problems.

### Step 1 - Build Model and Configure Solver
- Instantiate a concrete model and add variables, objective, and constraints as per the formulation.
- Select a MIP solver (e.g., `SolverFactory('highs')` in Pyomo, `pywraplp.Solver.CreateSolver('SCIP')` in OR-Tools).
- Set solver parameters: `time_limit`, `mip_rel_gap=0.0` for exact optimality, and `threads` for parallelism.

### Step 2 - Solve and Check Termination Status
- Invoke the solver with the model.
- Check both the solver status (e.g., `SolverStatus.ok`) and the termination condition (e.g., `TerminationCondition.optimal` or `.feasible`). Proceed only if acceptable.

### Step 3 - Extract and Validate Binary Solution
- Retrieve variable values, selecting arcs where `value(x[i,j]) > 0.5` (accounting for numerical tolerance).
- Reconstruct the path from source to sink and compute its total cost for verification.
- Output structured results for downstream processing.

### Code Usage
```python
# Example using Pyomo with HiGHS solver
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, TerminationCondition, SolverStatus

# 1. Build model
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=node_list)
model.A = pyo.Set(within=model.N * model.N, initialize=arcs_list)
model.cost = pyo.Param(model.A, initialize=cost_dict)
model.x = pyo.Var(model.A, within=pyo.Binary)

# Objective
model.obj = pyo.Objective(
    expr=sum(model.cost[i,j] * model.x[i,j] for (i,j) in model.A),
    sense=pyo.minimize
)

# Constraints
def flow_source_rule(m):
    return sum(m.x[source, j] for j in m.N if (source, j) in m.A) - \
           sum(m.x[i, source] for i in m.N if (i, source) in m.A) == 1
model.con_source = pyo.Constraint(rule=flow_source_rule)

def flow_sink_rule(m):
    return sum(m.x[i, sink] for i in m.N if (i, sink) in m.A) - \
           sum(m.x[sink, j] for j in m.N if (sink, j) in m.A) == 1
model.con_sink = pyo.Constraint(rule=flow_sink_rule)

def flow_conservation_rule(m, k):
    if k == source or k == sink:
        return pyo.Constraint.Skip
    return sum(m.x[i, k] for i in m.N if (i, k) in m.A) == \
           sum(m.x[k, j] for j in m.N if (k, j) in m.A)
model.con_flow = pyo.Constraint(model.N, rule=flow_conservation_rule)

# 2. Solve
solver = SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model)

# 3. Check status and extract
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    selected_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.x[i,j]) > 0.5]
    print(f"RESULT:{total_cost}")
else:
    print(f"ERROR:Solver failed with status {results.solver.termination_condition}")
```

### Common Pitfalls
- Setting `mip_rel_gap` to an invalid value (e.g., -1.0) causing solver errors; use 0.0 for exact optimality.
- Not checking both solver status and termination condition, potentially using results from failed solves.
- Forgetting to skip flow conservation constraints for source/sink nodes, creating conflicting constraints.
