---
name: Multi-Stage Resource Allocation with Bounded Production
description: |
  Model and solve linear production planning problems with resource capacity constraints, production bounds, and profit maximization using structured optimization frameworks.
---

# Workflow 1 (Solver-Specific API: Google OR-Tools)

## Modeling stage

### Strategy Overview
Directly construct the optimization model using a solver's native API (e.g., OR-Tools), embedding bounds within variable definitions and building constraints via coefficient loops. This approach is procedural and tightly coupled to the solver's object model.

### Step 1 - Define Index Sets and Data Structures
- Create lists for product and stage indices to organize data and enable systematic iteration.
- Store problem parameters (profit, min/max production, stage capacity) in dictionaries or lists indexed by these sets.
- Represent the time requirement matrix as a 2D list `time_required[stage][product]` for clear coefficient mapping.

### Step 2 - Create Decision Variables with Embedded Bounds
- Instantiate decision variables using `solver.NumVar(lower_bound, upper_bound, name)` for continuous production quantities.
- For integer production requirements, use `solver.IntVar(lower_bound, upper_bound, name)`.
- Store variables in a list or dictionary indexed by product for easy access.

### Step 3 - Formulate Resource Capacity Constraints
- For each stage, create a linear inequality constraint: `solver.Constraint(0, stage_capacity[s])`.
- Within a nested loop, set the coefficient for each product variable using `constraint.SetCoefficient(x[p], time_required[s][p])`.
- This builds the constraint `sum(time_required[s][p] * x[p]) <= stage_capacity[s]`.

### Step 4 - Set Linear Profit Maximization Objective
- Create a linear objective object using `solver.Objective()`.
- For each product, set its coefficient: `objective.SetCoefficient(x[p], profit[p])`.
- Call `objective.SetMaximization()` to define the optimization sense.

### Formulation Template
```json
{
  "sets": ["products", "stages"],
  "parameters": {
    "profit": {"index": "products"},
    "min_production": {"index": "products"},
    "max_production": {"index": "products"},
    "stage_capacity": {"index": "stages"},
    "time_required": {"index": ["stages", "products"]}
  },
  "decision_variables": [
    {"name": "x", "index": "products", "type": "NonNegativeContinuous", "bounds": ["min_production", "max_production"]}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[p] * x[p] for p in products)"
  },
  "constraints": [
    {"name": "resource_capacity", "index": "stages", "expression": "sum(time_required[s][p] * x[p] for p in products) <= stage_capacity[s]"}
  ]
}
```

### Common Pitfalls
- Manually recalculating constraint slacks or shadow prices that the solver can provide directly (e.g., `constraint.dual_value()`).
- Creating separate verification scripts that duplicate the model's constraint logic, violating DRY principles.
- Hardcoding tolerance values (e.g., `1e-6`) without considering the problem's numerical scale.

## Solving stage

### Strategy Overview
Configure the solver with practical limits, solve the model, and perform robust post-solution validation including status checks, feasibility verification, and optimality gap analysis.

### Step 1 - Configure and Execute Solver
- Instantiate the appropriate solver: `pywraplp.Solver.CreateSolver("GLOP")` for LP or `"CBC"` for MIP.
- Set practical runtime limits: `solver.SetTimeLimit(milliseconds)`.
- Configure parallel processing if supported: `solver.SetNumThreads(number_of_threads)`.
- Call `solver.Solve()` to obtain the solution status.

### Step 2 - Validate Solution Status and Extract Values
- Check if the status is `OPTIMAL` or `FEASIBLE` before extracting results.
- Extract the objective value using `objective.Value()`.
- Retrieve variable values via `variable.solution_value()` and store them in a structured format.

### Step 3 - Perform Post-Solution Analysis and Verification
- Compute actual resource usage per stage and compare against capacity to verify feasibility within a small tolerance.
- For integer models, compare the objective value to the continuous relaxation to assess the integrality gap.
- Identify binding constraints by checking if resource usage equals capacity (within tolerance).
- Extract sensitivity information (reduced costs, shadow prices) if available for interpretation.

### Step 4 - Output Standardized Results
- Print the objective value with a clear prefix (e.g., `RESULT:{total_profit}`).
- Output a detailed breakdown of production quantities and constraint utilization percentages.
- Include a summary of binding constraints and variables at their bounds.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
x = {}
for p in products:
    x[p] = solver.NumVar(min_production[p], max_production[p], f"x_{p}")
# ... add constraints and objective as described in Modeling stage

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_profit = objective.Value()
    print(f"RESULT:{total_profit}")
    # Extract and validate solution
    x_vals = {p: x[p].solution_value() for p in products}
    # ... perform verification and analysis
else:
    print("RESULT_JSON:{\"status\": \"failed\", \"reason\": \"infeasible_or_error\"}")
```

### Common Pitfalls
- Running multiple verification solves with identical parameters instead of analyzing the first solve's output comprehensively.
- Implementing custom optimality checks that duplicate the solver's own termination condition reporting.
- Using negative tolerance values (e.g., `-1e-8`) in an attempt to force optimality, which is mathematically meaningless.

# Workflow 2 (Modeling Language: Pyomo)

## Modeling stage

### Strategy Overview
Declaratively define the optimization model using a modeling language (Pyomo), separating the model structure from data via sets, parameters, and rule functions. This approach promotes clarity, maintainability, and solver independence.

### Step 1 - Define Abstract Model Structure with Sets
- Create a `ConcreteModel` and define `Set` objects for products and stages to structure the model.
- Use these sets to index all parameters, variables, and constraints, ensuring scalability.

### Step 2 - Declare Parameters and Decision Variables
- Define `Param` objects for all input data (profit, bounds, capacities, time matrix), indexed by the appropriate sets.
- Create decision variables as `Var` objects with domain `NonNegativeReals` (or `NonNegativeIntegers`).
- Enforce lower and upper bounds directly within the variable declaration or via separate constraints for clarity.

### Step 3 - Formulate Constraints via Rule Functions
- Implement resource capacity constraints as `Constraint` objects with a rule function that returns `sum(time_required[s,p] * model.x[p] for p in model.products) <= stage_capacity[s]`.
- Implement production bound constraints similarly, using rule functions for clarity and separation of logic.
- This declarative approach clearly separates the constraint expression from its construction.

### Step 4 - Define the Linear Objective
- Create an `Objective` object with `sense=maximize`.
- Define the expression as `sum(profit[p] * model.x[p] for p in model.products)` within a rule function.

### Formulation Template
```json
{
  "sets": ["products", "stages"],
  "parameters": [
    {"name": "profit", "index": ["products"]},
    {"name": "min_production", "index": ["products"]},
    {"name": "max_production", "index": ["products"]},
    {"name": "stage_capacity", "index": ["stages"]},
    {"name": "time_required", "index": ["stages", "products"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["products"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(profit[p] * x[p] for p in products)"
  },
  "constraints": [
    {"name": "production_lower_bound", "index": ["products"], "expression": "x[p] >= min_production[p]"},
    {"name": "production_upper_bound", "index": ["products"], "expression": "x[p] <= max_production[p]"},
    {"name": "stage_capacity", "index": ["stages"], "expression": "sum(time_required[s,p] * x[p] for p in products) <= stage_capacity[s]"}
  ]
}
```

### Common Pitfalls
- Creating unnecessary intermediate JSON formulations that serialize complex data structures, adding abstraction without benefit.
- Defining constraint rules that perform complex calculations instead of simple linear expressions, reducing solver performance.
- Hardcoding indices or parameter values within rule functions, limiting model reusability.

## Solving stage

### Strategy Overview
Select a suitable solver backend (e.g., HiGHS, CBC), configure it for reliable performance, solve the model, and implement robust checks for solution status and feasibility before extracting and analyzing results.

### Step 1 - Select and Configure Solver
- Instantiate a solver factory: `SolverFactory("highs")` for LP or `"cbc"` for MIP.
- Configure solver options: enable presolve (`presolve: True`), set a time limit (`time_limit: 30`), and specify optimality tolerance (`mip_rel_gap: 0.0` for exact solutions).
- Avoid setting redundant options (like `threads`) if the solver manages them automatically.

### Step 2 - Solve and Check Termination Status
- Execute `solver.solve(model, tee=False)` (or `tee=True` for debugging output).
- Verify the solver status is `SolverStatus.ok` and the termination condition is `optimal` or `feasible` before proceeding.
- Handle infeasible or error statuses gracefully with informative output.

### Step 3 - Extract and Validate Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Retrieve variable values into a dictionary: `x_vals = {p: pyo.value(model.x[p]) for p in model.products}`.
- Programmatically compute constraint slacks and resource utilization to verify feasibility within tolerance.
- For integer variables, cast extracted values to `int()` if discrete units are required.

### Step 4 - Perform Post-Optimal Analysis
- Identify binding constraints by checking if slack is near zero (within `1e-6` relative to the right-hand side).
- Determine which variables are at their lower or upper bounds.
- Compare LP relaxation and integer solution objectives to assess integrality gap when applicable.

### Step 5 - Output Structured Results
- Print the objective value with a standardized prefix.
- Provide a clear summary of production quantities, constraint utilization, and binding status.
- Ensure the reported total profit matches the sum of individual product contributions for consistency.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.products = pyo.Set(initialize=products)
model.stages = pyo.Set(initialize=stages)
# ... define parameters, variables, objective, and constraints as per Modeling stage

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)
status = results.solver.status
term = results.solver.termination_condition

if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    total_profit = pyo.value(model.obj)
    print(f"RESULT:{total_profit}")
    # ... extract, validate, and analyze solution
else:
    print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'reason': str(term)})}")
```

### Common Pitfalls
- Making multiple solver calls for verification when a single solve with comprehensive post-processing is sufficient.
- Assuming solver capabilities (e.g., shadow price availability) without verifying through the modeling interface.
- Writing complex constraint analysis loops that duplicate the solver's sensitivity analysis functions.
