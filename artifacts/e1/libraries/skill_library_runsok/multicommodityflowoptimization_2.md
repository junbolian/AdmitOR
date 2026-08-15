---
name: MultiCommodityFlowOptimization
description: |
  Model and solve multi-commodity flow problems with shared arc capacities, using structured decision variables and systematic constraint building for linear cost minimization.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (OR-Tools) for explicit model construction, focusing on procedural variable and constraint creation with nested loops. It is well-suited for rapid prototyping and scenarios where model data is already in simple Python data structures.

### Step 1 - Define Data Structures and Sets
- Create explicit lists or sets for origins, destinations, and commodities to structure the model.
- Use nested dictionaries or 3D lists to store parameters (cost, supply, demand, capacity) with indices matching the variable structure.

### Step 2 - Create Multi-Dimensional Flow Variables
- Instantiate a continuous, non-negative decision variable for each origin-destination-commodity combination (e.g., `x[i][j][k]`).
- Use descriptive naming with indices (e.g., `f"x_{i}_{j}_{k}"`) to aid in debugging and solution inspection.

### Step 3 - Build Supply and Demand Equality Constraints
- For each origin and commodity, create a linear equality constraint: sum of outgoing flows equals the available supply.
- For each destination and commodity, create a linear equality constraint: sum of incoming flows equals the required demand.

### Step 4 - Apply Aggregated Arc Capacity Constraints
- For each origin-destination pair, create a linear inequality constraint: the sum of flows for all commodities must be less than or equal to the arc capacity.

### Step 5 - Formulate Linear Cost Objective
- Define the objective as the minimization of the total cost, calculated as the sum of each flow multiplied by its per-unit cost coefficient.

### Formulation Template
```json
{
  "sets": ["origins", "destinations", "commodities"],
  "parameters": [
    "cost[origin][destination][commodity]",
    "supply[origin][commodity]",
    "demand[destination][commodity]",
    "capacity[origin][destination]"
  ],
  "decision_variables": ["flow[origin][destination][commodity] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j][k] * flow[i][j][k] )"
  },
  "constraints": [
    "sum_j flow[i][j][k] == supply[i][k] for all i, k",
    "sum_i flow[i][j][k] == demand[j][k] for all j, k",
    "sum_k flow[i][j][k] <= capacity[i][j] for all i, j"
  ]
}
```

### Common Pitfalls
- Using inconsistent indexing between parameters and variables, leading to incorrect constraint coefficients.
- Forgetting to set upper bounds on variables, which may default to infinity and hide model errors.
- Not verifying that total supply equals total demand for each commodity before solving, which can cause infeasibility.

## Solving stage

### Strategy Overview
Solve the linear program using a dedicated LP solver (e.g., GLOP) via OR-Tools' wrapper. Focus on systematic coefficient assignment, rigorous solution status checking, and post-solution validation.

### Step 1 - Initialize Solver and Objective
- Create a linear solver instance (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Instantiate the objective function and set its minimization sense.

### Step 2 - Build Constraints with Nested Loops
- Use triple-nested loops to create supply, demand, and capacity constraints, adding variable coefficients within the innermost loop.
- Keep constraint creation blocks separate for clarity and easier debugging.

### Step 3 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the result status explicitly (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`) before attempting to read solution values. Provide clear error messages for non-optimal statuses.

### Step 4 - Extract and Validate Solution
- Retrieve the objective value and all flow variable values.
- Programmatically recompute key sums (e.g., total flow from each origin for each commodity) and compare them against the original supply and demand parameters within a small tolerance (e.g., 1e-6) to validate model correctness.

### Step 5 - Report and Analyze Results
- Print a summary of the total cost and key statistics.
- Optionally, list only non-zero flows (values > tolerance) to simplify interpretation.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... create variables, constraints, objective ...

# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL:
    print(f'Optimal cost: {solver.Objective().Value()}')
    # ... extract and validate solution ...
elif status == solver.FEASIBLE:
    print('Feasible solution found, but not proven optimal.')
else:
    print('The problem does not have an optimal solution.')
```

### Common Pitfalls
- Assuming the solver status is `OPTIMAL` without checking, leading to errors when accessing solution values from an infeasible or unbounded model.
- Not using a tolerance when checking flow sums against supply/demand, causing false failures due to floating-point arithmetic.
- Omitting solver output (`solver.EnableOutput()`) during initial runs, missing valuable debugging information.

# Workflow 2 (Modeling Language - Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses a modeling language (Pyomo) for declarative model definition, separating the abstract formulation from the data. It enhances maintainability, readability, and is ideal for complex, data-driven applications.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for origins, destinations, and commodities.
- Define `Param` objects for cost, supply, demand, and capacity, indexed over the appropriate sets, to establish the model's abstract structure.

### Step 2 - Define Indexed Flow Variables
- Declare a single, indexed `Var` object (e.g., `model.flow`) over the Cartesian product of origin, destination, and commodity sets, with a lower bound of zero.

### Step 3 - Express Constraints Declaratively
- Use Pyomo's `Constraint` component with rule functions to define supply, demand, and capacity constraints. Each rule receives the model and the relevant indices.
- Write the constraint expressions using summations over the model sets for clarity (e.g., `sum(model.flow[i, j, k] for j in model.Destinations)`).

### Step 4 - Formulate the Objective
- Define the objective as a `summation` of `flow * cost` over all indices, using the `sense=minimize` attribute.

### Formulation Template
```json
{
  "sets": ["model.Origins", "model.Destinations", "model.Commodities"],
  "parameters": [
    "model.cost[O, D, C]",
    "model.supply[O, C]",
    "model.demand[D, C]",
    "model.capacity[O, D]"
  ],
  "decision_variables": ["model.flow[O, D, C] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[o,d,c] * model.flow[o,d,c] for o,d,c)"
  },
  "constraints": [
    "Supply: sum(model.flow[o,d,c] for d) == model.supply[o,c] for all o,c",
    "Demand: sum(model.flow[o,d,c] for o) == model.demand[d,c] for all d,c",
    "Capacity: sum(model.flow[o,d,c] for c) <= model.capacity[o,d] for all o,d"
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's 1-based indexing with Python's 0-based indexing when populating parameters from data.
- Defining constraint rules that inadvertently close over and use mutable external data, causing stale values.
- Not initializing all required indices of a sparse parameter, which can lead to "KeyError" during model construction.

## Solving stage

### Strategy Overview
Solve the model using a solver factory (e.g., HiGHS, CBC) interfaced through Pyomo. Emphasize proper solver configuration, detailed termination condition analysis, and structured solution handling.

### Step 1 - Instantiate Model with Data
- Create a `ConcreteModel` and populate its `Param` objects with the actual problem data, ensuring all indices required by the constraints are provided.

### Step 2 - Configure and Execute Solver
- Use `SolverFactory` to create a solver instance.
- Set solver options (e.g., time limit, optimality tolerance) appropriate for the problem size and required precision.
- Call `solve(model, tee=False)` to execute, using `tee=True` for initial debugging output.

### Step 3 - Inspect Solver Status and Termination Condition
- After solving, check both `results.solver.status` (e.g., `ok`, `error`) and `results.solver.termination_condition` (e.g., `optimal`, `feasible`, `infeasible`).
- Proceed to solution extraction only if the status indicates a valid solution is available.

### Step 4 - Extract and Verify Solution
- Safely access the objective value via `pyo.value(model.obj)`.
- Iterate over the flow variable index and retrieve solution values, applying a tolerance filter (e.g., `1e-6`) to identify non-zero flows.
- Optionally, implement a post-solve verification function that recomputes constraint left-hand sides and compares them to right-hand sides.

### Step 5 - Report Results and Handle Failures
- Print a summary report. For failed or suboptimal solves, output a structured dictionary or JSON containing the status, termination condition, and any error messages for downstream analysis.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print(f'Optimal cost: {pyo.value(model.obj)}')
    elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
        print('Feasible solution found.')
    # ... extract solution ...
else:
    print('Solver failed:', results.solver.message)
```

### Common Pitfalls
- Accessing variable values (`var.value`) without first checking the solver termination condition, potentially loading values from an unsolved or infeasible model.
- Using default solver settings that may be inappropriate for the problem scale, leading to long solve times or premature termination.
- Neglecting to deactivate the `tee` flag in production, causing excessive log output.
