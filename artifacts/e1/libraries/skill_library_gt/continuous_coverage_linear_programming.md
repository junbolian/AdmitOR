---
name: Continuous Coverage Linear Programming
description: |
  Model and solve linear programs with continuous decision variables, linear objective, and double-sided linear constraints for coverage problems, using either direct solver APIs or algebraic modeling languages.

---

# Workflow 1 (Direct Solver API with Google OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as a standard linear program using a low-level solver API. This approach directly maps the mathematical model to solver objects, offering fine-grained control and immediate feedback, suitable for prototyping and integration into larger systems.

### Step 1 - Define Sets and Parameters
- Identify the two fundamental index sets: `ITEMS` for selectable resources and `REQUIREMENTS` for coverage criteria.
- Organize data into parameter arrays: `cost[ITEMS]`, `min_req[REQUIREMENTS]`, `max_req[REQUIREMENTS]`, and a 2D `contribution[ITEMS][REQUIREMENTS]` matrix.

### Step 2 - Create Continuous Decision Variables
- Instantiate a continuous, non-negative decision variable for each item, representing the amount selected.
- Apply explicit lower and upper bounds (e.g., `0` and `max_amount`) to each variable during creation.

### Step 3 - Formulate Linear Objective
- Construct the objective function as the sum of `cost[i] * variable[i]` over all items.
- Set the optimization sense to minimization.

### Step 4 - Implement Double-Sided Coverage Constraints
- For each requirement, create two separate linear constraints: one for the minimum and one for the maximum.
- Express each constraint as a linear combination: `sum(contribution[i][r] * variable[i] for i in ITEMS)` compared to the bound.

### Formulation Template
```json
{
  "sets": ["ITEMS", "REQUIREMENTS"],
  "parameters": [
    "cost[ITEMS]",
    "min_req[REQUIREMENTS]",
    "max_req[REQUIREMENTS]",
    "contribution[ITEMS][REQUIREMENTS]"
  ],
  "decision_variables": ["Amount[ITEMS] (Continuous, NonNegative, Bounded)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * Amount[i] for i in ITEMS)"
  },
  "constraints": [
    "sum(contribution[i][r] * Amount[i] for i in ITEMS) >= min_req[r] for each r in REQUIREMENTS",
    "sum(contribution[i][r] * Amount[i] for i in ITEMS) <= max_req[r] for each r in REQUIREMENTS"
  ]
}
```

### Common Pitfalls
- Forgetting to set upper bounds on variables, which may be implicitly infinite and lead to unbounded problems.
- Creating constraints with the wrong index order, leading to shape mismatches (e.g., `contribution[r][i]` instead of `contribution[i][r]`).
- Not using a tolerance (e.g., `1e-6`) when checking constraint satisfaction post-solve due to numerical precision.

## Solving stage

### Strategy Overview
Utilize the Google OR-Tools wrapper for the GLOP solver, following a standard workflow of building the model, solving, and rigorously checking the solution status and feasibility.

### Step 1 - Initialize Solver and Build Model
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Use loops over the defined sets to create variables, set the objective, and add constraints as per the modeling stage.

### Step 2 - Solve and Check Status
- Invoke `solver.Solve()` and capture the result status.
- Check for `OPTIMAL` or `FEASIBLE` status; handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate diagnostics.

### Step 3 - Extract and Verify Solution
- Extract variable values using `.solution_value()`.
- Programmatically recalculate the left-hand side of all constraints to verify they are satisfied within a small numerical tolerance.
- Filter solution to report only variables with values above a tolerance (e.g., `1e-6`) to ignore numerical noise.

### Step 4 - (Optional) Cross-Verify with Alternative Solver
- Solve the same model using a different solver (e.g., `CBC` via OR-Tools) to verify solution consistency and robustness against solver-specific numerical behaviors.

### Code Usage
```python
# Example using Google OR-Tools' GLOP
from ortools.linear_solver import pywraplp

# 1. Initialize Solver
solver = pywraplp.Solver.CreateSolver('GLOP')

# 2. Build Model (following Formulation Template)
# ... Create variables `x[i]` with `solver.NumVar(lb, ub, name)`
# ... Set objective with `solver.Objective().SetMinimization()` and `SetCoefficient`
# ... Add constraints with `solver.Add(sum_expr >= min_req[r])`

# 3. Solve and Check Status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    # 4. Extract and Verify
    solution = {}
    for i in ITEMS:
        val = x[i].solution_value()
        if val > 1e-6:  # Filter negligible values
            solution[i] = val
    # ... Recalculate constraint totals for verification
else:
    print(f"Solver did not find a feasible solution. Status: {status}")
```

### Common Pitfalls
- Assuming a `FEASIBLE` status implies optimality; `OPTIMAL` is the desired status for cost minimization.
- Not setting a time limit for larger instances, which may cause the solver to run indefinitely.
- Misinterpreting variable bounds as constraints; they are treated differently by the solver.

# Workflow 2 (Algebraic Modeling with Pyomo and HiGHS)

## Modeling stage

### Strategy Overview
Use the Pyomo algebraic modeling language to declaratively define the optimization model. This approach separates model logic from data, improves readability and maintainability, and leverages Pyomo's built-in features like range constraints.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for `model.ITEMS` and `model.REQUIREMENTS`.
- Declare `Param` objects for all input data (`cost`, `min_req`, `max_req`, `contribution`), indexed by the appropriate sets.

### Step 2 - Define Bounded Continuous Variables
- Create a `Var` object (e.g., `model.Amount`) indexed by `ITEMS`, with domain `pyo.NonNegativeReals`.
- Specify individual bounds `(0, max_amount)` directly in the variable declaration.

### Step 3 - Construct Objective Function
- Define the objective as a `pyo.Objective` with the expression `sum(model.cost[i] * model.Amount[i] for i in model.ITEMS)` and sense `pyo.minimize`.

### Step 4 - Implement Efficient Range Constraints
- For each requirement, create a single `pyo.Constraint` using a three-part inequality `(lower, expression, upper)`.
- This encapsulates both min and max bounds in one constraint, reducing model size.

### Formulation Template
```json
{
  "sets": ["ITEMS", "REQUIREMENTS"],
  "parameters": [
    "cost[ITEMS]",
    "min_req[REQUIREMENTS]",
    "max_req[REQUIREMENTS]",
    "contribution[ITEMS][REQUIREMENTS]"
  ],
  "decision_variables": ["Amount[ITEMS] (NonNegativeReals, Bounded)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * Amount[i] for i in ITEMS)"
  },
  "constraints": [
    "(min_req[r], sum(contribution[i][r] * Amount[i] for i in ITEMS), max_req[r]) for each r in REQUIREMENTS"
  ]
}
```

### Common Pitfalls
- Incorrectly initializing `Param` objects with data that doesn't match the set indices, causing runtime errors.
- Using separate min and max constraints when a single range constraint is more efficient and numerically stable.
- Forgetting to call `pyo.value()` to evaluate Pyomo expressions when extracting results.

## Solving stage

### Strategy Overview
Employ the HiGHS solver through Pyomo's `SolverFactory`, configuring it for performance and reliability. Focus on proper handling of solver status and termination conditions to robustly interpret results.

### Step 1 - Instantiate Solver and Configure Options
- Create a solver object: `solver = pyo.SolverFactory('highs')`.
- Set practical options like `time_limit` and ensure `presolve` is enabled.

### Step 2 - Solve and Interpret Status Codes
- Call `results = solver.solve(model, tee=False)`.
- Check both `results.solver.status` (`ok`) and `results.solver.termination_condition` (`optimal`, `feasible`). Both must be satisfactory.

### Step 3 - Validate Solution Feasibility
- Extract variable values into a plain dictionary.
- Write a verification function that recalculates all constraint expressions and checks them against the bounds with tolerance.

### Step 4 - Analyze Solution Structure
- Identify which items have non-zero values in the optimal solution to understand active resources.
- For problems with exact requirements (min == max), verify the solution satisfies the equality tightly.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build Model (following Formulation Template)
model = pyo.ConcreteModel()
model.ITEMS = pyo.Set(initialize=items_list)
model.REQUIREMENTS = pyo.Set(initialize=reqs_list)
# ... Define all Parameters, Variables, Objective, and Range Constraints

# 2. Solve with HiGHS
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

# 3. Check Status and Termination
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = pyo.value(model.obj)  # Assuming objective named 'obj'
    # 4. Extract Solution
    solution = {i: pyo.value(model.Amount[i]) for i in model.ITEMS}
    # ... Call verification function on `solution`
else:
    # Handle infeasibility or other failures
    print(f"Solver failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Relying only on the solver status without checking the termination condition, potentially accepting suboptimal or timed-out solutions.
- Not setting a `time_limit`, risking long execution times for large or numerically difficult instances.
- Attempting to access variable values directly (`model.Amount[i]`) without using `pyo.value()`, which returns the Pyomo variable object, not its numerical value.
