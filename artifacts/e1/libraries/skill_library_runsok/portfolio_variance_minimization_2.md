---
name: Portfolio Variance Minimization
description: |
  Model portfolio optimization as a quadratic program to minimize variance under linear allocation and return constraints, and solve it using dedicated QP or general nonlinear solvers with robust status checking.

---

# Workflow 1 (Dedicated QP Solver)

## Modeling stage

### Strategy Overview
Formulate the portfolio selection problem as a convex Quadratic Program (QP) using the Markowitz mean-variance framework. The quadratic objective represents portfolio variance, while all constraints (budget, return, bounds) are linear, making it suitable for solvers like Gurobi or HiGHS.

### Step 1 - Define Core Data Structures
- Gather or construct the required input parameters: an array of expected returns, a symmetric positive semi-definite covariance matrix, a minimum required portfolio return, and a maximum allowable weight per asset.
- If a full covariance matrix is not provided, construct a reasonable proxy (e.g., identity matrix for uncorrelated assets, or a matrix built from assumed correlations and volatilities) to ensure the problem is well-defined.
- Convert all percentage inputs (e.g., returns) to decimal form for numerical consistency within the model.

### Step 2 - Declare Variables and Bounds
- Create a continuous decision variable for the weight of each asset. Enforce non-negativity and an upper bound simultaneously by defining the variable's domain and bounds (e.g., `Var(domain=NonNegativeReals, bounds=(0, max_weight))`).
- Use a model Set to index these variables over the collection of assets.

### Step 3 - Formulate Objective and Constraints
- Formulate the objective to minimize portfolio variance: the double sum of weights multiplied by the corresponding covariance matrix entries.
- Add a linear equality constraint to enforce full investment: the sum of all weights must equal 1.
- Add a linear inequality constraint to meet the minimum return threshold: the weighted sum of asset returns must be greater than or equal to the target.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": [
    "expected_returns[assets]",
    "covariance_matrix[assets, assets]",
    "min_required_return",
    "max_weight_per_asset"
  ],
  "decision_variables": ["weight[assets]"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in assets} sum_{j in assets} weight[i] * covariance_matrix[i,j] * weight[j]"
  },
  "constraints": [
    "budget: sum_{i in assets} weight[i] == 1",
    "min_return: sum_{i in assets} expected_returns[i] * weight[i] >= min_required_return",
    "bounds: 0 <= weight[i] <= max_weight_per_asset, for all i in assets"
  ]
}
```

### Common Pitfalls
- Using a covariance matrix that is not positive semi-definite, which can lead to solver errors or non-convex problems.
- Forgetting to scale percentage inputs (e.g., 12% vs. 0.12), causing objective and constraint scaling issues.
- Defining the upper bound and non-negativity as separate constraints instead of using the variable's native bounds, which adds unnecessary model complexity.

## Solving stage

### Strategy Overview
Solve the QP using a solver with native support for quadratic objectives and linear constraints (e.g., Gurobi, HiGHS). Configure solver-specific parameters for performance and precision, and implement rigorous checks on the solution status and feasibility.

### Step 1 - Select and Configure Solver
- Instantiate the solver via the modeling framework's factory (e.g., `SolverFactory("gurobi")`).
- Set key options for a QP: convergence tolerance (e.g., `BarConvTol`), time limit, number of threads, and a random seed for reproducibility. Avoid using MIP-specific parameters like `MIPGap`.

### Step 2 - Solve and Check Status
- Execute the solve command with `tee=False` for quiet operation unless debugging.
- Immediately check the high-level solver status (`SolverStatus.ok`) and the detailed termination condition (`TerminationCondition.optimal` or `.feasible`). Do not proceed if the status indicates an error or failure.

### Step 3 - Extract and Validate Solution
- Extract the optimal objective value and the values for all weight variables.
- Programmatically validate the solution: verify the sum of weights is 1 within a small tolerance (e.g., 1e-6), check that all weights satisfy their bounds, and confirm the achieved portfolio return meets the minimum requirement.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Assume 'model' is a Pyomo ConcreteModel built according to the formulation
solver = pyo.SolverFactory("gurobi")  # Or "highs"
solver.options["BarConvTol"] = 1e-8
solver.options["TimeLimit"] = 30
solver.options["Threads"] = 4
solver.options["Seed"] = 42

results = solver.solve(model, tee=False)
status = results.solver.status
termination = results.solver.termination_condition

ok_conditions = {TerminationCondition.optimal, TerminationCondition.feasible}
if status == SolverStatus.ok and termination in ok_conditions:
    objective_value = float(pyo.value(model.obj))
    weights = {i: pyo.value(model.w[i]) for i in model.assets}
    # ... add validation checks here
else:
    raise RuntimeError(f"Solver failed: Status={status}, Termination={termination}")
```

### Common Pitfalls
- Proceeding to extract solution values without checking the termination condition, potentially using results from an infeasible or error state.
- Using solver parameters inappropriate for continuous QP (e.g., `MIPGap`).
- Not validating the extracted solution against the original constraints, which can mask numerical inaccuracies.

# Workflow 2 (General-Purpose Nonlinear Solver)

## Modeling stage

### Strategy Overview
Model the same portfolio variance minimization problem, but structure it for solvers that handle general nonlinear objectives with constraints (e.g., IPOPT, SciPy's SLSQP). This approach is useful when dedicated QP solvers are unavailable, relying on the convexity of the quadratic form.

### Step 1 - Prepare Data and Matrix
- Assemble the same core parameters: expected returns, covariance matrix, return target, and weight bounds.
- Ensure the covariance matrix is formatted as a 2D array (e.g., NumPy matrix) for efficient computation within the objective function.

### Step 2 - Define Variable Bounds and Constraints
- Define the problem variables as a vector of continuous weights.
- Specify explicit bounds for each variable as a list of `(lower, upper)` tuples (e.g., `(0, max_weight)`).
- Encode the linear constraints separately: the budget constraint as an equality and the return constraint as an inequality.

### Step 3 - Formulate Objective for API
- Express the objective function as a callable that takes the weight vector `x` and returns `x.T @ cov_matrix @ x`. Note that some APIs (e.g., SciPy) expect a factor of 0.5 in front of the quadratic term.
- Provide a feasible initial guess (e.g., equal weights) to improve solver convergence.

### Formulation Template
```json
{
  "sets": ["n_assets"],
  "parameters": [
    "returns[n_assets]",
    "cov_matrix[n_assets, n_assets]",
    "target_return",
    "weight_upper_bound"
  ],
  "decision_variables": ["x[n_assets]"],
  "objective": {
    "sense": "min",
    "expression": "x' * cov_matrix * x"  # Or 0.5 * x' * cov_matrix * x for some APIs
  },
  "constraints": [
    {"type": "eq", "expression": "sum(x) - 1"},
    {"type": "ineq", "expression": "returns' * x - target_return"},
    {"type": "bounds", "lower": 0, "upper": "weight_upper_bound", "for": "each x"}
  ]
}
```

### Common Pitfalls
- Forgetting the 0.5 scaling factor in the objective when required by the solver API, leading to incorrect optimal values.
- Providing an infeasible initial guess (e.g., zeros when sum must be 1), causing solver convergence issues.
- Using a dense, inefficient double-loop to compute the quadratic objective within the callable instead of vectorized matrix multiplication.

## Solving stage

### Strategy Overview
Solve the problem using a nonlinear optimization solver, configuring it for precision and reliability. Focus on checking for local optimality and ensuring the final solution is validated against all constraints.

### Step 1 - Configure Solver Options
- Instantiate the solver (e.g., `SolverFactory("ipopt")` or SciPy's `minimize` with method='SLSQP').
- Set convergence tolerances (`tol`), maximum iterations, and verbosity level (`print_level` or `disp`).

### Step 2 - Invoke Solver and Check Outcome
- Call the solver, passing the objective function, constraints, bounds, and initial guess.
- After solving, inspect the solver's success flag and message. For Pyomo solvers, check `termination_condition` for `optimal`, `locallyOptimal`, or `feasible`.

### Step 3 - Post-Solve Validation and Output
- Extract the optimized weight vector and the final objective value.
- Recalculate the portfolio return and the sum of weights from the solution to verify constraint satisfaction within a numerical tolerance (e.g., 1e-6).
- If the covariance matrix was an assumption, note this in the output.

### Code Usage
```python
import numpy as np
from scipy.optimize import minimize

# Data: returns, cov_matrix, target_return, upper_bound
n = len(returns)
initial_guess = np.ones(n) / n  # Equal weights
bounds = [(0, upper_bound) for _ in range(n)]

constraints = [
    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},
    {'type': 'ineq', 'fun': lambda x: np.dot(returns, x) - target_return}
]

def objective(x):
    return 0.5 * x @ cov_matrix @ x  # Note 0.5 factor for SciPy

result = minimize(objective, initial_guess, method='SLSQP',
                  bounds=bounds, constraints=constraints,
                  options={'ftol': 1e-9, 'maxiter': 1000})

if result.success:
    optimal_weights = result.x
    optimal_variance = 2 * result.fun  # Adjust if 0.5 factor was used
    # ... perform validation checks
else:
    raise RuntimeError(f"Solver failed: {result.message}")
```

### Common Pitfalls
- Assuming solver `success=True` without checking the actual optimality conditions or message.
- Not adjusting the objective value after solving (e.g., forgetting to multiply by 2 if 0.5 was used in the formulation).
- Omitting post-solution validation, which is critical when using general nonlinear solvers that may converge to a local optimum or stop with small constraint violations.
