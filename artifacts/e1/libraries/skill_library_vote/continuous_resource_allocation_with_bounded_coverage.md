---
name: Continuous Resource Allocation with Bounded Coverage
description: |
  Model and solve linear optimization problems with continuous decision variables, linear cost minimization, and double-sided coverage constraints using structured formulation patterns and solver-agnostic implementation.

---

# Workflow 1 (LP with OR-Tools / pywraplp)

## Modeling stage

### Strategy Overview
Formulate the problem as a standard Linear Program (LP) using the OR-Tools linear solver wrapper. This approach is ideal for continuous-only problems and provides a clean, imperative API for model construction, suitable for quick prototyping and integration into larger systems.

### Step 1 - Define Index Sets and Parameters
- Declare clear index sets for items (e.g., `items`) and requirements (e.g., `requirements`) to structure all subsequent data.
- Organize all problem data into parameter arrays: `cost[item]`, `min_coverage[requirement]`, `max_coverage[requirement]`, and `contribution[item][requirement]`.

### Step 2 - Create Continuous Decision Variables
- Instantiate continuous decision variables (e.g., `amount[item]`) using `solver.NumVar`.
- Specify explicit lower and upper bounds for each variable directly in its declaration (e.g., `lb=0`, `ub=max_amount`) to reduce model complexity.

### Step 3 - Implement Double-Sided Coverage Constraints
- For each requirement, create two separate linear constraints: a lower bound (`sum(contribution * amount) >= min_coverage`) and an upper bound (`sum(contribution * amount) <= max_coverage`).
- Use list comprehensions or loops to build constraints efficiently across all requirements.

### Step 4 - Formulate Linear Cost Objective
- Define the objective function as the sum of cost per item multiplied by the decision variable: `minimize sum(cost[item] * amount[item])`.
- Set the objective sense to minimization and assign coefficients to each variable.

### Formulation Template
```json
{
  "sets": [
    "items",
    "requirements"
  ],
  "parameters": {
    "cost": {"index": "items", "type": "float"},
    "min_coverage": {"index": "requirements", "type": "float"},
    "max_coverage": {"index": "requirements", "type": "float"},
    "contribution": {"index": ["items", "requirements"], "type": "float"}
  },
  "decision_variables": [
    {"name": "amount", "index": "items", "type": "continuous", "bounds": ["lb", "ub"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * amount[i] for i in items)"
  },
  "constraints": [
    {"name": "min_coverage_constr", "index": "requirements", "expression": "sum(contribution[i][r] * amount[i] for i in items) >= min_coverage[r]"},
    {"name": "max_coverage_constr", "index": "requirements", "expression": "sum(contribution[i][r] * amount[i] for i in items) <= max_coverage[r]"}
  ]
}
```

### Common Pitfalls
- Forgetting to set upper bounds on variables, which can lead to unbounded solutions.
- Creating separate constraints for each bound when a single range constraint would be more efficient.
- Not using consistent indexing between parameters and variables, leading to dimension mismatch errors.

## Solving stage

### Strategy Overview
Solve the constructed LP model using the OR-Tools wrapper, defaulting to the `GLOP` solver for pure continuous problems. The workflow includes robust solution status checking, result extraction, and validation.

### Step 1 - Instantiate Solver and Build Model
- Create a solver instance with `pywraplp.Solver.CreateSolver('GLOP')`.
- Programmatically build the model using the steps defined in the modeling stage.

### Step 2 - Solve and Check Status
- Execute `solver.Solve()`.
- Check the result status using `solver.OPTIMAL` or `solver.FEASIBLE`. Handle infeasible or unbounded statuses with appropriate error messages or fallback logic.

### Step 3 - Extract and Validate Solution
- If optimal or feasible, extract the objective value via `solver.Objective().Value()`.
- Retrieve variable values by iterating over the decision variable objects.
- Programmatically verify that the solution satisfies all constraints within a numerical tolerance (e.g., `1e-6`).

### Step 4 - Output Structured Results
- Format the results into a structured dictionary or JSON object containing the objective value, non-zero variable values, and constraint satisfaction metrics.
- This facilitates easy parsing, logging, or passing to downstream processes.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# ... [Build model: define variables, constraints, objective]

# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL or status == solver.FEASIBLE:
    objective_value = solver.Objective().Value()
    # Extract variable values
    solution = {var.name(): var.solution_value() for var in ...}
    # Validate constraints
    # ... validation logic
    print(f"Optimal cost: {objective_value}")
else:
    print('The problem does not have an optimal solution.')
```

### Common Pitfalls
- Assuming `solver.Solve()` always returns an optimal solution without checking the status code.
- Not handling numerical precision issues when comparing constraint satisfaction, leading to false infeasibility flags.
- Hard-coding solver names (like 'GLOP'), which reduces portability; consider making the solver name a configurable parameter.

# Workflow 2 (LP with Pyomo and Range Constraints)

## Modeling stage

### Strategy Overview
Model the problem in Pyomo, leveraging its abstract modeling capabilities and support for range constraints. This approach is well-suited for problems where constraints naturally have both lower and upper bounds, and it integrates seamlessly with a wide variety of solvers.

### Step 1 - Define Abstract Sets and Parameters
- Use Pyomo's `Set` and `Param` components to declaratively define index sets (`items`, `requirements`) and parameters (`cost`, `min_coverage`, `max_coverage`, `contribution`).
- This promotes a clean separation of model structure from data.

### Step 2 - Declare Continuous Variables with Bounds
- Create a Pyomo `Var` object for the decision variable (e.g., `model.amount`), indexed by the items set.
- Specify the variable domain as `NonNegativeReals` and optionally set upper bounds using a `bounds=` rule or a separate parameter.

### Step 3 - Implement Range Constraints for Coverage
- For each requirement, create a single range constraint using Pyomo's syntax: `model.coverage_constraint[req] = Constraint(expr=(min_coverage[req], sum(...), max_coverage[req]))`.
- This is more concise and can be more efficient for the solver than separate inequality constraints.

### Step 4 - Define the Linear Objective
- Use Pyomo's `Objective` component to define the cost minimization objective: `model.total_cost = Objective(expr=sum(cost[i] * model.amount[i] for i in items), sense=minimize)`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "requirements"
  ],
  "parameters": {
    "cost": {"index": "items", "type": "Param"},
    "min_coverage": {"index": "requirements", "type": "Param"},
    "max_coverage": {"index": "requirements", "type": "Param"},
    "contribution": {"index": ["items", "requirements"], "type": "Param"}
  },
  "decision_variables": [
    {"name": "amount", "index": "items", "type": "Var", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum(cost[i] * amount[i] for i in items)"
  },
  "constraints": [
    {"name": "coverage_constraint", "index": "requirements", "type": "range", "expression": "(min_coverage[r], sum(contribution[i][r] * amount[i] for i in items), max_coverage[r])"}
  ]
}
```

### Common Pitfalls
- Incorrectly ordering the tuple in a Pyomo range constraint (should be `(lower, expression, upper)`).
- Not initializing all Pyomo `Param` objects with data before solving, which leads to runtime errors.
- Using mutable Python data structures (like lists) directly within Pyomo expressions instead of using Pyomo components.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., CBC, GLPK, or commercial solvers). This workflow emphasizes solver configuration, solution loading patterns, and post-solution validation for production robustness.

### Step 1 - Instantiate Solver and Configure Options
- Create a solver object using `SolverFactory('solver_name')` (e.g., `'cbc'` for LP).
- Configure solver options such as time limit (`seconds`), optimality tolerance, and to disable presolve if needed for debugging.

### Step 2 - Solve and Inspect Termination Condition
- Execute `results = solver.solve(model, ...)`.
- Check both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`) to distinguish between optimal, feasible, infeasible, or other outcomes.

### Step 3 - Load and Validate Solution
- If the solve was successful, load the solution into the model using `model.solutions.load_from(results)`.
- Programmatically loop through constraints to verify they are satisfied within tolerance using the solved variable values.

### Step 4 - Extract and Report Results
- Extract the objective value from `model.total_cost()`.
- Create a structured results dictionary, optionally converting floating-point values to exact fractions using `Fraction.limit_denominator()` for clarity.
- Output key metrics including the objective, non-zero variables, and constraint slack/surplus.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... [Define sets, params, variables, constraints, objective]

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    # Solution is optimal
    objective_value = pyo.value(model.total_cost)
    # Process variable values: model.amount[i]()
    # Validate constraints
else:
    # Handle infeasible, unbounded, or other statuses
    print(f"Solver terminated with status: {results.solver.termination_condition}")
```

### Common Pitfalls
- Accessing variable values (`model.var[i]`) before loading the solution, which returns `None`.
- Confusing `SolverStatus.ok` (solver ran normally) with `TerminationCondition.optimal` (found an optimal solution); both checks are necessary.
- Not setting a time limit for large problems, which can cause the process to hang indefinitely.
