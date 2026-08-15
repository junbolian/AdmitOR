---
name: Unit Commitment with Reserve Capacity
description: |
  Model and solve generator scheduling problems with discrete activation, continuous dispatch, and reserve capacity requirements using mixed-integer linear programming.
---

# Workflow 1 (Integer-Count Formulation)

## Modeling stage

### Strategy Overview
This workflow models the problem using integer variables to count active units per type, which is efficient when multiple identical generators exist. It linearizes per-unit output limits and defines startups via difference constraints.

### Step 1 - Define Core Variables
- Define integer variables `n[g,t]` for the number of active generators of type `g` in period `t`.
- Define continuous variables `P_total[g,t]` for the total power output from all generators of type `g` in period `t`.
- Define integer variables `s[g,t]` for the number of startups of type `g` in period `t`.

### Step 2 - Formulate Output Limits
- Enforce per-generator minimum and maximum output via `min_output[g] * n[g,t] <= P_total[g,t] <= max_output[g] * n[g,t]`.
- This linearly bounds total output based on the count of active units.

### Step 3 - Enforce Demand and Reserve
- Satisfy demand: `sum(P_total[g,t] for g in G) >= demand[t]`.
- Ensure reserve capacity: `sum(max_output[g] * n[g,t] for g in G) >= buffer_factor * demand[t]`.

### Step 4 - Model Activation and Startup Dynamics
- For `t > 0`, link active counts: `n[g,t] <= n[g,t-1] + s[g,t]`.
- For `t = 0`, define initial state: `n[g,0] <= initial_active[g] + s[g,0]`.
- Define startups as the positive increase: `s[g,t] >= n[g,t] - n[g,t-1]` and `s[g,t] >= 0`.
- Apply upper bounds: `s[g,t] <= n[g,t]` and per-period startup limits `s[g,t] <= startup_limit[g,t]`.

### Step 5 - Define Objective
- Minimize total cost: sum of `fixed_cost[g] * n[g,t]`, `variable_cost[g] * P_total[g,t]`, and `startup_cost[g] * s[g,t]` across all `g` and `t`.

### Formulation Template
```json
{
  "sets": [
    "G: generator types",
    "T: time periods"
  ],
  "parameters": [
    "demand[T]",
    "buffer_factor",
    "min_output[G]",
    "max_output[G]",
    "fixed_cost[G]",
    "variable_cost[G]",
    "startup_cost[G]",
    "startup_limit[G,T]",
    "initial_active[G]"
  ],
  "decision_variables": [
    "n[G,T] integer >= 0",
    "P_total[G,T] continuous >= 0",
    "s[G,T] integer >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[g] * n[g,t] + variable_cost[g] * P_total[g,t] + startup_cost[g] * s[g,t] for g in G, t in T)"
  },
  "constraints": [
    "output_min: P_total[g,t] >= min_output[g] * n[g,t] for g in G, t in T",
    "output_max: P_total[g,t] <= max_output[g] * n[g,t] for g in G, t in T",
    "demand: sum(P_total[g,t] for g in G) >= demand[t] for t in T",
    "reserve: sum(max_output[g] * n[g,t] for g in G) >= buffer_factor * demand[t] for t in T",
    "continuity: n[g,t] <= n[g,t-1] + s[g,t] for g in G, t in T, t>0",
    "initial_activation: n[g,0] <= initial_active[g] + s[g,0] for g in G",
    "startup_def: s[g,t] >= n[g,t] - n[g,t-1] for g in G, t in T, t>0",
    "startup_def0: s[g,0] >= n[g,0] - initial_active[g] for g in G",
    "startup_ub: s[g,t] <= startup_limit[g,t] for g in G, t in T"
  ]
}
```

### Common Pitfalls
- Forgetting to handle the initial period (`t=0`) separately in activation and startup constraints.
- Using `s[g,t] <= n[g,t] - n[g,t-1]` without considering shutdowns (negative differences), which creates infeasibility.
- Omitting the reserve capacity constraint or incorrectly formulating it without the `max_output` multiplier.

## Solving stage

### Strategy Overview
Solve the MIP model using a dedicated solver like SCIP via an optimization library. Focus on configuration, solution validation, and cost analysis.

### Step 1 - Configure Solver
- Select a MIP-capable solver (e.g., SCIP, HiGHS, CBC).
- Set termination parameters: `time_limit`, `mip_rel_gap`.
- Configure numerical tolerances if needed (e.g., integrality tolerance).

### Step 2 - Solve and Check Status
- Invoke the solver and capture the termination status.
- Proceed only if status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` with diagnostic steps.

### Step 3 - Validate Solution Feasibility
- Programmatically check all constraints using the solution values.
- Verify demand satisfaction, reserve capacity, output bounds, and startup logic.
- Calculate the objective value from raw solution data to cross-check the solver's reported cost.

### Step 4 - Extract and Report Results
- For each generator type and period, report `n[g,t]`, `P_total[g,t]`, `s[g,t]`, and average output per generator.
- Provide a cost breakdown (fixed, variable, startup) and total cost.

### Code Usage
```python
# build model from formulation
import ortools.linear_solver.pywraplp as ort
solver = ort.Solver.CreateSolver('SCIP')
# ... build variables and constraints using the formulation template ...

# solve with status / termination checks
solver.SetTimeLimit(30000)
status = solver.Solve()
if status == ort.Solver.OPTIMAL or status == ort.Solver.FEASIBLE:
    # Extract solution
    for g in G:
        for t in T:
            n_val = n[g,t].solution_value()
            p_val = P_total[g,t].solution_value()
            s_val = s[g,t].solution_value()
    # Validate constraints
    # ... validation code ...
else:
    print(f'Solver failed with status: {status}')
```

### Common Pitfalls
- Not setting a time limit, risking excessive runtime for large instances.
- Accepting the solver's objective value without independent verification.
- Misinterpreting floating-point solution values for integer variables (e.g., printing `-0.0`).

# Workflow 2 (Binary-Activation Formulation)

## Modeling stage

### Strategy Overview
This workflow uses binary activation variables per generator type, suitable for modeling individual unit decisions or when per-type counts are small. It employs linearization for startup logic.

### Step 1 - Define Discrete Activation Variables
- Define binary variables `a[g,t]` indicating if any generator of type `g` is active in period `t`.
- Define continuous variables `p[g,t]` for the total power output of type `g` in period `t`.
- Define integer variables `s[g,t]` for the number of startups of type `g` in period `t`.

### Step 2 - Formulate Output Limits with Binary Activation
- Enforce `min_output[g] * a[g,t] <= p[g,t] <= max_output[g] * a[g,t]`.
- This ensures output is zero when inactive and within bounds when active.

### Step 3 - Enforce Demand and Reserve
- Satisfy demand: `sum(p[g,t] for g in G) >= demand[t]`.
- Ensure reserve capacity: `sum(max_output[g] * a[g,t] for g in G) >= buffer_factor * demand[t]`.

### Step 4 - Linearize Startup Logic
- For `t > 0`, enforce activation continuity: `a[g,t] <= a[g,t-1] + s[g,t]`.
- For `t = 0`, set `a[g,0] <= initial_active_binary[g] + s[g,0]`.
- To linearize `s[g,t] <= max(0, a[g,t] - a[g,t-1])`, introduce auxiliary binary variable `w[g,t]` representing `a[g,t] AND a[g,t-1]` with constraints:
    - `w[g,t] <= a[g,t]`
    - `w[g,t] <= a[g,t-1]`
    - `w[g,t] >= a[g,t] + a[g,t-1] - 1`
- Then enforce `s[g,t] <= a[g,t] - w[g,t]` and `s[g,t] >= 0`.

### Step 5 - Define Objective
- Minimize total cost: sum of `fixed_cost[g] * a[g,t]`, `variable_cost[g] * p[g,t]`, and `startup_cost[g] * s[g,t]` across all `g` and `t`.

### Formulation Template
```json
{
  "sets": [
    "G: generator types",
    "T: time periods"
  ],
  "parameters": [
    "demand[T]",
    "buffer_factor",
    "min_output[G]",
    "max_output[G]",
    "fixed_cost[G]",
    "variable_cost[g]",
    "startup_cost[G]",
    "startup_limit[G,T]",
    "initial_active_binary[G]"
  ],
  "decision_variables": [
    "a[G,T] binary",
    "p[G,T] continuous >= 0",
    "s[G,T] integer >= 0",
    "w[G,T] binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[g] * a[g,t] + variable_cost[g] * p[g,t] + startup_cost[g] * s[g,t] for g in G, t in T)"
  },
  "constraints": [
    "output_min: p[g,t] >= min_output[g] * a[g,t] for g in G, t in T",
    "output_max: p[g,t] <= max_output[g] * a[g,t] for g in G, t in T",
    "demand: sum(p[g,t] for g in G) >= demand[t] for t in T",
    "reserve: sum(max_output[g] * a[g,t] for g in G) >= buffer_factor * demand[t] for t in T",
    "continuity: a[g,t] <= a[g,t-1] + s[g,t] for g in G, t in T, t>0",
    "initial_activation: a[g,0] <= initial_active_binary[g] + s[g,0] for g in G",
    "startup_linear1: s[g,t] <= a[g,t] - w[g,t] for g in G, t in T, t>0",
    "and_def1: w[g,t] <= a[g,t] for g in G, t in T, t>0",
    "and_def2: w[g,t] <= a[g,t-1] for g in G, t in T, t>0",
    "and_def3: w[g,t] >= a[g,t] + a[g,t-1] - 1 for g in G, t in T, t>0",
    "startup_ub: s[g,t] <= startup_limit[g,t] for g in G, t in T"
  ]
}
```

### Common Pitfalls
- Incorrectly linearizing the startup constraint without the auxiliary `w` variable, leading to `s[g,t] <= a[g,t] - a[g,t-1]` which is invalid when `a[g,t-1] > a[g,t]`.
- Forgetting to enforce `s[g,t] >= 0`, allowing negative startup counts.
- Mis-specifying the initial active state, causing infeasibility or suboptimal solutions.

## Solving stage

### Strategy Overview
Solve using a high-level modeling language (e.g., Pyomo) with a robust MILP solver (e.g., HiGHS). Emphasize model debugging and systematic validation.

### Step 1 - Build Model with Modeling Library
- Use Pyomo (or similar) to abstract model construction.
- Define sets, parameters, variables, and constraints as per the formulation.

### Step 2 - Configure and Solve
- Select solver backend (e.g., `'highs'`).
- Set options: `time_limit`, `mip_rel_gap`. Avoid conflicting options like `threads` if not supported.
- Solve and capture results object.

### Step 3 - Debug and Validate
- If infeasible, systematically deactivate constraint groups to isolate the conflict.
- For feasible solutions, compute constraint violations manually to verify satisfaction within tolerances.
- Check startup logic by verifying `s[g,t]` equals `max(0, a[g,t] - a[g,t-1])`.

### Step 4 - Analyze and Report
- Display activation status, output, and startups per type and period.
- Report solver status, termination condition, and solve time for reproducibility.
- Provide a clear total cost and its components.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.G = pyo.Set(initialize=G)
model.T = pyo.Set(initialize=T)
# ... define parameters, variables, and constraints using the formulation template ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 60
solver.options['mip_rel_gap'] = 0.001
results = solver.solve(model, tee=True)
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    # Extract solution
    for g in model.G:
        for t in model.T:
            a_val = pyo.value(model.a[g,t])
            p_val = pyo.value(model.p[g,t])
    # Validate and report
else:
    print(f'Solution not optimal. Status: {results.solver.termination_condition}')
```

### Common Pitfalls
- Using solver-specific options that conflict with the modeling layer or global environment.
- Not checking the termination condition, assuming `optimal` when solver may return `feasible` or `maxTimeLimit`.
- Failing to validate the linearization of startup constraints, leading to incorrect operational interpretation.
