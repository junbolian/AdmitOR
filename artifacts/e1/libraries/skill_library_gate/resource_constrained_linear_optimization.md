---
name: Resource-Constrained Linear Optimization
description: |
  Model and solve linear optimization problems with nonnegative continuous variables, linear inequality constraints, and a linear objective for maximization or minimization.
---

# Workflow 1 (Pyomo with HiGHS Solver)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo modeling library to construct an abstract, declarative model, which is then solved by the HiGHS LP solver via a solver factory interface. It is well-suited for production environments requiring robust error handling and solver configuration.

### Step 1 - Define Model and Index Sets
- Create a Pyomo `ConcreteModel` or `AbstractModel`.
- Define a `Set` to index the decision variables (e.g., products, activities).
- Use Python dictionaries to store parameters keyed by the set indices.

### Step 2 - Declare Decision Variables
- Add a `Var` to the model with `domain=pyo.NonNegativeReals` for nonnegative continuous variables.
- Optionally, specify variable bounds directly within the `Var` declaration if they are uniform.

### Step 3 - Formulate Linear Objective
- Define an `Objective` using `sum(profit[i] * model.x[i] for i in items)`.
- Set the `sense` attribute to `pyo.maximize` or `pyo.minimize`.

### Step 4 - Add Linear Inequality Constraints
- For a global resource constraint, add a `Constraint` with expression `sum(consumption[i] * model.x[i]) <= total_limit`.
- For individual upper bounds, add indexed constraints `model.x[i] <= max_production[i]`.

### Formulation Template
```json
{
  "sets": ["ITEMS"],
  "parameters": [
    {"name": "profit", "indexed_by": "ITEMS"},
    {"name": "resource_consumption", "indexed_by": "ITEMS"},
    {"name": "total_resource_limit"},
    {"name": "max_production", "indexed_by": "ITEMS"}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": "ITEMS", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in ITEMS)"
  },
  "constraints": [
    {"name": "resource_limit", "expression": "sum(resource_consumption[i] * x[i] for i in ITEMS) <= total_resource_limit"},
    {"name": "production_cap", "indexed_by": "ITEMS", "expression": "x[i] <= max_production[i]"}
  ]
}
```

### Common Pitfalls
- Assuming continuous variables are sufficient; always validate that fractional solutions are acceptable for the problem domain.
- Hardcoding parameter values inside constraint expressions, which reduces model reusability.
- Not organizing data in indexed structures, leading to verbose and error-prone model construction.

## Solving stage

### Strategy Overview
The solving stage involves instantiating a solver object via `SolverFactory`, configuring it with performance options, executing the solve, and rigorously checking the status and results before extracting the solution.

### Step 1 - Initialize and Configure Solver
- Create a solver instance: `solver = pyo.SolverFactory('highs')`.
- Set solver options such as `time_limit`, `threads`, and `log_level` using `solver.options`.

### Step 2 - Solve and Check Status
- Execute `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `TerminationCondition.optimal`.

### Step 3 - Load and Validate Solution
- Load solution into the model object.
- Compute actual resource usage from variable values to verify constraint satisfaction within a small tolerance.
- Extract the objective value via `float(pyo.value(model.obj))`.

### Step 4 - Implement Error Handling
- Catch solver-specific exceptions.
- Provide fallback to an alternative LP solver (e.g., `'glpk'`) if the primary solver fails.

### Code Usage
```python
import pyomo.environ as pyo

# Build model `model` according to the modeling stage steps.

# 1. Initialize and configure solver
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 60
solver.options['threads'] = 4

# 2. Solve and check status
try:
    results = solver.solve(model, tee=False)
except Exception as e:
    # Fallback to alternative solver
    solver = pyo.SolverFactory('glpk')
    results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    # 3. Load and validate solution
    # Solution is loaded into model by default in Pyomo
    objective_value = float(pyo.value(model.obj))
    # Verify constraints
    total_used = sum(pyo.value(model.x[i]) * resource_consumption[i] for i in items)
    if total_used <= total_resource_limit + 1e-6:
        print(f"Optimal objective: {objective_value}")
    else:
        print("Warning: Solution violates resource constraint.")
else:
    print("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Not checking solver termination condition, leading to acceptance of suboptimal or infeasible results.
- Extracting variable values without first loading the solution into the model object.
- Failing to validate that the solver's solution satisfies all constraints within numerical tolerance.

# Workflow 2 (OR-Tools with Solver Selection Logic)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools library to construct a model directly via its C++-inspired API. It employs conditional solver selection based on variable types (LP vs. MIP), making it suitable for prototyping and scenarios where variable domain might change.

### Step 1 - Instantiate Solver with Logic
- Use a helper function or conditional statement to select the solver.
- For continuous-only problems, use `'GLOP'`; if integer variables are required, use `'SCIP'` or `'CBC'`.

### Step 2 - Create Variables with Bounds
- Create nonnegative continuous variables using `solver.NumVar(lb, ub, name)`.
- Store variables in a list or dictionary indexed by the item set.

### Step 3 - Define Linear Objective
- Create an objective expression using `solver.Objective()`.
- Set coefficients for each variable with `objective.SetCoefficient(var, coefficient)`.
- Call `objective.SetMaximization()` or `objective.SetMinimization()`.

### Step 4 - Add Constraints
- Create a constraint object with `solver.Constraint(lb, ub)`.
- Add terms to the constraint using `constraint.SetCoefficient(var, coefficient)` for each variable.

### Formulation Template
```json
{
  "sets": ["ITEMS"],
  "parameters": [
    {"name": "profit", "indexed_by": "ITEMS"},
    {"name": "resource_consumption", "indexed_by": "ITEMS"},
    {"name": "total_resource_limit"},
    {"name": "max_production", "indexed_by": "ITEMS"}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": "ITEMS", "domain": "Continuous", "lower_bound": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in ITEMS)"
  },
  "constraints": [
    {"name": "resource_limit", "expression": "sum(resource_consumption[i] * x[i] for i in ITEMS) <= total_resource_limit"},
    {"name": "production_cap", "indexed_by": "ITEMS", "expression": "x[i] <= max_production[i]"}
  ]
}
```

### Common Pitfalls
- Hardcoding a single solver name without considering variable domain requirements.
- Creating separate, redundant model-building functions for LP and MIP versions.
- Not specifying variable bounds, which defaults to (-inf, inf), potentially causing unintended model behavior.

## Solving stage

### Strategy Overview
The solving stage involves executing the solver, checking the result status, and extracting the solution values directly from the variable objects. The focus is on a streamlined, single-pass solve with integrated domain checking.

### Step 1 - Solve and Check Result Status
- Call `solver.Solve()`.
- Check the return value: `result_status = solver.Solve()`.
- Verify `result_status` equals `pywraplp.Solver.OPTIMAL`.

### Step 2 - Extract and Verify Solution
- Extract the objective value via `solver.Objective().Value()`.
- Iterate through decision variables and retrieve their values with `var.solution_value()`.
- Optionally, compute actual resource usage to validate the solution.

### Step 3 - Implement Parameterized Solving Function
- Encapsulate model building and solving in a function that accepts a boolean `integer_vars` parameter.
- Use this parameter to select the appropriate solver at instantiation.

### Code Usage
```python
from ortools.linear_solver import pywraplp

def build_and_solve(profit, consumption, total_limit, max_prod, integer_vars=False):
    # 1. Instantiate Solver with Logic
    solver_id = 'SCIP' if integer_vars else 'GLOP'
    solver = pywraplp.Solver.CreateSolver(solver_id)
    if not solver:
        raise RuntimeError(f"Solver {solver_id} not available.")

    items = list(profit.keys())
    # 2. Create Variables
    x = {}
    for i in items:
        lb = 0
        ub = max_prod[i]
        x[i] = solver.NumVar(lb, ub, f'x_{i}')

    # 3. Define Objective
    objective = solver.Objective()
    for i in items:
        objective.SetCoefficient(x[i], profit[i])
    objective.SetMaximization()

    # 4. Add Constraints
    # Resource constraint
    constraint = solver.Constraint(0, total_limit)
    for i in items:
        constraint.SetCoefficient(x[i], consumption[i])
    # Individual upper bounds are already enforced by variable ub.

    # Solving Stage
    # 1. Solve and Check Result Status
    result_status = solver.Solve()
    if result_status != pywraplp.Solver.OPTIMAL:
        print('The problem does not have an optimal solution.')
        return None

    # 2. Extract and Verify Solution
    opt_obj = solver.Objective().Value()
    sol = {i: x[i].solution_value() for i in items}
    # Quick validation
    total_used = sum(sol[i] * consumption[i] for i in items)
    if total_used <= total_limit + 1e-6:
        return opt_obj, sol
    else:
        print('Solution validation failed.')
        return None

# Usage example with continuous variables
# profit_dict = {...}; consumption_dict = {...}
# solution = build_and_solve(profit_dict, consumption_dict, total_limit=1000, max_prod={...}, integer_vars=False)
```

### Common Pitfalls
- Solving the problem twice with different solvers due to unclear initial variable domain requirements.
- Not checking solver capabilities before instantiation, leading to runtime errors.
- Manually overriding the solver's computed objective value with a hardcoded number in the final output.
