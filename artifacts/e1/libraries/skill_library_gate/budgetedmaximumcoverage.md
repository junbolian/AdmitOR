---
name: BudgetedMaximumCoverage
description: |
  Model and solve weighted maximum coverage problems under a budget constraint using binary selection and coverage indicator variables with logical linking constraints.
---

# Workflow 1 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to create a clear, declarative formulation of the budgeted maximum coverage problem. It is designed for integration with high-performance commercial (e.g., Gurobi) or open-source (e.g., HiGHS, CBC) MIP solvers, offering flexibility and robust solution extraction.

### Step 1 - Define Sets and Parameters
- Declare a Pyomo `Set` for the selectable items (e.g., facilities, projects) and another for the coverage requirements (e.g., areas, customers).
- Define `Param` objects for item costs, requirement weights (e.g., population, revenue), the coverage relationship mapping, and the total budget.

### Step 2 - Create Decision Variables
- Create a binary variable `x[j]` for each selectable item `j` to represent the selection decision.
- Create a binary variable `y[i]` for each coverage requirement `i` to indicate whether it is satisfied.

### Step 3 - Formulate Objective and Constraints
- Set the objective to maximize the sum of weighted coverage: `sum(weight[i] * y[i] for i in requirements)`.
- Add a linear budget constraint: `sum(cost[j] * x[j] for j in items) <= budget`.
- For each requirement `i`, add a coverage activation constraint: `y[i] <= sum(x[j] for j in coverage_map[i])`. This ensures coverage is only possible if at least one covering item is selected.

### Formulation Template
```json
{
  "sets": [
    {"name": "items", "description": "Indices for selectable items (e.g., facilities)."},
    {"name": "requirements", "description": "Indices for coverage requirements (e.g., areas)."}
  ],
  "parameters": [
    {"name": "cost", "domain": "items", "description": "Cost of selecting each item."},
    {"name": "weight", "domain": "requirements", "description": "Benefit weight for covering each requirement."},
    {"name": "budget", "domain": "scalar", "description": "Total available budget."},
    {"name": "coverage_map", "domain": "requirements -> list[items]", "description": "Mapping from a requirement to the list of items that can cover it."}
  ],
  "decision_variables": [
    {"name": "x", "domain": "items", "type": "binary", "description": "1 if item is selected."},
    {"name": "y", "domain": "requirements", "type": "binary", "description": "1 if requirement is covered."}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i] * y[i] for i in requirements)"
  },
  "constraints": [
    {"name": "budget_limit", "expression": "sum(cost[j] * x[j] for j in items) <= budget"},
    {"name": "coverage_activation", "domain": "requirements", "expression": "y[i] <= sum(x[j] for j in coverage_map[i])"}
  ]
}
```

### Common Pitfalls
- Using a dense matrix for `coverage_map` when the relationship is sparse, leading to unnecessary memory overhead. Prefer a dictionary mapping requirement indices to lists of covering items.
- Formulating the coverage constraint as `y[i] == sum(...)`, which incorrectly forces coverage to be 1 if any covering item is selected, rather than allowing the solver to decide based on the objective.
- Forgetting to parameterize the budget, making the model less reusable for different scenarios.

## Solving stage

### Strategy Overview
This stage focuses on solving the Pyomo model with a configured MIP solver, handling solver statuses correctly, and extracting and validating the solution. It emphasizes reproducibility and solution verification.

### Step 1 - Configure and Execute Solver
- Instantiate a solver object (e.g., `SolverFactory('gurobi')`, `SolverFactory('highs')`).
- Set key parameters: `time_limit` for runtime control, `mipgap` (or equivalent) to `0.0` for exact optimality, `threads` for parallelism, and `seed` for reproducibility.
- Call `solver.solve(model, tee=True)` to execute and optionally print logs.

### Step 2 - Check Solver Status and Termination
- Verify `solver.status` is `SolverStatus.ok`.
- Check `solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible` before proceeding. Handle other conditions (e.g., `infeasible`, `maxTimeLimit`) with appropriate error messages.

### Step 3 - Extract and Validate Solution
- Extract selected items: `[j for j in model.items if pyo.value(model.x[j]) > 0.5]`.
- Extract covered requirements: `[i for i in model.requirements if pyo.value(model.y[i]) > 0.5]`.
- Calculate total cost and achieved objective value from the extracted variable values.
- Perform an independent verification: check that for every covered requirement, at least one selected item is in its `coverage_map`.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build Model (following the formulation template)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, objective, constraints

# 2. Solve
solver = pyo.SolverFactory('solver_name')  # e.g., 'gurobi', 'highs', 'cbc'
solver.options['time_limit'] = time_limit_seconds
solver.options['mipgap'] = 0.0
# Set other solver-specific options (threads, seed, etc.)
results = solver.solve(model, tee=verbose)

# 3. Check Status and Termination
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    # 4. Extract Solution
    selected_items = [j for j in model.items if pyo.value(model.x[j]) > 0.5]
    covered_reqs = [i for i in model.requirements if pyo.value(model.y[i]) > 0.5]
    total_cost = sum(cost_data[j] for j in selected_items)
    # 5. Validate
    # ... verification logic
else:
    raise Exception(f"Solver failed: Status={status}, Termination={term}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to attempts to extract solutions from failed solves.
- Using a loose `mipgap` when an exact optimal solution is required.
- Extracting variable values without the `pyo.value()` wrapper or using `== 1` instead of `> 0.5` for binary variables, which can fail due to solver tolerances.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, a constraint programming and SAT solver optimized for problems with linear constraints and Boolean variables. It is well-suited for binary decision problems, offering efficient search and native support for logical implications.

### Step 1 - Initialize Model and Create Variables
- Create a `cp_model.CpModel()` object.
- For each selectable item `j`, create a Boolean variable `x[j] = model.NewBoolVar('x_j')`.
- For each coverage requirement `i`, create a Boolean variable `y[i] = model.NewBoolVar('y_i')`.

### Step 2 - Add Budget Constraint
- Create a linear expression for total cost: `sum(cost[j] * x[j] for j in items)`.
- Add the constraint `model.Add(linear_cost_expr <= budget)`.

### Step 3 - Add Coverage Activation Constraints
- For each requirement `i`, create a linear expression representing the sum of covering item variables: `sum(x[j] for j in coverage_map[i])`.
- Add the constraint `model.Add(sum_covering_items >= y[i])`. This enforces the logical implication `y[i] => (at least one x[j] is true)`.

### Step 4 - Define Objective
- Create a linear expression for the weighted coverage: `sum(weight[i] * y[i] for i in requirements)`.
- Call `model.Maximize(weighted_coverage_expr)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "items", "description": "Indices for selectable items."},
    {"name": "requirements", "description": "Indices for coverage requirements."}
  ],
  "parameters": [
    {"name": "cost", "domain": "items", "description": "Cost of selecting each item."},
    {"name": "weight", "domain": "requirements", "description": "Benefit weight for covering each requirement."},
    {"name": "budget", "domain": "scalar", "description": "Total available budget."},
    {"name": "coverage_map", "domain": "requirements -> list[items]", "description": "Mapping from a requirement to the list of items that can cover it."}
  ],
  "decision_variables": [
    {"name": "x", "domain": "items", "type": "bool", "description": "True if item is selected."},
    {"name": "y", "domain": "requirements", "type": "bool", "description": "True if requirement is covered."}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i] * y[i] for i in requirements)"
  },
  "constraints": [
    {"name": "budget_limit", "expression": "sum(cost[j] * x[j] for j in items) <= budget"},
    {"name": "coverage_activation", "domain": "requirements", "expression": "sum(x[j] for j in coverage_map[i]) >= y[i]"}
  ]
}
```

### Common Pitfalls
- Using `model.Add(sum_covering_items == y[i])`, which incorrectly forces the sum to be exactly 1 when coverage is true, potentially making the model infeasible.
- Forgetting that CP-SAT uses Boolean variables (`NewBoolVar`) rather than integer variables within `[0,1]`.
- Building large linear expressions in a loop without using Python's `sum()` efficiently, which can slow down model construction.

## Solving stage

### Strategy Overview
This stage configures the CP-SAT solver for efficient search, solves the model, and extracts the Boolean solution. It emphasizes the handling of solver parameters and the deterministic extraction of results.

### Step 1 - Configure Solver Parameters
- Create a `cp_model.CpSolver()` object.
- Set `solver.parameters.max_time_in_seconds` for runtime control.
- Set `solver.parameters.num_search_workers` for parallel search.
- Set `solver.parameters.random_seed` for reproducibility.
- For exact solutions, set `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Verify `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. Handle `cp_model.INFEASIBLE` or `cp_model.UNKNOWN` appropriately.

### Step 3 - Extract Solution Values
- Extract selected items: `[j for j in items if solver.Value(x[j]) == 1]`.
- Extract covered requirements: `[i for i in requirements if solver.Value(y[i]) == 1]`.
- Compute derived metrics (total cost, objective value) by evaluating expressions with the extracted values.

### Step 4 - Verify Solution Feasibility
- Optionally, implement a verification function that checks the budget constraint and coverage relationships directly against the original data to ensure model correctness.

### Code Usage
```python
from ortools.sat.python import cp_model

# 1. Build Model
model = cp_model.CpModel()
# Create variables x[j], y[i] as model.NewBoolVar()
# Add constraints: model.Add(sum(cost[j] * x[j]) <= budget)
# For each i: model.Add(sum(x[j] for j in coverage_map[i]) >= y[i])
# Set objective: model.Maximize(sum(weight[i] * y[i]))

# 2. Configure and Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = time_limit_seconds
solver.parameters.num_search_workers = num_workers
solver.parameters.random_seed = random_seed
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

# 3. Check Status and Extract
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected_items = [j for j in items if solver.Value(x[j]) == 1]
    covered_reqs = [i for i in requirements if solver.Value(y[i]) == 1]
    total_cost = sum(cost_data[j] for j in selected_items)
    # 4. Verify (optional)
    # ... verification logic
else:
    raise Exception(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not setting `relative_gap_limit` when an exact solution is desired, as CP-SAT may stop early with a heuristic solution.
- Misinterpreting the status `cp_model.FEASIBLE` as suboptimal; it is a valid result when a time limit is reached.
- Attempting to use `solver.Value()` on a variable before checking the solve status, which may cause errors.
