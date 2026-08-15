---
name: Sequence Scheduling with Time Windows and Linear Penalties
description: |
  Model and solve sequencing problems with separation requirements, time windows, and linear deviation penalties using either CP-SAT or MIP solvers.

---

# Workflow 1 (CP-SAT with Explicit Transitivity)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, which natively handles integer variables and logical constraints. It models the problem with binary ordering variables, explicit transitivity constraints, and a linear penalty objective, leveraging the solver's efficient handling of indicator constraints.

### Step 1 - Define Core Variables
- Create an integer or continuous variable `t[i]` for each entity `i`, bounded by its `earliest[i]` and `latest[i]` time window.
- Create non-negative integer variables `e[i]` and `l[i]` for early and late deviations, bounded by `target[i] - earliest[i]` and `latest[i] - target[i]` respectively.
- Create a binary variable `y[i,j]` for each unordered pair `(i, j)` where `i < j`, to indicate precedence.

### Step 2 - Link Time and Deviations
- Add the constraint `t[i] - target[i] == l[i] - e[i]` for each entity `i`. This defines deviations without requiring absolute values.

### Step 3 - Enforce Separation with Indicator Constraints
- For each unordered pair `(i, j)`, add the indicator constraint: `y[i,j] == 1` implies `t[i] + sep[i,j] <= t[j]`.
- Add the complementary indicator constraint: `y[i,j] == -` implies `t[j] + sep[j,i] <= t[i]`. (Note: `y[i,j]` is binary; `y[i,j] == 0` can be used directly).

### Step 4 - Ensure Consistent Ordering
- Add symmetry constraints: `y[i,j] + y[j,i] == 1` for all `i < j` (if using directed variables for `i != j`).
- Add transitivity constraints: `y[i,j] + y[j,k] - 1 <= y[i,k]` for all distinct triples `(i, j, k)` to prevent cycles.

### Step 5 - Formulate Linear Objective
- Define the objective to minimize: `sum(early_penalty[i] * e[i] + late_penalty[i] * l[i])`.

### Formulation Template
```json
{
  "sets": [
    "I: set of entities to sequence"
  ],
  "parameters": [
    "earliest[i]: earliest allowed time for i",
    "latest[i]: latest allowed time for i",
    "target[i]: target (preferred) time for i",
    "sep[i,j]: required separation if i precedes j",
    "early_penalty[i]: cost per unit of early deviation",
    "late_penalty[i]: cost per unit of late deviation"
  ],
  "decision_variables": [
    "t[i]: continuous/integer, landing time of i",
    "e[i]: non-negative continuous/integer, early deviation of i",
    "l[i]: non-negative continuous/integer, late deviation of i",
    "y[i,j]: binary, 1 if i precedes j (for i != j)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} (early_penalty[i] * e[i] + late_penalty[i] * l[i])"
  },
  "constraints": [
    "time_window: earliest[i] <= t[i] <= latest[i] for all i in I",
    "deviation_def: t[i] - target[i] == l[i] - e[i] for all i in I",
    "separation_if_precedes: y[i,j] == 1 => t[i] + sep[i,j] <= t[j] for all i,j in I, i != j",
    "separation_if_follows: y[i,j] == 0 => t[j] + sep[j,i] <= t[i] for all i,j in I, i != j",
    "symmetry: y[i,j] + y[j,i] == 1 for all i,j in I, i < j",
    "transitivity: y[i,j] + y[j,k] - 1 <= y[i,k] for all distinct i,j,k in I"
  ]
}
```

### Common Pitfalls
- Using excessively large time units or bounds, which can degrade CP-SAT performance. Scale to integers where possible.
- Forgetting transitivity constraints, which can lead to infeasible or suboptimal solutions despite correct pairwise separation.
- Defining deviation variables without proper bounds, causing solver errors or unbounded behavior.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for exact optimization with runtime control and parallel search. After solving, verify the solution's feasibility and extract the complete sequence and deviations.

### Step 1 - Configure Solver Parameters
- Set `max_time_in_seconds` to control runtime.
- Set `num_search_workers` to leverage multiple CPU cores (e.g., 8).
- Set `random_seed` (e.g., 42) for reproducibility.
- Set `relative_gap_limit = 0.0` to enforce optimality proof.

### Step 2 - Solve and Check Status
- Invoke the solver and capture the status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.).
- If status is not `OPTIMAL` or `FEASIBLE`, terminate and report the failure reason.

### Step 3 - Extract and Verify Solution
- Extract values for `t[i]`, `e[i]`, `l[i]`, and `y[i,j]`.
- Perform a verification loop: check that all time window and separation constraints hold given the extracted ordering.
- Recalculate the objective value from extracted deviations to ensure consistency with the solver's reported value.

### Step 4 - Reconstruct and Report Output
- Reconstruct the total order from the binary variables `y[i,j]` using a topological sort.
- Package the solution (sequence, times, deviations, objective) into a structured format (e.g., JSON).

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (variable and constraint creation)
model.Minimize(objective_expr)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution values
    solution_t = [solver.Value(t_var[i]) for i in entities]
    # ... extract other variables
    # Verification checks
    for i in entities:
        assert earliest[i] <= solution_t[i] <= latest[i]
    # ... check separation constraints
else:
    # Handle failure
    raise Exception(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, leading to runtime errors.
- Using floating-point tolerances incorrectly when verifying integer-based CP-SAT solutions.
- Omitting solution verification, which can miss subtle infeasibilities due to numerical issues.

# Workflow 2 (MIP with Big-M Relaxation)

## Modeling stage

### Strategy Overview
This workflow formulates the problem as a Mixed-Integer Program (MIP) using a traditional Big-M approach for disjunctive separation constraints. It is designed for solvers like Gurobi, CPLEX, or HiGHS, and uses a single set of binary ordering variables with relaxed Big-M constraints, avoiding explicit transitivity.

### Step 1 - Define Variables and Bounds
- Create a continuous variable `t[i]` for each entity `i`.
- Set its lower bound to `earliest[i]` and upper bound to `latest[i]`.
- Create non-negative continuous variables `e[i]` and `l[i]` for deviations.
- Create a binary variable `y[i,j]` for each unordered pair `(i, j)` where `i < j`.

### Step 2 - Link Deviations and Calculate Big-M
- Add the constraint `t[i] - target[i] == l[i] - e[i]` for each `i`.
- Calculate a conservative Big-M value: `M = max(latest) - min(earliest) + max(sep) + buffer`.

### Step 3 - Enforce Separation via Big-M Constraints
- For each unordered pair `(i, j)` with `i < j`, add two constraints:
    - `t[j] >= t[i] + sep[i,j] - M * (1 - y[i,j])`
    - `t[i] >= t[j] + sep[j,i] - M * y[i,j]`
- This ensures the correct separation based on the value of `y[i,j]`.

### Step 4 - Enforce Mutual Exclusivity
- Add the constraint `y[i,j] + y[j,i] == 1` for all `i < j` (if using directed variables, this is inherent).

### Step 5 - Define Linear Penalty Objective
- Minimize `sum(early_penalty[i] * e[i] + late_penalty[i] * l[i])`.

### Formulation Template
```json
{
  "sets": [
    "I: set of entities to sequence"
  ],
  "parameters": [
    "earliest[i]: earliest allowed time for i",
    "latest[i]: latest allowed time for i",
    "target[i]: target (preferred) time for i",
    "sep[i,j]: required separation if i precedes j",
    "early_penalty[i]: cost per unit of early deviation",
    "late_penalty[i]: cost per unit of late deviation",
    "M: sufficiently large constant (Big-M)"
  ],
  "decision_variables": [
    "t[i]: continuous, landing time of i",
    "e[i]: non-negative continuous, early deviation of i",
    "l[i]: non-negative continuous, late deviation of i",
    "y[i,j]: binary, 1 if i precedes j (for i < j)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} (early_penalty[i] * e[i] + late_penalty[i] * l[i])"
  },
  "constraints": [
    "time_window: earliest[i] <= t[i] <= latest[i] for all i in I",
    "deviation_def: t[i] - target[i] == l[i] - e[i] for all i in I",
    "separation_bigM_1: t[j] >= t[i] + sep[i,j] - M * (1 - y[i,j]) for all i,j in I, i < j",
    "separation_bigM_2: t[i] >= t[j] + sep[j,i] - M * y[i,j] for all i,j in I, i < j"
  ]
}
```

### Common Pitfalls
- Choosing an excessively large Big-M value, which weakens the LP relaxation and slows convergence.
- Forgetting to make the separation matrix symmetric (`sep[j,i]` must be defined).
- Not providing proper variable bounds, which can lead to unbounded subproblems during solving.

## Solving stage

### Strategy Overview
Configure a MIP solver for optimality with a tight tolerance and time limit. Use presolve and heuristic settings to improve performance. After solving, verify all hard constraints and extract the sequence.

### Step 1 - Configure Solver for Proof of Optimality
- Set `MIPGap` (or equivalent) to `0.0` or a very small tolerance (e.g., `1e-6`).
- Set a `TimeLimit` to prevent excessive runtime.
- Set a deterministic `Seed` for reproducibility.
- Enable solver presolve and heuristics (usually default).

### Step 2 - Solve and Capture Termination Status
- Invoke the solver's optimize routine.
- Check the termination status (`OPTIMAL`, `FEASIBLE`, `TIME_LIMIT`, etc.).

### Step 3 - Validate Solution Feasibility
- If a solution is found, extract variable values.
- Programmatically verify all time window and separation constraints with a small numerical tolerance (e.g., `1e-6`).
- Confirm that early and late deviation variables are consistent with the time-target relationship.

### Step 4 - Analyze and Report Results
- Determine the final ordering by evaluating `y[i,j] > 0.5` for all pairs.
- Perform a topological sort to produce a total sequence.
- Report the schedule, deviations, objective value, and solver statistics.

### Code Usage
```python
# build model from formulation
import pulp  # or gurobipy, pyomo
prob = pulp.LpProblem("SequenceScheduling", pulp.LpMinimize)
# ... (variable and constraint creation)
prob += objective_expr

# solve with status / termination checks
# Example with PuLP's default solver
prob.solve(pulp.PULP_CBC_CMD(timeLimit=300, gapRel=0.0))

if pulp.LpStatus[prob.status] in ['Optimal', 'Feasible']:
    # Extract solution values
    solution_t = [pulp.value(t_var[i]) for i in entities]
    # ... extract other variables
    # Verification checks
    for i in entities:
        assert earliest[i] - 1e-6 <= solution_t[i] <= latest[i] + 1e-6
    # ... check separation constraints
else:
    # Handle failure
    raise Exception(f"Solver failed with status: {pulp.LpStatus[prob.status]}")
```

### Common Pitfalls
- Interpreting `Feasible` status as `Optimal` and reporting an unverified optimum.
- Not using a tolerance when checking constraints due to floating-point arithmetic in MIP solvers.
- Ignoring solver logs and statistics, which can provide insights for performance tuning on larger instances.
