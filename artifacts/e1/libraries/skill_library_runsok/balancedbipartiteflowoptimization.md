---
name: BalancedBipartiteFlowOptimization
description: |
  Model and solve balanced bipartite flow problems (e.g., transportation) with linear costs using equality constraints for supply and demand, then solve via LP/MILP backends.
---

# Workflow 1 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Model the problem as a concrete Pyomo model with explicit sets, parameters, and constraint rules, leveraging the algebraic modeling language for clarity and maintainability.

### Step 1 - Define Sets and Parameters
- Define a set `I` for supply nodes (origins) and a set `J` for demand nodes (destinations).
- Create parameters `supply[i]`, `demand[j]`, and `cost[i,j]` to store problem data, using dictionaries or arrays for initialization.
- Verify that total supply equals total demand (`sum(supply) == sum(demand)`) to confirm a balanced problem.

### Step 2 - Create Decision Variables
- Define a non-negative continuous decision variable `x[i,j]` representing the flow from origin `i` to destination `j`. Use `domain=pyo.NonNegativeReals`.

### Step 3 - Formulate Supply and Demand Constraints
- For each origin `i`, add a constraint enforcing that the sum of outgoing flows equals its supply: `sum(x[i,j] for j in J) == supply[i]`.
- For each destination `j`, add a constraint enforcing that the sum of incoming flows equals its demand: `sum(x[i,j] for i in I) == demand[j]`.

### Step 4 - Define Linear Cost Objective
- Formulate the objective to minimize total cost: `minimize sum(cost[i,j] * x[i,j] for i in I for j in J)`.

### Formulation Template
```json
{
  "sets": ["I (origins)", "J (destinations)"],
  "parameters": ["supply[i]", "demand[j]", "cost[i,j]"],
  "decision_variables": ["x[i,j] (flow)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "sum(x[i,j] for j in J) == supply[i], for all i in I",
    "sum(x[i,j] for i in I) == demand[j], for all j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to verify supply-demand balance before using equality constraints, leading to infeasibility.
- Using inefficient data structures for parameter initialization in large problems; prefer indexed `Param` objects or dictionaries.
- Not explicitly setting the variable domain to non-negative, which can cause solver errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source LP/MILP solver (e.g., CBC, HiGHS) with configured options, followed by rigorous status checking and solution validation.

### Step 1 - Instantiate and Configure Solver
- Create a solver instance using `pyo.SolverFactory("solver_name")` (e.g., "cbc" or "highs").
- Set solver options for performance and reliability, such as time limit (`seconds`), optimality gap (`ratio`), and threads.

### Step 2 - Solve and Check Status
- Execute `results = solver.solve(model, tee=False)`.
- Check that `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible` before proceeding.

### Step 3 - Extract and Validate Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate over variables `model.x[i,j]` to get flow values, applying a tolerance (e.g., `> 1e-6`) to filter non-zero flows.
- Programmatically verify that supply and demand constraints are satisfied by recomputing sums and comparing to original parameters.

### Step 4 - Handle Failures Gracefully
- If the solver status indicates failure (e.g., `infeasible`, `error`), output a structured JSON with failure reason and status details for debugging.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (following Modeling stage steps)
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_origins))
model.J = pyo.Set(initialize=range(num_destinations))
model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
# ... add parameters, constraints, objective

# Solve
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

# Check status and extract solution
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    obj_val = pyo.value(model.obj)
    # Extract and verify flows
    for i in model.I:
        for j in model.J:
            val = pyo.value(model.x[i,j])
            if val > 1e-6:
                print(f"Flow from {i} to {j}: {val}")
else:
    print(f'{{"status": "failed", "reason": "{term}"}}')
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to extraction errors from infeasible models.
- Omitting post-solve numerical verification, which can miss modeling errors or numerical inaccuracies.
- Using verbose solver output (`tee=True`) in production, which clutters logs.

# Workflow 2 (OR-Tools LP Solver)

## Modeling stage

### Strategy Overview
Model the problem directly using the OR-Tools `pywraplp` linear programming API, creating variables and constraints via solver methods for a lightweight, procedural approach.

### Step 1 - Initialize Solver and Data
- Create a solver instance with `pywraplp.Solver.CreateSolver("GLOP")` for linear problems.
- Organize input data as lists/arrays: `supply[i]`, `demand[j]`, `cost[i][j]`. Check that `sum(supply) == sum(demand)`.

### Step 2 - Create Flow Variables with Bounds
- Create a dictionary of continuous flow variables `x[i,j]` using `solver.NumVar(lower_bound, upper_bound, name)`.
- Set lower bound to 0 and upper bound to `solver.infinity()` (or a specific capacity if applicable) to enforce non-negativity.

### Step 3 - Add Supply and Demand Equality Constraints
- For each origin `i`, create an equality constraint: `solver.Constraint(supply[i], supply[i])` and add coefficient 1 for all `x[i,j]` across destinations `j`.
- For each destination `j`, create an equality constraint: `solver.Constraint(demand[j], demand[j])` and add coefficient 1 for all `x[i,j]` across origins `i`.

### Step 4 - Set Linear Minimization Objective
- Create the objective with `solver.Objective()`.
- For each variable `x[i,j]`, set its coefficient to `cost[i][j]` using `SetCoefficient`.
- Call `SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["origins indices", "destinations indices"],
  "parameters": ["supply list", "demand list", "cost matrix"],
  "decision_variables": ["x[i,j] (solver.NumVar)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i,j])"
  },
  "constraints": [
    "sum(x[i,j] for j) == supply[i] for each i",
    "sum(x[i,j] for i) == demand[j] for each j"
  ]
}
```

### Common Pitfalls
- Incorrectly ordering nested loops when adding coefficients to constraints, leading to wrong constraint definitions.
- Not using the same variable object reference when setting objective coefficients, causing missing terms.
- Assuming solver defaults to non-negativity; always set lower bound explicitly.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools solver, check solution status, extract results, and perform verification to ensure correctness.

### Step 1 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check if the result status is `pywraplp.Solver.OPTIMAL` or `FEASIBLE`; proceed only if successful.

### Step 2 - Extract Objective and Variable Values
- Get the objective value via `objective.Value()`.
- Retrieve each variable's value using `x[i,j].solution_value()`.

### Step 3 - Verify Constraint Satisfaction
- For each origin `i`, sum the solution values `x[i,j]` over all `j` and compare to `supply[i]` within a tolerance (e.g., `1e-6`).
- Repeat for each destination `j`.
- Print only non-zero flows (`> 1e-6`) for clarity.

### Step 4 - Provide Structured Output
- Output the optimal cost and a summary of active flows.
- If the solver fails, output a JSON structure with status and error details.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver('GLOP')
x = {}
for i in range(num_origins):
    for j in range(num_destinations):
        x[i, j] = solver.NumVar(0, solver.infinity(), f'x_{i}_{j}')

# Supply constraints
for i in range(num_origins):
    constraint = solver.Constraint(supply[i], supply[i])
    for j in range(num_destinations):
        constraint.SetCoefficient(x[i, j], 1)

# Demand constraints
for j in range(num_destinations):
    constraint = solver.Constraint(demand[j], demand[j])
    for i in range(num_origins):
        constraint.SetCoefficient(x[i, j], 1)

# Objective
objective = solver.Objective()
for i in range(num_origins):
    for j in range(num_destinations):
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# Solve and check
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    print(f'Optimal cost: {objective.Value()}')
    for i in range(num_origins):
        for j in range(num_destinations):
            val = x[i, j].solution_value()
            if val > 1e-6:
                print(f'Flow from {i} to {j}: {val}')
    # Verification
    for i in range(num_origins):
        total = sum(x[i, j].solution_value() for j in range(num_destinations))
        assert abs(total - supply[i]) < 1e-6, f'Supply constraint {i} violated'
else:
    print(f'{{"status": "failed", "solver_status": {status}}}')
```

### Common Pitfalls
- Confusing `solver.Solve()` return status with solution optimality; always compare to `OPTIMAL` or `FEASIBLE` constants.
- Not using a tolerance when checking floating-point equality in verification, leading to false failures.
- Forgetting to call `SetCoefficient` for all variables in a constraint, resulting in incomplete constraints.
