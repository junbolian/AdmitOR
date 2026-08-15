---
name: Network Flow with Node and Arc Capacities
description: |
  Model and solve network flow problems with arc capacities, node inflow capacities, and linear costs using structured data and solver-aware patterns.
---

# Workflow 1 (Dense Matrix Formulation with Bounded Variables)

## Modeling stage

### Strategy Overview
This workflow models the network flow problem using a dense, matrix-like representation, ideal for fully connected or small networks. It leverages variable bounds to implicitly enforce arc capacities, reducing the number of explicit constraints.

### Step 1 - Define Sets and Parameters
- Define a set of nodes (e.g., `NODES`).
- Define parameters: `net_demand[i]` (positive for demand, negative for supply), `node_capacity[i]`, `cost[i][j]`, and `arc_capacity[i][j]`. Use lists or 2D arrays for dense storage.
- Ensure all parameter matrices are fully populated for all `(i, j)` pairs, using a large value or zero for non-existent arcs.

### Step 2 - Create Flow Variables with Bounds
- Create a continuous, non-negative flow variable `x[i][j]` for each possible arc `(i, j)` where `i != j`.
- Set the variable's upper bound directly to `arc_capacity[i][j]` in the `NumVar` constructor to encode the arc capacity constraint implicitly.
- Store variables in a dictionary or 2D list keyed by `(i, j)`.

### Step 3 - Enforce Flow Conservation
- For each node `i`, create a flow conservation constraint: `sum(x[j][i] for j in NODES) - sum(x[i][j] for j in NODES) == net_demand[i]`.
- Use solver summation utilities for efficient expression building.

### Step 4 - Apply Node Capacity Constraints
- For each node `i`, create a constraint limiting total inflow: `sum(x[j][i] for j in NODES) <= node_capacity[i]`.
- This is an explicit constraint added to the model.

### Step 5 - Formulate Linear Cost Objective
- Define the objective as the sum of `cost[i][j] * x[i][j]` over all `(i, j)` pairs.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": ["NODES"],
  "parameters": {
    "net_demand": {"type": "float", "index": "NODES"},
    "node_capacity": {"type": "float", "index": "NODES"},
    "cost": {"type": "float", "index": ["NODES", "NODES"]},
    "arc_capacity": {"type": "float", "index": ["NODES", "NODES"]}
  },
  "decision_variables": {
    "x": {"type": "continuous", "index": ["NODES", "NODES"], "bounds": [0, "arc_capacity"]}
  },
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in NODES for j in NODES)"
  },
  "constraints": {
    "flow_conservation": "sum(x[j][i] for j in NODES) - sum(x[i][j] for j in NODES) == net_demand[i], for i in NODES",
    "node_capacity_bound": "sum(x[j][i] for j in NODES) <= node_capacity[i], for i in NODES"
  }
}
```

### Common Pitfalls
- Creating flow variables for `i == j` (self-loops), which wastes resources. Always skip these pairs.
- Using explicit `x[i][j] <= arc_capacity[i][j]` constraints instead of variable bounds, which unnecessarily increases model size.
- Forgetting to handle non-existent arcs in dense cost/capacity matrices, leading to unintended zero-cost or infinite-capacity routes.

## Solving stage

### Strategy Overview
Solve using a linear programming solver backend (e.g., GLOP, HiGHS) with a focus on efficient model building for dense networks and robust solution extraction.

### Step 1 - Select and Configure Solver
- Choose a pure LP solver like `GLOP` or `HiGHS` since variables are continuous.
- Set a time limit (e.g., `time_limit=30`) and enable parallel processing if supported (e.g., `threads=4`).

### Step 2 - Build Model Programmatically
- Use nested loops over `NODES` to create variables and objective coefficients.
- Use helper functions or list comprehensions with the solver's `Sum` method to build flow conservation and node capacity constraints efficiently.

### Step 3 - Solve and Check Status
- Invoke the solver and capture the status and termination condition.
- Proceed only if status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` by logging diagnostics and returning an empty solution.

### Step 4 - Extract and Filter Solution
- Iterate over all flow variables `x[i][j]`.
- Collect flows with value above a small tolerance (e.g., `1e-6`) into a solution dictionary.
- Compute the objective value from the solver.

### Step 5 - Verify Solution (Optional)
- Programmatically verify flow conservation and node capacity constraints are satisfied within tolerance.
- Perform sanity checks, such as comparing total supply with total demand.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
x = {}
for i in NODES:
    for j in NODES:
        if i != j:
            x[i, j] = solver.NumVar(0, arc_capacity[i][j], f'x_{i}_{j}')
# ... add constraints and objective ...

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    solution = {(i, j): x[i, j].solution_value() for i in NODES for j in NODES if i != j and x[i, j].solution_value() > 1e-6}
    obj_value = solver.Objective().Value()
else:
    # handle infeasible/unbounded
    solution = {}
    obj_value = None
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to extraction of invalid results.
- Using a loose tolerance for filtering zero flows, which can miss near-zero flows or include numerical noise.
- Omitting the verification step, which can let constraint violations go undetected in the final solution.

# Workflow 2 (Sparse Graph Formulation with Explicit Constraints)

## Modeling stage

### Strategy Overview
This workflow models the network as a sparse graph, creating variables and constraints only for existing arcs. It uses explicit constraints for all capacities, providing clarity and flexibility for post-solution analysis, and is suitable for large, sparse networks.

### Step 1 - Define Sparse Data Structures
- Define the set of nodes `NODES`.
- Store parameters in dictionaries keyed by arc tuple `(i, j)` for `cost`, `arc_capacity`, and by node for `net_demand` and `node_capacity`.
- Define a set `ARCS` containing only the tuples `(i, j)` for which an arc exists (i.e., where `cost` or `arc_capacity` is defined).

### Step 2 - Create Flow Variables for Existing Arcs
- For each arc `(i, j)` in `ARCS`, create a continuous, non-negative flow variable `x[i,j]` with no upper bound set at creation.
- Store variables in a dictionary keyed by `(i, j)`.

### Step 3 - Enforce Flow Conservation
- For each node `i`, create a flow conservation constraint: `sum(x[j,i] for j if (j,i) in ARCS) - sum(x[i,j] for j if (i,j) in ARCS) == net_demand[i]`.
- Use conditional sums over the sparse `ARCS` set.

### Step 4 - Apply Explicit Capacity Constraints
- For each arc `(i, j)` in `ARCS`, add an explicit arc capacity constraint: `x[i,j] <= arc_capacity[i,j]`.
- For each node `i`, add an explicit node capacity constraint: `sum(x[j,i] for j if (j,i) in ARCS) <= node_capacity[i]`.

### Step 5 - Formulate Linear Cost Objective
- Define the objective as the sum of `cost[i,j] * x[i,j]` over all arcs `(i, j)` in `ARCS`.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": ["NODES", "ARCS"],
  "parameters": {
    "net_demand": {"type": "float", "index": "NODES"},
    "node_capacity": {"type": "float", "index": "NODES"},
    "cost": {"type": "float", "index": "ARCS"},
    "arc_capacity": {"type": "float", "index": "ARCS"}
  },
  "decision_variables": {
    "x": {"type": "continuous", "index": "ARCS", "bounds": [0, null]}
  },
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for (i,j) in ARCS)"
  },
  "constraints": {
    "flow_conservation": "sum(x[j,i] for (j,i) in ARCS) - sum(x[i,j] for (i,j) in ARCS) == net_demand[i], for i in NODES",
    "arc_capacity_bound": "x[i,j] <= arc_capacity[i,j], for (i,j) in ARCS",
    "node_capacity_bound": "sum(x[j,i] for (j,i) in ARCS) <= node_capacity[i], for i in NODES"
  }
}
```

### Common Pitfalls
- Creating the `ARCS` set incorrectly, leading to missing variables or constraints for valid arcs.
- Using `Constraint.Skip` incorrectly in frameworks like Pyomo, which can break constraint indexing if not handled in the rule logic.
- Forgetting to include the node capacity constraint, which is a distinct requirement from arc capacities and flow conservation.

## Solving stage

### Strategy Overview
Solve using a MIP-capable solver (e.g., CBC, SCIP) configured for linear problems, with a focus on efficient handling of sparse constraints and detailed solution verification.

### Step 1 - Select and Configure Solver
- Choose a solver like `CBC` that handles sparse models efficiently.
- Set solver options: time limit (`seconds=30`), optimality gap (`ratio=0.0`), and threads (`threads=4`).

### Step 2 - Build Model Using Sparse Iteration
- Iterate over the `ARCS` set to create variables and arc capacity constraints.
- Iterate over `NODES` to create flow conservation and node capacity constraints, using list comprehensions to sum over relevant arcs.

### Step 3 - Solve and Validate Termination
- Invoke the solver and capture the solver status and termination condition.
- Check that the status is `ok` and the termination condition is `optimal` or `feasible` before solution extraction.

### Step 4 - Extract and Analyze Solution
- Extract the value for each flow variable `x[i,j]`.
- Filter and store non-zero flows (above tolerance).
- Compute the objective value and optionally the cost contribution per arc.

### Step 5 - Perform Comprehensive Verification
- Programmatically recompute inflows, outflows, and check flow conservation for each node against `net_demand`.
- Verify all arc and node capacity constraints are satisfied within a numerical tolerance.
- Log any violations for debugging.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.NODES = pyo.Set(initialize=NODES)
model.ARCS = pyo.Set(initialize=ARCS, dimen=2)
model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)
# ... add constraints and objective using Pyomo rules ...

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, options={'seconds': 30})
status = results.solver.status
term = results.solver.termination_condition

if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    solution = {(i, j): pyo.value(model.x[i, j]) for (i, j) in model.ARCS if pyo.value(model.x[i, j]) > 1e-6}
    obj_value = float(pyo.value(model.obj))
else:
    # handle unsuccessful solve
    solution = {}
    obj_value = None
```

### Common Pitfalls
- Assuming `SolverStatus.ok` alone guarantees a valid solution; always check the termination condition as well.
- Not using a tolerance when checking constraint satisfaction in verification, leading to false failures due to floating-point arithmetic.
- Extracting variable values without converting via `pyo.value()` or equivalent, which may return the variable object instead of its numerical value.
