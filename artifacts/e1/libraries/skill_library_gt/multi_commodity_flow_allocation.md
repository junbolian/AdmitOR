---
name: Multi-Commodity Flow Allocation
description: |
  Model and solve multi-source, multi-destination, multi-product allocation problems with exact demand satisfaction and profit maximization using linear programming.

---
# Workflow 1 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define sets, parameters, and constraints declaratively, then solves with a configurable open-source solver (e.g., HiGHS, CBC, GLPK). It emphasizes a clean separation between model logic and solver execution.

### Step 1 - Define Index Sets
- Identify and define the three fundamental sets: sources (e.g., companies), destinations (e.g., markets), and commodities (e.g., product types).
- Initialize sets using Pyomo's `Set` component with clear, iterable data structures (e.g., lists).

### Step 2 - Declare Parameters
- Define demand as a 2D parameter indexed by `(destination, commodity)`.
- Define profit coefficients as a 3D parameter indexed by `(source, destination, commodity)`.
- Use Python dictionaries with tuple keys for explicit initialization to ensure correct mapping and avoid silent indexing errors.

### Step 3 - Create Decision Variables
- Create a 3D decision variable `x[source, destination, commodity]` representing the allocation quantity.
- Set the variable domain to `pyo.NonNegativeReals` to enforce non-negativity implicitly at the variable level.

### Step 4 - Formulate Objective Function
- Construct a linear objective to maximize total profit: sum of `profit[s,d,c] * x[s,d,c]` over all indices.
- Use Pyomo's `Objective` component with `sense=pyo.maximize`.

### Step 5 - Impose Demand Satisfaction Constraints
- For each `(destination, commodity)` pair, create an equality constraint.
- The constraint forces the sum of allocations from all sources to exactly equal the demand: `sum(x[s,d,c] for s in sources) == demand[d,c]`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "commodities"],
  "parameters": [
    {"name": "demand", "dimensions": ["destinations", "commodities"]},
    {"name": "profit", "dimensions": ["sources", "destinations", "commodities"]}
  ],
  "decision_variables": [
    {"name": "x", "dimensions": ["sources", "destinations", "commodities"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s,d,c] * x[s,d,c] for s in sources for d in destinations for c in commodities)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "condition": "sum(x[s,d,c] for s in sources) == demand[d,c]", "forall": ["destinations", "commodities"]}
  ]
}
```

### Common Pitfalls
- Using ambiguous or overlapping names for model components and Python loop variables, leading to scoping errors.
- Initializing parameters with default values instead of explicit dictionaries, causing misalignment between indices and data.
- Forgetting to check both solver status *and* termination condition before attempting to load a solution.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a primary open-source solver with a fallback mechanism. Implement robust solution verification and structured error handling to ensure reliability.

### Step 1 - Configure Solver with Fallback
- Define a list of solver names and their options (e.g., `[('highs', {'time_limit': 30}), ('cbc', {'seconds': 30})]`).
- Iterate through the list, attempting to solve with each until one returns a successful status.
- For each solver, set options via `solver.options[key] = value`.

### Step 2 - Execute Solve and Check Status
- Call `solver.solve(model, tee=False)` to execute the optimization.
- Check that `results.solver.status` is `SolverStatus.ok`.
- Check that `results.solver.termination_condition` is either `optimal` or `feasible`. Only proceed to load solution if both checks pass.

### Step 3 - Load and Verify Solution
- If the solve was successful, compute the total allocation for each `(destination, commodity)` pair.
- Assert that the computed total matches the demand parameter within a small tolerance (e.g., `1e-6`).
- Extract and report the objective value.

### Step 4 - Handle Failure Gracefully
- If all solvers fail, output a structured JSON result indicating failure reason (e.g., `{"status": "failed", "reason": "solver_error"}`).
- Avoid crashing; ensure the workflow provides actionable output regardless of solver outcome.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# Build model from formulation (following Modeling Stage steps)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, objective, constraints ...

# Solve with status / termination checks
solvers = [('highs', {'time_limit': 30}), ('cbc', {'seconds': 30})]  # Example solvers
results = None
solver_used = None

for solver_name, options in solvers:
    solver = pyo.SolverFactory(solver_name)
    for key, value in options.items():
        solver.options[key] = value
    results = solver.solve(model, tee=False)
    status = results.solver.status
    term = results.solver.termination_condition

    if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
        solver_used = solver_name
        break

# Process results
if solver_used:
    # Verification
    for d in model.destinations:
        for c in model.commodities:
            total = sum(pyo.value(model.x[s, d, c]) for s in model.sources)
            assert abs(total - model.demand[d, c]) < 1e-6, f"Demand mismatch for ({d},{c})"
    objective_value = float(pyo.value(model.obj))
    print(f'RESULT:{objective_value}')
else:
    # Failure handling
    print(f'RESULT_JSON:{json.dumps({"status": "failed", "reason": "solver_error"})}')
```

### Common Pitfalls
- Loading solutions without checking `termination_condition`, potentially using invalid results from suboptimal or infeasible solves.
- Not using `pyo.value()` to extract numeric values from Pyomo components post-solve.
- Omitting a fallback solver strategy, causing the entire workflow to fail due to a single solver's configuration or availability issue.

# Workflow 2 (OR-Tools LP with GLOP/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools linear solver API to construct the model imperatively. It is suited for rapid prototyping and environments where Pyomo is not available, leveraging efficient, low-level variable and constraint construction.

### Step 1 - Initialize Solver and Data Structures
- Choose an appropriate LP solver (e.g., `GLOP` for continuous, `CBC` for MIP extensions).
- Organize input data as nested lists or dictionaries: `demand[destination][commodity]`, `profit[source][destination][commodity]`.

### Step 2 - Create Decision Variables
- Use nested loops over `sources`, `destinations`, `commodities` to create variables.
- Create each variable with `solver.NumVar(lb, ub, name)`. Set `lb=0` and `ub=solver.infinity()` for non-negativity without explicit upper bounds.
- Store variables in a dictionary keyed by tuple `(source, destination, commodity)` for efficient access.

### Step 3 - Build Demand Satisfaction Constraints
- For each `(destination, commodity)` pair, create a new constraint with `solver.Constraint(demand_value, demand_value)` to enforce equality.
- Within the loop for each pair, add the contribution from each source variable using `constraint.SetCoefficient(var, 1.0)`.

### Step 4 - Set Linear Objective
- Initialize the objective with `solver.Objective()`.
- Iterate through all variable indices, adding each term using `objective.SetCoefficient(var, profit_coefficient)`.
- Set the objective sense to maximization with `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "commodities"],
  "parameters": [
    {"name": "demand", "dimensions": ["destinations", "commodities"]},
    {"name": "profit", "dimensions": ["sources", "destinations", "commodities"]}
  ],
  "decision_variables": [
    {"name": "x", "dimensions": ["sources", "destinations", "commodities"], "domain": "continuous, >=0"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s][d][c] * x[s][d][c] for s in sources for d in destinations for c in commodities)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "condition": "sum(x[s][d][c] for s in sources) == demand[d][c]", "forall": ["destinations", "commodities"]}
  ]
}
```

### Common Pitfalls
- Mismatching indices between the profit coefficient data structure and the order of loops used to set objective coefficients.
- Forgetting to call `SetCoefficient` for every variable in a constraint, leading to incorrect constraint definitions.
- Using `solver.infinity()` for an upper bound when a finite capacity constraint should exist.

## Solving stage

### Strategy Overview
Solve the imperatively built model using the OR-Tools solver, perform solution verification by recomputing key totals, and implement cross-solver validation for critical applications.

### Step 1 - Execute the Solve
- Call `solver.Solve()` to run the optimization.
- Check the returned status code against `pywraplp.Solver.OPTIMAL` first, then `FEASIBLE`. Handle other statuses as failures.

### Step 2 - Extract and Verify Solution
- If status is optimal or feasible, iterate through variables and extract `var.solution_value()`.
- For each `(destination, commodity)` pair, recompute the total allocation by summing the solution values from all sources.
- Verify this total equals the demand within a tolerance (e.g., `1e-6`). Print a warning for any mismatch.

### Step 3 - Report Results
- Print the objective value from `objective.Value()`.
- Optionally, print only non-zero allocations (`if val > 1e-6`) to keep output concise and actionable.

### Step 4 - Cross-Solver Validation (Optional)
- For increased confidence, solve the same model with a different solver backend (e.g., solve with `GLOP`, then with `CBC`).
- Compare objective values and key variable values to confirm consistency.

### Code Usage
```python
from ortools.linear_solver import pywraplp
import math

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
if not solver:
    raise RuntimeError('Solver not available.')

# Create variables and store in dict
x = {}
for s in sources:
    for d in destinations:
        for c in commodities:
            x[(s, d, c)] = solver.NumVar(0, solver.infinity(), f'x_{s}_{d}_{c}')

# Demand satisfaction constraints
for d in destinations:
    for c in commodities:
        constraint = solver.Constraint(demand[d][c], demand[d][c])
        for s in sources:
            constraint.SetCoefficient(x[(s, d, c)], 1.0)

# Objective
objective = solver.Objective()
for s in sources:
    for d in destinations:
        for c in commodities:
            objective.SetCoefficient(x[(s, d, c)], profit[s][d][c])
objective.SetMaximization()

# Solve with status / termination checks
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    # Verification
    for d in destinations:
        for c in commodities:
            total = sum(x[(s, d, c)].solution_value() for s in sources)
            if not math.isclose(total, demand[d][c], abs_tol=1e-6):
                print(f'Warning: Demand mismatch for ({d},{c}): {total} vs {demand[d][c]}')
    # Report
    print(f'RESULT:{objective.Value()}')
    # Print non-zero allocations
    for (s, d, c), var in x.items():
        val = var.solution_value()
        if val > 1e-6:
            print(f'{var.name()} = {val}')
else:
    print(f'RESULT_JSON:{{"status": "failed", "reason": "solver_status_{status}"}}')
```

### Common Pitfalls
- Assuming `FEASIBLE` status guarantees optimality; it only indicates a feasible solution was found.
- Not using a tolerance (`math.isclose`) when comparing floating-point numbers during verification, leading to false mismatch errors.
- Attempting to access `solution_value()` on variables when the solver status is not `OPTIMAL` or `FEASIBLE`, causing crashes.
