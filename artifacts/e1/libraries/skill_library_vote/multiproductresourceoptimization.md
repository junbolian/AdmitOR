---
name: MultiProductResourceOptimization
description: |
  A skill for solving linear optimization problems with multi-dimensional continuous variables, box bounds, linear inequality constraints, and a linear profit maximization objective, using systematic modeling and robust solving workflows.
---

# Workflow 1 (Pyomo with HiGHS Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's ConcreteModel for a clear, structured linear program formulation. It leverages the HiGHS solver, a high-performance open-source LP solver, and emphasizes explicit variable bounds and post-solution verification.

### Step 1 - Define Sets and Parameters
- **Create an index set for products**: Use a Pyomo `Set` object to define the range of products, enabling clean indexing for all parameters and variables.
- **Store parameters as Python data structures**: Define lists or dictionaries for profit per unit, resource consumption per unit, minimum and maximum production bounds, and total resource capacity, keeping data separate from the model logic.

### Step 2 - Construct Variables with Explicit Bounds
- **Declare continuous, non-negative decision variables**: Use `pyo.Var(domain=pyo.NonNegativeReals)` to represent production quantities for each product.
- **Apply product-specific bounds directly**: Set lower and upper bounds on each variable using the `bounds` argument or `setlb()`/`setub()` methods to enforce minimum and maximum production limits.

### Step 3 - Formulate Objective and Constraints
- **Build a linear profit maximization objective**: Sum the product of profit coefficients and decision variables across all products.
- **Add a linear resource capacity constraint**: Create a single linear inequality constraint where the sum of resource consumption (coefficient * variable) across all products is less than or equal to the total available capacity.

### Formulation Template
```json
{
  "sets": ["P: Set of products"],
  "parameters": [
    "profit[p]: Profit per unit for product p",
    "resource_use[p]: Resource units consumed per unit of product p",
    "min_prod[p]: Minimum production quantity for product p",
    "max_prod[p]: Maximum production quantity for product p",
    "total_capacity: Total available resource units"
  ],
  "decision_variables": ["x[p]: Production quantity of product p"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[p] * x[p] for p in P)"
  },
  "constraints": [
    "ResourceCapacity: sum(resource_use[p] * x[p] for p in P) <= total_capacity",
    "BoxBounds: min_prod[p] <= x[p] <= max_prod[p] for all p in P"
  ]
}
```

### Common Pitfalls
- **Blindly accepting solver output without verification**: Always cross-check the final solution against the original constraints and bounds.
- **Inconsistent parameter indexing**: Ensure the order of products is consistent across all parameter arrays (profits, resource use, bounds) to prevent misalignment.
- **Omitting explicit bound enforcement**: Relying solely on constraints for bounds can be less efficient; use variable bounds for better solver performance.

## Solving stage

### Strategy Overview
This stage focuses on configuring the HiGHS solver for robust performance, implementing comprehensive solution status checks, and performing post-solution analysis to verify feasibility and resource utilization.

### Step 1 - Configure and Execute Solver
- **Instantiate the HiGHS solver via Pyomo**: Use `SolverFactory('highs')` to create the solver object.
- **Set practical solver options**: Configure `time_limit` for runtime control, `threads` for parallel processing, and enable `presolve` for model simplification.

### Step 2 - Verify Solution Status and Extract Results
- **Check solver status and termination condition**: Verify that `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible` before proceeding.
- **Extract variable values and objective**: Use `pyo.value()` to retrieve the solution for each decision variable and the objective function.

### Step 3 - Perform Post-Solution Validation
- **Recalculate total resource usage**: Compute the sum of resource consumption from the solved variables and compare it against the capacity to check constraint satisfaction and identify slack.
- **Verify individual variable bounds**: Ensure each production quantity lies within its specified minimum and maximum bounds.
- **Calculate and report key metrics**: Output total profit, resource utilization percentage, and per-product contributions for manual verification.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=range(len(profit_list)))
model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals, bounds=lambda m, i: (min_list[i], max_list[i]))
model.profit_obj = pyo.Objective(expr=sum(profit_list[i] * model.x[i] for i in model.P), sense=pyo.maximize)
model.capacity_con = pyo.Constraint(expr=sum(resource_list[i] * model.x[i] for i in model.P) <= total_capacity)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    solution = {i: pyo.value(model.x[i]) for i in model.P}
    total_profit = pyo.value(model.profit_obj)
    # Post-solution validation
    used_resource = sum(resource_list[i] * solution[i] for i in model.P)
    print(f"Solution valid. Total Profit: {total_profit}. Resource Used: {used_resource}/{total_capacity}")
else:
    print("Solver did not return a valid solution.")
```

### Common Pitfalls
- **Trusting solver results without checking status**: A non-optimal or error termination condition can still produce numerical values that are not valid solutions.
- **Neglecting to compute derived metrics**: Failing to recalculate resource usage from the solution misses an opportunity to catch potential numerical or modeling errors.
- **Using default solver settings for large problems**: Always consider setting time limits and enabling presolve for better performance and reliability.

# Workflow 2 (Pyomo with CBC and Integer Relaxation Analysis)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo with the CBC solver, focusing on a clean separation of data and model. It systematically handles ambiguity in variable domain (continuous vs. integer) by solving both relaxations and comparing results to inform decision-making.

### Step 1 - Abstract Data with Pyomo Sets
- **Initialize a product set for indexing**: Use `pyo.Set(initialize=range(n))` to create a maintainable index, enabling vectorized operations in constraints and objectives.
- **Store all numerical parameters externally**: Keep profit, resource use, and bound data in standard Python lists/dictionaries, making the model template adaptable to different datasets.

### Step 2 - Define Variables with Embedded Bounds
- **Use a flexible variable domain declaration**: Allow the domain (`NonNegativeReals` or `NonNegativeIntegers`) to be a parameter, facilitating easy switching between continuous and integer models.
- **Embed bounds in the variable declaration**: Apply product-specific lower and upper bounds directly within the `bounds` argument of `pyo.Var()` for a concise formulation.

### Step 3 - Build Linear Objective and Capacity Constraint
- **Construct a vectorized linear objective**: Sum the product of profit coefficients and variables using a generator expression over the product set.
- **Formulate the resource constraint as a linear inequality**: Use the same indexing pattern to sum resource consumption across all products.

### Formulation Template
```json
{
  "sets": ["PRODUCTS: Index set for all products"],
  "parameters": [
    "unit_profit[PRODUCTS]: Profit coefficient",
    "unit_resource[PRODUCTS]: Resource consumption coefficient",
    "lb[PRODUCTS]: Lower bound (minimum production)",
    "ub[PRODUCTS]: Upper bound (maximum production)",
    "capacity: Total resource availability"
  ],
  "decision_variables": ["q[PRODUCTS]: Quantity to produce"],
  "objective": {
    "sense": "max",
    "expression": "sum(unit_profit[p] * q[p] for p in PRODUCTS)"
  },
  "constraints": [
    "ResourceLimit: sum(unit_resource[p] * q[p] for p in PRODUCTS) <= capacity"
  ]
}
```

### Common Pitfalls
- **Hard-coding variable domains**: Making the variable domain (continuous/integer) inflexible prevents easy comparison of relaxation strategies.
- **Mixing data preparation with model logic**: Embedding raw numerical values directly in constraint expressions reduces reusability and clarity.
- **Overlooking the value of continuous relaxation**: Not solving the continuous version forfeits a useful upper bound for assessing the quality of integer solutions.

## Solving stage

### Strategy Overview
This stage configures the CBC solver with practical tolerances, implements robust solution checking, and executes a systematic analysis comparing continuous and integer solutions to guide final implementation choices.

### Step 1 - Configure CBC Solver
- **Set a reasonable time limit**: Use `solver.options['seconds']` to prevent excessively long runs.
- **Configure for optimality**: Set `solver.options['ratio'] = 0.0` to instruct CBC to seek an optimal solution (zero gap) when possible.
- **Enable parallel processing**: Utilize `solver.options['threads']` to leverage multiple CPU cores for faster solving.

### Step 2 - Solve and Validate Multiple Formulations
- **Solve the continuous relaxation first**: Obtain the upper bound on profit and the continuous solution.
- **Solve the integer formulation**: If the problem context suggests discrete units, solve with integer variables to get a implementable plan.
- **Perform rigorous solution status checks**: For each solve, verify both `SolverStatus.ok` and an acceptable `TerminationCondition` before extracting results.

### Step 3 - Analyze and Compare Results
- **Compare objective values**: Calculate the optimality gap between the continuous upper bound and the integer solution value.
- **Check rounding feasibility**: Test if rounding the continuous solution to integers respects all bounds and the resource constraint, providing a quick feasibility check.
- **Document the trade-offs**: Report the difference in profit and solution values, helping to decide if the integer constraint's cost is acceptable.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

def solve_production_model(profits, resources, mins, maxs, capacity, integer=False):
    """Solves the production planning model, optionally with integer variables."""
    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=range(len(profits)))
    # Choose domain based on input flag
    domain = pyo.NonNegativeIntegers if integer else pyo.NonNegativeReals
    model.q = pyo.Var(model.P, domain=domain, bounds=lambda m, i: (mins[i], maxs[i]))
    model.obj = pyo.Objective(expr=sum(profits[i] * model.q[i] for i in model.P), sense=pyo.maximize)
    model.cap = pyo.Constraint(expr=sum(resources[i] * model.q[i] for i in model.P) <= capacity)

    solver = pyo.SolverFactory('cbc')
    solver.options['seconds'] = 30
    solver.options['ratio'] = -0.0  # Seek optimal solution
    results = solver.solve(model, tee=False)

    if (results.solver.status == SolverStatus.ok and
        results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
        solution = {i: pyo.value(model.q[i]) for i in model.P}
        total_profit = pyo.value(model.obj)
        return solution, total_profit
    else:
        return None, None

# Example usage for comparison
# cont_sol, cont_profit = solve_production_model(profit_list, resource_list, min_list, max_list, total_cap, integer=False)
# int_sol, int_profit = solve_production_model(profit_list, resource_list, min_list, max_list, total_cap, integer=True)
# if cont_sol and int_sol:
#     print(f"Continuous Profit: {cont_profit}, Integer Profit: {int_profit}, Gap: {cont_profit - int_profit}")
```

### Common Pitfalls
- **Ignoring solver termination conditions**: Assuming a solved model is optimal without checking `termination_condition` can lead to accepting suboptimal or infeasible points.
- **Not using the continuous relaxation as a benchmark**: Solving only the integer problem misses the chance to quantify the cost of integrality constraints.
- **Failing to set a time limit for CBC**: Allowing the solver to run indefinitely on large or complex integer problems can waste computational resources.
