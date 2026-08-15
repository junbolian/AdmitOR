---
name: MultiPeriodProductionPlanningWithSetups
description: |
  Model and solve multi-period production planning problems with setup costs, inventory holding, and resource constraints using cumulative demand data and big-M activation.
---

# Workflow 1 (Pyomo-based MILP with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling to formulate a Mixed Integer Linear Program (MILP) with clear separation of data and model. It is designed for integration with open-source solvers like HiGHS or CBC, focusing on structured parameter handling and explicit constraint definitions.

### Step 1 - Define Sets and Parameters
- Define index sets for `products` and `periods`.
- Load or compute parameters: `cumulative_demand[product, period]`, `production_cost[product, period]`, `setup_cost[product, period]`, `holding_cost[product, period]`, `resource_consumption[product]`, `resource_capacity[period]`, `max_production_limit[product, period]`.
- Precompute `period_demand[product, period]` as the difference between consecutive cumulative demands, handling the first period separately.

### Step 2 - Declare Decision Variables
- Declare `production_quantity[product, period]` as a non-negative continuous variable.
- Declare `inventory_level[product, period]` as a non-negative continuous variable.
- Declare `setup_indicator[product, period]` as a binary variable.

### Step 3 - Formulate Inventory Balance Constraints
- For each product and period, enforce `inventory_level[p, t] == inventory_level[p, t-1] + production_quantity[p, t] - period_demand[p, t]` for `t > 0`.
- For the first period (`t == 0`), enforce `inventory_level[p, 0] == production_quantity[p, 0] - period_demand[p, 0]`.
- Optionally, enforce zero terminal inventory: `inventory_level[p, final_period] == 0`.

### Step 4 - Implement Setup Activation and Capacity Constraints
- Link production to setup using a big-M constraint: `production_quantity[p, t] <= max_production_limit[p, t] * setup_indicator[p, t]`.
- Enforce shared resource capacity per period: `sum(resource_consumption[p] * production_quantity[p, t] for p in products) <= resource_capacity[t]`.

### Step 5 - Define the Objective Function
- Minimize total cost: `sum(production_cost[p, t] * production_quantity[p, t] + setup_cost[p, t] * setup_indicator[p, t] + holding_cost[p, t] * inventory_level[p, t] for p in products, t in periods)`.

### Formulation Template
```json
{
  "sets": ["products", "periods"],
  "parameters": {
    "cumulative_demand": ["product", "period"],
    "production_cost": ["product", "period"],
    "setup_cost": ["product", "period"],
    "holding_cost": ["product", "period"],
    "resource_consumption": ["product"],
    "resource_capacity": ["period"],
    "max_production_limit": ["product", "period"]
  },
  "decision_variables": {
    "production_quantity": ["product", "period", "continuous", "nonnegative"],
    "inventory_level": ["product", "period", "continuous", "nonnegative"],
    "setup_indicator": ["product", "period", "binary"]
  },
  "objective": {
    "sense": "min",
    "expression": "sum(production_cost * production_quantity + setup_cost * setup_indicator + holding_cost * inventory_level)"
  },
  "constraints": [
    "inventory_balance",
    "setup_activation_bigM",
    "resource_capacity",
    "terminal_inventory_zero"
  ]
}
```

### Common Pitfalls
- Incorrectly computing `period_demand` from `cumulative_demand` without handling the initial period.
- Setting the big-M coefficient (`max_production_limit`) too small, making the model infeasible, or too large, weakening the LP relaxation.
- Forgetting to enforce non-negativity on inventory variables, leading to invalid solutions.
- Using negative values for solver tolerances (e.g., `mip_rel_gap`), causing parameter errors.

## Solving stage

### Strategy Overview
This stage focuses on solving the Pyomo model using an open-source MILP solver (e.g., HiGHS, CBC), configuring solver options for performance, and implementing robust solution extraction and verification.

### Step 1 - Instantiate Solver and Set Options
- Create a solver instance (e.g., `SolverFactory('appsi_highs')` or `'cbc'`).
- Set practical limits: `time_limit=30`, `threads=4`.
- Set optimality tolerance: `mip_rel_gap=0.0` or a small positive value (e.g., `1e-4`). Avoid negative values.

### Step 2 - Solve and Check Status
- Call `solver.solve(model, tee=False)` (use `tee=True` for debugging).
- Check solver status: `results.solver.status` should be `SolverStatus.ok`.
- Check termination condition: `results.solver.termination_condition` should be `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract and Post-Process Solution
- Extract variable values using `pyo.value(variable)`.
- For binary `setup_indicator` variables, round values (e.g., `1 if value > 0.5 else 0`) to handle numerical precision.
- Compute the objective value from extracted solution for validation against the solver-reported value.

### Step 4 - Verify Solution Feasibility
- Systematically check all constraint types (inventory balance, resource capacity, setup activation, non-negativity) with a tolerance (e.g., `1e-6`).
- Recalculate cumulative demand satisfaction and ensure terminal inventory conditions are met.
- Print a cost breakdown (production, setup, holding) for insight.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (concrete example)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective ...

# Solve
solver = pyo.SolverFactory('appsi_highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
solver.options['mip_rel_gap'] = -1.0  # CAUTION: Avoid negative values; use 0.0 instead.
results = solver.solve(model, tee=False)

# Check status and extract
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    # Extract solution
    production_plan = {(p,t): pyo.value(model.production_quantity[p,t]) for p in model.products for t in model.periods}
    # ... extract other variables ...
    # Post-process and verify
else:
    print("Solver did not find an optimal/feasible solution.")
```

### Common Pitfalls
- Not checking both solver status and termination condition before extracting results.
- Setting invalid solver parameters (like negative `mip_rel_gap`) leading to immediate errors.
- Mixing data transformation logic within the solving stage, causing scope issues during verification.
- Ignoring numerical precision in binary variables, leading to incorrect setup cost reporting.

# Workflow 2 (OR-Tools CP-SAT for Discrete Production)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT solver, treating production quantities as integer variables. It is suitable for problems where production quantities are naturally discrete (e.g., units, batches) and leverages CP-SAT's strength in logical constraints and integrality.

### Step 1 - Define Model and Integer Variables
- Create a CP-SAT model: `model = cp_model.CpModel()`.
- Define `production_quantity[product, period]` as an integer variable with domain `[0, max_production_limit]`.
- Define `inventory_level[product, period]` as an integer variable with domain `[0, large_upper_bound]`.
- Define `setup_indicator[product, period]` as a Boolean variable (`model.NewBoolVar()`).

### Step 2 - Formulate Demand and Inventory Constraints
- For each product and period, compute `period_demand` from cumulative data.
- Enforce inventory flow: `inventory_level[p, t] == inventory_level[p, t-1] + production_quantity[p, t] - period_demand[p, t]` for `t > 0`. Handle initial period separately.
- Optionally, enforce `inventory_level[p, final_period] == 0`.

### Step 3 - Link Production to Setup Using Logical Constraints
- Use `model.Add(production_quantity[p, t] > 0).OnlyEnforceIf(setup_indicator[p, t])` to enforce setup when production is positive.
- Use `model.Add(production_quantity[p, t] == 0).OnlyEnforceIf(setup_indicator[p, t].Not())` to allow zero production without setup.
- Alternatively, use a linear big-M constraint: `model.Add(production_quantity[p, t] <= max_production_limit * setup_indicator[p, t])`.

### Step 4 - Add Resource Capacity Constraints
- For each period, sum resource consumption: `sum(resource_consumption[p] * production_quantity[p, t] for p in products) <= resource_capacity[t]`.

### Step 5 - Define Linear Objective
- Define the objective expression as a linear sum of costs: `sum(production_cost * production_quantity + setup_cost * setup_indicator + holding_cost * inventory_level)`.
- Call `model.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": ["products", "periods"],
  "parameters": {
    "cumulative_demand": ["product", "period"],
    "production_cost": ["product", "period"],
    "setup_cost": ["product", "period"],
    "holding_cost": ["product", "period"],
    "resource_consumption": ["product"],
    "resource_capacity": ["period"],
    "max_production_limit": ["product", "period"]
  },
  "decision_variables": {
    "production_quantity": ["product", "period", "integer", "nonnegative"],
    "inventory_level": ["product", "period", "integer", "nonnegative"],
    "setup_indicator": ["product", "period", "boolean"]
  },
  "objective": {
    "sense": "min",
    "expression": "sum(production_cost * production_quantity + setup_cost * setup_indicator + holding_cost * inventory_level)"
  },
  "constraints": [
    "inventory_balance_integer",
    "setup_activation_logical",
    "resource_capacity_linear"
  ]
}
```

### Common Pitfalls
- Using excessively large upper bounds for integer variables, which can degrade solver performance.
- Incorrectly implementing logical constraints for setup activation, leading to infeasibility or incorrect costs.
- Forgetting that CP-SAT requires integer coefficients; ensure all parameters in constraints are integers or scaled appropriately.
- Neglecting to handle the initial inventory condition, assuming it is zero.

## Solving stage

### Strategy Overview
This stage involves solving the CP-SAT model, configuring solver parameters for search, and extracting the integer solution with verification. CP-SAT provides built-in search strategies and parallelism.

### Step 1 - Configure and Solve
- Optionally, set solver parameters: `model.Proto().num_search_workers = 4`.
- Call `solver = cp_model.CpSolver()` and set a time limit: `solver.parameters.max_time_in_seconds = 30`.
- Solve: `status = solver.Solve(model)`.

### Step 2 - Interpret Solver Status
- Check status: `status` can be `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, or `UNKNOWN`.
- For `OPTIMAL` or `FEASIBLE`, proceed to solution extraction.

### Step 3 - Extract Integer Solution
- Extract variable values using `solver.Value(variable)`.
- Boolean `setup_indicator` variables will be 0 or 1.
- Compute the objective value from extracted values for validation.

### Step 4 - Verify and Report
- Verify all constraints with integer arithmetic (no tolerance needed).
- Print a production plan and cost breakdown.
- For automated parsing, output a consistent result line (e.g., `RESULT:{objective_value}`).

### Code Usage
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... define variables, constraints, objective ...

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 4  # Optional
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    objective_value = solver.ObjectiveValue()
    # Extract solution
    production_plan = {}
    for p in products:
        for t in periods:
            prod_val = solver.Value(production_quantity[p, t])
            setup_val = solver.Value(setup_indicator[p, t])
            inv_val = solver.Value(inventory_level[p, t])
            production_plan[(p,t)] = prod_val
    # Verify and report
    print(f"RESULT:{objective_value}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not handling the `UNKNOWN` status, which may occur with time limits.
- Assuming the solver always finds an optimal solution; always check for `FEASIBLE` as well.
- Using non-integer coefficients in linear constraints, causing CP-SAT errors.
- Overlooking the need to scale costs if they are not integers, requiring pre-multiplication by a factor (e.g., 100).
