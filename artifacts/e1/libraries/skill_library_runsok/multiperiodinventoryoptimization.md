---
name: MultiPeriodInventoryOptimization
description: |
  Model and solve multi-period inventory problems with fixed and variable ordering costs as mixed-integer linear programs, using standard inventory balance constraints and big-M linking.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Formulate the problem as a capacitated lot-sizing MILP using Pyomo's abstract modeling syntax. This approach separates model logic from data, enabling easy testing of different scenarios and solver backends.

### Step 1 - Define Sets and Parameters
- Define a set `PERIODS` representing the planning horizon, including period `0` for initial inventory.
- Populate parameter dictionaries for `demand`, `fixed_cost`, `variable_cost`, and `holding_cost` for each period.
- Define a scalar parameter `max_order_qty` as the upper bound for order quantities.

### Step 2 - Create Decision Variables
- Create binary variables `order_indicator[p]` for order placement in each period `p`.
- Create continuous variables `order_quantity[p]` for the amount ordered in each period `p`.
- Create continuous variables `inventory[p]` for the ending inventory level in each period `p`.

### Step 3 - Formulate Inventory Balance Constraints
- For the first period, enforce `inventory[0] + order_quantity[1] == demand[1] + inventory[1]`.
- For subsequent periods `p>1`, enforce `inventory[p-1] + order_quantity[p] == demand[p] + inventory[p]`.
- Explicitly set `inventory[0] = 0` for zero initial inventory.

### Step 4 - Link Binary and Continuous Variables
- Add constraints `order_quantity[p] <= max_order_qty * order_indicator[p]` for each period `p`. This ensures an order quantity can only be positive if the indicator is 1.

### Step 5 - Set Terminal Condition and Objective
- Enforce `inventory[final_period] == 0` for no terminal inventory.
- Construct the objective to minimize total cost: sum over periods of `fixed_cost[p]*order_indicator[p] + variable_cost[p]*order_quantity[p] + holding_cost[p]*inventory[p]`.

### Formulation Template
```json
{
  "sets": ["PERIODS"],
  "parameters": ["demand", "fixed_cost", "variable_cost", "holding_cost", "max_order_qty"],
  "decision_variables": ["order_indicator (binary)", "order_quantity (continuous)", "inventory (continuous)"],
  "objective": {
    "sense": "min",
    "expression": "sum( fixed_cost[p] * order_indicator[p] + variable_cost[p] * order_quantity[p] + holding_cost[p] * inventory[p] for p in PERIODS )"
  },
  "constraints": [
    "inventory_balance[p]: inventory[p-1] + order_quantity[p] == demand[p] + inventory[p] for p > 0",
    "order_linkage[p]: order_quantity[p] <= max_order_qty * order_indicator[p]",
    "initial_inventory: inventory[0] == 0",
    "terminal_inventory: inventory[final_period] == 0"
  ]
}
```

### Common Pitfalls
- Forgetting to define period `0` for initial inventory, leading to index errors in balance constraints.
- Using an insufficiently large `max_order_qty` in the big-M constraint, which can cut off valid optimal solutions.
- Not verifying that all cost and demand parameters are non-negative, as negative values may invalidate the model's economic logic.

## Solving stage

### Strategy Overview
Build a Pyomo ConcreteModel, solve it using an open-source MILP solver (HiGHS or CBC), and rigorously check the solution status before extracting and reporting results.

### Step 1 - Instantiate Model and Populate Data
- Create a `pyo.ConcreteModel()`.
- Define the `model.PERIODS` set and populate all parameter dictionaries from the problem data.
- Use reasonable defaults (e.g., average of known values) to fill any missing or placeholder data points.

### Step 2 - Build Model Using Formulation
- Declare variables (`pyo.Var`) with appropriate bounds and domains (e.g., `pyo.Binary`, `pyo.NonNegativeReals`).
- Add constraints (`pyo.Constraint`) using the rules defined in the modeling stage.
- Set the objective (`pyo.Objective`).

### Step 3 - Configure and Execute Solver
- Instantiate the solver, e.g., `solver = pyo.SolverFactory('highs')` or `'cbc'`.
- Set solver options: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0`.
- Solve the model: `results = solver.solve(model, tee=False)`.

### Step 4 - Validate Solution and Extract Results
- Check the solver status: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `assert results.solver.termination_condition == pyo.TerminationCondition.optimal`.
- Extract variable values using `pyo.value(model.order_indicator[p])` and verify inventory balances numerically.

### Step 5 - Report and Analyze
- Print the total cost and a period-by-period table of decisions (order indicator, quantity, inventory).
- Calculate and display a cost breakdown (fixed, variable, holding) per period.
- Perform a simple sensitivity analysis, such as constraining the total number of orders to understand consolidation trade-offs.

### Code Usage
```python
import pyomo.environ as pyo

# 1. Build model from formulation
model = pyo.ConcreteModel()
model.PERIODS = pyo.RangeSet(0, T)  # T is the final period
# ... populate parameters, add variables, constraints, objective

# 2. Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    print("Optimal solution found.")
    # Extract and print solution
else:
    print("Solver failed:", results.solver.termination_condition)
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, which can lead to extracting invalid solutions from infeasible or non-optimal runs.
- Misinterpreting binary variable values close to 0 or 1 due to solver tolerances; round to the nearest integer for reporting.
- Setting conflicting solver options (e.g., `threads` when the solver is already configured for parallel processing), which can cause errors.

# Workflow 2 (OR-Tools with SCIP/CBC)

## Modeling stage

### Strategy Overview
Formulate the problem directly using the OR-Tools linear solver API, which uses an imperative, builder-style pattern. This is suitable for embedding in applications or when fine-grained control over the solving process is required.

### Step 1 - Initialize Solver and Define Horizon
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Define the number of periods `T` and a large constant `M` for the big-M constraint (e.g., `M = sum(demands)`).

### Step 2 - Declare Variables with Bounds
- Create binary variables `y[t] = solver.BoolVar(f'y_{t}')` for order indicators.
- Create continuous variables `q[t] = solver.NumVar(0, max_order_qty, f'q_{t}')` for order quantities.
- Create continuous variables `i[t] = solver.NumVar(0, solver.infinity(), f'i_{t}')` for inventory levels.

### Step 3 - Implement Inventory Balance Constraints
- For `t` in `1..T`, add constraint `i[t-1] + q[t] == demand[t] + i[t]`.
- Explicitly set `i[0] = 0` by adding a constraint `i[0] == 0`.

### Step 4 - Link Order Indicator and Quantity
- For each period `t`, add constraint `q[t] <= M * y[t]`. This enforces the fixed-cost structure.

### Step 5 - Set Terminal Condition and Objective Function
- Add constraint `i[T] == 0` for zero terminal inventory.
- Build the objective: `solver.Minimize( sum( fixed_cost[t]*y[t] + variable_cost[t]*q[t] + holding_cost[t]*i[t] for t in 1..T ) )`.

### Formulation Template
```json
{
  "sets": ["t in 1..T"],
  "parameters": ["demand[t]", "fixed_cost[t]", "variable_cost[t]", "holding_cost[t]", "max_order_qty", "M (big-M)"],
  "decision_variables": ["y[t] (binary)", "q[t] (continuous)", "i[t] (continuous)"],
  "objective": {
    "sense": "min",
    "expression": "sum( fixed_cost[t]*y[t] + variable_cost[t]*q[t] + holding_cost[t]*i[t] )"
  },
  "constraints": [
    "inventory_balance[t]: i[t-1] + q[t] == demand[t] + i[t]",
    "order_linkage[t]: q[t] <= M * y[t]",
    "initial_inventory: i[0] == 0",
    "terminal_inventory: i[T] == 0"
  ]
}
```

### Common Pitfalls
- Setting `M` too small, which artificially restricts order quantities. Use a safe upper bound like the total demand.
- Forgetting to define inventory variable `i[0]` and then referencing it in the first period's balance constraint.
- Not using `solver.infinity()` for inventory upper bounds, which can inadvertently cap inventory if demand is high.

## Solving stage

### Strategy Overview
Use the OR-Tools solver object to build the model imperatively, configure time limits and parallelism, solve, and then programmatically interrogate the solution status and variable values.

### Step 1 - Build Model and Set Objective
- Use loops to create variables and add constraints as defined in the modeling stage.
- Assemble the objective function using `solver.Minimize()` and `objective.SetCoefficient()` or by summing terms directly.

### Step 2 - Configure Solver Performance
- Set a time limit: `solver.SetTimeLimit(30000)` (time in milliseconds).
- Enable parallel processing if supported: `solver.SetNumThreads(4)`.
- Set other relevant parameters like relative gap tolerance if needed.

### Step 3 - Invoke Solver and Check Result
- Call `status = solver.Solve()`.
- Check if `status == pywraplp.Solver.OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `NOT_SOLVED` statuses appropriately.

### Step 4 - Extract and Verify Solution
- If optimal/feasible, retrieve variable values using `.solution_value()`.
- Programmatically recalculate inventory balances to verify numerical consistency.
- Store results in structured formats (e.g., lists, dictionaries) for reporting.

### Step 5 - Output Standardized Results
- Print total cost and a detailed schedule.
- Optionally, plot the inventory profile over time to visualize the solution.
- Log solver statistics like solve time and iteration count for performance analysis.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
T = num_periods
M = total_demand  # Big-M constant
# ... create variables y, q, i, add constraints, set objective

# 2. Solve with status / termination checks
solver.SetTimeLimit(30000)
status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL:
    print(f"Optimal cost: {solver.Objective().Value()}")
    for t in range(1, T+1):
        y_val = y[t].solution_value()
        q_val = q[t].solution_value()
        i_val = i[t].solution_value()
        print(f"Period {t}: Order? {round(y_val)}, Qty {q_val:.2f}, Inv {i_val:.2f}")
elif status == pywraplp.Solver.FEASIBLE:
    print("Feasible solution found, but may not be optimal.")
else:
    print("No solution found.")
```

### Common Pitfalls
- Assuming `solver.Solve()` returns only `OPTIMAL`; always handle `FEASIBLE` and error statuses.
- Not rounding binary variable values before using them in logical checks, as they may be very close to 0 or 1.
- Overlooking the need to set `i[0]` and `i[T]` constraints, which are separate from the looped balance constraints.
