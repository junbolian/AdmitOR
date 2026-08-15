---
name: Quadratic Portfolio Optimization
description: |
  Model and solve portfolio allocation problems with variance minimization, linear return constraints, and allocation bounds using quadratic programming solvers.

---
# Workflow 1 (Convex QP with Commercial Solver)

## Modeling stage

### Strategy Overview
This workflow models the portfolio problem as a convex Quadratic Program (QP) suitable for commercial solvers like Gurobi or CPLEX. It emphasizes ensuring the covariance matrix is positive definite to guarantee convexity, enabling the use of efficient QP algorithms.

### Step 1 - Define Model Structure
- Create a concrete Pyomo model with a set for assets.
- Define parameters for expected returns, covariance matrix, minimum required return, and maximum allocation per asset.
- Declare continuous decision variables for portfolio weights, bounded between 0 and the maximum allocation.

### Step 2 - Formulate Objective and Constraints
- Construct the objective as a quadratic expression: minimize the sum of `w_i * cov_ij * w_j` for all asset pairs `i, j`.
- Add a linear equality constraint: the sum of all portfolio weights must equal 1.
- Add a linear inequality constraint: the weighted sum of expected returns must meet or exceed the minimum target return.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": [
    {"name": "expected_return", "index": "assets", "type": "float"},
    {"name": "covariance", "index": ["assets", "assets"], "type": "float"},
    {"name": "min_return", "index": null, "type": "float"},
    {"name": "max_alloc", "index": "assets", "type": "float"}
  ],
  "decision_variables": [
    {"name": "w", "index": "assets", "type": "continuous", "bounds": [0, "max_alloc"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( w[i] * covariance[i,j] * w[j] for i in assets for j in assets )"
  },
  "constraints": [
    {"name": "budget", "expression": "sum( w[i] for i in assets ) == 1"},
    {"name": "return_requirement", "expression": "sum( expected_return[i] * w[i] for i in assets ) >= min_return"}
  ]
}
```

### Common Pitfalls
- Using a covariance matrix that is not positive definite, which can cause solver failures or non-convex warnings.
- Forgetting to enforce non-negativity on weights if short-selling is not allowed.
- Setting an unrealistically high minimum return target that renders the problem infeasible.

## Solving stage

### Strategy Overview
This stage focuses on configuring a commercial QP solver (e.g., Gurobi) for robust performance, verifying solution optimality, and extracting and validating results against the original problem constraints.

### Step 1 - Configure and Execute Solver
- Instantiate the solver factory (e.g., `SolverFactory('gurobi')`).
- Set key parameters: `TimeLimit`, `MIPGap` (for continuous QP, set to 0.0), `Threads`, and `Seed` for reproducibility.
- If the covariance matrix might be non-convex, set the `NonConvex` parameter appropriately (e.g., `NonConvex=2` for Gurobi).

### Step 2 - Validate and Extract Solution
- After solving, check that `SolverStatus` is `ok` and `TerminationCondition` is `optimal` or `feasible`.
- Manually recalculate the portfolio's expected return and variance from the solution weights to verify objective value and constraint satisfaction.
- Filter out near-zero weight values (e.g., `< 1e-6`) for cleaner reporting.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (model construction based on formulation template)
# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    # Extract and process solution
    optimal_weights = [pyo.value(model.w[a]) for a in model.assets]
    # ... validation calculations
else:
    # Handle solver failure
    print("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Trusting the solver's objective value without recalculating key portfolio statistics for verification.
- Not handling solver parameter errors gracefully (e.g., resetting invalid `MIPGap` to a default like 0.0).
- Ignoring solver warnings about non-convexity, which can lead to locally optimal or incorrect solutions.

# Workflow 2 (Nonlinear Programming with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow models the problem for open-source Nonlinear Programming (NLP) solvers like IPOPT, which handle general nonlinear objectives and constraints. It is flexible and does not strictly require convexity, but benefits from good initial variable values.

### Step 1 - Prepare Data and Model
- Ensure the covariance matrix is numerically stable; add a small diagonal perturbation if necessary to avoid singularities.
- Create a concrete Pyomo model with sets and parameters identical to Workflow 1.
- Define continuous variables for portfolio weights with the same bounds.

### Step 2 - Formulate Nonlinear Problem
- Define the quadratic variance objective using the same double summation expression.
- Implement the linear budget and return constraints.
- Consider initializing variables with a feasible starting point (e.g., equal weights `1/n_assets`) to aid solver convergence.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": [
    {"name": "expected_return", "index": "assets", "type": "float"},
    {"name": "covariance", "index": ["assets", "assets"], "type": "float"},
    {"name": "min_return", "index": null, "type": "float"},
    {"name": "max_alloc", "index": "assets", "type": "float"}
  ],
  "decision_variables": [
    {"name": "w", "index": "assets", "type": "continuous", "bounds": [0, "max_alloc"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( w[i] * covariance[i,j] * w[j] for i in assets for j in assets )"
  },
  "constraints": [
    {"name": "budget", "expression": "sum( w[i] for i in assets ) == 1"},
    {"name": "return_requirement", "expression": "sum( expected_return[i] * w[i] for i in assets ) >= min_return"}
  ]
}
```

### Common Pitfalls
- Providing a covariance matrix with zero or negative eigenvalues, leading to solver convergence issues.
- Omitting variable bounds, which can cause the solver to explore invalid negative allocations.
- Using an infeasible initial point that violates constraints, slowing down the solver.

## Solving stage

### Strategy Overview
This stage involves configuring an NLP solver (e.g., IPOPT), managing its options for performance and output control, and rigorously checking solution feasibility and quality after solving.

### Step 1 - Configure and Run Solver
- Check solver availability via `SolverFactory('ipopt')`.
- Set solver options: `tol=1e-6` for convergence tolerance, `max_iter=500`, `print_level=0` for minimal console output.
- Wrap the solver call in a try-except block to gracefully handle exceptions like missing solvers or numerical errors.

### Step 2 - Verify Solution and Report
- Check that `SolverStatus` is `ok` and `TerminationCondition` is `optimal`, `locallyOptimal`, or `feasible`.
- Calculate the actual portfolio return from the solution weights to confirm the minimum return constraint is satisfied.
- Extract the objective value and variable values, and compute derived metrics (e.g., portfolio standard deviation) for reporting.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (model construction based on formulation template)
# Initialize variables for better convergence
for a in model.assets:
    model.w[a] = 1.0 / len(model.assets)

# solve with status / termination checks
solver = pyo.SolverFactory('ipopt')
solver.options['tol'] = 1e-6
solver.options['max_iter'] = III
solver.options['print_level'] = 0

try:
    results = solver.solve(model, tee=False)
except Exception as e:
    print(f"Solver failed with exception: {e}")
    results = None

if results and (results.solver.status == pyo.SolverStatus.ok and
                results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                                         pyo.TerminationCondition.locallyOptimal,
                                                         pyo.TerminationCondition.feasible]):
    # Extract and validate solution
    portfolio_return = sum(pyo.value(model.expected_return[a]) * pyo.value(model.w[a]) for a in model.assets)
    # ... further processing
else:
    print("Solver did not converge to a satisfactory solution.")
```

### Common Pitfalls
- Accepting solutions from a solver with `unknown` or `infeasible` termination conditions without further investigation.
- Not recalculating constraint values from the solution, potentially missing small constraint violations due to solver tolerances.
- Failing to provide a feasible initial point, which can lead to slower convergence or solver failure.
