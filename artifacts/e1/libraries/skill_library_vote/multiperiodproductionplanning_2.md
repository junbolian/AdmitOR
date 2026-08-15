---
name: MultiPeriodProductionPlanning
description: |
  Model and solve multi-period, multi-product production planning problems with inventory balance, time-varying resource capacities, and terminal inventory requirements using linear programming.

---

# Workflow 1 (OR-Tools / pywraplp)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' `pywraplp` interface to construct a linear programming model directly. It is well-suited for rapid prototyping and deployment in environments where a lightweight, Python-native solver interface is preferred. The model emphasizes clarity in variable and constraint definition, with explicit handling of time periods and product indices.

### Step 1 - Define Core Variables
- Define three core variable families: `production[p][t]`, `sales[p][t]`, and `inventory[p][t]` for each product `p` and period `t`. This separation clarifies material flow.
- Set variable bounds directly during creation. For `sales[p][t]`, use the upper bound `max_sales[p][t]`. For `inventory[p][t]`, use the upper bound `inventory_capacity`.

### Step 2 - Implement Inventory Balance Constraints
- For the initial period (`t=0`), add the constraint: `production[p][0] == sales[p][0] + inventory[p][0]`.
- For subsequent periods (`t>0`), add the flow constraint: `inventory[p][t-1] + production[p][t] == sales[p][t] + inventory[p][t]`.

### Step 3 - Enforce Resource and Inventory Limits
- For each resource `r` and period `t`, create a capacity constraint: `sum(resource_usage[p][r] * production[p][t] for p in products) <= resource_capacity[r][t]`.
- Add a terminal inventory equality constraint for the final period `T`: `inventory[p][T] == terminal_inventory_target[p]`.

### Step 4 - Formulate the Objective
- Define the objective to maximize profit: `sum( (unit_revenue[p] * sales[p][t]) - (holding_cost * inventory[p][t]) for p in products for t in periods )`.

### Formulation Template
```json
{
  "sets": [
    "products",
    "periods",
    "resources"
  ],
  "parameters": [
    "max_sales[product][period]",
    "unit_revenue[product]",
    "holding_cost",
    "resource_usage[product][resource]",
    "resource_capacity[resource][period]",
    "inventory_capacity",
    "terminal_inventory_target[product]"
  ],
  "decision_variables": [
    "production[product][period]",
    "sales[product][period]",
    "inventory[product][period]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(unit_revenue[p] * sales[p][t] - holding_cost * inventory[p][t])"
  },
  "constraints": [
    "inventory_balance_initial",
    "inventory_balance_subsequent",
    "resource_capacity[resource][period]",
    "terminal_inventory"
  ]
}
```

### Common Pitfalls
- Assuming feasibility without validating that sales bounds are compatible with inventory dynamics and terminal conditions, especially when production capacity is zero in some periods.
- Inconsistent handling of zero-capacity periods (e.g., using `-1` or `-1e-6`). Use a conditional: `if capacity[t] == 0: production_sum <= 0`.
- Not deriving implicit bounds from inventory equations (e.g., `inventory[t-1] <= capacity` implies a bound on `sales[t]`).

## Solving stage

### Strategy Overview
Solve the model using the CBC backend via `pywraplp`. Configure solver parameters for performance and reliability. After solving, rigorously check the solution status and verify all constraint families to ensure feasibility and correctness.

### Step 1 - Initialize Solver and Set Parameters
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver('CBC')`.
- Set practical limits: `solver.SetTimeLimit(time_limit_ms)` and `solver.SetNumThreads(num_threads)`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Check for `status == pywraplp.Solver.OPTIMAL` or `status == pywraplp.Solver.FEASIBLE`. If not, output a structured error message and avoid reading solution values.

### Step 3 - Extract and Verify Solution
- If the solve was successful, extract values using `variable.solution_value()`.
- Programmatically verify key constraint families (inventory balance, capacity limits, sales bounds, terminal inventory) against the extracted values to catch any solver inconsistencies.

### Step 4 - Report Production Plan
- Output the total objective value and a detailed, readable table of `production[p][t]`, `sales[p][t]`, and `inventory[p][t]` for all products and periods.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('CBC')
solver.SetTimeLimit(30000)  # 30 seconds
solver.SetNumThreads(4)

# ... (variable and constraint creation)
# ... (objective definition)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_profit = solver.Objective().Value()
    # Extract and print solution
    for p in products:
        for t in periods:
            prod_val = production[p][t].solution_value()
            # ... extract other variables
    print(f"Total Profit: {total_profit}")
else:
    print(f"Solver failed with status: {status}")
    # Optionally, implement infeasibility analysis here.
```

### Common Pitfalls
- Trusting a non-optimal or infeasible status and attempting to read solution values, which may be undefined or misleading.
- Not using solver time or iteration limits, risking long, unproductive runs.
- Outputting pseudo-numeric answers when the solver execution fails.

# Workflow 2 (Pyomo / SolverFactory)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo modeling language to declaratively define the optimization problem. It is ideal for complex, large-scale models where separation of model definition from solver execution is beneficial. The approach leverages Pyomo's `Set`, `Var`, `Constraint`, and `Objective` components for a clean, maintainable model structure.

### Step 1 - Declare Model Sets and Parameters
- Define Pyomo `Set` objects for `products`, `periods`, and `resources`.
- Declare all time-varying and product-specific parameters as dictionaries or rule-based `Param` objects (e.g., `machine_capacity[machine, period]`).

### Step 2 - Define Variables with Bounds and Domains
- Declare `pyo.Var` objects for `model.production`, `model.sales`, and `model.inventory`, indexed by the appropriate sets.
- Specify `domain=pyo.NonNegativeReals` and set bounds directly on the variable declaration where possible (e.g., `bounds=(0, inventory_capacity)` for inventory).

### Step 3 - Construct Constraints via Rules
- Implement inventory balance using constraint rules. For `t=0`, use a separate rule. For `t>0`, use a single rule with `pyo.Constraint.Skip` for the initial period.
- Create resource capacity constraints with a rule that sums `usage[p][r] * model.production[p,t]` across products for each resource and period.

### Step 4 - Formulate the Objective Expression
- Define a `pyo.Objective` with `sense=pyo.maximize`. The expression should be `sum(unit_revenue[p] * model.sales[p,t] - holding_cost * model.inventory[p,t])`.

### Formulation Template
```json
{
  "sets": [
    "model.P (products)",
    "model.T (periods)",
    "model.R (resources)"
  ],
  "parameters": [
    "model.max_sales (indexed by P, T)",
    "model.unit_revenue (indexed by P)",
    "model.holding_cost (scalar)",
    "model.resource_usage (indexed by P, R)",
    "model.resource_capacity (indexed by R, T)",
    "model.terminal_inventory_target (indexed by P)"
  ],
  "decision_variables": [
    "model.production (Var, indexed by P, T)",
    "model.sales (Var, indexed by P, T)",
    "model.inventory (Var, indexed by P, T)"
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(model.unit_revenue[p] * model.sales[p,t] - model.holding_cost * model.inventory[p,t] for p in model.P for t in model.T)"
  },
  "constraints": [
    "model.inventory_balance_initial (indexed by P)",
    "model.inventory_balance_subsequent (indexed by P, T, skip t=0)",
    "model.resource_capacity_constr (indexed by R, T)"
  ]
}
```

### Common Pitfalls
- Failing to correctly implement the `Constraint.Skip` logic in the inventory balance rule for the first period, leading to duplicate or incorrect constraints.
- Not validating parameter data compatibility (e.g., sales bounds exceeding what inventory dynamics allow given terminal conditions).
- Using a dummy objective (e.g., `expr=0`) for feasibility testing, which can mask conflicts. Use a meaningful objective to push against constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., CBC via `SolverFactory`). Configure solver options for deterministic performance. After solving, check both the solver status and model termination condition, then perform post-solution verification of constraints and resource utilization.

### Step 1 - Instantiate Solver and Configure
- Create the solver object: `solver = SolverFactory('cbc')`.
- Set solver options: `solver.options['ratio'] = 0.0` (for optimality gap), `solver.options['seconds'] = 30`, `solver.options['threads'] = 4`.

### Step 2 - Solve and Inspect Results
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `TerminationCondition.optimal` or `...feasible`.

### Step 3 - Verify Solution and Calculate Metrics
- If the solve was successful, load the solution into the model (`model.solutions.load_from(results)`).
- Programmatically iterate through constraints to verify satisfaction within a tolerance.
- Calculate actual vs. maximum resource utilization to identify binding constraints.

### Step 4 - Output Structured Results
- Print the objective value and a period-by-period plan. Optionally, output results as a structured dictionary or JSON for downstream processing.
- Implement fallback error handling to output solver status details if the solve fails.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=products)
model.T = pyo.Set(initialize=periods)
# ... (define parameters, variables, constraints, objective)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    total_profit = pyo.value(model.obj)
    # Access variable values: pyo.value(model.production[p,t])
    print(f"Total Profit: {total_profit}")
    # ... print detailed plan
else:
    print(f"Solver failed. Status: {results.solver.status}, Condition: {results.solver.termination_condition}")
    # Output structured error info
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or failed solves.
- Ignoring solver error messages or suggestions (e.g., for infeasibility analysis).
- Forgetting to load the solution into the model before accessing variable values, resulting in `None` or initial values.
