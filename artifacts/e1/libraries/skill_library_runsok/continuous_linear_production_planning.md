---
name: Continuous Linear Production Planning
description: |
  Model and solve continuous-variable linear programs for resource-constrained production planning with profit maximization, using structured data and robust solver handling.

---

# Workflow 1 (OR-Tools / GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools for modeling, leveraging its efficient C++ backend (GLOP) for continuous linear programming. It emphasizes embedding variable bounds directly during creation and using simple linear algebra for constraints.

### Step 1 - Define Data Structures
- Organize all problem parameters as parallel lists or dictionaries indexed by product ID for clarity and maintainability.
- Store profit per unit, resource consumption per unit, and minimum/maximum production bounds in these structures.

### Step 2 - Create Decision Variables with Bounds
- Instantiate continuous decision variables using `solver.NumVar(lb, ub, name)` to directly encode lower and upper bounds.
- Use a list or dictionary to store variable objects for easy access in constraints and the objective.

### Step 3 - Formulate the Objective Function
- Define the objective as a linear expression: `sum(profit[i] * x[i] for i in products)`.
- Set the sense to maximization using `solver.Maximize()`.

### Step 4 - Add the Global Resource Constraint
- Formulate the capacity constraint as a linear inequality: `sum(consumption[i] * x[i] for i in products) <= total_capacity`.
- Add this single constraint to the model using `solver.Add()`.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": [
    {"name": "profit", "index": "products"},
    {"name": "consumption", "index": "products"},
    {"name": "min_production", "index": "products"},
    {"name": "max_production", "index": "products"},
    {"name": "capacity", "index": null}
  ],
  "decision_variables": [
    {"name": "x", "index": "products", "type": "continuous", "lb": "min_production", "ub": "max_production"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in products)"
  },
  "constraints": [
    {"name": "capacity", "expression": "sum(consumption[i] * x[i] for i in products) <= capacity"}
  ]
}
```

### Common Pitfalls
- Forgetting to convert parameter dictionaries to lists in the order corresponding to the variable list when building linear expressions.
- Using `solver.IntVar` instead of `solver.NumVar` for continuous quantities, which unnecessarily restricts the solution space.
- Not verifying that the sum of minimum required resource consumption does not exceed total capacity, which leads to infeasibility.

## Solving stage

### Strategy Overview
The solving stage focuses on using the GLOP solver, checking solution status rigorously, and performing post-solution analysis to extract insights like shadow prices and reduced costs.

### Step 1 - Invoke the Solver
- Create a solver instance with `pywraplp.Solver.CreateSolver('GLOP')`.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Validate Solution Status
- Check if the result status is `pywraplp.Solver.OPTIMAL` or `FEASIBLE`.
- If not optimal/feasible, report the status and avoid extracting variable values.

### Step 3 - Extract and Analyze Solution
- Retrieve the objective value and all variable values.
- Calculate derived metrics like total resource used and capacity utilization percentage.
- Access dual values (shadow prices) for the capacity constraint using `solver.DualValue(constraint)` to understand marginal resource value.

### Step 4 - Perform Sensitivity Check (Optional)
- Compute profit-per-unit-consumption ratios to verify the solution aligns with economic intuition when the capacity constraint is binding.
- Test the impact of small capacity changes on the objective value using the shadow price.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
x = {}
for i in products:
    x[i] = solver.NumVar(min_prod[i], max_prod[i], f'x_{i}')
objective_terms = [profit[i] * x[i] for i in products]
solver.Maximize(solver.Sum(objective_terms))
capacity_constraint = solver.Add(
    solver.Sum(consumption[i] * x[i] for i in products) <= total_capacity
)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    solution = {i: x[i].solution_value() for i in products}
    shadow_price = solver.DualValue(capacity_constraint)
    # ... analysis ...
else:
    print(f'Solver did not find optimal solution. Status: {status}')
```

### Common Pitfalls
- Assuming the solver always returns an optimal solution without checking the status code.
- Misinterpreting the shadow price sign; for a maximization problem with a `<=` constraint, the shadow price is non-negative.
- Not handling the case where the solver might return `UNBOUNDED` or `INFEASIBLE`, leading to runtime errors when querying values.

# Workflow 2 (Pyomo / HiGHS or CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a declarative, algebraic modeling style, abstracting problem components into sets, parameters, variables, and constraints. It supports multiple solvers (HiGHS for LP, CBC for MIP) with a fallback strategy.

### Step 1 - Define Abstract Model Components
- Declare a Pyomo `Set` for the product indices.
- Declare `Param` components for all input data (profit, consumption, bounds, capacity), initializing them from dictionaries.

### Step 2 - Declare Continuous Decision Variables
- Create a Pyomo `Var` indexed by the product set, with domain `pyo.NonNegativeReals`.
- Do not set bounds on the variable declaration; instead, implement them as separate constraints for flexibility.

### Step 3 - Formulate Objective and Constraints
- Define the objective as a `pyo.Objective` with sense `maximize`.
- Add the global capacity constraint as a single `pyo.Constraint`.
- Add lower and upper bound constraints as indexed `pyo.Constraint` objects using rule functions.

### Step 4 - Structure for Maintainability
- Use `ConcreteModel` for problems with instantiated data.
- Keep constraint rules simple and separate to allow easy modification or deactivation.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": [
    {"name": "profit", "index": "I"},
    {"name": "consumption", "index": "I"},
    {"name": "min_prod", "index": "I"},
    {"name": "max_prod", "index": "I"},
    {"name": "capacity", "index": null}
  ],
  "decision_variables": [
    {"name": "x", "index": "I", "type": "continuous", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    {"name": "capacity_limit", "expression": "sum(consumption[i] * x[i] for i in I) <= capacity"},
    {"name": "min_bound", "expression": "x[i] >= min_prod[i] for i in I"},
    {"name": "max_bound", "expression": "x[i] <= max_prod[i] for i in I"}
  ]
}
```

### Common Pitfalls
- Using an `AbstractModel` with data decoupling when a simple `ConcreteModel` suffices, adding unnecessary complexity.
- Defining variable bounds directly in the `Var` declaration and then also adding bound constraints, leading to redundant model components.
- Not using `initialize` for `Param` components, causing errors when building expressions.

## Solving stage

### Strategy Overview
Solving involves selecting a primary solver (HiGHS for LP), implementing a fallback chain, meticulously checking termination conditions, and safely loading solutions only when valid.

### Step 1 - Configure Solver with Fallback
- Attempt to use `SolverFactory('highs')` as the primary solver for continuous LPs.
- If unavailable or failing, fall back to `'glpk'` or `'cbc'` in sequence.

### Step 2 - Solve with Deferred Solution Loading
- Call `solver.solve(model, load_solutions=False)` to separate solving from solution loading.
- Capture the results object for status inspection.

### Step 3 - Check Termination Condition
- Verify `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `.feasible`.
- Only if both checks pass, load the solution into the model using `model.solutions.load_from(results)`.

### Step 4 - Extract and Report Results
- Extract variable values using `pyo.value(model.x[i])` and the objective value.
- Calculate verification metrics like total consumption and constraint slack.
- Provide structured output suitable for both automated processing and human review.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=products)
model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
model.profit = pyo.Param(model.I, initialize=profit_dict)
model.consumption = pyo.Param(model.I, initialize=consumption_dict)
model.min_prod = pyo.Param(model.I, initialize=min_dict)
model.max_prod = pyo.Param(model.I, initialize=max_dict)
model.capacity = pyo.Param(initialize=total_capacity)

model.obj = pyo.Objective(
    expr=sum(model.profit[i] * model.x[i] for i in model.I),
    sense=pyo.maximize
)
model.cap_con = pyo.Constraint(
    expr=sum(model.consumption[i] * model.x[i] for i in model.I) <= model.capacity
)
model.min_con = pyo.Constraint(model.I, rule=lambda m, i: m.x[i] >= m.min_prod[i])
model.max_con = pyo.Constraint(model.I, rule=lambda m, i: m.x[i] <= m.max_prod[i])

# solve with status / termination checks
solver_names = ['highs', 'glpk', 'cbc']
solver = None
for name in solver_names:
    s = pyo.SolverFactory(name)
    if s.available():
        solver = s
        break
if solver is None:
    raise RuntimeError('No solver available')

results = solver.solve(model, tee=False, load_solutions=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal,
                                              TerminationCondition.feasible)):
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    solution = {i: pyo.value(model.x[i]) for i in model.I}
else:
    print(f'Solve failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}')
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) without checking termination condition, potentially loading invalid or suboptimal results.
- Assuming a solver factory is available without calling `.available()` or handling the `ApplicationError` if it's not.
- Not using `pyo.value()` to extract numeric values from Pyomo components, leading to symbolic expression objects.
