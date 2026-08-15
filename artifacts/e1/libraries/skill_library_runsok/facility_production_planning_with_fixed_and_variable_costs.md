---
name: Facility Production Planning with Fixed and Variable Costs
description: |
  Model and solve multi-period production planning problems with facility operation decisions, linking binary and continuous variables via Big-M constraints to minimize total fixed and variable costs while satisfying demand.

---

# Workflow 1 (Direct Solver API - OR-Tools / Pywraplp)

## Modeling stage

### Strategy Overview
This workflow uses a direct, low-level solver API (e.g., OR-Tools' `pywraplp`) for explicit control over variable and constraint creation. It is ideal for tightly integrated applications where performance and direct manipulation of the model are priorities.

### Step 1 - Define Core Sets and Parameters
- Gather the list of production facilities and planning time periods.
- Collect cost parameters (`fixed_cost`, `variable_cost`), capacity parameters (`min_production`, `max_production`), and demand per period.

### Step 2 - Create Binary-Continuous Variable Pairs
- For each facility and time period, create a binary variable `operate[f,t]` (0/1) representing the on/off decision.
- Create a continuous variable `production[f,t]` (≥0) representing the production quantity, with an explicit upper bound of `max_production[f]`.

### Step 3 - Implement Big-M Linking Constraints
- Add a lower bound constraint: `production[f,t] >= min_production[f] * operate[f,t]`. This enforces minimum production if the facility is open.
- Add an upper bound constraint: `production[f,t] <= max_production[f] * operate[f,t]`. This forces production to zero if closed and respects capacity.

### Step 4 - Enforce Demand Satisfaction
- For each time period, create a constraint summing `production[f,t]` across all facilities, requiring it to be greater than or equal to the period's demand.

### Step 5 - Formulate Linear Objective
- Construct the objective to minimize the sum of fixed costs (`fixed_cost[f] * operate[f,t]`) and variable costs (`variable_cost[f] * production[f,t]`) across all facilities and periods.

### Formulation Template
```json
{
  "sets": [
    "facilities",
    "time_periods"
  ],
  "parameters": [
    "fixed_cost[facilities]",
    "variable_cost[facilities]",
    "min_production[facilities]",
    "max_production[facilities]",
    "demand[time_periods]"
  ],
  "decision_variables": [
    "operate[facilities, time_periods] ∈ {0,1}",
    "production[facilities, time_periods] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_f ∑_t (fixed_cost[f] * operate[f,t] + variable_cost[f] * production[f,t])"
  },
  "constraints": [
    "production_linking_lower[f,t]: production[f,t] ≥ min_production[f] * operate[f,t]",
    "production_linking_upper[f,t]: production[f,t] ≤ max_production[f] * operate[f,t]",
    "demand_satisfaction[t]: ∑_f production[f,t] ≥ demand[t]"
  ]
}
```

### Common Pitfalls
- Forgetting to set an explicit upper bound on the continuous `production` variable, which can slow down the solver.
- Using an overly large or small value for `min_production` in the linking constraint, which can weaken the formulation.
- Not verifying that the sum of `max_production` across facilities can meet demand, leading to infeasibility.

## Solving stage

### Strategy Overview
Solve the model using a MIP-capable solver backend (e.g., SCIP, CBC) via a direct API. Focus on configuring solver limits, extracting solutions, and performing validation checks.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver instance (e.g., `Solver.CreateSolver("SCIP")`).
- Set practical limits: `SetTimeLimit(ms)`, `SetNumThreads(n)`, and enable verbose output if needed for debugging.

### Step 2 - Build Model from Formulation
- Translate the formulation into solver API calls: create variables, set objective coefficients, and add constraints using nested loops over facilities and periods.

### Step 3 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the result status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.) before proceeding.

### Step 4 - Extract and Validate Solution
- If optimal or feasible, retrieve the objective value.
- Extract values for `operate` and `production` variables. For binary variables, apply a threshold (e.g., `> 0.5`) to interpret the solution.
- Programmatically verify that all constraints (demand, min/max production) are satisfied within a small tolerance.

### Step 5 - Report Solution and Costs
- Output a summary: operational schedule, production quantities, and a breakdown of fixed versus variable costs.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)  # 30 seconds
# ... create variables, objective, constraints ...

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    # Extract and validate variable values
    for f in facilities:
        for t in time_periods:
            op_val = operate[f,t].solution_value()
            prod_val = production[f,t].solution_value()
            # Validation checks...
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Attempting to access `.solution_value()` on variables before confirming the solve status is `OPTIMAL` or `FEASIBLE`.
- Not using a tolerance (e.g., `1e-6`) when checking constraint satisfaction, leading to false failures due to numerical precision.
- Setting conflicting solver parameters (like both `SetTimeLimit` and an optimality gap) without understanding their interaction.

# Workflow 2 (Modeling Language - Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses a high-level modeling language (Pyomo) to declaratively define the optimization problem. It separates the model definition from the solver interface, improving readability, maintainability, and ease of modification for similar problems.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for `facilities` and `time_periods`.
- Define `Param` objects for all input data (`fixed_cost`, `variable_cost`, `min_production`, `max_production`, `demand`), initializing them from dictionaries.

### Step 2 - Define Decision Variables with Domains
- Declare `operate` as a `pyo.Var` with `domain=pyo.Binary`, indexed over facilities and periods.
- Declare `production` as a `pyo.Var` with `domain=pyo.NonNegativeReals`, similarly indexed.

### Step 3 - Construct Constraints via Rules
- Create a `Constraint` for the lower production link, using a rule that returns `model.production[f,t] >= model.min_production[f] * model.operate[f,t]`.
- Create a `Constraint` for the upper production link with a similar rule.
- Create a `Constraint` for demand satisfaction per period, using a rule that sums `model.production[f,t]` across facilities.

### Step 4 - Formulate the Objective Expression
- Define an `Objective` with `sense=pyo.minimize`.
- The expression should be the sum over all indices of `fixed_cost[f] * operate[f,t] + variable_cost[f] * production[f,t]`.

### Formulation Template
```json
{
  "sets": [
    "facilities",
    "time_periods"
  ],
  "parameters": [
    "fixed_cost[facilities]",
    "variable_cost[facilities]",
    "min_production[facilities]",
    "max_production[facilities]",
    "demand[time_periods]"
  ],
  "decision_variables": [
    "operate[facilities, time_periods] ∈ {0,1}",
    "production[facilities, time_periods] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_f ∑_t (fixed_cost[f] * operate[f,t] + variable_cost[f] * production[f,t])"
  },
  "constraints": [
    "production_linking_lower[f,t]: production[f,t] ≥ min_production[f] * operate[f,t]",
    "production_linking_upper[f,t]: production[f,t] ≤ max_production[f] * operate[f,t]",
    "demand_satisfaction[t]: ∑_f production[f,t] ≥ demand[t]"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters within constraint rules, leading to `KeyError` or using wrong values.
- Defining constraints with mutable operations inside the rule that cause side effects; rules should be pure functions of the model.
- Not initializing all parameters before creating the model, which results in an incomplete or erroneous instance.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with a solver (e.g., CBC, HiGHS). Leverage Pyomo's utilities for solution querying and validation, handling solver status and termination conditions robustly.

### Step 1 - Create Solver Instance and Configure Options
- Instantiate the solver: `solver = SolverFactory('cbc')`.
- Set key options: `seconds` for time limit, `ratio` for optimality gap (use `0.0` for optimality), and `threads` for parallelism if supported.

### Step 2 - Solve and Inspect Results Object
- Call `results = solver.solve(model, tee=False)` to solve. Use `tee=True` for verbose output.
- Inspect the `results` object: check `results.solver.status` and `results.solver.termination_condition`.

### Step 3 - Validate Solution and Extract Values
- If status is `ok` and termination is `optimal` or `feasible`, proceed.
- Use `pyo.value(model.operate[f,t])` and `pyo.value(model.production[f,t])` to extract variable values.
- Implement a verification function to check demand satisfaction and production bounds against the extracted values with a tolerance.

### Step 4 - Perform Cost Breakdown and Reporting
- Calculate total fixed cost (`sum(fixed_cost[f] * operate_value[f,t])`) and total variable cost separately for analysis.
- Generate a readable report of the operational schedule and production plan.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    # Extract and validate solution
    for f in model.facilities:
        for t in model.time_periods:
            op_val = pyo.value(model.operate[f,t])
            prod_val = pyo.value(model.production[f,t])
            # Validation checks...
else:
    print("Solve failed or no feasible solution found.")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition` before accessing variable values, which can lead to errors on infeasible or unbounded models.
- Setting solver options incorrectly for the chosen backend (e.g., using `mip_gap` for CBC instead of `ratio`).
- Assuming extracted binary variable values are exactly 0 or 1; they may be fractional due to numerical tolerances, so thresholding (`> 0.5`) is necessary.
