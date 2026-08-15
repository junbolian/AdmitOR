---
name: Cardinality-Constrained Assignment with Conflicts
description: |
  Model and solve binary assignment problems with one-to-one matching, fixed total assignments, and conditional conflicts, minimizing total cost.

---

# Workflow 1 (CP-SAT with Logical Implications)

## Modeling stage

### Strategy Overview
This workflow models the problem using OR-Tools CP-SAT, leveraging its native support for logical constraints via `OnlyEnforceIf` to encode conditional conflicts directly, avoiding big-M formulations.

### Step 1 - Define Sets and Parameters
- Define the two sets to be matched, e.g., `set1` and `set2`, as lists of identifiers.
- Define a cost dictionary `cost[i][j]` for each potential assignment.
- Define the required total number of assignments `K`.
- Define a list of conflict pairs `conflict_pairs` where `(i1, j1, i2, j2)` indicates that if assignment `(i1, j1)` is active, then assignment `(i2, j2)` must be inactive.

### Step 2 - Create Binary Assignment Variables
- Create a 2D dictionary of binary variables `x[i][j]` using `model.NewBoolVar(f"x_{i}_{j}")`.
- Each variable equals 1 if element `i` from `set1` is assigned to element `j` from `set2`.

### Step 3 - Add One-to-One Matching Constraints
- For each `i` in `set1`, add constraint `sum(x[i][j] for j in set2) <= 1`.
- For each `j` in `set2`, add constraint `sum(x[i][j] for i in set1) <= 1`.

### Step 4 - Add Fixed Cardinality Constraint
- Add a global constraint `sum(x[i][j] for i in set1 for j in set2) == K`.

### Step 5 - Add Conditional Conflict Constraints
- For each conflict pair `(i1, j1, i2, j2)`, add the logical implication: `model.Add(x[i2][j2] == 0).OnlyEnforceIf(x[i1][j1])`.

### Step 6 - Define Linear Objective
- Define the objective to minimize: `sum(cost[i][j] * x[i][j] for i in set1 for j in set2)`.

### Formulation Template
```json
{
  "sets": ["set1", "set2"],
  "parameters": ["cost[set1][set2]", "K", "conflict_pairs"],
  "decision_variables": ["x[set1][set2] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "sum(x[i][j] for j in set2) <= 1, ∀i ∈ set1",
    "sum(x[i][j] for i in set1) <= 1, ∀j ∈ set2",
    "sum(x[i][j] for all i,j) == K",
    "x[i2][j2] == 0, ∀(i1,j1,i2,j2) ∈ conflict_pairs, enforced if x[i1][j1] == 1"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce the `OnlyEnforceIf` constraint bidirectionally if the conflict is mutual; use two separate constraints if needed.
- Using large, dense cost matrices can slow model construction; use sparse dictionaries for large, mostly-infeasible assignment spaces.
- Misinterpreting the conflict list format; ensure each tuple clearly identifies the triggering assignment and the forbidden assignment.

## Solving stage

### Strategy Overview
Solve using the OR-Tools CP-SAT solver, configured for exact optimization with runtime limits and parallel search, then extract and verify the assignment solution.

### Step 1 - Configure Solver Parameters
- Instantiate the CP-SAT solver.
- Set `solver.parameters.max_time_in_seconds` to control runtime.
- Set `solver.parameters.num_search_workers` for parallel processing.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to require optimality.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status: `cp_model.OPTIMAL` or `cp_model.FEASIBLE` are acceptable. Handle `INFEASIBLE` or `UNKNOWN` with appropriate error output.

### Step 3 - Extract Solution
- If the solve was successful, iterate over all `x[i][j]` variables.
- Collect tuples `(i, j)` where `solver.Value(x[i][j]) == 1`.
- Calculate the total cost by summing `cost[i][j]` for these active assignments.

### Step 4 - Validate Solution
- Programmatically verify that the extracted assignments satisfy all constraints: one-to-one matching, cardinality, and all conflict implications.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build model as per Modeling Stage steps)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters as per Step 1
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    assignments = []
    total_cost = 0.0
    for i in set1:
        for j in set2:
            if solver.Value(x[i][j]) == 1:
                assignments.append((i, j))
                total_cost += cost[i][j]
    # Output result, e.g., print(f"RESULT:{total_cost}")
    # Validate assignments (Step 4)
else:
    # Output structured error, e.g., print(f"RESULT_JSON:{{'status':{status}}}")
```

### Common Pitfalls
- Not checking for `FEASIBLE` status when a time limit is set; a feasible but non-optimal solution may still be useful.
- Assuming variable indices match list indices; ensure consistent mapping between model variable names and data structures.
- Omitting solution validation, which is critical for catching modeling errors in complex conditional constraints.

# Workflow 2 (MILP with Pairwise Conflict Constraints)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Linear Program (MILP) using a modeling framework like Pyomo, encoding conditional conflicts as pairwise linear inequalities, suitable for solvers like CBC or Gurobi.

### Step 1 - Define Sets and Parameters
- Define the two sets to be matched, e.g., `model.set1` and `model.set2` as Pyomo `Set` objects.
- Define a cost parameter `model.cost[i,j]` via a Pyomo `Param` initialized from a dictionary.
- Define the required total number of assignments `model.K` as a parameter.
- Define a set `model.conflict_pairs` containing tuples `(i1, j1, i2, j2)` representing mutually exclusive assignments.

### Step 2 - Create Binary Assignment Variables
- Define a binary variable `model.x[i,j]` for each `i` in `set1` and `j` in `set2` using `pyo.Var(domain=pyo.Binary)`.

### Step 3 - Add One-to-One Matching Constraints
- For each `i` in `set1`, add constraint `sum(model.x[i,j] for j in model.set2) <= 1`.
- For each `j` in `set2`, add constraint `sum(model.x[i,j] for i in model.set1) <= 1`.

### Step 4 - Add Fixed Cardinality Constraint
- Add a global constraint `sum(model.x[i,j] for i in model.set1 for j in model.set2) == model.K`.

### Step 5 - Add Pairwise Conflict Constraints
- For each `(i1, j1, i2, j2)` in `model.conflict_pairs`, add a linear constraint: `model.x[i1,j1] + model.x[i2,j2] <= 1`.

### Step 6 - Define Linear Objective
- Define the objective: `sum(model.cost[i,j] * model.x[i,j] for i in model.set1 for j in model.set2)` and set `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["set1", "set2", "conflict_pairs"],
  "parameters": ["cost[set1,set2]", "K"],
  "decision_variables": ["x[set1,set2] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j])"
  },
  "constraints": [
    "sum(x[i,j] for j in set2) <= 1, ∀i ∈ set1",
    "sum(x[i,j] for i in set1) <= 1, ∀j ∈ set2",
    "sum(x[i,j] for all i,j) == K",
    "x[i1,j1] + x[i2,j2] <= 1, ∀(i1,j1,i2,j2) ∈ conflict_pairs"
  ]
}
```

### Common Pitfalls
- Using the pairwise constraint `x_A + x_B <= 1` for a one-way conditional conflict (if A then not B) wastes a constraint; ensure conflicts are symmetric or use two separate constraints for directionality.
- Defining the cost parameter as a dense matrix for sparse problems can cause memory issues; use a dictionary with default values for missing assignments.
- Not indexing the `conflict_pairs` set correctly within the modeling framework, leading to constraint construction errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver (e.g., CBC via `pyo.SolverFactory`), configured for optimality, with proper handling of solver status and solution extraction.

### Step 1 - Select and Configure Solver
- Instantiate a solver object, e.g., `solver = pyo.SolverFactory("cbc")`.
- Set solver options: `seconds` for time limit, `ratio=0.0` for zero optimality gap tolerance, and `threads` for parallel processing.

### Step 2 - Solve and Check Termination Condition
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.termination_condition`. Accept `TerminationCondition.optimal` or `TerminationCondition.feasible`. Handle `infeasible` or `other` with error output.

### Step 3 - Extract Solution
- If the solve was successful, iterate over `model.x[i,j]` variables.
- Collect tuples `(i, j)` where `pyo.value(model.x[i,j]) > 0.5`.
- Calculate the total cost by summing `model.cost[i,j]` for these active assignments.

### Step 4 - Validate Solution
- Programmatically verify the extracted assignments satisfy all one-to-one, cardinality, and pairwise conflict constraints.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (build model as per Modeling Stage steps)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

term_cond = str(results.solver.termination_condition)
if term_cond in ["optimal", "feasible"]:
    assignments = []
    total_cost = 0.0
    for i in model.set1:
        for j in model.set2:
            if pyo.value(model.x[i,j]) > 0.5:
                assignments.append((i, j))
                total_cost += pyo.value(model.cost[i,j])
    # Output result, e.g., print(f"RESULT:{total_cost}")
    # Validate assignments (Step 4)
else:
    # Output structured error, e.g., print(f"RESULT_JSON:{term_cond}")
```

### Common Pitfalls
- Using `pyo.value()` on a variable without checking if the solve succeeded first, which may raise an error.
- Setting `ratio=0.0` with a tight time limit may prevent finding any feasible solution; consider a small positive gap for practical timeouts.
- Not using `pyo.value()` to access parameter values in the solution extraction loop, which is necessary for Pyomo parameters.
