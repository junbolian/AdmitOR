---
name: Multi-Dimensional Knapsack with Item Selection Limits
description: |
  Model and solve resource allocation problems where discrete items with individual profit and consumption across multiple constrained resources are selected in integer quantities, subject to per-item upper bounds and per-resource capacity limits.
---

# Workflow 1 (MIP Solver via OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Program (MIP) using the OR-Tools linear solver wrapper (`pywraplp`). It is suited for direct, low-level control over variable and constraint construction, efficient for large, sparse problems, and integrates seamlessly with SCIP or CBC.

### Step 1 - Define Integer Decision Variables
- Create integer decision variables for each item, representing the selection count.
- Set variable bounds directly to embed per-item upper limits (`0 <= x[i] <= demand_limit[i]`).

### Step 2 - Formulate Linear Profit Objective
- Define the objective as a linear sum of profit coefficients multiplied by the corresponding decision variables.
- Set the objective sense to maximization.

### Step 3 - Encode Multi-Dimensional Capacity Constraints
- For each constrained resource, create a linear constraint with an upper bound equal to the resource capacity.
- For each item that consumes the resource, set the coefficient of its decision variable in the constraint to 1 (or a consumption rate).

### Formulation Template
```json
{
  "sets": [
    "items",
    "resources"
  ],
  "parameters": [
    {"name": "profit", "index": "items", "type": "float"},
    {"name": "demand_limit", "index": "items", "type": "int"},
    {"name": "capacity", "index": "resources", "type": "float"},
    {"name": "consumes", "index": ["items", "resources"], "type": "binary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "integer", "bounds": "[0, demand_limit[i]]"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "resource_capacity", "index": "resources", "expression": "sum(consumes[i, r] * x[i] for i in items) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Forgetting to set variable bounds, leading to unbounded variables.
- Using a dense consumption matrix for sparse problems, causing inefficient model building.
- Not verifying that all coefficients are set correctly, which can lead to silent constraint errors.

## Solving stage

### Strategy Overview
This stage focuses on configuring the MIP solver, solving the model, and rigorously checking the solution status and feasibility. It emphasizes performance tuning and post-solution validation.

### Step 1 - Configure Solver and Performance Parameters
- Instantiate a solver backend (e.g., `SCIP` or `CBC`).
- Set a time limit (`SetTimeLimit`) and the number of threads (`SetNumThreads`) for predictable runtime.

### Step 2 - Solve and Check Status Codes
- Call the solver's `Solve()` method.
- Check the returned status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.) before attempting to read solution values.

### Step 3 - Extract and Validate Solution
- If the status is `OPTIMAL` or `FEASIBLE`, extract variable values and the objective value.
- Programmatically verify that the solution satisfies all variable bounds and capacity constraints within a small numerical tolerance.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# Define variables, objective, constraints here...
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    solution = {i: x[i].solution_value() for i in items}
    # Perform feasibility verification
    for r in resources:
        total_consumed = sum(consumes[i, r] * solution[i] for i in items)
        assert total_consumed <= capacity[r] + 1e-6
else:
    raise Exception(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Proceeding to read solution values without checking solver status, risking runtime errors.
- Setting conflicting solver parameters (e.g., both a gap and a time limit) without understanding their interaction.
- Not performing post-solution feasibility checks, which can miss numerical inaccuracies from the solver.

# Workflow 2 (Pyomo with High-Level Abstraction)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a declarative, algebraic modeling approach. It is ideal for readability, maintainability, and leveraging Pyomo's built-in set and parameter management. It targets solvers like CBC or HiGHS via the `pyo.SolverFactory` interface.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for items and resources to structure the model.
- Define `Param` objects for profit, demand limits, capacities, and consumption relationships.

### Step 2 - Declare Integer Decision Variables
- Create a `Var` indexed by the item set with `domain=pyo.NonNegativeIntegers`.
- Optionally, set variable bounds within the domain or via constraints.

### Step 3 - Construct Objective and Constraints Algebraically
- Formulate the objective as a `sum` expression over the defined parameters and variables.
- Create two constraint rules: one for per-item upper bounds and one for per-resource capacity, using `sum` and the consumption parameter.

### Formulation Template
```json
{
  "sets": [
    "items",
    "resources"
  ],
  "parameters": [
    {"name": "profit", "index": "items", "type": "pyo.Param"},
    {"name": "demand_limit", "index": "items", "type": "pyo.Param"},
    {"name": "capacity", "index": "resources", "type": "pyo.Param"},
    {"name": "consumes", "index": ["items", "resources"], "type": "pyo.Param", "domain": "pyo.Binary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "pyo.Var", "domain": "pyo.NonNegativeIntegers"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "item_limit", "index": "items", "expression": "x[i] <= demand_limit[i]"},
    {"name": "resource_capacity", "index": "resources", "expression": "sum(consumes[i, r] * x[i] for i in items) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Using Python lists/dicts instead of Pyomo `Param` objects, which breaks solver compatibility.
- Defining constraint rules incorrectly (e.g., not returning an expression or returning `None`).
- Not initializing parameters before model instantiation, leading to runtime errors.

## Solving stage

### Strategy Overview
This stage involves configuring a solver via Pyomo's factory, solving the instance, and performing detailed checks on the solver's termination condition and the model's status. It includes solution extraction and analysis.

### Step 1 - Instantiate Solver and Set Options
- Use `pyo.SolverFactory("solver_name")` (e.g., `"cbc"` or `"highs"`).
- Pass options such as `time_limit`, `mipgap`, and `threads` via `options=` dict or solver-specific methods.

### Step 2 - Solve and Inspect Termination Status
- Execute `solver.solve(model)`.
- Check both `model.solutions.solver.status` (e.g., `SolverStatus.ok`) and `model.solutions.solver.termination_condition` (e.g., `TerminationCondition.optimal`).

### Step 3 - Extract, Cast, and Analyze Solution
- Use `pyo.value(model.x[i])` to get variable values and cast them to integers.
- Compute constraint slacks to identify binding constraints and verify feasibility.
- Generate a report of objective value, key variable values, and resource utilization percentages.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# Define sets, params, variables, objective, constraints here...

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
results = solver.solve(model, options={'seconds': 30, 'ratio': 0.0})

if (pyo.check_optimal_termination(results) or
    results.solver.termination_condition == pyo.TerminationCondition.feasible):
    objective_value = pyo.value(model.obj)
    solution = {i: int(pyo.value(model.x[i])) for i in model.items}
    # Analyze binding constraints
    for r in model.resources:
        total_consumed = sum(pyo.value(model.consumes[i, r]) * solution[i] for i in model.items)
        slack = pyo.value(model.capacity[r]) - total_consumed
        print(f"Resource {r} slack: {slack}")
else:
    raise Exception(f"Solver terminated with condition: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus` (process status) with `TerminationCondition` (solution quality).
- Not converting variable values to integers, which may leave them as floats and cause downstream issues.
- Omitting the `pyo.value()` wrapper when accessing parameter or variable values post-solution.
