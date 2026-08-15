---
name: Multi-Period Production-Inventory Planning
description: |
  Model and solve multi-period production planning problems with inventory balance, resource capacity, and sales limits using linear programming, with workflows for both direct solver APIs and algebraic modeling frameworks.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a direct, low-level API (e.g., OR-Tools `pywraplp`) to construct a linear program. It is suitable for straightforward implementations where explicit control over variable and constraint creation is preferred, and integration with other Python libraries is minimal.

### Step 1 - Define Core Variables
- Declare three core variable types as non-negative continuous: `production_quantity[p,t]`, `inventory_level[p,t]`, and `sales_quantity[p,t]` for each product `p` and period `t`.
- Set explicit upper bounds on variables where known: `sales_quantity[p,t] <= sales_limit[p,t]` and `inventory_level[p,t] <= inventory_capacity[p]`.

### Step 2 - Implement Inventory Dynamics
- Create inventory balance constraints recursively. For the first period (`t=0`): `production_quantity[p,0] == sales_quantity[p,0] + inventory_level[p,0]`.
- For subsequent periods (`t>0`): `inventory_level[p,t-1] + production_quantity[p,t] == sales_quantity[p,t] + inventory_level[p,t]`.

### Step 3 - Incorporate Resource Constraints
- For each machine/resource `m` and period `t`, sum the resource consumption: `sum_over_p( time_required[p,m] * production_quantity[p,t] ) <= machine_capacity[m,t]`.
- Ensure `time_required` and `machine_capacity` parameters are defined as dictionaries or 2D arrays.

### Step 4 - Set Terminal and Objective
- Add equality constraints for terminal inventory: `inventory_level[p, final_period] == terminal_inventory_value[p]`.
- Formulate the objective to maximize profit: `sum_over_p_t( profit_per_unit[p] * sales_quantity[p,t] - holding_cost[p] * inventory_level[p,t] )`.

### Formulation Template
```json
{
  "sets": [
    "products",
    "periods",
    "machines"
  ],
  "parameters": [
    "sales_limit[product, period]",
    "inventory_capacity[product]",
    "machine_capacity[machine, period]",
    "time_required[product, machine]",
    "profit_per_unit[product]",
    "holding_cost[product]",
    "terminal_inventory_value[product]"
  ],
  "decision_variables": [
    "production_quantity[product, period] >= 0",
    "sales_quantity[product, period] >= 0",
    "inventory_level[product, period] >= 0"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales_quantity[p,t] - holding_cost[p] * inventory_level[p,t]) over p,t"
  },
  "constraints": [
    "inventory_balance_first_period[p]: production_quantity[p,0] == sales_quantity[p,0] + inventory_level[p,0]",
    "inventory_balance[p,t>0]: inventory_level[p,t-1] + production_quantity[p,t] == sales_quantity[p,t] + inventory_level[p,t]",
    "machine_capacity[m,t]: sum(time_required[p,m] * production_quantity[p,t] for p in products) <= machine_capacity[m,t]",
    "sales_limit[p,t]: sales_quantity[p,t] <= sales_limit[p,t]",
    "inventory_capacity[p,t]: inventory_level[p,t] <= inventory_capacity[p]",
    "terminal_inventory[p]: inventory_level[p, final_period] == terminal_inventory_value[p]"
  ]
}
```

### Common Pitfalls
- Forgetting to define the inventory balance for the first period separately, leading to an index error for `t-1`.
- Incorrectly summing resource usage across the wrong index (e.g., summing over periods instead of products).
- Not setting upper bounds on `sales_quantity` and `inventory_level` variables, which can lead to unbounded models if limits are not enforced via constraints.

## Solving stage

### Strategy Overview
Solve the constructed model using the CBC solver via a direct API. Focus on configuring solver options for performance, rigorously checking the solution status, and programmatically verifying constraint satisfaction to ensure model fidelity.

### Step 1 - Configure and Execute Solver
- Instantiate the solver (e.g., `solver = pywraplp.Solver.CreateSolver('CBC')`).
- Set practical solver options: `solver.SetTimeLimit(30000)` for a 30-second limit, `solver.SetNumThreads(4)` for parallel processing.

### Step 2 - Check Solution Status and Extract Values
- After solving, check the primary result status: `if result_status == pywraplp.Solver.OPTIMAL:`.
- Extract variable values into structured dictionaries or DataFrames for easy analysis: `production_plan[p,t] = production_quantity[p,t].solution_value()`.

### Step 3 - Implement Solution Verification
- Programmatically verify all constraint types with tolerance checks (e.g., `abs(lhs - rhs) < 1e-6`).
- Calculate key metrics: machine utilization (`used_hours / capacity`), total revenue, total holding cost, and validate the objective value.

### Step 4 - Analyze and Report
- Identify binding constraints by checking slack values (near zero for capacity constraints).
- Print detailed schedules for production, sales, and inventory by period and product.
- Compute profit contribution per constrained resource hour to understand product prioritization.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('CBC')
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# ... (variable and constraint creation code)

# solve with status / termination checks
result_status = solver.Solve()
if result_status == pywraplp.Solver.OPTIMAL:
    print('Optimal solution found.')
    # Extract and verify solution
    for p in products:
        for t in periods:
            prod_val = production_quantity[p,t].solution_value()
            # ... store values
    # Verification loop
    tolerance = 1e-6
    for constr in all_constraints:
        # ... check satisfaction
elif result_status == pywraplp.Solver.FEASIBLE:
    print('Feasible, but not proven optimal.')
else:
    print('Solve failed.')
```

### Common Pitfalls
- Assuming `OPTIMAL` status without checking, leading to errors when accessing `solution_value()` on an infeasible model.
- Not using a tolerance when verifying constraints, causing false failures due to floating-point arithmetic.
- Omitting thread configuration for larger models, resulting in slower solve times.

# Workflow 2 (Algebraic Modeling Language - Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses an Algebraic Modeling Language (AML) like Pyomo to declaratively define the model. It separates the abstract formulation from data, improving readability and maintainability for complex, multi-dimensional problems.

### Step 1 - Declare Abstract Sets and Parameters
- Define abstract sets: `model.PRODUCTS`, `model.PERIODS`, `model.MACHINES`.
- Declare parameters using `pyo.Param` with appropriate indexing, e.g., `model.sales_limit = pyo.Param(model.PRODUCTS, model.PERIODS)`.

### Step 2 - Define Variables with Bounds
- Create variables using `pyo.Var` with explicit domains (`pyo.NonNegativeReals`).
- Integrate bounds directly into variable declarations where possible: `model.inventory_level = pyo.Var(model.PRODUCTS, model.PERIODS, bounds=(0, inventory_capacity))`.

### Step 3 - Construct Constraints Declaratively
- Implement inventory balance using a rule function that handles the first period logic with `Constraint.Skip`.
- Define machine capacity and sales limit constraints using summation components over the appropriate sets.

### Step 4 - Formulate Objective and Terminal Conditions
- Build the objective function as a `pyo.Objective` with `sense=pyo.maximize`.
- Add terminal inventory as a separate `pyo.Constraint` rule indexed by products.

### Formulation Template
```json
{
  "sets": [
    "PRODUCTS",
    "PERIODS",
    "MACHINES"
  ],
  "parameters": [
    "sales_limit[PRODUCTS, PERIODS]",
    "inventory_capacity[PRODUCTS]",
    "machine_capacity[MACHINES, PERIODS]",
    "time_required[PRODUCTS, MACHINES]",
    "profit_per_unit[PRODUCTS]",
    "holding_cost[PRODUCTS]",
    "terminal_inventory_value[PRODUCTS]"
  ],
  "decision_variables": [
    "production_quantity[PRODUCTS, PERIODS] in NonNegativeReals",
    "sales_quantity[PRODUCTS, PERIODS] in NonNegativeReals",
    "inventory_level[PRODUCTS, PERIODS] in NonNegativeReals, bounds=(0, inventory_capacity)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales_quantity[p,t] for p in PRODUCTS for t in PERIODS) - sum(holding_cost[p] * inventory_level[p,t] for p in PRODUCTS for t in PERIODS)"
  },
  "constraints": [
    "inventory_balance_rule(p,t): rule function handling t=0 and t>0 cases",
    "machine_capacity_rule(m,t): sum(time_required[p,m] * production_quantity[p,t] for p in PRODUCTS) <= machine_capacity[m,t]",
    "sales_limit_rule(p,t): sales_quantity[p,t] <= sales_limit[p,t]",
    "terminal_inventory_rule(p): inventory_level[p, final_period] == terminal_inventory_value[p]"
  ]
}
```

### Common Pitfalls
- Defining parameter dictionaries with incorrect indexing (e.g., `(machine, product)` instead of `(product, machine)`), causing silent errors in constraint rules.
- Forgetting to use `Constraint.Skip` in rule functions for boundary conditions, leading to redundant or malformed constraints.
- Not initializing all required parameters before model instantiation, resulting in runtime errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external solver like HiGHS or CBC. Leverage Pyomo's solver manager for status checking and solution loading. Emphasize reusable verification functions to validate the solution against the abstract model.

### Step 1 - Instantiate Solver and Solve
- Create a solver object: `solver = pyo.SolverFactory('highs')`.
- Solve with `tee=True` to see solver log: `results = solver.solve(model, tee=True)`.

### Step 2 - Check Termination Status Rigorously
- Inspect both solver status and termination condition: `if (results.solver.status == pyo.SolverStatus.ok) and (results.solver.termination_condition == pyo.TerminationCondition.optimal):`.
- Handle feasible but non-optimal solutions appropriately.

### Step 3 - Load and Verify Solution
- Use `model.solutions.load_from(results)` to populate variable values.
- Call a custom verification function that iterates over all constraints, calculates left-hand and right-hand sides using `pyo.value()`, and checks against a tolerance.

### Step 4 - Analyze and Report
- Extract variable values into structured formats (e.g., pandas DataFrame) for reporting.
- Calculate utilization metrics and profit breakdowns by iterating over model components.
- Print schedules and identify bottlenecks by examining constraint dual values or slack.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (set, parameter, variable, constraint, objective definition)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, tee=True)

if (results.solver.status == pyo.SolverStatus.ok) and
   (results.solver.termination_condition == pyo.TerminationCondition.optimal):
    print('Optimal solution found.')
    # Load solution
    model.solutions.load_from(results)
    # Verify solution
    verify_solution(model, tolerance=1e-6)
    # Analyze and report
    for p in model.PRODUCTS:
        for t in model.PERIODS:
            prod_val = pyo.value(model.production_quantity[p,t])
            # ... store values
else:
    print('Solve did not converge to optimal.')
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially accepting suboptimal or failed solutions.
- Accessing variable values via `pyo.value()` before loading the solution, resulting in `None` or initial values.
- Writing verification functions that rely on internal constraint expressions without using `pyo.value()`, leading to incorrect evaluations.
