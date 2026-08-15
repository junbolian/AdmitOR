---
name: Continuous Production Planning with Resource Constraints
description: |
  Model and solve continuous linear programs for production planning with individual product limits and a shared resource capacity to maximize total profit.
---

# Workflow 1 (OR-Tools / GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools with the GLOP linear programming solver. It emphasizes efficiency by embedding individual upper bounds directly as variable limits, reducing the number of explicit constraints.

### Step 1 - Define Data Structures
- Organize problem parameters into parallel lists or arrays indexed by product.
- Store `profit_per_unit`, `resource_consumption_per_unit`, and `max_production` for each product.
- Define the total available resource capacity as a scalar.

### Step 2 - Create Decision Variables
- Instantiate a continuous decision variable for each product's production quantity.
- Set the variable's lower bound to 0 and its upper bound to the product's `max_production` directly during creation.

### Step 3 - Formulate Resource Constraint
- Create a single linear constraint representing the shared resource.
- The left-hand side is the sum of each product's production quantity multiplied by its resource consumption rate.
- Set the constraint's upper bound to the total available resource.

### Step 4 - Define Objective Function
- Create a linear objective to maximize total profit.
- The objective expression is the sum of each product's production quantity multiplied by its profit per unit.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": ["profit", "resource_consumption", "max_production", "total_resource"],
  "decision_variables": [
    {
      "name": "production_quantity",
      "type": "continuous",
      "lower_bound": 0,
      "upper_bound": "max_production[i]"
    }
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * production_quantity[i] for i in products)"
  },
  "constraints": [
    {
      "name": "resource_capacity",
      "expression": "sum(resource_consumption[i] * production_quantity[i] for i in products) <= total_resource"
    }
  ]
}
```

### Common Pitfalls
- Forgetting to check if the solver object was created successfully, leading to runtime errors.
- Not verifying the solver status before extracting solution values, which can cause crashes on infeasible or unbounded models.
- Using inefficient loops to build constraints and objective for large numbers of products.

## Solving stage

### Strategy Overview
Solve the model using the GLOP linear solver, perform rigorous status checks, and extract solution values along with key performance metrics for validation and reporting.

### Step 1 - Instantiate Solver and Build Model
- Create a GLOP solver instance.
- Build the model by following the modeling steps, adding variables, constraint, and objective.

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the returned status (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`). Proceed only for `OPTIMAL` or `FEASIBLE`.

### Step 3 - Extract and Validate Solution
- Extract the objective value.
- Retrieve the production quantity for each product.
- Calculate the actual resource usage to verify constraint satisfaction.

### Step 4 - Perform Post-Solution Analysis
- Compute resource utilization percentage.
- Identify which products are produced at their maximum capacity.
- Sort products by production quantity or profit contribution for insights.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('GLOP')
if solver is None:
    raise Exception('Solver creation failed')

# Create variables with bounds
x = {}
for i in range(num_products):
    x[i] = solver.NumVar(0, max_production[i], f'x_{i}')

# Add resource constraint
constraint_expr = sum(resource_consumption[i] * x[i] for i in range(num_products))
solver.Add(constraint_expr <= total_resource)

# Set objective
objective = solver.Objective()
for i in range(num_products):
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_profit = objective.Value()
    # Extract solution and perform analysis
    resource_used = sum(resource_consumption[i] * x[i].solution_value() for i in range(num_products))
    utilization = (resource_used / total_resource) * 100
else:
    print('No optimal solution found.')
```

### Common Pitfalls
- Assuming the solver status is always `OPTIMAL` without checking for `FEASIBLE`.
- Not handling the case where the solver object creation fails (returns `None`).
- Extracting variable values via `.solution_value()` without first confirming a successful solve.

# Workflow 2 (Pyomo / HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for model definition and the HiGHS solver. It structures the model explicitly with Pyomo components (Sets, Params, Vars, Constraints), making it highly readable and maintainable for complex extensions.

### Step 1 - Define Model and Abstract Sets
- Create a Pyomo `ConcreteModel`.
- Define a `Set` to represent the index of products, initialized from the product list or range.

### Step 2 - Declare Parameters
- Define `Param` components for `profit`, `resource_consumption`, and `max_production`, indexed by the product set.
- Define a scalar `Param` for the `total_resource`.

### Step 3 - Declare Decision Variables
- Define a `Var` component for production quantity, indexed by the product set.
- Set the variable domain to `NonNegativeReals` and optionally set upper bounds via the `bounds` argument or a rule.

### Step 4 - Formulate Objective and Constraints
- Define the objective as a `maximize` rule summing profit.
- Add a single `Constraint` for the shared resource capacity.
- Add individual upper bound constraints explicitly for each product (or via variable bounds).

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": ["profit", "resource_consumption", "max_production", "total_resource"],
  "decision_variables": [
    {
      "name": "production_quantity",
      "type": "continuous",
      "domain": "NonNegativeReals",
      "bounds": "(0, max_production[i])"
    }
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * production_quantity[i] for i in products)"
  },
  "constraints": [
    {
      "name": "resource_capacity",
      "expression": "sum(resource_consumption[i] * production_quantity[i] for i in products) <= total_resource"
    },
    {
      "name": "individual_limits",
      "expression": "production_quantity[i] <= max_production[i] for i in products"
    }
  ]
}
```

### Common Pitfalls
- Confusing Pyomo `Set` initialization with `initialize` expecting an iterable or callable.
- Forgetting to call `pyo.value()` on Pyomo expressions when extracting numeric results after solving.
- Defining variable bounds incorrectly within a rule, leading to unexpected model behavior.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via the `SolverFactory`, configure solver options for performance, and perform a two-tier check on both solver status and termination condition before accepting the solution.

### Step 1 - Configure and Execute Solver
- Create a solver instance using `SolverFactory('highs')`.
- Optionally set solver options like time limit or optimality tolerance.
- Execute the solve command with `solve(model, ...)`.

### Step 2 - Verify Solution Status
- Check the solver status (`SolverStatus.ok`) to ensure the solve process completed without error.
- Check the termination condition (`TerminationCondition.optimal` or `.feasible`) to confirm solution quality.

### Step 3 - Extract and Analyze Results
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate through variables to get production quantities.
- Calculate derived metrics like resource utilization and profit-per-resource ratios.

### Step 4 - Validate Against Intuition
- Sort products by efficiency (profit per resource unit).
- Compare the sorted list with the solution's production quantities to sanity-check optimality.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_products))
model.profit = pyo.Param(model.I, initialize=lambda m, i: profit[i])
model.resource_consumption = pyo.Param(model.I, initialize=lambda m, i: resource_consumption[i])
model.max_production = pyo.Param(model.I, initialize=lambda m, i: max_production[i])
model.total_resource = pyo.Param(initialize=total_resource)

model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals, bounds=lambda m, i: (0, m.max_production[i]))

def obj_rule(m):
    return sum(m.profit[i] * m.x[i] for i in m.I)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

def resource_rule(m):
    return sum(m.resource_consumption[i] * m.x[i] for i in m.I) <= m.total_resource
model.resource_con = pyo.Constraint(rule=resource_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_profit = pyo.value(model.obj)
    # Extract solution and perform analysis
    resource_used = sum(pyo.value(model.x[i]) * model.resource_consumption[i] for i in model.I)
else:
    print('Solve failed or no acceptable solution found.')
```

### Common Pitfalls
- Checking only the termination condition without verifying the solver status is `ok`.
- Not using `pyo.value()` to convert Pyomo expressions to floats after solving.
- Assuming the HiGHS solver is always available; missing fallback to another solver like CBC.
