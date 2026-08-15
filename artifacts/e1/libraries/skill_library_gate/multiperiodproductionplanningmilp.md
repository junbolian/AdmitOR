---
name: MultiPeriodProductionPlanningMILP
description: |
  Model and solve multi-period production planning with setup costs as a mixed-integer linear program, using inventory balance, capacity constraints, and big-M linking, then solve with a MILP-capable solver and verify solution feasibility.
---

# Workflow 1 (OR-Tools / SCIP)

## Modeling stage

### Strategy Overview
Formulate the problem as a MILP using the OR-Tools (Python) API, defining variables and constraints directly within the solver's object model. This approach is procedural and tightly integrated with the solver's native constructs.

### Step 1 - Define Sets and Parameters
- Enumerate all products and time periods as lists or ranges.
- Define all time-varying parameters (demand, production cost, setup cost, holding cost, capacity, production limit, resource consumption) as dictionaries or 2D arrays indexed by product and period.

### Step 2 - Create Decision Variables
- Create continuous variables for production quantity `x[p,t]` and inventory level `I[p,t]` with lower bound 0.
- Create binary variables for setup indicator `y[p,t]`.
- Use the solver's `NumVar` and `BoolVar` methods within nested loops over products and periods.

### Step 3 - Formulate Inventory Balance Constraints
- For the first period, enforce `I[p,1] = x[p,1] - demand[p,1]` (assuming zero initial inventory).
- For subsequent periods, enforce `I[p,t] = I[p,t-1] + x[p,t] - demand[p,t]`.
- Add each equation as a linear constraint using the solver's `Add` method.

### Step 4 - Link Production to Setup with Big-M
- For each product-period pair, add the constraint `x[p,t] <= production_limit[p,t] * y[p,t]`.
- This ensures the binary variable `y[p,t]` is forced to 1 if `x[p,t] > 0`.

### Step 5 - Enforce Resource Capacity Constraints
- For each time period, sum the expression `resource_consumption[p] * x[p,t]` over all products.
- Add a linear constraint limiting this sum to be less than or equal to the period's capacity.

### Step 6 - Define the Objective Function
- Build the objective expression as the sum of production costs (`production_cost[p,t] * x[p,t]`), setup costs (`setup_cost[p,t] * y[p,t]`), and holding costs (`holding_cost[p,t] * I[p,t]`) over all products and periods.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": ["products", "periods"],
  "parameters": [
    "demand[product, period]",
    "production_cost[product, period]",
    "setup_cost[product, period]",
    "holding_cost[product, period]",
    "capacity[period]",
    "production_limit[product, period]",
    "resource_consumption[product]"
  ],
  "decision_variables": [
    "x[product, period] (continuous, >=0)",
    "I[product, period] (continuous, >=0)",
    "y[product, period] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(production_cost * x + setup_cost * y + holding_cost * I)"
  },
  "constraints": [
    "I[p,1] = x[p,1] - demand[p,1] for all p",
    "I[p,t] = I[p,t-1] + x[p,t] - demand[p,t] for all p, t>1",
    "x[p,t] <= production_limit[p,t] * y[p,t] for all p, t",
    "sum(resource_consumption[p] * x[p,t]) <= capacity[t] for all t"
  ]
}
```

### Common Pitfalls
- Using an overly large or loose value for the big-M coefficient (`production_limit`), which weakens the linear relaxation and slows solver performance.
- Forgetting to handle the initial inventory condition correctly, leading to infeasible or incorrect inventory trajectories.
- Not setting appropriate time limits or solver parameters, which can cause the solve to run indefinitely on large instances.

## Solving stage

### Strategy Overview
Instantiate a MILP-capable solver via OR-Tools, configure its parameters, build the model using the procedural steps, solve, and then rigorously check the solution status and feasibility.

### Step 1 - Solver Initialization and Configuration
- Create a solver instance using `pywraplp.Solver.CreateSolver('SCIP')` or `'CBC'`.
- Set performance parameters: `solver.SetTimeLimit(limit_in_milliseconds)`, `solver.SetNumThreads(number_of_threads)`.

### Step 2 - Build Model Programmatically
- Implement nested loops over products and periods to create variables and add constraints as defined in the modeling stage.
- Use `solver.Add()` for constraints and `solver.Objective().SetMinimization()` for the objective.

### Step 3 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:`.
- If optimal or feasible, retrieve the objective value via `solver.Objective().Value()`.

### Step 4 - Extract and Validate Solution
- Retrieve variable values using `.solution_value()` for each variable.
- Implement a post-solve verification function that recomputes inventory balances, checks capacity and setup constraints, and recalculates total cost within a small tolerance (e.g., 1e-6).

### Step 5 - Report Results
- Print the objective value and key solution metrics (total production, setups, inventory).
- Optionally, write results to a structured output format for further analysis.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(60000)  # 60 seconds
solver.SetNumThreads(4)

# Variable creation loops
x = {}
I = {}
y = {}
for p in products:
    for t in periods:
        x[p,t] = solver.NumVar(0, production_limit[p,t], f'x_{p}_{t}')
        I[p,t] = solver.NumVar(0, solver.infinity(), f'I_{p}_{t}')
        y[p,t] = solver.BoolVar(f'y_{p}_{t}')

# Add constraints (inventory, big-M, capacity)...
# Build objective...

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    # Extract and verify solution...
else:
    print('No feasible solution found.')
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing good solutions from early termination.
- Failing to verify the numerical feasibility of the retrieved solution due to solver tolerances.
- Omitting error handling for cases where the solver fails or hits the time limit.

# Workflow 2 (Pyomo / Highs)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo, defining abstract sets, parameters, and variables. This approach separates the model structure from data, promoting reusability and clean integration with various solvers like HiGHS.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for products and periods.
- Define `Param` objects for all required data, indexed by the appropriate sets, allowing data to be loaded separately.

### Step 2 - Define Decision Variables with Bounds
- Declare `Var` objects for production quantity `model.x`, inventory level `model.I`, and setup indicator `model.y`.
- Specify variable domains: `NonNegativeReals` for `x` and `I`, `Binary` for `y`.
- Set upper bounds for `model.x` directly using the `bounds` argument with the `production_limit` parameter.

### Step 3 - Construct Inventory Balance Constraints as Rules
- Create a Pyomo `Constraint` component with indexing over products and periods.
- Write a rule function that returns the inventory balance equation `model.I[p,t-1] + model.x[p,t] == demand[p,t] + model.I[p,t]` for `t>1`, handling the first period separately.

### Step 4 - Implement Big-M and Capacity Constraints
- Add a constraint rule `model.x[p,t] <= model.production_limit[p,t] * model.y[p,t]` for all product-period pairs.
- Add another constraint rule summing `resource_consumption[p] * model.x[p,t]` over products, limiting it to `capacity[t]` for each period.

### Step 5 - Formulate the Objective Function
- Use Pyomo's `Objective` component to minimize the sum of production, setup, and holding costs.
- Construct the expression by summing over the product and period sets using `sum()` or `quicksum()`.

### Formulation Template
```json
{
  "sets": ["model.P", "model.T"],
  "parameters": [
    "model.demand",
    "model.production_cost",
    "model.setup_cost",
    "model.holding_cost",
    "model.capacity",
    "model.production_limit",
    "model.resource_consumption"
  ],
  "decision_variables": [
    "model.x (NonNegativeReals, bounds)",
    "model.I (NonNegativeReals)",
    "model.y (Binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(production_cost * x + setup_cost * y + holding_cost * I)"
  },
  "constraints": [
    "InventoryBalance(p, t)",
    "SetupActivation(p, t)",
    "ResourceCapacity(t)"
  ]
}
```

### Common Pitfalls
- Incorrectly handling Pyomo rule function indexing, leading to constraints being skipped or applied to wrong indices.
- Defining parameters as concrete Python dictionaries instead of Pyomo `Param` objects, which limits model portability and data separation.
- Not using `quicksum` for large expressions within rules, which can cause significant performance overhead.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with the HiGHS solver, configure solver options for performance, solve the model, and then perform systematic solution verification and reporting.

### Step 1 - Solver Selection and Configuration
- Instantiate the solver: `solver = SolverFactory('highs')`.
- Set key options: `solver.options['time_limit'] = 60`, `solver.options['mip_rel_gap'] = 0.0001`, `solver.options['threads'] = 4`.

### Step 2 - Solve and Capture Results
- Call `results = solver.solve(model, tee=False)` (set `tee=True` to see solver log).
- Check the solver termination condition from `results.solver.termination_condition` (e.g., `optimal`, `feasible`, `maxTimeLimit`).

### Step 3 - Extract and Verify Solution Values
- Retrieve variable values using `pyo.value(model.x[p,t])`.
- Implement a verification function that checks all constraint categories (inventory, capacity, setup, bounds) numerically with a tolerance (e.g., 1e-6).

### Step 4 - Analyze and Report Solution
- Calculate and print a cost breakdown (production, setup, holding).
- Report key performance indicators like capacity utilization and number of setups.
- Output the total objective value in a parsable format (e.g., `RESULT:{total_cost}`).

### Step 5 - Validate Optimality (Optional)
- For confirmed optimal solutions, add a cut `model.obj <= current_best - epsilon` and re-solve; infeasibility confirms optimality.
- Monitor the solver log for gap closure and iteration count to assess solution quality.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=products)
model.T = pyo.Set(initialize=periods)
# Define parameters, variables, constraints, objective...

# solve with status / termination checks
solver = SolverFactory('highs')
solver.options['time_limit'] = 60
solver.options['mip_rel_gap'] = -1e-4
results = solver.solve(model)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    total_cost = pyo.value(model.obj)
    # Verify solution and report...
else:
    print(f'Solver terminated with status: {results.solver.termination_condition}')
```

### Common Pitfalls
- Relying solely on the solver's termination status without numerically verifying constraint satisfaction, which can miss numerical issues.
- Not setting an appropriate optimality gap (`mip_rel_gap`), leading to excessively long solve times or premature stopping.
- Forgetting to load data into Pyomo `Param` objects before solving, resulting in an uninitialized model.
