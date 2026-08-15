---
name: Multi-Period Production Planning with Setup Costs
description: |
  Model and solve multi-period production planning problems with setup costs, inventory, and backlog using mixed-integer linear programming (MILP) with different solver backends.

---

# Workflow 1 (OR-Tools with SCIP)

## Modeling stage

### Strategy Overview
Formulate the problem as a MILP using the OR-Tools API, defining binary setup variables linked to production via big-M constraints, and tracking inventory and backlog flow across periods.

### Step 1 - Define Sets and Parameters
- Define a set `T` representing the planning periods (e.g., `range(1, num_periods+1)`).
- Create dictionaries for time-dependent parameters: `demand[t]`, `fixed_cost[t]`, `variable_cost[t]`, `holding_cost[t]`, `backlog_cost[t]`.
- Define a sufficiently large constant `M` (e.g., sum of all demands) for big-M constraints.

### Step 2 - Create Decision Variables
- Create binary variable `y[t]` for production setup decision in each period `t`.
- Create continuous variable `x[t]` for production quantity in period `t`, with lower bound 0 and upper bound `M`.
- Create continuous variable `I[t]` for ending inventory in period `t`, with lower bound 0 and upper bound `M`.
- Create continuous variable `B[t]` for ending backlog in period `t`, with lower bound 0 and upper bound `M`.

### Step 3 - Formulate Inventory and Backlog Flow
- For each period `t`, add the demand balance constraint: `I[t-1] + x[t] + B[t-1] == demand[t] + I[t] + B[t]`.
- Handle boundary conditions: explicitly set `I[0] = 0`, `B[0] = 0`, `I[T] = 0`, and `B[T] = 0`.

### Step 4 - Link Production to Setup
- For each period `t`, add the linking constraint: `x[t] <= M * y[t]`. This ensures production is zero if setup is not active.

### Step 5 - Define Objective Function
- Formulate the objective to minimize total cost: `sum( fixed_cost[t]*y[t] + variable_cost[t]*x[t] + holding_cost[t]*I[t] + backlog_cost[t]*B[t] for t in T )`.

### Formulation Template
```json
{
  "sets": ["T (planning periods)"],
  "parameters": [
    "demand[t]",
    "fixed_cost[t]",
    "variable_cost[t]",
    "holding_cost[t]",
    "backlog_cost[t]",
    "M (big-M constant)"
  ],
  "decision_variables": [
    "y[t] ∈ {0, 1}",
    "x[t] ≥ 0",
    "I[t] ≥ 0",
    "B[t] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "Σ_t ( fixed_cost[t]*y[t] + variable_cost[t]*x[t] + holding_cost[t]*I[t] + backlog_cost[t]*B[t] )"
  },
  "constraints": [
    "I[t-1] + x[t] + B[t-1] == demand[t] + I[t] + B[t], ∀ t ∈ T",
    "x[t] ≤ M * y[t], ∀ t ∈ T",
    "I[0] = 0, B[0] = 0, I[T] = 0, B[T] = 0"
  ]
}
```

### Common Pitfalls
- Setting `M` too small, which can cut off feasible production quantities. Use a safe upper bound like total demand.
- Forgetting to enforce zero inventory/backlog at the horizon end, which can lead to suboptimal solutions.
- Incorrectly indexing the initial (`t-1`) and final (`T`) periods in the demand balance loop.

## Solving stage

### Strategy Overview
Build the model using the OR-Tools `pywraplp` interface, solve with the SCIP solver, and implement robust checks for solution status and numerical accuracy.

### Step 1 - Initialize Solver and Model
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Optionally set performance parameters: `solver.SetTimeLimit(time_limit_in_ms)` and `solver.SetNumThreads(num_threads)`.

### Step 2 - Create Variables and Add Constraints
- Create variable dictionaries by iterating over periods, using `solver.BoolVar()` for `y[t]` and `solver.NumVar(0, M, ...)` for continuous variables.
- Add constraints using `solver.Add()` within loops, implementing the formulation from the modeling stage.

### Step 3 - Set Objective and Solve
- Initialize the objective: `objective = solver.Objective()`.
- Use `SetCoefficient` to add each variable-cost term in a loop over all periods and variables.
- Call `objective.SetMinimization()` and then `solver.Solve()`.

### Step 4 - Check Solver Status and Retrieve Solution
- Check the result status: `if solver.ResultStatus() == pywraplp.Solver.OPTIMAL:` or `FEASIBLE`.
- Retrieve the objective value: `total_cost = objective.Value()`.
- Extract variable values into dictionaries (e.g., `y_val[t] = y[t].solution_value()`).

### Step 5 - Validate Solution and Handle Numerical Precision
- Recompute the demand balance for each period using the extracted values to verify constraint satisfaction within a tolerance (e.g., `1e-6`).
- Treat near-zero values (e.g., `-0.0`) as zero when interpreting results.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
# ... variable and constraint creation ...
# ... objective construction ...

# solve with status / termination checks
status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    print(f"Objective value: {solver.Objective().Value()}")
    # Retrieve and process variable values
else:
    print("No optimal or feasible solution found.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing valid solutions.
- Interpreting solver floating-point output literally; always use a tolerance for comparisons.
- Omitting a time limit for large instances, which can cause excessive runtimes.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's `ConcreteModel`, leveraging its declarative syntax to define sets, parameters, variables, constraints, and objective, targeting open-source solvers like HiGHS or CBC.

### Step 1 - Initialize Model and Sets
- Create a Pyomo `ConcreteModel()`.
- Define a `Set` for planning periods, e.g., `model.T = pyo.Set(initialize=range(1, num_periods+1))`.
- Define a `Set` for periods including time zero for boundary conditions if needed.

### Step 2 - Define Parameters
- Use `pyo.Param(model.T)` to store time-series data: `model.demand`, `model.fixed_cost`, `model.variable_cost`, `model.holding_cost`, `model.backlog_cost`.
- Define `model.M` as a scalar parameter for the big-M value.

### Step 3 - Declare Decision Variables
- Define binary variable `model.y` over `model.T` using `pyo.Var(model.T, within=pyo.Binary)`.
- Define non-negative continuous variables `model.x`, `model.I`, `model.B` over `model.T` using `within=pyo.NonNegativeReals`.

### Step 4 - Construct Constraints
- Define the demand balance constraint as a `pyo.Constraint(model.T)` using a rule function that accesses `model.I[t-1]`, `model.B[t-1]`, etc.
- Define the production linking constraint: `model.x[t] <= model.M * model.y[t]` for each `t`.
- Enforce boundary conditions via fixed variable values: `model.I[0].fix(0)`, `model.B[0].fix(0)`, and add constraints `model.I[T] == 0`, `model.B[T] == 0`.

### Step 5 - Formulate the Objective
- Define the objective using `pyo.Objective(expr=sum( model.fixed_cost[t]*model.y[t] + ... for t in model.T ), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["T (planning periods)"],
  "parameters": [
    "demand[t]",
    "fixed_cost[t]",
    "variable_cost[t]",
    "holding_cost[t]",
    "backlog_cost[t]",
    "M (big-M constant)"
  ],
  "decision_variables": [
    "y[t] ∈ {0, 1}",
    "x[t] ≥ 0",
    "I[t] ≥ 0",
    "B[t] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "Σ_t ( fixed_cost[t]*y[t] + variable_cost[t]*x[t] + holding_cost[t]*I[t] + backlog_cost[t]*B[t] )"
  },
  "constraints": [
    "I[t-1] + x[t] + B[t-1] == demand[t] + I[t] + B[t], ∀ t ∈ T",
    "x[t] ≤ M * y[t], ∀ t ∈ T",
    "I[0] = 0, B[0] = 0, I[T] = 0, B[T] = 0"
  ]
}
```

### Common Pitfalls
- Incorrectly handling index `t-1` in Pyomo constraint rules; ensure the index exists in the set or handle the first period separately.
- Forgetting to `.fix()` initial condition variables, leading to an over-constrained model.
- Using mutable parameters incorrectly; for one-off solves, simple initialization is sufficient.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with the HiGHS or CBC solver, configure solve options appropriately, and implement comprehensive checks on solver status and termination conditions.

### Step 1 - Select and Configure Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")` or `solver = pyo.SolverFactory("cbc")`.
- For CBC, set options like `solver.options['seconds'] = time_limit` and `solver.options['ratio'] = mip_gap`.
- For HiGHS, use default settings or minimal configuration (e.g., `solver.options['time_limit'] = time_limit`).

### Step 2 - Solve and Capture Results
- Execute the solve: `results = solver.solve(model, tee=False)`.
- Capture the results object for status checking.

### Step 3 - Verify Solver Status and Termination
- Check if the solver ran successfully: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `if results.solver.termination_condition == pyo.TerminationCondition.optimal:` or `.feasible`.
- If not optimal/feasible, inspect `results.solver.message` for diagnostics.

### Step 4 - Extract and Validate Solution
- Retrieve the objective value: `total_cost = pyo.value(model.obj)`.
- Extract variable values into dictionaries (e.g., `y_val = {t: pyo.value(model.y[t]) for t in model.T}`).
- Optionally, recompute the objective from extracted values to validate against the solver's reported value.

### Step 5 - Analyze and Present Results
- Calculate a cost breakdown (fixed, variable, holding, backlog) from the solution.
- Print or log a period-by-period table of decisions (`y[t]`), production (`x[t]`), inventory (`I[t]`), and backlog (`B[t]`).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    print(f"Objective value: {pyo.value(model.obj)}")
    # Process solution
else:
    print("Solve failed or did not find optimal/feasible solution.")
```

### Common Pitfalls
- Assuming `SolverStatus.ok` alone indicates optimality; must also check `termination_condition`.
- Using incompatible solver options (e.g., setting `threads` for HiGHS without proper support).
- Not handling the case where a variable value is `None` due to solver failure.
