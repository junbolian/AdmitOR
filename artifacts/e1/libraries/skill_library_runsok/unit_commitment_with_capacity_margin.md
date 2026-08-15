---
name: Unit Commitment with Capacity Margin
description: |
  Model and solve mixed-integer linear programs for unit commitment with generator counts, startup dynamics, and system-wide capacity margin requirements.

---

# Workflow 1 (Pyomo-based MILP)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to construct a structured MILP model, emphasizing clear separation of sets, parameters, and constraints. It is designed for flexibility and integration with open-source solvers like CBC.

### Step 1 - Define Sets and Parameters
- Define a set `G` for generator types and a set `T` for time periods.
- Declare parameters for costs (`fixed_cost`, `variable_cost`, `startup_cost`), operational limits (`min_output`, `max_output`, `max_startup`), and system requirements (`demand`, `capacity_margin`). Use `pyo.Param` with appropriate indexing.

### Step 2 - Declare Decision Variables
- Declare `n_op[g,t]` as `pyo.NonNegativeInteger` for the number of operational units.
- Declare `p[g,t]` as `pyo.NonNegativeReals` for the total power output per type.
- Declare `s[g,t]` as `pyo.NonNegativeInteger` for the number of startups.

### Step 3 - Formulate Operational and Output Constraints
- Link output to operational status: `p[g,t] >= min_output[g] * n_op[g,t]` and `p[g,t] <= max_output[g] * n_op[g,t]`.
- Enforce demand satisfaction: `sum(p[g,t] for g in G) >= demand[t]`.
- Enforce capacity margin: `sum(max_output[g] * n_op[g,t] for g in G) >= capacity_margin[t]`.

### Step 4 - Model Time-Coupled Dynamics
- For `t > 0`, enforce startup limit: `s[g,t] <= n_op[g,t-1]`.
- For `t > 0`, enforce state transition: `n_op[g,t] <= n_op[g,t-1] + s[g,t]`.
- For `t == 0`, enforce initial startup limit: `s[g,0] <= max_startup_initial[g]`. Use `pyo.Constraint.Skip` for boundary conditions.

### Formulation Template
```json
{
  "sets": ["G (generator types)", "T (time periods)"],
  "parameters": [
    "fixed_cost[g]", "variable_cost[g]", "startup_cost[g]",
    "min_output[g]", "max_output[g]", "max_startup_initial[g]",
    "demand[t]", "capacity_margin[t]"
  ],
  "decision_variables": [
    "n_op[g,t] (NonNegativeInteger)",
    "p[g,t] (NonNegativeReals)",
    "s[g,t] (NonNegativeInteger)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[g]*n_op[g,t] + variable_cost[g]*p[g,t] + startup_cost[g]*s[g,t] for g in G for t in T)"
  },
  "constraints": [
    "output_lower_bound: p[g,t] >= min_output[g] * n_op[g,t]",
    "output_upper_bound: p[g,t] <= max_output[g] * n_op[g,t]",
    "demand_satisfaction: sum(p[g,t] for g in G) >= demand[t]",
    "capacity_margin_req: sum(max_output[g] * n_op[g,t] for g in G) >= capacity_margin[t]",
    "startup_limit_t0: s[g,0] <= max_startup_initial[g]",
    "startup_limit: s[g,t] <= n_op[g,t-1] for t > 0",
    "state_transition: n_op[g,t] <= n_op[g,t-1] + s[g,t] for t > 0"
  ]
}
```

### Common Pitfalls
- Forgetting to skip constraints for the initial period (`t==0`) in time-coupled dynamics, leading to index errors.
- Defining `max_startup_initial` incorrectly, which should reflect the maximum number of units that can be started from a cold state.
- Using continuous variables for unit counts (`n_op`, `s`), which fails to capture the discrete nature of generator commitment.

## Solving stage

### Strategy Overview
This stage focuses on solving the Pyomo model with a MILP solver, configuring for performance, and implementing robust solution checking and validation.

### Step 1 - Select and Configure Solver
- Instantiate a solver: `solver = pyo.SolverFactory("cbc")`.
- Set key options: `solver.options["seconds"] = TIMELIMIT`, `solver.options["ratio"] = MIPGAP`, `solver.options["threads"] = NUM_THREADS`.

### Step 2 - Solve and Check Status
- Solve the model: `results = solver.solve(model, tee=VERBOSE_FLAG)`.
- Check solver status: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check termination condition: `assert results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]`.

### Step 3 - Extract and Validate Solution
- Extract objective value: `total_cost = pyo.value(model.obj)`.
- Extract variable values into dictionaries for reporting.
- Implement a post-solve verification routine that checks each constraint against the solution with a tolerance (e.g., `1e-6`) to confirm feasibility.

### Code Usage
```python
import pyomo.environ as pyo

# Build model 'model' according to the formulation template
# ...

# Solve
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False)

# Check status and termination
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    total_cost = pyo.value(model.obj)
    # Extract solution values...
    # n_op_sol = {(g,t): pyo.value(model.n_op[g,t]) for g in model.G for t in model.T}
    # p_sol = ...
    # s_sol = ...
    print(f"Solve successful. Total cost: {total_cost}")
    # Call verification function here
else:
    print("Solve failed or did not converge to a feasible solution.")
```

### Common Pitfalls
- Proceeding to extract variable values without checking `termination_condition`, which may lead to accessing undefined values from an incomplete solve.
- Setting an overly restrictive MIP gap (`ratio=0.0`) on large models without a time limit, causing excessive solve times.
- Omitting post-solve verification, which can miss subtle constraint violations due to numerical tolerances.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, modeling the problem with integer decision variables and linear constraints. It is suited for cases where a highly efficient, dedicated integer programming solver is preferred.

### Step 1 - Initialize Model and Create Variable Containers
- Create a CP-SAT model: `model = cp_model.CpModel()`.
- Create dictionaries to hold integer decision variables: `n_op = {}`, `p = {}`, `s = {}`. Variables are created via `model.NewIntVar(lb, ub, name)`.

### Step 2 - Define Variables with Appropriate Bounds
- For each `(g,t)`, define `n_op[g,t]` as an integer variable with bounds `[0, max_operational_units[g]]`.
- Define `p[g,t]` as an integer variable (or continuous via scaling) with bounds `[0, max_output[g] * max_operational_units[g]]`.
- Define `s[g,t]` as an integer variable with bounds `[0, max_startup[g,t]]`.

### Step 3 - Enforce Output and Operational Logic
- Add constraints linking output to operational count: `p[g,t] >= min_output[g] * n_op[g,t]` and `p[g,t] <= max_output[g] * n_op[g,t]`.
- Add demand constraint: `sum(p[g,t] for g in G) >= demand[t]`.
- Add capacity margin constraint: `sum(max_output[g] * n_op[g,t] for g in G) >= capacity_margin[t]`.

### Step 4 - Implement Time-Coupled Startup and State Dynamics
- For `t > 0`, add constraint: `s[g,t] <= n_op[g,t-1]`.
- For `t > 0`, add constraint: `n_op[g,t] <= n_op[g,t-1] + s[g,t]`.
- For `t == 0`, add constraint: `s[g,0] <= max_startup_initial[g]`.

### Step 5 - Define Linear Objective
- Build objective expression: `sum(fixed_cost[g]*n_op[g,t] + variable_cost[g]*p[g,t] + startup_cost[g]*s[g,t] for g in G for t in T)`.
- Set the model to minimize this expression: `model.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": ["G (generator types)", "T (time periods)"],
  "parameters": [
    "fixed_cost[g]", "variable_cost[g]", "startup_cost[g]",
    "min_output[g]", "max_output[g]", "max_operational_units[g]", "max_startup_initial[g]",
    "demand[t]", "capacity_margin[t]"
  ],
  "decision_variables": [
    "n_op[g,t] (IntVar, 0..max_operational_units[g])",
    "p[g,t] (IntVar, 0..max_output[g]*max_operational_units[g])",
    "s[g,t] (IntVar, 0..max_startup[g,t])"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[g]*n_op[g,t] + variable_cost[g]*p[g,t] + startup_cost[g]*s[g,t] for g in G for t in T)"
  },
  "constraints": [
    "output_lower_bound: p[g,t] >= min_output[g] * n_op[g,t]",
    "output_upper_bound: p[g,t] <= max_output[g] * n_op[g,t]",
    "demand_satisfaction: sum(p[g,t] for g in G) >= demand[t]",
    "capacity_margin_req: sum(max_output[g] * n_op[g,t] for g in G) >= capacity_margin[t]",
    "startup_limit_t0: s[g,0] <= max_startup_initial[g]",
    "startup_limit: s[g,t] <= n_op[g,t-1] for t > 0",
    "state_transition: n_op[g,t] <= n_op[g,t-1] + s[g,t] for t > 0"
  ]
}
```

### Common Pitfalls
- Using `model.NewIntVar` without specifying proper upper bounds, which can drastically reduce solver performance.
- Forgetting that CP-SAT requires integer coefficients; scaling fractional parameters (e.g., costs) may be necessary.
- Incorrectly ordering indices when creating variables in nested loops, leading to key errors in constraint construction.

## Solving stage

### Strategy Overview
This stage involves solving the CP-SAT model, setting time limits and optional parameters, and extracting the solution with appropriate checks.

### Step 1 - Configure and Execute Solver
- Create a solver instance: `solver = cp_model.CpSolver()`.
- Set solver parameters: `solver.parameters.max_time_in_seconds = TIMELIMIT`, `solver.parameters.num_search_workers = NUM_THREADS`.
- Execute the solve: `status = solver.Solve(model)`.

### Step 2 - Interpret Solve Status
- Check the solve status: `if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:`.
- Handle `cp_model.UNKNOWN` (often due to time limit) or `cp_model.INFEASIBLE` statuses appropriately.

### Step 3 - Extract Solution and Compute Costs
- If the status is optimal or feasible, extract variable values using `solver.Value(var)`.
- Compute the objective value from extracted values for verification, as `solver.ObjectiveValue()` may not be populated for non-optimal solves.

### Step 4 - Validate Solution
- Programmatically check all constraints against the extracted solution values within a small tolerance to ensure the solver's solution is valid.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model 'model' according to the formulation template
# ...

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4

status = solver.Solve(model)

# Interpret status
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    total_cost = solver.ObjectiveValue() if status == cp_model.OPTIMAL else None
    # Extract solution values...
    # n_op_sol = {(g,t): solver.Value(n_op[g,t]) for g in G for t in T}
    # p_sol = ...
    # s_sol = ...
    # If total_cost is None, recompute from extracted values and cost parameters
    print(f"Solve successful. Status: {'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'}.")
    # Call verification function here
elif status == cp_model.UNKNOWN:
    print("Solve status UNKNOWN, likely hit time limit.")
elif status == cp_model.INFEASIBLE:
    print("Model is infeasible.")
```

### Common Pitfalls
- Assuming `solver.ObjectiveValue()` is always available; it is only guaranteed for `OPTIMAL` status. For `FEASIBLE` status, recompute the objective from variable values.
- Not setting `max_time_in_seconds`, allowing the solver to run indefinitely on difficult instances.
- Failing to scale the model if using non-integer cost coefficients, which CP-SAT does not natively support.
