---
name: Bounded Linear Resource Allocation
description: |
  Model and solve linear profit maximization problems with individual variable upper bounds and a shared linear resource constraint using solver-agnostic templates and robust solution handling.

---

# Workflow 1 (OR-Tools LP with Explicit Bounds)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to build a compact LP model. Variables are declared with explicit lower and upper bounds, efficiently encoding non-negativity and individual limits. The objective and single resource constraint are built using linear expressions.

### Step 1 - Define Data Structures
- Store problem instance data in parallel, index-aligned lists for profits, resource consumption rates, and individual upper limits.
- Define the shared resource capacity as a scalar parameter.

### Step 2 - Instantiate Solver and Variables
- Create a solver instance (e.g., `solver = pywraplp.Solver.CreateSolver('GLOP')`).
- For each item `i`, create a continuous decision variable `x[i]` using `solver.NumVar(0, upper_limit[i], f'x_{i}')`. This sets both non-negativity and the individual bound.

### Step 3 - Formulate Objective and Constraint
- Build the linear profit objective: `objective = solver.Objective()`. For each variable, set its coefficient using `objective.SetCoefficient(x[i], profit[i])`. Set the sense to maximization.
- Build the shared resource constraint: `constraint = solver.Constraint(0, capacity)`. For each variable, set its coefficient using `constraint.SetCoefficient(x[i], consumption[i])`.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit[I]",
    "consumption[I]",
    "upper_limit[I]",
    "capacity"
  ],
  "decision_variables": ["x[I] (continuous, 0 <= x_i <= upper_limit_i)"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_i * x_i for i in I)"
  },
  "constraints": [
    "sum(consumption_i * x_i for i in I) <= capacity"
  ]
}
```

### Common Pitfalls
- Forgetting to set the objective sense to maximization, which defaults to minimization.
- Manually summing coefficients in a loop instead of using `SetCoefficient` for each variable, which is less efficient and more error-prone.
- Accessing solution values without first checking the solver status, leading to runtime errors on infeasible or unbounded models.

## Solving stage

### Strategy Overview
Solve the model using the GLOP backend, which is optimized for continuous LPs. Implement robust status checking and solution extraction. Perform post-solution validation by calculating profit-to-consumption ratios to verify the solution aligns with economic intuition.

### Step 1 - Solve and Check Status
- Execute `solver.Solve()`.
- Check if the result status is `OPTIMAL` or `FEASIBLE` using `solver.ResultStatus()` before proceeding. If not, handle the error.

### Step 2 - Extract and Validate Solution
- Extract the objective value using `solver.Objective().Value()`.
- For each variable, extract its value using `x[i].solution_value()`.
- Calculate total resource consumption and verify it is within capacity (allowing for small numerical tolerance).

### Step 3 - Analyze and Report
- Compute profit-to-consumption ratios and rank items. Verify that items with higher ratios are prioritized in the solution.
- Print a summary including objective value, capacity usage percentage, and non-zero production decisions.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
x = {}
for i in range(num_items):
    x[i] = solver.NumVar(0, upper_limit[i], f'x_{i}')
# ... build objective and constraint as per modeling stage

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'Optimal profit: {solver.Objective().Value()}')
    total_consumption = 0
    for i in range(num_items):
        val = x[i].solution_value()
        if val > 1e-6:
            total_consumption += consumption[i] * val
            print(f'  Item {i}: {val}')
    print(f'Capacity used: {total_consumption}/{capacity}')
else:
    print('No optimal solution found.')
```

### Common Pitfalls
- Using exact equality (`==`) to check constraint satisfaction against capacity, which fails due to floating-point arithmetic; use a tolerance (e.g., `abs(total_use - capacity) < 1e-6`).
- Not checking for `FEASIBLE` status in addition to `OPTIMAL`, which may cause valid but suboptimal solutions to be incorrectly rejected.
- Omitting the calculation of derived metrics (like capacity usage), reducing the utility of the solution report.

# Workflow 2 (Pyomo with Declarative Bounds)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a declarative, solver-agnostic model. Variables are defined with bounds specified via a rule or lambda function, separating the model logic from data. The objective and constraint are expressed using Pyomo's summation syntax for clarity.

### Step 1 - Define Abstract Sets and Parameters
- Define a Pyomo `Set` to index the items/activities.
- Define `Param` objects for profits, consumption rates, and upper limits, indexed by the set.
- Define the scalar capacity parameter.

### Step 2 - Declare Bounded Variables
- Declare a continuous variable `model.x` indexed by the item set, with domain `pyo.NonNegativeReals`.
- Set individual upper bounds using a `bounds` rule: `model.x = pyo.Var(model.I, bounds=lambda m, i: (0, m.upper_limit[i]))`.

### Step 3 - Formulate Objective and Constraint
- Define the objective using `pyo.Objective(expr=sum(model.profit[i] * model.x[i] for i in model.I), sense=pyo.maximize)`.
- Define the resource constraint using `pyo.Constraint(expr=sum(model.consumption[i] * model.x[i] for i in model.I) <= model.capacity)`.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit[I]",
    "consumption[I]",
    "upper_limit[I]",
    "capacity"
  ],
  "decision_variables": ["x[I] (continuous, bounded by (0, upper_limit_i))"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_i * x_i for i in I)"
  },
  "constraints": [
    "sum(consumption_i * x_i for i in I) <= capacity"
  ]
}
```

### Common Pitfalls
- Defining bounds directly in the `domain` argument instead of using the `bounds` argument, which can be less flexible.
- Hard-coding numerical data within the model rules, which reduces reusability; always reference `Param` objects.
- Using Python's built-in `sum` instead of Pyomo's `summation` or `pyo.sum`, which can lead to incorrect expression construction in some contexts.

## Solving stage

### Strategy Overview
Solve the model using an open-source solver like HiGHS or CBC via Pyomo's `SolverFactory`. Configure practical solver options for time and tolerance. Implement a two-layer check on both solver status and termination condition before extracting results.

### Step 1 - Configure and Execute Solver
- Instantiate a solver: `solver = pyo.SolverFactory('highs')`.
- Set options like time limit: `solver.options['time_limit'] = 30`.
- Execute the solve: `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Solution Status
- Check if the solver status is `ok`: `pyo.check_optimal_termination(results)` or inspect `results.solver.status`.
- Additionally, check the termination condition is `optimal` or `feasible`.

### Step 3 - Extract and Analyze Results
- Safely extract the objective value using `pyo.value(model.obj)`.
- Iterate through variables to get values using `pyo.value(model.x[i])`.
- Calculate total consumption and verify constraint satisfaction within tolerance.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_items))
model.profit = pyo.Param(model.I, initialize=profit_data)
# ... define other parameters and variables as per modeling stage

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    print(f'Optimal profit: {pyo.value(model.obj)}')
    total_consumption = 0
    for i in model.I:
        val = pyo.value(model.x[i])
        if val > 1e-6:
            total_consumption += pyo.value(model.consumption[i]) * val
            print(f'  Item {i}: {val}')
    print(f'Capacity used: {total_consumption}/{pyo.value(model.capacity)}')
else:
    print(f'Solver failed: {results.solver.termination_condition}')
```

### Common Pitfalls
- Relying solely on `pyo.check_optimal_termination()` without considering `feasible` termination conditions, which may discard valid solutions.
- Not using `pyo.value()` to extract results, leading to direct access of variable attributes that may not be populated.
- Ignoring numerical precision when checking for non-zero variables; use a tolerance (e.g., `> 1e-6`) instead of `> 0`.
