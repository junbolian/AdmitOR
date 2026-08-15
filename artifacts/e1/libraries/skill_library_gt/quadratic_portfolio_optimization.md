---
name: Quadratic Portfolio Optimization
description: |
  Model and solve portfolio optimization problems with variance minimization, linear constraints, and continuous weights using quadratic programming formulations.
---

# Workflow 1 (Pyomo with NLP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to formulate a quadratic program (QP) for portfolio optimization, treating the covariance matrix as a parameter. It is designed for use with nonlinear programming (NLP) solvers like IPOPT, which can handle convex QPs efficiently.

### Step 1 - Define Model Structure
- Create a Pyomo `ConcreteModel` to hold all components.
- Define a `Set` for assets, typically using `pyo.RangeSet` or `pyo.Set(initialize=range(n_assets))`.
- Declare `Param` objects for the expected returns vector and the covariance matrix, ensuring they are indexed appropriately.

### Step 2 - Declare Decision Variables and Bounds
- Define continuous decision variables for portfolio weights, e.g., `model.w = pyo.Var(model.assets, bounds=(0, max_weight))`.
- Set explicit upper bounds per asset to enforce diversification limits.

### Step 3 - Formulate Quadratic Objective
- Construct the portfolio variance objective as a double summation: `sum(model.w[i] * model.covariance[i, j] * model.w[j] for i in model.assets for j in model.assets)`.
- Attach it to the model as a minimization objective using `pyo.Objective(expr=..., sense=pyo.minimize)`.

### Step 4 - Add Linear Constraints
- Add a budget constraint enforcing that weights sum to one: `pyo.Constraint(expr=sum(model.w[i] for i in model.assets) == 1)`.
- Add a minimum return constraint: `pyo.Constraint(expr=sum(model.w[i] * model.expected_returns[i] for i in model.assets) >= min_return)`.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["expected_returns", "covariance_matrix", "min_return", "max_weight"],
  "decision_variables": ["w"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in assets} sum_{j in assets} w[i] * covariance_matrix[i,j] * w[j]"
  },
  "constraints": [
    "sum_{i in assets} w[i] == 1",
    "sum_{i in assets} expected_returns[i] * w[i] >= min_return",
    "0 <= w[i] <= max_weight for all i in assets"
  ]
}
```

### Common Pitfalls
- Assuming missing covariance data can be fabricated arbitrarily without justification, leading to non-reproducible results.
- Using an incomplete covariance matrix (e.g., empty or identity) which misrepresents asset correlations and invalidates the variance objective.
- Formulating the variance as a simple sum of squares unless assets are explicitly uncorrelated.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an NLP solver configured for quadratic problems. Focus on robust solver setup, status checking, and post-solution validation of constraints and derived metrics.

### Step 1 - Configure Solver
- Use `pyo.SolverFactory('ipopt')` (or another NLP solver).
- Set key options for reliability and precision: `tol=1e-7`, `max_iter=500`, `acceptable_tol=1e-5`, `print_level=0` to suppress verbose output.

### Step 2 - Execute Solve with Robust Checks
- Wrap the solver call in a try-except block to catch exceptions.
- After solving, check both `results.solver.status == pyo.SolverStatus.ok` and `results.solver.termination_condition` (acceptable values: `optimal`, `locallyOptimal`, `feasible`).
- If status or termination is not acceptable, diagnose infeasibility or numerical issues before proceeding.

### Step 3 - Extract and Validate Results
- Retrieve optimal weights and the objective value from the model instance.
- Manually compute the portfolio's expected return using optimal weights to verify the minimum return constraint is satisfied.
- Verify the sum of weights equals 1 (within a small tolerance) and that all weights respect their bounds.

### Step 4 - Handle Missing Data with Defaults
- If a covariance matrix is not provided, construct a synthetic, positive-definite matrix for testing. For example, use volatilities proportional to expected returns and a moderate correlation: `σ_i = 0.3 * r_i`, `ρ = 0.2`, then build `covariance[i,j] = σ_i * σ_j * ρ` for i≠j and `covariance[i,i] = σ_i²`.
- Clearly document any synthetic data assumptions in the output.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
model.assets = pyo.RangeSet(0, n_assets-1)
model.expected_returns = pyo.Param(model.assets, initialize=expected_returns_dict)
model.covariance = pyo.Param(model.assets, model.assets, initialize=covariance_dict)
model.w = pyo.Var(model.assets, bounds=(0, max_weight))

model.obj = pyo.Objective(
    expr=sum(model.w[i] * model.covariance[i, j] * model.w[j] for i in model.assets for j in model.assets),
    sense=pyo.minimize
)
model.budget = pyo.Constraint(expr=sum(model.w[i] for i in model.assets) == 1)
model.return_req = pyo.Constraint(expr=sum(model.w[i] * model.expected_returns[i] for i in model.assets) >= min_return)

# Solve with status / termination checks
solver = pyo.SolverFactory('ipopt')
solver.options['tol'] = 1e-7
solver.options['max_iter'] = 500
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                              pyo.TerminationCondition.locallyOptimal,
                                              pyo.TerminationCondition.feasible]):
    # Extract results
    weights = [pyo.value(model.w[i]) for i in model.assets]
    variance = pyo.value(model.obj)
else:
    # Handle failure
    raise RuntimeError(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Ignoring solver errors or unknown statuses and proceeding as if the solve succeeded.
- Setting solver options that conflict with the environment (e.g., `threads` causing errors in certain solvers).
- Not verifying constraint satisfaction post-solve, leading to acceptance of invalid solutions.

# Workflow 2 (Direct QP Solver Interface)

## Modeling stage

### Strategy Overview
This workflow formulates the portfolio optimization problem as a standard quadratic program (QP) in matrix form, suitable for direct interface with dedicated QP solvers (e.g., via `cvxopt`, `quadprog`, or solver-specific APIs). It emphasizes the canonical `min (1/2) x' P x + q' x` form.

### Step 1 - Map to Canonical QP Form
- Identify the decision variable vector `x` as the portfolio weights.
- Construct the quadratic coefficient matrix `P` as `2 * covariance_matrix` (if the solver expects `(1/2) x' P x`).
- Set the linear coefficient vector `q` to zero for pure variance minimization.

### Step 2 - Encode Linear Constraints
- Express the equality constraint (sum of weights = 1) as `A_eq * x = b_eq`.
- Express the inequality constraint (minimum return) as `A_ineq * x >= b_ineq`. Combine with upper bound constraints `x <= ub` as part of the inequality matrix or as separate variable bounds.
- Ensure all constraint matrices and vectors are correctly dimensioned.

### Step 3 - Define Variable Bounds
- Specify explicit lower bounds (typically 0) and upper bounds per asset.
- If the solver supports bound constraints directly, use them; otherwise, incorporate them as inequality constraints.

### Formulation Template
```json
{
  "sets": ["n_assets"],
  "parameters": ["covariance_matrix", "expected_returns", "min_return", "max_weight"],
  "decision_variables": ["x"],
  "objective": {
    "sense": "min",
    "expression": "(1/2) * x' * P * x"
  },
  "constraints": [
    "A_eq * x == b_eq  # sum(x) == 1",
    "A_ineq * x >= b_ineq  # expected_returns' * x >= min_return",
    "0 <= x_i <= max_weight for all i"
  ]
}
```

### Common Pitfalls
- Forgetting to scale the covariance matrix by 2 when using the `(1/2) x' P x` convention, leading to incorrect objective values.
- Incorrectly signing inequality constraints (e.g., using `<=` for minimum return requirement).
- Providing a covariance matrix that is not positive semi-definite, causing solver failures.

## Solving stage

### Strategy Overview
Call a dedicated QP solver with the canonical matrices and vectors. This workflow often yields faster and more numerically stable solutions for convex QPs. It requires careful matrix construction and solver option configuration.

### Step 1 - Prepare Solver Inputs
- Assemble `P`, `q`, `A`, `b`, `A_eq`, `b_eq`, `lb`, and `ub` according to the solver's API.
- Ensure the covariance matrix is positive semi-definite; if necessary, add a small diagonal term for numerical stability.

### Step 2 - Configure and Run Solver
- Select an appropriate QP solver (e.g., `cvxopt.solvers.qp`, `quadprog.solve_qp`, or a commercial solver's API).
- Set solver-specific options for tolerance, iteration limits, and verbosity.
- Execute the solver call within a try-except block to handle input errors or infeasibility.

### Step 3 - Interpret Solver Output
- Check the solver's exit flag or status code. A status of `optimal` or `converged` indicates success.
- Extract the solution vector (optimal weights) and the optimal objective value.
- If the solver reports `infeasible` or `unbounded`, analyze the constraints for conflicts or errors.

### Step 4 - Validate and Report Solution
- Compute the achieved portfolio return and variance from the solution vector to verify they meet constraints.
- Report the solution in a standardized format, including weights, objective value, and constraint satisfaction checks.

### Code Usage
```python
import numpy as np
import cvxopt
from cvxopt import matrix, solvers

# Build model from formulation
# P = 2 * covariance_matrix for (1/2) x' P x form
P = matrix(2.0 * covariance_matrix)
q = matrix(np.zeros(n_assets))
# Equality constraint: sum(x) = 1
A_eq = matrix(np.ones((1, n_assets)))
b_eq = matrix(1.0)
# Inequality constraint: expected_returns' * x >= min_return  ->  -expected_returns' * x <= -min_return
A_ineq = matrix(-expected_returns.reshape(1, n_assets))
b_ineq = matrix(-min_return)
# Combine equality and inequality for cvxopt (G, h for inequalities, A, b for equalities)
G = matrix(np.vstack([-np.eye(n_assets), np.eye(n_assets)]))  # for bounds: -x <= 0 and x <= ub
h = matrix(np.hstack([np.zeros(n_assets), np.full(n_assets, max_weight)]))

solvers.options['show_progress'] = False
solvers.options['abstol'] = 1e-7
solvers.options['reltol'] = 1e-6
solvers.options['maxiters'] = 100

# Solve with status / termination checks
solution = solvers.qp(P, q, G, h, A_eq, b_eq)

if solution['status'] == 'optimal':
    weights = np.array(solution['x']).flatten()
    variance = solution['primal objective']
else:
    raise RuntimeError(f"QP solver failed with status: {solution['status']}")
```

### Common Pitfalls
- Passing a non-positive-definite `P` matrix without regularization, causing the solver to fail.
- Misinterpreting solver status codes (e.g., treating `unknown` as success).
- Neglecting to scale the objective correctly for the solver's expected form, resulting in a variance off by a factor of 2.
