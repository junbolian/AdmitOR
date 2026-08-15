---
name: BudgetedMaximumCoverage
description: |
  Model and solve budgeted maximum coverage problems using binary selection and coverage indicator variables with linear activation constraints, maximizing weighted coverage under a cost budget.
---

# Workflow 1 (CP-SAT via OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, designed for constraint programming and integer optimization. It is well-suited for binary decision problems with logical constraints, offering robust performance and easy-to-use Python APIs.

### Step 1 - Define Variables
- Create binary selection variables for each candidate item using `model.NewBoolVar()`.
- Create auxiliary binary coverage indicator variables for each demand element using `model.NewBoolVar()`.

### Step 2 - Enforce Budget Constraint
- Add a linear constraint: the sum of selection variable values multiplied by their costs must be less than or equal to the budget parameter.

### Step 3 - Link Coverage to Selection
- For each demand element, add a linear constraint: the coverage indicator variable must be less than or equal to the sum of the selection variables for all items that can cover it.

### Step 4 - Formulate Objective
- Set the objective to maximize the weighted sum of all coverage indicator variables, where weights represent the benefit of covering each element.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "J: set of demand elements to cover"
  ],
  "parameters": [
    "cost_i: cost of selecting item i ∈ I",
    "weight_j: benefit weight for covering element j ∈ J",
    "budget: total cost budget",
    "coverage_map_j: list of item indices i ∈ I that can cover element j"
  ],
  "decision_variables": [
    "x_i ∈ {0,1}: 1 if item i is selected",
    "y_j ∈ {0,1}: 1 if element j is covered"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight_j * y_j for j in J)"
  },
  "constraints": [
    "budget_limit: sum(cost_i * x_i for i in I) <= budget",
    "coverage_activation_j: y_j <= sum(x_i for i in coverage_map_j) for all j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to define the coverage mapping as a list-of-lists or dictionary, leading to incorrect constraint generation.
- Using `model.NewIntVar(0, 1, ...)` instead of `model.NewBoolVar()` for binary variables, which is less efficient.
- Setting an optimality gap (`relative_gap_limit`) greater than zero when an exact optimal solution is required.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver with parameters for time limits, parallelism, and optimality tolerance. Extract and validate the solution, ensuring the solver status indicates success.

### Step 1 - Configure Solver
- Instantiate `cp_model.CpSolver()`.
- Set key parameters: `max_time_in_seconds` for runtime control, `num_search_workers` for parallelism, and `random_seed` for reproducibility.
- For exact solutions, set `relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check if the returned status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before proceeding. Handle `INFEASIBLE` or `UNKNOWN` statuses with appropriate error messages.

### Step 3 - Extract Solution
- For each binary variable, retrieve its value using `solver.Value(variable)`.
- Build a list of selected items where `solver.Value(x_i) == 1`.
- Build a list of covered elements where `solver.Value(y_j) == 1`.
- Compute the total cost and objective value from the variable values for verification.

### Step 4 - Verify Solution
- Programmatically verify that the budget constraint is satisfied by the selected items.
- For each element marked as covered, verify that at least one selected item is in its coverage map.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... create variables, add constraints, set objective ...

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected_items = [i for i in I if solver.Value(x[i]) == 1]
    covered_elements = [j for j in J if solver.Value(y[j]) == 1]
    total_cost = sum(cost[i] for i in selected_items)
    obj_value = solver.ObjectiveValue()
    # ... output results ...
else:
    print(f"Solver failed with status: {status}")
    # ... handle infeasible or error case ...
```

### Common Pitfalls
- Not checking solver status before accessing `solver.Value()` or `solver.ObjectiveValue()`, which can cause runtime errors.
- Misinterpreting `FEASIBLE` as suboptimal; it is a valid solution but not proven optimal if the time limit was reached.
- Overlooking the need to verify coverage logic post-solve, which can catch modeling errors in the constraint generation.

# Workflow 2 (MILP via Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to formulate the problem as a Mixed-Integer Linear Program (MILP). It connects to external solvers (e.g., CBC, Gurobi) via a standardized interface, offering flexibility and access to advanced solver features.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for items and demand elements.
- Declare Pyomo `Param` objects for costs, weights, budget, and a `coverage_map` parameter defining the covering relationships.

### Step 2 - Create Binary Variables
- Define a `Var` with `domain=pyo.Binary` for each selection decision.
- Define a `Var` with `domain=pyo.Binary` for each coverage indicator.

### Step 3 - Add Budget Constraint
- Use a `Constraint` rule to enforce the sum of `cost_i * x_i` is less than or equal to the budget.

### Step 4 - Add Coverage Activation Constraints
- For each demand element, add a `Constraint` enforcing `y_j <= sum(x_i for i in coverage_map[j])`.

### Step 5 - Define Objective
- Set the model's objective to maximize `sum(weight_j * y_j)` using `pyo.maximize`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "J: set of demand elements to cover"
  ],
  "parameters": [
    "cost: dict mapping i ∈ I to cost",
    "weight: dict mapping j ∈ J to benefit weight",
    "budget: scalar budget value",
    "coverage: dict mapping j ∈ J to list of i ∈ I"
  ],
  "decision_variables": [
    "x[i] ∈ {0,1}: selection variable",
    "y[j] ∈ {0,1}: coverage indicator variable"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[j] * y[j] for j in J)"
  },
  "constraints": [
    "budget_limit: sum(cost[i] * x[i] for i in I) <= budget",
    "coverage_activation: y[j] <= sum(x[i] for i in coverage[j]) for all j in J"
  ]
}
```

### Common Pitfalls
- Defining the `coverage` parameter as a dense matrix instead of a sparse dictionary, leading to memory issues for large problems.
- Using `==` instead of `<=` in the coverage activation constraint, which incorrectly forces coverage if any covering item is selected.
- Not initializing all Pyomo parameters before model instantiation, causing runtime errors.

## Solving stage

### Strategy Overview
Instantiate a solver via Pyomo's `SolverFactory`, configure it with time limits and optimality gap settings, solve the model, and rigorously check the solver status and termination condition before extracting results.

### Step 1 - Select and Configure Solver
- Use `SolverFactory('solver_name')` (e.g., `'cbc'`, `'gurobi'`).
- Set solver options: `time_limit` (or `tmlim`), `threads` for parallelism, and `mipgap` (or `ratio`) to 0.0 for exact solutions.

### Step 2 - Solve and Inspect Termination
- Call `results = solver.solve(model, tee=False)`.
- Check both `results.solver.status` (should be `SolverStatus.ok`) and `results.solver.termination_condition` (should be `TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Threshold Variables
- Retrieve variable values using `pyo.value(m.x[i])`.
- Use a threshold (e.g., `> 0.5`) to determine the binary state, accounting for solver floating-point precision.
- Build lists of selected items and covered elements based on the thresholded values.

### Step 4 - Validate and Report
- Compute the total cost and objective value from the extracted solution.
- Perform a quick sanity check that the budget constraint and coverage logic hold.
- Output results in a structured format (e.g., JSON) for downstream processing.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=ITEM_INDICES)
model.J = pyo.Set(initialize=ELEMENT_INDICES)
# ... define parameters, variables, constraints, objective ...

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 300
solver.options['ratio'] = 0.0
solver.options['threads'] = 8

results = solver.solve(model)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    covered_elements = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
    total_cost = sum(cost[i] for i in selected_items)
    obj_value = pyo.value(model.objective)
    # ... output results ...
else:
    print(f"Solver failed: {results.solver.termination_condition}")
    # ... handle infeasible or error case ...
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (the solver ran) with `TerminationCondition.optimal` (it found an optimal solution), leading to acceptance of suboptimal or infeasible results.
- Not using a threshold when reading binary variable values, causing misclassification due to tiny numerical errors (e.g., 0.999999 vs 1.0).
- Forgetting to set the `ratio` or `mipgap` parameter to zero, resulting in early termination with a suboptimal solution.
