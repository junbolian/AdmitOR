---
name: BinaryAssignmentMaximization
description: |
  Model and solve one-to-one assignment problems with compatibility constraints to maximize total assignments, using binary decision variables and solver-aware implementations.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the assignment problem as a Constraint Programming (CP) model using OR-Tools' CP-SAT solver, which is efficient for pure binary integer problems. The model uses Boolean variables, linear constraints for capacity and compatibility, and a linear objective.

### Step 1 - Define Sets and Parameters
- Define the two sets of entities to be matched (e.g., `set_A`, `set_B`).
- Create a binary compatibility matrix `compatible[i][j]` (1 if assignment is allowed, 0 otherwise).

### Step 2 - Create Binary Decision Variables
- For each pair `(i, j)` where `i` in `set_A` and `j` in `set_B`, create a Boolean variable `assign[i][j]` using `model.NewBoolVar()`.
- Use descriptive naming (e.g., `assign_i_j`) for debugging.

### Step 3 - Add Capacity Constraints
- For each element `i` in `set_A`, add constraint: `sum(assign[i][j] for j in set_B) <= 1`.
- For each element `j` in `set_B`, add constraint: `sum(assign[i][j] for i in set_A) <= 1`.

### Step 4 - Enforce Compatibility
- For all pairs `(i, j)`, add linear inequality: `assign[i][j] <= compatible[i][j]`. This ensures assignments only occur where compatible.

### Step 5 - Set Objective
- Define the objective to maximize the total number of assignments: `model.Maximize(sum(assign[i][j] for i in set_A for j in set_B))`.

### Formulation Template
```json
{
  "sets": ["set_A", "set_B"],
  "parameters": [
    {
      "name": "compatible",
      "type": "binary_matrix",
      "dimensions": ["set_A", "set_B"],
      "description": "1 if assignment i->j is allowed, 0 otherwise."
    }
  ],
  "decision_variables": [
    {
      "name": "assign",
      "type": "binary",
      "dimensions": ["set_A", "set_B"],
      "description": "1 if element i from set_A is assigned to element j from set_B."
    }
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(assign[i][j] for i in set_A for j in set_B)"
  },
  "constraints": [
    "sum(assign[i][j] for j in set_B) <= 1, for all i in set_A",
    "sum(assign[i][j] for i in set_A) <= 1, for all j in set_B",
    "assign[i][j] <= compatible[i][j], for all i in set_A, j in set_B"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce the one-to-one capacity constraints for both sets.
- Using a dense compatibility matrix for sparse problems, which creates unnecessary variables and constraints.
- Not verifying that the compatibility matrix is binary, leading to incorrect constraint enforcement.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with practical configuration for time limits, parallelism, and reproducibility. Extract and verify the solution, handling both optimal and feasible outcomes.

### Step 1 - Configure Solver
- Instantiate `CpSolver()`.
- Set `solver.parameters.max_time_in_seconds` for a runtime limit.
- Enable parallelism with `solver.parameters.num_search_workers`.
- Set `solver.parameters.random_seed` for reproducibility.
- Optionally set `solver.parameters.relative_gap_limit = 0.0` for exact solutions.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. If not, proceed to failure handling.

### Step 3 - Extract Solution
- If status is acceptable, iterate over all `assign[i][j]` variables.
- Collect pairs where `solver.Value(assign[i][j]) == 1`.
- Compute the objective value as the count of these assignments (or use `solver.ObjectiveValue()`).

### Step 4 - Verify and Output
- Perform a sanity check: verify collected assignments respect capacity and compatibility constraints.
- Format results into a structured output (e.g., JSON) containing status, objective value, and list of assignments.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build model as per Modeling stage steps)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Apply configuration
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = []
    for i in set_A:
        for j in set_B:
            if solver.Value(assign[i][j]) == 1:
                assignments.append((i, j))
    objective_value = len(assignments)  # or solver.ObjectiveValue()
    result = {
        "status": "SUCCESS",
        "objective": objective_value,
        "assignments": assignments
    }
else:
    result = {
        "status": "FAILURE",
        "reason": f"Solver status: {status}",
        "assignments": []
    }
# Output result (e.g., print as JSON)
```

### Common Pitfalls
- Not handling the `FEASIBLE` status, which may provide a valid but non-optimal solution.
- Assuming `solver.ObjectiveValue()` is always available; for `FEASIBLE` status, it may be undefined.
- Omitting verification, which can miss constraint violations due to solver tolerances or extraction errors.

# Workflow 2 (MIP with Pyomo and HiGHS)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Programming (MIP) model using Pyomo's abstract or concrete modeling. This approach is portable across solvers and integrates well with algebraic modeling systems.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `set_A` and `set_B`.
- Define a `Param` for `compatible` indexed over both sets, initialized with binary values.

### Step 2 - Declare Binary Variables
- Create a `Var` indexed over `set_A x set_B`, domain=`Binary`, named `assign`.

### Step 3 - Build Capacity Constraints
- For each `i` in `set_A`, add constraint: `sum(assign[i, j] for j in set_B) <= 1`.
- For each `j` in `set_B`, add constraint: `sum(assign[i, j] for i in set_A) <= 1`.

### Step 4 - Add Compatibility Constraints
- For each `(i, j)`, add constraint: `assign[i, j] <= compatible[i, j]`.

### Step 5 - Define Objective
- Create an objective expression: `sum(assign[i, j] for i in set_A for j in set_B)`.
- Set model objective to maximize this expression.

### Formulation Template
```json
{
  "sets": ["set_A", "set_B"],
  "parameters": [
    {
      "name": "compatible",
      "type": "Param",
      "index_domain": ["set_A", "set_B"],
      "description": "Binary parameter indicating allowed assignments."
    }
  ],
  "decision_variables": [
    {
      "name": "assign",
      "type": "Var",
      "domain": "Binary",
      "index_domain": ["set_A", "set_B"]
    }
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(assign[i, j] for i in set_A, j in set_B)"
  },
  "constraints": [
    "sum(assign[i, j] for j in set_B) <= 1, forall i in set_A",
    "sum(assign[i, j] for i in set_A) <= 1, forall j in set_B",
    "assign[i, j] <= compatible[i, j], forall i in set_A, j in set_B"
  ]
}
```

### Common Pitfalls
- Using 1-based indexing when the solver expects 0-based, causing index errors.
- Not initializing the `compatible` parameter for all index pairs, leading to missing data errors.
- Creating the model concretely with large sets can be memory-intensive; consider sparse initialization.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via the `SolverFactory`, with robust error handling for solver status and termination conditions. Provide fallback to alternative solvers if needed.

### Step 1 - Instantiate Solver
- Create solver object: `solver = SolverFactory('highs')`.
- Set solver options if needed (e.g., `solver.options['time_limit'] = 30`).

### Step 2 - Solve with Careful Status Handling
- Call `results = solver.solve(model, tee=False, load_solutions=False)`.
- Inspect `results.solver.status` and `results.solver.termination_condition`.

### Step 3 - Load and Extract Solution
- If status is `ok` and termination is `optimal` or `feasible`, load the solution: `model.solutions.load_from(results)`.
- Iterate over `assign` variable indices, check `value(assign[i, j]) > 0.5` to collect assignments.
- Compute objective as the count of assignments or from `model.obj()`.

### Step 4 - Implement Fallback and Output
- If primary solver fails, attempt fallback (e.g., `SolverFactory('glpk')`).
- Output structured results including solver status, objective, and assignments.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.set_A = pyo.Set(initialize=set_A_indices)
model.set_B = pyo.Set(initialize=set_B_indices)
model.compatible = pyo.Param(model.set_A, model.set_B, initialize=compatible_data)
model.assign = pyo.Var(model.set_A, model.set_B, domain=pyo.Binary)
# ... (add constraints and objective as per Modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
# Set options
solver.options['time_limit'] = 30

results = solver.solve(model, tee=False, load_solutions=False)
status = results.solver.status
term = results.solver.termination_condition

if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    model.solutions.load_from(results)
    assignments = []
    for i in model.set_A:
        for j in model.set_B:
            if pyo.value(model.assign[i, j]) > 0.5:
                assignments.append((i, j))
    objective_value = len(assignments)
    result = {
        "status": "SUCCESS",
        "solver_termination": str(term),
        "objective": objective_value,
        "assignments": assignments
    }
else:
    # Optional fallback to another solver
    result = {
        "status": "FAILURE",
        "solver_status": str(status),
        "termination": str(term),
        "assignments": []
    }
# Output result
```

### Common Pitfalls
- Forgetting `load_solutions=False` and then trying to access variable values before loading.
- Misinterpreting `SolverStatus.ok` (only indicates solver ran, not solution quality).
- Not accounting for solver-specific option syntax when switching between solvers (e.g., HiGHS vs GLPK).
