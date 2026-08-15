---
name: Continuous Linear Production Planning
description: |
  Model and solve continuous linear programs for production allocation with individual capacity bounds and shared linear resource constraints, maximizing total profit.

---

# Workflow 1 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model definition, separating the mathematical formulation from the solver backend. It is designed for flexibility and integration with open-source solvers like CBC and GLPK.

### Step 1 - Define Indexed Sets and Parameters
- Create a set `I` to index all products or items.
- Define dictionaries or lists for parameters: `profit[i]`, `resource_consumption[i]`, `max_production[i]`, and scalar `total_resource_limit`.
- Ensure all parameter containers are aligned with the index set `I`.

### Step 2 - Declare Decision Variables
- Declare a continuous variable `x[i]` for each `i` in `I`, representing the production quantity.
- Set the variable domain to `NonNegativeReals` to enforce non-negativity.
- Do not embed individual upper bounds (`max_production[i]`) in the variable domain; handle them via explicit constraints.

### Step 3 - Formulate Objective and Constraints
- Build a linear objective to maximize total profit: `sum(profit[i] * x[i] for i in I)`.
- Add a linear resource constraint: `sum(resource_consumption[i] * x[i] for i in I) <= total_resource_limit`.
- Add individual capacity constraints: `x[i] <= max_production[i]` for each `i` in `I`.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit[I] (profit per unit)",
    "resource_consumption[I] (resource use per unit)",
    "max_production[I] (individual upper bound)",
    "total_resource_limit (scalar capacity)"
  ],
  "decision_variables": ["x[I] (production quantity)"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    "resource_limit: sum(resource_consumption[i] * x[i] for i in I) <= total_resource_limit",
    "capacity_i: x[i] <= max_production[i] for each i in I"
  ]
}
```

### Common Pitfalls
- Mismatching the order of indices between sets and parameter arrays, causing incorrect coefficient assignment.
- Forgetting to enforce non-negativity on variables, allowing invalid negative production.
- Embedding upper bounds in the variable domain, which can obscure constraint activity in solver reports.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured open-source LP solver (e.g., CBC). The focus is on robust solving, status checking, and extracting a detailed solution analysis.

### Step 1 - Configure and Execute Solver
- Instantiate the solver via `SolverFactory('solver_name')` (e.g., `'cbc'`).
- Set solver options such as time limit (`seconds`) and optimality tolerance.
- Solve the model with `solve(model, tee=False)` and capture the result object.

### Step 2 - Validate Solver Status and Termination
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- If status is not optimal/feasible, analyze logs or provide a fallback (e.g., a greedy heuristic estimate).
- Only extract solution values if the solve was successful.

### Step 3 - Extract and Analyze Solution
- Load the solution into the model instance.
- Compute the total profit (`pyo.value(model.obj)`) and total resource usage.
- Identify binding constraints by checking if `total_resource_usage ≈ total_resource_limit` and which `x[i] == max_production[i]`.
- Calculate profit-to-resource ratios for each item to validate the solution's economic logic.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (model defined as per Modeling stage)
model = create_production_model(data)

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30  # Set time limit
results = solver.solve(model, tee=False)

# Check solve status
from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    # Load solution for analysis
    model.solutions.load_from(results)
    total_profit = pyo.value(model.obj)
    # Calculate total resource usage
    total_resource = sum(pyo.value(model.x[i]) * model.resource_consumption[i] for i in model.I)
    print(f"Optimal profit: {total_profit}, Resource used: {total_resource}")
else:
    print(f"Solver failed: {status}, {term}")
    # Implement fallback analysis or error handling
```

### Common Pitfalls
- Not checking termination condition, assuming `SolverStatus.ok` alone guarantees optimality.
- Forgetting to load the solution before accessing variable values (`model.solutions.load_from(results)`).
- Omitting a time limit, allowing the solver to run indefinitely on large or numerically difficult instances.

# Workflow 2 (Ortools with Primary/Backup Solvers)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools linear solver wrapper, which provides a unified API to multiple LP backends (GLOP, HiGHS, GLPK). It emphasizes efficient model construction and built-in solver fallback mechanisms.

### Step 1 - Initialize Solver and Define Variables
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver('GLOP')`).
- Define continuous variables `x[i]` with explicit lower bound (0) and upper bound (`max_production[i]`) directly in the variable creation.
- Use descriptive variable names (e.g., `x_0`, `x_1`) for easier debugging.

### Step 2 - Build Linear Expressions for Constraints
- Construct the resource constraint by creating a linear expression: `sum(resource_consumption[i] * x[i] for i in range(n_items))`.
- Add the constraint to the solver with the limit: `solver.Add(expr <= total_resource_limit)`.
- Individual upper bounds are already enforced via variable definitions, but can be added as explicit constraints for clarity.

### Step 3 - Set Linear Objective
- Define the objective as a linear expression: `sum(profit[i] * x[i] for i in range(n_items))`.
- Set the objective sense to maximization using `solver.Maximize(obj_expr)`.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit[I] (profit per unit)",
    "resource_consumption[I] (resource use per unit)",
    "max_production[I] (individual upper bound)",
    "total_resource_limit (scalar capacity)"
  ],
  "decision_variables": ["x[I] (production quantity, 0 <= x[i] <= max_production[i])"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    "resource_limit: sum(resource_consumption[i] * x[i] for i in I) <= total_resource_limit"
  ]
}
```

### Common Pitfalls
- Creating variables without upper bounds, requiring additional individual constraints and increasing model size.
- Building large linear expressions in a non-vectorized way, impacting model construction time for many items.
- Not verifying that the sum of maximum possible resource consumption (`sum(max_production[i] * resource_consumption[i])`) exceeds the total limit, which is a prerequisite for the constraint to be potentially binding.

## Solving stage

### Strategy Overview
Solve using OR-Tools' solver, implementing a fallback chain if the primary solver fails. Extract solution values and perform post-solve validation and analysis.

### Step 1 - Solve with Primary Solver and Check Status
- Call `solver.Solve()` and check the result status (`pywraplp.Solver.OPTIMAL`).
- If optimal, proceed to solution extraction.
- If not optimal, log the status and proceed to a backup solver.

### Step 2 - Implement Solver Fallback Chain
- If the primary solver (e.g., `'GLOP'`) fails, try a secondary solver (e.g., `'HiGHS'` or `'CBC'`).
- Rebuild the model with the new solver instance if the API requires it.
- Set appropriate solver-specific options (time limit, threads) for each attempt.

### Step 3 - Extract Solution and Verify Feasibility
- Extract variable values using `x[i].solution_value()`.
- Compute total profit and total resource usage from the solution.
- Programmatically verify all constraints: check non-negativity, individual upper bounds, and the resource limit.
- Calculate profit-to-resource ratios to analyze the solution structure and identify prioritized items.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
def create_and_solve(profit, resource_cons, max_prod, limit, solver_id='GLOP'):
    solver = pywraplp.Solver.CreateSolver(solver_id)
    if not solver:
        raise RuntimeError(f"Solver {solver_id} not available.")
    n = len(profit)
    x = [solver.NumVar(0.0, max_prod[i], f'x_{i}') for i in range(n)]

    # Resource constraint
    resource_ct = solver.Constraint(0, limit)
    for i in range(n):
        resource_ct.SetCoefficient(x[i], resource_cons[i])

    # Objective
    objective = solver.Objective()
    for i in range(n):
        objective.SetCoefficient(x[i], profit[i])
    objective.SetMaximization()

    # Solve with status / termination checks
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        total_profit = objective.Value()
        total_resource = sum(x[i].solution_value() * resource_cons[i] for i in range(n))
        return status, total_profit, total_resource, [x[i].solution_value() for i in range(n)]
    else:
        return status, None, None, None

# Example usage with fallback
data = {...}
solvers_to_try = ['GLOP', 'HiGHS', 'CBC']
solution_found = False

for solver_id in solvers_to_try:
    status, profit, resource_used, vals = create_and_solve(**data, solver_id=solver_id)
    if status == pywraplp.Solver.OPTIMAL:
        print(f"Solved with {solver_id}. Profit: {profit}")
        solution_found = True
        break
    else:
        print(f"Solver {solver_id} failed with status: {status}")

if not solution_found:
    print("All solvers failed. Implement greedy fallback or error handling.")
```

### Common Pitfalls
- Assuming the first solver in the chain is always available; always check `Solver.CreateSolver` does not return `None`.
- Not setting solver-specific options (like time limits) for backup solvers, leading to unpredictable runtimes.
- Failing to verify solution feasibility programmatically, potentially accepting infeasible results due to solver tolerances.
