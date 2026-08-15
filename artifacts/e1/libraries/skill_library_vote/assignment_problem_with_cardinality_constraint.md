---
name: Assignment Problem with Cardinality Constraint
description: |
  Model and solve bipartite assignment problems with exact total assignments using binary decision variables and cost minimization.
---

# Workflow 1 (CP-SAT for Exact Matching)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, designed for discrete optimization with logical constraints. It is well-suited for assignment problems requiring exact cardinality and binary variables, offering fast search and built-in parallelization.

### Step 1 - Define Sets and Parameters
- Define two finite sets, `I` and `J`, representing the items to be matched (e.g., tasks and workers).
- Define a cost matrix `c[i][j]` as a 2D list or dictionary, where `i` in `I` and `j` in `J`.

### Step 2 - Create Binary Assignment Variables
- For each `(i, j)` pair, create a binary decision variable `x[i, j]` using `model.NewBoolVar()`.
- Store variables in a dictionary keyed by tuple `(i, j)` for easy reference.

### Step 3 - Add One-to-One Matching Constraints
- For each `i` in `I`, add a constraint: `sum(x[i, j] for j in J) <= 1`.
- For each `j` in `J`, add a constraint: `sum(x[i, j] for i in I) <= 1`.

### Step 4 - Add Exact Total Assignments Constraint
- Add a global constraint: `sum(x[i, j] for i in I for j in J) == K`, where `K` is the required number of total assignments.

### Step 5 - Formulate Linear Objective
- Define the objective to minimize: `sum(c[i][j] * x[i, j] for i in I for j in J)`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": ["c[i][j] (cost matrix)", "K (exact total assignments)"],
  "decision_variables": ["x[i,j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(c[i][j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "sum(x[i,j] for j in J) <= 1 for each i in I",
    "sum(x[i,j] for i in I) <= 1 for each j in J",
    "sum(x[i,j] for i in I for j in J) == K"
  ]
}
```

### Common Pitfalls
- Forgetting to ensure `K` does not exceed `min(|I|, |J|)` given the one-to-one constraints, which can cause infeasibility.
- Using incorrect indices when populating the cost matrix, leading to mismatched variable dimensions.
- Not storing variable references, making constraint and solution extraction difficult.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver with time limits and parallel search. Extract and verify the solution, handling both optimal and feasible statuses.

### Step 1 - Configure Solver Parameters
- Instantiate `CpSolver()`.
- Set `solver.parameters.max_time_in_seconds` for runtime control.
- Set `solver.parameters.num_search_workers` for parallel search.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` for exact optimization.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if `status in (cp_model.OPTIMAL, cp_model.FEASIBLE)`.

### Step 3 - Extract and Validate Solution
- If feasible/optimal, retrieve objective value via `solver.ObjectiveValue()`.
- Iterate over all `(i, j)` pairs, check `if solver.Value(x[i, j]) == 1`, and collect assignments as tuples `(i, j, c[i][j])`.
- Manually verify the solution satisfies all constraints (cardinality, exact total `K`) and that the sum of collected costs matches the reported objective.

### Step 4 - Handle Failure Cases
- If status is not feasible or optimal, output a structured error message (e.g., JSON) indicating infeasibility or other solver status.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build model as per Modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters as per Step 1
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    objective_value = solver.ObjectiveValue()
    assignments = []
    for i in I:
        for j in J:
            if solver.Value(x[i, j]) == 1:
                assignments.append((i, j, c[i][j]))
    # Validate (optional but recommended)
    # ...
else:
    # Handle failure
    print({"status": "FAILED", "solver_status": status})
```

### Common Pitfalls
- Not setting `relative_gap_limit = 0.0`, causing the solver to stop early with a suboptimal solution.
- Assuming `FEASIBLE` status implies optimality; always check for `OPTIMAL` if an exact optimum is required.
- Omitting solution validation, which can miss modeling errors.

# Workflow 2 (MILP Solver with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model formulation and a MILP solver (e.g., HiGHS, CBC) via SolverFactory. It is suitable for users familiar with algebraic modeling languages and for integration into larger Pyomo-based optimization pipelines.

### Step 1 - Define Abstract Sets and Parameters
- Define Pyomo `Set` objects for `model.I` and `model.J`.
- Define a `Param` `model.c` indexed by `(i, j)` to store the cost matrix, initialized via a dictionary.

### Step 2 - Declare Binary Variables
- Declare a `Var` `model.x` indexed by `model.I * model.J` within `model.Binary`.

### Step 3 - Formulate Objective Function
- Define `model.obj = Objective(expr=sum(model.c[i,j] * model.x[i,j] for i in model.I for j in model.J), sense=minimize)`.

### Step 4 - Add Assignment Constraints
- Add constraints for each `i` in `model.I`: `sum(model.x[i,j] for j in model.J) <= 1`.
- Add constraints for each `j` in `model.J`: `sum(model.x[i,j] for i in model.I) <= 1`.

### Step 5 - Add Global Cardinality Constraint
- Add a constraint: `sum(model.x[i,j] for i in model.I for j in model.J) == K`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": ["c[i,j] (cost)", "K (exact total assignments)"],
  "decision_variables": ["x[i,j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(c[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "sum(x[i,j] for j in J) <= 1 ∀i ∈ I",
    "sum(x[i,j] for i in I) <= 1 ∀j ∈ J",
    "sum(x[i,j] for i in I for j in J) == K"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters or variables, leading to `KeyError` during model construction.
- Forgetting to deactivate the solver's built-in presolve or cut generation, which can sometimes interfere with exact cardinality constraints.
- Not verifying that `K` is an integer parameter within the model.

## Solving stage

### Strategy Overview
Instantiate a MILP solver via Pyomo's SolverFactory, configure it for exact solving, and handle termination conditions robustly. Extract solution values using Pyomo's value functions.

### Step 1 - Select and Configure Solver
- Use `SolverFactory('highs')` (or `'cbc'`, `'scip'`).
- Set options: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0`, `solver.options['threads'] = 4`.

### Step 2 - Solve with Exception Handling
- Wrap the solve call in a try-except block to catch exceptions like `ApplicationError` or `ValueError`.
- Call `results = solver.solve(model, tee=False)`.

### Step 3 - Check Solver Status and Termination
- Check `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 4 - Extract Solution and Verify
- Retrieve objective value via `float(pyo.value(model.obj))`.
- Iterate over `model.x`, check `if pyo.value(model.x[i, j]) > 0.5`, and collect assignments `(i, j, pyo.value(model.c[i,j]))`.
- Perform a quick sanity check: count assignments and verify they equal `K` and satisfy row/column limits.

### Step 5 - Diagnose Infeasibility
- If infeasible, implement a brute-force feasibility check (e.g., using `itertools.combinations`) on the input data to rule out data errors.
- Review constraint logic and parameter signs.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_list)
model.J = pyo.Set(initialize=J_list)
model.c = pyo.Param(model.I, model.J, initialize=cost_dict)
model.x = pyo.Var(model.I, model.J, within=pyo.Binary)
# ... (add objective and constraints as per Modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
try:
    results = solver.solve(model, tee=False)
except Exception as e:
    print({"status": "SOLVER_ERROR", "exception": str(e)})
    results = None

if results and results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
        obj_val = float(pyo.value(model.obj))
        assignments = []
        for i in model.I:
            for j in model.J:
                if pyo.value(model.x[i, j]) > 0.5:
                    assignments.append((i, j, pyo.value(model.c[i, j])))
        # Validation...
    else:
        print({"status": "INFEASIBLE_OR_LIMIT", "termination": str(results.solver.termination_condition)})
else:
    print({"status": "SOLVER_FAILED"})
```

### Common Pitfalls
- Not setting `mip_rel_gap=0.0`, leading to early termination with a gap.
- Confusing `solver.status` with `termination_condition`; both must be checked.
- Using `pyo.value()` on variables/parameters without ensuring the model instance contains the solution.
