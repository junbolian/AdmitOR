---
name: Production Planning with Fixed-Charge Costs
description: |
  Model and solve multi-period production planning with fixed activation costs and variable production costs using mixed-integer linear programming.

---

# Workflow 1 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for model definition, interfacing with open-source MILP solvers like CBC or HiGHS. It emphasizes a clean separation of sets, parameters, variables, and constraints for maintainability and solver compatibility.

### Step 1 - Define Index Sets
- Define a set `F` for production entities (e.g., factories, machines).
- Define a set `T` for discrete time periods (e.g., months, weeks).

### Step 2 - Declare Parameters
- Declare `fixed_cost[f]` for the cost incurred if entity `f` is active in a period.
- Declare `variable_cost[f]` for the per-unit production cost for entity `f`.
- Declare `min_production[f]` and `max_production[f]` for the minimum and maximum output if active.
- Declare `demand[t]` for the required production in period `t`.

### Step 3 - Create Decision Variables
- Create binary variables `run[f,t] ∈ {0,1}` to indicate if entity `f` is active in period `t`. Avoid reserved names like `activate`.
- Create continuous variables `production[f,t] ≥ 0` for the production quantity from entity `f` in period `t`.

### Step 4 - Formulate Linking Constraints
- Add constraint `production[f,t] ≥ min_production[f] * run[f,t]` to enforce minimum output if active.
- Add constraint `production[f,t] ≤ max_production[f] * run[f,t]` to enforce capacity limits and force zero production when inactive.

### Step 5 - Formulate Demand and Objective
- Add constraint `sum(production[f,t] for f in F) ≥ demand[t]` for each period `t`.
- Define objective to minimize total cost: `sum(fixed_cost[f] * run[f,t] + variable_cost[f] * production[f,t])` over all `f,t`.

### Formulation Template
```json
{
  "sets": ["F (entities)", "T (time periods)"],
  "parameters": [
    "fixed_cost[F]",
    "variable_cost[F]",
    "min_production[F]",
    "max_production[F]",
    "demand[T]"
  ],
  "decision_variables": [
    "run[F,T] ∈ {0,1}",
    "production[F,T] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{f in F, t in T} (fixed_cost[f] * run[f,t] + variable_cost[f] * production[f,t])"
  },
  "constraints": [
    "production[f,t] ≥ min_production[f] * run[f,t] ∀ f∈F, t∈T",
    "production[f,t] ≤ max_production[f] * run[f,t] ∀ f∈F, t∈T",
    "sum_{f in F} production[f,t] ≥ demand[t] ∀ t∈T"
  ]
}
```

### Common Pitfalls
- Using variable names that conflict with Pyomo reserved keywords (e.g., `activate`, `active`).
- Forgetting to attach parameters to the model object, causing scope issues in constraint rules.
- Creating redundant constraints (e.g., separate `production[f,t] ≤ max_production[f]` and `production[f,t] ≤ M * run[f,t]`).

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured open-source solver (CBC or HiGHS), with robust handling of solver status and solution validation to ensure reliable results.

### Step 1 - Instantiate Solver and Set Options
- Instantiate the solver factory (e.g., `SolverFactory("cbc")` or `SolverFactory("highs")`).
- Set key options: `seconds` for time limit, `ratio` or `mip_rel_gap` for optimality gap tolerance (use `0.0` for exact optimality), and `threads` for parallel processing if supported.

### Step 2 - Solve and Check Termination Status
- Call `solver.solve(model, tee=False)` to execute the solve.
- Check `solver.status == SolverStatus.ok` and `termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}` before extracting results.

### Step 3 - Extract and Validate Solution
- Extract the objective value using `pyo.value(model.obj)`.
- For binary variables, use a threshold (e.g., `pyo.value(model.run[f,t]) > 0.5`) to determine activation status.
- Iterate through constraints to verify satisfaction (demand, min/max production) within a numerical tolerance (e.g., `1e-6`).

### Step 4 - Output Structured Results
- Compute cost breakdowns (total fixed vs. variable) for insight.
- Output a structured summary including activation status, production quantities per period, and demand satisfaction.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (model definition steps from Modeling stage)
model = pyo.ConcreteModel()
model.F = pyo.Set(initialize=entities)
model.T = pyo.Set(initialize=periods)
# ... (add parameters, variables, objective, constraints)

# Solve
solver = pyo.SolverFactory('cbc')  # or 'highs'
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

# Check status and extract
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    total_cost = pyo.value(model.obj)
    # Extract variable values and validate
else:
    # Handle infeasible/error case
    output = {'status': 'failed', 'reason': 'infeasible_or_error', 'solver_status': str(status), 'termination_condition': str(term)}
```

### Common Pitfalls
- Accessing variable values without checking solver status and termination condition first.
- Setting conflicting solver options (e.g., `threads` with HiGHS may cause errors).
- Using `== 1` for binary variable checks instead of a tolerance-based threshold.

# Workflow 2 (OR-Tools with SCIP/CBC Backend)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to directly construct a MILP model. It is suited for environments where a Python-native, solver-agnostic API is preferred, leveraging SCIP or CBC as the backend.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")` (or "CBC").
- Store parameters in dictionaries or lists indexed by entity `i` and period `t`.

### Step 2 - Create Variables with Bounds
- Create binary variables `run[i,t] = solver.IntVar(0, 1, f"run_{i}_{t}")`.
- Create continuous variables `production[i,t] = solver.NumVar(0, max_production[i], f"prod_{i}_{t}")`, using the maximum capacity as the natural upper bound.

### Step 3 - Add Linking Constraints Directly
- Add constraint `production[i,t] >= min_production[i] * run[i,t]` using `solver.Add()`.
- Add constraint `production[i,t] <= max_production[i] * run[i,t]` using `solver.Add()`. OR-Tools handles the linearization.

### Step 4 - Add Demand and Objective
- For each period `t`, add constraint `sum(production[i,t] for i) >= demand[t]`.
- Create the objective: `objective = solver.Objective()`. Add terms using `SetCoefficient(run[i,t], fixed_cost[i])` and `SetCoefficient(production[i,t], variable_cost[i])`. Set minimization.

### Formulation Template
```json
{
  "sets": ["I (entities)", "T (time periods)"],
  "parameters": [
    "fixed_cost[I]",
    "variable_cost[I]",
    "min_production[I]",
    "max_production[I]",
    "demand[T]"
  ],
  "decision_variables": [
    "run[I,T] ∈ {0,1}",
    "production[I,T] ∈ [0, max_production[I]]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I, t in T} (fixed_cost[i] * run[i,t] + variable_cost[i] * production[i,t])"
  },
  "constraints": [
    "production[i,t] ≥ min_production[i] * run[i,t] ∀ i∈I, t∈T",
    "production[i,t] ≤ max_production[i] * run[i,t] ∀ i∈I, t∈T",
    "sum_{i in I} production[i,t] ≥ demand[t] ∀ t∈T"
  ]
}
```

### Common Pitfalls
- Not using descriptive variable names in `IntVar`/`NumVar`, complic debugging.
- Forgetting to call `objective.SetMinimization()` after setting coefficients.
- Manually implementing Big-M with large constants when `max_production[i]` provides a tight, natural bound.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' solver interface, configure performance settings, and implement verification to confirm solution feasibility and optimality.

### Step 1 - Configure Solver Performance
- Set time limit: `solver.SetTimeLimit(limit_in_milliseconds)`.
- Set number of threads: `solver.SetNumThreads(num_threads)`.
- For SCIP, set optimality gap via `solver.SetSolverSpecificParametersAsString("limits/gap=0.0")`.

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check result status: `status in (solver.OPTIMAL, solver.FEASIBLE)`.

### Step 3 - Extract and Verify Solution Values
- Extract binary variable values using `run[i,t].solution_value()`.
- Extract continuous variable values using `production[i,t].solution_value()`.
- Programmatically verify all constraints: check min/max production bounds for active entities, demand satisfaction per period, and zero production for inactive entities.

### Step 4 - Analyze and Report Results
- Calculate total fixed cost and total variable cost separately for insight.
- Output a clear production schedule and activation pattern.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (create variables, add constraints, set objective)

# Configure solver
solver.SetTimeLimit(30000)  # 30 seconds
solver.SetNumThreads(4)

# Solve
status = solver.Solve()

# Check status and extract
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    for i in entities:
        for t in periods:
            run_val = run[i,t].solution_value()
            prod_val = production[i,t].solution_value()
            # Verify constraints
            if run_val > 0.5:
                assert prod_val >= min_production[i] - 1e-6
                assert prod_val <= max_production[i] + 1e-6
            else:
                assert prod_val <= 1e-6
    # Verify demand
    for t in periods:
        total_prod = sum(production[i,t].solution_value() for i in entities)
        assert total_prod >= demand[t] - 1e-6
else:
    # Handle non-optimal/feasible status
    print(f'Solver finished with status: {status}')
```

### Common Pitfalls
- Assuming `solver.OPTIMAL` is the only successful status; `solver.FEASIBLE` is also acceptable for a valid solution.
- Not using a tolerance when checking constraint satisfaction due to floating-point arithmetic.
- Overlooking the need to verify that production is zero for inactive entities.
