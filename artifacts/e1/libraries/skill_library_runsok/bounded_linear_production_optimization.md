---
name: Bounded Linear Production Optimization
description: |
  Model and solve linear production problems with bounded decision variables and a single resource constraint, maximizing profit via continuous or integer programming.
---

# Workflow 1 (Google OR-Tools LP/GLOP)

## Modeling stage

### Strategy Overview
Formulate the problem as a continuous Linear Program (LP) using Google OR-Tools' `pywraplp` API. Leverage built-in variable bounds to handle min/max production limits efficiently, and construct a single linear constraint for the shared resource capacity.

### Step 1 - Define Data Structures
- Organize all product-specific parameters (profit per unit, resource consumption per unit, minimum and maximum production) into parallel lists or dictionaries indexed by product ID.
- Store the total resource capacity as a single scalar value.

### Step 2 - Create Bounded Variables
- For each product, create a decision variable using `solver.NumVar(lower_bound, upper_bound, name)`.
- This directly encodes the lower and upper bound constraints, reducing the number of explicit constraints in the model.

### Step 3 - Formulate Resource Constraint
- Create a single linear inequality constraint using `solver.Constraint(-inf, total_capacity)`.
- For each product, add its contribution to the constraint using `constraint.SetCoefficient(variable, resource_per_unit)`.

### Step 4 - Define Linear Objective
- Create the objective expression using `solver.Objective()`.
- Set coefficients for each variable equal to its profit per unit and set the objective sense to maximize.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": ["profit", "resource_per_unit", "min_production", "max_production", "total_capacity"],
  "decision_variables": ["x[product]"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[product] * x[product] for product in products)"
  },
  "constraints": [
    "sum(resource_per_unit[product] * x[product] for product in products) <= total_capacity",
    "min_production[product] <= x[product] <= max_production[product] for product in products"
  ]
}
```

### Common Pitfalls
- Forgetting to check if the solver object was created successfully (`solver` is not `None`).
- Confusing the order of arguments for `solver.Constraint` (lower bound, upper bound).
- Not verifying that the extracted solution satisfies all constraints numerically.

## Solving stage

### Strategy Overview
Solve the LP model using the GLOP backend. Implement a robust solve-check-output pattern that handles different solver statuses, extracts the solution, and performs post-solution validation.

### Step 1 - Initialize Solver and Solve
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Call `status = solver.Solve()` to execute the optimization.

### Step 2 - Check Solution Status
- Check if `status` is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`.
- If not, output a structured error message (e.g., JSON) indicating infeasibility or other failure.

### Step 3 - Extract and Validate Solution
- If optimal/feasible, get the objective value via `solver.Objective().Value()`.
- Extract each variable's value via `variable.solution_value()`.
- Recalculate total resource usage and verify it is within capacity and that variable bounds are satisfied.

### Step 4 - Output Results
- Print a clear summary including total profit, resource usage, and individual production quantities.
- Output a final result in a consistent, parseable format (e.g., `RESULT:{objective_value}`).

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
if not solver:
    raise RuntimeError("Solver creation failed")

# Create variables with bounds
x = {}
for i in products:
    x[i] = solver.NumVar(min_production[i], max_production[i], f'x_{i}')

# Resource constraint
constraint = solver.Constraint(0, total_capacity)
for i in products:
    constraint.SetCoefficient(x[i], resource_per_unit[i])

# Objective
objective = solver.Objective()
for i in products:
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# 2. Solve with status / termination checks
status = solver.Solve()

if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    obj_val = objective.Value()
    solution = {i: x[i].solution_value() for i in products}
    # Post-solution validation
    used_resource = sum(resource_per_unit[i] * solution[i] for i in products)
    print(f"Optimal profit: {obj_val}")
    print(f"Resource used: {used_resource}/{total_capacity}")
    print(f"RESULT:{obj_val}")
else:
    print(f"RESULT_JSON:{{\"status\":\"{status}\", \"message\":\"Solver did not find optimal solution.\"}}")
```

### Common Pitfalls
- Assuming the solver status is always `OPTIMAL` without checking for `FEASIBLE`.
- Not handling the case where the solver object is `None` (backend not available).
- Extracting variable values without checking the solve status first, which may cause errors.

# Workflow 2 (Pyomo with CBC/MILP)

## Modeling stage

### Strategy Overview
Formulate the problem using Pyomo for structured, object-oriented modeling. Use `pyo.Var` with `bounds` and `domain` arguments to handle variable bounds and optional integrality. This approach cleanly separates data (`pyo.Param`) from model structure, facilitating reuse and integer formulations.

### Step 1 - Define Abstract Sets and Parameters
- Define a Pyomo `Set` to represent the index of products.
- Define `Param` objects for profit, resource consumption per unit, min/max bounds, and total capacity, initialized from external data.

### Step 2 - Declare Decision Variables
- Create a `Var` indexed over the product set.
- Specify the `domain` (`pyo.NonNegativeReals` for LP, `pyo.Integers` for MILP).
- Use the `bounds` argument with a rule function to set individual lower and upper bounds for each product.

### Step 3 - Construct Objective Function
- Define an `Objective` using a rule that sums `profit[i] * x[i]` over all products.
- Set the sense to `pyo.maximize`.

### Step 4 - Add Constraints
- Add a single `Constraint` for the total resource capacity using a rule that sums `resource_use[i] * x[i]`.
- Individual bound constraints are handled within the variable declaration and do not need separate constraints.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": ["profit", "resource_use", "min_prod", "max_prod", "capacity"],
  "decision_variables": ["x[product]"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[product] * x[product] for product in products)"
  },
  "constraints": [
    "sum(resource_use[product] * x[product] for product in products) <= capacity"
  ]
}
```

### Common Pitfalls
- Confusing Pyomo `Rule` functions with direct expressions; rules must accept the model as the first argument.
- Forgetting to deactivate the `load_solutions` option when solver status checking is required.
- Using mutable data structures (like lists) inside `Param` initialization functions, which can lead to unexpected behavior.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via `SolverFactory`. Implement robust status checking using both `solver.status` and `termination_condition`. Extract and verify the solution, and handle cases where integer solutions are required.

### Step 1 - Configure and Run Solver
- Instantiate the solver: `solver = pyo.SolverFactory('cbc')`.
- Set solver options if needed (e.g., time limit, optimality gap tolerance).
- Solve with `results = solver.solve(model, tee=False, load_solutions=False)`.

### Step 2 - Check Solver Status and Termination
- Check `results.solver.status` equals `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `.feasible`.
- If checks fail, output a failure payload without loading the solution.

### Step 3 - Load and Extract Solution
- If status checks pass, load the solution: `model.solutions.load_from(results)`.
- Extract the objective value using `pyo.value(model.obj)`.
- Extract variable values using `pyo.value(model.x[i])` or a dictionary comprehension.

### Step 4 - Post-Solution Analysis
- Recalculate total resource usage and verify constraint satisfaction.
- For MILP, compute the optimality gap relative to the LP relaxation if available.
- Output results in a structured format.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# 1. Build model from formulation
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=range(num_products))

# Parameters
model.profit = pyo.Param(model.P, initialize=profit_data)
model.resource_use = pyo.Param(model.P, initialize=resource_per_unit_data)
model.min_prod = pyo.Param(model.P, initialize=min_prod_data)
model.max_prod = pyo.Param(model.P, initialize=max_prod_data)
model.capacity = pyo.Param(initialize=total_capacity)

# Variables (choose domain: NonNegativeReals or Integers)
model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals,
                  bounds=lambda m, i: (m.min_prod[i], m.max_prod[i]))

# Objective
model.obj = pyo.Objective(expr=sum(model.profit[i] * model.x[i] for i in model.P),
                          sense=pyo.maximize)

# Constraints
@model.Constraint()
def resource_limit(model):
    return sum(model.resource_use[i] * model.x[i] for i in model.P) <= model.capacity

# 2. Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0  # For optimality gap

results = solver.solve(model, tee=False, load_solutions=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    solution = {i: pyo.value(model.x[i]) for i in model.P}
    # Verification
    used = sum(pyo.value(model.resource_use[i]) * solution[i] for i in model.P)
    print(f"Optimal profit: {obj_val}")
    print(f"Resource used: {used}/{pyo.value(model.capacity)}")
    print(f"RESULT:{obj_val}")
else:
    failure_payload = {"status": str(status), "termination": str(term)}
    print(f"RESULT_JSON:{json.dumps(failure_payload)}")
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) before checking termination conditions, which can load invalid results.
- Not setting `domain=pyo.Integers` when integer solutions are required, resulting in unrealistic fractional production quantities.
- Misinterpreting the `ratio` option in CBC; setting it to 0.0 demands exact optimality, which may increase solve time.
