---
name: SchedulingWithDeviationsAndOrdering
description: |
  Model and solve scheduling problems with time windows, pairwise separation constraints, and linear penalties for deviations from target times, using binary ordering variables to enforce precedence.
---

# Workflow 1 (CP-SAT with Indicator Constraints)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, leveraging its native support for indicator constraints (`OnlyEnforceIf`) to model separation conditions without big-M constants, which can improve propagation and performance.

### Step 1 - Define Core Variables
- Create a continuous variable `t[i]` for each entity `i`, bounded between its `earliest[i]` and `latest[i]`.
- Create non-negative continuous variables `e[i]` and `l[i]` for early and late deviations, with upper bounds `target[i] - earliest[i]` and `latest[i] - target[i]` respectively.
- Create a binary variable `y[i,j]` for each unordered pair `(i, j)` where `i < j`, representing that `i` precedes `j` if `1`.

### Step 2 - Link Times and Deviations
- For each entity `i`, add the linear constraint `t[i] - target[i] == l[i] - e[i]`. This ensures deviations correctly reflect the difference between scheduled and target time.

### Step 3 - Enforce Separation with Indicators
- For each unordered pair `(i, j)` with `i < j`, add two indicator constraints:
  - `t[i] + sep[i,j] <= t[j]`. Enforce this constraint only if `y[i,j] == 1`.
  - `t[j] + sep[j,i] <= t[i]`. Enforce this constraint only if `y[i,j] == 0`.
- This directly encodes the logical relationship without a big-M constant.

### Step 4 - Ensure Consistent Ordering
- For each unordered pair `(i, j)` with `i < j`, add the constraint `y[i,j] + y[j,i] == 1`. This defines `y[j,i]` as the complement.
- Optionally, add transitivity constraints for all triples `(i, j, k)` to strengthen the formulation: `y[i,j] + y[j,k] - 1 <= y[i,k]`.

### Step 5 - Formulate Linear Penalty Objective
- Set the objective to minimize `sum(early_penalty[i] * e[i] + late_penalty[i] * l[i] for all i)`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of entities to schedule.",
    "P: Set of unordered pairs (i,j) where i < j."
  ],
  "parameters": [
    "earliest[i], latest[i]: Time window bounds for entity i.",
    "target[i]: Preferred target time for entity i.",
    "sep[i,j]: Required separation time if i precedes j (asymmetric).",
    "early_penalty[i], late_penalty[i]: Linear penalty coefficients for deviations."
  ],
  "decision_variables": [
    "t[i]: Continuous, scheduled time for entity i.",
    "e[i], l[i]: Continuous, non-negative early and late deviation for entity i.",
    "y[i,j]: Binary, 1 if i precedes j (for i<j)."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(early_penalty[i] * e[i] + late_penalty[i] * l[i] for i in I)"
  },
  "constraints": [
    "time_window: earliest[i] <= t[i] <= latest[i] for i in I",
    "deviation_link: t[i] - target[i] == l[i] - e[i] for i in I",
    "separation_if_precedes: t[i] + sep[i,j] <= t[j] enforced if y[i,j]==1 for (i,j) in P",
    "separation_if_follows: t[j] + sep[j,i] <= t[i] enforced if y[i,j]==0 for (i,j) in P",
    "symmetry: y[i,j] + y[j,i] == 1 for (i,j) in P",
    "transitivity: y[i,j] + y[j,k] - 1 <= y[i,k] for distinct i,j,k in I (optional)"
  ]
}
```

### Common Pitfalls
- Forgetting to define the complement variable `y[j,i]` or the symmetry constraint, leading to an incomplete precedence model.
- Using indicator constraints with a CP-SAT backend that does not support them (ensure solver is CP-SAT).
- Not setting appropriate bounds on deviation variables, which can lead to unbounded or poorly scaled models.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for efficient search, solve the model, and implement robust verification to ensure solution feasibility and objective correctness.

### Step 1 - Configure Solver Parameters
- Set a time limit (`max_time_in_seconds`).
- Enable parallel search (`num_search_workers`).
- Set a fixed random seed for reproducibility.
- Set the optimality gap to zero (`relative_gap_limit = 0.0`) if a proven optimum is required.

### Step 2 - Solve and Check Status
- Invoke the solver and capture the status code (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).
- If status is not `OPTIMAL` or `FEASIBLE`, exit with a clear error message and diagnostic information.

### Step 3 - Extract and Validate Solution
- Extract values for all `t[i]`, `e[i]`, `l[i]`, and `y[i,j]` variables.
- Run a verification script that checks:
  1. All `t[i]` are within `[earliest[i], latest[i]]`.
  2. For each pair `(i, j)`, the separation constraint holds based on the extracted ordering (`y[i,j]`).
  3. The calculated penalty `sum(penalty * deviation)` matches the solver's reported objective value.

### Step 4 - Report Results
- Output the objective value, schedule (entity, time, deviations), and the final precedence ordering derived from `y[i,j]` values.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()

# ... (Create variables and constraints as per modeling steps)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution and verify
    pass
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Attempting to access variable values before checking the solver status, leading to runtime errors.
- Not verifying the solution independently, which can miss issues due to solver tolerances or modeling errors.
- Setting an overly restrictive time limit or gap tolerance for large instances, causing premature termination.

# Workflow 2 (MIP with Big-M in Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for model abstraction and a traditional MIP solver (e.g., Gurobi, HiGHS) with a big-M formulation for separation constraints, offering flexibility and compatibility with a wide range of solvers.

### Step 1 - Define Model Sets and Parameters
- Declare a Pyomo `Set` for entities `I` and a `Set` for ordered pairs `IxI`.
- Define parameters for time windows, target times, separation matrix, and penalty coefficients as Pyomo `Param` objects or dictionaries.

### Step 2 - Create Decision Variables
- Create continuous variables `model.t[i]` within bounds `[earliest[i], latest[i]]`.
- Create non-negative continuous variables `model.e[i]` and `model.l[i]` for deviations.
- Create binary variables `model.y[i,j]` for all ordered pairs `(i,j), i!=j`, where `y[i,j]=1` indicates `i` precedes `j`.

### Step 3 - Link Deviations and Enforce Time Windows
- For each `i`, add constraint `model.t[i] - target[i] == model.l[i] - model.e[i]`.
- Time window bounds can be set directly as variable bounds or as explicit constraints.

### Step 4 - Enforce Separation via Big-M Constraints
- Compute a sufficiently large `M`, e.g., `max(latest) - min(earliest) + max(separation)`.
- For each ordered pair `(i,j), i!=j`, add two constraints:
  - `model.t[i] + sep[i,j] <= model.t[j] + M * (1 - model.y[i,j])`
  - `model.t[j] + sep[j,i] <= model.t[i] + M * model.y[i,j]`
- This ensures separation is active only in the direction indicated by the binary variable.

### Step 5 - Enforce Mutual Exclusivity of Ordering
- For each unordered pair `(i,j), i<j`, add constraint `model.y[i,j] + model.y[j,i] == 1`.

### Step 6 - Define Linear Objective
- Minimize `sum(early_penalty[i] * model.e[i] + late_penalty[i] * model.l[i] for i in I)`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of entities.",
    "IxI: Set of all ordered pairs (i,j) where i != j."
  ],
  "parameters": [
    "earliest[i], latest[i]: Time window bounds.",
    "target[i]: Target time.",
    "sep[i,j]: Separation if i precedes j.",
    "early_penalty[i], late_penalty[i]: Penalty coefficients.",
    "M: Large constant for big-M constraints."
  ],
  "decision_variables": [
    "t[i]: Continuous, scheduled time.",
    "e[i], l[i]: Continuous, non-negative deviations.",
    "y[i,j]: Binary, 1 if i precedes j (for i!=j)."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(early_penalty[i] * e[i] + late_penalty[i] * l[i] for i in I)"
  },
  "constraints": [
    "time_window: earliest[i] <= t[i] <= latest[i] for i in I",
    "deviation_link: t[i] - target[i] == l[i] - e[i] for i in I",
    "separation_forward: t[i] + sep[i,j] <= t[j] + M*(1 - y[i,j]) for (i,j) in IxI, i!=j",
    "separation_backward: t[j] + sep[j,i] <= t[i] + M*y[i,j] for (i,j) in IxI, i!=j",
    "ordering_mutex: y[i,j] + y[j,i] == 1 for i,j in I, i<j"
  ]
}
```

### Common Pitfalls
- Choosing an overly large `M` value, which weakens the LP relaxation and slows solving.
- Forgetting to skip the `i=j` case in pair-wise constraints, creating meaningless self-referential constraints.
- Not properly handling asymmetric separation parameters, leading to incorrect constraint logic.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model, configure a MIP solver with appropriate settings, solve, and perform post-solution validation and analysis.

### Step 1 - Instantiate Model and Select Solver
- Create a `ConcreteModel()` and populate it using the modeling steps.
- Use `SolverFactory('solver_name')` to create a solver interface (e.g., 'gurobi', 'highs').

### Step 2 - Configure Solver Options
- Set a time limit (`TimeLimit`).
- Set optimality tolerance (`MIPGap`).
- Set the number of threads (`Threads`).
- Set a random seed (`Seed`) for reproducibility.

### Step 3 - Solve and Inspect Termination
- Invoke `solver.solve(model, tee=True/False)`.
- Check `results.solver.status` and `results.solver.termination_condition`.
- If status is not `ok` or termination is not `optimal`/`feasible`, analyze logs for infeasibility or other issues.

### Step 4 - Extract and Verify Solution
- If solve was successful, load solution into the model using `model.solutions.load_from(results)`.
- Extract variable values via `pyo.value(model.t[i])` etc.
- Perform verification checks similar to Workflow 1, ensuring all constraints are satisfied given the extracted `y[i,j]` values.

### Step 5 - Analyze and Report
- Compute the objective value from extracted deviations for cross-validation.
- Output the schedule, ordering, and objective value in a structured format.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=entity_indices)
# ... (Add variables, constraints, objective as per modeling steps)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = -1e-6
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model, tee=False)
status = results.solver.status
termination = results.solver.termination_condition

if status == pyo.SolverStatus.ok and termination == pyo.TerminationCondition.optimal:
    # Extract and verify solution
    pass
else:
    print(f"Solver terminated with status: {status}, condition: {termination}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or infeasible results.
- Attempting to access variable values before loading the solution into the model object.
- Using default solver options that are inappropriate for the problem size, such as no time limit or loose optimality gap.
