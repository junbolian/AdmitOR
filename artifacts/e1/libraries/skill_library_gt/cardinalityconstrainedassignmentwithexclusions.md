---
name: CardinalityConstrainedAssignmentWithExclusions
description: |
  Model and solve binary assignment problems with exact total assignments, at-most-one constraints per element, and pairwise incompatibility rules, minimizing total cost.
---

# Workflow 1 (CP-SAT with Indicator Constraints)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT for its native support of indicator constraints (`OnlyEnforceIf`), avoiding big-M formulations for conditional logic. It is well-suited for problems where incompatibility rules are naturally expressed as "if-then" conditions.

### Step 1 - Define Core Assignment Variables
- Declare binary decision variables `x[i][j]` for each potential assignment between elements of set `I` and set `J`.
- Use `model.NewBoolVar(f"x_{i}_{j}")` to create each variable, ensuring a unique, traceable name.

### Step 2 - Enforce Assignment Cardinality Constraints
- For each element `i` in `I`, add constraint `sum(x[i][j] for j in J) <= 1` to allow at most one assignment.
- For each element `j` in `J`, add constraint `sum(x[i][j] for i in I) <= 1` to allow at most one assignment.
- Add a global cardinality constraint `sum(x[i][j] for i in I, j in J) == K` to enforce the exact total number of assignments `K`.

### Step 3 - Model Pairwise Incompatibility as Indicator Constraints
- For each conditional rule "if assignment `(i1, j1)` is selected, then assignment `(i2, j2)` must not be selected", create an indicator constraint.
- Use `model.Add(x[i2][j2] == 0).OnlyEnforceIf(x[i1][j1])`. This is more efficient than linearizing with `x[i1][j1] + x[i2][j2] <= 1` when the condition is one-directional.

### Step 4 - Formulate Linear Cost Objective
- Define a 2D cost parameter `cost[i][j]` for each potential assignment.
- Set the objective to minimize total cost: `model.Minimize(sum(cost[i][j] * x[i][j] for i in I, j in J))`. CP-SAT accepts floating-point coefficients.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": ["cost[i][j] for i in I, j in J", "K (exact total assignments)", "incompatibility_rules: list of (if (i1,j1), then_not (i2,j2))"],
  "decision_variables": ["x[i][j] ∈ {0,1} for i in I, j in J"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i][j] for j in J) <= 1 for each i in I",
    "sum(x[i][j] for i in I) <= 1 for each j in J",
    "sum(x[i][j] for i in I, j in J) == K",
    "x[i2][j2] == 0 enforced if x[i1][j1] == 1 for each incompatibility rule"
  ]
}
```

### Common Pitfalls
- Using big-M linearization for conditional constraints when CP-SAT's native `OnlyEnforceIf` is available and more efficient.
- Forgetting to enforce the global cardinality constraint `== K`, leading to solutions with fewer assignments than required.
- Not using unique variable names, which complicates debugging and solution extraction.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for a balance of speed and proof of optimality, using parallel search and a time limit. Extract and validate the solution against all modeled constraints.

### Step 1 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds = <time_limit>` to enforce a runtime cap.
- Set `solver.parameters.num_search_workers = <num_cores>` to enable parallel search.
- Set `solver.parameters.random_seed = <seed>` for reproducibility.
- Set `solver.parameters.relative_gap_limit = -1.0` to search for proven optimal solutions (disable gap tolerance).

### Step 2 - Solve and Check Status
- Invoke `solver.Solve(model)`.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. If not, handle as infeasible or search limit reached.

### Step 3 - Extract and Validate Solution
- For each variable `x[i][j]`, check `if solver.Value(x[i][j]) == 1` to identify active assignments.
- Store assignments and compute total cost by summing corresponding `cost[i][j]`.
- Programmatically verify all constraints: cardinality per element, total assignment count `K`, and that no indicator constraint is violated.

### Step 4 - Output Standardized Results
- Print a human-readable summary (e.g., `RESULT:{total_cost}`).
- Output a structured JSON payload containing solver status, objective value, and the list of assignments for downstream processing.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (variable and constraint creation as per modeling stage)
model.Minimize(objective_expr)

# solve with status / termination checks
solver = cp_model.CpSolver()
# ... (parameter configuration)
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract solution
    assignments = []
    total_cost = 0.0
    for i in I:
        for j in J:
            if solver.Value(x[i][j]) == 1:
                assignments.append((i, j))
                total_cost += cost[i][j]
    # ... (output results)
else:
    # Handle no solution found
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking for `cp_model.FEASIBLE` status when a time limit may prevent proving optimality, missing valid solutions.
- Failing to validate the extracted solution against constraints, potentially outputting an infeasible result due to modeling errors.
- Setting an overly restrictive time limit for problems that require proof of optimality.

# Workflow 2 (MILP with Linearized Constraints)

## Modeling stage

### Strategy Overview
This workflow uses a traditional Mixed-Integer Linear Programming (MILP) formulation with linear pairwise constraints, suitable for solvers like Gurobi, CBC, or CPLEX. It explicitly linearizes all incompatibility rules, creating a purely linear model.

### Step 1 - Define Binary Assignment Variables
- Declare binary decision variables `x[i,j]` for each `i` in set `I` and `j` in set `J`.
- In Pyomo, use `model.x = Var(I, J, within=Binary)` or similar construct in other modeling frameworks.

### Step 2 - Enforce Standard Assignment and Cardinality Constraints
- Add constraints `sum(x[i,j] for j in J) <= 1` for each `i` in `I`.
- Add constraints `sum(x[i,j] for i in I) <= 1` for each `j` in `J`.
- Add a global cardinality constraint `sum(x[i,j] for i in I, j in J) == K` to fix the total number of assignments.

### Step 3 - Linearize All Incompatibility Rules
- For each pairwise incompatibility rule, regardless of directionality, add a linear constraint `x[i1, j1] + x[i2, j2] <= 1`.
- Use a `ConstraintList` or iterative addition to handle a potentially large, programmatically generated set of such rules.

### Step 4 - Define Linear Cost Objective
- Define parameter `cost[i,j]` for each potential assignment.
- Set the objective to minimize `sum(cost[i,j] * x[i,j] for i in I, j in J)`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": ["cost[i,j] for i in I, j in J", "K (exact total assignments)", "incompatible_pairs: list of ((i1,j1), (i2,j2))"],
  "decision_variables": ["x[i,j] ∈ {0,1} for i in I, j in J"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i,j] for j in J) <= 1 for each i in I",
    "sum(x[i,j] for i in I) <= 1 for each j in J",
    "sum(x[i,j] for i in I, j in J) == K",
    "x[i1,j1] + x[i2,j2] <= 1 for each incompatible pair"
  ]
}
```

### Common Pitfalls
- Adding redundant linear incompatibility constraints (e.g., both `x[a]+x[b]<=1` and `x[b]+x[a]<=1`), which increases problem size unnecessarily.
- Modeling one-directional "if-then" rules as bidirectional exclusions, which may overly restrict the feasible space.
- Not leveraging the solver's presolve capabilities by manually simplifying the model excessively.

## Solving stage

### Strategy Overview
Utilize a high-performance MILP solver (e.g., Gurobi) configured for optimality, with a time limit and controlled parallelism. Implement robust solution checking and extraction.

### Step 1 - Select and Configure Solver
- Instantiate the solver (e.g., `SolverFactory('gurobi')`).
- Set optimality tolerance: `opt.options['MIPGap'] = 0.0` for proven optimality.
- Set a time limit: `opt.options['TimeLimit'] = <time_limit>`.
- Set a random seed for reproducibility: `opt.options['Seed'] = <seed>`.
- Control parallel threads: `opt.options['Threads'] = <num_threads>`.

### Step 2 - Solve and Verify Termination Status
- Execute `results = solver.solve(model, tee=<verbose_flag>)`.
- Check both the solver status (e.g., `results.solver.status == SolverStatus.ok`) and the termination condition (e.g., `results.solver.termination_condition == TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Validate Solution
- If solve was successful, retrieve the objective value from `model.obj()` or `results.Problem.objective()`.
- Iterate over variables `x[i,j]` and collect assignments where `value(x[i,j]) > 0.5`.
- Compute the total cost from the assignments and verify it matches the reported objective.
- Optionally, run a post-solve validation script to check all constraints are satisfied.

### Step 4 - Output and Handle Failures
- Print assignments and total cost in a clear, structured format.
- If the solver did not find a feasible solution, output a structured error message (e.g., JSON with `{"status": "infeasible"}`) for automated handling.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_set)
model.J = pyo.Set(initialize=J_set)
model.x = pyo.Var(model.I, model.J, within=pyo.Binary)
# ... (constraint and objective creation as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    # Extract solution
    assignments = []
    for i in model.I:
        for j in model.J:
            if pyo.value(model.x[i,j]) > 0.5:
                assignments.append((i, j))
    # ... (output results)
else:
    # Handle solve failure
    print({"status": "solve_failed", "termination_condition": str(results.solver.termination_condition)})
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`), leading to extraction attempts from incomplete solves.
- Not using a tolerance (e.g., `> 0.5`) when checking binary variable values due to solver numerical precision.
- Omitting a time limit, allowing the solver to run indefinitely on difficult instances.
