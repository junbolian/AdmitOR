---
name: Generator Commitment and Dispatch
description: |
  Model and solve multi-period generator scheduling with startup costs, capacity buffer, and per-unit output limits using integer or binary activation variables.

---

# Workflow 1 (Integer Activation with Count-Based Logic)

## Modeling stage

### Strategy Overview
This workflow models generator activation using integer variables to represent counts of active units per type and period. It is suitable for problems with multiple identical generators, reducing model size and complexity while capturing count-based constraints and startup accounting efficiently.

### Step 1 - Define Sets and Parameters
- Define sets for generator types and time periods.
- Define parameters for demand, per-unit capacity limits, cost coefficients, and buffer factor.

### Step 2 - Define Decision Variables
- Define integer variables for the number of active generators per type per period.
- Define continuous variables for total power output per type per period.
- Define integer variables for the number of startups per type per period.

### Step 3 - Formulate Core Operational Constraints
- Enforce demand satisfaction: total output must meet demand each period.
- Enforce capacity buffer: total available capacity must exceed demand by a buffer factor.
- Enforce per-unit output limits: total output must be between minimum and maximum per active generator.

### Step 4 - Formulate Activation and Startup Logic
- For the first period, link startups directly to active generators (initial activation).
- For subsequent periods, enforce activation continuity: active count cannot exceed previous active count plus startups.
- Define startups as the non-negative increase in active count, driven by cost minimization.

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
    "base_cost[g in G]",
    "power_cost[g in G]",
    "startup_cost[g in G]",
    "buffer_factor"
  ],
  "decision_variables": [
    "active[g in G, t in T] ∈ NonNegativeIntegers",
    "power[g in G, t in T] ∈ NonNegativeReals",
    "startup[g in G, t in T] ∈ NonNegativeIntegers"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(base_cost[g] * active[g,t] + power_cost[g] * power[g,t] + startup_cost[g] * startup[g,t] for g in G, t in T)"
  },
  "constraints": [
    "demand_satisfaction[t in T]: sum(power[g,t] for g in G) >= demand[t]",
    "capacity_buffer[t in T]: sum(max_output[g] * active[g,t] for g in G) >= buffer_factor * demand[t]",
    "output_lower[g in G, t in T]: power[g,t] >= min_output[g] * active[g,t]",
    "output_upper[g in G, t in T]: power[g,t] <= max_output[g] * active[g,t]",
    "initial_startup[g in G]: startup[g,0] >= active[g,0]",
    "activation_continuity[g in G, t in T, t>0]: active[g,t] <= active[g,t-1] + startup[g,t]",
    "startup_definition[g in G, t in T, t>0]: startup[g,t] >= active[g,t] - active[g,t-1]"
  ]
}
```

### Common Pitfalls
- Using binary activation variables when the problem requires tracking integer counts of generators.
- Incorrectly linearizing startup constraints, e.g., using `startup <= active_t - active_{t-1}` which fails when activation decreases.
- Missing initial state assumptions; ensure the model allows generators to be initially inactive without forcing infeasibility.

## Solving stage

### Strategy Overview
Configure the MIP solver with appropriate optimality tolerances and termination criteria. After solving, verify solution feasibility and optimality, then extract and report cost breakdowns for validation.

### Step 1 - Configure Solver and Solve
- Set solver options such as time limit and optimality gap (e.g., `mip_rel_gap`).
- Avoid invalid solver settings like negative optimality gaps.
- Solve the model and capture the termination status.

### Step 2 - Verify Solution and Extract Results
- Check solver status; if infeasible, review constraint formulation.
- Programmatically verify all constraints using solution values to catch modeling errors.
- Compute total cost and its components (fixed, variable, startup) from variable values to cross-check the solver's objective.

### Step 3 - Report and Validate
- Print the objective value and a detailed cost breakdown.
- Use a consistent output format (e.g., `RESULT:{objective_value}`) for easy parsing.
- Ensure logical consistency, e.g., startups occur only when activation increases.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... populate model using the formulation template ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 60
solver.options['mip_rel_gap'] = 1e-4
result = solver.solve(model)

# check status
if result.solver.termination_condition == pyo.TerminationCondition.optimal:
    print(f"Optimal solution found.")
    # extract and verify solution
    # ... verification code ...
    print(f"RESULT:{pyo.value(model.objective)}")
else:
    print(f"Solver terminated with status: {result.solver.termination_condition}")
    # handle infeasibility or other statuses
```

### Common Pitfalls
- Premature termination after finding a feasible solution without verifying optimality.
- Ignoring solver status codes; an infeasible status requires investigating constraints.
- Not verifying all constraints systematically, leading to acceptance of incorrect solutions.

# Workflow 2 (Binary Activation with Linearized Logic)

## Modeling stage

### Strategy Overview
This workflow models generator activation using binary variables for on/off status per type and period, with linearized constraints for startup logic. It is suitable when per-unit tracking is required or when logical constraints are more naturally expressed with binary variables.

### Step 1 - Define Sets and Parameters
- Define sets for generator types and time periods.
- Define parameters for demand, per-unit capacity limits, cost coefficients, and buffer factor.

### Step 2 - Define Decision Variables
- Define binary variables for the activation status of each generator type per period.
- Define continuous variables for power output per type per period.
- Define integer variables for the number of startups per type per period.

### Step 3 - Formulate Core Operational Constraints
- Enforce demand satisfaction: total output must meet demand each period.
- Enforce capacity buffer: total available capacity must exceed demand by a buffer factor.
- Enforce per-unit output limits using big-M or direct multiplication with binary activation.

### Step 4 - Formulate Linearized Startup and Activation Logic
- For the first period, link startups to activation (startups required for initial activation).
- For subsequent periods, linearize the product of binary variables to represent simultaneous activity across periods.
- Enforce startup limits using linearized constraints: startups ≤ increase in activation.

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
    "base_cost[g in G]",
    "power_cost[g in G]",
    "startup_cost[g in G]",
    "buffer_factor"
  ],
  "decision_variables": [
    "active[g in G, t in T] ∈ Binary",
    "power[g in G, t in T] ∈ NonNegativeReals",
    "startup[g in G, t in T] ∈ NonNegativeIntegers",
    "w[g in G, t in T, t>0] ∈ Binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(base_cost[g] * active[g,t] + power_cost[g] * power[g,t] + startup_cost[g] * startup[g,t] for g in G, t in T)"
  },
  "constraints": [
    "demand_satisfaction[t in T]: sum(power[g,t] for g in G) >= demand[t]",
    "capacity_buffer[t in T]: sum(max_output[g] * active[g,t] for g in G) >= buffer_factor * demand[t]",
    "output_lower[g in G, t in T]: power[g,t] >= min_output[g] * active[g,t]",
    "output_upper[g in G, t in T]: power[g,t] <= max_output[g] * active[g,t]",
    "initial_startup[g in G]: startup[g,0] >= active[g,0]",
    "linearization1[g in G, t in T, t>0]: w[g,t] <= active[g,t]",
    "linearization2[g in G, t in T, t>0]: w[g,t] <= active[g,t-1]",
    "linearization3[g in G, t in T, t>0]: w[g,t] >= active[g,t] + active[g,t-1] - 1",
    "startup_limit[g in G, t in T, t>0]: startup[g,t] <= active[g,t] - w[g,t]",
    "activation_continuity[g in G, t in T, t>0]: active[g,t] <= active[g,t-1] + startup[g,t]"
  ]
}
```

### Common Pitfalls
- Using integer activation variables when binary variables are more appropriate for per-unit logical constraints.
- Incorrect linearization of startup constraints leading to infeasible or overly restrictive models.
- Creating nonlinear terms by multiplying decision variables directly; always linearize such products.

## Solving stage

### Strategy Overview
Configure the solver with stable options, avoiding parameters that may cause conflicts. Solve incrementally if needed, and thoroughly verify the solution's logical consistency and constraint satisfaction.

### Step 1 - Configure Solver and Solve Incrementally
- Use solver options like `time_limit` and `mip_rel_gap`; avoid problematic settings like `threads` if they cause conflicts.
- Start with a simplified model (e.g., without startup constraints) to verify baseline feasibility, then add complexity incrementally.

### Step 2 - Verify Solution Feasibility and Logic
- After solving, manually check all constraints, especially logical ones like startup definitions and activation continuity.
- Verify that startups occur only when activation increases and that the capacity buffer is satisfied.

### Step 3 - Validate Cost Structure and Output
- Compute total cost from variable values to cross-check the solver's objective.
- Analyze output dispatch to ensure cheaper generators are prioritized within their limits.
- Report results in a structured format for validation and debugging.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... populate model using the formulation template ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 60
solver.options['mip_rel_gap'] = -1e-4  # Use a small positive value instead
result = solver.solve(model)

# check status and verify
if result.solver.termination_condition == pyo.TerminationCondition.optimal:
    print("Optimal solution found.")
    # extensive verification
    for t in model.T:
        total_power = sum(pyo.value(model.power[g,t]) for g in model.G)
        assert total_power >= pyo.value(model.demand[t]), f"Demand violation in {t}"
        # ... more verification ...
    print(f"RESULT:{pyo.value(model.objective)}")
else:
    print(f"Solver terminated: {result.solver.termination_condition}")
```

### Common Pitfalls
- Setting invalid solver options (e.g., negative optimality gap) leading to errors.
- Not verifying solution feasibility across all constraints, especially after incremental model changes.
- Accepting solver output without cross-checking cost calculations or logical consistency.
