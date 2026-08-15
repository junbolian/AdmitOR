---
name: MultiPeriodProductionPlanningWithSetupCosts
description: |
  Model and solve multi-period production planning problems with setup costs, inventory, and backlog using mixed-integer linear programming.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a clean, declarative MILP formulation. It leverages Pyomo's `Set`, `Param`, and `Var` components for structured data handling and is designed for solvers like HiGHS or CBC.

### Step 1 - Define Sets and Parameters
- Declare a set `T` for planning periods (e.g., `range(1, num_periods+1)`).
- Create parameter dictionaries for `demand`, `fixed_cost`, `variable_cost`, `holding_cost`, and `backlog_cost`, all indexed by `T`.
- Define a large constant `M` (e.g., sum of all demands) for big-M constraints.

### Step 2 - Create Decision Variables
- Define binary variable `y[t]` for production setup decisions (`pyo.Var(domain=pyo.Binary)`).
- Define non-negative continuous variables `x[t]` for production quantity, `I[t]` for inventory, and `B[t]` for backlog (`pyo.Var(domain=pyo.NonNegativeReals)`).

### Step 3 - Formulate Demand Balance with Backlog
- For each period `t`, enforce flow conservation: `I[t-1] + x[t] + B[t-1] == demand[t] + I[t] + B[t]`.
- Handle the initial period (`t=1`) by substituting `I[0] = 0` and `B[0] = 0`.
- Optionally, enforce final boundary conditions `I[T] = 0` and `B[T] = 0` as separate constraints.

### Step 4 - Link Production to Setup
- Add big-M constraints: `x[t] <= M * y[t]` for all `t` in `T`. This ensures production only occurs when the setup is active.

### Step 5 - Define Cost Objective
- Minimize the sum of all costs: `sum(fixed_cost[t]*y[t] + variable_cost[t]*x[t] + holding_cost[t]*I[t] + backlog_cost[t]*B[t] for t in T)`.

### Formulation Template
```json
{
  "sets": ["T (planning periods)"],
  "parameters": [
    "demand[T]",
    "fixed_cost[T]",
    "variable_cost[T]",
    "holding_cost[T]",
    "backlog_cost[T]",
    "M (big-M constant)"
  ],
  "decision_variables": [
    "y[T] ∈ {0,1} (setup)",
    "x[T] ≥ 0 (production)",
    "I[T] ≥ 0 (inventory)",
    "B[T] ≥ 0 (backlog)"
  ],
  "objective": {
    "sense": "min",
    "expression": "Σ_t (fixed_cost[t]*y[t] + variable_cost[t]*x[t] + holding_cost[t]*I[t] + backlog_cost[t]*B[t])"
  },
  "constraints": [
    "I[t-1] + x[t] + B[t-1] == demand[t] + I[t] + B[t], ∀t ∈ T (with I[0]=B[0]=0)",
    "x[t] ≤ M * y[t], ∀t ∈ T",
    "I[T] == 0, B[T] == 0 (optional boundary)"
  ]
}
```

### Common Pitfalls
- Incorrectly modeling backlog flow (e.g., using `B[t-1]` on the wrong side of the balance equation).
- Setting `M` too small, which can cut off feasible production quantities.
- Forgetting to enforce non-negativity on inventory and backlog variables, which is implicit in their domain but must be specified.
- Hard-coding parameter values inside constraint rules, reducing model flexibility.

## Solving stage

### Strategy Overview
This stage focuses on solving the Pyomo model with a MILP solver (HiGHS or CBC), performing rigorous solution status checks, and extracting a detailed cost breakdown for validation and analysis.

### Step 1 - Instantiate Solver and Configure
- Create a solver object: `solver = pyo.SolverFactory('highs')` or `solver = pyo.SolverFactory('cbc')`.
- Set solver options if needed (e.g., `solver.options['time_limit'] = 30`).

### Step 2 - Solve and Check Status
- Execute `results = solver.solve(model, tee=False)`.
- Check the solver status: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `assert results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]`.

### Step 3 - Extract and Validate Solution
- Access variable values: `model.y[t].value`, `model.x[t].value`, etc.
- Compute a detailed cost breakdown by component (fixed, variable, holding, backlog) using Python loops and the solved values.
- Perform a sanity check: verify that the demand balance constraint holds numerically for each period (allowing for small tolerances).

### Step 4 - Report Results
- Print or return a structured summary including production schedule, inventory/backlog levels, and the cost breakdown.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (model construction using steps above)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    # Extract solution
    production_plan = {t: model.x[t].value for t in model.T}
    # ... extract other variables
    # Calculate cost breakdown
    total_fixed = sum(model.fixed_cost[t]() * model.y[t].value for t in model.T)
    # ... other cost components
else:
    raise Exception(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming a `feasible` status means `optimal`; always check the termination condition explicitly.
- Not handling numerical precision artifacts (e.g., `-1e-10` in backlog variables); round small values to zero for reporting.
- Forgetting to check both solver status and termination condition, which can mask infeasibility or solver errors.
- Using `model.display()` or `model.pprint()` on large models, which can produce excessive output.

# Workflow 2 (OR-Tools with SCIP/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT (for MILP) or the MPSolver interface, which is well-suited for direct, imperative model construction. It emphasizes efficient variable creation and constraint addition in a loop, ideal for integration into larger applications.

### Step 1 - Initialize Solver and Define Parameters
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')` or `'CBC_MIXED_INTEGER_PROGRAMMING'`.
- Store time-dependent parameters (demand, costs) in Python lists or dictionaries indexed by period.

### Step 2 - Create Variables in Batch
- In a loop over all periods, create binary setup variables: `y[t] = solver.BoolVar(f'y_{t}')`.
- Create continuous production, inventory, and backlog variables with appropriate bounds (0 to a large upper bound like total demand): `x[t] = solver.NumVar(0, M, f'x_{t}')`.

### Step 3 - Add Demand Balance Constraints
- For the first period, add: `solver.Add(0 + x[1] + 0 == demand[1] + I[1] + B[1])`.
- For subsequent periods `t`, add: `solver.Add(I[t-1] + x[t] + B[t-1] == demand[t] + I[t] + B[t])`.
- Optionally, add final boundary constraints: `solver.Add(I[T] == 0)` and `solver.Add(B[T] == 0)`.

### Step 4 - Add Production Linking Constraints
- In the same loop, add big-M constraints: `solver.Add(x[t] <= M * y[t])`.

### Step 5 - Set Linear Cost Objective
- Build the objective expression by summing cost terms across all periods: `solver.Minimize(sum(fixed_cost[t]*y[t] + ...))`.

### Formulation Template
```json
{
  "sets": ["T (planning periods)"],
  "parameters": [
    "demand[T]",
    "fixed_cost[T]",
    "variable_cost[T]",
    "holding_cost[T]",
    "backlog_cost[T]",
    "M (big-M constant)"
  ],
  "decision_variables": [
    "y[T] ∈ {0,1} (setup, OR-Tools BoolVar)",
    "x[T] ∈ [0, M] (production, NumVar)",
    "I[T] ≥ 0 (inventory, NumVar)",
    "B[T] ≥ 0 (backlog, NumVar)"
  ],
  "objective": {
    "sense": "min",
    "expression": "Σ_t (fixed_cost[t]*y[t] + variable_cost[t]*x[t] + holding_cost[t]*I[t] + backlog_cost[t]*B[t])"
  },
  "constraints": [
    "I[t-1] + x[t] + B[t-1] == demand[t] + I[t] + B[t], ∀t ∈ T (with I[0]=B[0]=0)",
    "x[t] ≤ M * y[t], ∀t ∈ T",
    "I[T] == 0, B[T] == 0 (optional boundary)"
  ]
}
```

### Common Pitfalls
- Using `solver.IntVar` instead of `solver.BoolVar` for binary variables, which is less efficient.
- Not setting an upper bound on continuous variables, which some OR-Tools solvers require.
- Incorrectly ordering indices in the demand balance constraint, leading to infeasible or nonsensical flows.
- Building the objective inside the variable creation loop, which can cause performance overhead or syntax errors.

## Solving stage

### Strategy Overview
This stage involves executing the OR-Tools model, setting practical solver limits (time, threads), and implementing robust post-solution analysis to extract decisions and compute verification metrics.

### Step 1 - Configure Solver Settings
- Set a time limit: `solver.SetTimeLimit(60000)` (time in milliseconds).
- Set the number of threads: `solver.SetNumThreads(4)` for parallel solving (if supported by the backend).

### Step 2 - Solve and Interpret Result Status
- Call `status = solver.Solve()`.
- Map the returned status to outcomes: `status == pywraplp.Solver.OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`.
- For non-optimal statuses, decide whether to accept the best bound or report failure.

### Step 3 - Extract Solution Values
- If the status is `OPTIMAL` or `FEASIBLE`, retrieve variable values using `.solution_value()`: `y_val = y[t].solution_value()`.
- Store results in structured containers (e.g., lists or dictionaries) for easy access.

### Step 4 - Compute and Validate Costs
- Calculate the total cost and individual cost components using the retrieved solution values and the original parameter dictionaries.
- Validate key constraints by recomputing the demand balance for each period and checking for any significant deviations beyond a small tolerance (e.g., 1e-5).

### Step 5 - Output Structured Results
- Format the solution as a dictionary or JSON object containing the production schedule, inventory/backlog trajectory, cost breakdown, and solver statistics.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (variable and constraint creation as per modeling stage)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    # Extract solution values
    solution = {}
    for t in T:
        solution[t] = {
            'y': y[t].solution_value(),
            'x': x[t].solution_value(),
            'I': I[t].solution_value(),
            'B': B[t].solution_value()
        }
    # Calculate cost breakdown
    total_cost = solver.Objective().Value()
    # Detailed calculation
    fixed_cost_total = sum(fixed_cost[t] * y[t].solution_value() for t in T)
    # ... other components
else:
    print(f"No feasible solution found. Solver status: {status}")
```

### Common Pitfalls
- Confusing `solver.OPTIMAL` with `solver.FEASIBLE`; the latter does not guarantee optimality.
- Not setting a time limit for large instances, potentially causing the solver to run indefinitely.
- Accessing `.solution_value()` on variables before checking the solve status, which may raise an error.
- Neglecting to account for numerical precision when checking constraint satisfaction (e.g., using exact equality).
