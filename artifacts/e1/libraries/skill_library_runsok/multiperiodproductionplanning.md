---
name: MultiPeriodProductionPlanning
description: |
  Model and solve multi-period, multi-product production planning problems with inventory balance, time-varying capacities, and profit maximization.
---

# Workflow 1 (OR-Tools LP with CBC)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using OR-Tools' linear solver wrapper. Define variables and constraints directly within the solver API, leveraging its efficient construction for large-scale LPs.

### Step 1 - Define Core Variables
- Create three non-negative decision variables per product and period: `production[p][t]`, `sales[p][t]`, and `inventory[p][t]`.
- Set variable bounds during creation for performance: `solver.NumVar(lb, ub, name)`.
- Use dictionaries or nested lists keyed by `(product, period)` for variable storage.

### Step 2 - Enforce Inventory Flow
- For the initial period (`t=0`), add the balance constraint: `production[p][0] == sales[p][0] + inventory[p][0]`.
- For subsequent periods (`t>0`), add the flow constraint: `inventory[p][t-1] + production[p][t] == sales[p][t] + inventory[p][t]`.

### Step 3 - Apply Operational Constraints
- Add sales upper bound constraints: `sales[p][t] <= max_sales[p][t]`.
- Add resource capacity constraints per machine type `m` and period `t`: `sum(usage[p][m] * production[p][t] for p in products) <= capacity[m][t]`.
- Add terminal inventory requirement: `inventory[p][final_period] == terminal_target[p]`.

### Step 4 - Formulate Objective
- Define the objective to maximize total profit: `sum(revenue[p] * sales[p][t] - holding_cost * inventory[p][t] for p in products for t in periods)`.
- Set coefficients using `objective.SetCoefficient(variable, coefficient)`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "machines"],
  "parameters": {
    "revenue": {"product": "value"},
    "holding_cost": "value",
    "max_sales": {"product": {"period": "value"}},
    "machine_capacity": {"machine": {"period": "value"}},
    "machine_usage": {"product": {"machine": "value"}},
    "terminal_target": {"product": "value"}
  },
  "decision_variables": [
    {"name": "production", "index": ["product", "period"], "type": "continuous", "lb": 0},
    {"name": "sales", "index": ["product", "period"], "type": "continuous", "lb": 0},
    {"name": "inventory", "index": ["product", "period"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[p] * sales[p][t] - holding_cost * inventory[p][t])"
  },
  "constraints": [
    {"name": "inventory_balance_initial", "expression": "production[p][0] == sales[p][0] + inventory[p][0]"},
    {"name": "inventory_balance_subsequent", "expression": "inventory[p][t-1] + production[p][t] == sales[p][t] + inventory[p][t]"},
    {"name": "sales_bound", "expression": "sales[p][t] <= max_sales[p][t]"},
    {"name": "resource_capacity", "expression": "sum(usage[p][m] * production[p][t]) <= capacity[m][t]"},
    {"name": "terminal_inventory", "expression": "inventory[p][final_period] == terminal_target[p]"}
  ]
}
```

### Common Pitfalls
- Forgetting to define separate inventory balance logic for the initial period (`t=0`).
- Incorrectly signing the holding cost in the objective (should be subtracted).
- Using unbounded inventory variables without a capacity limit, leading to unrealistic solutions.

## Solving stage

### Strategy Overview
Solve the built model using the CBC backend via OR-Tools' `pywraplp`. Configure solver options, check termination statuses comprehensively, and extract solution values systematically.

### Step 1 - Configure and Solve
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver("CBC")`.
- Set performance options: `solver.SetTimeLimit(time_limit_ms)`, `solver.SetNumThreads(num_threads)`.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Validate Solution Status
- Check for optimal or feasible status: `if status in (solver.OPTIMAL, solver.FEASIBLE):`.
- If infeasible, analyze by temporarily relaxing constraints (e.g., terminal inventory) to diagnose the conflict.
- For other statuses (e.g., `UNBOUNDED`), review variable bounds and objective coefficients.

### Step 3 - Extract and Verify Results
- Retrieve variable values using `.solution_value()`.
- Print a detailed plan (production, sales, inventory per period) for validation.
- Manually recompute the objective value from extracted results as a sanity check.
- Verify key constraints, especially inventory balance and capacity usage, with the extracted values.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("CBC")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# ... (variable and constraint creation as per Modeling Stage)

objective = solver.Objective()
# ... (set objective coefficients)
solver.Maximize(objective)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f"Objective value: {solver.Objective().Value()}")
    # Extract and print solution
    for p in products:
        for t in periods:
            prod_val = production[(p, t)].solution_value()
            # ... extract other variables
else:
    print("No optimal or feasible solution found.")
    # Analyze infeasibility
```

### Common Pitfalls
- Not setting a time limit for large instances, risking long runtimes.
- Assuming `OPTIMAL` is the only acceptable status; `FEASIBLE` solutions are often valid.
- Failing to manually verify the solution against the original constraints.

# Workflow 2 (Pyomo with Highs/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model paradigm, separating problem structure from data. This approach enhances readability, maintainability, and facilitates switching between solvers.

### Step 1 - Define Model Sets and Parameters
- Declare Pyomo Sets: `model.products`, `model.periods`, `model.machines`.
- Declare Pyomo Parameters for all input data (revenue, costs, capacities, usage coefficients, sales bounds, terminal targets).

### Step 2 - Create Decision Variables
- Define continuous, non-negative variables: `model.production`, `model.sales`, `model.inventory`.
- Set variable bounds directly in the definition (e.g., `bounds=(0, max_inventory)`).

### Step 3 - Build Constraints with Rule Functions
- Define a Pyomo `Constraint` with a rule function for inventory balance, using `model.periods.first()` to handle the initial period logic.
- Define separate constraint rules for sales bounds and resource capacities, iterating over the appropriate sets.
- Implement the terminal inventory requirement as a simple equality constraint rule.

### Step 4 - Construct the Objective
- Define the objective expression using Pyomo's `summation` or a generator: `sum(model.revenue[p] * model.sales[p,t] - model.holding_cost * model.inventory[p,t] for ...)`.
- Use `model.obj = pyo.Objective(expr=expr, sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "machines"],
  "parameters": {
    "revenue": {"product": "value"},
    "holding_cost": "value",
    "max_sales": {"product": {"period": "value"}},
    "machine_capacity": {"machine": {"period": "value"}},
    "machine_usage": {"product": {"machine": "value"}},
    "terminal_target": {"product": "value"}
  },
  "decision_variables": [
    {"name": "production", "index": ["product", "period"], "type": "pyo.Var", "domain": "pyo.NonNegativeReals"},
    {"name": "sales", "index": ["product", "period"], "type": "pyo.Var", "domain": "pyo.NonNegativeReals"},
    {"name": "inventory", "index": ["product", "period"], "type": "pyo.Var", "domain": "pyo.NonNegativeReals", "bounds": [0, "max_inventory"]}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[p] * sales[p][t] - holding_cost * inventory[p][t])"
  },
  "constraints": [
    {"name": "inventory_balance", "rule": "rule_inventory_balance"},
    {"name": "sales_bound", "rule": "rule_sales_bound"},
    {"name": "resource_capacity", "rule": "rule_resource_capacity"},
    {"name": "terminal_inventory", "rule": "rule_terminal_inventory"}
  ]
}
```

### Common Pitfalls
- Defining constraint rules that incorrectly index over the first period for the subsequent period balance equation.
- Using mutable Python data structures (lists/dicts) directly inside Pyomo rules; use `model.param[index]` instead.
- Forgetting to deactivate constraints during infeasibility debugging, making it hard to isolate issues.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., Highs or CBC). Leverage Pyomo's standardized interface for setting options, retrieving results, and performing post-solve validation.

### Step 1 - Instantiate and Configure Solver
- Create a solver object: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set solver options: `solver.options["time_limit"] = time_limit`, `solver.options["threads"] = num_threads`.

### Step 2 - Solve and Check Termination
- Execute `results = solver.solve(model, tee=False)`.
- Check the solve status: `pyo.check_optimal_termination(results)` or manually verify `results.solver.status == pyo.SolverStatus.ok` and `results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}`.

### Step 3 - Extract and Analyze Solution
- Access variable values using `pyo.value(model.variable[index])` or `model.variable[index].value`.
- Print a formatted production plan and compute actual resource usage.
- Implement a post-solve validation function that checks all constraints using the extracted values to ensure numerical satisfaction.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
# ... (define sets, parameters, variables, constraints, objective as per Modeling Stage)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["threads"] = 4

results = solver.solve(model)

if pyo.check_optimal_termination(results):
    print(f"Solver status: {results.solver.status}")
    # Extract solution
    for p in model.products:
        for t in model.periods:
            prod_val = pyo.value(model.production[p, t])
            # ... extract other variables
else:
    print("Solve failed or no feasible solution.")
    # Analyze results object for infeasibility clues
```

### Common Pitfalls
- Relying solely on `check_optimal_termination` and missing feasible but non-optimal solutions.
- Not using `pyo.value()` to safely extract variable values, which may be `None` if the solve failed.
- Ignoring the `tee=True` option for smaller problems, which provides valuable solver log output.
