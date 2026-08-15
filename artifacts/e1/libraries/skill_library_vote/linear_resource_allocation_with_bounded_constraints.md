---
name: Linear Resource Allocation with Bounded Constraints
description: |
  Model and solve linear cost minimization problems with continuous non-negative variables and double-sided linear constraints, using structured data and verification patterns.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a direct, low-level solver API (e.g., OR-Tools) for explicit control over variable and constraint creation. It is suited for prototyping and educational purposes where understanding the matrix structure is key.

### Step 1 - Define Index Sets and Data Structure
- Create clear index sets for `items` (e.g., foods, resources) and `requirements` (e.g., nutrients, components).
- Organize data into separate arrays: `costs[item]`, `lower_bounds[requirement]`, `upper_bounds[requirement]`, and `coefficient_matrix[item][requirement]`.
- Use descriptive variable names to map directly to the problem's natural structure.

### Step 2 - Create Continuous Non-Negative Variables
- For each `item`, create a continuous decision variable with a lower bound of 0 and no upper bound (or a specified upper bound if applicable).
- Use the pattern `solver.NumVar(0, solver.infinity(), f'x_{i}')` to enforce non-negativity.

### Step 3 - Implement Double-Sided Linear Constraints
- For each `requirement`, create two separate linear constraints: one for the lower bound and one for the upper bound.
- Build each constraint by iterating over all `items` and setting coefficients using `constraint.SetCoefficient(x[item], coefficient_matrix[item][requirement])`.
- Set the constraint bounds: `constraint_lower.SetBounds(lower_bound, solver.infinity())` and `constraint_upper.SetBounds(-solver.infinity(), upper_bound)`.

### Step 4 - Set Linear Minimization Objective
- Initialize the objective for minimization: `objective = solver.Objective()`.
- Add the linear cost terms: `objective.SetCoefficient(x[item], costs[item])` for each `item`.
- Set the optimization direction: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    {"name": "items", "description": "Index set for selectable resources."},
    {"name": "requirements", "description": "Index set for constraints or components to balance."}
  ],
  "parameters": [
    {"name": "cost", "index": "items", "description": "Unit cost per item."},
    {"name": "lower_bound", "index": "requirements", "description": "Minimum required total for each requirement."},
    {"name": "upper_bound", "index": "requirements", "description": "Maximum allowed total for each requirement."},
    {"name": "coefficient", "index": ["items", "requirements"], "description": "Contribution of one unit of item to the requirement."}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "min_req", "index": "requirements", "expression": "sum(coefficient[i][r] * x[i] for i in items) >= lower_bound[r]"},
    {"name": "max_req", "index": "requirements", "expression": "sum(coefficient[i][r] * x[i] for i in items) <= upper_bound[r]"}
  ]
}
```

### Common Pitfalls
- Hard-coding array dimensions instead of using the length of index sets, reducing reusability.
- Incorrectly transposing the coefficient matrix (items vs. requirements), leading to wrong constraint values.
- Forgetting to set the objective sense to minimization, defaulting to maximization.

## Solving stage

### Strategy Overview
Solve the model using a dedicated LP solver (e.g., GLOP), followed by systematic solution verification to ensure feasibility and handle solver statuses appropriately.

### Step 1 - Select and Configure LP Solver
- Instantiate the solver for linear programming: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- For problems with potential integer requirements, consider `'CBC'` or `'SCIP'` instead.

### Step 2 - Solve and Check Status
- Execute the solve: `status = solver.Solve()`.
- Check for `OPTIMAL` or `FEASIBLE` status. For non-optimal statuses, provide detailed error information and avoid attempting to extract a solution.

### Step 3 - Extract and Validate Solution
- Extract the objective value: `opt_cost = solver.Objective().Value()`.
- Extract variable values, filtering for non-zero values above a small tolerance (e.g., `1e-6`) for cleaner output.
- Implement a verification function that recomputes each constraint's total from the solution and compares it against the bounds with a tolerance (e.g., `1e-5`). Report any violations.

### Step 4 - Output Structured Results
- Print the objective value with a clear prefix (e.g., `RESULT: {opt_cost}`).
- Print non-zero decision variables.
- Print a summary of constraint satisfaction.

### Code Usage
```python
# Solve the model
status = solver.Solve()

# Check solver status
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    opt_cost = solver.Objective().Value()
    print(f'RESULT: {opt_cost}')
    
    # Extract non-zero variables
    for i in range(num_items):
        val = x[i].solution_value()
        if val > 1e-6:
            print(f'  x[{i}] = {val}')
    
    # Verify constraints
    tolerance = 1e-5
    for r in range(num_requirements):
        total = 0.0
        for i in range(num_items):
            total += coefficient_matrix[i][r] * x[i].solution_value()
        if total < lower_bound[r] - tolerance:
            print(f'VIOLATION (min): requirement {r}, total {total} < bound {lower_bound[r]}')
        if total > upper_bound[r] + tolerance:
            print(f'VIOLATION (max): requirement {r}, total {total} > bound {upper_bound[r]}')
else:
    print(f'Solver failed with status: {status}')
```

### Common Pitfalls
- Assuming `FEASIBLE` status guarantees optimality; it does not.
- Not using a tolerance when checking constraint satisfaction, leading to false violation reports due to floating-point precision.
- Attempting to access `.solution_value()` on variables when the solver status is not `OPTIMAL` or `FEASIBLE`, causing crashes.

# Workflow 2 (Modeling Language - Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses a high-level modeling language (Pyomo) to declaratively define the optimization problem. It separates the abstract model from the data, enhancing readability and maintainability for complex problems.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `model.items` and `model.requirements`.
- Declare `Param` objects for `model.cost`, `model.min_req`, `model.max_req`, and `model.coefficient` indexed appropriately.

### Step 2 - Declare Non-Negative Decision Variables
- Create a `Var` object for `model.x`, indexed by `model.items`, with `domain=pyo.NonNegativeReals`.

### Step 3 - Construct Double-Sided Constraints via Rules
- Define two `Constraint` components, indexed by `model.requirements` (e.g., `model.min_constraint` and `model.max_constraint`).
- For each, write a rule function that returns the linear expression `sum(model.coefficient[i, r] * model.x[i] for i in model.items)` and the appropriate inequality (`>=` or `<=`) with the bound parameter.

### Step 4 - Define Linear Objective Function
- Create an `Objective` component with `sense=pyo.minimize`.
- Set the expression to `sum(model.cost[i] * model.x[i] for i in model.items)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of items (e.g., foods)."},
    {"name": "R", "description": "Set of requirements (e.g., nutrients)."}
  ],
  "parameters": [
    {"name": "c", "index": "I", "description": "Cost per unit of item."},
    {"name": "L", "index": "R", "description": "Lower limit for each requirement."},
    {"name": "U", "index": "R", "description": "Upper limit for each requirement."},
    {"name": "a", "index": ["I", "R"], "description": "Amount of requirement r provided by one unit of item i."}
  ],
  "decision_variables": [
    {"name": "x", "index": "I", "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(c[i] * x[i] for i in I)"
  },
  "constraints": [
    {"name": "meet_min", "index": "R", "expression": "sum(a[i, r] * x[i] for i in I) >= L[r]"},
    {"name": "respect_max", "index": "R", "expression": "sum(a[i, r] * x[i] for i in I) <= U[r]"}
  ]
}
```

### Common Pitfalls
- Defining constraint rules that modify global state or have side effects, leading to unpredictable behavior.
- Using mutable data structures (like lists) directly inside Pyomo `Param` declarations without proper initialization.
- Confusing the index order in the coefficient parameter `a[i, r]`, which must match the summation in the constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an efficient LP solver (e.g., HiGHS, CBC) via a solver factory, with configuration for optimality and runtime, followed by validation of the results.

### Step 1 - Instantiate Solver with Configuration
- Create a solver object: `solver = pyo.SolverFactory('appsi_highs')` or `solver = pyo.SolverFactory('cbc')`.
- Set solver options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`. For exact optimality, set `solver.options['ratio'] = 0.0` (CBC) or equivalent optimality tolerance.

### Step 2 - Solve and Inspect Termination
- Execute the solve: `results = solver.solve(model, tee=False)`.
- Check the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`). Accept `optimal` or `feasible` conditions.

### Step 3 - Extract and Verify Solution
- Access the objective value: `model.obj()`.
- Iterate through `model.x` to extract variable values, reporting those above a small tolerance.
- Recompute each constraint's total from the solution variable values and compare against bounds with tolerance to validate feasibility.

### Step 4 - Standardize Output and Handle Failures
- Print results in a consistent, parseable format (e.g., `RESULT: {obj_value}`).
- For failed solves, output a structured error message indicating infeasibility or solver error.

### Code Usage
```python
# Solve the model
results = solver.solve(model)

# Check termination condition
from pyomo.environ import TerminationCondition, SolverStatus
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    
    obj_value = pyo.value(model.obj)
    print(f'RESULT: {obj_value}')
    
    # Print non-zero variables
    for i in model.I:
        val = pyo.value(model.x[i])
        if val > 1e-6:
            print(f'  x[{i}] = {val}')
    
    # Verify constraints
    tolerance = 1e-5
    for r in model.R:
        total = sum(pyo.value(model.a[i, r]) * pyo.value(model.x[i]) for i in model.I)
        if total < pyo.value(model.L[r]) - tolerance:
            print(f'VIOLATION (min): requirement {r}, total {total} < bound {pyo.value(model.L[r])}')
        if total > pyo.value(model.U[r]) + tolerance:
            print(f'VIOLATION (max): requirement {r}, total {total} > bound {pyo.value(model.U[r])}')
else:
    print('infeasible_or_error', results.solver)
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially accepting suboptimal or failed solutions.
- Accessing `pyo.value` on an undefined variable if the solver did not produce a solution.
- Setting an overly strict optimality gap (`ratio=0.0`) on large problems, causing excessive solve times; use a small positive tolerance (e.g., `1e-6`) if needed.
