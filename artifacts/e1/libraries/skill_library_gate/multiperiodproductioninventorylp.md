---
name: MultiPeriodProductionInventoryLP
description: |
  Model and solve multi-period production-inventory problems as linear programs to maximize profit under resource, sales, and inventory constraints, using either a direct solver API or an algebraic modeling framework.

---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., OR-Tools) for explicit, low-level model construction. It is suitable for users who prefer fine-grained control over variable and constraint creation, and for integrating into systems where a lightweight, non-algebraic interface is preferred.

### Step 1 - Define Core Variables
- Create three separate non-negative decision variable arrays: `production[p,t]`, `sales[p,t]`, and `inventory[p,t]` for each product `p` and time period `t`.
- Set appropriate bounds directly during variable creation: `0` as the lower bound, and `solver.infinity()` or explicit capacity limits (e.g., `max_inventory`) as the upper bound.

### Step 2 - Formulate Inventory Balance Constraints
- For the initial period `t=0`, add constraints: `production[p,0] == sales[p,0] + inventory[p,0]`.
- For subsequent periods `t>0`, add constraints: `inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t]`.
- Implement these constraints using nested loops over products and periods.

### Step 3 - Add Capacity and Limit Constraints
- Add resource capacity constraints per period: `sum_{p} usage_coeff[p,r] * production[p,t] <= capacity[r,t]` for each resource `r`.
- Add sales limit constraints as variable upper bounds or explicit constraints: `sales[p,t] <= sales_limit[p,t]`.
- Add terminal inventory target as an equality constraint: `inventory[p,T] == terminal_target[p]`.

### Step 4 - Define the Objective Function
- Formulate the objective to maximize total profit: `sum_{p,t} (unit_profit[p] * sales[p,t] - holding_cost[p] * inventory[p,t])`.
- Set coefficients for each variable individually within the solver's objective object.

### Formulation Template
```json
{
  "sets": [
    "products",
    "periods",
    "resources"
  ],
  "parameters": [
    "unit_profit[product]",
    "holding_cost[product]",
    "usage_coeff[product, resource]",
    "capacity[resource, period]",
    "sales_limit[product, period]",
    "max_inventory[product]",
    "terminal_target[product]"
  ],
  "decision_variables": [
    "production[product, period] >= 0",
    "sales[product, period] >= 0",
    "inventory[product, period] >= 0, <= max_inventory[product]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(unit_profit[p] * sales[p,t] - holding_cost[p] * inventory[p,t]) for p in products, t in periods"
  },
  "constraints": [
    "initial_balance: production[p,0] == sales[p,0] + inventory[p,0] for p in products",
    "dynamic_balance: inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t] for p in products, t in periods where t>0",
    "resource_capacity: sum(usage_coeff[p,r] * production[p,t] for p in products) <= capacity[r,t] for r in resources, t in periods",
    "terminal_condition: inventory[p,T] == terminal_target[p] for p in products"
  ]
}
```

### Common Pitfalls
- Forgetting to handle the initial period (`t=0`) separately in the inventory balance, leading to an index error.
- Setting variable bounds incorrectly (e.g., using `None` instead of `solver.infinity()` for an unbounded upper limit).
- Adding the objective coefficient for `inventory` variables as positive, which should be negative (cost).

## Solving stage

### Strategy Overview
This stage focuses on solving the constructed model using a direct LP solver (e.g., GLOP), rigorously checking the solution status, extracting results, and performing post-solve validation to ensure correctness and feasibility.

### Step 1 - Initialize Solver and Solve
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Call the solver's `Solve()` method.

### Step 2 - Check Solution Status
- Check if the solver status is `OPTIMAL` or `FEASIBLE`. If not, handle the failure by logging diagnostics and exiting gracefully.
- For verification, optionally solve with a second solver (e.g., SCIP) and compare objective values.

### Step 3 - Extract and Structure Solution
- Extract variable values using `.solution_value()` for all `production`, `sales`, and `inventory` variables.
- Store the results in a structured format (e.g., nested dictionaries keyed by product and period).

### Step 4 - Programmatic Verification
- Re-evaluate all constraints using the extracted solution values to confirm feasibility.
- Print a verification summary indicating `OK` or `FAIL` for each constraint type.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
# ... (Variable and constraint creation as per Modeling Stage)
objective = solver.Objective()
# ... (Set objective coefficients)
solver.Maximize(objective)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f"Objective value = {solver.Objective().Value()}")
    # Extract and print solution
    for p in products:
        for t in periods:
            prod_val = production[p,t].solution_value()
            # ... extract other variables
            print(f"Product {p}, Period {t}: Prod={prod_val}, ...")
    # Optional verification
    verify_constraints(production, sales, inventory, params)
else:
    print("The problem does not have an optimal solution.")
    print(f"Solver status: {status}")
```

### Common Pitfalls
- Assuming `OPTIMAL` status without checking for `FEASIBLE`, which may provide a valid but suboptimal solution.
- Not verifying that extracted solution values satisfy all constraints, especially after manual model modifications.
- Misinterpreting solver status codes; always refer to the solver's documentation for their meaning.

# Workflow 2 (Algebraic Modeling Framework)

## Modeling stage

### Strategy Overview
This workflow uses an algebraic modeling framework (e.g., Pyomo) to declaratively define sets, parameters, variables, and constraints. It is suitable for rapid prototyping, clear separation of model logic from data, and leveraging advanced solver interfaces.

### Step 1 - Declare Model Components
- Define `pyo.Set` objects for `products`, `periods`, and `resources`.
- Define `pyo.Param` objects for all input parameters (profit, costs, capacities, limits).
- Declare `pyo.Var` objects for `production`, `sales`, and `inventory` with appropriate domains (e.g., `pyo.NonNegativeReals`) and bounds.

### Step 2 - Build Constraints with Rule Functions
- Implement inventory balance as a `pyo.Constraint` with a rule function. Inside the rule, use conditional logic (`if t == 0`) to apply the correct equation for each period.
- Implement resource capacity and sales limit constraints using `pyo.Constraint` rules that iterate over the relevant sets.
- Implement the terminal inventory condition as a separate constraint rule.

### Step 3 - Construct the Objective
- Define the objective as a `pyo.Objective` with `sense=pyo.maximize`.
- Use a summation expression over sets and parameters to calculate total profit: `sum(profit[p] * sales[p,t] - holding_cost[p] * inventory[p,t] for p in products for t in periods)`.

### Formulation Template
```json
{
  "sets": [
    "products",
    "periods",
    "resources"
  ],
  "parameters": [
    "profit[product]",
    "holding_cost[product]",
    "resource_usage[product, resource]",
    "resource_capacity[resource, period]",
    "sales_capacity[product, period]",
    "inventory_capacity[product]",
    "terminal_inventory[product]"
  ],
  "decision_variables": [
    "production[product, period] in NonNegativeReals",
    "sales[product, period] in NonNegativeReals",
    "inventory[product, period] in NonNegativeReals, bounds=(0, inventory_capacity[product])"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[p] * sales[p,t] - holding_cost[p] * inventory[p,t] for p in products for t in periods)"
  },
  "constraints": [
    "inventory_balance[product, period]: (rule with conditional logic for t=0 and t>0)",
    "resource_limit[resource, period]: sum(resource_usage[p,r] * production[p,t] for p in products) <= resource_capacity[r,t]",
    "sales_limit[product, period]: sales[p,t] <= sales_capacity[p,t]",
    "terminal_inventory[product]: inventory[p, final_period] == terminal_inventory[p]"
  ]
}
```

### Common Pitfalls
- Using Python loops inside constraint rules incorrectly, leading to performance issues or incorrect constraint indexing; prefer set-based summations.
- Forgetting to handle the `Skip` condition in Pyomo constraint rules for boundary cases (e.g., `t==0` in dynamic balance), causing redundant or incorrect constraints.
- Mismatching the indexing order between parameter dictionaries and constraint rule arguments.

## Solving stage

### Strategy Overview
This stage involves selecting a suitable solver (e.g., CBC, HiGHS), configuring it, solving the Pyomo model, and implementing robust result extraction and validation. It emphasizes handling solver failures gracefully and outputting structured results.

### Step 1 - Configure and Execute Solver
- Instantiate a solver object via `pyo.SolverFactory('solver_name')` (e.g., `'cbc'`).
- Set solver options such as time limit (`seconds`) and optimality gap tolerance (`ratio`).
- Call `solver.solve(model, tee=False)` to execute the solve.

### Step 2 - Validate Solver Termination
- Check both `solver.status` (should be `ok`) and `model.solutions[0].termination_condition` (should be `optimal` or `feasible`).
- If termination is not successful, output a structured JSON payload with error details instead of raising an exception.

### Step 3 - Extract and Format Solution
- Use `pyo.value(var)` to retrieve the value of each decision variable.
- Populate solution dictionaries or arrays organized by product and period.
- Print a clear summary including the objective value and key decision variable values.

### Step 4 - Post-Solve Verification and Output
- Implement a verification function that checks each constraint type against the extracted solution, logging any violations.
- Format the final output for automation, using a consistent prefix like `RESULT:` for success.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (Define sets, params, variables, constraints, objective as per Modeling Stage)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, tee=False)

# Check solver and model status
if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:
    print(f"RESULT:{pyo.value(model.objective)}")
    # Extract solution
    sol = {}
    for p in model.products:
        for t in model.periods:
            sol[(p,t)] = {
                'production': pyo.value(model.production[p,t]),
                'sales': pyo.value(model.sales[p,t]),
                'inventory': pyo.value(model.inventory[p,t])
            }
    # Print detailed solution
    print(sol)
else:
    # Handle failure
    fail_payload = {
        "status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
    print(f"RESULT_JSON:{json.dumps(fail_payload)}")
```

### Common Pitfalls
- Confusing `solver.status` (communication status) with `termination_condition` (solution quality); both must be checked.
- Not using `pyo.value()` to access variable values, leading to references to the variable object instead of its numerical solution.
- Omitting post-solve verification, which can mask modeling errors that the solver might not explicitly report.
