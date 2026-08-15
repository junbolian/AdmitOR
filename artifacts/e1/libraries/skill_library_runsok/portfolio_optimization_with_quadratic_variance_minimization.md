---
name: Portfolio Optimization with Quadratic Variance Minimization
description: |
  Model and solve portfolio optimization problems with variance minimization objectives, linear constraints, and continuous decision variables using quadratic programming solvers.
---

# Workflow 1 (Commercial Solver with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's algebraic modeling framework to construct a convex quadratic program, leveraging a commercial solver's efficiency for large-scale problems. The model is built with explicit sets and parameters for clarity and scalability.

### Step 1 - Define Model Structure
- Instantiate a `ConcreteModel` and define a `Set` for the collection of assets.
- Declare `Param` objects for expected returns, variances, and a covariance dictionary for off-diagonal terms.
- Define continuous `Var` objects for portfolio weights, using `bounds=(0, max_weight)` to enforce position limits directly.

### Step 2 - Construct Quadratic Objective
- Formulate the portfolio variance as the sum of variance terms (`variances[i] * w[i]**2`) plus twice the sum of covariance terms (`2 * covariances[(i,j)] * w[i] * w[j]`) for all `i < j`.
- Use Pyomo's `summation` or a loop to build the expression incrementally, ensuring symmetric covariance pairs are counted once and doubled correctly.
- Set the objective to minimize this variance expression.

### Step 3 - Implement Linear Constraints
- Add a budget constraint as an equality: the sum of all portfolio weights must equal 1.
- Add a return target constraint as an inequality: the weighted sum of expected returns must meet or exceed a minimum threshold.
- Rely on variable bounds for position limits; avoid creating separate constraints for upper bounds unless necessary for reporting.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["expected_returns", "variances", "covariances", "min_return", "max_weight"],
  "decision_variables": ["w"],
  "objective": {
    "sense": "min",
    "expression": "sum(variances[i] * w[i]**2 for i in assets) + 2 * sum(covariances[(i,j)] * w[i] * w[j] for i,j in assets if i < j)"
  },
  "constraints": [
    "budget: sum(w[i] for i in assets) == 1",
    "return_target: sum(expected_returns[i] * w[i] for i in assets) >= min_return"
  ]
}
```

### Common Pitfalls
- Forgetting to multiply off-diagonal covariance terms by 2, leading to an incorrect variance calculation.
- Defining separate upper-bound constraints for each variable instead of using the more efficient `bounds` argument in the variable declaration.
- Using a dense covariance matrix parameter when a dictionary for off-diagonal terms is sufficient, which can slow down model construction for large asset universes.

## Solving stage

### Strategy Overview
Solve the model using a commercial quadratic programming solver via Pyomo's `SolverFactory`. Configure solver options for performance and reliability, implement robust solution status checks, and validate results post-solve.

### Step 1 - Configure and Execute Solver
- Instantiate the solver (e.g., `SolverFactory('gurobi')`).
- Set key options such as `TimeLimit`, `MIPGap` (for QP), `Threads`, and `Seed` for reproducibility.
- Call `solver.solve(model)` and capture the results object.

### Step 2 - Check Solver Status and Termination
- Inspect `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `SolverStatus.ok` and termination is `TerminationCondition.optimal` or `.feasible`.
- For any other status, output a structured error message and halt processing.

### Step 3 - Validate and Extract Solution
- Extract the objective value using `pyo.value(model.objective)`.
- Iterate through decision variables to retrieve the optimal portfolio weights.
- Programmatically verify constraint satisfaction (budget sum, return target, bounds) within a small numerical tolerance.
- Print the objective value with a `"RESULT:"` prefix for automated parsing and optionally output detailed weights and constraint checks.

### Code Usage
```python
import pyomo.environ as pyo

# Assume 'model' is already built per the Modeling stage
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = -1.0  # Use -1 for QP optimality tolerance
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model)

# Status and termination checks
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    obj_val = pyo.value(model.objective)
    print(f"RESULT:{obj_val}")
    # Extract and validate solution...
else:
    print(f"ERROR: Solve failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming the solve was successful without checking termination conditions, potentially using invalid solution values.
- Setting solver options that conflict with the problem type (e.g., MIP-specific options for a continuous QP).
- Not providing a fallback solver or error handling, causing the workflow to crash on solver unavailability.

# Workflow 2 (Open-Source Solver with Direct Matrix Formulation)

## Modeling stage

### Strategy Overview
This workflow uses a matrix-based formulation, constructing the quadratic objective via a covariance matrix, and is designed for use with open-source solvers. It emphasizes a compact model structure suitable for smaller problems or environments without commercial licenses.

### Step 1 - Define Model with Matrix Parameters
- Create a `ConcreteModel` and an asset `Set`.
- Declare a `Param` representing the full covariance matrix (a 2D array) and a vector `Param` for expected returns.
- Define portfolio weight variables with `bounds=(0, max_weight)`.

### Step 2 - Build Objective Using Matrix Multiplication
- Construct the portfolio variance using Pyomo's expression for quadratic form: `sum( sum( cov_matrix[i,j] * w[i] * w[j] for j in assets ) for i in assets )`.
- Alternatively, use a pre-computed matrix if the modeling interface supports it. Set this as the minimization objective.

### Step 3 - Implement Standard Linear Constraints
- Add the budget equality constraint (`sum(w[i]) == 1`).
- Add the return target inequality constraint using the dot product of the expected returns vector and weight variables.
- Use variable bounds for position limits.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["expected_returns", "cov_matrix", "min_return", "max_weight"],
  "decision_variables": ["w"],
  "objective": {
    "sense": "min",
    "expression": "sum( sum( cov_matrix[i,j] * w[i] * w[j] for j in assets ) for i in assets )"
  },
  "constraints": [
    "budget: sum(w[i] for i in assets) == 1",
    "return_target: sum(expected_returns[i] * w[i] for i in assets) >= min_return"
  ]
}
```

### Common Pitfalls
- Supplying a non-positive semidefinite covariance matrix, which can make the QP non-convex and cause solver failures with open-source solvers.
- Using an inefficient double summation for the quadratic form on very large asset universes, impacting model construction time.
- Neglecting to provide an initial feasible solution (e.g., equal weights), which can hinder convergence for some nonlinear solvers.

## Solving stage

### Strategy Overview
Solve the model using an open-source solver (e.g., HiGHS, IPOPT) via Pyomo, with a fallback to a SciPy optimizer. This approach prioritizes accessibility and includes explicit verification of solution optimality.

### Step 1 - Attempt Primary Open-Source Solver
- Instantiate the primary solver (e.g., `SolverFactory('highs')` for QP).
- Set essential options like `time_limit`. Avoid advanced options unless necessary.
- Solve the model and capture results.

### Step 2 - Implement Solver Fallback Mechanism
- If the primary solver is not available or fails, attempt an alternative (e.g., `SolverFactory('ipopt')` for NLP).
- For the fallback, configure appropriate tolerances (`tol`, `acceptable_tol`) and iteration limits.
- As a last resort, extract the Pyomo model's components and solve using `scipy.minimize` with the `'SLSQP'` method, defining the objective as `w @ cov_matrix @ w`.

### Step 3 - Verify and Report Solution
- Check solver status and termination condition rigorously. For open-source solvers, also accept `TerminationCondition.locallyOptimal`.
- Extract variable values and the objective value.
- Perform post-solution validation: compute the actual portfolio return and sum of weights to ensure constraints are met within tolerance.
- Output the result in a consistent format (`RESULT:{objective_value}`) and provide detailed diagnostics if the solve fails.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Assume 'model' is built per the Modeling stage
solver_names = ['highs', 'ipopt']
solver = None
results = None

for name in solver_names:
    solver = pyo.SolverFactory(name)
    if solver.available():
        if name == 'ipopt':
            solver.options['tol'] = 1e-8
            solver.options['max_iter'] = 1000
        results = solver.solve(model)
        break

if results is None:
    # Fallback to SciPy
    import numpy as np
    from scipy.optimize import minimize
    # ... (extract parameters, define objective and constraints) ...
    # res = minimize(objective, x0, constraints=cons, method='SLSQP')
    # Process SciPy result
else:
    # Check Pyomo solver results
    if (results.solver.status == SolverStatus.ok and
        results.solver.termination_condition in (TerminationCondition.optimal,
                                                  TerminationCondition.locallyOptimal,
                                                  TerminationCondition.feasible)):
        obj_val = pyo.value(model.objective)
        print(f"RESULT:{obj_val}")
    else:
        print(f"ERROR: Solve unsuccessful with {solver}.")
```

### Common Pitfalls
- Not verifying solver availability (`solver.available()`) before calling `solve`, leading to cryptic errors.
- Using solver options inappropriate for the problem type (e.g., linear solver options for a nonlinear solver like IPOPT).
- Failing to provide a fallback path, rendering the workflow unusable in restricted software environments.
