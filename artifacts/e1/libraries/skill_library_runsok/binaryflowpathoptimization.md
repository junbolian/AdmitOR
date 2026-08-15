---
name: BinaryFlowPathOptimization
description: |
  Model and solve binary network flow problems as shortest path selection using either MIP solvers or specialized graph algorithms.
---

# Workflow 1 (MIP Solver with Explicit Binary Variables)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) with explicit binary decision variables for each arc. This approach uses a generic MIP solver (e.g., CBC, SCIP) and is suitable for problems where arc selection is inherently binary, and flow conservation constraints define a single path from source to sink.

### Step 1 - Define Network Structure
- Identify the set of nodes (e.g., `N`) and the set of directed arcs (e.g., `A`). Exclude self-loops (i.e., arcs where head equals tail).
- Define a cost parameter `c[i,j]` for each arc `(i,j)` in `A`.

### Step 2 - Create Binary Decision Variables
- Create a binary decision variable `x[i,j]` for each arc `(i,j)` in `A`. `x[i,j] = 1` indicates the arc is selected in the optimal path.

### Step 3 - Enforce Flow Conservation
- Define a supply/demand parameter `b[i]` for each node `i`. For a single source-sink path problem, set `b[source] = 1`, `b[sink] = -1`, and `b[i] = 0` for all other (transshipment) nodes.
- For each node `i` in `N`, add the flow balance constraint: `sum(x[i,j] for all (i,j) in A) - sum(x[j,i] for all (j,i) in A) = b[i]`.

### Step 4 - Set Objective
- Formulate the objective to minimize the total cost of selected arcs: `minimize sum(c[i,j] * x[i,j] for all (i,j) in A)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i != j"
  ],
  "parameters": [
    "c[A]: cost per arc",
    "b[N]: net supply at node (1 for source, -1 for sink, 0 otherwise)"
  ],
  "decision_variables": [
    "x[A] ∈ {0,1}: binary arc selection"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( c[i,j] * x[i,j] for (i,j) in A )"
  },
  "constraints": [
    "flow_conservation[i in N]: sum( x[i,j] for (i,j) in A ) - sum( x[j,i] for (j,i) in A ) = b[i]"
  ]
}
```

### Common Pitfalls
- Adding redundant constraints (e.g., `sum(x[source,j]) = 1` or `sum(x[j,sink]) = 1`), which can cause infeasibility without improving the model. Flow conservation alone is sufficient.
- Forgetting to exclude self-loops from the arc set, which creates unnecessary variables and can distort the solution.
- Mis-specifying the supply/demand sign convention, leading to incorrect or infeasible models.

## Solving stage

### Strategy Overview
Implement the MIP model using a modeling library (e.g., Pyomo, OR-Tools LP) and solve it with an appropriate MIP solver (e.g., CBC, SCIP). Focus on correct solver configuration, status checking, and solution validation.

### Step 1 - Build Model from Formulation
- Instantiate a solver object (e.g., `SolverFactory('cbc')` in Pyomo, `pywraplp.Solver.CreateSolver('SCIP')` in OR-Tools).
- Create the model sets, parameters, and binary variables as defined in the formulation.
- Add the flow conservation constraints using loops over nodes.

### Step 2 - Configure and Execute Solver
- Set solver parameters for performance and control, such as a time limit (`seconds`), optimality gap tolerance (`ratio`), and number of threads.
- Invoke the solver on the model instance.

### Step 3 - Check Solver Status and Extract Solution
- After solving, check the solver status and termination condition. Accept results marked as `optimal` or `feasible`.
- If a solution is available, retrieve the values of the binary variables `x[i,j]`. Arcs with a value > 0.5 are considered selected.

### Step 4 - Validate Solution Integrity
- Verify flow conservation by recalculating `outflow - inflow` for each node using the solution values and comparing it to the supply `b[i]`.
- Confirm that the selected arcs form a single, simple directed path from the source to the sink.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(within=model.N*model.N, initialize=arcs)
model.c = pyo.Param(model.A, initialize=cost_dict)
model.b = pyo.Param(model.N, initialize=supply_dict)
model.x = pyo.Var(model.A, within=pyo.Binary)

def flow_rule(model, i):
    outflow = sum(model.x[i,j] for (i,j) in model.A if (i,j) in model.A)
    inflow = sum(model.x[j,i] for (j,i) in model.A if (j,i) in model.A)
    return outflow - inflow == model.b[i]
model.flow = pyo.Constraint(model.N, rule=flow_rule)

model.obj = pyo.Objective(expr=sum(model.c[a] * model.x[a] for a in model.A), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = time_limit
solver.options['ratio'] = optimality_gap
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:
    # Extract solution
    selected_arcs = [a for a in model.A if pyo.value(model.x[a]) > 0.5]
    total_cost = pyo.value(model.obj)
    # Validate flow conservation
    for i in model.N:
        outflow = sum(pyo.value(model.x[i,j]) for (i,j) in model.A if (i,j) in model.A)
        inflow = sum(pyo.value(model.x[j,i]) for (j,i) in model.A if (j,i) in model.A)
        assert abs(outflow - inflow - pyo.value(model.b[i])) < 1e-6
else:
    # Handle infeasibility or other statuses
    raise Exception(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `solver.termination_condition` before extracting results, potentially reading invalid solution data.
- Using a loose tolerance (e.g., 0.0) for checking binary variable values; a threshold like 0.5 is robust.
- Failing to validate the solution post-solve, which can miss modeling errors that the solver did not flag.

# Workflow 2 (Specialized Min-Cost Flow Algorithm)

## Modeling stage

### Strategy Overview
Leverage a specialized min-cost flow algorithm (e.g., OR-Tools `SimpleMinCostFlow`) by modeling binary arc selection as a unit-capacity flow problem. This approach is efficient and exploits the network structure, but requires the solver backend to support min-cost flow with integer capacities.

### Step 1 - Define Network with Capacities
- Identify nodes `N` and directed arcs `A` (excluding self-loops).
- Assign a unit capacity (e.g., `capacity = 1`) to each arc to enforce binary flow.
- Define a cost `c[i,j]` for each arc `(i,j)`.

### Step 2 - Set Node Supplies
- Define node supplies `s[i]`. For a single path problem, set `s[source] = 1`, `s[sink] = -1`, and `s[i] = 0` for all other nodes.

### Step 3 - Map to Min-Cost Flow
- The problem becomes: find a flow of value 1 from source to sink that satisfies the supplies and respects arc capacities, minimizing total cost. Due to unit capacities, the flow on each arc will be binary (0 or 1).

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i != j"
  ],
  "parameters": [
    "c[A]: cost per arc",
    "s[N]: supply at node (1 for source, -1 for sink, 0 otherwise)"
  ],
  "decision_variables": [
    "f[A] ∈ {0,1}: flow on arc (implicitly integer due to unit capacity)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( c[i,j] * f[i,j] for (i,j) in A )"
  },
  "constraints": [
    "flow_conservation[i in N]: sum( f[i,j] for (i,j) in A ) - sum( f[j,i] for (j,i) in A ) = s[i]",
    "capacity[A]: f[i,j] <= 1"
  ]
}
```

### Common Pitfalls
- Using a solver backend that does not support min-cost flow with integer capacities, requiring a fallback to MIP.
- Incorrectly setting the sink supply as a positive value; demand must be represented as negative supply.
- Assuming the algorithm handles negative cost cycles; some implementations require non-negative costs or additional preprocessing.

## Solving stage

### Strategy Overview
Implement the model using a library with a built-in min-cost flow solver (e.g., OR-Tools). The solver handles the integrality implicitly. Focus on correctly populating the graph, setting supplies, and interpreting the flow solution.

### Step 1 - Initialize Solver and Populate Graph
- Create a min-cost flow solver object (e.g., `SimpleMinCostFlow()`).
- Add each arc using `add_arc_with_capacity_and_unit_cost(tail, head, capacity=1, unit_cost)`.

### Step 2 - Set Node Supplies and Solve
- For each node `i`, set its supply using `set_node_supply(node_index, supply_value)`.
- Invoke the solver's `solve()` method.

### Step 3 - Check Feasibility and Extract Solution
- Check the solver's return status (e.g., `OPTIMAL` or `FEASIBLE`). Handle `INFEASIBLE` status appropriately.
- If feasible, iterate through all arcs. Arcs with `flow(arc_index) > 0` (typically exactly 1) are selected.

### Step 4 - Validate Path Structure
- Verify that the total flow equals the source supply (e.g., 1).
- Trace the path from source to sink using the selected arcs to ensure connectivity and flow conservation.

### Code Usage
```python
# build model from formulation
from ortools.graph import pywrapgraph

# Initialize solver
min_cost_flow = pywrapgraph.SimpleMinCostFlow()

# Add arcs with unit capacity
arc_indices = {}
for idx, (i, j) in enumerate(arcs):
    arc_idx = min_cost_flow.AddArcWithCapacityAndUnitCost(
        tail=i, head=j, capacity=1, unit_cost=cost_dict[(i,j)]
    )
    arc_indices[(i,j)] = arc_idx

# Set node supplies
min_cost_flow.SetNodeSupply(source_node, 1)
min_cost_flow.SetNodeSupply(sink_node, -1)
# All other nodes default to supply 0

# solve with status / termination checks
status = min_cost_flow.Solve()

if status == min_cost_flow.OPTIMAL or status == min_cost_flow.FEASIBLE:
    # Extract solution
    selected_arcs = []
    total_cost = min_cost_flow.OptimalCost()
    for (i,j), arc_idx in arc_indices.items():
        if min_cost_flow.Flow(arc_idx) > 0.5:
            selected_arcs.append((i,j))
    # Validate total flow
    assert sum(min_cost_flow.Flow(arc_idx) for arc_idx in arc_indices.values()) == 1
else:
    # Handle infeasibility
    raise Exception(f"Min-cost flow solver failed with status: {status}")
```

### Common Pitfalls
- Assuming the solver returns integer flows without verifying; while unit capacities enforce this, it's good practice to check.
- Not handling the case where the graph is disconnected, leading to an `INFEASIBLE` status.
- Misinterpreting the arc index returned by `AddArcWithCapacityAndUnitCost` when mapping back to the original arc.
