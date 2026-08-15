---
name: BinaryAssignmentWithExclusions
description: |
  Model and solve binary assignment problems with cardinality and pairwise exclusion constraints to minimize total cost using MILP or CP-SAT solvers.

---
# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, designed for discrete optimization with logical constraints. It excels at encoding conditional implications and pairwise exclusions directly without big-M formulations, leveraging the `OnlyEnforceIf` method for complex logic.

### Step 1 - Define Binary Assignment Variables
- Create a 2D matrix of binary decision variables `x[i][j]` using `model.NewBoolVar(f"x_{i}_{j}")` to represent assignment between elements of two sets `I` and `J`.
- Store variables in a list-of-lists or dictionary for easy access during constraint and objective building.

### Step 2 - Enforce Cardinality Constraints
- Add constraints `sum(x[i][j] for i in I) <= 1` for each `j` in `J` and `sum(x[i][j] for j in J) <= 1` for each `i` in `I` to ensure at-most-one assignment per element.
- Optionally, add a global cardinality constraint `sum(x[i][j] for i in I, j in J) == K` to fix the exact number of total assignments if required.

### Step 3 - Implement Pairwise Exclusions
- For each incompatible pair `(i1, j1)` and `(i2, j2)`, add a linear constraint `x[i1][j1] + x[i2][j2] <= 1` to prevent both assignments.
- For conditional exclusions (if assignment A then not assignment B), use `model.Add(x[i2][j2] == 0).OnlyEnforceIf(x[i1][j1])` for a more efficient logical encoding.

### Step 4 - Set Linear Objective
- Define the objective to minimize total cost: `model.Minimize(sum(cost[i][j] * x[i][j] for i in I, j in J))`. CP-SAT supports real-valued coefficients directly.

### Formulation Template
```json
{
  "sets": ["I", "J", "incompatible_pairs"],
  "parameters": ["cost[I][J] (float)", "K (int, optional)"],
  "decision_variables": ["x[I][J] (binary)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i][j] for i in I) <= 1 for each j in J",
    "sum(x[i][j] for j in J) <= 1 for each i in I",
    "sum(x[i][j] for i in I, j in J) == K (if required)",
    "x[i1][j1] + x[i2][j2] <= 1 for each (i1,j1,i2,j2) in incompatible_pairs"
  ]
}
```

### Common Pitfalls
- Forgetting to index variables consistently, leading to `KeyError` or incorrect constraints.
- Using `OnlyEnforceIf` on non-binary expressions; the condition must be a Boolean variable.
- Not handling floating-point cost coefficients carefully; CP-SAT accepts them, but extreme values can cause numerical issues.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for a balance of speed and optimality, extract solutions with robust status checks, and output structured results for validation and integration.

### Step 1 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds = <timeout>` for runtime control.
- Enable parallel search with `solver.parameters.num_search_workers = <num_cores>`.
- Set `solver.parameters.random_seed = <seed>` for reproducibility.
- For exact optimization, set `solver.parameters.relative_gap_limit = -1.0`.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)` and capture the result status.
- Check if `status in (cp_model.OPTIMAL, cp_model.FEASIBLE)` to proceed with solution extraction. Handle `cp_model.INFEASIBLE` or `cp_model.UNKNOWN` appropriately.

### Step 3 - Extract and Validate Solution
- Iterate over all variables `x[i][j]` and collect assignments where `solver.Value(x[i][j]) == 1`.
- Compute the objective value via `solver.ObjectiveValue()`.
- Optionally, validate that the extracted assignments satisfy all cardinality and exclusion constraints programmatically.

### Step 4 - Output Structured Results
- Print or return a JSON payload containing solver status, objective value, and list of assignments for easy parsing by downstream systems.

### Code Usage
```python
import json
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... define variables, constraints, objective as per modeling stage

# Solve with status / termination checks
solver = cp_model.CpSolver()
# Apply configuration from Step 1
status = solver.Solve(model)

# Extract results
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = []
    for i in I:
        for j in J:
            if solver.Value(x[i][j]) == 1:
                assignments.append((i, j))
    result_payload = {
        "status": str(status),
        "objective_value": solver.ObjectiveValue(),
        "assignments": assignments
    }
    print(f"RESULT_JSON:{json.dumps(result_payload)}")
else:
    print(f"SOLVE_FAILED: status={status}")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid solutions.
- Assuming variable indices match parameter indices, causing incorrect cost calculations.
- Omitting structured output makes automated result parsing difficult.

# Workflow 2 (MILP with Pyomo and CBC/Gurobi)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for algebraic modeling and a MILP solver (e.g., CBC, Gurobi) for optimization. It is well-suited for problems with many pairwise exclusion constraints, leveraging presolve and cutting-plane algorithms for efficiency.

### Step 1 - Define Sets and Parameters
- Declare index sets `model.I = pyo.Set(initialize=<I_values>)` and `model.J = pyo.Set(initialize=<J_values>)`.
- Define cost parameter `model.cost = pyo.Param(model.I, model.J, initialize=cost_dict)` for objective coefficients.
- Optionally, define a set `model.incompatible_pairs` containing tuples `(i1, j1, i2, j2)` for exclusions.

### Step 2 - Create Binary Assignment Variables
- Create binary variables `model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)` representing assignment decisions.

### Step 3 - Enforce Assignment Cardinality
- Add constraints `sum(model.x[i, j] for i in model.I) <= 1 for each j in model.J` and `sum(model.x[i, j] for j in model.J) <= 1 for each i in model.I`.
- If a fixed total number of assignments `K` is required, add `sum(model.x[i, j] for i in model.I, j in model.J) == K`.

### Step 4 - Add Pairwise Exclusion Constraints
- Use `pyo.ConstraintList()` and iterate through `model.incompatible_pairs` to add constraints `model.x[i1, j1] + model.x[i2, j2] <= 1` for each incompatible pair.

### Step 5 - Define Linear Objective
- Set `model.obj = pyo.Objective(expr=sum(model.cost[i, j] * model.x[i, j] for i in model.I for j in model.J), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["I", "J", "incompatible_pairs"],
  "parameters": ["cost[I][J] (float)", "K (int, optional)"],
  "decision_variables": ["x[I][J] (binary)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i][j] for i in I) <= 1 for each j in J",
    "sum(x[i][j] for j in J) <= 1 for each i in I",
    "sum(x[i][j] for i in I, j in J) == K (if required)",
    "x[i1][j1] + x[i2][j2] <= 1 for each (i1,j1,i2,j2) in incompatible_pairs"
  ]
}
```

### Common Pitfalls
- Using `model.ConstraintList()` without proper initialization, leading to empty constraint lists.
- Mismatch between set indices and parameter keys causing `KeyError` during model construction.
- Forgetting to set the objective sense, defaulting to minimization but not explicitly stated.

## Solving stage

### Strategy Overview
Select an appropriate MILP solver, configure it for performance and accuracy, solve with rigorous status checking, and extract results while ensuring solution validity.

### Step 1 - Select and Configure Solver
- For open-source use, instantiate `solver = pyo.SolverFactory("cbc")`. For commercial performance, use `solver = pyo.SolverFactory("gurobi")`.
- Set solver options: `solver.options["seconds"] = <timeout>`, `solver.options["ratio"] = 0.0` for optimality gap tolerance (use `0.0` for exact), and `solver.options["threads"] = <num_threads>` for parallelism.

### Step 2 - Solve and Verify Termination
- Execute `results = solver.solve(model, tee=False)`.
- Check both `results.solver.status == pyo.SolverStatus.ok` and `results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)` before extracting solutions.

### Step 3 - Extract Assignments and Objective
- Iterate over `model.x` and collect indices where `pyo.value(model.x[i, j]) > 0.5` (binary threshold).
- Retrieve the objective value via `pyo.value(model.obj)`.

### Step 4 - Validate and Output Results
- Programmatically verify that the extracted assignments satisfy all cardinality and exclusion constraints.
- Output a structured dictionary with status, objective value, and assignments for integration.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective as per modeling stage

# Solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False)

# Extract results
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    assignments = []
    for i in model.I:
        for j in model.J:
            if pyo.value(model.x[i, j]) > 0.5:
                assignments.append((i, j))
    result_payload = {
        "status": results.solver.termination_condition.name,
        "objective_value": pyo.value(model.obj),
        "assignments": assignments
    }
    print(f"RESULT_JSON:{json.dumps(result_payload)}")
else:
    print(f"SOLVE_FAILED: status={results.solver.status}, termination={results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `solver.status` with `termination_condition`; both must be checked for a valid solution.
- Using `pyo.value()` on variables before solving, which returns `None` and causes errors.
- Not setting a time limit or gap tolerance, potentially allowing the solver to run indefinitely.
