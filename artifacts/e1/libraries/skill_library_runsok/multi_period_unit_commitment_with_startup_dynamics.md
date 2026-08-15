---
name: Multi-Period Unit Commitment with Startup Dynamics
description: |
  Model and solve multi-period power generation planning with generator startup logic, capacity bounds, and reserve requirements using MILP, with workflows for Pyomo and OR-Tools.
---

# Workflow 1 (Pyomo-based MILP with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling to structure a multi-period unit commitment problem as a Mixed-Integer Linear Program (MILP). It cleanly separates sets, parameters, and variables, enabling solver-agnostic formulation and leveraging open-source solvers like CBC or HiGHS.

### Step 1 - Define Sets and Parameters
- Define a set `G` for generator types and a set `T` for time periods.
- Define parameters for demand, generator capacities, costs, availability limits, and initial conditions.

### Step 2 - Design Decision Variables
- Create integer variable `n[g,t]` for the number of generators of type `g` online in period `t`.
- Create continuous variable `p[g,t]` for the total power output (MW) from type `g` in period `t`.
- Create integer variable `s[g,t]` for the number of generators of type `g` started up in period `t`.

### Step 3 - Formulate Objective Function
- Minimize total cost, summing base operating cost, per-unit output cost, and startup cost across all periods and generator types.

### Step 4 - Implement Core Constraints
- **Demand Satisfaction**: For each period `t`, total output must meet demand.
- **Generator Capacity Bounds**: For each `g,t`, output must be between `min_output[g] * n[g,t]` and `max_output[g] * n[g,t]`.
- **Availability Limits**: For each `g,t`, `n[g,t]` cannot exceed `max_available[g]`.
- **Reserve Requirement**: For each `t`, total maximum capacity must meet or exceed a reserve target (e.g., `demand[t] * reserve_factor`).
- **Startup Dynamics**: For `t=0`, `n[g,0] <= s[g,0] + initial_online[g]`. For `t>0`, `n[g,t] <= n[g,t-1] + s[g,t]`.

### Formulation Template
```json
{
  "sets": ["G (generator types)", "T (time periods)"],
  "parameters": [
    "demand[T]",
    "min_output[G]", "max_output[G]",
    "base_cost[G]", "per_mw_cost[G]", "startup_cost[G]",
    "max_available[G]",
    "initial_online[G]",
    "reserve_factor"
  ],
  "decision_variables": [
    "n[G,T] (NonNegativeIntegers)",
    "p[G,T] (NonNegativeReals)",
    "s[G,T] (NonNegativeIntegers)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{g in G, t in T} ( base_cost[g] * n[g,t] + per_mw_cost[g] * p[g,t] + startup_cost[g] * s[g,t] )"
  },
  "constraints": [
    "demand_satisfaction[t]: sum_{g in G} p[g,t] >= demand[t] for all t in T",
    "min_output_bound[g,t]: p[g,t] >= min_output[g] * n[g,t] for all g in G, t in T",
    "max_output_bound[g,t]: p[g,t] <= max_output[g] * n[g,t] for all g in G, t in T",
    "availability_limit[g,t]: n[g,t] <= max_available[g] for all g in G, t in T",
    "reserve_requirement[t]: sum_{g in G} max_output[g] * n[g,t] >= demand[t] * reserve_factor for all t in T",
    "startup_initial[g]: n[g,0] <= s[g,0] + initial_online[g] for all g in G",
    "startup_dynamics[g,t>0]: n[g,t] <= n[g,t-1] + s[g,t] for all g in G, t in T, t>0"
  ]
}
```

### Common Pitfalls
- Using a single ranged constraint for capacity bounds (`min_output * n <= p <= max_output * n`), which some solvers may not support. Use two separate inequalities.
- Forgetting to handle the initial period (`t=0`) separately in the startup dynamics, leading to incorrect linking of generator counts.
- Misinterpreting the reserve requirement as a function of actual output `p[g,t]` instead of maximum potential capacity `max_output[g] * n[g,t]`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source MILP solver (e.g., CBC, HiGHS) via `SolverFactory`. Configure solver options for performance, verify solution status rigorously, and extract results for validation and reporting.

### Step 1 - Configure and Run Solver
- Instantiate the solver via `SolverFactory("solver_name")` (e.g., `"cbc"` or `"highs"`).
- Set key options: time limit (`seconds`), optimality gap (`ratio`), and number of threads (`threads`).
- Call `solver.solve(model, tee=False)` to execute.

### Step 2 - Verify Solution Status
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `.feasible`.
- If status is not ok or termination is not acceptable, analyze infeasibility or other issues.

### Step 3 - Extract and Validate Solution
- Extract variable values using `pyo.value(model.n[g,t])`.
- Programmatically verify all constraints are satisfied within tolerance.
- Recalculate the total cost from extracted values to confirm objective value.

### Step 4 - Report Results
- Print a period-by-period summary showing generator counts, outputs, startups, total power, and reserve margin.
- Output the total cost and solver statistics.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model built using the formulation above)

# 1. Configure and run solver
solver = pyo.SolverFactory("cbc")  # or "highs"
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

# 2. Verify solution status
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    # 3. Extract and validate
    total_cost = pyo.value(model.obj)
    # ... extract other variable values
    # ... run validation checks
    # 4. Report results
    print(f"RESULT:{total_cost}")
    # ... print detailed summary
else:
    # Handle failure
    print(f"RESULT_JSON:{{'status':'{status}', 'termination':'{term}', 'message':'Solver failed'}}")
```

### Common Pitfalls
- Not checking both `solver.status` and `solver.termination_condition`, leading to misinterpretation of suboptimal or infeasible results.
- Setting conflicting solver options (e.g., `threads` when the solver is already globally initialized) which may cause errors.
- Assuming variable values exist without checking solution status first, causing `ValueError`.

# Workflow 2 (OR-Tools MILP with SCIP Backend)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools (`pywraplp`) to construct a multi-period unit commitment MILP directly via its solver API. It employs the SCIP solver backend, defines variables and constraints procedurally, and is suitable for environments where a direct solver interface is preferred over an abstract modeling layer.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Store input data (demand, costs, capacities) in dictionaries or lists indexed by generator type and period.

### Step 2 - Create Variables with Explicit Bounds
- For each `g,t`, create integer variable `n[g,t]` with bounds `[0, max_available[g]]`.
- Create continuous variable `p[g,t]` with bounds `[0, solver.infinity()]`.
- Create integer variable `s[g,t]` with bounds `[0, max_available[g]]`.

### Step 3 - Build Objective Function
- Create a linear expression summing all cost components.
- Set the objective to minimize this expression using `solver.Minimize()`.

### Step 4 - Add Constraints via Solver Methods
- **Demand Satisfaction**: For each `t`, add `solver.Add(sum(p[g,t] for g in G) >= demand[t])`.
- **Capacity Bounds**: For each `g,t`, add `p[g,t] >= min_output[g] * n[g,t]` and `p[g,t] <= max_output[g] * n[g,t]`.
- **Reserve Requirement**: For each `t`, add `solver.Add(sum(max_output[g] * n[g,t] for g in G) >= demand[t] * reserve_factor)`.
- **Startup Dynamics**: For `t=0`, add `n[g,0] <= s[g,0] + initial_online[g]`. For `t>0`, add `n[g,t] <= n[g,t-1] + s[g,t]`.

### Formulation Template
```json
{
  "sets": ["G (generator types)", "T (time periods)"],
  "parameters": [
    "demand[T]",
    "min_output[G]", "max_output[G]",
    "base_cost[G]", "per_mw_cost[G]", "startup_cost[G]",
    "max_available[G]",
    "initial_online[G]",
    "reserve_factor"
  ],
  "decision_variables": [
    "n[G,T] (IntVar, 0..max_available[G])",
    "p[G,T] (NumVar, 0..inf)",
    "s[G,T] (IntVar, 0..max_available[G])"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{g in G, t in T} ( base_cost[g] * n[g,t] + per_mw_cost[g] * p[g,t] + startup_cost[g] * s[g,t] )"
  },
  "constraints": [
    "demand_satisfaction[t]: sum_{g in G} p[g,t] >= demand[t]",
    "min_output_bound[g,t]: p[g,t] >= min_output[g] * n[g,t]",
    "max_output_bound[g,t]: p[g,t] <= max_output[g] * n[g,t]",
    "reserve_requirement[t]: sum_{g in G} max_output[g] * n[g,t] >= demand[t] * reserve_factor",
    "startup_initial[g]: n[g,0] <= s[g,0] + initial_online[g]",
    "startup_dynamics[g,t>0]: n[g,t] <= n[g,t-1] + s[g,t]"
  ]
}
```

### Common Pitfalls
- Forgetting to set upper bounds on integer variables (`n`, `s`), which can lead to unbounded or poorly performing models.
- Incorrectly ordering constraint indices when building sums over sets, leading to mismatched dimensions.
- Using `solver.infinity()` for variable bounds without considering that very large bounds can negatively affect solver numerical stability.

## Solving stage

### Strategy Overview
Solve the OR-Tools model using the SCIP backend. Set solver parameters for time limit and parallelism, solve, and then extract solution values directly from the variable objects. Perform post-solution validation and reporting.

### Step 1 - Set Solver Parameters and Solve
- Set a time limit in milliseconds: `solver.SetTimeLimit(30000)`.
- Set number of threads: `solver.SetNumThreads(4)`.
- Call `solver.Solve()` to execute the optimization.

### Step 2 - Check Solver Result
- Check the result status: `result_status = solver.Solve()`.
- Interpret status: `result_status == pywraplp.Solver.OPTIMAL` or `FEASIBLE` indicates success.

### Step 3 - Extract Solution Values
- For each variable, retrieve its value using `.solution_value()` (e.g., `n[g,t].solution_value()`).
- Store values in structured data for validation and reporting.

### Step 4 - Validate and Report
- Programmatically verify that all constraints are satisfied using the extracted values.
- Compute derived metrics (total power, reserve margin) and compare against requirements.
- Print a formatted summary and the total cost.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# ... (model built using the formulation above)

# 1. Set parameters and solve
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)
result_status = solver.Solve()

# 2. Check solver result
if result_status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    # 3. Extract solution values
    total_cost = solver.Objective().Value()
    solution_n = {(g,t): n[g,t].solution_value() for g in G for t in T}
    solution_p = {(g,t): p[g,t].solution_value() for g in G for t in T}
    solution_s = {(g,t): s[g,t].solution_value() for g in G for t in T}
    # 4. Validate and report
    # ... run validation checks
    print(f"RESULT:{total_cost}")
    # ... print detailed summary
else:
    # Handle failure
    print(f"RESULT_JSON:{{'status':'{result_status}', 'message':'Solver did not find a feasible solution'}}")
```

### Common Pitfalls
- Assuming `solver.Solve()` returns a boolean; it returns an enum status that must be compared to `OPTIMAL` or `FEASIBLE`.
- Not using `.solution_value()` method and instead trying to access variable values directly, which are not populated.
- Omitting validation after solving, which can miss subtle constraint violations due to solver tolerances.
