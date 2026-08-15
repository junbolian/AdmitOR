---
name: Continuous Assignment with Capacity and Demand Constraints
description: |
  Model and solve linear assignment problems with resource capacities, task demands, per-assignment limits, and linear cost minimization using continuous decision variables.

---

# Workflow 1 (OR-Tools LP with pywraplp)

## Modeling stage

### Strategy Overview
Formulate the problem as a bipartite flow (transportation) linear program using Google OR-Tools' linear solver wrapper. This approach is efficient for medium-scale problems and provides a direct, low-level API for variable and constraint creation.

### Step 1 - Define Core Sets and Parameters
- Define sets for resources (e.g., `resources`) and tasks (e.g., `tasks`).
- Populate parameter dictionaries: `capacity[resource]`, `requirement[task]`, `cost[resource][task]`, and `assignment_limit[resource][task]`.

### Step 2 - Create Continuous Decision Variables
- Instantiate a solver object (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Create a non-negative continuous variable `x[i][j]` for each resource-task pair, with upper bound directly set to `assignment_limit[i][j]`.

### Step 3 - Formulate Capacity and Demand Constraints
- For each resource `i`, add a constraint: `sum(x[i][j] for j in tasks) <= capacity[i]`.
- For each task `j`, add an equality constraint: `sum(x[i][j] for i in resources) == requirement[j]`.

### Step 4 - Define Linear Cost Objective
- Create a linear objective expression: `sum(cost[i][j] * x[i][j] for i in resources for j in tasks)`.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": ["resources", "tasks"],
  "parameters": [
    {"name": "capacity", "index": "resources"},
    {"name": "requirement", "index": "tasks"},
    {"name": "cost", "index": ["resources", "tasks"]},
    {"name": "assignment_limit", "index": ["resources", "tasks"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["resources", "tasks"], "type": "continuous", "lower_bound": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in resources for j in tasks)"
  },
  "constraints": [
    {"name": "capacity", "expression": "sum(x[i][j] for j in tasks) <= capacity[i]", "index": "resources"},
    {"name": "demand", "expression": "sum(x[i][j] for i in resources) == requirement[j]", "index": "tasks"},
    {"name": "limit", "expression": "x[i][j] <= assignment_limit[i][j]", "index": ["resources", "tasks"]}
  ]
}
```

### Common Pitfalls
- Forgetting to check if the solver backend (`GLOP`) is available, leading to a `None` solver instance.
- Not accounting for floating-point precision when checking variable bounds or extracting non-zero assignments (use a tolerance like `1e-6`).
- Misindexing parameter dictionaries when building constraints, causing `KeyError` or incorrect model logic.

## Solving stage

### Strategy Overview
Solve the linear program using the OR-Tools wrapper, check solution status, extract results, and perform verification. This workflow provides a procedural, step-by-step control flow.

### Step 1 - Instantiate Solver and Set Options
- Create the solver instance with error handling for backend availability.
- Optionally set solver parameters like time limit or verbosity.

### Step 2 - Solve and Check Status
- Call `solver.Solve()`.
- Verify the result status is `OPTIMAL` or `FEASIBLE` before proceeding.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value.
- Iterate over all variables, extracting values greater than a small tolerance.
- Programmatically verify that the extracted solution satisfies all capacity, demand, and limit constraints.

### Step 4 - Output Structured Results
- Output the objective value in a standard format (e.g., `RESULT:{total_cost}`).
- Provide a detailed JSON payload containing solver status, objective value, and a list of non-zero assignments.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("GLOP")
if solver is None:
    raise RuntimeError("Solver backend not available.")

# Create variables with bounds
x = {}
for i in resources:
    for j in tasks:
        x[i, j] = solver.NumVar(0, assignment_limit[i][j], f"x_{i}_{j}")

# Add capacity constraints
for i in resources:
    ct = solver.Constraint(0, capacity[i])
    for j in tasks:
        ct.SetCoefficient(x[i, j], 1)

# Add demand constraints
for j in tasks:
    ct = solver.Constraint(requirement[j], requirement[j])
    for i in resources:
        ct.SetCoefficient(x[i, j], 1)

# Set objective
objective = solver.Objective()
for i in resources:
    for j in tasks:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    assignments = []
    for i in resources:
        for j in tasks:
            val = x[i, j].solution_value()
            if val > 1e-6:
                assignments.append({"resource": i, "task": j, "amount": val})
    # Verification (optional but recommended)
    # ...
    print(f"RESULT:{total_cost}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Assuming the solver status `OPTIMAL` means all constraints are perfectly satisfied; always verify against original data with tolerance.
- Not handling infeasible or unbounded statuses, causing crashes when accessing solution values.
- Extracting all variable values without a tolerance, resulting in verbose output with near-zero values.

---

# Workflow 2 (Pyomo with High-Level Solver)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling components, leveraging set-based declarations for clarity and scalability. This approach separates model definition from data, making it easy to test different instances.

### Step 1 - Declare Index Sets
- Define Pyomo `Set` objects for resources and tasks to index variables and constraints.

### Step 2 - Define Parameters as Model Components
- Use `Param` components (or plain dictionaries within rules) to hold `capacity`, `requirement`, `cost`, and `assignment_limit` data, indexed appropriately.

### Step 3 - Create Continuous Variables
- Declare a `Var` indexed over the Cartesian product of resource and task sets, with domain `NonNegativeReals`.

### Step 4 - Construct Constraints via Rules
- Define capacity, demand, and limit constraints using `Constraint` components with rule functions that reference the model's sets and parameters.

### Step 5 - Define the Objective
- Create an `Objective` component with the linear cost expression and sense set to minimize.

### Formulation Template
```json
{
  "sets": ["model.R", "model.T"],
  "parameters": [
    {"name": "model.capacity", "index": "model.R"},
    {"name": "model.requirement", "index": "model.T"},
    {"name": "model.cost", "index": ["model.R", "model.T"]},
    {"name": "model.limit", "index": ["model.R", "model.T"]}
  ],
  "decision_variables": [
    {"name": "model.x", "index": ["model.R", "model.T"], "type": "continuous", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum(model.cost[i,j] * model.x[i,j] for i in model.R for j in model.T)"
  },
  "constraints": [
    {"name": "model.capacity_con", "rule": "sum(model.x[i,j] for j in model.T) <= model.capacity[i]", "index": "model.R"},
    {"name": "model.demand_con", "rule": "sum(model.x[i,j] for i in model.R) == model.requirement[j]", "index": "model.T"},
    {"name": "model.limit_con", "rule": "model.x[i,j] <= model.limit[i,j]", "index": ["model.R", "model.T"]}
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's `ConcreteModel` (data immediate) with `AbstractModel` (data deferred), leading to initialization errors.
- Using Python's built-in `sum` inside rule functions instead of Pyomo's `summation` or generator expressions, which can cause performance issues or errors.
- Not ensuring parameter dictionaries are fully populated for all index combinations, causing `KeyError` during constraint construction.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a high-performance LP solver (e.g., HiGHS, CBC) via the `SolverFactory` interface. This workflow emphasizes solver-agnostic code, status checking, and solution verification.

### Step 1 - Select and Configure Solver
- Instantiate a solver via `SolverFactory` (e.g., `'highs'` for LP).
- Set options like time limit (`seconds`), optimality tolerance (`ratio`), and number of threads.

### Step 2 - Solve and Check Termination Conditions
- Call `solver.solve(model)`.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Verify Solution Values
- Access the objective value via `pyo.value(model.obj)`.
- Iterate over variables to extract non-zero assignments using a tolerance.
- Programmatically verify constraint satisfaction against the original data.

### Step 4 - Report Results and Handle Failures
- Output the objective value and a detailed assignment breakdown.
- If the solve fails, output the solver status and termination condition to aid debugging.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.R = pyo.Set(initialize=resources)
model.T = pyo.Set(initialize=tasks)

model.capacity = pyo.Param(model.R, initialize=capacity_dict)
model.requirement = pyo.Param(model.T, initialize=requirement_dict)
model.cost = pyo.Param(model.R, model.T, initialize=cost_dict)
model.limit = pyo.Param(model.R, model.T, initialize=limit_dict)

model.x = pyo.Var(model.R, model.T, domain=pyo.NonNegativeReals)

def capacity_rule(m, i):
    return sum(m.x[i, j] for j in m.T) <= m.capacity[i]
model.capacity_con = pyo.Constraint(model.R, rule=capacity_rule)

def demand_rule(m, j):
    return sum(m.x[i, j] for i in m.R) == m.requirement[j]
model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

def limit_rule(m, i, j):
    return m.x[i, j] <= m.limit[i, j]
model.limit_con = pyo.Constraint(model.R, model.T, rule=limit_rule)

model.obj = pyo.Objective(
    expr=sum(model.cost[i, j] * model.x[i, j] for i in model.R for j in model.T),
    sense=pyo.minimize
)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['seconds'] = 30
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    assignments = []
    for i in model.R:
        for j in model.T:
            val = pyo.value(model.x[i, j])
            if val > 1e-6:
                assignments.append({"resource": i, "task": j, "amount": val})
    print(f"RESULT:{total_cost}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `SolverStatus` and `TerminationCondition`, leading to misinterpretation of solver results (e.g., `ok` status with `infeasible` termination).
- Accessing variable values before verifying the solve was successful, causing `ValueError` or `AttributeError`.
- Using `pyo.value()` on an expression that hasn't been solved, which may return `None` or an uninitialized value.
