---
name: Budgeted Set Coverage
description: |
  Model and solve binary selection problems with coverage objectives under a knapsack constraint using either CP-SAT or Pyomo MILP frameworks.

---

# Workflow 1 (CP-SAT with Logical Implications)

## Modeling stage

### Strategy Overview
This workflow models the problem using OR-Tools CP-SAT, leveraging its native support for Boolean logic to encode coverage relationships directly. The strategy separates selection and coverage variables, using `AddBoolOr` constraints to enforce logical implications efficiently.

### Step 1 - Define Variables and Data Mapping
- Create two sets of binary decision variables: `x[i]` for selecting items and `y[j]` for covering targets.
- Map coverage relationships using a dictionary `coverage_map[j] = [i1, i2, ...]` listing which items can cover each target.
- Store parameters: `cost[i]` for item cost, `weight[j]` for target benefit, and `budget` as a scalar.

### Step 2 - Formulate Budget Constraint
- Add a linear knapsack constraint: `sum(cost[i] * x[i] for i in items) <= budget`.

### Step 3 - Enforce Coverage Logic
- For each target `j`, add a logical constraint: `model.AddBoolOr([y[j].Not()] + [x[i] for i in coverage_map[j]])`. This ensures `y[j]` can be 1 only if at least one covering `x[i]` is 1.

### Step 4 - Define Objective
- Set the objective to maximize the weighted sum of coverage: `model.Maximize(sum(weight[j] * y[j] for j in targets))`.

### Formulation Template
```json
{
  "sets": ["items", "targets"],
  "parameters": ["cost[items]", "weight[targets]", "budget", "coverage_map[targets] -> list[items]"],
  "decision_variables": ["x[items] ∈ {0,1}", "y[targets] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[j] * y[j] for j in targets)"
  },
  "constraints": [
    "sum(cost[i] * x[i] for i in items) <= budget",
    "for each j in targets: y[j] implies (sum(x[i] for i in coverage_map[j]) >= 1)"
  ]
}
```

### Common Pitfalls
- Forgetting to add `.Not()` to the coverage variable in the `AddBoolOr` list, which incorrectly forces coverage.
- Using integer arithmetic for the budget constraint instead of the solver's linear sum, risking overflow or performance issues.
- Not providing a clear mapping from target indices to covering item indices, leading to constraint construction errors.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured time and optimality limits. Extract solution values, validate constraint satisfaction, and output structured results.

### Step 1 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds = <time_limit>` to ensure termination.
- Use `solver.parameters.num_search_workers = <num_cores>` for parallel search.
- Set `solver.parameters.random_seed = <seed>` for reproducibility and `solver.parameters.relative_gap_limit = 0.0` for exact solutions.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)` and capture the result status.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before extracting values.

### Step 3 - Extract and Validate Solution
- Retrieve selected items: `[i for i in items if solver.Value(x[i]) == 1]`.
- Retrieve covered targets: `[j for j in targets if solver.Value(y[j]) == 1]`.
- Manually verify that each covered target has at least one selected item from its covering set.

### Step 4 - Output Structured Results
- Print a JSON payload containing solver status, objective value, selected items, covered targets, total cost, and total benefit.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (variable and constraint creation)
# solve with status / termination checks
solver = cp_model.CpSolver()
# ... (set parameters)
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    obj_val = solver.ObjectiveValue()
    selected = [i for i in items if solver.Value(x[i]) == 1]
    # ... (extract and validate)
else:
    # handle infeasible or error status
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, missing valid but non-optimal solutions.
- Assuming variable values are integers without calling `solver.Value()`, leading to type errors.
- Omitting post-solve validation, which can miss modeling errors where constraints are incorrectly formulated.

# Workflow 2 (Pyomo MILP with Linear Constraints)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to formulate the problem as a Mixed-Integer Linear Program (MILP). Coverage relationships are encoded as linear inequality constraints, and the model is solved via an external MILP solver like HiGHS or CBC.

### Step 1 - Define Sets and Parameters
- Create Pyomo Sets for `items` and `targets`.
- Define Parameters: `cost`, `weight`, `budget`, and a `coverage_map` (as a dictionary or rule-based function).

### Step 2 - Create Binary Variables
- Instantiate `model.x = pyo.Var(items, domain=pyo.Binary)` for selection.
- Instantiate `model.y = pyo.Var(targets, domain=pyo.Binary)` for coverage.

### Step 3 - Formulate Linear Coverage Constraints
- For each target `j`, add a constraint: `model.y[j] <= sum(model.x[i] for i in coverage_map[j])`. This linear inequality enforces the logical implication.

### Step 4 - Add Budget Constraint and Objective
- Add budget constraint: `sum(cost[i] * model.x[i] for i in items) <= budget`.
- Set objective: `model.obj = pyo.Objective(expr=sum(weight[j] * model.y[j] for j in targets), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["items", "targets"],
  "parameters": ["cost[items]", "weight[targets]", "budget", "coverage_map[targets] -> list[items]"],
  "decision_variables": ["x[items] ∈ {0,1}", "y[targets] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[j] * y[j] for j in targets)"
  },
  "constraints": [
    "sum(cost[i] * x[i] for i in items) <= budget",
    "for each j in targets: y[j] <= sum(x[i] for i in coverage_map[j])"
  ]
}
```

### Common Pitfalls
- Using Pyomo's `Param` with mutable data without proper initialization, causing indexing errors.
- Writing coverage constraints that incorrectly sum over all items instead of only the covering subset, leading to invalid models.
- Forgetting to set the objective sense to `maximize`, defaulting to minimization.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver via the `SolverFactory`. Configure solver options, check termination conditions, and extract solution values for validation and reporting.

### Step 1 - Select and Configure Solver
- Instantiate solver: `solver = pyo.SolverFactory('<solver_name>')` (e.g., 'highs', 'cbc').
- Set options: `solver.options['time_limit'] = <time_limit>`, `solver.options['mip_rel_gap'] = 0.0` for exact solutions, and `solver.options['threads'] = <num_threads>`.

### Step 2 - Solve and Inspect Results
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Extract Solution Values
- Retrieve objective value: `obj_val = pyo.value(model.obj)`.
- Extract selected items: `[i for i in items if pyo.value(model.x[i]) > 0.5]`.
- Extract covered targets: `[j for j in targets if pyo.value(model.y[j]) > 0.5]`.

### Step 4 - Validate and Report
- Compute total cost from selected items and verify it does not exceed budget.
- Ensure each covered target has at least one selected covering item.
- Output results in a structured format (e.g., dictionary or JSON).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (set, parameter, variable, constraint, objective definition)
# solve with status / termination checks
solver = pyo.SolverFactory('<solver_name>')
# ... (set solver options)
results = solver.solve(model)
if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    obj_val = pyo.value(model.obj)
    selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
    # ... (extract and validate)
else:
    # handle solver failure or infeasibility
```

### Common Pitfalls
- Setting `mip_rel_gap = -1.0` (a common default) instead of `0.0` for exact solutions, leading to early termination.
- Comparing `pyo.value(var)` to `1` exactly; use `> 0.5` to avoid floating-point precision issues.
- Not checking both solver status and termination condition, potentially processing results from failed solves.
