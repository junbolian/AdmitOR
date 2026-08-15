---
name: Bounded Linear Production Planning
description: |
  Model and solve linear production planning problems with bounded decision variables, linear profit objectives, and resource capacity constraints using structured formulation and solver-aware implementation.
---

# Workflow 1 (Solver-Specific API - OR-Tools/GLOP)

## Modeling stage

### Strategy Overview
This workflow uses a solver-specific API (e.g., OR-Tools) where the model is built directly within the solver's object model. It is efficient for pure Linear Programming (LP) problems with continuous variables and explicit bounds.

### Step 1 - Define Bounded Decision Variables
- Identify each product/item requiring a production quantity. For each, define a continuous decision variable with explicit lower and upper bounds (e.g., `min_production[i]` and `max_production[i]`).
- Use the solver's native `NumVar` method to create variables with bounds directly, avoiding separate bound constraints.

### Step 2 - Formulate Linear Profit Objective
- Define a linear objective to maximize total profit. Sum the product of profit per unit (`profit[i]`) and the production quantity variable across all items.
- Use the solver's `Objective()` method to set up the expression and specify maximization.

### Step 3 - Add Aggregate Resource Constraints
- For each shared, limited resource (e.g., machine hours), create a linear inequality constraint.
- The constraint sums the resource consumption (`resource_use_per_unit[i] * x[i]`) across all products and ensures it does not exceed the total resource capacity.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": [
    {"name": "profit", "set": "products"},
    {"name": "min_production", "set": "products"},
    {"name": "max_production", "set": "products"},
    {"name": "resource_use_per_unit", "set": "products"},
    {"name": "resource_capacity"}
  ],
  "decision_variables": [
    {"name": "production_quantity", "set": "products", "bounds": ["min_production", "max_production"]}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * production_quantity[i] for i in products)"
  },
  "constraints": [
    {"name": "resource_limit", "expression": "sum(resource_use_per_unit[i] * production_quantity[i] for i in products) <= resource_capacity"}
  ]
}
```

### Common Pitfalls
- Creating separate constraint objects for variable bounds when the solver's variable definition supports them directly, leading to redundant constraints.
- Assuming continuous variables are always appropriate; if production quantities must be integers, this LP formulation is invalid.
- Hard-coding data within the model-building code instead of separating parameters for maintainability.

## Solving stage

### Strategy Overview
Solve the model using a dedicated LP solver (e.g., GLOP). The focus is on efficient model construction, robust solution status checking, and validation of results against the original constraints.

### Step 1 - Initialize Solver and Build Model
- Create a solver instance appropriate for continuous LP problems (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Build the model by following the modeling steps, using the solver's methods to add variables, objective, and constraints.

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the returned status for `OPTIMAL` or `FEASIBLE`. Do not proceed to extract results if the status indicates `INFEASIBLE` or `UNBOUNDED`.

### Step 3 - Extract and Validate Solution
- Extract variable values and objective value using the solver's methods.
- Programmatically verify the solution: recompute total resource usage to confirm the capacity constraint is satisfied within a small tolerance, and check that variable values respect their bounds.

### Code Usage
```python
# Import solver library
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')
if not solver:
    raise RuntimeError('Solver creation failed')

# 2. Define data (placeholders)
products = range(num_products)
profit = [ ... ]  # list of profit per unit
min_prod = [ ... ] # list of minimum production
max_prod = [ ... ] # list of maximum production
resource_use = [ ... ] # list of resource consumption per unit
capacity = ... # total resource capacity

# 3. Create bounded variables
x = {}
for i in products:
    x[i] = solver.NumVar(min_prod[i], max_prod[i], f'x_{i}')

# 4. Add resource capacity constraint
constraint = solver.Constraint(0, capacity)
for i in products:
    constraint.SetCoefficient(x[i], resource_use[i])

# 5. Set objective
objective = solver.Objective()
for i in products:
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# 6. Solve and check status
status = solver.Solve()
if status not in [solver.OPTIMAL, solver.FEASIBLE]:
    raise Exception(f'Solver failed with status: {status}')

# 7. Extract and validate solution
total_profit = objective.Value()
total_resource_used = 0
for i in products:
    production_val = x[i].solution_value()
    # Validate bounds
    if not (min_prod[i] - 1e-6 <= production_val <= max_prod[i] + 1e-6):
        print(f'Warning: Variable x[{i}] = {production_val} outside bounds.')
    total_resource_used += resource_use[i] * production_val

if abs(total_resource_used - capacity) > 1e-6 and status == solver.OPTIMAL:
    print(f'Warning: Resource usage ({total_resource_used}) does not match capacity ({capacity}).')
```

### Common Pitfalls
- Failing to check solver status before extracting solution values, which can lead to runtime errors.
- Using excessive manual verification that duplicates the solver's internal checks; trust the `OPTIMAL` status but validate for sanity.
- Switching solver backends without a clear error-handling strategy if the primary solver fails.

# Workflow 2 (Modeling Language - Pyomo with CBC)

## Modeling stage

### Strategy Overview
This workflow uses a modeling language (Pyomo) to abstract the formulation from the solver. It separates data from model structure, enhancing clarity and maintainability, and is suitable for problems that may later require extensions (e.g., integer variables).

### Step 1 - Define Sets and Parameters
- Explicitly define a `Set` for products/items.
- Define all problem data (profits, bounds, resource requirements) as `Param` objects initialized from external data structures. Use lambda functions for clean initialization.

### Step 2 - Declare Bounded Variables
- Declare continuous, non-negative decision variables (e.g., `pyo.Var(domain=pyo.NonNegativeReals)`).
- Enforce lower and upper bounds by creating separate linear inequality constraints (`var >= min_bound` and `var <= max_bound`). This explicit formulation is clear and portable across solvers.

### Step 3 - Construct Objective and Constraints
- Define the linear profit objective using a `sum` expression over the product set.
- Formulate the resource capacity constraint as a single linear inequality summing resource consumption across all products.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": [
    {"name": "profit", "set": "products"},
    {"name": "min_production", "set": "products"},
    {"name": "max_production", "set": "products"},
    {"name": "resource_use_per_unit", "set": "products"},
    {"name": "resource_capacity"}
  ],
  "decision_variables": [
    {"name": "production_quantity", "set": "products", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * production_quantity[i] for i in products)"
  },
  "constraints": [
    {"name": "min_bound", "expression": "production_quantity[i] >= min_production[i] for i in products"},
    {"name": "max_bound", "expression": "production_quantity[i] <= max_production[i] for i in products"},
    {"name": "resource_limit", "expression": "sum(resource_use_per_unit[i] * production_quantity[i] for i in products) <= resource_capacity"}
  ]
}
```

### Common Pitfalls
- Embedding data directly within Pyomo rules instead of using parameters, making the model difficult to update.
- Forgetting to define the variable domain, which defaults to `Reals` and may not be appropriate.
- Creating overly complex lambda functions within constraints; keep expressions simple and linear.

## Solving stage

### Strategy Overview
Solve the abstract Pyomo model using a compatible solver (e.g., CBC). Configure solver options for performance and precision, and implement systematic checks on the solver's termination condition and solution status.

### Step 1 - Instantiate Model and Select Solver
- Create a Pyomo `ConcreteModel` and populate it using the defined formulation.
- Select an appropriate solver (e.g., `'cbc'` for LP/MIP) and configure options like time limits (`seconds`) and optimality tolerances (`ratio`) if needed.

### Step 2 - Solve and Inspect Termination
- Pass the model to the solver's `solve` method.
- Check both the `SolverStatus` (e.g., `ok`) and the `TerminationCondition` (e.g., `optimal`, `feasible`). A model can be solved successfully (`ok`) but only be feasible, not optimal.

### Step 3 - Extract, Validate, and Analyze
- Load the solution into the model instance.
- Extract variable values using `pyo.value()` and compute the objective value.
- Perform validation: recalculate constraint left-hand sides to ensure satisfaction and verify variable bounds.
- Optionally, compute derived metrics (e.g., profit-per-unit-resource) to analyze the solution's intuition.

### Code Usage
```python
# Import Pyomo
import pyomo.environ as pyo

# 1. Define external data (placeholders)
products = range(num_products)
profit_data = {i: ... for i in products}  # profit per unit
min_prod_data = {i: ... for i in products}
max_prod_data = {i: ... for i in products}
resource_use_data = {i: ... for i in products}
capacity = ...

# 2. Create Concrete Model
model = pyo.ConcreteModel()
model.products = pyo.Set(initialize=products)

# 3. Define Parameters
model.profit = pyo.Param(model.products, initialize=profit_data)
model.min_prod = pyo.Param(model.products, initialize=min_prod_data)
model.max_prod = pyo.Param(model.products, initialize=max_prod_data)
model.resource_use = pyo.Param(model.products, initialize=resource_use_data)
model.capacity = pyo.Param(initialize=capacity)

# 4. Define Variables
model.x = pyo.Var(model.products, domain=pyo.NonNegativeReals)

# 5. Define Bound Constraints
def min_bound_rule(m, i):
    return m.x[i] >= m.min_prod[i]
model.min_bound = pyo.Constraint(model.products, rule=min_bound_rule)

def max_bound_rule(m, i):
    return m.x[i] <= m.max_prod[i]
model.max_bound = pyo.Constraint(model.products, rule=max_bound_rule)

# 6. Define Resource Constraint
def resource_limit_rule(m):
    return sum(m.resource_use[i] * m.x[i] for i in m.products) <= m.capacity
model.resource_limit = pyo.Constraint(rule=resource_limit_rule)

# 7. Define Objective
def profit_rule(m):
    return sum(m.profit[i] * m.x[i] for i in m.products)
model.objective = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

# 8. Select and Configure Solver
solver = pyo.SolverFactory('cbc')
# Optional: Set solver options
# solver.options['seconds'] = 60
# solver.options['ratio'] = 0.0

# 9. Solve and Check Status
results = solver.solve(model, tee=False)  # Set tee=True for solver output

# Check if solver ran successfully
if results.solver.status != pyo.SolverStatus.ok:
    raise RuntimeError('Solver failed to run.')
if results.solver.termination_condition not in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    raise RuntimeError(f'No optimal/feasible solution found. Termination: {results.solver.termination_condition}')

# 10. Load solution and validate
# Load solution into model instance (required for some solvers)
model.solutions.load_from(results)

total_resource_used = 0
for i in model.products:
    val = pyo.value(model.x[i])
    # Validate bounds
    if not (pyo.value(model.min_prod[i]) - 1e-6 <= val <= pyo.value(model.max_prod[i]) + 1e-6):
        print(f'Warning: Variable x[{i}] = {val} violates bounds.')
    total_resource_used += pyo.value(model.resource_use[i]) * val

# Validate resource constraint
if abs(total_resource_used - pyo.value(model.capacity)) > 1e-6 and results.solver.termination_condition == pyo.TerminationCondition.optimal:
    print(f'Warning: Resource usage ({total_resource_used}) does not match capacity ({pyo.value(model.capacity)}).')

# Compute objective
total_profit = pyo.value(model.objective)
```

### Common Pitfalls
- Not loading the solution into the model instance after solving with certain solvers, leading to `pyo.value()` returning `None`.
- Confusing `SolverStatus.ok` (the solver ran) with `TerminationCondition.optimal` (it found an optimal solution); both must be checked.
- Manually solving an LP relaxation when using a MIP solver for an LP problem, which is redundant and inefficient.
