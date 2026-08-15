---
name: Portfolio Optimization as Quadratic Program
description: |
  Model and solve portfolio mean-variance optimization as a convex quadratic program with linear constraints, using specialized QP or general NLP solvers.

---

# Workflow 1 (Pyomo with QP/NLP Solver)

## Modeling stage

### Strategy Overview
Model the portfolio optimization problem as a concrete Pyomo model, defining the quadratic variance objective and linear constraints explicitly. This approach leverages algebraic modeling for clarity and flexibility, suitable for both commercial QP and open-source NLP solvers.

### Step 1 - Define Model Structure
- Instantiate a `ConcreteModel` and create a set representing the assets.
- Declare decision variables for portfolio weights with explicit bounds (e.g., `bounds=(0, max_weight)`).
- Initialize variables near a feasible point, such as equal weights, to aid solver convergence.

### Step 2 - Formulate Quadratic Objective
- Construct the portfolio variance objective as the quadratic form `sum(cov_matrix[i][j] * w[i] * w[j] for i, j in assets)`.
- If a covariance matrix is not provided, assume a reasonable default (e.g., identity matrix) and document this assumption.

### Step 3 - Implement Linear Constraints
- Add a budget constraint enforcing the sum of weights equals one.
- Add a minimum return constraint as a linear inequality using expected asset returns.
- Rely on variable bounds for non-negativity and upper limits; avoid redundant explicit constraints.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["returns", "cov_matrix", "min_return", "max_weight"],
  "decision_variables": [
    {"name": "w", "index": "assets", "bounds": [0, "max_weight"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cov_matrix[i][j] * w[i] * w[j] for i in assets for j in assets)"
  },
  "constraints": [
    {"name": "budget", "expression": "sum(w[i] for i in assets) == 1"},
    {"name": "min_return", "expression": "sum(returns[i] * w[i] for i in assets) >= min_return"}
  ]
}
```

### Common Pitfalls
- Using MIP-specific solver parameters (e.g., `MIPGap`) for a continuous QP, causing errors.
- Forgetting to scope parameters (like `returns`) correctly within Pyomo rules, leading to `NameError`.
- Not validating that the minimum return target is achievable given the provided returns and bounds, resulting in infeasibility.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver factory (e.g., Gurobi for QP, IPOPT for NLP). Check solver status and termination condition rigorously before extracting results, and perform post-solution validation.

### Step 1 - Configure and Run Solver
- Instantiate the solver via `SolverFactory` and set appropriate options (e.g., tolerance, time limit, thread count).
- Call `solve(model, tee=False)` to execute the optimization.

### Step 2 - Validate Solution Status
- Check that `results.solver.status` is `SolverStatus.ok`.
- Verify that `results.solver.termination_condition` indicates optimality or feasibility.
- If the solve fails, output a structured error payload with status and termination details.

### Step 3 - Extract and Verify Results
- Extract optimal weights and objective value using `pyo.value()`.
- Compute the achieved portfolio return from the optimized weights.
- Validate that all constraints are satisfied within a numerical tolerance.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (assume `model` is defined per Modeling stage)
solver = pyo.SolverFactory("solver_name")  # e.g., "gurobi", "ipopt"
solver.options["tol"] = 1e-8
solver.options["TimeLimit"] = 30

results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

ok_terms = {TerminationCondition.optimal,
            TerminationCondition.locallyOptimal,
            TerminationCondition.feasible}

if status == SolverStatus.ok and term in ok_terms:
    weights = [float(pyo.value(model.w[i])) for i in model.assets]
    objective = float(pyo.value(model.obj))
    portfolio_return = sum(returns[i] * weights[i] for i in range(len(returns)))
    # Output results
else:
    # Handle failure
    raise RuntimeError(f"Solver failed: {status}, {term}")
```

### Common Pitfalls
- Not converting Pyomo numeric values to standard Python floats before further calculations.
- Assuming optimal termination without checking for `feasible` or `locallyOptimal` conditions, which may be acceptable.
- Omitting post-solution validation, potentially missing constraint violations due to numerical tolerances.

---

# Workflow 2 (SciPy with SLSQP)

## Modeling stage

### Strategy Overview
Formulate the portfolio optimization problem directly for SciPy's `minimize` function, representing the quadratic objective and constraints in a format compatible with sequential quadratic programming (SLSQP). This is a lightweight approach suitable for convex QPs without external solver dependencies.

### Step 1 - Define Problem Dimensions and Data
- Determine the number of assets `n`.
- Prepare the covariance matrix; if missing, use an identity matrix as default.
- Prepare arrays for expected returns, minimum return target, and weight upper bound.

### Step 2 - Construct Objective Function
- Define a function that computes the portfolio variance: `0.5 * w @ cov_matrix @ w` (the 0.5 factor improves numerical stability for quadratic forms).
- For an identity covariance, the objective simplifies to `0.5 * sum(w_i**2)`.

### Step 3 - Encode Constraints and Bounds
- Create a list of constraint dictionaries: an equality constraint for the budget and an inequality constraint for the minimum return.
- Define a list of `(lower, upper)` tuples for variable bounds to enforce non-negativity and maximum weight.

### Formulation Template
```json
{
  "sets": [],
  "parameters": ["returns", "cov_matrix", "min_return", "max_weight"],
  "decision_variables": ["w"],
  "objective": {
    "sense": "min",
    "expression": "0.5 * w @ cov_matrix @ w"
  },
  "constraints": [
    {"type": "eq", "expression": "sum(w) - 1"},
    {"type": "ineq", "expression": "returns @ w - min_return"}
  ],
  "bounds": ["(0, max_weight) for each variable"]
}
```

### Common Pitfalls
- Forgetting the 0.5 factor in the quadratic objective, which does not affect the optimum but changes the objective value.
- Incorrectly ordering or typing constraints (e.g., using `'eq'` for inequality).
- Not providing an initial guess (e.g., equal weights), which can slow convergence.

## Solving stage

### Strategy Overview
Use SciPy's `minimize` with method `'SLSQP'` to solve the formulated problem. Check the optimization result's success flag and validate the solution against constraints.

### Step 1 - Configure and Execute Optimizer
- Call `minimize` with the objective function, initial guess, constraints, bounds, and method `'SLSQP'`.
- Set optional tolerances (e.g., `tol=1e-8`) for convergence criteria.

### Step 2 - Check Optimization Success
- Inspect the result's `success` attribute.
- If `success` is `False`, review the `message` and `status` for diagnostics.

### Step 3 - Validate and Report Solution
- Extract the optimal weight vector.
- Verify that constraints are satisfied within tolerance (e.g., sum of weights ≈ 1).
- Compute the actual portfolio variance and return for reporting.

### Code Usage
```python
import numpy as np
from scipy.optimize import minimize

# Assume `returns`, `cov_matrix`, `min_return`, `max_weight` are defined
n_assets = len(returns)
initial_guess = np.ones(n_assets) / n_assets  # Equal weights
bounds = [(0, max_weight) for _ in range(n_assets)]

# Objective
def portfolio_variance(w):
    return 0.5 * w @ cov_matrix @ w

# Constraints
constraints = [
    {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
    {'type': 'ineq', 'fun': lambda w: returns @ w - min_return}
]

result = minimize(portfolio_variance, initial_guess,
                  method='SLSQP', bounds=bounds,
                  constraints=constraints, tol=1e-8)

if result.success:
    weights = result.x
    objective_value = 2 * result.fun  # Adjust if 0.5 factor was used
    portfolio_return = returns @ weights
    # Output results
else:
    raise RuntimeError(f"Optimization failed: {result.message}")
```

### Common Pitfalls
- Misinterpreting the objective value: if the objective function includes a 0.5 factor, the true variance is `2 * result.fun`.
- Not verifying constraint satisfaction numerically, which can mask small violations.
- Using an inappropriate method (e.g., `'COBYLA'`) that may not handle quadratic objectives as efficiently as SLSQP.
