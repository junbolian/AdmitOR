---
name: MultiResourceKnapsackILP
description: |
  Formulate and solve integer linear programs for resource allocation with multiple shared constraints, maximizing linear revenue subject to demand and capacity limits.
---

# Workflow 1 (OR-Tools Backend)

## Modeling stage

### Strategy Overview
Model the problem as a multi-dimensional knapsack ILP using the OR-Tools MIP solver interface. This approach directly encodes the problem into the solver's native model structure for efficient solving.

### Step 1 - Define Data Structures
- Define arrays for per-item revenue, demand upper bounds, and per-resource capacities.
- Construct a binary resource usage matrix `resource_usage[r][i]` where `1` indicates item `i` consumes resource `r`.
- Use zero-based indexing for compatibility with solver loops.

### Step 2 - Declare Decision Variables
- Create integer variables `x[i]` for each item, bounded between `0` and `demand[i]`.
- Use `solver.IntVar(lb, ub, name)` to enforce non-negativity and demand limits simultaneously.

### Step 3 - Formulate Resource Constraints
- For each resource `r`, add a linear constraint: `sum(resource_usage[r][i] * x[i] for i in items) <= capacity[r]`.
- Build constraints efficiently by iterating the usage matrix and only setting coefficients for entries equal to `1`.

### Step 4 - Set Linear Objective
- Define the objective to maximize total revenue: `sum(revenue[i] * x[i] for i in items)`.
- Use `solver.Maximize()` to set the objective sense.

### Formulation Template
```json
{
  "sets": ["items", "resources"],
  "parameters": [
    {"name": "revenue", "index": "items", "type": "float"},
    {"name": "demand", "index": "items", "type": "int"},
    {"name": "capacity", "index": "resources", "type": "int"},
    {"name": "resource_usage", "index": ["resources", "items"], "type": "binary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "integer", "bounds": "[0, demand[i]]"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "resource_limit", "index": "resources", "expression": "sum(resource_usage[r][i] * x[i] for i in items) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Forgetting to set variable upper bounds, leading to unbounded or unrealistic solutions.
- Inefficiently adding zero coefficients in constraints, which slows model building.
- Using float coefficients for binary usage indicators instead of integers, which can cause numerical issues.

## Solving stage

### Strategy Overview
Solve the built model using the OR-Tools wrapper, configuring for MILP with SCIP or CBC backend. Implement robust solution extraction and validation.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver('SCIP')`).
- Set a time limit (e.g., `solver.SetTimeLimit(60000)` for 60 seconds) and enable multiple threads (e.g., `solver.SetNumThreads(4)`).

### Step 2 - Solve and Check Status
- Call `solver.Solve()` and capture the result status.
- Verify the status is `OPTIMAL` or `FEASIBLE` before attempting to extract variable values.

### Step 3 - Extract and Validate Solution
- Iterate through decision variables and collect values where `x[i].solution_value() > 0`.
- Recompute total resource consumption using the solution and compare against capacities to confirm feasibility.
- Calculate the achieved objective value and compare it to `solver.Objective().Value()` for consistency.

### Step 4 - Handle Suboptimal or Failed Solves
- If status is not optimal, log the solver status and any best bound information.
- For time-limited runs, report the best feasible solution found even if optimality is not proven.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (build variables, constraints, objective as per modeling stage)

# solve with status / termination checks
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    print(f'Objective value = {solver.Objective().Value()}')
    # Extract solution
    for i in items:
        val = x[i].solution_value()
        if val > 0:
            print(f'x[{i}] = {val}')
    # Validate constraints
    for r in resources:
        usage = sum(resource_usage[r][i] * x[i].solution_value() for i in items)
        print(f'Resource {r} usage: {usage} / {capacity[r]}')
else:
    print('No optimal or feasible solution found.')
    print(f'Solver status: {status}')
```

### Common Pitfalls
- Not checking solver status before accessing `.solution_value()`, which can cause runtime errors.
- Omitting solution validation, potentially missing subtle constraint violations due to solver tolerances.
- Setting conflicting solver parameters (e.g., both gap tolerance and time limit) without understanding precedence.

# Workflow 2 (Pyomo with CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract modeling components, separating sets, parameters, variables, and constraints. This approach emphasizes model clarity, maintainability, and solver independence.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `items` and `resources`.
- Declare `Param` objects for `revenue`, `demand`, `capacity`, and `resource_usage` indexed appropriately.
- This separation allows easy swapping of problem data.

### Step 2 - Declare Variables with Integrated Bounds
- Create integer variables `model.x[i]` with `domain=pyo.NonNegativeIntegers`.
- Set variable bounds directly using a rule: `bounds=(0, model.demand[i])` to encode demand limits.

### Step 3 - Define Constraint Rules
- Create a `resource_constraint_rule(r, model)` that sums `model.x[i]` for all items `i` where `model.resource_usage[r,i] == 1`.
- Use Pyomo's `Constraint` object indexed over the resource set for clean, readable model structure.

### Step 4 - Construct Objective Function
- Define the objective as `sum(model.revenue[i] * model.x[i] for i in model.items)`.
- Use `pyo.Objective(rule=..., sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["items", "resources"],
  "parameters": [
    {"name": "revenue", "index": "items", "type": "float"},
    {"name": "demand", "index": "items", "type": "int"},
    {"name": "capacity", "index": "resources", "type": "int"},
    {"name": "resource_usage", "index": ["resources", "items"], "type": "binary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "integer", "bounds": "(0, demand[i])"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "resource_limit", "index": "resources", "expression": "sum(x[i] for i in items if resource_usage[r,i]==1) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Defining constraint rules that inefficiently iterate over all items for each resource, slowing model building.
- Confusing Pyomo's `bounds` argument with separate `Constraint` objects, leading to redundant or conflicting limits.
- Not initializing `Param` objects before model instantiation, causing initialization errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via `pyomo.SolverFactory`. Leverage Pyomo's solution management and diagnostic outputs for robust solving and debugging.

### Step 1 - Instantiate Solver and Configure Options
- Create a solver instance: `solver = pyo.SolverFactory('cbc')`.
- Set key options: `solver.options['seconds'] = 30`, `solver.options['threads'] = 4`, `solver.options['ratio'] = 0.0` for optimality tolerance.

### Step 2 - Solve and Load Solution
- Execute `results = solver.solve(model, tee=False)`.
- Check termination condition: `results.solver.termination_condition` should be `optimal` or `feasible`.
- Load the solution into the model using `model.solutions.load_from(results)`.

### Step 3 - Validate and Report Solution
- Extract variable values via `pyo.value(model.x[i])`.
- Compute actual resource usage and compare against capacities programmatically to validate feasibility.
- Report only non-zero variable values and key metrics like total revenue and resource utilization percentages.

### Step 4 - Implement Fallback for Solution Loading Errors
- If solution loading fails (`SolverError`), check `results.solution_status` and `results.incumbent_objective` to manually construct a solution report.
- Capture solver status and termination condition in a structured output (e.g., JSON) for failed solves.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (define sets, params, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model, tee=False)

# Check termination
if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    # Load solution safely
    try:
        model.solutions.load_from(results)
    except:
        print("Warning: Solution loading failed, extracting from results object.")
    # Extract and validate
    total_rev = 0
    for i in model.items:
        val = pyo.value(model.x[i])
        if val > 0:
            total_rev += pyo.value(model.revenue[i]) * val
            print(f'x[{i}] = {val}')
    print(f'Total revenue (from solution): {total_rev}')
    print(f'Solver objective: {pyo.value(model.obj)}')
else:
    print(f'Solve failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}')
```

### Common Pitfalls
- Assuming `tee=False` suppresses all output; some solvers may still print via different channels.
- Not handling the case where `load_from(results)` fails despite a feasible solve.
- Forgetting to set `pyo.value()` when accessing variable values after solution load.
