---
name: MinCostFlowSolver
description: |
  Model and solve minimum cost flow problems with supply/demand nodes and capacitated arcs using linear programming, with robust verification and error handling.
---

# Workflow 1 (Pyomo-CBC LP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling to separate problem structure from data, leveraging the CBC solver for linear programming. It is well-suited for medium-sized problems and emphasizes clean, declarative model construction.

### Step 1 - Define Network Sets and Parameters
- Define a Pyomo `Set` for nodes (e.g., `model.N`).
- Define a Pyomo `Set` for directed arcs as a subset of the Cartesian product of nodes (e.g., `model.A`).
- Define Pyomo `Param` objects for node net demand (`model.b`), arc cost (`model.c`), and arc capacity (`model.u`).

### Step 2 - Create Flow Variables
- Create a continuous decision variable `model.x` indexed by `model.A`.
- Set the variable domain to `NonNegativeReals`.
- Optionally, set upper bounds directly using the capacity parameter.

### Step 3 - Enforce Flow Conservation
- For each node `i` in `model.N`, add a constraint: `sum(model.x[j,i] for (j,i) in model.A) - sum(model.x[i,j] for (i,j) in model.A) == model.b[i]`.
- Ensure the constraint rule only sums over arcs that exist in the defined set `model.A`.

### Step 4 - Apply Arc Capacity Limits
- For each arc `(i,j)` in `model.A`, add a constraint: `model.x[i,j] <= model.u[i,j]`.

### Step 5 - Formulate Linear Cost Objective
- Define the objective to minimize: `sum(model.c[i,j] * model.x[i,j] for (i,j) in model.A)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (subset of N x N)"
  ],
  "parameters": [
    "b[i]: net demand (positive) or supply (negative) at node i",
    "c[(i,j)]: unit cost of flow on arc (i,j)",
    "u[(i,j)]: capacity limit of arc (i,j)"
  ],
  "decision_variables": [
    "x[(i,j)]: flow on arc (i,j), continuous, non-negative"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( c[(i,j)] * x[(i,j)] for (i,j) in A )"
  },
  "constraints": [
    "FlowConservation[i in N]: sum( x[(j,i)] for (j,i) in A ) - sum( x[(i,j)] for (i,j) in A ) == b[i]",
    "Capacity[(i,j) in A]: x[(i,j)] <= u[(i,j)]"
  ]
}
```

### Common Pitfalls
- Using generator expressions in constraint rules that assume all possible node pairs exist, leading to `KeyError` for missing arcs.
- Not verifying that the arcs set `A` is defined correctly before building constraints.
- Confusing net supply (negative `b[i]`) with net demand (positive `b[i]`) in the flow conservation equation.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via `SolverFactory`, with explicit configuration for time limits and optimality tolerance. Includes robust solution status checking and post-solution verification.

### Step 1 - Instantiate Solver and Set Options
- Create solver instance: `solver = SolverFactory('cbc')`.
- Configure options: `solver.options['seconds'] = <time_limit>`, `solver.options['ratio'] = <optimality_gap>`.

### Step 2 - Solve and Check Status
- Execute `results = solver.solve(model, tee=False)`.
- Check `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Extract and Filter Solution
- If solve was successful, retrieve objective value: `model.obj()`.
- Iterate over `model.x` to collect flows with values above a small tolerance (e.g., `1e-6`).

### Step 4 - Verify Solution Feasibility
- For each node, recompute `inflow - outflow` from solution values and compare to `model.b[i]` within a numerical tolerance.
- Log any significant violations for debugging.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 60
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
        obj_val = pyo.value(model.obj)
        # Extract non-zero flows
        flows = {(i,j): pyo.value(model.x[i,j]) for (i,j) in model.A if pyo.value(model.x[i,j]) > 1e-6}
        # Verification logic here
    else:
        raise Exception(f"Solver terminated with condition: {results.solver.termination_condition}")
else:
    raise Exception("Solver failed to execute.")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to errors when extracting from infeasible/unbounded models.
- Forgetting to call `pyo.value()` on the objective and variables to get numeric results.
- Using a zero tolerance without considering solver numerical precision, potentially missing small flows.

# Workflow 2 (OR-Tools GLOP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear programming solver (GLOP) directly, building the model imperatively. It is efficient for pure linear flow problems and offers a straightforward API for rapid prototyping.

### Step 1 - Initialize Solver and Data Structures
- Create solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Organize input data: dictionaries for `demand`, `cost`, `capacity`, and a list of directed arcs.

### Step 2 - Create Flow Variables with Bounds
- For each arc `(i,j)` in the arc list, create a variable: `x[(i,j)] = solver.NumVar(0, capacity[(i,j)], f'x_{i}_{j}')`.
- Store variables in a dictionary indexed by arc.

### Step 3 - Build Flow Conservation Constraints
- For each node `i`, create a constraint object: `ct = solver.Constraint(demand[i], demand[i])`.
- For each arc `(j,i)` where `i` is the destination, add `x[(j,i)]` to the constraint with coefficient `1`.
- For each arc `(i,j)` where `i` is the origin, add `x[(i,j)]` to the constraint with coefficient `-1`.

### Step 4 - Set Linear Cost Objective
- Create objective: `objective = solver.Objective()`.
- For each arc, set coefficient: `objective.SetCoefficient(x[(i,j)], cost[(i,j)])`.
- Set objective sense to minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "nodes: list of node identifiers",
    "arcs: list of directed arc tuples (i,j)"
  ],
  "parameters": [
    "demand[i]: net demand at node i (supply is negative demand)",
    "cost[(i,j)]: unit cost on arc",
    "capacity[(i,j)]: upper bound on flow"
  ],
  "decision_variables": [
    "x[(i,j)]: flow variable, continuous, bounded [0, capacity[(i,j)]]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[(i,j)] * x[(i,j)] for (i,j) in arcs )"
  },
  "constraints": [
    "FlowBalance[i]: sum( x[(j,i)] for (j,i) in arcs if destination==i ) - sum( x[(i,j)] for (i,j) in arcs if origin==i ) == demand[i]",
    "Capacity[(i,j)]: x[(i,j)] <= capacity[(i,j)] (enforced via variable bounds)"
  ]
}
```

### Common Pitfalls
- Incorrectly filtering arcs when building flow conservation constraints, leading to missing terms or accessing undefined variables.
- Setting variable bounds incorrectly (e.g., negative lower bound).
- Not handling the case where a node has no incoming or outgoing arcs, which should result in a sum of zero.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' GLOP solver, with direct access to solution values and simple status codes. Includes basic verification and error handling.

### Step 1 - Solve and Check Result Status
- Execute `solver.Solve()`.
- Check result status: `if status == pywraplp.Solver.OPTIMAL:` or `FEASIBLE`.

### Step 2 - Extract Objective and Flows
- Retrieve objective value: `objective.Value()`.
- Iterate over the arc list and collect variable values: `x[(i,j)].solution_value()`.

### Step 3 - Verify Flow Conservation
- Recompute net flow for each node using solution values.
- Compare against original demand within a tolerance (e.g., `1e-5`).

### Step 4 - Output Results
- Print objective value with a standard prefix (e.g., `RESULT:{objective_value}`).
- Optionally, print non-zero flows and verification summary.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... create variables, constraints, objective ...

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    obj_val = solver.Objective().Value()
    # Extract flows
    flows = {}
    for (i,j) in arcs:
        val = x[(i,j)].solution_value()
        if val > 1e-6:
            flows[(i,j)] = val
    # Verification logic here
    print(f"RESULT:{obj_val}")
else:
    raise Exception(f"Solver did not find optimal/feasible solution. Status: {status}")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid solutions.
- Assuming all arcs have a corresponding variable without verifying the dictionary was populated correctly.
- Neglecting to handle solver creation failure (e.g., `solver` is `None`).
