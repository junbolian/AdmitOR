---
name: AssignmentProblemWithCardinalityAndConflicts
description: |
  Solve one-to-one matching problems with fixed total assignments, pairwise incompatibilities, and linear cost minimization using binary decision variables.
---

# Workflow 1 (CP-SAT via OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, which is designed for discrete optimization problems with logical constraints. It excels at problems with many binary variables and complex conditional logic, offering a clean API for `OnlyEnforceIf` style constraints.

### Step 1 - Define Sets and Parameters
- Define the source set `I` and destination set `J` as Python lists or ranges.
- Define a cost matrix `cost[i][j]` as a 2D list or dictionary mapping assignment tuples to numerical costs.
- Define the required total number of assignments `K` as an integer.
- Define any pairwise conflict pairs as a list of tuples `((i1, j1), (i2, j2))`.

### Step 2 - Create Binary Assignment Variables
- Use `model.NewBoolVar(f'x_{i}_{j}')` to create a binary variable `x[i][j]` for each `i` in `I` and `j` in `J`.
- Store variables in a 2D list or dictionary for easy access during constraint building.

### Step 3 - Enforce One-to-One Matching
- For each source `i` in `I`, add constraint `sum(x[i][j] for j in J) <= 1`.
- For each destination `j` in `J`, add constraint `sum(x[i][j] for i in I) <= 1`.

### Step 4 - Enforce Fixed Cardinality
- Add a global constraint `sum(x[i][j] for i in I for j in J) == K`.

### Step 5 - Add Conflict Constraints
- For each conflict pair `((a,b), (c,d))`, add a linear constraint `x[a][b] + x[c][d] <= 1`.
- Alternatively, for conditional conflicts (if A then not B), use `model.Add(conflict_var == 0).OnlyEnforceIf(trigger_var)`.

### Step 6 - Define Linear Objective
- Formulate the objective as `model.Minimize(sum(cost[i][j] * x[i][j] for i in I for j in J))`.

### Formulation Template
```json
{
  "sets": ["I (source)", "J (destination)"],
  "parameters": ["cost[I][J]", "K (total assignments)", "conflict_pairs"],
  "decision_variables": ["x[I][J] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "sum_j x[i][j] ≤ 1 ∀i ∈ I",
    "sum_i x[i][j] ≤ 1 ∀j ∈ J",
    "sum_{i,j} x[i][j] = K",
    "x[a][b] + x[c][d] ≤ 1 ∀ ((a,b),(c,d)) ∈ conflict_pairs"
  ]
}
```

### Common Pitfalls
- Forgetting to check for `FEASIBLE` status in addition to `OPTIMAL` when a time limit is set.
- Using large, dense cost matrices in list-of-lists format when a dictionary for sparse costs is more efficient.
- Misapplying `OnlyEnforceIf` for symmetric conflicts; use the simpler linear form `x1 + x2 <= 1`.

## Solving stage

### Strategy Overview
The solving stage configures the CP-SAT solver for performance and reproducibility, executes the model, and rigorously checks the status before extracting and verifying the solution.

### Step 1 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` to control runtime.
- Set `solver.parameters.num_search_workers` to the number of CPU cores for parallel solving.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to seek proven optimality.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)` and capture the result status.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before proceeding.

### Step 3 - Extract Solution
- Iterate through all variables `x[i][j]`.
- If `solver.Value(x[i][j]) == 1`, record the assignment `(i, j)` and its cost.
- Calculate the total cost from the solution for verification.

### Step 4 - Verify Constraints
- Verify each `i` appears in at most one active assignment.
- Verify each `j` appears in at most one active assignment.
- Verify the total number of active assignments equals `K`.
- Verify all conflict constraints are satisfied.

### Code Usage
```python
from ortools.sat.python import cp_model
import json

# 1. Build Model
model = cp_model.CpModel()
# ... [Variable and constraint creation as per Modeling Stage] ...

# 2. Configure and Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = -1.0  # Disable relative gap, use absolute

status = solver.Solve(model)

# 3. Check Status and Extract Solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = []
    total_cost = 0
    for i in I:
        for j in J:
            if solver.Value(x[i][j]) == 1:
                assignments.append((i, j))
                total_cost += cost[i][j]
    result = {"status": "SUCCESS", "objective": total_cost, "assignments": assignments}
else:
    result = {"status": "FAILED", "solver_status": status}
print(json.dumps(result, indent=2))
```

### Common Pitfalls
- Setting `relative_gap_limit` to a negative value incorrectly; use `-1.0` to disable.
- Not handling the `FEASIBLE` status when a time limit prevents proving optimality.
- Attempting to access `solver.Value()` on a variable before checking the solve status, which may crash.

# Workflow 2 (MILP via Pyomo with Gurobi/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to formulate the problem as a Mixed-Integer Linear Program (MILP). It can interface with commercial solvers like Gurobi or open-source ones like CBC, providing flexibility and advanced MIP tuning.

### Step 1 - Declare Abstract Sets and Parameters
- Use `pyo.Set(initialize=...)` to define abstract sets `model.I` and `model.J`.
- Use `pyo.Param(model.I, model.J, initialize=...)` or a dictionary to define the cost parameter.
- Define scalar parameters for `K` and a set for `conflict_pairs`.

### Step 2 - Define Binary Decision Variables
- Declare `model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)`.

### Step 3 - Enforce Matching and Cardinality via Constraints
- Add a `pyo.Constraint` rule for rows: `sum(model.x[i,j] for j in model.J) <= 1` for each `i`.
- Add a `pyo.Constraint` rule for columns: `sum(model.x[i,j] for i in model.I) <= 1` for each `j`.
- Add a global constraint: `sum(model.x[i,j] for i in model.I for j in model.J) == K`.

### Step 4 - Implement Conflict Constraints
- For each conflict pair, add a concrete constraint: `model.x[a,b] + model.x[c,d] <= 1`.
- This can be done by iterating over the `conflict_pairs` list and adding constraints to the model.

### Step 5 - Formulate the Objective Function
- Define `model.obj = pyo.Objective(expr=sum(cost[i,j] * model.x[i,j] for i in model.I for j in model.J), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": ["cost[I,J]", "K", "ConflictPairs"],
  "decision_variables": ["x[I,J] binary"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j])"
  },
  "constraints": [
    "RowLimit(i): sum_j x[i,j] <= 1",
    "ColLimit(j): sum_i x[i,j] <= 1",
    "TotalAssignments: sum_{i,j} x[i,j] = K",
    "Conflict((a,b),(c,d)): x[a,b] + x[c,d] <= 1"
  ]
}
```

### Common Pitfalls
- Defining the cost parameter inside a function scope where the model cannot access it; pass it as an argument or make it a model parameter.
- Using `==` instead of `<=` for the one-to-one matching constraints, which would incorrectly force an assignment for every element.
- Adding conflict constraints for non-existent variable indices, causing a key error.

## Solving stage

### Strategy Overview
This stage involves selecting a solver backend (Gurobi or CBC), configuring it for optimality and performance, solving the Pyomo model, and handling the solver's termination status to robustly extract results.

### Step 1 - Instantiate Solver and Set Options
- For Gurobi: `solver = pyo.SolverFactory('gurobi')`. Set options like `opt['MIPGap']=0.0`, `opt['TimeLimit']=30`, `opt['Threads']=8`, `opt['Seed']=42`.
- For CBC: `solver = pyo.SolverFactory('cbc')`. Set options like `opt['seconds']=30`, `opt['ratio']=0.0` (for gap), `opt['threads']=8`.

### Step 2 - Solve and Check Termination Status
- Execute `results = solver.solve(model, tee=False)`.
- Import `SolverStatus` and `TerminationCondition` from `pyomo.opt`.
- Check if `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]`.

### Step 3 - Extract and Validate Solution
- If solve was successful, iterate through `model.x`.
- Where `pyo.value(model.x[i,j]) > 0.5`, record the assignment.
- Calculate the objective value from the assignments for cross-verification with `pyo.value(model.obj)`.

### Step 4 - Handle Failures Gracefully
- If the solver fails to find a feasible solution, output a structured error message including the solver status and termination condition for debugging.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# 1. Build Model (Abstract or Concrete)
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=source_list)
model.J = pyo.Set(initialize=dest_list)
# ... [Variable, constraint, objective creation as per Modeling Stage] ...

# 2. Select and Configure Solver
solver = pyo.SolverFactory('gurobi')  # or 'cbc'
solver_options = {
    'MIPGap': 0.0,
    'TimeLimit': 30,
    'Threads': 8,
    'Seed': 42
}

# 3. Solve and Check Status
results = solver.solve(model, options=solver_options)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    assignments = []
    total_cost = 0
    for i in model.I:
        for j in model.J:
            if pyo.value(model.x[i, j]) > 0.5:
                assignments.append((i, j))
                total_cost += cost_dict[(i, j)]  # Use pre-defined cost dictionary
    result = {"status": "SUCCESS", "objective": total_cost, "assignments": assignments}
else:
    result = {
        "status": "FAILED",
        "solver_status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
print(json.dumps(result, indent=2))
```

### Common Pitfalls
- For CBC, setting `ratio=-1` to seek optimality; use `ratio=0.0` instead.
- Not checking both `SolverStatus.ok` and `TerminationCondition` before extracting values.
- Assuming the model object is updated after `solve`; always use `pyo.value()` or `model.x[i,j].value` to access solution values.
