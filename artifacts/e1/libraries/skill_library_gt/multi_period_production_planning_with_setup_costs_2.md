---
name: Multi-Period Production Planning with Setup Costs
description: |
  Model and solve multi-period production planning problems with setup costs, inventory balance, and resource constraints using MILP formulations, with verification and solver handling.

---

# Workflow 1 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Formulate a Mixed-Integer Linear Program (MILP) using Pyomo's abstract or concrete modeling. Use cumulative demand directly in inventory balance constraints to ensure demand satisfaction across the planning horizon.

### Step 1 - Define Core Variables
- Create continuous, non-negative variables for `production_quantity[product, period]` and `inventory_level[product, period]`.
- Create binary variables for `binary_setup[product, period]` to indicate production setup activation.

### Step 2 - Formulate Inventory Balance
- For the first period, define inventory as production minus the first cumulative demand: `inventory[p,0] == production[p,0] - cumulative_demand[p][0]`.
- For subsequent periods, define inventory recursively: `inventory[p,t] == inventory[p,t-1] + production[p,t] - (cumulative_demand[p][t] - cumulative_demand[p][t-1])`.

### Step 3 - Enforce Setup Activation and Limits
- Link production to setup decisions using a big-M constraint: `production[p,t] <= max_production_limit[p][t] * binary_setup[p,t]`. Use the maximum possible production (e.g., remaining demand) as a tight big-M coefficient.

### Step 4 - Impose Resource and Final Conditions
- Add a linear resource capacity constraint per period: `sum(product: resource_consumption[p] * production[p,t]) <= resource_capacity[t]`.
- Set final inventory to zero: `inventory[p, final_period] == 0`.

### Step 5 - Define Cost Objective
- Minimize total cost: sum over all products and periods of `production_cost[p][t] * production[p,t] + setup_cost[p][t] * binary_setup[p,t] + holding_cost[p][t] * inventory[p,t]`.

### Formulation Template
```json
{
  "sets": [
    "products",
    "periods"
  ],
  "parameters": [
    "cumulative_demand[products][periods]",
    "max_production_limit[products][periods]",
    "resource_consumption[products]",
    "resource_capacity[periods]",
    "production_cost[products][periods]",
    "setup_cost[products][periods]",
    "holding_cost[products][periods]"
  ],
  "decision_variables": [
    "production_quantity[products][periods] >= 0",
    "inventory_level[products][periods] >= 0",
    "binary_setup[products][periods] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{p,t} (production_cost[p][t] * production_quantity[p][t] + setup_cost[p][t] * binary_setup[p][t] + holding_cost[p][t] * inventory_level[p][t])"
  },
  "constraints": [
    "inventory_balance_initial[p]: inventory_level[p][0] == production_quantity[p][0] - cumulative_demand[p][0]",
    "inventory_balance_subsequent[p][t>0]: inventory_level[p][t] == inventory_level[p][t-1] + production_quantity[p][t] - (cumulative_demand[p][t] - cumulative_demand[p][t-1])",
    "setup_activation[p][t]: production_quantity[p][t] <= max_production_limit[p][t] * binary_setup[p][t]",
    "resource_capacity_period[t]: sum_{p} resource_consumption[p] * production_quantity[p][t] <= resource_capacity[t]",
    "final_inventory_zero[p]: inventory_level[p][final_period] == 0"
  ]
}
```

### Common Pitfalls
- Using an overly large, non-tight big-M value for setup activation, which weakens the LP relaxation.
- Incorrectly indexing cumulative demand differences, leading to inventory balance errors.
- Forgetting to set final inventory to zero, allowing leftover inventory without cost penalty.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via the `SolverFactory`. Configure solver options for performance and precision, then implement systematic verification of the solution.

### Step 1 - Configure and Run Solver
- Instantiate the solver: `solver = SolverFactory('highs')`.
- Set key options: `time_limit=30`, `mip_rel_gap=0.0` (for exact optimality), `mip_abs_gap=1e-8`, `primal_feasibility_tolerance=1e-8`, `dual_feasibility_tolerance=1e-8`.
- Solve the model and capture the results object.

### Step 2 - Check Solver Status and Extract Solution
- Verify the solver termination condition is `optimal` or `feasible`.
- Load results into the model instance.
- Extract variable values into dictionaries, rounding binary variables: `rounded_setup = 1 if value > 0.5 else 0`.

### Step 3 - Implement Comprehensive Verification
- Check inventory balance equations for each product and period with a tolerance (e.g., 1e-6).
- Verify resource capacity constraints are satisfied.
- Confirm setup activation logic: if `production_quantity > 0`, then `binary_setup == 1`.
- Validate final inventory is zero.
- Ensure all inventory levels are non-negative.
- Recalculate total cost from extracted values and compare to solver-reported objective.

### Step 4 - Report Solution
- Print a table of production quantities, inventory levels, and setup decisions for each product and period.
- Output the verified total cost and a cost breakdown (production, setup, holding).

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective ...
instance = model.create_instance(data)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1.0  # Use -1 for default, 0.0 for exact
results = solver.solve(instance, tee=True)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    instance.solutions.load_from(results)
    # Extract and verify solution
    # ... verification code ...
else:
    print(f"Solver terminated with status: {results.solver.termination_condition}")
```

### Common Pitfalls
- Setting invalid solver parameter values (e.g., negative MIP gap).
- Accessing model variables for verification before loading the solution.
- Ignoring numerical precision in binary variables, leading to incorrect setup interpretation.

# Workflow 2 (OR-Tools with SCIP)

## Modeling stage

### Strategy Overview
Build a MILP directly using the OR-Tools linear solver wrapper (pywraplp). Convert cumulative demand to period demand for a standard inventory balance formulation.

### Step 1 - Define Core Variables
- Create continuous variables with lower bound 0 for `production_quantity[product][period]`.
- Create continuous variables with lower bound 0 for `inventory_level[product][period]`.
- Create binary variables for `binary_setup[product][period]`.

### Step 2 - Convert Demand and Formulate Inventory Balance
- Pre-process data: `period_demand[p][t] = cumulative_demand[p][t] - cumulative_demand[p][t-1]` (with `cumulative_demand[p][-1] = 0`).
- For the first period (t=0), set `inventory_level[p][0] == production_quantity[p][0] - period_demand[p][0]`.
- For t>0, enforce `inventory_level[p][t] == inventory_level[p][t-1] + production_quantity[p][t] - period_demand[p][t]`.

### Step 3 - Enforce Setup Activation and Limits
- Add constraints: `production_quantity[p][t] <= max_production_limit[p][t] * binary_setup[p][t]`.

### Step 4 - Impose Resource and Final Conditions
- For each period, create a linear expression: `sum_{p} resource_consumption[p] * production_quantity[p][t]`.
- Add constraint that this expression is `<= resource_capacity[t]`.
- Set `inventory_level[p][final_period] == 0`.

### Step 5 - Define Cost Objective
- Create the objective: `solver.Minimize(sum_{p,t} (production_cost[p][t] * production_quantity[p][t] + setup_cost[p][t] * binary_setup[p][t] + holding_cost[p][t] * inventory_level[p][t]))`.

### Formulation Template
```json
{
  "sets": [
    "products",
    "periods"
  ],
  "parameters": [
    "cumulative_demand[products][periods]",
    "max_production_limit[products][periods]",
    "resource_consumption[products]",
    "resource_capacity[periods]",
    "production_cost[products][periods]",
    "setup_cost[products][periods]",
    "holding_cost[products][periods]"
  ],
  "decision_variables": [
    "production_quantity[products][periods] >= 0",
    "inventory_level[products][periods] >= 0",
    "binary_setup[products][periods] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{p,t} (production_cost[p][t] * production_quantity[p][t] + setup_cost[p][t] * binary_setup[p][t] + holding_cost[p][t] * inventory_level[p][t])"
  },
  "constraints": [
    "period_demand[p][t] = cumulative_demand[p][t] - cumulative_demand[p][t-1] (pre-processed)",
    "inventory_balance_initial[p]: inventory_level[p][0] == production_quantity[p][0] - period_demand[p][0]",
    "inventory_balance_subsequent[p][t>0]: inventory_level[p][t] == inventory_level[p][t-1] + production_quantity[p][t] - period_demand[p][t]",
    "setup_activation[p][t]: production_quantity[p][t] <= max_production_limit[p][t] * binary_setup[p][t]",
    "resource_capacity_period[t]: sum_{p} resource_consumption[p] * production_quantity[p][t] <= resource_capacity[t]",
    "final_inventory_zero[p]: inventory_level[p][final_period] == 0"
  ]
}
```

### Common Pitfalls
- Incorrectly calculating period demand from cumulative data, leading to unmet demand.
- Building complex linear expressions inefficiently; construct them manually term-by-term.
- Forgetting to set variable bounds, allowing negative production or inventory.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' SCIP solver interface. Set performance options, solve, and then verify all constraints and objective value programmatically.

### Step 1 - Configure and Run Solver
- Create solver: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Set a time limit: `solver.SetTimeLimit(30000)` (in milliseconds).
- Optionally set thread count: `solver.SetNumThreads(4)`.
- Call `solver.Solve()`.

### Step 2 - Extract Solution and Verify Status
- Check the solver result: `if result == pywraplp.Solver.OPTIMAL or result == pywraplp.Solver.FEASIBLE`.
- Extract variable values using `.solution_value()`.
- Round binary variable values to 0 or 1 based on a tolerance (e.g., 0.5).

### Step 3 - Implement Comprehensive Verification
- Re-evaluate all inventory balance equations using extracted values and period demand, checking within tolerance.
- Compute resource usage per period and verify against capacity.
- Confirm setup activation logic.
- Check final inventory is zero and all inventory is non-negative.
- Recalculate total cost from extracted values and compare to `solver.Objective().Value()`.

### Step 4 - Report Solution and Cost Breakdown
- Print a structured solution (product, period, production, inventory, setup).
- Output a detailed cost breakdown (production, setup, holding) for analysis.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... create variables, add constraints, set objective ...

# solve with status / termination checks
solver.SetTimeLimit(30000)
result_status = solver.Solve()

if result_status == pywraplp.Solver.OPTIMAL:
    # Extract solution values
    prod_val = production_quantity[p][t].solution_value()
    # ... verification and reporting ...
else:
    print(f"Solver did not find optimal solution. Status: {result_status}")
```

### Common Pitfalls
- Using `solver.Sum()` for large expressions; manually sum terms for better performance and clarity.
- Not handling numerical precision in verification, leading to false constraint violations.
- Overlooking the need to pre-process cumulative demand into period demand before building constraints.
