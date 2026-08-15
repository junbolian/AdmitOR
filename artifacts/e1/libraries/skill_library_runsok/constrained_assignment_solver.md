---
name: Constrained Assignment Solver
description: |
  Model and solve binary assignment problems with cardinality and pairwise exclusion constraints using either CP-SAT or MILP frameworks.
---

# Workflow 1 (CP-SAT for Logical Constraints)

## Modeling stage

### Strategy Overview
Use OR-Tools CP-SAT to model binary assignment problems with logical constraints, leveraging its native efficiency for combinatorial constraints and Boolean logic.

### Step 1 - Define Variables and Data Structures
- Create binary decision variables for each potential assignment between two sets (e.g., `x[i][j]`). Use `model.NewBoolVar()` and store them in a dictionary with tuple keys `(i, j)` for clarity.
- Structure cost data as a dictionary with the same tuple keys `(i, j)` for efficient linear objective construction.

### Step 2 - Formulate Cardinality Constraints
- For each element in the first set, add a constraint `sum(x[i][j] for j in second_set) <= 1`.
- For each element in the second set, add a constraint `sum(x[i][j] for i in first_set) <= 1`.
- Add a global constraint `sum(x[i][j] for all i, j) == K` to enforce an exact total number of assignments.

### Step 3 - Add Pairwise Exclusion Constraints
- For each pair of incompatible assignments `(i1, j1)` and `(i2, j2)`, add a linear constraint `x[i1][j1] + x[i2][j2] <= 1`.

### Step 4 - Set Linear Minimization Objective
- Formulate the objective as `model.Minimize(sum(cost[i][j] * x[i][j] for all i, j))`.

### Formulation Template
```json
{
  "sets": ["first_set", "second_set"],
  "parameters": ["cost_matrix", "total_assignments_K", "exclusion_pairs"],
  "decision_variables": ["x[i][j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "sum(x[i][j] for j) <= 1 ∀ i",
    "sum(x[i][j] for i) <= 1 ∀ j",
    "sum(x[i][j] for all i,j) == K",
    "x[i1][j1] + x[i2][j2] <= 1 ∀ (i1,j1,i2,j2) in exclusion_pairs"
  ]
}
```

### Common Pitfalls
- Forgetting to check solver status before extracting variable values, leading to runtime errors.
- Using floating-point cost coefficients without ensuring they are compatible with CP-SAT's internal arithmetic.
- Hard-coding constraint indices instead of iterating over sets, reducing reusability.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for exact solutions, handle status checks robustly, and extract assignments with verification.

### Step 1 - Configure Solver Parameters
- Instantiate `cp_model.CpSolver()`.
- Set key parameters: `max_time_in_seconds` for time limit, `num_search_workers` for parallelism, `random_seed` for reproducibility, and `relative_gap_limit = 0.0` for exact optimality.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check if the status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before proceeding. For other statuses, handle as infeasible or error.

### Step 3 - Extract and Verify Solution
- Iterate over all binary variables; if `solver.Value(x_var) == 1`, record the assignment.
- Compute the total objective value by summing the corresponding costs from the original data structure (not relying solely on `solver.ObjectiveValue()` for precision).
- Optionally, programmatically verify all cardinality and exclusion constraints are satisfied.

### Step 4 - Standardize Output
- For successful solves, print a simple `RESULT:{total_cost}` line and a human-readable assignment list.
- For failures, output a structured JSON payload with solver status and failure reason.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
x = {}
for i in first_set:
    for j in second_set:
        x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")
# Add constraints and objective as per modeling steps

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = []
    total_cost = 0.0
    for (i, j), var in x.items():
        if solver.Value(var) == 1:
            assignments.append((i, j))
            total_cost += cost_matrix[(i, j)]
    print(f"RESULT:{total_cost}")
else:
    print(f'RESULT_JSON:{{"status": {status}, "reason": "infeasible or error"}}')
```

### Common Pitfalls
- Not setting a random seed, leading to non-reproducible results across runs.
- Extracting variable values without checking solver status first, causing crashes.
- Using `solver.ObjectiveValue()` directly for cost reporting without verifying against the original cost data, which may introduce floating-point discrepancies.

# Workflow 2 (Pyomo MILP with Solver Fallback)

## Modeling stage

### Strategy Overview
Use Pyomo to build a MILP model for assignment problems, separating data from structure, and employ a solver fallback strategy for reliability across environments.

### Step 1 - Define Sets and Parameters
- Declare Pyomo `Set` objects for the two assignment dimensions (e.g., `model.sources`, `model.targets`).
- Define a `Param` for the cost matrix, initialized via a dictionary with tuple keys `(i, j)`.

### Step 2 - Create Binary Variables
- Create binary variables `model.x[i, j]` over the Cartesian product of the two sets using `pyo.Var(domain=pyo.Binary)`.

### Step 3 - Implement Hierarchical Constraints
- Add a constraint for each target: `sum(model.x[i, j] for i in sources) <= 1`.
- Add a constraint for each source: `sum(model.x[i, j] for j in targets) <= 1`.
- Add a global cardinality constraint: `sum(model.x[i, j] for all i, j) == K`.
- For each pairwise exclusion `(i1, j1, i2, j2)`, add a constraint `model.x[i1, j1] + model.x[i2, j2] <= 1`.

### Step 4 - Set Minimization Objective
- Define the objective as `pyo.Objective(expr=sum(cost[i, j] * model.x[i, j] for all i, j), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["sources", "targets"],
  "parameters": ["cost_dict", "K", "exclusion_pairs"],
  "decision_variables": ["x[i,j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j])"
  },
  "constraints": [
    "sum(x[i,j] for i in sources) <= 1 ∀ j ∈ targets",
    "sum(x[i,j] for j in targets) <= 1 ∀ i ∈ sources",
    "sum(x[i,j] for all i,j) == K",
    "x[i1,j1] + x[i2,j2] <= 1 ∀ (i1,j1,i2,j2) in exclusion_pairs"
  ]
}
```

### Common Pitfalls
- Mixing Pyomo's 1‑based and Python's 0‑based indexing in constraint rules.
- Defining parameters with incomplete data, causing initialization errors.
- Adding constraints with duplicate names, which Pyomo silently overwrites.

## Solving stage

### Strategy Overview
Solve with a primary open-source MILP solver (e.g., HiGHS), implement a fallback to a secondary solver (e.g., GLPK), and rigorously check termination conditions before solution extraction.

### Step 1 - Configure Primary Solver
- Use `SolverFactory('highs')` (or similar). Set options: `time_limit=30`, `mip_rel_gap=0.0`, `threads=4`, and `seed=42` for deterministic results.

### Step 2 - Solve with Fallback Logic
- Attempt solve with primary solver. If it fails or returns an unknown status, immediately switch to a fallback solver (e.g., `'glpk'` or `'cbc'`).
- Call `solver.solve(model, tee=False, load_solutions=False)` to prevent automatic loading.

### Step 3 - Check Status and Load Solution
- Check both `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.
- Only if both checks pass, load the solution into the model using `model.solutions.load_from(results)`.

### Step 4 - Extract and Verify Assignments
- Iterate over `model.x`; if `pyo.value(model.x[i,j]) > 0.5`, record the assignment.
- Compute total cost from the original cost dictionary for verification.
- Optionally, run a post‑solve validation function to confirm all constraints are satisfied.

### Step 5 - Standardize Output
- Print `RESULT:{objective_value}` for successful solves.
- For failures, output a JSON payload with solver status, termination condition, and error details.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=sources)
model.targets = pyo.Set(initialize=targets)
model.cost = pyo.Param(model.sources, model.targets, initialize=cost_dict)
model.x = pyo.Var(model.sources, model.targets, domain=pyo.Binary)
# Add constraints and objective as per modeling steps

# solve with status / termination checks
solver_names = ['highs', 'glpk']  # primary and fallback
solved = False
results = None

for name in solver_names:
    solver = pyo.SolverFactory(name)
    if solver.available():
        solver.options['time_limit'] = 30
        solver.options['mip_rel_gap'] = 0.0
        results = solver.solve(model, tee=False, load_solutions=False)
        if (results.solver.status == SolverStatus.ok and
            results.solver.termination_condition in (TerminationCondition.optimal,
                                                     TerminationCondition.feasible)):
            solved = True
            break

if solved:
    model.solutions.load_from(results)
    total_cost = sum(pyo.value(model.cost[i,j]) * pyo.value(model.x[i,j])
                     for i in model.sources for j in model.targets)
    print(f"RESULT:{total_cost}")
else:
    print(f'RESULT_JSON:{{"status": {results.solver.status}, "termination": {results.solver.termination_condition}}}')
```

### Common Pitfalls
- Forgetting to set `load_solutions=False`, which can cause errors when no feasible solution exists.
- Not checking both `SolverStatus.ok` and `TerminationCondition`, leading to acceptance of incomplete or invalid solutions.
- Using `.get_values()` on Pyomo variables instead of `pyo.value()` or `.value`, which may raise AttributeError.
