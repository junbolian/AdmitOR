---
name: Continuous Resource-Constrained Production Planning
description: |
  Model and solve linear programs for maximizing profit subject to individual production limits and a shared linear resource constraint, using continuous decision variables.
---

# Workflow 1 (OR-Tools LP with GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear programming (LP) interface, directly constructing the model via the `pywraplp` API. It is well-suited for straightforward, medium-scale problems where a fast, dedicated LP solver (GLOP) is preferred, and the solution process is tightly controlled within a single Python script.

### Step 1 - Define Data Structures
- Organize problem data into parallel lists or dictionaries, indexed by item identifier.
- Store per-item parameters: unit profit, unit resource consumption, and maximum production capacity.
- Define the global resource capacity limit as a scalar.

### Step 2 - Instantiate Solver and Variables
- Create a GLOP solver instance using `pywraplp.Solver.CreateSolver('GLOP')`.
- Define continuous decision variables in a loop, using `solver.NumVar(lower_bound, upper_bound, name)` with a lower bound of 0 and an upper bound from the item's maximum production capacity.

### Step 3 - Formulate Objective Function
- Initialize a linear objective expression using `solver.Objective()`.
- In a loop, set the coefficient for each variable using `objective.SetCoefficient(variable, profit_per_unit)`.
- Set the objective sense to maximization.

### Step 4 - Add Constraints
- For the shared linear resource constraint, create a linear expression by summing `resource_consumption[i] * variable[i]` across all items, then add it via `solver.Add(expression <= total_capacity)`.
- Individual upper bound constraints are implicitly handled by the variable bounds defined in Step 2, but can be added explicitly if needed for clarity or post-solve analysis.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit[I] (unit profit)",
    "resource_consumption[I] (resource units per unit produced)",
    "max_production[I] (individual capacity limit)",
    "total_capacity (global resource limit)"
  ],
  "decision_variables": ["x[I] (production quantity, continuous)"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(resource_consumption[i] * x[i] for i in I) <= total_capacity",
    "x[i] <= max_production[i] for i in I",
    "x[i] >= 0 for i in I"
  ]
}
```

### Common Pitfalls
- Forgetting to verify the solver was created successfully (`if solver:` check).
- Not leveraging variable bounds to simplify the model, leading to redundant constraints.
- Assuming the solver always returns an optimal solution without checking the result status.

## Solving stage

### Strategy Overview
The solving stage focuses on executing the model with the GLOP solver, rigorously checking the solution status, extracting results, and performing post-solve validation and analysis to ensure correctness and interpretability.

### Step 1 - Execute Solver and Check Status
- Call `solver.Solve()` and capture the result status.
- Check if the status is `pywraplp.Solver.OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses with informative error messages.

### Step 2 - Extract and Validate Solution
- If optimal/feasible, loop through variables and extract their `.solution_value()`.
- Validate the solution by recalculating total resource usage and verifying it does not exceed the capacity (within a small tolerance).
- Verify that each production quantity respects its individual upper bound.

### Step 3 - Analyze Solution Structure
- Calculate the total profit achieved.
- Identify which items are produced at their maximum capacity (`binding_upper_bounds`).
- Compute the profit-to-resource-consumption ratio for each item; the optimal solution typically prioritizes items with higher ratios until the resource constraint binds.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
if not solver:
    raise Exception('Solver initialization failed')

# Variable creation example
x = {}
for i in items:
    x[i] = solver.NumVar(0, max_production[i], f'x_{i}')

# Objective
objective = solver.Objective()
for i in items:
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# Resource constraint
constraint_expr = sum(resource_consumption[i] * x[i] for i in items)
solver.Add(constraint_expr <= total_capacity)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    solution = {i: x[i].solution_value() for i in items}
    total_resource_used = sum(resource_consumption[i] * solution[i] for i in items)
    # Validation and analysis...
else:
    print(f'Solver did not find an optimal solution. Status: {status}')
```

### Common Pitfalls
- Extracting solution values without first confirming a feasible status, leading to errors.
- Using loose tolerances for solution validation, potentially missing constraint violations.
- Omitting post-solve analysis, which is crucial for understanding the driver of the optimal solution (e.g., binding resource constraint).

# Workflow 2 (Pyomo with CBC/GLPK/HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to declaratively define the optimization model. It separates data from model structure, enhancing clarity and scalability for larger problems. It supports multiple open-source solvers (e.g., CBC, GLPK, HiGHS) via a unified interface, facilitating solver fallback and comparison.

### Step 1 - Organize Data with Pyomo Components
- Define an indexed `Set` for all items.
- Store input data as `pyo.Param` objects indexed by the item set (e.g., `profit`, `resource_consumption`, `max_production`). This cleanly separates data from model logic.

### Step 2 - Declare Model and Variables
- Instantiate a `pyo.ConcreteModel()`.
- Define a continuous `pyo.Var` for production quantity, indexed by the item set, with a domain of `pyo.NonNegativeReals`. Individual upper bounds can be set later within constraints.

### Step 3 - Define Objective Function
- Use a `pyo.Objective` component with a rule that sums `profit[i] * x[i]` across all items.
- Explicitly set the sense to `pyo.maximize`.

### Step 4 - Add Constraints Declaratively
- For the global resource constraint, create a single `pyo.Constraint` with a rule that sums `resource_consumption[i] * x[i]` and ensures it is `<= total_capacity`.
- For individual upper bounds, create an indexed `pyo.Constraint` over the item set, where the rule for each item is `x[i] <= max_production[i]`.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit[I] (unit profit, Pyomo Param)",
    "resource_consumption[I] (resource units per unit produced, Pyomo Param)",
    "max_production[I] (individual capacity limit, Pyomo Param)",
    "total_capacity (global resource limit, scalar)"
  ],
  "decision_variables": ["model.x[I] (production quantity, Var, NonNegativeReals)"],
  "objective": {
    "sense": "max",
    "expression": "sum(model.profit[i] * model.x[i] for i in model.I)"
  },
  "constraints": [
    "model.resource_constraint: sum(model.resource_consumption[i] * model.x[i] for i in model.I) <= total_capacity",
    "model.capacity_constraints[i]: model.x[i] <= model.max_production[i] for i in model.I"
  ]
}
```

### Common Pitfalls
- Confusing `ConcreteModel` (instantiated with data) with `AbstractModel` (requires data later).
- Forgetting to initialize `Param` objects, leading to model construction errors.
- Defining constraints with incorrect indexing, resulting in missing or extra constraints.

## Solving stage

### Strategy Overview
The solving stage leverages Pyomo's `SolverFactory` to interface with various LP solvers. It implements robust solver fallback logic, detailed solution status checking, and post-solution validation and analysis to ensure reliable results.

### Step 1 - Configure and Execute Solver with Fallback
- Create a solver instance via `SolverFactory('solver_name')` (e.g., 'cbc', 'glpk', 'highs').
- Set solver-specific options (e.g., time limit, tolerance).
- Implement a fallback loop: if the primary solver fails or is unavailable, try the next configured alternative.

### Step 2 - Check Solution Status and Load Results
- Solve the model with `load_solutions=False` to separate solving from result loading.
- Inspect both `results.solver.status` and `results.solver.termination_condition`.
- Only load the solution into the model object (`model.solutions.load_from(results)`) if the status indicates optimality or feasibility.

### Step 3 - Validate and Analyze Solution
- Extract variable values using `pyo.value(model.x[i])`.
- Recalculate total resource usage and profit to validate against constraints and objective.
- Perform efficiency analysis by sorting items by `profit[i]/resource_consumption[i]` to verify the solution logic matches expected economic principles.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=item_indices)

model.profit = pyo.Param(model.I, initialize=profit_data)
model.resource_consumption = pyo.Param(model.I, initialize=resource_consumption_data)
model.max_production = pyo.Param(model.I, initialize=max_production_data)

model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)

def obj_rule(m):
    return sum(m.profit[i] * m.x[i] for i in m.I)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

def resource_rule(m):
    return sum(m.resource_consumption[i] * m.x[i] for i in m.I) <= total_capacity
model.resource_constraint = pyo.Constraint(rule=resource_rule)

def capacity_rule(m, i):
    return m.x[i] <= m.max_production[i]
model.capacity_constraints = pyo.Constraint(model.I, rule=capacity_rule)

# solve with status / termination checks
solver_names = ['cbc', 'glpk', 'highs']
solved = False
results = None

for name in solver_names:
    solver = pyo.SolverFactory(name)
    if solver.available():
        solver.options['seconds'] = time_limit
        results = solver.solve(model, tee=verbose, load_solutions=False)
        if results.solver.status in [pyo.SolverStatus.ok, pyo.SolverStatus.warning] and \
           results.solver.termination_condition == pyo.TerminationCondition.optimal:
            solved = True
            break

if solved:
    model.solutions.load_from(results)
    solution = {i: pyo.value(model.x[i]) for i in model.I}
    # Validation and analysis...
else:
    print('No solver found an optimal solution.')
```

### Common Pitfalls
- Loading solutions without checking termination conditions, potentially loading suboptimal or infeasible points.
- Not using `load_solutions=False`, which can cause confusion if the solve fails.
- Assuming a specific solver (e.g., 'glpk') is always available without checking `.available()` first.
