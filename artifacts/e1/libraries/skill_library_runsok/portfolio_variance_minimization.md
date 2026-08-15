---
name: Portfolio Variance Minimization
description: |
  Model and solve portfolio allocation problems with quadratic variance minimization, budget, return target, and allocation bounds using specialized QP solvers or general-purpose optimization libraries.
---

# Workflow 1 (Pyomo with Commercial/High-Performance Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's algebraic modeling language to build a precise quadratic optimization model, suitable for interfacing with high-performance solvers like Gurobi or HiGHS. It emphasizes a clean separation of data and model structure, explicit handling of symmetric covariance terms, and efficient use of variable bounds.

### Step 1 - Define Data Structures
- Separate input data from the model building logic for clarity and reusability.
- Define sets (e.g., assets), scalar parameters (e.g., target return, max allocation), and dictionaries for returns, variances, and a full or upper-triangular covariance matrix.

### Step 2 - Build Algebraic Model
- Instantiate a `pyo.ConcreteModel()` and define a `pyo.Set` for assets.
- Declare `pyo.Param` objects for returns and variances, initialized from the input dictionaries.
- For covariances, define a `pyo.Set` for asset pairs and a corresponding `pyo.Param`, ensuring symmetry by including both `(i,j)` and `(j,i)` or by iterating over `i<j` in the objective.
- Create continuous, non-negative decision variables `x[i]` with an upper bound defined directly in the variable declaration.

### Step 3 - Formulate Quadratic Objective
- Construct the portfolio variance objective as `xᵀQx`.
- Implement this as a rule summing diagonal variance terms (`variances[i] * x[i]**2`) and off-diagonal covariance terms (`2 * covariances[i,j] * x[i] * x[j]` for `i<j`).
- Set the objective sense to minimize.

### Step 4 - Add Linear Constraints
- Add a budget constraint enforcing that the sum of allocations equals 1.
- Add a return target constraint ensuring the weighted sum of returns meets or exceeds the minimum required return.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": [
    {"name": "returns", "index": "assets"},
    {"name": "variances", "index": "assets"},
    {"name": "covariances", "index": ["assets", "assets"]},
    {"name": "min_return", "type": "scalar"},
    {"name": "max_alloc", "type": "scalar"}
  ],
  "decision_variables": [
    {"name": "x", "index": "assets", "domain": "NonNegativeReals", "bounds": [0, "max_alloc"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(variances[i] * x[i]^2 for i in assets) + 2 * sum(covariances[i,j] * x[i] * x[j] for i,j in assets where i < j)"
  },
  "constraints": [
    {"name": "budget", "expression": "sum(x[i] for i in assets) == 1"},
    {"name": "return_target", "expression": "sum(returns[i] * x[i] for i in assets) >= min_return"}
  ]
}
```

### Common Pitfalls
- Forgetting to include symmetric covariance terms (`(i,j)` and `(j,i)`) in the parameter initialization, leading to an incorrect objective.
- Adding separate constraints for individual upper bounds instead of leveraging the more efficient variable bounds declaration.
- Using a dense covariance matrix parameter without filtering for `i != j`, which is inefficient but not incorrect if covariances for `i=j` are set to variances.

## Solving stage

### Strategy Overview
This stage focuses on solving the Pyomo model with a capable quadratic programming solver, configuring it for performance and precision, rigorously checking the solution status, and extracting and validating the results.

### Step 1 - Configure and Execute Solver
- Instantiate the solver factory (e.g., `SolverFactory("gurobi")` or `SolverFactory("highs")`).
- Set solver-specific options such as time limit, optimality gap tolerance (`MIPGap`), number of threads, and a random seed for reproducibility.
- Call `solver.solve(model, tee=True)` to execute and monitor the log.

### Step 2 - Validate Solution Status
- Check that the solver status (`results.solver.status`) is `SolverStatus.ok`.
- Check that the termination condition (`results.solver.termination_condition`) is `optimal` or `feasible`.
- If either check fails, return a detailed error payload without attempting to extract variable values.

### Step 3 - Extract and Verify Results
- Extract the objective value using `pyo.value(model.obj)`.
- Extract allocations by iterating over `model.assets` and retrieving `model.x[i].value`.
- Programmatically verify that key constraints (budget sum, return target) are satisfied within a small tolerance.
- Compute derived metrics like the actual portfolio return.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Assume `model` is built using the steps above
solver = pyo.SolverFactory("gurobi")  # or "highs"
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = 0.0
solver.options["Threads"] = -1
solver.options["Seed"] = 42

results = solver.solve(model, tee=True)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = float(pyo.value(model.obj))
    allocations = {i: model.x[i].value for i in model.assets}
    # Verification
    total_alloc = sum(allocations.values())
    actual_return = sum(pyo.value(model.returns[i]) * allocations[i] for i in model.assets)
    # Return results dictionary
else:
    # Return failure dictionary with status and term
```

### Common Pitfalls
- Proceeding to extract variable values without confirming the solver status and termination condition, which can lead to errors or misleading results.
- Not verifying that the extracted solution satisfies the model constraints within a numerical tolerance.
- Assuming dual values are available for all constraints when using certain solvers or problem types.

# Workflow 2 (Matrix-based Formulation with SciPy)

## Modeling stage

### Strategy Overview
This workflow employs a matrix-based approach, constructing the covariance matrix `Q` and using SciPy's optimization interface. It is suitable for environments without specialized QP solvers and leverages SciPy's ability to handle general nonlinear constraints, including quadratic objectives.

### Step 1 - Construct Covariance Matrix
- Build a symmetric `n x n` covariance matrix `Q` from input variances and covariances.
- Place variances on the diagonal.
- Fill off-diagonal elements with the corresponding covariance values, ensuring symmetry (`Q[i,j] = Q[j,i]`).

### Step 2 - Define Optimization Problem in Functional Form
- Define the objective function as `f(x) = x.T @ Q @ x`.
- Define the initial guess `x0` (e.g., equal allocation `1/n`).
- Set variable bounds as a list of tuples `(0, max_alloc)` for each asset.

### Step 3 - Specify Constraints as Dictionaries
- Formulate the budget constraint as an equality: `sum(x) - 1 == 0`.
- Formulate the return target constraint as an inequality: `returns @ x - min_return >= 0`.
- Optionally, encode individual upper bounds via the `bounds` argument instead of additional constraints.

### Formulation Template
```json
{
  "sets": ["n_assets"],
  "parameters": [
    {"name": "Q", "type": "matrix", "dim": ["n_assets", "n_assets"]},
    {"name": "returns", "type": "vector", "dim": "n_assets"},
    {"name": "min_return", "type": "scalar"},
    {"name": "max_alloc", "type": "scalar"}
  ],
  "decision_variables": [
    {"name": "x", "dim": "n_assets", "domain": "Real", "bounds": [0, "max_alloc"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "x' * Q * x"
  },
  "constraints": [
    {"name": "budget", "type": "eq", "expression": "sum(x) = 1"},
    {"name": "return_target", "type": "ineq", "expression": "returns' * x >= min_return"}
  ]
}
```

### Common Pitfalls
- Providing a non-symmetric covariance matrix `Q`, which leads to an incorrect quadratic form.
- Using an optimization method (e.g., `'SLSQP'`) that does not properly exploit the quadratic structure, potentially leading to slower convergence or inferior results compared to a dedicated QP solver.
- Forgetting to verify that the covariance matrix is positive semidefinite; if it is not, the problem is non-convex and requires a solver capable of handling indefinite QP.

## Solving stage

### Strategy Overview
This stage involves using SciPy's `minimize` function with a method suited for constrained optimization (like `'SLSQP'` or `'trust-constr'`), checking the success flag, and validating the solution against the original constraints.

### Step 1 - Configure and Run Optimizer
- Call `scipy.optimize.minimize` with the objective function, initial guess, bounds, constraints, and method.
- For quadratic problems with constraints, `method='SLSQP'` or `method='trust-constr'` are typical choices.
- Specify convergence tolerances (`tol`, `ftol`) if needed.

### Step 2 - Check Optimization Result
- Inspect the `success` attribute of the result object.
- Review the `message` for details on termination.
- If `success` is `False`, analyze the status and message to diagnose failure.

### Step 3 - Extract and Validate Solution
- Extract the solution vector from `result.x`.
- Compute the objective value (`result.fun`) and the actual portfolio return.
- Programmatically assert that the budget and return constraints are satisfied within tolerance.
- Check that all allocations respect the variable bounds.

### Code Usage
```python
import numpy as np
from scipy.optimize import minimize

# Assume Q, returns, min_return, max_alloc are defined
n = len(returns)
x0 = np.ones(n) / n  # Equal allocation initial guess

def objective(x):
    return x @ Q @ x

# Constraints
cons = [
    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
    {'type': 'ineq', 'fun': lambda x: returns @ x - min_return}
]
bounds = [(0, max_alloc) for _ in range(n)]

result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=cons)

if result.success:
    allocations = result.x
    variance = result.fun
    actual_return = returns @ allocations
    # Validate constraints
    # Return results dictionary
else:
    # Return failure dictionary with result.message
```

### Common Pitfalls
- Assuming `result.success == True` without reading the `message`, which may indicate a feasible but non-optimal solution.
- Not verifying constraint satisfaction post-solution, as the solver's internal tolerance may differ from the required precision.
- Using an inappropriate initial guess `x0` that violates bounds or linear constraints, which can cause some solvers to fail.
