---
name: MultiPeriodProductionPlanning
description: |
  Formulate and solve multi-period production planning with setup costs, inventory holding, and capacity constraints as a Mixed-Integer Linear Program (MILP) using tight Big-M constraints and inventory balance recursion.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem in Pyomo using explicit Set objects for clean indexing. Formulate a MILP with tight cumulative-demand-based Big-M constraints to improve solver performance. Structure the objective as a sum of production, setup, and holding costs.

### Step 1 - Define Model Sets and Parameters
- Create Pyomo Sets for `products` and `periods` to index all variables and constraints.
- Define all cost, demand, capacity, and consumption parameters as Pyomo Params or dictionaries.

### Step 2 - Create Decision Variables
- Define continuous variable `production_quantity` indexed by product and period.
- Define binary variable `setup_indicator` indexed by product and period.
- Define continuous variable `inventory_level` indexed by product and period.

### Step 3 - Implement Inventory Balance Constraints
- For the first period, enforce `production_quantity[p,1] == demand[p,1] + inventory_level[p,1]`.
- For subsequent periods, enforce `inventory_level[p,m-1] + production_quantity[p,m] == demand[p,m] + inventory_level[p,m]`.

### Step 4 - Link Production to Setup with Tight Big-M
- For each product-period pair, calculate `cumulative_remaining_demand`.
- Add constraint `production_quantity[p,m] <= cumulative_remaining_demand * setup_indicator[p,m]`.

### Step 5 - Enforce Capacity Constraints
- For each period, sum the resource consumption across all products: `sum(consumption[p] * production_quantity[p,m] for p in products) <= capacity[m]`.

### Step 6 - Formulate the Cost Objective
- Define objective to minimize total cost: `sum(production_cost[p,m] * production_quantity[p,m] + setup_cost[p,m] * setup_indicator[p,m] + holding_cost[p] * inventory_level[p,m])` over all products and periods.

### Formulation Template
```json
{
  "sets": ["products", "periods"],
  "parameters": [
    "demand[product, period]",
    "production_cost[product, period]",
    "setup_cost[product, period]",
    "holding_cost[product]",
    "capacity[period]",
    "resource_consumption[product]"
  ],
  "decision_variables": [
    "production_quantity[product, period] (continuous, >=0)",
    "setup_indicator[product, period] (binary)",
    "inventory_level[product, period] (continuous, >=0)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(production_cost[p,m] * production_quantity[p,m] + setup_cost[p,m] * setup_indicator[p,m] + holding_cost[p] * inventory_level[p,m] for p in products, m in periods)"
  },
  "constraints": [
    "inventory_balance_first_period: production_quantity[p,1] == demand[p,1] + inventory_level[p,1] for p in products",
    "inventory_balance_subsequent: inventory_level[p,m-1] + production_quantity[p,m] == demand[p,m] + inventory_level[p,m] for p in products, m in periods where m>1",
    "setup_activation: production_quantity[p,m] <= sum(demand[p,k] for k in range(m, total_periods+1)) * setup_indicator[p,m] for p in products, m in periods",
    "capacity_limit: sum(resource_consumption[p] * production_quantity[p,m] for p in products) <= capacity[m] for m in periods"
  ]
}
```

### Common Pitfalls
- Using an arbitrary large constant for Big-M instead of cumulative remaining demand, which degrades solver performance.
- Forgetting to handle the base case for inventory balance in the first period, leading to an undefined `inventory_level[p,0]`.
- Setting conflicting solver options (e.g., `mip_rel_gap` to a negative value) which can cause the solver to fail.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver with minimal, robust configuration. Perform explicit solution status checks and post-solution validation of key constraints. Handle numerical tolerances gracefully.

### Step 1 - Initialize Solver and Set Options
- Create solver object: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set essential options: `solver.options["time_limit"] = timeout_seconds`. Avoid setting unnecessary parameters.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status == pyo.SolverStatus.ok` and `results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}`.

### Step 3 - Extract and Validate Solution
- Extract variable values using `pyo.value(model.production_quantity[p, m])`.
- Programmatically verify inventory balance and capacity constraints hold within a small tolerance (e.g., 1e-6).
- Treat small negative values (e.g., -1e-10) as zero for reporting.

### Step 4 - Calculate and Report Results
- Compute total cost and its breakdown (production, setup, holding).
- Print key outputs: production quantities, setup indicators, inventory levels, and capacity utilization.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (model defined as per Modeling stage)
# ...

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 300  # seconds
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    print("Solver succeeded.")
    # Extract and validate solution
    for p in model.products:
        for m in model.periods:
            prod_qty = pyo.value(model.production_quantity[p, m])
            # ... process values
    total_cost = pyo.value(model.objective)
    print(f"RESULT:{total_cost}")
else:
    print(f"RESULT_JSON:{{'status': '{results.solver.status}', 'termination_condition': '{results.solver.termination_condition}'}}")
```

### Common Pitfalls
- Accessing variable values directly from Pyomo Set objects in loops can cause `AttributeError`; use `model.products` and `model.periods` instead.
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of suboptimal or failed solutions.
- Overlooking numerical precision, causing validation failures for constraints satisfied within solver tolerance.

# Workflow 2 (OR-Tools with CBC/SCIP)

## Modeling stage

### Strategy Overview
Model the problem directly using the OR-Tools linear solver API. Use dictionaries to index variables and constraints. Apply the same tight Big-M logic using cumulative demand. Structure the model for efficient construction and solving with the CBC or SCIP backend.

### Step 1 - Initialize Solver and Create Variable Containers
- Create solver instance: `solver = pywraplp.Solver.CreateSolver("CBC")`.
- Initialize dictionaries (`defaultdict` or nested dicts) to hold variables indexed by `(product, period)`.

### Step 2 - Define Variables with Bounds
- Create continuous variable `production_quantity[p][m]` with lower bound 0.
- Create binary variable `setup_indicator[p][m]`.
- Create continuous variable `inventory_level[p][m]` with lower bound 0.

### Step 3 - Add Inventory Balance Constraints
- For each product, for the first period: `production_quantity[p][1] == demand[p][1] + inventory_level[p][1]`.
- For each product and subsequent period: `inventory_level[p][m-1] + production_quantity[p][m] == demand[p][m] + inventory_level[p][m]`.

### Step 4 - Add Setup Activation Constraints
- Pre-calculate `cumulative_demand_remaining[p][m]`.
- Add constraint `production_quantity[p][m] <= cumulative_demand_remaining[p][m] * setup_indicator[p][m]`.

### Step 5 - Add Aggregate Capacity Constraints
- For each period, create a constraint: `sum(resource_consumption[p] * production_quantity[p][m] for p in products) <= capacity[m]`.

### Step 6 - Set Objective Function
- Build objective expression as a sum of cost terms over all products and periods.
- Call `solver.Minimize(objective_expression)`.

### Formulation Template
```json
{
  "sets": ["products", "periods"],
  "parameters": [
    "demand[product][period]",
    "production_cost[product][period]",
    "setup_cost[product][period]",
    "holding_cost[product]",
    "capacity[period]",
    "resource_consumption[product]"
  ],
  "decision_variables": [
    "production_quantity[product][period] (solver.NumVar, lb=0)",
    "setup_indicator[product][period] (solver.BoolVar)",
    "inventory_level[product][period] (solver.NumVar, lb=0)"
  ],
  "objective": {
    "sense": "min",
    "expression": "solver.Sum(production_cost[p][m] * production_quantity[p][m] + setup_cost[p][m] * setup_indicator[p][m] + holding_cost[p] * inventory_level[p][m] for p in products for m in periods)"
  },
  "constraints": [
    "inventory_balance_first: production_quantity[p][1] == demand[p][1] + inventory_level[p][1] for p in products",
    "inventory_balance: inventory_level[p][m-1] + production_quantity[p][m] == demand[p][m] + inventory_level[p][m] for p in products, m in periods where m>1",
    "setup_link: production_quantity[p][m] <= sum(demand[p][k] for k in range(m, total_periods)) * setup_indicator[p][m] for p in products, m in periods",
    "capacity: solver.Sum(resource_consumption[p] * production_quantity[p][m] for p in products) <= capacity[m] for m in periods"
  ]
}
```

### Common Pitfalls
- Forgetting to pre-calculate cumulative demand for Big-M, leading to repeated calculations inside loops or incorrect bounds.
- Using `solver.IntVar` instead of `solver.BoolVar` for setup indicators, which increases problem complexity unnecessarily.
- Not structuring variable dictionaries clearly, making constraint formulation error-prone and hard to debug.

## Solving stage

### Strategy Overview
Solve the OR-Tools model with performance-oriented settings (time limit, threads). Explicitly check the solver result status. Extract solution values from variable dictionaries and perform validation. Output results in a structured format.

### Step 1 - Configure Solver Performance Settings
- Set a time limit: `solver.SetTimeLimit(time_limit_milliseconds)`.
- Optionally control threads: `solver.SetNumThreads(num_threads)`.

### Step 2 - Invoke Solver and Interpret Status
- Call `status = solver.Solve()`.
- Check `status == pywraplp.Solver.OPTIMAL` for proven optimality, or `status == pywraplp.Solver.FEASIBLE` for a feasible solution.

### Step 3 - Extract and Validate Solution Values
- Iterate over variable dictionaries, using `.solution_value()` on each variable object.
- Verify inventory balance and capacity constraints hold within tolerance.
- Treat near-zero values (e.g., `-1e-9`) as zero.

### Step 4 - Compute Cost Breakdown and Report
- Calculate total cost and individual cost components from the extracted solution values.
- Print production plan, setup schedule, inventory profile, and capacity utilization.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('CBC')
# ... create variables and constraints as per Modeling stage

# Solve with status / termination checks
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)
status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL:
    print('Optimal solution found.')
    total_cost = solver.Objective().Value()
    # Extract solution values
    solution_dict = {}
    for p in products:
        for m in periods:
            solution_dict[(p, m, 'prod')] = production_quantity[p][m].solution_value()
            # ... extract other variables
    print(f'RESULT:{total_cost}')
elif status == pywraplp.Solver.FEASIBLE:
    print('Feasible solution found (not proven optimal).')
    total_cost = solver.Objective().Value()
    print(f'RESULT:{total_cost}')
else:
    print(f'RESULT_JSON:{{"status": {status}}}')
```

### Common Pitfalls
- Not handling both `OPTIMAL` and `FEASIBLE` statuses, which may discard good feasible solutions when optimality is not proven.
- Accessing `.solution_value()` on a variable before checking the solver status, which may raise an error.
- Omitting post-solution validation, potentially accepting solutions that violate constraints due to numerical issues.
