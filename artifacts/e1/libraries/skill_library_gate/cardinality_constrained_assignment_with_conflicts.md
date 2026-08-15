---
name: Cardinality-Constrained Assignment with Conflicts
description: |
  Model and solve one-to-one assignment problems with fixed total assignments, pairwise conflicts, and linear cost minimization using CP-SAT or MIP solvers.

---

# Workflow 1 (CP-SAT with Conditional Enforcement)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT for its native support of implication constraints (`OnlyEnforceIf`), which is ideal for modeling conditional conflicts directly. It is well-suited for problems where conflicts are defined as "if assignment A is active, then assignment B must be forbidden."

### Step 1 - Define Binary Assignment Variables
- Create a binary decision variable `x[i][j]` for each possible assignment between element `i` in the first set and element `j` in the second set.
- Use `model.NewBoolVar(f"x_{i}_{j}")` to instantiate each variable.

### Step 2 - Enforce One-to-One Matching Cardinality
- For each element `i` in the first set, add a constraint `sum(x[i][j] for j in J) <= 1`.
- For each element `j` in the second set, add a constraint `sum(x[i][j] for i in I) <= 1`.
- This ensures at most one assignment per element in each dimension.

### Step 3 - Fix Total Number of Assignments
- Add a global cardinality constraint: `sum(x[i][j] for all i, j) == K`, where `K` is the required number of assignments.
- Combined with the "at most one" constraints, this enforces exactly `K` total assignments.

### Step 4 - Model Conditional Conflict Constraints
- For each conflict rule stating that assignment `(a,b)` forbids assignment `(c,d)`, add the implication: `model.Add(x[c][d] == 0).OnlyEnforceIf(x[a][b])`.
- This directly encodes the conditional logic without requiring linearization.

### Step 5 - Define Linear Minimization Objective
- Formulate the objective as `sum(cost[i][j] * x[i][j] for all i, j)`, where `cost` is a given matrix.
- Set the objective sense to minimize using `model.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": [
    "I = [...]",
    "J = [...]"
  ],
  "parameters": [
    "cost[i][j] for i in I, j in J",
    "K (total assignments)",
    "conflicts = [(a,b,c,d) ...]"
  ],
  "decision_variables": [
    "x[i][j] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "sum_j x[i][j] ≤ 1 ∀ i ∈ I",
    "sum_i x[i][j] ≤ 1 ∀ j ∈ J",
    "sum_{i,j} x[i][j] = K",
    "x[c][d] = 0 if x[a][b] = 1 ∀ (a,b,c,d) in conflicts"
  ]
}
```

### Common Pitfalls
- Forgetting to combine the "at most one" constraints with the fixed total `K` constraint, which can lead to under-assignment.
- Incorrectly ordering the indices in implication constraints, leading to reversed logic.
- Using floating-point coefficients in the objective without ensuring they are compatible with CP-SAT's internal representation.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for exact optimization with parallel search and time limits. Always check solver status and programmatically verify the solution against all constraints.

### Step 1 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` for a runtime limit.
- Set `solver.parameters.num_search_workers` to leverage multiple CPU cores (e.g., 8).
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to enforce exact optimization.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)` and capture the status.
- Check if `status` is `cp_model.OPTIMAL` (proven optimum) or `cp_model.FEASIBLE` (feasible solution found within limits).

### Step 3 - Extract and Verify Solution
- Iterate over all `x[i][j]` variables; collect indices where `solver.Value(x[i][j]) == 1`.
- Calculate the total cost by summing `cost[i][j]` for active assignments.
- Programmatically verify: row/column sums ≤ 1, total assignments = K, and all conflict implications hold.

### Step 4 - Standardize Output
- Print status, objective value, and list of active assignments.
- For programmatic use, output a clear result line like `RESULT:{objective_value}` on success.
- On failure or infeasibility, output a structured JSON error payload with solver status details.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (construct variables, constraints, objective)
# solve with status / termination checks
solver = cp_model.CpSolver()
# ... (set parameters)
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract and verify solution
    assignments = [(i, j) for i in I for j in J if solver.Value(x[i][j]) == 1]
    total_cost = sum(cost[i][j] for i, j in assignments)
    # Verify constraints programmatically
    # ... (verification logic)
    print(f"RESULT:{total_cost}")
else:
    # Handle failure
    print(json.dumps({"error": "Solver failed", "status": status}))
```

### Common Pitfalls
- Not checking for `FEASIBLE` status, which may miss valid but non-optimal solutions when time runs out.
- Assuming variable values are integers without calling `solver.Value()`.
- Neglecting to verify the solution, which can miss modeling errors.

---

# Workflow 2 (MIP with Linear Conflict Constraints)

## Modeling stage

### Strategy Overview
This workflow uses a traditional MIP formulation (e.g., with Pyomo and Gurobi/CBC) where all constraints, including conflicts, are expressed linearly. It is portable across many solvers and uses the standard `x[a,b] + x[c,d] <= 1` pattern for pairwise incompatibilities.

### Step 1 - Define Sets and Binary Variables
- Define index sets `I` and `J` for the two assignment dimensions.
- Create binary decision variables `x[i,j]` using `pyo.Var(I, J, within=pyo.Binary)`.

### Step 2 - Enforce Cardinality Constraints
- Add constraints: `sum(x[i,j] for j in J) <= 1` for each `i` in `I`.
- Add constraints: `sum(x[i,j] for i in I) <= 1` for each `j` in `J`.

### Step 3 - Set Fixed Total Assignments
- Add a global constraint: `sum(x[i,j] for i in I, j in J) == K`.

### Step 4 - Model Conflicts as Linear Pairwise Constraints
- For each incompatible pair of assignments `(a,b)` and `(c,d)`, add a linear constraint: `x[a,b] + x[c,d] <= 1`.
- This directly prohibits both assignments from being selected simultaneously.

### Step 5 - Define Linear Cost Minimization Objective
- Define the objective as `sum(cost[i,j] * x[i,j] for i in I, j in J)`, where `cost` is a provided parameter dictionary.
- Set the objective sense to minimize.

### Formulation Template
```json
{
  "sets": [
    "I = [...]",
    "J = [...]"
  ],
  "parameters": [
    "cost[i,j] for i in I, j in J",
    "K (total assignments)",
    "incompatible_pairs = [((a,b), (c,d)) ...]"
  ],
  "decision_variables": [
    "x[i,j] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j])"
  },
  "constraints": [
    "sum_j x[i,j] ≤ 1 ∀ i ∈ I",
    "sum_i x[i,j] ≤ 1 ∀ j ∈ J",
    "sum_{i,j} x[i,j] = K",
    "x[a,b] + x[c,d] ≤ 1 ∀ ((a,b), (c,d)) in incompatible_pairs"
  ]
}
```

### Common Pitfalls
- Defining the cost parameter as a 2D list without proper indexing, leading to key errors when building the objective.
- Using `==` instead of `<=` in the one-to-one constraints, which would incorrectly force an assignment for every element.
- Forgetting to convert the `K` parameter to an integer or float as required by the modeling framework.

## Solving stage

### Strategy Overview
Configure a MIP solver (Gurobi or CBC) for exact optimization with time and gap limits. Check solver status and termination condition, then extract and verify the solution.

### Step 1 - Configure Solver and Solve
- Instantiate the solver factory (e.g., `pyo.SolverFactory("gurobi")`).
- Set key parameters: `MIPGap=0.0` (or `ratio=0.0` for CBC) for optimality, `TimeLimit` for runtime, `Threads` for parallelism, and `Seed` for reproducibility.
- Call `solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Verify `results.solver.status == pyo.SolverStatus.ok`.
- Check `results.solver.termination_condition` for `optimal` (proven optimum) or `feasible` (solution within limits).

### Step 3 - Extract Solution and Compute Cost
- Iterate over `x[i,j]` variables; if `pyo.value(x[i,j]) > 0.5`, consider the assignment active.
- Store active assignments in a list.
- Compute the total cost by summing `cost[i,j]` for active assignments, independent of the solver's objective value, for verification.

### Step 4 - Verify and Report Results
- Programmatically verify all constraints: row/column sums, total assignments, and conflict constraints.
- Print the objective value and list of assignments.
- Provide a structured error output if the solver fails or proves infeasibility.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_list)
model.J = pyo.Set(initialize=J_list)
model.x = pyo.Var(model.I, model.J, within=pyo.Binary)
# ... (add constraints and objective)
# solve with status / termination checks
solver = pyo.SolverFactory("gurobi")
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = time_limit
results = solver.solve(model)
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    # Extract and verify solution
    assignments = [(i, j) for i in model.I for j in model.J if pyo.value(model.x[i,j]) > 0.5]
    total_cost = sum(cost_dict[i,j] for i, j in assignments)
    # ... (verification logic)
    print(f"RESULT:{total_cost}")
else:
    # Handle failure
    print(json.dumps({"error": "Solver failed", "status": str(results.solver.status)}))
```

### Common Pitfalls
- Setting a negative `MIPGap` value, which causes a solver error.
- Comparing variable values to exactly 1.0; use a tolerance (e.g., `> 0.5`) due to floating-point precision.
- Not passing necessary data (like the cost dictionary) to the solving function, causing scope errors in post-processing.
