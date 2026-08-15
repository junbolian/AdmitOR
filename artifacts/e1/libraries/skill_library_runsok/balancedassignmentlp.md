---
name: BalancedAssignmentLP
description: |
  Model and solve balanced resource-to-task assignment problems with linear costs, supply-demand equality, and per-assignment capacity limits using continuous variables.
---

# Workflow 1 (Google OR-Tools LP)

## Modeling stage

### Strategy Overview
Formulate the problem as a balanced transportation linear program (LP) using the OR-Tools linear solver wrapper. This approach is suitable for problems with divisible resources (e.g., hours, materials) where the total supply equals total demand.

### Step 1 - Define Core Sets and Data
- Identify the two sets: `RESOURCES` (e.g., persons, machines) and `TASKS` (e.g., projects, jobs).
- Define parameters: `resource_capacity[i]` (total supply per resource), `task_requirement[j]` (total demand per task), `unit_cost[i][j]` (cost per unit assigned), and `max_assignment[i][j]` (upper bound per resource-task pair).
- Verify the balance condition: `sum(resource_capacity) == sum(task_requirement)`.

### Step 2 - Create Continuous Assignment Variables
- For each `i` in `RESOURCES` and `j` in `TASKS`, create a continuous decision variable `x[i,j]`.
- Set the variable's lower bound to 0 and its upper bound to `max_assignment[i][j]`.

### Step 3 - Enforce Supply and Demand Constraints
- **Supply Constraints**: For each resource `i`, enforce `sum(x[i,j] for all j) == resource_capacity[i]`.
- **Demand Constraints**: For each task `j`, enforce `sum(x[i,j] for all i) == task_requirement[j]`.

### Step 4 - Formulate Linear Cost Objective
- Define the objective to minimize total cost: `minimize sum(unit_cost[i][j] * x[i,j] for all i, j)`.

### Formulation Template
```json
{
  "sets": [
    "RESOURCES",
    "TASKS"
  ],
  "parameters": [
    "resource_capacity[RESOURCES]",
    "task_requirement[TASKS]",
    "unit_cost[RESOURCES][TASKS]",
    "max_assignment[RESOURCES][TASKS]"
  ],
  "decision_variables": [
    "x[RESOURCES][TASKS] (continuous, >=0)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(unit_cost[i][j] * x[i][j] for i in RESOURCES, j in TASKS)"
  },
  "constraints": [
    "supply(i): sum(x[i][j] for j in TASKS) == resource_capacity[i] for each i in RESOURCES",
    "demand(j): sum(x[i][j] for i in RESOURCES) == task_requirement[j] for each j in TASKS",
    "capacity(i,j): x[i][j] <= max_assignment[i][j] for each i in RESOURCES, j in TASKS"
  ]
}
```

### Common Pitfalls
- Forgetting to verify total supply equals total demand, leading to infeasibility.
- Setting `max_assignment[i][j]` too low such that demand cannot be met.
- Using integer variables unnecessarily when resources are divisible, which slows solving.

## Solving stage

### Strategy Overview
Build and solve the model using the `pywraplp` interface of Google OR-Tools. This workflow is efficient for prototyping and solving medium-sized LPs with a clean, imperative API.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance (e.g., `solver = pywraplp.Solver.CreateSolver('GLOP')`).
- Store indices in lists (e.g., `resources = range(num_resources)`, `tasks = range(num_tasks)`).
- Load parameter data into lists or dictionaries.

### Step 2 - Build Variables and Model
- Create variables in nested loops using `solver.NumVar(lb, ub, name)`.
- Add supply, demand, and capacity constraints by creating constraint objects and setting coefficients.
- Set the objective by adding all variable-cost products.

### Step 3 - Solve and Check Status
- Invoke `solver.Solve()`.
- Check the result status (`OPTIMAL` or `FEASIBLE`) before extracting values.
- Implement a time limit using `solver.SetTimeLimit()` for robustness.

### Step 4 - Extract and Validate Solution
- Retrieve variable values for non-zero assignments.
- Programmatically verify that supply and demand constraints are satisfied within a small tolerance.
- Output the objective value and a summary of assignments.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')
if not solver:
    raise Exception('Solver not available.')

# 2. Define data (placeholders)
resources = list(range(num_resources))
tasks = list(range(num_tasks))
resource_capacity = [...]  # list length num_resources
task_requirement = [...]   # list length num_tasks
unit_cost = [[...], ...]  # matrix [resource][task]
max_assignment = [[...], ...]  # matrix [resource][task]

# 3. Create variables
x = {}
for i in resources:
    for j in tasks:
        x[i, j] = solver.NumVar(0, max_assignment[i][j], f'x_{i}_{j}')

# 4. Add supply constraints
for i in resources:
    constraint = solver.Constraint(resource_capacity[i], resource_capacity[i])
    for j in tasks:
        constraint.SetCoefficient(x[i, j], 1)

# 5. Add demand constraints
for j in tasks:
    constraint = solver.Constraint(task_requirement[j], task_requirement[j])
    for i in resources:
        constraint.SetCoefficient(x[i, j], 1)

# 6. Set objective
objective = solver.Objective()
for i in resources:
    for j in tasks:
        objective.SetCoefficient(x[i, j], unit_cost[i][j])
objective.SetMinimization()

# 7. Solve with time limit
solver.SetTimeLimit(solve_time_limit_ms)
result_status = solver.Solve()

# 8. Check status and extract solution
if result_status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'RESULT:{objective.Value()}')
    # Extract non-zero assignments
    for i in resources:
        for j in tasks:
            val = x[i, j].solution_value()
            if val > 1e-6:
                print(f'Assignment {i}->{j}: {val}')
else:
    print('No optimal solution found.')
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing valid solutions.
- Omitting time limits, risking hangs on pathological instances.
- Failing to verify solution feasibility numerically (e.g., using tolerances for floating-point comparisons).

# Workflow 2 (Pyomo with LP Solver)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling environment, separating problem specification from solver execution. This approach is ideal for integration into larger Python workflows, research, or when solver independence is desired.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for `RESOURCES` and `TASKS`.
- Declare `Param` objects for `resource_capacity`, `task_requirement`, `unit_cost`, and `max_assignment`, indexed appropriately.

### Step 2 - Define Continuous Decision Variables
- Create a Pyomo `Var` object `x`, indexed over `RESOURCES × TASKS`, with domain `pyo.NonNegativeReals`.

### Step 3 - Construct Constraints via Rules
- Implement a rule for supply constraints returning `sum(x[i,j] for j) == resource_capacity[i]`.
- Implement a rule for demand constraints returning `sum(x[i,j] for i) == task_requirement[j]`.
- Implement a rule for capacity constraints returning `x[i,j] <= max_assignment[i,j]`.

### Step 4 - Formulate Objective Expression
- Define the objective using Pyomo's `Objective` with `sense=pyo.minimize` and expression `sum(unit_cost[i,j] * x[i,j] for i,j)`.

### Formulation Template
```json
{
  "sets": [
    "m.RESOURCES",
    "m.TASKS"
  ],
  "parameters": [
    "m.resource_capacity(m.RESOURCES)",
    "m.task_requirement(m.TASKS)",
    "m.unit_cost(m.RESOURCES, m.TASKS)",
    "m.max_assignment(m.RESOURCES, m.TASKS)"
  ],
  "decision_variables": [
    "m.x(m.RESOURCES, m.TASKS, domain=NonNegativeReals)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(m.unit_cost[i,j] * m.x[i,j] for i in m.RESOURCES, j in m.TASKS)"
  },
  "constraints": [
    "supply(i): sum(m.x[i,j] for j in m.TASKS) == m.resource_capacity[i]",
    "demand(j): sum(m.x[i,j] for i in m.RESOURCES) == m.task_requirement[j]",
    "capacity(i,j): m.x[i,j] <= m.max_assignment[i,j]"
  ]
}
```

### Common Pitfalls
- Using concrete models without first validating data, leading to instantiation errors.
- Confusing 1‑based and 0‑based indexing when populating Pyomo parameters.
- Not leveraging Pyomo's ability to check constraint duals for sensitivity analysis.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with concrete data, then solve it using an LP solver (e.g., CBC, HiGHS) via the `SolverFactory`. This workflow emphasizes solver agnosticism and detailed solution inspection.

### Step 1 - Instantiate Model with Data
- Create a concrete model instance.
- Populate all `Set` and `Param` objects with the problem data.

### Step 2 - Configure and Execute Solver
- Create a solver object using `SolverFactory('solver_name')`.
- Set solver options (e.g., `time_limit`, `presolve='on'`).
- Call `solver.solve(model)` and capture the result object.

### Step 3 - Validate Termination and Solution
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal`).
- If optimal, extract variable values via `model.x[i,j].value`.
- Programmatically verify constraint satisfaction.

### Step 4 - Report Standardized Output
- Print the objective value in a parseable format (e.g., `RESULT:{value}`).
- Output a matrix or list of non-zero assignments for validation.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Create concrete model
model = pyo.ConcreteModel()

# 2. Define sets (placeholder data)
model.RESOURCES = pyo.Set(initialize=range(num_resources))
model.TASKS = pyo.Set(initialize=range(num_tasks))

# 3. Define parameters (placeholder data)
def resource_capacity_init(model, i):
    return resource_capacity_data[i]  # user-defined
model.resource_capacity = pyo.Param(model.RESOURCES, initialize=resource_capacity_init)

def task_requirement_init(model, j):
    return task_requirement_data[j]  # user-defined
model.task_requirement = pyo.Param(model.TASKS, initialize=task_requirement_init)

# Similarly initialize model.unit_cost and model.max_assignment as indexed Params

# 4. Define variables
model.x = pyo.Var(model.RESOURCES, model.TASKS, domain=pyo.NonNegativeReals)

# 5. Define objective
model.obj = pyo.Objective(
    expr=sum(model.unit_cost[i,j] * model.x[i,j] for i in model.RESOURCES for j in model.TASKS),
    sense=pyo.minimize
)

# 6. Define constraints via rules
def supply_rule(model, i):
    return sum(model.x[i,j] for j in model.TASKS) == model.resource_capacity[i]
model.supply_constraint = pyo.Constraint(model.RESOURCES, rule=supply_rule)

def demand_rule(model, j):
    return sum(model.x[i,j] for i in model.RESOURCES) == model.task_requirement[j]
model.demand_constraint = pyo.Constraint(model.TASKS, rule=demand_rule)

def capacity_rule(model, i, j):
    return model.x[i,j] <= model.max_assignment[i,j]
model.capacity_constraint = pyo.Constraint(model.RESOURCES, model.TASKS, rule=capacity_rule)

# 7. Solve
solver = pyo.SolverFactory('cbc')  # or 'highs', 'glpk'
solver.options['seconds'] = time_limit
results = solver.solve(model)

# 8. Check solution status
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    print(f'RESULT:{pyo.value(model.obj)}')
    # Extract and print non-zero assignments
    for i in model.RESOURCES:
        for j in model.TASKS:
            val = pyo.value(model.x[i,j])
            if val > 1e-6:
                print(f'Assignment {i}->{j}: {val}')
else:
    print('Solver did not find an optimal solution.')
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially accepting suboptimal or incomplete solutions.
- Using `pyo.value()` on uninitialized variables after a failed solve.
- Forgetting to set `presolve='on'` for LP solvers, missing performance gains.
