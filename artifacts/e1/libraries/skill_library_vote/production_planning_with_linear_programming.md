---
name: Production Planning with Linear Programming
description: |
  Model and solve linear production planning problems with continuous variables, resource capacity constraints, and individual product bounds using standard LP solvers.
---

# Workflow 1 (OR-Tools with GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to build a compact, imperative model. Variable bounds are set directly during creation, and constraints are added via linear expressions. It is optimized for speed and clarity in pure LP problems.

### Step 1 - Define Data Structures
- Organize problem parameters into parallel arrays or dictionaries indexed by product.
- Store `profit_per_unit`, `time_per_unit`, `min_production`, and `max_production` for each product.
- Define a scalar `total_capacity` for the shared resource.

### Step 2 - Create Solver and Variables
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Create continuous decision variables using `solver.NumVar(lower_bound, upper_bound, name)`.
- Use the pre-defined `min_production` and `max_production` arrays directly as bounds.

### Step 3 - Add Capacity Constraint
- Formulate the linear inequality: sum(`time_per_unit[i]` * `x[i]`) <= `total_capacity`.
- Use `solver.Add()` to create the constraint from a constructed linear expression.

### Step 4 - Set Linear Objective
- Define the maximization objective: sum(`profit_per_unit[i]` * `x[i]`).
- Set it using `solver.Maximize()`.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": {
    "profit_per_unit": {"index": "products", "type": "float"},
    "time_per_unit": {"index": "products", "type": "float"},
    "min_production": {"index": "products", "type": "float"},
    "max_production": {"index": "products", "type": "float"},
    "total_capacity": {"type": "float"}
  },
  "decision_variables": {
    "x": {"index": "products", "type": "continuous", "bounds": ["min_production", "max_production"]}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[i] * x[i] for i in products)"
  },
  "constraints": {
    "capacity": "sum(time_per_unit[i] * x[i] for i in products) <= total_capacity"
  }
}
```

### Common Pitfalls
- Using `CBC` or `SCIP` for a pure continuous LP, which is less efficient than `GLOP`.
- Forgetting to check solver status before accessing solution values, causing runtime errors.
- Manually adding bound constraints as separate inequalities, duplicating the bounds already set on variables.

## Solving stage

### Strategy Overview
Solve the model using the GLOP backend, check termination status rigorously, and extract the solution. Perform post-solution validation by calculating derived metrics like capacity utilization.

### Step 1 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check if `status` is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`. Proceed only if true.

### Step 2 - Extract and Store Solution
- Retrieve the objective value via `solver.Objective().Value()`.
- Extract variable values using a list comprehension: `[x[i].solution_value() for i in range(n_products)]`.

### Step 3 - Validate and Analyze Solution
- Calculate total time used: sum(`time_per_unit[i]` * `production_quantity[i]`).
- Verify it does not exceed `total_capacity`.
- Compute profit per unit time (`profit_per_unit[i]` / `time_per_unit[i]`) to interpret the solution.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
x = {}
for i in range(n_products):
    x[i] = solver.NumVar(min_production[i], max_production[i], f'x_{i}')
# Capacity constraint
constraint_expr = sum(time_per_unit[i] * x[i] for i in range(n_products))
solver.Add(constraint_expr <= total_capacity)
# Objective
solver.Maximize(sum(profit_per_unit[i] * x[i] for i in range(n_products)))

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    production_quantities = [x[i].solution_value() for i in range(n_products)]
    # Validation and analysis
    total_time_used = sum(time_per_unit[i] * production_quantities[i] for i in range(n_products))
else:
    print('Solver did not find an optimal or feasible solution.')
```

### Common Pitfalls
- Assuming `OPTIMAL` is the only acceptable status; `FEASIBLE` solutions are often usable.
- Not storing the solution values in a structured way for later reporting or validation.
- Overlooking the value of reduced costs or shadow prices for solution insight.

# Workflow 2 (Pyomo with HiGHS/GLPK)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to create a declarative, data-separated model. Constraints for bounds are explicitly written, providing clear tracking. The model is solved via Pyomo's `SolverFactory` with open-source LP solvers like HiGHS.

### Step 1 - Structure Model and Sets
- Create a `pyo.ConcreteModel()`.
- Define a `Set` for products to index all parameters and variables.

### Step 2 - Define Parameters
- Declare `pyo.Param` objects for `profit`, `time`, `min_prod`, `max_prod` (indexed by the product set).
- Define a scalar `pyo.Param` for `capacity`.

### Step 3 - Declare Continuous Variables
- Create `pyo.Var(model.products, domain=pyo.NonNegativeReals)` for production quantities.
- Do not set bounds on the variable declaration; bounds will be explicit constraints.

### Step 4 - Formulate Explicit Bound Constraints
- Add constraints: `model.lower_bound = pyo.Constraint(model.products, rule=lambda m, i: m.x[i] >= m.min_prod[i])`.
- Add constraints: `model.upper_bound = pyo.Constraint(model.products, rule=lambda m, i: m.x[i] <= m.max_prod[i])`.

### Step 5 - Formulate Capacity Constraint and Objective
- Add constraint: `sum(m.time[i] * m.x[i] for i in m.products) <= m.capacity`.
- Set objective: `pyo.Objective(expr=sum(m.profit[i] * m.x[i] for i in m.products), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": {
    "profit": {"index": "products", "type": "float"},
    "time": {"index": "products", "type": "float"},
    "min_prod": {"index": "products", "type": "float"},
    "max_prod": {"index": "products", "type": "float"},
    "capacity": {"type": "float"}
  },
  "decision_variables": {
    "x": {"index": "products", "type": "continuous", "domain": "NonNegativeReals"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in products)"
  },
  "constraints": {
    "lower_bound": "x[i] >= min_prod[i] for i in products",
    "upper_bound": "x[i] <= max_prod[i] for i in products",
    "capacity": "sum(time[i] * x[i] for i in products) <= capacity"
  }
}
```

### Common Pitfalls
- Using `domain=pyo.NonNegativeReals` and also adding explicit non-negativity constraints, creating redundancy.
- Forgetting to deactivate the `load_solutions` option when using HiGHS, which can cause errors on infeasible solves.
- Mixing up Pyomo's `ConcreteModel` (immediate data) and `AbstractModel` (data later) paradigms, leading to initialization errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory, configure performance options, and implement robust status checking and solution loading. Include a fallback to an alternative solver if the primary fails.

### Step 1 - Configure and Run Solver
- Create solver object: `solver = SolverFactory('highs')`.
- Set options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`.
- Solve with `load_solutions=False`: `results = solver.solve(model, load_solutions=False, tee=False)`.

### Step 2 - Check Termination Status
- Check `results.solver.status` and `results.solver.termination_condition`.
- Accept status `ok` with termination `optimal` or `feasible`.

### Step 3 - Load and Extract Solution
- If status is acceptable, load solution: `model.solutions.load_from(results)`.
- Extract objective value: `pyo.value(model.obj)`.
- Extract variable values: `[pyo.value(model.x[i]) for i in model.products]`.

### Step 4 - Validate and Implement Fallback
- Calculate derived metrics (e.g., capacity usage) to validate feasibility.
- If primary solver fails, re-initialize `SolverFactory` with a fallback (e.g., `'glpk'`) and re-solve.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.products = pyo.Set(initialize=range(n_products))
model.profit = pyo.Param(model.products, initialize=profit_data)
model.time = pyo.Param(model.products, initialize=time_data)
model.min_prod = pyo.Param(model.products, initialize=min_prod_data)
model.max_prod = pyo.Param(model.products, initialize=max_prod_data)
model.capacity = pyo.Param(initialize=total_capacity)
model.x = pyo.Var(model.products, domain=pyo.NonNegativeReals)
def lower_bound_rule(m, i):
    return m.x[i] >= m.min_prod[i]
model.lower_bound = pyo.Constraint(model.products, rule=lower_bound_rule)
def upper_bound_rule(m, i):
    return m.x[i] <= m.max_prod[i]
model.upper_bound = pyo.Constraint(model.products, rule=upper_bound_rule)
def capacity_rule(m):
    return sum(m.time[i] * m.x[i] for i in m.products) <= m.capacity
model.capacity_con = pyo.Constraint(rule=capacity_rule)
model.obj = pyo.Objective(expr=sum(m.profit[i] * m.x[i] for i in m.products), sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, load_solutions=False)
if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    model.solutions.load_from(results)
    objective_value = pyo.value(model.obj)
    production_quantities = [pyo.value(model.x[i]) for i in model.products]
else:
    # Fallback to GLPK
    solver_fb = pyo.SolverFactory('glpk')
    results_fb = solver_fb.solve(model, load_solutions=False)
    # ... repeat status check and load
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) with HiGHS on an infeasible problem, which raises an exception.
- Not setting a time limit, allowing the solver to run indefinitely on large or difficult instances.
- Failing to provide a clear fallback path when the primary solver is not available.
