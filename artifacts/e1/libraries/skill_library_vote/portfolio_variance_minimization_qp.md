---
name: Portfolio Variance Minimization QP
description: |
  Model and solve portfolio optimization as a convex quadratic program to minimize variance subject to budget, return target, and position limits.

---

# Workflow 1 (Pyomo with Commercial Solver)

## Modeling stage

### Strategy Overview
Use Pyomo's algebraic modeling to construct a convex QP with a quadratic variance objective and linear constraints, designed for high-performance commercial solvers like Gurobi.

### Step 1 - Define Model Structure
- Instantiate a `ConcreteModel` and define a `Set` for the collection of assets.
- Declare `Param` objects for expected returns, variances, and pairwise covariances, using dictionaries for efficient indexing.

### Step 2 - Declare Decision Variables
- Create a `Var` for portfolio weights, with domain `NonNegativeReals`.
- Enforce position limits directly via variable bounds, e.g., `bounds=(0, max_weight)`.

### Step 3 - Formulate Quadratic Objective
- Build the portfolio variance expression: `sum(variances[i] * w[i]**2) + 2 * sum(covariances[(i,j)] * w[i] * w[j])` for i<j.
- Set the model's `Objective` to minimize this expression.

### Step 4 - Add Linear Constraints
- Add a budget `Constraint` as an equality: `sum(w[i]) == 1`.
- Add a return target `Constraint` as a linear inequality: `sum(expected_returns[i] * w[i]) >= min_return`.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["expected_returns", "variances", "covariances", "min_return", "max_weight"],
  "decision_variables": ["w[assets]"],
  "objective": {
    "sense": "min",
    "expression": "sum(variances[i] * w[i]**2) + 2 * sum(covariances[(i,j)] * w[i] * w[j] for i<j)"
  },
  "constraints": [
    "sum(w[i]) == 1",
    "sum(expected_returns[i] * w[i]) >= min_return"
  ]
}
```

### Common Pitfalls
- Forgetting to double the off-diagonal covariance terms in the quadratic expression.
- Using a non-positive-definite covariance matrix, which may violate convexity assumptions.
- Setting overly restrictive position limits (`max_weight`) that render the problem infeasible with the return target.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a commercial QP solver (e.g., Gurobi) with configuration for reproducibility and performance, followed by rigorous solution status checking and validation.

### Step 1 - Configure and Run Solver
- Instantiate the solver via `SolverFactory("solver_name")`.
- Set key parameters: `TimeLimit=30`, `MIPGap=0.0` (for exact QP optimality), `Threads=4`, `Seed=42` for reproducibility.
- Call `solver.solve(model)`.

### Step 2 - Check Solver Status
- Verify `status == SolverStatus.ok`.
- Verify `termination_condition` is `optimal` or `feasible`.
- If status is not ok or termination is not acceptable, output a structured error payload.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value via `float(pyo.value(model.obj))`.
- Extract variable values and print for transparency.
- Programmatically validate that constraints (sum=1, return≥target, bounds) are satisfied within a small tolerance.

### Code Usage
```python
import pyomo.environ as pyo
import json

# Assume `model` is built using the modeling steps above
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
results = solver.solve(model)

status = results.solver.status
term = results.solver.termination_condition

if status == pyo.SolverStatus.ok and term in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    obj_val = float(pyo.value(model.obj))
    weights = {i: pyo.value(model.w[i]) for i in model.assets}
    print(f"RESULT:{obj_val}")
    # Add verification checks here
else:
    payload = {
        "status": "failed",
        "reason": "infeasible_or_error",
        "solver_status": str(status),
        "termination_condition": str(term),
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of failed solves.
- Omitting a time limit, allowing the solver to run indefinitely on large or ill-conditioned problems.
- Failing to provide a fallback error output format (e.g., JSON) for automated parsing in pipelines.

---

# Workflow 2 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Construct the same QP model in Pyomo, optimized for use with open-source nonlinear solvers (e.g., IPOPT, SciPy) which may require careful initialization and parameter tuning.

### Step 1 - Define Model and Data
- Create a `ConcreteModel` with an `assets` Set.
- Store parameters (returns, variances, covariances) as Python dictionaries or `Param` objects.

### Step 2 - Initialize Variables with Bounds
- Declare weight variables with `bounds=(0, max_weight)`.
- Provide a sensible initial guess (e.g., equal weights) to aid solver convergence, using the `value` attribute.

### Step 3 - Build Objective and Constraints
- Assemble the quadratic variance objective, ensuring proper handling of covariance pairs.
- Add the linear budget and return constraints as in Workflow 1.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["expected_returns", "variances", "covariances", "min_return", "max_weight"],
  "decision_variables": ["w[assets]"],
  "objective": {
    "sense": "min",
    "expression": "sum(variances[i] * w[i]**2) + 2 * sum(covariances[(i,j)] * w[i] * w[j] for i<j)"
  },
  "constraints": [
    "sum(w[i]) == 1",
    "sum(expected_returns[i] * w[i]) >= min_return"
  ]
}
```

### Common Pitfalls
- Providing no initial guess, causing the open-source solver to fail or converge poorly.
- Using an asymmetric or incorrectly indexed covariance dictionary, leading to an incorrect objective.
- Neglecting to scale problem data (returns, variances), which can cause numerical issues for some solvers.

## Solving stage

### Strategy Overview
Solve using an open-source solver with a fallback strategy, configure for numerical stability, and employ multiple checks to confirm solution quality.

### Step 1 - Select and Configure Solver
- Attempt to use a preferred solver (e.g., IPOPT) with options: `tol=1e-8`, `max_iter=1000`, `print_level=0`.
- Implement a try-except block to fallback to an alternative solver (e.g., SciPy's SLSQP) if the primary is unavailable.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model)`.
- Check that `solver.status` is `ok` and `termination_condition` indicates `optimal`, `locallyOptimal`, or `feasible`.

### Step 3 - Validate and Refine Solution
- Extract objective and variable values.
- Recompute portfolio return and total weight to validate constraint satisfaction.
- Optionally, solve from different initial points to increase confidence in optimality for non-convex formulations.

### Code Usage
```python
import pyomo.environ as pyo

# Assume `model` is built, with initial values set on model.w
solver_names = ['ipopt', 'scip']
solved = False
results = None

for name in solver_names:
    solver = pyo.SolverFactory(name)
    if solver.available():
        if name == 'ipopt':
            solver.options['tol'] = 1e-8
            solver.options['max_iter'] = 1000
        try:
            results = solver.solve(model)
            status = results.solver.status
            term = results.solver.termination_condition
            if status == pyo.SolverStatus.ok and term in [pyo.TerminationCondition.optimal,
                                                          pyo.TerminationCondition.locallyOptimal,
                                                          pyo.TerminationCondition.feasible]:
                solved = True
                break
        except Exception as e:
            print(f"Solver {name} failed with error: {e}")
            continue

if solved:
    obj_val = float(pyo.value(model.obj))
    print(f"RESULT:{obj_val}")
    # Add verification checks here
else:
    print("RESULT:All available solvers failed.")
```

### Common Pitfalls
- Relying on a single solver without a fallback, causing workflow failure in environments with limited solver availability.
- Not setting convergence tolerances appropriately, leading to premature termination or excessive runtime.
- Interpreting `locallyOptimal` as a global optimum without considering potential non-convexity in the covariance matrix.
