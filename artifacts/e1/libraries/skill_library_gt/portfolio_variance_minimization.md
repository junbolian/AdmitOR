---
name: Portfolio Variance Minimization
description: |
  Model and solve portfolio optimization problems with quadratic variance objectives under linear constraints, handling incomplete covariance data and solver selection.
---

# Workflow 1 (Dedicated QP Solver)

## Modeling stage

### Strategy Overview
This workflow uses a dedicated quadratic programming (QP) solver, such as those in SciPy or CVXOPT, which natively handle quadratic objectives and linear constraints. It is suitable for problems where a full, valid covariance matrix can be constructed or synthesized.

### Step 1 - Define Problem Dimensions and Data
- Identify the number of assets and gather or synthesize expected returns and a covariance matrix.
- If the covariance matrix is incomplete, construct a synthetic positive definite matrix using variances (e.g., `var_i`) and reasonable correlation assumptions, ensuring symmetry.
- Store parameters as NumPy arrays, converting percentages to decimals consistently.

### Step 2 - Formulate Variables and Bounds
- Define continuous decision variables for portfolio weights, one per asset.
- Set variable bounds, typically `[0, max_weight]` for long-only portfolios with upper limits.

### Step 3 - Specify Objective and Constraints
- Formulate the objective as minimizing the quadratic form `x.T @ cov_matrix @ x`.
- Define the budget constraint as the sum of weights equals one.
- Define the minimum return constraint as a linear inequality: `expected_returns @ x >= min_return`.
- Optionally, add other linear constraints like sector limits.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": {
    "expected_returns": "array per asset",
    "cov_matrix": "square, positive definite matrix",
    "min_return": "scalar threshold",
    "max_weight": "scalar upper bound"
  },
  "decision_variables": ["weights[asset]"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in assets} sum_{j in assets} weights[i] * cov_matrix[i,j] * weights[j]"
  },
  "constraints": [
    {"name": "budget", "expression": "sum(weights) == 1"},
    {"name": "min_return", "expression": "dot(expected_returns, weights) >= min_return"},
    {"name": "upper_bound", "expression": "weights[asset] <= max_weight, for all asset"}
  ]
}
```

### Common Pitfalls
- Using an invalid (non-positive definite) covariance matrix, causing solver failure.
- Mixing percentage and decimal representations inconsistently across parameters.
- Implementing the quadratic objective incorrectly (e.g., with nested loops) instead of using vectorized operations.
- Assuming feasibility without verifying that the minimum return target is achievable given bounds.

## Solving stage

### Strategy Overview
Leverage a QP-capable optimization library. The SciPy `minimize` function with the SLSQP method is a common, accessible choice. This stage involves building the model from the formulation, solving with robust status checks, and validating the solution.

### Step 1 - Configure Solver and Model
- Import the required optimization function (e.g., `scipy.optimize.minimize`).
- Define the objective function and constraint dictionaries/lambda functions as specified in the modeling stage.
- Set an initial guess (e.g., equal weights) and variable bounds.

### Step 2 - Solve and Check Termination Status
- Call the solver with the problem specification.
- Immediately check the solver's success flag or status message. Do not proceed if the status indicates failure or infeasibility.
- For successful solves, extract the optimal variable values.

### Step 3 - Validate Solution and Report Metrics
- Calculate the achieved portfolio return and variance from the optimal weights, independent of the solver's reported objective.
- Numerically verify all constraints (budget, return, bounds) are satisfied within a small tolerance.
- Report key outputs: optimal weights, portfolio variance, achieved return, and constraint checks.

### Code Usage
```python
import numpy as np
from scipy.optimize import minimize

# Assume parameters are defined: cov_matrix, expected_returns, min_return, max_weight, n_assets
# Build model from formulation
def objective(x):
    return x @ cov_matrix @ x

constraints = [
    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
    {'type': 'ineq', 'fun': lambda x: expected_returns @ x - min_return}
]
bounds = [(0, max_weight) for _ in range(n_assets)]
x0 = np.full(n_assets, 1/n_assets)  # Initial guess

# Solve with status / termination checks
result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
if not result.success:
    raise RuntimeError(f"Solver failed: {result.message}")

optimal_weights = result.x
# Post-solution validation
achieved_return = expected_returns @ optimal_weights
achieved_variance = optimal_weights @ cov_matrix @ optimal_weights
print(f"Weights: {optimal_weights}")
print(f"Portfolio Variance: {achieved_variance}")
print(f"Achieved Return: {achieved_return}")
print(f"Return Constraint Met: {achieved_return >= min_return - 1e-6}")
print(f"Sum of Weights: {np.sum(optimal_weights)}")
```

### Common Pitfalls
- Trusting the solver's objective value without recalculating variance from the solution.
- Ignoring non-success solver statuses (e.g., `False` for `success`).
- Not verifying constraint satisfaction numerically, leading to acceptance of slightly infeasible solutions.
- Missing library dependencies; always use try/except blocks for imports in production code.

# Workflow 2 (Linear Solver with Feasibility-Then-Evaluation)

## Modeling stage

### Strategy Overview
This workflow uses a linear programming (LP) solver (e.g., OR-Tools, PuLP) when a dedicated QP solver is unavailable. It finds a feasible portfolio satisfying all linear constraints, then evaluates the variance of that portfolio. This yields a feasible, but not necessarily optimal, solution.

### Step 1 - Define Linear Problem Components
- Identify the same sets, parameters (expected returns, min_return, max_weight), and decision variables (weights) as in Workflow 1.
- Note that the covariance matrix is not used in the model but will be needed for post-hoc evaluation.

### Step 2 - Formulate Linear Constraints Only
- Define the budget constraint (sum of weights == 1).
- Define the minimum return constraint as a linear inequality.
- Define upper bound constraints for each weight.
- The objective for the LP solve is set to a constant (e.g., minimize 0) since the primary goal is feasibility.

### Step 3 - Plan for Post-Hoc Evaluation
- Ensure the covariance matrix is available or synthesized for variance calculation after solving the LP.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": {
    "expected_returns": "array per asset",
    "min_return": "scalar threshold",
    "max_weight": "scalar upper bound"
  },
  "decision_variables": ["weights[asset]"],
  "objective": {
    "sense": "min",
    "expression": "0"
  },
  "constraints": [
    {"name": "budget", "expression": "sum(weights) == 1"},
    {"name": "min_return", "expression": "dot(expected_returns, weights) >= min_return"},
    {"name": "upper_bound", "expression": "weights[asset] <= max_weight, for all asset"}
  ]
}
```

### Common Pitfalls
- Forgetting that this approach does not optimize variance; it only finds a feasible point.
- Using an infeasible minimum return target, causing the LP solver to fail.
- Synthesizing a covariance matrix incorrectly (e.g., not symmetric, not positive definite) for the post-hoc evaluation, making the variance metric meaningless.

## Solving stage

### Strategy Overview
Use a linear programming interface to find any portfolio weights satisfying the linear constraints. After obtaining a feasible solution, calculate its variance using the covariance matrix externally. This provides a baseline feasible portfolio and its risk.

### Step 1 - Build and Solve Linear Model
- Instantiate a linear solver (e.g., `ortools.linear_solver.pywraplp.Solver.CreateSolver('GLOP')`).
- Create continuous variables with appropriate bounds.
- Add the linear constraints as defined.
- Set a dummy objective (e.g., `solver.Minimize(0)`).
- Solve the model and check the result status is `OPTIMAL` or `FEASIBLE`.

### Step 2 - Extract Feasible Solution
- If the solve was successful, retrieve the values of the weight variables.
- If the solver returns `INFEASIBLE`, diagnose constraint conflicts (e.g., minimum return too high).

### Step 3 - Evaluate Portfolio Variance
- Using the extracted feasible weights and the (prepared) covariance matrix, compute the portfolio variance via `weights.T @ cov_matrix @ weights`.
- Also compute the achieved return to confirm constraint satisfaction.

### Code Usage
```python
# Example using OR-Tools linear solver
from ortools.linear_solver import pywraplp
import numpy as np

# Assume parameters are defined: expected_returns, min_return, max_weight, n_assets, cov_matrix
# Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
weights = {}
for i in range(n_assets):
    weights[i] = solver.NumVar(0, max_weight, f'w_{i}')

# Budget constraint
solver.Add(sum(weights[i] for i in range(n_assets)) == 1)
# Return constraint
solver.Add(sum(expected_returns[i] * weights[i] for i in range(n_assets)) >= min_return)
# Dummy objective
solver.Minimize(0)

# Solve with status / termination checks
status = solver.Solve()
if status not in [solver.OPTIMAL, solver.FEASIBLE]:
    raise RuntimeError(f"Linear solver failed to find feasible solution. Status: {status}")

# Extract solution
feasible_weights = np.array([weights[i].solution_value() for i in range(n_assets)])

# Post-hoc evaluation
achieved_return = expected_returns @ feasible_weights
portfolio_variance = feasible_weights @ cov_matrix @ feasible_weights
print(f"Feasible Weights: {feasible_weights}")
print(f"Portfolio Variance (evaluated): {portfolio_variance}")
print(f"Achieved Return: {achieved_return}")
print(f"Return Constraint Met: {achieved_return >= min_return - 1e-6}")
```

### Common Pitfalls
- Assuming the LP solution is optimal for variance; it is merely feasible.
- Not handling the case where the LP solver returns `INFEASIBLE`; the model should include logic to adjust targets or inform the user.
- Calculating variance with an incorrect or mismatched covariance matrix relative to the asset set.
- Over-calling the solver with different synthetic data without addressing core data completeness issues.
