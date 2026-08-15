---
name: Multi-Product Resource-Constrained Production Planning
description: |
  Formulate and solve integer linear programs for maximizing profit subject to individual product bounds and shared resource capacity.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (OR-Tools) for explicit model construction, where variable bounds are defined at creation and constraints are added individually. It is well-suited for rapid prototyping and deployment in environments where a compiled, high-performance solver is preferred.

### Step 1 - Define Indexed Data Structures
- Store all problem parameters in parallel lists or dictionaries, indexed by a common product identifier (e.g., `product_index`).
- Include `profit_coefficient`, `resource_consumption_per_unit`, `lower_bound`, and `upper_bound` for each product.
- Use a placeholder `total_resource_capacity` for the shared resource limit.

### Step 2 - Create Integer Variables with Bounds
- For each product, instantiate a non-negative integer decision variable using `solver.IntVar(lower_bound, upper_bound, name)`.
- This directly encodes individual product bounds into the variable's domain, reducing the number of explicit constraints.

### Step 3 - Formulate Linear Constraints
- Create a linear resource capacity constraint: `sum(resource_consumption_per_unit[i] * variable[i]) <= total_resource_capacity`.
- Use a generator expression or loop to build the sum for clarity and maintainability.

### Step 4 - Define Linear Objective
- Build the objective function as `sum(profit_coefficient[i] * variable[i])`.
- Explicitly set the sense to maximization.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": [
    {"name": "profit", "index": "products"},
    {"name": "resource_usage", "index": "products"},
    {"name": "min_production", "index": "products"},
    {"name": "max_production", "index": "products"},
    {"name": "total_capacity", "index": null}
  ],
  "decision_variables": [
    {"name": "x", "index": "products", "domain": "nonnegative_integers"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in products)"
  },
  "constraints": [
    {"name": "resource_limit", "expression": "sum(resource_usage[i] * x[i] for i in products) <= total_capacity"}
  ]
}
```

### Common Pitfalls
- Forgetting to set variable bounds, leading to an unbounded or incorrectly bounded problem.
- Mismatching indices between parameter lists and variable arrays, causing incorrect coefficient assignment.
- Using `solver.IntVar(0, solver.infinity(), name)` without later adding explicit bound constraints, which violates individual product limits.

## Solving stage

### Strategy Overview
Solving involves configuring the CBC MIP solver through the OR-Tools interface, executing the solve, and robustly handling the solution status to extract and validate results.

### Step 1 - Configure Solver and Set Parameters
- Instantiate the solver with `pywraplp.Solver.CreateSolver('CBC')`.
- Set a time limit (e.g., `solver.SetTimeLimit(30000)`) and the number of threads (e.g., `solver.SetNumThreads(4)`) to manage performance.

### Step 2 - Solve and Check Status
- Execute `solver.Solve()`.
- Check the result status for `OPTIMAL` or `FEASIBLE` to determine if a usable solution was found. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error messages.

### Step 3 - Extract and Verify Solution
- If the status is acceptable, retrieve the objective value with `solver.Objective().Value()`.
- Iterate through decision variables to collect their `.solution_value()`.
- Programmatically verify the solution by recalculating total resource usage and checking against bounds and capacity.

### Step 4 - Package Output
- Return results in a structured format (e.g., JSON) containing the status, objective value, variable values, and derived metrics.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('CBC')
# ... (variable and constraint creation as per modeling stage)
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# solve with status / termination checks
result_status = solver.Solve()
if result_status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    solution = {var.name(): var.solution_value() for var in variable_list}
    # ... (verification and output packaging)
else:
    # Handle infeasible, unbounded, or other error statuses
    print(f"Solver finished with status: {result_status}")
```

### Common Pitfalls
- Assuming `OPTIMAL` is the only acceptable status; `FEASIBLE` solutions from time-limited runs are often valuable.
- Not verifying that extracted variable values are integers, as solvers may return fractional values within tolerance.
- Omitting the time limit, which can cause the solver to run indefinitely on large or complex instances.

# Workflow 2 (Modeling Framework - Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to declaratively define sets, parameters, variables, and constraints. It promotes solver-agnostic, maintainable code and is ideal for complex models or research where switching solvers is necessary.

### Step 1 - Declare Abstract Model Components
- Define a `Set` for products to index all model components.
- Declare `Param`eters for `profit`, `resource_usage`, `min_production`, `max_production`, and `total_capacity`.

### Step 2 - Define Variables and Explicit Bound Constraints
- Create a `Var` indexed by the product set with domain `pyo.NonNegativeIntegers`.
- Create two explicit `Constraint` rules: one for lower bounds (`model.x[i] >= model.min_production[i]`) and one for upper bounds (`model.x[i] <= model.max_production[i]`). This enhances model clarity and debugging.

### Step 3 - Formulate Objective and Resource Constraint
- Define an `Objective` rule to maximize `sum(model.profit[i] * model.x[i] for i in model.products)`.
- Add a `Constraint` rule for the resource limit: `sum(model.resource_usage[i] * model.x[i] for i in model.products) <= model.total_capacity`.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": [
    {"name": "profit", "index": "products"},
    {"name": "resource_usage", "index": "products"},
    {"name": "min_production", "index": "products"},
    {"name": "max_production", "index": "products"},
    {"name": "total_capacity", "index": null}
  ],
  "decision_variables": [
    {"name": "x", "index": "products", "domain": "nonnegative_integers"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in products)"
  },
  "constraints": [
    {"name": "min_bound", "expression": "x[i] >= min_production[i] for i in products"},
    {"name": "max_bound", "expression": "x[i] <= max_production[i] for i in products"},
    {"name": "resource_limit", "expression": "sum(resource_usage[i] * x[i] for i in products) <= total_capacity"}
  ]
}
```

### Common Pitfalls
- Using variable bounds (e.g., `bounds=(min, max)`) instead of explicit constraints, which can make it harder to inspect and debug bound violations.
- Incorrectly indexing parameters within constraint rules, leading to `KeyError` or silent model errors.
- Forgetting to initialize all parameters before creating a `ConcreteModel`, resulting in uninitialized data errors.

## Solving stage

### Strategy Overview
Solving with Pyomo involves instantiating a solver object (e.g., CBC via `pyo.SolverFactory`), configuring it, executing the solve, and carefully loading and checking the solution status before extracting results.

### Step 1 - Instantiate and Configure Solver
- Create a solver instance: `solver = pyo.SolverFactory('cbc')`.
- Set solver options such as time limit (`seconds`), optimality gap (`ratio`), and threads.

### Step 2 - Solve with Status Checking
- Execute `results = solver.solve(model, tee=False, load_solutions=False)`.
- First, check the solver status (`results.solver.status`) is `ok`. Then, check the termination condition (`results.solver.termination_condition`) for `optimal` or `feasible`.

### Step 3 - Load and Validate Solution
- Only if the termination condition is acceptable, load the solution into the model: `model.solutions.load_from(results)`.
- Extract variable values using `pyo.value(model.x[i])` and the objective value using `pyo.value(model.objective)`.
- Recompute key metrics (total resource used) to validate constraint satisfaction.

### Step 4 - Implement Fallback and Analysis
- For infeasible or error statuses, provide a structured fallback output (e.g., JSON with `"status": "failed"`).
- Optionally, perform post-solve analysis, such as calculating profit-to-resource ratios to understand solution drivers.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, params, vars, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False, load_solutions=False)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
        model.solutions.load_from(results)
        objective_value = pyo.value(model.objective)
        solution = {i: pyo.value(model.x[i]) for i in model.products}
        # ... (verification and output)
    else:
        print(f"Solver terminated with condition: {results.solver.termination_condition}")
else:
    print("Solver failed.")
```

### Common Pitfalls
- Loading the solution (`load_solutions=True`) before checking termination condition, which may load an infeasible or suboptimal point and cause errors.
- Misinterpreting the `optimal` termination condition; a non-zero optimality gap may still return `optimal` if the gap tolerance is met.
- Not setting a time limit, which can lead to excessively long solve times for difficult instances.
