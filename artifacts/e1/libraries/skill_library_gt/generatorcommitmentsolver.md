---
name: GeneratorCommitmentSolver
description: |
  Model and solve generator commitment problems with integer activation counts, linearized startup constraints, and capacity reserve requirements using mixed-integer linear programming.
---

# Workflow 1 (MILP with Integer Activation Variables)

## Modeling stage

### Strategy Overview
This workflow models generator commitment using integer variables to represent the count of active generators per type, separating total power output from per-generator logic. It employs linear constraints for startup accounting and capacity buffer requirements, suitable for solvers like SCIP or CPLEX.

### Step 1 - Define Core Sets and Parameters
- Define sets for generator types `G` and time periods `T`.
- Define parameters for demand `demand[t]`, per-type min/max output `min_output[g]`, `max_output[g]`, maximum active generators per type `max_active[g]`, and maximum initial startups `max_startup_p0[g]`.
- Define cost parameters: base cost `base_cost[g]`, power cost `power_cost[g]`, and startup cost `startup_cost[g]`.
- Define a reserve factor `buffer_factor`.

### Step 2 - Define Decision Variables
- Define integer variable `n[g,t]` for the number of active generators of type `g` in period `t`.
- Define continuous variable `P_total[g,t]` for the total power output from type `g` in period `t`.
- Define integer variable `s[g,t]` for the number of generators started up of type `g` in period `t`.

### Step 3 - Formulate Power Output Constraints
- Enforce minimum output: `P_total[g,t] >= min_output[g] * n[g,t]`.
- Enforce maximum output: `P_total[g,t] <= max_output[g] * n[g,t]`.
- Satisfy demand: `sum_{g in G} P_total[g,t] >= demand[t]`.

### Step 4 - Formulate Activation and Startup Logic
- Enforce activation continuity: `n[g,t] <= n[g,t-1] + s[g,t]` for `t >= 1`.
- Enforce startup definition: `s[g,t] >= n[g,t] - n[g,t-1]` for `t >= 1`.
- Bound startups: `s[g,t] <= n[g,t]`.
- Handle initial period: `s[g,0] <= max_startup_p0[g]`.

### Step 5 - Enforce Capacity and Type Limits
- Enforce capacity buffer: `sum_{g in G} max_output[g] * n[g,t] >= buffer_factor * demand[t]`.
- Enforce type capacity limit: `n[g,t] <= max_active[g]`.

### Formulation Template
```json
{
  "sets": [
    "G: generator types",
    "T: time periods"
  ],
  "parameters": [
    "demand[t in T]",
    "min_output[g in G]",
    "max_output[g in G]",
    "max_active[g in G]",
    "max_startup_p0[g in G]",
    "base_cost[g in G]",
    "power_cost[g in G]",
    "startup_cost[g in G]",
    "buffer_factor"
  ],
  "decision_variables": [
    "n[g in G, t in T] integer >= 0",
    "P_total[g in G, t in T] continuous >= 0",
    "s[g in G, t in T] integer >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{g in G, t in T} (base_cost[g] * n[g,t] + power_cost[g] * P_total[g,t] + startup_cost[g] * s[g,t])"
  },
  "constraints": [
    "min_output_constraint: P_total[g,t] >= min_output[g] * n[g,t]",
    "max_output_constraint: P_total[g,t] <= max_output[g] * n[g,t]",
    "demand_satisfaction: sum_{g in G} P_total[g,t] >= demand[t]",
    "activation_continuity: n[g,t] <= n[g,t-1] + s[g,t] for t >= 1",
    "startup_definition: s[g,t] >= n[g,t] - n[g,t-1] for t >= 1",
    "startup_bound: s[g,t] <= n[g,t]",
    "initial_startup_limit: s[g,0] <= max_startup_p0[g]",
    "capacity_buffer: sum_{g in G} max_output[g] * n[g,t] >= buffer_factor * demand[t]",
    "type_capacity_limit: n[g,t] <= max_active[g]"
  ]
}
```

### Common Pitfalls
- Omitting the initial startup limit (`max_startup_p0`) can lead to infeasible or unrealistic solutions for the first period.
- Using binary variables for `n[g,t]` incorrectly restricts the model to a single generator per type, violating the problem's multi-unit nature.
- Forgetting to enforce the capacity buffer constraint can result in insufficient reserve capacity for demand fluctuations.

## Solving stage

### Strategy Overview
This solving stage uses a MILP solver (e.g., SCIP) via an interface like OR-Tools. It focuses on proper solver configuration, rigorous solution status checking, and post-solution validation against the problem's logical constraints.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance suitable for mixed-integer linear problems (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set a reasonable time limit (e.g., `solver.SetTimeLimit(30000)`).
- Configure thread usage according to solver documentation (e.g., `solver.SetNumThreads(4)` if supported).

### Step 2 - Build Model from Formulation
- Instantiate all sets, parameters, and decision variables as defined in the formulation template.
- Add the objective function using the provided cost coefficients.
- Add all constraints, ensuring correct indexing for time periods (e.g., handling `t=0` separately).

### Step 3 - Solve and Check Status
- Call `solver.Solve()`.
- Check the solver status: `OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`.
- If status is not `OPTIMAL` or `FEASIBLE`, diagnose using solver methods (e.g., `solver.VerifySolution()`).

### Step 4 - Extract and Validate Solution
- Extract variable values (`n[g,t].solution_value()`, `P_total[g,t].solution_value()`, `s[g,t].solution_value()`).
- Programmatically verify key logical constraints: demand satisfaction, startup definition (`s[g,t] >= n[g,t] - n[g,t-1]`), and activation continuity.
- Compute the objective value from extracted values and cross-check with the solver's reported objective.

### Step 5 - Analyze and Report
- Summarize activation patterns and cost breakdown by generator type and period.
- Report any warnings (e.g., unused capacity, high startup counts).

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
# ... (variable and constraint creation as per formulation)

# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL or status == solver.FEASIBLE:
    # Extract solution
    for g in G:
        for t in T:
            n_val = n[g,t].solution_value()
            p_val = P_total[g,t].solution_value()
            s_val = s[g,t].solution_value()
    # Validate logical constraints
    for g in G:
        for t in T:
            if t > 0:
                assert s_val >= n_val - n_prev, f"Startup definition violated for {g},{t}"
            n_prev = n_val
else:
    print(f"Solver terminated with status: {status}")
    # Investigate infeasibility or other issues
```

### Common Pitfalls
- Trusting a non-`OPTIMAL` status without verifying solution feasibility against the problem's semantics.
- Ignoring solver option conflicts (e.g., setting `threads` on a solver that uses a global scheduler).
- Failing to validate the logical consistency of startups and activations, especially in the initial period.

# Workflow 2 (MILP with Linearized Binary Activation)

## Modeling stage

### Strategy Overview
This workflow models generator commitment using binary activation variables per generator unit, linearizing startup events with auxiliary variables. It is suited for problems where individual generator identity matters or for solvers requiring binary variables, using a "big-M" linearization for startup logic.

### Step 1 - Define Sets and Parameters
- Define sets for generator units `I` (grouped by type `G`), time periods `T`.
- Define parameters for demand `demand[t]`, per-unit min/max output `P_min[i]`, `P_max[i]`, and startup cost `startup_cost[i]`.
- Define a large constant `M` (e.g., `M = max(P_max[i])`).

### Step 2 - Define Binary Decision Variables
- Define binary variable `a[i,t]` indicating if generator `i` is active in period `t`.
- Define continuous variable `p[i,t]` for power output of generator `i` in period `t`.
- Define binary variable `s[i,t]` indicating if generator `i` is started up in period `t`.

### Step 3 - Formulate Output and Demand Constraints
- Enforce output limits: `p[i,t] >= P_min[i] * a[i,t]` and `p[i,t] <= P_max[i] * a[i,t]`.
- Satisfy demand: `sum_{i in I} p[i,t] >= demand[t]`.

### Step 4 - Linearize Startup Logic
- Enforce startup detection: `s[i,t] >= a[i,t] - a[i,t-1]` for `t >= 1`.
- Bound startup variable: `s[i,t] <= a[i,t]`.
- Optionally, use big-M to linearize: `s[i,t] <= 1 - a[i,t-1]` and `s[i,t] <= a[i,t]`.

### Step 5 - Enforce System-Wide Constraints
- Enforce capacity buffer: `sum_{i in I} P_max[i] * a[i,t] >= buffer_factor * demand[t]`.
- Enforce type capacity limit: `sum_{i in I_g} a[i,t] <= max_active[g]`.

### Formulation Template
```json
{
  "sets": [
    "I: generator units",
    "G: generator types (partition of I)",
    "T: time periods"
  ],
  "parameters": [
    "demand[t in T]",
    "P_min[i in I]",
    "P_max[i in I]",
    "max_active[g in G]",
    "startup_cost[i in I]",
    "operational_cost[i in I]",
    "buffer_factor",
    "M: large constant"
  ],
  "decision_variables": [
    "a[i in I, t in T] binary",
    "p[i in I, t in T] continuous >= 0",
    "s[i in I, t in T] binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I, t in T} (operational_cost[i] * p[i,t] + startup_cost[i] * s[i,t])"
  },
  "constraints": [
    "min_output: p[i,t] >= P_min[i] * a[i,t]",
    "max_output: p[i,t] <= P_max[i] * a[i,t]",
    "demand_satisfaction: sum_{i in I} p[i,t] >= demand[t]",
    "startup_definition: s[i,t] >= a[i,t] - a[i,t-1] for t >= 1",
    "startup_bound: s[i,t] <= a[i,t]",
    "linearization_1: s[i,t] <= 1 - a[i,t-1] (optional)",
    "capacity_buffer: sum_{i in I} P_max[i] * a[i,t] >= buffer_factor * demand[t]",
    "type_capacity_limit: sum_{i in I_g} a[i,t] <= max_active[g]"
  ]
}
```

### Common Pitfalls
- Setting `M` too small, which can cut off feasible solutions, or too large, which can cause numerical instability.
- Ambiguously handling the initial state (`a[i,-1]`); always parameterize initial activation status.
- Over-constraining startup logic with unnecessary auxiliary variables or nonlinear terms.

## Solving stage

### Strategy Overview
This solving stage uses a MILP solver via an interface like PuLP or a direct solver API. It emphasizes careful handling of binary variables, managing numerical tolerances, and implementing post-solution analysis to verify unit-level constraints.

### Step 1 - Choose Solver and Set Tolerances
- Select a solver supporting binary MILP (e.g., CBC, Gurobi).
- Set appropriate integrality and feasibility tolerances (e.g., `mipgap=0.01`).

### Step 2 - Build Model with Linearized Constraints
- Instantiate the model with binary and continuous variables.
- Add the linearized startup constraints, ensuring correct handling of the initial period (e.g., using parameter `initial_a[i]`).
- Add the capacity buffer and type limit constraints.

### Step 3 - Solve and Handle Status
- Invoke the solver.
- Check termination status: optimal, feasible, infeasible, or unbounded.
- If infeasible, use solver features (e.g., IIS computation) to identify conflicting constraints.

### Step 4 - Extract and Verify Unit-Level Solution
- Extract binary activation and startup values.
- Verify that for each unit and period, `s[i,t]` is 1 only if `a[i,t]` increased from the previous period.
- Check that total power output meets demand within tolerances.

### Step 5 - Report and Sensitivity Analysis
- Report total cost, number of startups, and capacity utilization.
- Optionally, perform sensitivity analysis on key parameters (e.g., demand, buffer factor).

### Code Usage
```python
# build model from formulation
import pulp
model = pulp.LpProblem("GeneratorCommitment", pulp.LpMinimize)
# ... (define variables and constraints as per formulation)

# solve with status / termination checks
solver = pulp.PULP_CBC_CMD(timeLimit=30, gapRel=0.01)
model.solve(solver)

status = pulp.LpStatus[model.status]
if status in ['Optimal', 'Feasible']:
    # Extract solution
    for i in I:
        for t in T:
            a_val = a[i,t].varValue
            s_val = s[i,t].varValue
    # Validate startup logic
    for i in I:
        for t in T:
            if t > 0:
                a_prev = a[i,t-1].varValue
                assert s_val >= a_val - a_prev - 1e-5, f"Startup logic violated for {i},{t}"
else:
    print(f"Model solve failed with status: {status}")
    # Compute IIS if supported
```

### Common Pitfalls
- Assuming a zero initial state without parameterization, forcing unnecessary startups and increasing cost.
- Accepting a solver's feasible status without verifying that startup variables correctly reflect activation changes.
- Neglecting to check for numerical issues when using large `M` values in linearization.
