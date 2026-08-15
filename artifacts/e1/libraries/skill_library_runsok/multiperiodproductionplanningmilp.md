---
name: MultiPeriodProductionPlanningMILP
description: |
  Model and solve multi-period production planning with setup costs as a mixed-integer linear program, using tight Big-M bounds and verifying solution feasibility.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for declarative model construction, focusing on a clean separation of data and model logic. It emphasizes using cumulative demand for tight Big-M constraints and explicit inventory balance equations.

### Step 1 - Define Sets and Parameters
- Declare sets for products and time periods as lists or ranges.
- Define parameters for demand, variable production cost, fixed setup cost, holding cost, capacity, and resource consumption coefficients.

### Step 2 - Create Decision Variables
- Create a continuous variable for production quantity per product and period, with a lower bound of zero.
- Create a binary variable for the setup indicator per product and period.
- Create a continuous variable for inventory level per product and period, with a lower bound of zero.

### Step 3 - Formulate Inventory Balance
- For the first period, enforce `inventory[p, 1] == production[p, 1] - demand[p, 1]`.
- For subsequent periods, enforce `inventory[p, t] == inventory[p, t-1] + production[p, t] - demand[p, t]`.

### Step 4 - Link Production to Setup
- For each product and period, calculate the cumulative remaining demand from that period onward.
- Add a constraint: `production[p, t] <= cumulative_demand[p, t] * setup_indicator[p, t]`.

### Step 5 - Enforce Capacity Limits
- For each period, sum the resource consumption of all production: `sum(consumption[p] * production[p, t] for p in products) <= capacity[t]`.

### Step 6 - Define Objective Function
- Minimize total cost: sum of (production_cost * production) + (setup_cost * setup_indicator) + (holding_cost * inventory) across all products and periods.

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
    "production[product, period] (continuous, >=0)",
    "setup_indicator[product, period] (binary)",
    "inventory[product, period] (continuous, >=0)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(production_cost * production + setup_cost * setup_indicator + holding_cost * inventory)"
  },
  "constraints": [
    "inventory_balance_first_period",
    "inventory_balance_subsequent_periods",
    "setup_activation (Big-M)",
    "capacity_limit"
  ]
}
```

### Common Pitfalls
- Using an arbitrary large number for Big-M instead of cumulative demand, which weakens the formulation.
- Incorrectly indexing inventory balance for the first period, leading to undefined `inventory[p, 0]`.
- Forgetting to set lower bounds (>=0) on production and inventory variables.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver via `SolverFactory`. Focus on robust solver configuration, explicit status checking, and post-solution verification.

### Step 1 - Instantiate Solver and Set Options
- Create a solver instance: `solver = SolverFactory('highs')` (or `'cbc'`).
- Set options like `time_limit` and `mip_rel_gap`. Avoid setting invalid options like negative gaps or conflicting `threads`.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]`.

### Step 3 - Extract and Validate Solution
- Extract variable values using `pyo.value(var)`.
- Programmatically verify key constraints: inventory balances sum to zero, capacity limits are respected, and production only occurs when setup indicator is 1.
- Treat small negative values (e.g., -1e-10) as zero due to numerical precision.

### Step 4 - Report Results and Cost Breakdown
- Print or return production plan, setup schedule, and inventory levels.
- Calculate and display individual cost components (production, setup, holding) for validation.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (model defined as per modeling stage)
model = create_model(data)

# Solve
solver = pyo.SolverFactory('highs')
results = solver.solve(model, tee=True)  # tee=True for solver log

# Check status
if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimal solution found.")
    elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
        print("Feasible solution found.")
    else:
        print(f"Solver stopped: {results.solver.termination_condition}")
else:
    print("Solver failed.")

# Extract and verify solution
if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    production_plan = {(p, t): pyo.value(model.production[p, t]) for p in model.products for t in model.periods}
    # ... verification logic
```

### Common Pitfalls
- Assuming `SolverStatus.ok` implies optimality; must also check `termination_condition`.
- Iterating directly over Pyomo Set objects to extract values, which can cause attribute errors; iterate over the original data lists instead.
- Not handling numerical artifacts, leading to incorrect interpretation of near-zero inventory.

# Workflow 2 (OR-Tools with CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools for imperative model construction, providing fine-grained control over variable and constraint creation. It is suited for integration into larger applications and emphasizes solver performance.

### Step 1 - Initialize Model and Create Variable Arrays
- Create a CP-SAT or MIP solver instance from `ortools.linear_solver`.
- Create continuous variable arrays for production quantity and inventory level.
- Create Boolean variable arrays for setup indicators.

### Step 2 - Add Inventory Balance Constraints
- For each product, add a constraint for the first period: `inventory[p][0] == production[p][0] - demand[p][0]`.
- For each subsequent period, add: `inventory[p][t] == inventory[p][t-1] + production[p][t] - demand[p][t]`.

### Step 3 - Add Setup Activation with Cumulative Big-M
- For each product and period, compute the sum of demand from that period to the end.
- Add a constraint: `production[p][t] <= cumulative_demand * setup_indicator[p][t]`.

### Step 4 - Add Capacity Constraints
- For each period, create a linear expression summing `resource_consumption[p] * production[p][t]` across products.
- Add a constraint that this sum is less than or equal to the period's capacity.

### Step 5 - Set Objective
- Create a linear expression summing all cost components: variable production cost, fixed setup cost, and inventory holding cost.
- Set the objective to minimize this total cost expression.

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
    "production[product][period] (continuous, lb=0)",
    "setup_indicator[product][period] (Boolean)",
    "inventory[product][period] (continuous, lb=0)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_over_p_t(production_cost * production + setup_cost * setup_indicator + holding_cost * inventory)"
  },
  "constraints": [
    "inventory_flow",
    "setup_force",
    "resource_capacity"
  ]
}
```

### Common Pitfalls
- Forgetting to set lower bounds on continuous variables, allowing negative production.
- Using an incorrect data structure (e.g., list of lists) that causes index mismatches.
- Not scaling large cost coefficients, which can lead to numerical issues in the solver.

## Solving stage

### Strategy Overview
Solve the model using the built-in CBC solver in OR-Tools. Emphasize explicit solver status checks, solution validation, and handling of solver parameters for performance.

### Step 1 - Configure Solver Parameters
- Set a time limit if needed: `solver.SetTimeLimit(time_limit_ms)`.
- Set a relative MIP gap: `solver.SetNumThreads(num_threads)` and enable verbose output for debugging.

### Step 2 - Invoke Solver and Check Result
- Call `result_status = solver.Solve()`.
- Map the returned status to `OPTIMAL`, `FEASIBLE`, or other states. Do not assume a non-zero status code means optimal.

### Step 3 - Extract and Verify Solution Values
- If status is `OPTIMAL` or `FEASIBLE`, retrieve variable values using `.SolutionValue()`.
- Recompute inventory balances and capacity usage to verify the solution satisfies all constraints within a small tolerance.

### Step 4 - Output Solution and Diagnostics
- Print the production schedule, setup pattern, and final inventory.
- Output the total cost and a breakdown by cost type.
- Report capacity utilization per period for insight.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver('CBC')
# ... variable and constraint creation as per modeling stage

# Solve
solver.SetTimeLimit(30000)  # 30 seconds
result_status = solver.Solve()

# Check status
if result_status == pywraplp.Solver.OPTIMAL:
    print('Optimal solution found.')
elif result_status == pywraplp.Solver.FEASIBLE:
    print('Feasible solution found.')
else:
    print('No solution found.')

# Extract and verify
if result_status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    for p in products:
        for t in periods:
            prod_val = production[p][t].solution_value()
            # ... verification logic
```

### Common Pitfalls
- Confusing `FEASIBLE` with `OPTIMAL`; only `OPTIMAL` guarantees proven optimality.
- Not handling the case where the solver hits a time limit and returns a feasible but not optimal solution.
- Attempting to access `.solution_value()` on variables when the solver status is not `OPTIMAL` or `FEASIBLE`, causing errors.
