---
name: Budgeted Maximum Coverage
description: |
  Model and solve binary selection problems with weighted coverage objectives under budget constraints using two complementary solver backends.

---

# Workflow 1 (Pyomo-based MILP)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract modeling language. It defines separate binary variables for selection and coverage, links them via implication constraints, and maximizes a weighted sum of coverage indicators subject to a linear budget constraint.

### Step 1 - Define Sets and Parameters
- Define a set `I` for coverage targets (e.g., areas, customers) and a set `J` for selectable items (e.g., facilities, towers).
- Define parameters: `weight[i]` for target benefit, `cost[j]` for item cost, `budget` for total resource limit, and a mapping `coverage[i]` listing items `j` that cover target `i`.

### Step 2 - Create Decision Variables
- Create binary selection variables `x[j] ∈ {0,1}` for each item `j ∈ J`.
- Create binary coverage indicator variables `y[i] ∈ {0,1}` for each target `i ∈ I`.

### Step 3 - Formulate Objective and Constraints
- **Objective**: Maximize total weighted coverage: `max Σ weight[i] * y[i]`.
- **Budget Constraint**: Enforce total cost limit: `Σ cost[j] * x[j] ≤ budget`.
- **Coverage Activation**: For each target `i`, enforce `y[i] ≤ Σ_{j ∈ coverage[i]} x[j]`. This ensures coverage is only counted if at least one covering item is selected.

### Formulation Template
```json
{
  "sets": [
    "I: set of coverage targets",
    "J: set of selectable items"
  ],
  "parameters": [
    "weight[i ∈ I]: benefit of covering target i",
    "cost[j ∈ J]: cost of selecting item j",
    "budget: total available budget",
    "coverage[i ∈ I]: list of items j that cover target i"
  ],
  "decision_variables": [
    "x[j ∈ J] ∈ {0,1}: 1 if item j is selected",
    "y[i ∈ I] ∈ {0,1}: 1 if target i is covered"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i] * y[i] for i in I)"
  },
  "constraints": [
    "budget_limit: sum(cost[j] * x[j] for j in J) <= budget",
    "coverage_activation[i ∈ I]: y[i] <= sum(x[j] for j in coverage[i])"
  ]
}
```

### Common Pitfalls
- Forgetting to define the `coverage` mapping as a sparse data structure, leading to memory inefficiency for large problems.
- Using equality (`y[i] == sum(...)`) instead of inequality (`y[i] <= sum(...)`), which incorrectly forces coverage when an item is selected.
- Not verifying that all `coverage[i]` lists are non-empty; empty lists make the constraint `y[i] <= 0`, forcing `y[i] = 0`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver backend (e.g., HiGHS, Gurobi, CBC). Configure solver options for performance and reproducibility, check termination status, and extract solution values with proper handling of binary variable thresholds.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object via `SolverFactory("<solver_name>")`.
- Set key options: `time_limit` (e.g., 30 seconds), `mip_rel_gap` (e.g., 0.0 for optimality), `threads` (e.g., 4 for parallelism), and `seed` (e.g., 42 for reproducibility).

### Step 2 - Solve and Check Status
- Call `solver.solve(model, tee=False)` to execute the optimization.
- Check that `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is either `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract and Validate Solution
- Extract selected items: `[j for j in model.J if pyo.value(model.x[j]) > 0.5]`.
- Extract covered targets: `[i for i in model.I if pyo.value(model.y[i]) > 0.5]`.
- Compute total cost and verify it does not exceed the budget.
- Validate coverage: for each covered target, ensure at least one selected item is in its coverage set.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=target_indices)
model.J = pyo.Set(initialize=item_indices)

model.x = pyo.Var(model.J, domain=pyo.Binary)
model.y = pyo.Var(model.I, domain=pyo.Binary)

model.obj = pyo.Objective(expr=sum(weight[i] * model.y[i] for i in model.I), sense=pyo.maximize)
model.budget_con = pyo.Constraint(expr=sum(cost[j] * model.x[j] for j in model.J) <= budget)

def coverage_rule(m, i):
    return m.y[i] <= sum(m.x[j] for j in coverage[i])
model.coverage_con = pyo.Constraint(model.I, rule=coverage_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
    selected_items = [j for j in model.J if pyo.value(model.x[j]) > 0.5]
    covered_targets = [i for i in model.I if pyo.value(model.y[i]) > 0.5]
    total_cost = sum(cost[j] for j in selected_items)
    # ... output results
else:
    # Handle infeasible or error status
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to extraction errors from incomplete solves.
- Using exact equality (`== 1.0`) to test binary variable values, which can fail due to floating-point precision; use a threshold (`> 0.5`).
- Omitting the validation step, which can miss modeling errors or solver inaccuracies.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
This workflow models the problem using Google OR-Tools' CP-SAT solver, a constraint programming solver for linear integer problems. It uses the `cp_model.CpModel()` API to create Boolean selection and coverage variables, linear inequality constraints, and a linear maximization objective.

### Step 1 - Initialize Model and Data Structures
- Create a `CpModel` instance.
- Store input data (weights, costs, budget, coverage mapping) in efficient Python structures (lists, dictionaries).

### Step 2 - Create Boolean Variables
- Create Boolean selection variables `x[j] = model.NewBoolVar("x_j")` for each item `j`.
- Create Boolean coverage indicator variables `y[i] = model.NewBoolVar("y_i")` for each target `i`.

### Step 3 - Add Linear Constraints
- **Budget Constraint**: Add `sum(cost[j] * x[j] for j in J) <= budget` using `model.AddLinearConstraint`.
- **Coverage Activation**: For each target `i`, add `y[i] <= sum(x[j] for j in coverage[i])` by constructing a linear sum of Boolean variables.

### Step 4 - Define Maximization Objective
- Set the objective to maximize `sum(weight[i] * y[i] for i in I)` using `model.Maximize`.

### Formulation Template
```json
{
  "sets": [
    "I: list of coverage target indices",
    "J: list of selectable item indices"
  ],
  "parameters": [
    "weight[i]: integer or float benefit of covering target i",
    "cost[j]: integer or float cost of selecting item j",
    "budget: integer or float total budget",
    "coverage[i]: list of item indices j that cover target i"
  ],
  "decision_variables": [
    "x[j]: Boolean variable (True if item j selected)",
    "y[i]: Boolean variable (True if target i covered)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i] * y[i] for i in I)"
  },
  "constraints": [
    "budget_limit: sum(cost[j] * x[j] for j in J) <= budget",
    "coverage_activation[i]: y[i] <= sum(x[j] for j in coverage[i])"
  ]
}
```

### Common Pitfalls
- Using non-integer coefficients with CP-SAT, which requires scaling or conversion; CP-SAT works best with integer data.
- Forgetting that `model.Add(sum(vars) >= 1)` creates a linear constraint, not a logical OR; for Boolean variables, this is correct but the distinction matters for more complex logic.
- Not leveraging CP-SAT's ability to handle large numbers of Boolean variables efficiently compared to traditional MILP solvers.

## Solving stage

### Strategy Overview
Solve the CP-SAT model using the `CpSolver()` class. Configure solver parameters for parallel search and time limits, check the solution status, and extract variable values using the solver's `Value()` method.

### Step 1 - Configure Solver Parameters
- Instantiate `CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds` (e.g., 30), `solver.parameters.num_search_workers` (e.g., 8), `solver.parameters.random_seed` (e.g., 42), and `solver.parameters.relative_gap_limit` (e.g., 0.0).

### Step 2 - Solve and Interpret Status
- Call `status = solver.Solve(model)`.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. Handle `INFEASIBLE` or `UNKNOWN` statuses appropriately.

### Step 3 - Extract Solution and Verify
- Extract selected items: `[j for j in J if solver.Value(x[j]) == 1]`.
- Extract covered targets: `[i for i in I if solver.Value(y[i]) == 1]`.
- Compute total cost and verify budget compliance.
- Validate that each covered target has at least one selected item in its coverage set.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()

# Create Boolean variables
x = [model.NewBoolVar(f"x_{j}") for j in range(num_items)]
y = [model.NewBoolVar(f"y_{i}") for i in range(num_targets)]

# Budget constraint
model.Add(sum(cost[j] * x[j] for j in range(num_items)) <= budget)

# Coverage activation constraints
for i in range(num_targets):
    model.Add(y[i] <= sum(x[j] for j in coverage[i]))

# Objective
model.Maximize(sum(weight[i] * y[i] for i in range(num_targets)))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected_items = [j for j in range(num_items) if solver.Value(x[j]) == 1]
    covered_targets = [i for i in range(num_targets) if solver.Value(y[i]) == 1]
    total_cost = sum(cost[j] for j in selected_items)
    # ... output results
else:
    # Handle infeasible or unknown status
    print(f"Solver status: {status}")
```

### Common Pitfalls
- Not setting `num_search_workers` for parallel execution, missing performance gains on multi-core machines.
- Misinterpreting `FEASIBLE` as suboptimal; CP-SAT may return a feasible solution when time limit is reached, which is acceptable but not proven optimal.
- Using `solver.Value()` on variables before checking the solve status, which can raise errors.
