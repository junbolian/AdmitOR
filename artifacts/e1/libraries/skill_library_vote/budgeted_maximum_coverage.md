---
name: Budgeted Maximum Coverage
description: |
  Model and solve binary optimization problems where selection decisions (with costs) must cover weighted elements under a budget, using either a CP-SAT or MILP framework.

---
# Workflow 1 (CP-SAT with Logical Encoding)

## Modeling stage

### Strategy Overview
This workflow uses OR-Tools CP-SAT, which natively handles logical constraints. It is ideal for problems where the relationship between selection and coverage is best expressed as implications (e.g., coverage requires at least one selected item). The model directly encodes these logical rules without auxiliary variables.

### Step 1 - Define Binary Variables
- Create two sets of Boolean decision variables: `x[i]` for selecting item `i` and `y[j]` for covering element `j`.
- Both variable types are binary (True/False) in CP-SAT.

### Step 2 - Map Coverage Relationships
- Define a data structure (e.g., a dictionary `coverage_sets`) that maps each element `j` to the list of items `i` that can cover it.
- This external mapping clarifies the problem structure and is used to generate constraints.

### Step 3 - Formulate Logical Coverage Constraints
- For each element `j`, enforce the implication: if `y[j]` is True, then at least one `x[i]` in `coverage_sets[j]` must be True.
- Implement this efficiently using `AddBoolOr([y[j].Not()] + covering_vars])`, where `covering_vars` is the list of `x[i]` for `i` in `coverage_sets[j]`.

### Step 4 - Add Knapsack (Budget) Constraint
- Add a linear constraint: `sum(cost[i] * x[i] for i in items) <= budget`.
- This limits the total cost of selected items.

### Step 5 - Define Weighted Objective
- Maximize the total weighted coverage: `maximize sum(weight[j] * y[j] for j in elements)`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "elements"
  ],
  "parameters": [
    "cost[items]",
    "weight[elements]",
    "budget",
    "coverage_sets[elements] -> list of items"
  ],
  "decision_variables": [
    "x[items] ∈ {0,1}",
    "y[elements] ∈ {0,1}"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[j] * y[j] for j in elements)"
  },
  "constraints": [
    "y[j] <= sum(x[i] for i in coverage_sets[j]) for each j in elements",
    "sum(cost[i] * x[i] for i in items) <= budget"
  ]
}
```

### Common Pitfalls
- Creating unnecessary auxiliary variables for the coverage implication, which CP-SAT can handle directly.
- Using `AddImplication` in a loop for each covering item, which is less efficient than a single `AddBoolOr`.
- Forgetting to map `coverage_sets` correctly, leading to incorrect or missing constraints.

## Solving stage

### Strategy Overview
Solving involves configuring the CP-SAT solver for binary optimization with logical and linear constraints. Focus on setting appropriate limits for runtime and optimality, and implementing robust checks on the solver result.

### Step 1 - Configure Solver Parameters
- Set `max_time_in_seconds` to control runtime.
- Set `num_search_workers` for parallel search (e.g., to the number of CPU cores).
- Set `random_seed` for reproducibility.
- Set `relative_gap_limit = 0.0` to search for proven optimal solutions when required.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the result status: `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`. Handle each case appropriately (e.g., `FEASIBLE` may indicate a time limit).

### Step 3 - Extract and Validate Solution
- Extract selected items where `solver.Value(x[i]) == 1`.
- Extract covered elements where `solver.Value(y[j]) == 1`.
- Manually verify that the solution satisfies the budget constraint and coverage implications to catch modeling errors.

### Step 4 - Report Comprehensive Results
- Output the objective value, selected items, covered elements, total cost, and solver status.
- Format key results with a prefix (e.g., `RESULT:`) for potential automated parsing.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in items}
y = {j: model.NewBoolVar(f"y_{j}") for j in elements}

# Coverage constraints
for j in elements:
    covering_vars = [x[i] for i in coverage_sets[j]]
    model.AddBoolOr([y[j].Not()] + covering_vars)

# Budget constraint
model.Add(sum(cost[i] * x[i] for i in items) <= budget)

# Objective
model.Maximize(sum(weight[j] * y[j] for j in elements))

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

# Check status and extract
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    obj_val = solver.ObjectiveValue()
    selected = [i for i in items if solver.Value(x[i]) == 1]
    covered = [j for j in elements if solver.Value(y[j]) == 1]
    total_cost = sum(cost[i] for i in selected)
    # Verification and reporting
    print(f"RESULT: {obj_val}")
else:
    print("No solution found.")
```

### Common Pitfalls
- Interpreting `FEASIBLE` as `OPTIMAL` without checking the status difference.
- Not setting a time limit, leading to potentially long runs on large instances.
- Extracting variable values without checking the solver status first, which may cause errors.

# Workflow 2 (MILP with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to formulate the problem as a Mixed-Integer Linear Program (MILP), suitable for solvers like HiGHS or CBC. It models coverage constraints as linear inequalities, making it a natural fit for traditional MILP solvers and those familiar with algebraic modeling.

### Step 1 - Define Binary Variables
- Create two Pyomo `Var` objects with `domain=pyo.Binary`: `build[i]` for item selection and `cover[j]` for element coverage.

### Step 2 - Structure Coverage Data
- Store coverage relationships in a Python dictionary `coverage_map[j] = list of i`.
- This structure is used in constraint rules and avoids iteration issues with Pyomo parameter objects.

### Step 3 - Formulate Linear Coverage Constraints
- For each element `j`, enforce `cover[j] <= sum(build[i] for i in coverage_map[j])`.
- This linear inequality correctly models the logical requirement: coverage is only possible if at least one covering item is selected.

### Step 4 - Add Linear Knapsack Constraint
- Add constraint: `sum(cost[i] * build[i] for i in items) <= budget`.

### Step 5 - Define Weighted Sum Objective
- Maximize `sum(weight[j] * cover[j] for j in elements)`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "elements"
  ],
  "parameters": [
    "cost[items]",
    "weight[elements]",
    "budget",
    "coverage_map[elements] -> list of items"
  ],
  "decision_variables": [
    "build[items] ∈ {0,1}",
    "cover[elements] ∈ {0,1}"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[j] * cover[j] for j in elements)"
  },
  "constraints": [
    "cover[j] <= sum(build[i] for i in coverage_map[j]) for each j in elements",
    "sum(cost[i] * build[i] for i in items) <= budget"
  ]
}
```

### Common Pitfalls
- Embedding coverage mappings within Pyomo `Param` objects, which can complicate iteration in constraint rules.
- Using `==` instead of `<=` in coverage constraints, which would incorrectly force coverage if a covering item is selected.
- Not separating selection and coverage variables, which obscures the problem logic.

## Solving stage

### Strategy Overview
Solving involves selecting an appropriate MILP solver (e.g., HiGHS, CBC), configuring it for binary optimization, and rigorously checking both solver status and termination condition before extracting results.

### Step 1 - Select and Configure Solver
- Instantiate the solver via `SolverFactory("solver_name")` (e.g., `"highs"` or `"cbc"`).
- Set key parameters: `time_limit` for runtime, `mip_rel_gap=0.0` for exact solutions (or a small tolerance), and `threads` for parallel processing.

### Step 2 - Solve and Check Termination
- Call `solver.solve(model, tee=False)`.
- Check both `results.solver.status` (should be `SolverStatus.ok`) and `results.solver.termination_condition` (acceptable values are `TerminationCondition.optimal` or `TerminationCondition.feasible`).

### Step 3 - Extract and Validate Solution
- Extract selected items where `pyo.value(build[i]) > 0.5` (using a threshold to account for numerical tolerances).
- Extract covered elements where `pyo.value(cover[j]) > 0.5`.
- Compute the total cost of selected items and verify it does not exceed the budget.

### Step 4 - Report Standardized Output
- Print the objective value with a consistent prefix (e.g., `RESULT:`).
- Include details like selected items, covered elements, total cost, and solver termination condition for debugging.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model
model = pyo.ConcreteModel()
model.build = pyo.Var(items, domain=pyo.Binary)
model.cover = pyo.Var(elements, domain=pyo.Binary)

# Objective
model.obj = pyo.Objective(
    expr=sum(weight[j] * model.cover[j] for j in elements),
    sense=pyo.maximize
)

# Budget constraint
model.budget_con = pyo.Constraint(
    expr=sum(cost[i] * model.build[i] for i in items) <= budget
)

# Coverage constraints
def coverage_rule(m, j):
    return m.cover[j] <= sum(m.build[i] for i in coverage_map[j])
model.coverage_con = pyo.Constraint(elements, rule=coverage_rule)

# Solve
solver = pyo.SolverFactory("highs")  # or "cbc"
solver.options["time_limit"] = 30.0
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

# Check and extract
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = float(pyo.value(model.obj))
    selected = [i for i in items if pyo.value(model.build[i]) > 0.5]
    covered = [j for j in elements if pyo.value(model.cover[j]) > 0.5]
    total_cost = sum(cost[i] for i in selected)
    print(f"RESULT: {obj_val}")
else:
    print(f"Solver failed: Status={status}, Termination={term}")
```

### Common Pitfalls
- Setting `mip_rel_gap = -1.0` (solver default) instead of `0.0` when an exact optimum is needed.
- Checking only the solver status (`ok`) without verifying the termination condition, potentially accepting `infeasible` or `unbounded` results.
- Extracting variable values using exact equality (`== 1`) instead of a tolerance (`> 0.5`), which may fail due to floating-point rounding.
