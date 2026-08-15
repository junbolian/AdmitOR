---
name: Production Planning with Resource Constraints
description: |
  Model and solve linear production planning problems with resource capacity constraints, production bounds, and profit maximization objectives using both OR-Tools and Pyomo frameworks.
---

# Workflow 1 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools for a direct, imperative modeling style. Variables and constraints are built via a solver API, suitable for rapid prototyping and deployment in environments where Pyomo is not available. It emphasizes explicit bound setting during variable creation and matrix-based constraint formulation.

### Step 1 - Define Data Structures
- Organize problem parameters as indexed lists or dictionaries for products and resources.
- Store unit profits, minimum/maximum production bounds, and resource capacities in flat lists.
- Represent resource consumption (e.g., time per unit) as a 2D list `resource_consumption[resource_index][product_index]`.

### Step 2 - Create Solver and Variables
- Instantiate a linear solver (e.g., `pywraplp.Solver.CreateSolver('GLOP')` for LP, `'CBC'` for MIP).
- Create decision variables for production quantities. Use `solver.NumVar(lower_bound, upper_bound, name)` for continuous variables or `solver.IntVar` for integer variables, directly encoding production bounds.

### Step 3 - Formulate Resource Constraints
- For each resource, create a linear constraint `solver.Constraint(0, resource_capacity)`.
- Iterate over products, setting coefficients using `constraint.SetCoefficient(variable, resource_consumption[resource][product])`.

### Step 4 - Set Objective Function
- Create the objective with `solver.Objective()`.
- For each product, set the coefficient to its unit profit using `objective.SetCoefficient(variable, profit[product])`.
- Specify maximization via `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["products", "resources"],
  "parameters": {
    "profit": "list indexed by product",
    "min_production": "list indexed by product",
    "max_production": "list indexed by product",
    "resource_capacity": "list indexed by resource",
    "resource_consumption": "2D list [resource][product]"
  },
  "decision_variables": ["production_quantity[product] (continuous or integer)"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[p] * production_quantity[p] for p in products)"
  },
  "constraints": [
    "lower_bound: production_quantity[p] >= min_production[p] for p in products",
    "upper_bound: production_quantity[p] <= max_production[p] for p in products",
    "resource_capacity: sum(resource_consumption[r][p] * production_quantity[p] for p in products) <= resource_capacity[r] for r in resources"
  ]
}
```

### Common Pitfalls
- Forgetting to set the objective sense to maximization, leading to a default minimization.
- Incorrectly ordering indices in the 2D consumption matrix, causing wrong constraint coefficients.
- Using `NumVar` when integer production is required, yielding impractical fractional solutions.

## Solving stage

### Strategy Overview
Solving involves executing the model, rigorously checking solver status, and validating the solution's feasibility and optimality. Post-solution analysis includes constraint verification and bottleneck identification.

### Step 1 - Execute Solve and Check Status
- Call `solver.Solve()` and capture the status code.
- Check for `pywraplp.Solver.OPTIMAL` or `FEASIBLE` status before proceeding. Handle infeasible or unbounded statuses with appropriate error messages.

### Step 2 - Extract and Validate Solution
- Extract variable values using `variable.solution_value()`.
- Recalculate resource usage and production totals to verify no constraint violations exist within a small tolerance (e.g., 1e-6).
- Compare extracted objective value with a recomputed sum of profits for consistency.

### Step 3 - Perform Post-Optimality Analysis
- Compute utilization percentages for each resource (`used_capacity / total_capacity * 100`) to identify bottlenecks.
- For LP problems, optionally extract reduced costs and dual values for sensitivity analysis.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... variable and constraint creation ...

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    for p in products:
        prod_val = production_vars[p].solution_value()
        # ... process solution ...
    # Validate
    for r in resources:
        used = sum(resource_consumption[r][p] * production_vars[p].solution_value() for p in products)
        if used > resource_capacity[r] + 1e-6:
            print(f"Validation failed for resource {r}")
else:
    print(f"Solver did not find an optimal solution. Status: {status}")
```

### Common Pitfalls
- Assuming a `FEASIBLE` status guarantees optimality; it may indicate a suboptimal solution.
- Not accounting for floating-point precision in validation checks, leading to false feasibility failures.
- Omitting solver time limits for larger problems, risking excessive runtime.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a declarative, algebraic modeling style, separating model definition from solver choice. It leverages Pyomo's `Set` and `Param` objects for clean data management and is ideal for complex, maintainable models integrated into larger systems.

### Step 1 - Define Abstract Sets and Parameters
- Create Pyomo `Set` objects for indexing (e.g., `model.P` for products, `model.R` for resources).
- Declare `Param` objects for all input data (profits, bounds, capacities, consumption matrix), initializing them from dictionaries or nested dictionaries.

### Step 2 - Declare Decision Variables
- Define a variable for production quantity, e.g., `model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)`.
- Use `pyo.NonNegativeIntegers` if production must be in whole units.

### Step 3 - Construct Objective Function
- Define the objective as a Pyomo `Objective` object: `model.obj = pyo.Objective(expr=sum(model.profit[p] * model.x[p] for p in model.P), sense=pyo.maximize)`.

### Step 4 - Implement Constraints via Rules
- Create lower and upper bound constraints using `Constraint` objects with rules indexed by the product set.
- Create resource capacity constraints using rules indexed by the resource set, summing `model.consumption[r,p] * model.x[p]` over products.

### Formulation Template
```json
{
  "sets": ["P (products)", "R (resources)"],
  "parameters": {
    "profit": "Param(P)",
    "min_prod": "Param(P)",
    "max_prod": "Param(P)",
    "capacity": "Param(R)",
    "consumption": "Param(R, P)"
  },
  "decision_variables": ["x[p] in NonNegativeReals (or NonNegativeIntegers)"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[p] * x[p] for p in P)"
  },
  "constraints": [
    "min_production: x[p] >= min_prod[p] for p in P",
    "max_production: x[p] <= max_prod[p] for p in P",
    "resource_limit: sum(consumption[r,p] * x[p] for p in P) <= capacity[r] for r in R"
  ]
}
```

### Common Pitfalls
- Using Python's built-in `sum` inside Pyomo expressions instead of `pyo.summation` or a generator expression within `pyo.Objective`/`Constraint`.
- Confusing Pyomo `Param` initialization with direct Python dictionary assignment.
- Not defining sets before parameters that depend on them, causing initialization errors.

## Solving stage

### Strategy Overview
Solving uses Pyomo's `SolverFactory` to interface with solvers like HiGHS (LP) or CBC (MIP). The focus is on robust status checking, solution extraction, and post-solution validation within the Pyomo model object.

### Step 1 - Configure and Execute Solver
- Instantiate solver: `solver = pyo.SolverFactory('highs')` (or `'cbc'`).
- Set options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`.
- Solve with `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Solver Status and Termination
- Check `results.solver.status` equals `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `feasible`.
- If checks fail, analyze logs or infeasibility diagnostics.

### Step 3 - Extract Solution and Verify Feasibility
- Extract objective value via `pyo.value(model.obj)`.
- Extract variable values via `pyo.value(model.x[p])` for each product.
- Programmatically compute constraint left-hand sides and compare to right-hand sides to verify feasibility within tolerance.

### Step 4 - Analyze Solution and Constraints
- Calculate slack for each constraint (`rhs - lhs`).
- Identify binding constraints (slack near zero).
- Report resource utilization percentages and profit contributions per product.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=product_indices)
# ... add parameters, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_profit = pyo.value(model.obj)
    for p in model.P:
        prod_qty = pyo.value(model.x[p])
        # ... process solution ...
    # Verify constraints
    for r in model.R:
        lhs = sum(pyo.value(model.consumption[r,p]) * pyo.value(model.x[p]) for p in model.P)
        if lhs > pyo.value(model.capacity[r]) + 1e-6:
            print(f"Capacity violation for resource {r}")
else:
    print("Solve failed or did not converge to an acceptable solution.")
```

### Common Pitfalls
- Accessing `pyo.value` on an undefined or uninitialized component.
- Not importing `SolverStatus` and `TerminationCondition` for status checks.
- Setting solver options incorrectly (e.g., `solver.options['timeLimit']` vs `solver.options['time_limit']`).
