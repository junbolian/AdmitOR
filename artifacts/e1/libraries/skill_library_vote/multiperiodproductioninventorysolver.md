---
name: MultiPeriodProductionInventorySolver
description: |
  Model and solve multi-period production-inventory problems with resource capacity, sales limits, and terminal inventory targets using linear programming.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Structure the problem as a linear program using Pyomo's ConcreteModel, defining core variable families for production, inventory, and sales across products and periods. Enforce material flow with inventory balance constraints, resource limits with linear capacity constraints, and market/storage limits with variable bounds.

### Step 1 - Define Core Sets and Parameters
- Declare sets for `products` and `periods` as ordered lists.
- Define parameters for `profit_per_unit`, `holding_cost`, `sales_limit`, `machine_capacity`, `usage_rate`, `max_inventory`, and `target_inventory` using dictionaries or 2D arrays.
- Use Pyomo's `Set` and `Param` components for structured indexing.

### Step 2 - Create Decision Variables
- Instantiate three variable families: `model.production[product, period]`, `model.inventory[product, period]`, and `model.sales[product, period]`.
- Set domain to `pyo.NonNegativeReals` for all variables.
- Apply bounds directly: `model.inventory.bounds = (0, max_inventory)`.

### Step 3 - Formulate Inventory Balance Constraints
- For the initial period (t=0), add constraint: `model.production[p,0] == model.sales[p,0] + model.inventory[p,0]`.
- For subsequent periods (t>0), add constraint: `model.inventory[p,t-1] + model.production[p,t] == model.sales[p,t] + model.inventory[p,t]`.
- Implement efficiently using a single rule with `pyo.Constraint.Skip` for t=0.

### Step 4 - Add Resource Capacity and Market Constraints
- For each machine/resource type `m` and period `t`, add constraint: `sum(usage_rate[p,m] * model.production[p,t] for p in products) <= machine_capacity[m,t]`.
- Add sales limit constraints: `model.sales[p,t] <= sales_limit[p,t]`.
- Add terminal inventory equality: `model.inventory[p, final_period] == target_inventory[p]`.

### Step 5 - Define Profit Maximization Objective
- Construct objective expression: `sum(profit_per_unit[p] * model.sales[p,t] - holding_cost * model.inventory[p,t] for p in products for t in periods)`.
- Set objective sense to `pyo.maximize`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "machines"],
  "parameters": [
    "profit_per_unit[product]",
    "holding_cost",
    "sales_limit[product, period]",
    "machine_capacity[machine, period]",
    "usage_rate[product, machine]",
    "max_inventory",
    "target_inventory[product]"
  ],
  "decision_variables": [
    "production[product, period]",
    "inventory[product, period]",
    "sales[product, period]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit * sales) - sum(holding_cost * inventory)"
  },
  "constraints": [
    "initial_balance: production[p,0] = sales[p,0] + inventory[p,0]",
    "inventory_balance: inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0",
    "capacity: sum(usage_rate * production) <= machine_capacity per machine, period",
    "sales_limit: sales <= sales_limit per product, period",
    "terminal_inventory: inventory[p, final_period] = target_inventory"
  ]
}
```

### Common Pitfalls
- Forgetting to handle the initial period separately in inventory balance, leading to an undefined `inventory[p,-1]`.
- Using nested dictionaries for multi-dimensional parameters without proper tuple-key indexing, causing Pyomo indexing errors.
- Setting `sales_limit` as a variable bound instead of a constraint, which prevents later modification or relaxation.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver via `SolverFactory`. Configure solver options for performance and determinism, implement robust solution status checking, and verify constraint satisfaction post-solve.

### Step 1 - Configure and Run Solver
- Instantiate solver: `solver = pyo.SolverFactory('highs')` or `solver = pyo.SolverFactory('cbc')`.
- Set practical options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`. For LP, avoid MIP-specific options like `mip_rel_gap`.
- Solve with `load_solutions=False`: `results = solver.solve(model, tee=False, load_solutions=False)`.

### Step 2 - Check Solver Status and Termination
- Import `SolverStatus` and `TerminationCondition` from `pyomo.opt`.
- Check: `if results.solver.status == SolverStatus.ok and results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:`.
- Only if checks pass, load the solution: `model.solutions.load_from(results)`.

### Step 3 - Extract and Verify Solution
- Extract objective value: `obj_val = pyo.value(model.obj)`.
- Iterate through variable indices to collect `production`, `inventory`, and `sales` values into dictionaries.
- Implement a verification function that recalculates each constraint's left-hand and right-hand sides using solved values, checking against a tolerance (e.g., `1e-6`).

### Step 4 - Perform Post-Solution Analysis
- Calculate machine utilization percentages per period: `(used_hours / capacity) * 100`.
- Compute sales limit utilization: `(actual_sales / sales_limit) * 100`.
- Break down total revenue and total holding cost to validate objective components.
- Identify binding constraints by checking which constraints are active at equality (within tolerance).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (function returning a ConcreteModel)
model = build_production_inventory_model(data)

# Configure and solve
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, tee=False, load_solutions=False)

# Check status and load solution
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal,
                                             TerminationCondition.feasible}):
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    # Extract variable values...
else:
    # Handle failure: print results.solver.status and results.solver.termination_condition
    raise RuntimeError("Solver did not return an optimal or feasible solution.")

# Verify constraints
verify_solution(model, tolerance=1e-6)
```

### Common Pitfalls
- Loading solutions without checking status first, causing errors when the model is infeasible.
- Using `tee=True` in production, which clutters logs; reserve for debugging.
- Not setting `threads` to a positive integer, which can cause solver errors.

# Workflow 2 (OR-Tools with CBC/GLOP)

## Modeling stage

### Strategy Overview
Formulate the problem directly using OR-Tools' `pywraplp` API, creating variables and constraints via solver methods. This workflow is suitable for both linear programming (GLOP) and mixed-integer programming (CBC) with explicit control over variable bounds.

### Step 1 - Initialize Solver and Create Variables
- Create solver: `solver = pywraplp.Solver.CreateSolver('CBC')` for MIP or `'GLOP'` for LP.
- Define decision variables using `solver.NumVar` or `solver.IntVar` for integer quantities.
- Store variables in dictionaries with tuple keys `(product, period)` for `production`, `inventory`, `sales`.
- Set bounds during creation: `production[p,t] = solver.NumVar(0, solver.infinity(), name)`.

### Step 2 - Set Variable Bounds for Limits
- Apply sales limits directly as variable upper bounds: `sales[p,t] = solver.NumVar(0, sales_limit[p][t], name)`.
- Apply inventory capacity as variable bounds: `inventory[p,t] = solver.NumVar(0, max_inventory, name)`.

### Step 3 - Build Inventory Balance Constraints
- For period 0: `solver.Add(production[p,0] == sales[p,0] + inventory[p,0])`.
- For period t>0: `solver.Add(inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t])`.
- Loop over products and periods to add all constraints.

### Step 4 - Add Resource Capacity Constraints
- For each machine `m` and period `t`, create a constraint: `ct = solver.Constraint(-solver.infinity(), machine_capacity[m][t])`.
- For each product `p`, add term: `ct.SetCoefficient(production[p,t], usage_rate[p][m])`.

### Step 5 - Define Terminal Inventory and Objective
- Add terminal inventory equality: `solver.Add(inventory[p, final_period] == target_inventory)`.
- Create objective: `objective = solver.Objective()`.
- Set coefficients: `objective.SetCoefficient(sales[p,t], profit_per_unit[p])` and `objective.SetCoefficient(inventory[p,t], -holding_cost)`.
- Set optimization sense: `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "machines"],
  "parameters": [
    "profit_per_unit[product]",
    "holding_cost",
    "sales_limit[product, period]",
    "machine_capacity[machine, period]",
    "usage_rate[product, machine]",
    "max_inventory",
    "target_inventory[product]"
  ],
  "decision_variables": [
    "production[product, period] (NumVar/IntVar, lb=0)",
    "inventory[product, period] (NumVar/IntVar, lb=0, ub=max_inventory)",
    "sales[product, period] (NumVar/IntVar, lb=0, ub=sales_limit)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit * sales) - sum(holding_cost * inventory)"
  },
  "constraints": [
    "initial_balance: production[p,0] = sales[p,0] + inventory[p,0]",
    "inventory_balance: inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0",
    "capacity: sum(usage_rate * production) <= machine_capacity per machine, period",
    "terminal_inventory: inventory[p, final_period] = target_inventory"
  ]
}
```

### Common Pitfalls
- Using `solver.infinity()` for constraint upper bounds when a finite capacity exists, which can hide modeling errors.
- Forgetting to set negative coefficients for holding costs in the objective, effectively maximizing costs.
- Creating variables without storing references, making them inaccessible later for solution extraction.

## Solving stage

### Strategy Overview
Solve the OR-Tools model, set performance options like time limit and threads, verify solution status, and extract variable values for reporting and validation.

### Step 1 - Configure Solver and Solve
- Set solver time limit: `solver.SetTimeLimit(30000)` (milliseconds).
- Set number of threads: `solver.SetNumThreads(4)`.
- Call `solver.Solve()` to execute optimization.

### Step 2 - Verify Solution Status
- Check result status: `if status in (solver.OPTIMAL, solver.FEASIBLE):`.
- If status is `solver.INFEASIBLE` or `solver.UNBOUNDED`, output diagnostic information and terminate.

### Step 3 - Extract Solution Values
- Extract objective value: `obj_val = objective.Value()`.
- Iterate through variable dictionaries, get values via `.solution_value()`.
- Store results in nested dictionaries or a DataFrame for analysis.

### Step 4 - Validate and Analyze Solution
- Recompute machine usage: `used_hours = sum(usage_rate[p][m] * production[p,t].solution_value())` and compare against capacity.
- Verify inventory balances and terminal conditions with tolerance.
- Calculate utilization percentages and identify binding constraints.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver('CBC')
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Create variables, constraints, objective...
# (Refer to Modeling stage steps)

# Solve
status = solver.Solve()

# Check status and extract results
if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    production_vals = {(p,t): production[p,t].solution_value() for p in products for t in periods}
    # Extract other variables...
    # Perform verification
    verify_ortools_solution(solver, data, tolerance=1e-6)
else:
    # Handle failure
    print(f"Solver status: {status}")
```

### Common Pitfalls
- Not setting a time limit for large instances, causing indefinite runtime.
- Assuming `solver.OPTIMAL` is the only acceptable status; `solver.FEASIBLE` may also be acceptable for near-optimal solutions.
- Extracting variable values without checking status first, leading to access errors.
