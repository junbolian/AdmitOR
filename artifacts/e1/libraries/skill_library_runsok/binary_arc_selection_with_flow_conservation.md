---
name: Binary Arc Selection with Flow Conservation
description: |
  Model and solve binary arc selection problems with flow conservation constraints using either specialized network flow solvers or general-purpose MILP solvers.
---

# Workflow 1 (Specialized Network Flow Solver)

## Modeling stage

### Strategy Overview
This workflow leverages a min-cost flow formulation, recognizing that binary arc selection with unit flow from a single source to a single sink is equivalent to a shortest path problem. It uses a specialized solver (e.g., OR-Tools MinCostFlow) which is highly efficient for this class of problems.

### Step 1 - Map Problem to Network Flow Structure
- Identify the set of nodes and the set of directed arcs connecting them.
- Define a cost parameter for each arc, typically stored in a dictionary keyed by (from_node, to_node).
- Determine the source node (supply = 1) and sink node (demand = 1) for a single unit of flow.

### Step 2 - Encode Binary Selection via Unit Capacities
- Represent the binary arc selection decision by setting the capacity of each arc to 1.
- This ensures each arc can be used at most once, enforcing the binary nature without explicit binary variables.

### Step 3 - Formalize Flow Conservation
- For the source node, set a net supply of 1.
- For the sink node, set a net demand of 1 (or supply of -1).
- For all intermediate (transshipment) nodes, enforce a net supply of 0, ensuring flow balance.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i,j ∈ N"
  ],
  "parameters": [
    "c_{ij}: cost of using arc (i,j) for (i,j) ∈ A",
    "source: node with net supply of 1",
    "sink: node with net demand of 1"
  ],
  "decision_variables": [
    "f_{ij}: flow on arc (i,j) (continuous, bounded by [0,1])"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j) ∈ A} c_{ij} * f_{ij}"
  },
  "constraints": [
    "Flow Balance: ∑_{j: (i,j) ∈ A} f_{ij} - ∑_{j: (j,i) ∈ A} f_{ji} = supply_i, ∀ i ∈ N, where supply_source = 1, supply_sink = -1, supply_i = 0 otherwise.",
    "Capacity: 0 ≤ f_{ij} ≤ 1, ∀ (i,j) ∈ A"
  ]
}
```

### Common Pitfalls
- Incorrectly setting node supplies (e.g., using positive demand for sink instead of negative supply).
- Forgetting to exclude self-loop arcs unless explicitly part of the problem.
- Assuming the solver automatically handles infeasible instances; always check solver status.

## Solving stage

### Strategy Overview
Solve the formulated min-cost flow problem using a dedicated, efficient algorithm (e.g., OR-Tools SimpleMinCostFlow). This stage focuses on correctly interfacing with the solver API, checking solution status, and extracting the selected path.

### Step 1 - Initialize Solver and Add Graph Data
- Instantiate the specialized flow solver object.
- Add each arc to the solver, specifying its tail node, head node, capacity (1), and unit cost.

### Step 2 - Set Node Supplies
- Iterate over all nodes.
- Call the solver's method to set the supply for the source node to 1, the sink node to -1, and all other nodes to -1.

### Step 3 - Solve and Validate Status
- Invoke the solver's `solve()` method.
- Check the returned status (e.g., `OPTIMAL`, `INFEASIBLE`, `UNBALANCED`). Proceed only if the status indicates an optimal solution was found.

### Step 4 - Extract and Interpret Solution
- Iterate over all arcs and query the flow value on each.
- Arcs with a flow value greater than a small tolerance (e.g., 0.5) constitute the selected path from source to sink.
- Sum the cost of selected arcs to obtain the total cost, or retrieve it directly from the solver if available.

### Code Usage
```python
# Example using OR-Tools SimpleMinCostFlow
from ortools.graph.python import min_cost_flow

# 1. Initialize solver
smcf = min_cost_flow.SimpleMinCostFlow()

# 2. Add arcs (tail, head, capacity, unit cost)
for (i, j), cost in arc_costs.items():
    arc_index = smcf.add_arc_with_capacity_and_unit_cost(i, j, 1, cost)

# 3. Set node supplies
for node in nodes:
    supply = 1 if node == source else (-1 if node == sink else 0)
    smcf.set_node_supply(node, supply)

# 4. Solve and check status
status = smcf.solve()
if status == smcf.OPTIMAL:
    # 5. Extract solution
    total_cost = smcf.optimal_cost()
    selected_arcs = []
    for arc_idx in range(smcf.num_arcs()):
        if smcf.flow(arc_idx) > 0.5:  # Flow is 1 for selected arcs
            tail = smcf.tail(arc_idx)
            head = smcf.head(arc_idx)
            selected_arcs.append((tail, head))
else:
    raise Exception(f"Solver did not find optimal solution. Status: {status}")
```

### Common Pitfalls
- Not checking solver status before extracting results, leading to runtime errors.
- Misinterpreting flow values due to numerical tolerance; use a clear threshold.
- Assuming the solver's internal arc indexing matches the original problem's arc ordering.

# Workflow 2 (General-Purpose MILP Solver)

## Modeling stage

### Strategy Overview
This workflow formulates the problem as a Mixed-Integer Linear Program (MILP) using explicit binary variables for arc selection and flow balance constraints. It is solver-agnostic, compatible with Gurobi, CPLEX, HiGHS, etc., and is easily extended to more complex variants (e.g., multiple commodities, fixed charges).

### Step 1 - Define Explicit Binary Decision Variables
- Create a binary variable `y_{ij}` for each arc `(i,j)`, representing whether the arc is selected.
- Optionally, define a continuous flow variable `f_{ij}` bounded by the selection variable.

### Step 2 - Formulate Flow Conservation Constraints
- For the source node, enforce that net outflow equals the total demand (e.g., 1).
- For the sink node, enforce that net inflow equals the total demand.
- For all intermediate nodes, enforce that total inflow equals total outflow.

### Step 3 - Link Flow to Binary Selection
- Add linking constraints: `f_{ij} <= M * y_{ij}`, where `M` is an upper bound on flow (e.g., the demand amount, which is 1 for unit flow problems).
- For pure binary selection problems, the flow variable can be omitted, and the binary variable directly represents unit flow.

### Step 4 - Construct Linear Objective
- Define the objective as the minimization of the sum of arc costs multiplied by their respective selection (or flow) variables.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i,j ∈ N and i != j (no self-loops)"
  ],
  "parameters": [
    "c_{ij}: cost of selecting arc (i,j) for (i,j) ∈ A",
    "source: origin node",
    "sink: destination node",
    "demand: required flow from source to sink (typically 1)"
  ],
  "decision_variables": [
    "y_{ij}: binary, 1 if arc (i,j) is selected, 0 otherwise"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j) ∈ A} c_{ij} * y_{ij}"
  },
  "constraints": [
    "Path Continuity (Source): ∑_{j: (source,j) ∈ A} y_{source,j} - ∑_{j: (j,source) ∈ A} y_{j,source} = demand",
    "Path Continuity (Sink): ∑_{j: (j,sink) ∈ A} y_{j,sink} - ∑_{j: (sink,j) ∈ A} y_{sink,j} = demand",
    "Flow Balance (Intermediate): ∑_{j: (i,j) ∈ A} y_{i,j} = ∑_{j: (j,i) ∈ A} y_{j,i}, ∀ i ∈ N \\ {source, sink}",
    "Binary: y_{ij} ∈ {0, 1}, ∀ (i,j) ∈ A"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops from the arc set, which can lead to nonsensical solutions.
- Using an unnecessarily large `M` in linking constraints, which weakens the LP relaxation.
- Incorrectly signing the flow balance constraints for source and sink nodes.

## Solving stage

### Strategy Overview
Solve the MILP model using a general-purpose solver via a modeling framework (e.g., Pyomo, PuLP). This involves configuring solver parameters, executing the solve, rigorously checking termination status, and extracting the binary solution.

### Step 1 - Build Model Using a Modeling Framework
- Instantiate a concrete model object.
- Define sets, parameters, variables, objective, and constraints according to the formulation.

### Step 2 - Configure Solver and Execute
- Select an appropriate MILP solver (e.g., HiGHS, Gurobi, CBC).
- Set solver parameters such as time limit, optimality gap tolerance (MIPGap), and number of threads.
- Call the solver's `solve()` method on the model.

### Step 3 - Check Solver Status and Termination Condition
- Verify the solver status indicates a normal completion (e.g., `ok`).
- Check the termination condition confirms optimality (or acceptable feasibility).

### Step 4 - Extract and Validate Solution
- Retrieve the objective value.
- Iterate over the binary variables, collecting those with a value greater than 0.5 into the set of selected arcs.
- Perform a sanity check, such as verifying the selected arcs form a valid path from source to sink.

### Code Usage
```python
# Example using Pyomo with a generic MILP solver
import pyomo.environ as pyo

# 1. Build Model
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(within=model.N * model.N, initialize=arcs)  # arcs is a list of (i,j) tuples
model.c = pyo.Param(model.A, initialize=arc_costs)  # arc_costs dict
model.source = pyo.Param(initialize=source_node)
model.sink = pyo.Param(initialize=sink_node)
model.demand = pyo.Param(initialize=1)

model.y = pyo.Var(model.A, within=pyo.Binary)  # Binary selection variables

# Objective
def obj_rule(m):
    return pyo.sum(m.c[i,j] * m.y[i,j] for (i,j) in m.A)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Constraints (Flow Balance)
def source_balance_rule(m, i):
    if i == m.source:
        return pyo.sum(m.y[i,j] for (i,j) in m.A if i == m.source) - pyo.sum(m.y[j,i] for (j,i) in m.A if i == m.source) == m.demand
    return pyo.Constraint.Skip
model.source_con = pyo.Constraint(model.N, rule=source_balance_rule)

# ... Similar rules for sink and intermediate nodes ...

# 2. Solve
solver = pyo.SolverFactory('highs')  # or 'gurobi', 'cbc'
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model)

# 3. Check Status
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    # 4. Extract Solution
    total_cost = pyo.value(model.obj)
    selected_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.y[i,j]) > 0.5]
else:
    raise Exception("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`); both must be checked.
- Extracting variable values without first checking solution availability, leading to errors.
- Not parameterizing source, sink, and demand, making the model less reusable.
