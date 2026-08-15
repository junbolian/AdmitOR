---
name: BinaryAssignmentWithCardinalityAndExclusion
description: |
  Model and solve binary assignment problems with cardinality constraints, pairwise exclusions, and cost minimization using MILP/CP-SAT solvers.
---

# Workflow 1 (Pyomo with MILP Solver)

## Modeling stage

### Strategy Overview
Formulate the assignment problem as a Mixed-Integer Linear Program (MILP) using Pyomo's structured modeling. This approach is portable across open-source (HiGHS, GLPK) and commercial (Gurobi) solvers, emphasizing clear separation of sets, parameters, variables, and constraints.

### Step 1 - Define Sets and Parameters
- Define two sets: `SET_A` (e.g., items from first group) and `SET_B` (e.g., items from second group).
- Define a cost parameter `COST[a][b]` representing the penalty for assigning `a` to `b`. Use a dictionary or 2D array for initialization.

### Step 2 - Create Binary Decision Variables
- Create binary decision variables `x[a, b]` for all `a` in `SET_A` and `b` in `SET_B` using `pyo.Var(domain=pyo.Binary)`.

### Step 3 - Implement Cardinality Constraints
- Add constraint `sum(x[a, b] for b in SET_B) <= 1` for each `a` in `SET_A` to enforce at most one assignment per element of SET_A.
- Add constraint `sum(x[a, b] for a in SET_A) <= 1` for each `b` in `SET_B` to enforce at most one assignment per element of SET_B.
- Add a global cardinality constraint `sum(x[a, b] for a in SET_A for b in SET_B) == K` to fix the total number of assignments to `K`.

### Step 4 - Add Pairwise Exclusion Constraints
- For each incompatible assignment pair `(a1, b1, a2, b2)`, add a linear constraint `x[a1, b1] + x[a2, b2] <= 1`.

### Step 5 - Formulate Objective
- Define the objective to minimize total cost: `minimize sum(COST[a][b] * x[a, b] for a in SET_A for b in SET_B)`.

### Formulation Template
```json
{
  "sets": ["SET_A", "SET_B"],
  "parameters": ["COST[a][b]"],
  "decision_variables": ["x[a,b] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "∑_{a∈SET_A, b∈SET_B} COST[a][b] * x[a,b]"
  },
  "constraints": [
    "∑_{b∈SET_B} x[a,b] ≤ 1 ∀a∈SET_A",
    "∑_{a∈SET_A} x[a,b] ≤ 1 ∀b∈SET_B",
    "∑_{a∈SET_A, b∈SET_B} x[a,b] = K",
    "x[a1,b1] + x[a2,b2] ≤ 1 ∀(a1,b1,a2,b2)∈INCOMPATIBLE_PAIRS"
  ]
}
```

### Common Pitfalls
- Using lambda functions for constraints that cause indexing issues; prefer explicit `add_component` for pairwise exclusions.
- Setting `MIPGap` to an invalid value like `-1`; use `0.0` for optimality or a small positive tolerance.
- Omitting the global cardinality constraint (`K`) when a specific number of assignments is required.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver, with robust status checking and solution extraction. Implement verification via enumeration for small instances to validate model correctness.

### Step 1 - Configure and Execute Solver
- Instantiate the solver via `pyo.SolverFactory("solver_name")` (e.g., "highs", "gurobi").
- Set key parameters: `time_limit=30`, `mip_rel_gap=0.0` (or `MIPGap=0.0`), `threads=4`, `seed=42` for reproducibility.
- Execute the solve with `solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Check `solver.status == pyo.SolverStatus.ok` and `solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]`.
- If status is not acceptable, log an error or try a fallback solver (e.g., switch from HiGHS to GLPK).

### Step 3 - Extract and Verify Solution
- Iterate over variables `x[a,b]` and collect assignments where `pyo.value(x[a,b]) > 0.5`.
- Recalculate total cost from the extracted assignments to verify objective value consistency.
- For small problems (e.g., |SET_A|*|SET_B| ≤ 100), perform exhaustive enumeration using `itertools` to confirm optimality.

### Step 4 - Output Standardized Results
- Print the solver status, total cost, and list of assignments.
- For automated parsing, output the final objective value with a prefix: `print(f"RESULT:{total_cost}")`.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.A = pyo.Set(initialize=SET_A)
model.B = pyo.Set(initialize=SET_B)
model.x = pyo.Var(model.A, model.B, domain=pyo.Binary)
# ... add objective and constraints as per modeling steps

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)

if (pyo.check_optimal_termination(results) or
    (solver.status == pyo.SolverStatus.ok and
     solver.termination_condition == pyo.TerminationCondition.feasible)):
    # Extract solution
    assignments = [(a, b) for a in model.A for b in model.B if pyo.value(model.x[a, b]) > 0.5]
    total_cost = sum(COST[a][b] for a, b in assignments)
    print(f"RESULT:{total_cost}")
else:
    print("SOLVE_FAILED")
```

### Common Pitfalls
- Trusting a non-optimal or unknown solver status without verification; always check both status and termination condition.
- Outputting pseudo-numeric answers when the solve fails; instead, provide a clear failure signal.
- Using a cost matrix with missing entries for some (a,b) pairs without proper default values.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Formulate the problem using Google OR-Tools CP-SAT, a constraint programming solver optimized for Boolean and integer variables. This workflow is efficient for binary assignment problems and provides fine-grained control over search parameters.

### Step 1 - Initialize Model and Create Variables
- Create a CP-SAT model: `model = cp_model.CpModel()`.
- For each `a` in `SET_A` and `b` in `SET_B`, create a binary variable `x[a, b] = model.NewBoolVar(f"x_{a}_{b}")`.

### Step 2 - Enforce Assignment Cardinality
- For each `a` in `SET_A`, add `model.Add(sum(x[a, b] for b in SET_B) <= 1)`.
- For each `b` in `SET_B`, add `model.Add(sum(x[a, b] for a in SET_A) <= 1)`.
- Add global cardinality: `model.Add(sum(x[a, b] for a in SET_A for b in SET_B) == K)`.

### Step 3 - Add Pairwise Incompatibility Constraints
- For each incompatible pair `(a1, b1, a2, b2)`, add `model.Add(x[a1, b1] + x[a2, b2] <= 1)`.

### Step 4 - Define Linear Minimization Objective
- Create a linear expression: `objective_expr = sum(COST[a][b] * x[a, b] for a in SET_A for b in SET_B)`.
- Set the objective: `model.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": ["SET_A", "SET_B"],
  "parameters": ["COST[a][b]"],
  "decision_variables": ["x[a,b] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "∑_{a∈SET_A, b∈SET_B} COST[a][b] * x[a,b]"
  },
  "constraints": [
    "∑_{b∈SET_B} x[a,b] ≤ 1 ∀a∈SET_A",
    "∑_{a∈SET_A} x[a,b] ≤ 1 ∀b∈SET_B",
    "∑_{a∈SET_A, b∈SET_B} x[a,b] = K",
    "x[a1,b1] + x[a2,b2] ≤ 1 ∀(a1,b1,a2,b2)∈INCOMPATIBLE_PAIRS"
  ]
}
```

### Common Pitfalls
- Using `model.NewIntVar` instead of `model.NewBoolVar` for binary variables, which reduces solver efficiency.
- Forgetting to scale large integer costs, which can cause numerical issues; consider scaling or using floating-point objectives if supported.
- Adding constraints with incorrect indexing, leading to missing or incorrect constraints.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured search parameters, extract the first feasible/optimal solution, and verify results. This solver is designed for combinatorial problems and often finds solutions quickly.

### Step 1 - Configure Solver Parameters
- Create a solver instance: `solver = cp_model.CpSolver()`.
- Set parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 8`, `solver.parameters.random_seed = 42`.
- For exact optimality, set `solver.parameters.relative_gap_limit = -1.0` (or a small positive value for early stopping).

### Step 2 - Execute Solve and Check Status
- Execute `status = solver.Solve(model)`.
- Check if `status in [cp_model.OPTIMAL, cp_model.FEASIBLE]`. If `OPTIMAL`, the best bound is proven.

### Step 3 - Extract Assignments and Compute Cost
- Iterate over all variable indices and collect assignments where `solver.Value(x[a, b]) == 1`.
- Compute total cost by summing `COST[a][b]` for each active assignment. Optionally, verify against `solver.ObjectiveValue()`.

### Step 4 - Validate with Enumeration (Small Instances)
- For small problem sizes, enumerate all feasible assignments using `itertools.combinations` and `itertools.permutations` to confirm the solver's solution is optimal.

### Step 5 - Output Results
- Print the status (`OPTIMAL`/`FEASIBLE`), total cost, and assignment list.
- Output the final objective value in a parseable format: `print(f"RESULT:{total_cost}")`.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
x = {}
for a in SET_A:
    for b in SET_B:
        x[(a, b)] = model.NewBoolVar(f"x_{a}_{b}")
# ... add constraints and objective as per modeling steps

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    assignments = [(a, b) for a in SET_A for b in SET_B if solver.Value(x[(a, b)]) == 1]
    total_cost = sum(COST[a][b] for a, b in assignments)
    print(f"RESULT:{total_cost}")
else:
    print("SOLVE_FAILED")
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; only `OPTIMAL` guarantees the best bound is found.
- Not using `num_search_workers` to parallelize search, leaving performance on the table.
- Misinterpreting the `relative_gap_limit` parameter; use `-1.0` to disable early stopping for proven optimality.
