---
name: AssignmentWithCardinalityAndConflicts
description: |
  Model and solve bipartite assignment problems with fixed total matches, pairwise conflicts, and linear cost minimization using either CP-SAT or MILP frameworks.
---

# Workflow 1 (CP-SAT with Conditional Logic)

## Modeling stage

### Strategy Overview
This workflow uses Google's CP-SAT solver via OR-Tools, which natively handles Boolean logic and conditional constraints efficiently. It is ideal for problems where conflicts are best expressed as implications.

### Step 1 - Define Sets and Parameters
- Define the two sets to be matched, `I` and `J`, and the required number of total assignments `K`.
- Define a cost matrix `cost[i][j]` for each potential assignment.
- Define a list of conflict pairs `conflicts = [(i1, j1, i2, j2), ...]` representing "if (i1,j1) is assigned then (i2,j2) cannot be."

### Step 2 - Create Binary Assignment Variables
- Create a 2D matrix of Boolean variables `x[i][j]` using `model.NewBoolVar(f"x_{i}_{j}")`.
- Each variable indicates whether element `i` from set `I` is assigned to element `j` from set `J`.

### Step 3 - Add One-to-One Matching Constraints
- For each `i` in `I`, add constraint `sum(x[i][j] for j in J) <= 1`.
- For each `j` in `J`, add constraint `sum(x[i][j] for i in I) <= 1`.
- This enforces a bipartite matching structure.

### Step 4 - Add Fixed Cardinality Constraint
- Add a global constraint `sum(x[i][j] for i in I for j in J) == K`.
- Combined with the matching constraints, this ensures exactly `K` total assignments.

### Step 5 - Add Conditional Conflict Constraints
- For each conflict pair `(i1, j1, i2, j2)`, add `model.Add(x[i2][j2] == 0).OnlyEnforceIf(x[i1][j1])`.
- This is more direct and efficient than a big-M formulation for CP-SAT.

### Step 6 - Set Linear Minimization Objective
- Define the objective as `model.Minimize(sum(cost[i][j] * x[i][j] for i in I for j in J))`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": [
    {"name": "K", "type": "int"},
    {"name": "cost", "type": "dict", "keys": ["i", "j"]},
    {"name": "conflicts", "type": "list", "items": ["i1", "j1", "i2", "j2"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["i", "j"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I for j in J)"
  },
  "constraints": [
    "sum(x[i][j] for j in J) <= 1 for all i in I",
    "sum(x[i][j] for i in I) <= 1 for all j in J",
    "sum(x[i][j] for i in I for j in J) == K",
    "x[i2][j2] == 0 enforced if x[i1][j1] == 1 for each conflict"
  ]
}
```

### Common Pitfalls
- Forgetting to combine the `<=1` constraints with the `==K` constraint, which can lead to under-assignment.
- Using linear inequalities for conflicts (`x1 + x2 <= 1`) when conditional logic (`OnlyEnforceIf`) is more semantically clear and often more efficient for CP-SAT.
- Not using unique names for Boolean variables, which can complicate debugging.

## Solving stage

### Strategy Overview
Solve the model using the `CpSolver` with practical configurations for time limits, parallelism, and optimality. Extract and verify the solution.

### Step 1 - Configure Solver Parameters
- Instantiate `CpSolver()`.
- Set `solver.parameters.max_time_in_seconds = TIMEOUT`.
- Set `solver.parameters.num_search_workers = NUM_WORKERS` for parallelism.
- Set `solver.parameters.random_seed = SEED` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to require an optimal solution.

### Step 2 - Solve and Check Status
- Execute `status = solver.Solve(model)`.
- Check if `status` is `cp_model.OPTIMAL` (proven optimal) or `cp_model.FEASIBLE` (feasible solution found). Proceed only if status is acceptable.

### Step 3 - Extract Solution and Objective
- Retrieve the objective value via `solver.ObjectiveValue()`.
- Iterate through all `x[i][j]` variables and collect those where `solver.Value(x[i][j]) == 1` as the active assignments.

### Step 4 - Programmatic Verification
- Verify the solution satisfies all constraints: each row/column sum <=1, total assignments == K, and all conflict conditions hold.
- Recalculate the total cost from the active assignments and compare with the reported objective value.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation (follow Modeling Stage steps)
model = cp_model.CpModel()
# ... (variable creation, constraint addition, objective setting)

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = -0.0  # Negative value for exact optimality

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Objective value: {solver.ObjectiveValue()}")
    assignments = []
    for i in I:
        for j in J:
            if solver.Value(x[i][j]) == 1:
                assignments.append((i, j))
    # ... (use assignments)
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, which may discard acceptable solutions.
- Misinterpreting `relative_gap_limit`; a value of `0.0` requires optimality, which may be impossible within the time limit.
- Extracting variable values without verifying the solver status first, leading to errors.

# Workflow 2 (MILP with Linear Conflict Constraints)

## Modeling stage

### Strategy Overview
This workflow uses a standard Mixed-Integer Linear Programming (MILP) formulation, suitable for solvers like Gurobi or CBC. Conflicts are modeled as linear inequalities, making the model portable across many MILP solvers.

### Step 1 - Define Sets and Parameters
- Define the two sets to be matched, `I` and `J`, and the required number of total assignments `K`.
- Define a cost dictionary `cost[(i, j)]` for each potential assignment.
- Define a list of conflict pairs `conflicts = [(i1, j1, i2, j2), ...]`.

### Step 2 - Create Binary Assignment Variables
- Create binary decision variables `x[i,j] ∈ {0,1}` using the modeling framework's variable constructor (e.g., `pyo.Var` within `pyo.Binary` domain).

### Step 3 - Add One-to-One Matching Constraints
- For each `i` in `I`, add constraint `sum(x[i,j] for j in J) <= 1`.
- For each `j` in `J`, add constraint `sum(x[i,j] for i in I) <= 1`.

### Step 4 - Add Fixed Cardinality Constraint
- Add a global constraint `sum(x[i,j] for i in I for j in J) == K`.

### Step 5 - Add Linear Conflict Constraints
- For each conflict pair `(i1, j1, i2, j2)`, add a linear inequality `x[i1,j1] + x[i2,j2] <= 1`.
- This prevents both assignments from being selected simultaneously.

### Step 6 - Set Linear Minimization Objective
- Define the objective as `minimize sum(cost[i,j] * x[i,j] for i in I for j in J)`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": [
    {"name": "K", "type": "int"},
    {"name": "cost", "type": "dict", "keys": ["i", "j"]},
    {"name": "conflicts", "type": "list", "items": ["i1", "j1", "i2", "j2"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["i", "j"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "sum(x[i,j] for j in J) <= 1 for all i in I",
    "sum(x[i,j] for i in I) <= 1 for all j in J",
    "sum(x[i,j] for i in I for j in J) == K",
    "x[i1,j1] + x[i2,j2] <= 1 for each conflict"
  ]
}
```

### Common Pitfalls
- Using a dense cost matrix when the problem is sparse, which can cause memory issues. Prefer a dictionary.
- Adding redundant conflict constraints (e.g., both `x1 + x2 <=1` and `x2 + x1 <=1`).
- Not labeling constraints meaningfully, making debugging difficult.

## Solving stage

### Strategy Overview
Solve the MILP model using a solver like Gurobi or CBC via a modeling interface (e.g., Pyomo). Configure for optimality, extract the solution, and perform verification.

### Step 1 - Instantiate Solver and Set Parameters
- Instantiate the solver object (e.g., `SolverFactory("gurobi")`).
- Set `TimeLimit` parameter to control runtime.
- Set `MIPGap` (or equivalent) to `0.0` to require optimality.
- Set `Threads` for parallel processing and `Seed` for reproducibility if supported.

### Step 2 - Solve and Check Termination Status
- Execute the solve command (e.g., `results = solver.solve(model)`).
- Check the solver status (e.g., `SolverStatus.ok`) and termination condition (e.g., `TerminationCondition.optimal` or `TerminationCondition.feasible`).

### Step 3 - Extract Solution and Objective
- Retrieve the objective value via the model's objective attribute (e.g., `pyo.value(model.obj)`).
- Iterate through all `x[i,j]` variables and collect those where `pyo.value(var) > 0.5` as active assignments.

### Step 4 - Programmatic Verification
- Verify the solution satisfies all constraints: row/column sums, total cardinality, and conflict inequalities.
- Recalculate total cost from active assignments and parameters.

### Code Usage
```python
import pyomo.environ as pyo

# build model from formulation (follow Modeling Stage steps)
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_list)
model.J = pyo.Set(initialize=J_list)
model.x = pyo.Var(model.I, model.J, within=pyo.Binary)
# ... (constraint and objective addition)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'cbc'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
if solver.name == 'gurobi':
    solver.options['Threads'] = 8
    solver.options['Seed'] = 42

results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    print(f"Objective value: {pyo.value(model.obj)}")
    assignments = []
    for i in model.I:
        for j in model.J:
            if pyo.value(model.x[i,j]) > 0.5:
                assignments.append((i, j))
    # ... (use assignments)
else:
    print("No acceptable solution found.")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to misinterpretation of infeasible or error states.
- Extracting variable values with a strict `== 1.0` check; use `> 0.5` to account for numerical tolerances.
- Forgetting to pass the model instance when creating the solver factory, causing scope errors.
