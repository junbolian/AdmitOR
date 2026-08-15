---
name: MultiPeriodProductionInventoryLP
description: |
  Model and solve multi-period production-inventory problems with resource capacity, sales limits, and terminal inventory targets using linear programming to maximize profit net of holding costs.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Build a Pyomo model using `ConcreteModel` with explicit `Set` and `Param` objects for structured data handling. Define separate variables for production, inventory, and sales to enforce clear flow conservation. Use direct variable bounds for efficiency and implement constraints with conditional logic for period-specific formulations.

### Step 1 - Define Sets and Parameters
- Declare Pyomo `Set` objects for `products` and `periods` to index all variables and constraints.
- Define `Param` objects for all input data: `profit_per_unit`, `holding_cost`, `sales_limit`, `resource_usage`, `resource_capacity`, `target_inventory`, and `inventory_capacity`. Use dictionary initialization with tuple keys for multi-dimensional parameters.

### Step 2 - Create Decision Variables
- Instantiate `production`, `inventory`, and `sales` as `Var` objects indexed by `products` and `periods`.
- Set the domain to `NonNegativeReals` for all variables. Apply the `inventory_capacity` limit directly via the `bounds=(0, inventory_capacity)` argument in the `inventory` variable declaration.

### Step 3 - Formulate Inventory Balance Constraints
- Create a single `Constraint` rule indexed over `products` and `periods`.
- Inside the rule, use conditional logic: for `t == 0`, return `production[p,0] == sales[p,0] + inventory[p,0]`. For `t > 0`, return `inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t]`. Use `Constraint.Skip` for the first period in the general rule to avoid redundancy.

### Step 4 - Add Resource and Sales Constraints
- For each resource type (e.g., machine), create a `Constraint` indexed over `periods` that sums `resource_usage[p] * production[p,t]` across all products and enforces `<= resource_capacity`.
- Create a `Constraint` indexed over `products` and `periods` to enforce `sales[p,t] <= sales_limit[p,t]`.

### Step 5 - Set Terminal Inventory and Objective
- Add an equality `Constraint` indexed over `products` enforcing `inventory[p, final_period] == target_inventory`.
- Define the objective as `maximize sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t] for p in products for t in periods)`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "resources"],
  "parameters": [
    "profit_per_unit[products]",
    "holding_cost",
    "sales_limit[products, periods]",
    "resource_usage[products, resources]",
    "resource_capacity[resources, periods]",
    "target_inventory[products]",
    "inventory_capacity"
  ],
  "decision_variables": [
    "production[products, periods]",
    "inventory[products, periods]",
    "sales[products, periods]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t] for p in products for t in periods)"
  },
  "constraints": [
    "inventory_balance[p,t]: production[p,0] == sales[p,0] + inventory[p,0] if t==0 else inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t]",
    "resource_capacity[r,t]: sum(resource_usage[p,r] * production[p,t] for p in products) <= resource_capacity[r,t]",
    "sales_limit[p,t]: sales[p,t] <= sales_limit[p,t]",
    "terminal_inventory[p]: inventory[p, final_period] == target_inventory[p]"
  ]
}
```

### Common Pitfalls
- Assuming sales limits are minimum requirements rather than maximum ceilings. The constraint must be `sales[p,t] <= sales_limit[p,t]`.
- Applying holding cost to inventory incorrectly. The cost is incurred on the inventory level `inventory[p,t]` carried at the end of period `t`.
- Creating redundant constraints for the initial inventory balance. Use conditional logic within a single constraint rule.
- Misindexing resource capacity parameters. Ensure `resource_capacity` is indexed by `(resource, period)` to allow time-varying capacities (e.g., downtime).

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver via `SolverFactory`. Configure solver options for performance, rigorously check solver status and termination condition before extracting results, and implement post-solve verification to validate constraint satisfaction and analyze bottlenecks.

### Step 1 - Configure and Run Solver
- Instantiate the solver: `solver = SolverFactory('highs')` (or `'cbc'`).
- Set practical options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`. For CBC, also set `solver.options['ratio'] = 0.0` for zero optimality gap.
- Solve with `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Solution Status
- Check if `results.solver.status == SolverStatus.ok`.
- Check if `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If checks fail, do not load solution values; instead, report the status and termination condition for debugging.

### Step 3 - Extract and Verify Solution
- If status checks pass, load solution values using `model.solutions.load_from(results)`.
- Programmatically verify all constraints:
    - Recompute inventory balances and compare with tolerance (e.g., `abs(lhs - rhs) < 1e-6`).
    - Calculate resource usage and compare against capacity.
    - Check sales against limits and terminal inventory against targets.
- Print a verification report listing any violations.

### Step 4 - Analyze Results and Bottlenecks
- Extract and display production, inventory, and sales plans in a structured format (e.g., nested dictionaries).
- Calculate machine utilization percentages (`used_capacity / total_capacity * 100`) for each resource and period to identify binding constraints.
- Compute total revenue, total holding cost, and net profit from variable values to validate the objective.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (model building steps as per Modeling stage)
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    model.solutions.load_from(results)
    # Proceed with extraction and verification
else:
    print(f"Solver failed: {results.solver.status}, {results.solver.termination_condition}")
```

### Common Pitfalls
- Loading solution values without checking termination condition, potentially reading invalid or infeasible results.
- Using an invalid number of threads (e.g., `-1`). Set `threads` to a positive integer.
- Neglecting to verify constraints post-solve, which can miss numerical issues or model formulation errors.
- Switching solvers unnecessarily when the primary solver reports optimality.

# Workflow 2 (OR-Tools with CBC/GLOP)

## Modeling stage

### Strategy Overview
Build a model directly using the OR-Tools linear solver wrapper (`pywraplp`). Create variables with explicit bounds, add constraints via summation loops, and define the objective by setting coefficients. This approach is efficient for prototyping and leverages OR-Tools' robust solver interfaces.

### Step 1 - Initialize Solver and Data Structures
- Create solver instance: `solver = pywraplp.Solver.CreateSolver('CBC')` for MIP-capable or `'GLOP'` for pure LP.
- Define core data structures as Python lists/dictionaries for `products`, `periods`, `profit_per_unit`, `holding_cost`, `sales_limit`, `resource_usage`, `resource_capacity`, `target_inventory`, and `inventory_capacity`.

### Step 2 - Create Variables with Bounds
- Use nested loops over `products` and `periods` to create variables:
    - `production[p][t] = solver.NumVar(0, solver.infinity(), f'prod_{p}_{t}')`
    - `sales[p][t] = solver.NumVar(0, sales_limit[p][t], f'sales_{p}_{t}')`
    - `inventory[p][t] = solver.NumVar(0, inventory_capacity, f'inv_{p}_{t}')`

### Step 3 - Add Inventory Balance Constraints
- For `t == 0`: Add constraint `production[p][0] == sales[p][0] + inventory[p][0]`.
- For `t > 0`: Add constraint `inventory[p][t-1] + production[p][t] == sales[p][t] + inventory[p][t]`.

### Step 4 - Add Resource Capacity and Terminal Constraints
- For each resource and period, create a constraint: `sum(resource_usage[p][r] * production[p][t] for p in products) <= resource_capacity[r][t]`.
- For each product, add terminal constraint: `inventory[p][final_period] == target_inventory[p]`.

### Step 5 - Define Maximization Objective
- Initialize objective: `objective = solver.Objective()`.
- Loop over all products and periods:
    - `objective.SetCoefficient(sales[p][t], profit_per_unit[p])`
    - `objective.SetCoefficient(inventory[p][t], -holding_cost)`
- Set `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "resources"],
  "parameters": [
    "profit_per_unit[products]",
    "holding_cost",
    "sales_limit[products, periods]",
    "resource_usage[products, resources]",
    "resource_capacity[resources, periods]",
    "target_inventory[products]",
    "inventory_capacity"
  ],
  "decision_variables": [
    "production[products, periods] in [0, INF]",
    "sales[products, periods] in [0, sales_limit]",
    "inventory[products, periods] in [0, inventory_capacity]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t])"
  },
  "constraints": [
    "initial_balance[p]: production[p,0] == sales[p,0] + inventory[p,0]",
    "inventory_balance[p,t>0]: inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t]",
    "resource_capacity[r,t]: sum(resource_usage[p,r] * production[p,t]) <= resource_capacity[r,t]",
    "terminal_inventory[p]: inventory[p, final_period] == target_inventory[p]"
  ]
}
```

### Common Pitfalls
- Applying sales limits incorrectly by setting them as variable upper bounds during creation but also adding redundant `<=` constraints.
- Forgetting to set the objective sense to maximization.
- Using `solver.infinity()` for production upper bounds when a practical large number might be more stable.
- Misaligning indices when populating resource usage sums, leading to incorrect capacity constraints.

## Solving stage

### Strategy Overview
Solve the OR-Tools model, check the result status, and extract solution values. Perform post-solve analysis to verify feasibility, calculate key performance indicators, and understand binding constraints through utilization metrics.

### Step 1 - Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE`.
- If not optimal/feasible, report the status and abort solution extraction.

### Step 2 - Extract Solution Values
- If status is acceptable, loop over all variable arrays (`production`, `sales`, `inventory`) and retrieve values using `.solution_value()`.
- Store values in structured dictionaries or lists for reporting.

### Step 3 - Post-Solve Verification and Analysis
- Recompute inventory balances, resource usage, and sales limit adherence to ensure solution feasibility within a tolerance.
- Calculate machine utilization percentages for each resource and period.
- Compute total profit, revenue, and holding costs from extracted values.
- Identify binding constraints by checking which resource capacities are fully utilized or which sales limits are met exactly.

### Step 4 - Report Structured Output
- Print a summary with total production and sales per product.
- Output a period-by-period plan for production, sales, and inventory.
- Display profit decomposition and bottleneck analysis.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('CBC')
# ... (variable and constraint creation as per Modeling stage)
# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL or status == solver.FEASIBLE:
    # Extract solution values
    production_plan = [[production[p][t].solution_value() for t in periods] for p in products]
    # ... extract other variables
    # Proceed with verification and analysis
else:
    print(f"Solver returned status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing `.solution_value()`, which can cause crashes.
- Assuming `OPTIMAL` is the only acceptable status; `FEASIBLE` is also valid for obtaining a usable solution.
- Omitting post-solve verification, potentially missing subtle constraint violations.
- Incorrectly calculating utilization percentages by using wrong indices for capacity parameters.
