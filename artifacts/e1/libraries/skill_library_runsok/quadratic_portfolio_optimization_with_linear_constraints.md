---
name: Quadratic Portfolio Optimization with Linear Constraints
description: |
  Model and solve portfolio variance minimization under linear budget, return, and bound constraints using quadratic programming solvers.
---

# Workflow 1 (Pyomo with Commercial QP Solver)

## Modeling stage

### Strategy Overview
This workflow models the portfolio optimization problem using Pyomo's abstract modeling capabilities, designed for integration with commercial quadratic programming solvers like Gurobi. It emphasizes structured parameterization, explicit constraint definition, and efficient quadratic objective formulation.

### Step 1 - Define Model Structure and Sets
- Create a concrete Pyomo model and define an indexed set for assets (e.g., `model.assets`).
- Use `pyo.RangeSet` or `pyo.Set` to enable clean indexing of parameters, variables, and constraints.

### Step 2 - Parameterize Problem Data
- Declare expected returns as a `pyo.Param` indexed by the asset set.
- Declare the covariance matrix as a 2D `pyo.Param` indexed by the asset set twice.
- Initialize these parameters with provided data dictionaries for efficient model construction.

### Step 3 - Declare Decision Variables and Bounds
- Define continuous decision variables for portfolio weights (e.g., `model.w`) indexed by the asset set.
- Set variable domain to `pyo.NonNegativeReals` and apply explicit upper bounds via the `bounds` argument to enforce allocation limits.

### Step 4 - Formulate Quadratic Objective
- Construct the portfolio variance objective as a double summation: `sum(m.w[i] * m.covariance[i, j] * m.w[j] for i in m.assets for j in m.assets)`.
- Assign it to the model as a `pyo.Objective` with sense `minimize`.

### Step 5 - Implement Linear Constraints
- Add a linear equality constraint for the budget: `sum(m.w[i] for i in m.assets) == 1`.
- Add a linear inequality constraint for the minimum return: `sum(m.expected_returns[i] * m.w[i] for i in m.assets) >= min_return`. Store `min_return` as a scalar parameter.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["expected_returns[assets]", "covariance[assets, assets]", "min_return", "max_weight"],
  "decision_variables": ["w[assets] (continuous, bounds=(0, max_weight))"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in assets} sum_{j in assets} w[i] * covariance[i,j] * w[j]"
  },
  "constraints": [
    "sum_{i in assets} w[i] == 1",
    "sum_{i in assets} expected_returns[i] * w[i] >= min_return"
  ]
}
```

### Common Pitfalls
- Forgetting to ensure the covariance matrix parameter is positive semi-definite, which can lead to solver errors or non-convex warnings.
- Hard-coding parameter values inside constraint rules instead of using model parameters, reducing reusability.
- Using inefficient objective expressions (e.g., nested loops over Python lists) instead of Pyomo's indexed summations.

## Solving stage

### Strategy Overview
This solving stage configures and calls a commercial QP solver (e.g., Gurobi) via Pyomo's SolverFactory, with robust settings for convex problems, systematic solution status checking, and post-solve validation.

### Step 1 - Configure Solver and Options
- Instantiate the solver using `pyo.SolverFactory("gurobi")`.
- Set key options: `TimeLimit` for runtime control, `MIPGap=0.0` for exact optimality tolerance, `Threads` for parallelism, and `Seed` for reproducibility.
- For non-convex covariance matrices, set `NonConvex=2` to allow solving.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model, tee=False)`.
- Check if `results.solver.status` equals `SolverStatus.ok`.
- Verify `results.solver.termination_condition` is `TerminationCondition.optimal` or `.feasible`.

### Step 3 - Extract and Validate Solution
- Load the solution into the model if not loaded automatically.
- Extract the objective value using `pyo.value(model.obj)`.
- Retrieve optimal weights via dictionary comprehension: `{i: pyo.value(model.w[i]) for i in model.assets}`.
- Compute the actual portfolio return from weights and expected returns to verify the minimum return constraint is satisfied within tolerance.

### Step 4 - Handle Failures Gracefully
- If the solver status is not OK or termination is not acceptable, output a structured JSON with failure details (status, termination condition, reason).
- Wrap the solve call in a try-except block to catch and report solver-specific exceptions.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Assume model built according to Modeling stage
solver = pyo.SolverFactory("gurobi")
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = 0.0
solver.options["Threads"] = 4
solver.options["Seed"] = 42
# If covariance may be non-convex:
# solver.options["NonConvex"] = 2

try:
    results = solver.solve(model, tee=False)
    status = results.solver.status
    term = results.solver.termination_condition

    acceptable_termination = {TerminationCondition.optimal, TerminationCondition.feasible}
    if status == SolverStatus.ok and term in acceptable_termination:
        # Load solution if needed (some solvers auto-load)
        # model.solutions.load_from(results)
        obj_val = pyo.value(model.obj)
        weights = {i: pyo.value(model.w[i]) for i in model.assets}
        # Validation
        portfolio_return = sum(expected_returns_data[i] * weights[i] for i in model.assets)
        # ... output success results
    else:
        output = {"status": "solver_failed", "solver_status": str(status), "termination": str(term)}
except Exception as e:
    output = {"status": "error", "reason": str(e)}
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to extraction of invalid solutions.
- Omitting post-solve validation, potentially missing constraint violations due to solver tolerances.
- Using default solver options that may be too loose for precise financial optimization.

# Workflow 2 (Pyomo with Open-Source NLP Solver)

## Modeling stage

### Strategy Overview
This workflow models the problem for open-source nonlinear programming solvers like IPOPT, which handle smooth quadratic objectives. It focuses on parameterization for flexibility, explicit indexing, and construction of a positive definite covariance matrix for numerical stability.

### Step 1 - Initialize Model and Index Sets
- Create a `pyo.ConcreteModel()` and define an asset set (e.g., `model.I`) using `pyo.Set(initialize=asset_names)`.
- Use this set for all indexed components to ensure consistency.

### Step 2 - Define Parameters with Validation
- Store expected returns as `pyo.Param(model.I)`.
- Store the covariance matrix as `pyo.Param(model.I, model.I)`.
- If covariance data is not provided, generate a synthetic positive definite matrix (e.g., using factor model `A @ A.T + epsilon * I`) and validate its eigenvalues.

### Step 3 - Declare Bounded Continuous Variables
- Define variables for portfolio weights (e.g., `model.x`) over the asset set with domain `pyo.NonNegativeReals`.
- Apply individual upper bounds via the `bounds` argument (e.g., `bounds=(0, max_allocation)`).

### Step 4 - Build Quadratic Objective
- Formulate variance minimization as `sum(model.x[i] * model.cov[i,j] * model.x[j] for i in model.I for j in model.I)`.
- Assign as the model objective with `sense=pyo.minimize`.

### Step 5 - Add Linear Equality and Inequality Constraints
- Impose the budget constraint: `sum(model.x[i] for i in model.I) == 1`.
- Impose the minimum return constraint: `sum(model.ret[i] * model.x[i] for i in model.I) >= target_return`. Define `target_return` as a scalar parameter.

### Formulation Template
```json
{
  "sets": ["I (assets)"],
  "parameters": ["ret[I]", "cov[I, I]", "target_return", "max_alloc"],
  "decision_variables": ["x[I] (continuous, bounds=(0, max_alloc))"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in I} x[i] * cov[i,j] * x[j]"
  },
  "constraints": [
    "sum_{i in I} x[i] == 1",
    "sum_{i in I} ret[i] * x[i] >= target_return"
  ]
}
```

### Common Pitfalls
- Providing a covariance matrix that is not positive definite, causing solver convergence issues.
- Using mutable Python data structures (like lists) inside Pyomo rules, which can lead to unexpected behavior.
- Neglecting to scale the objective or constraints, potentially leading to numerical difficulties for solvers like IPOPT.

## Solving stage

### Strategy Overview
This stage uses the IPOPT solver via Pyomo, configured for quadratic problems with linear constraints. It emphasizes solver option tuning, robust status checking, and post-solution verification.

### Step 1 - Instantiate and Configure Solver
- Create solver object: `solver = pyo.SolverFactory("ipopt")`.
- Verify solver availability (is not `None`).
- Set options: `tol=1e-7` (convergence tolerance), `max_iter=500`, `acceptable_tol=1e-5` (practical stopping), and `print_level=0` to suppress output.

### Step 2 - Solve with Error Handling
- Execute `results = solver.solve(model, tee=False)` within a try-except block to catch `ApplicationError` and other exceptions.
- Check `results.solver.status` equals `SolverStatus.ok`.
- Check `results.solver.termination_condition` is in `{optimal, locallyOptimal, feasible}`.

### Step 3 - Extract and Verify Results
- Extract objective value: `pyo.value(model.obj)`.
- Extract weights: `[pyo.value(model.x[i]) for i in model.I]`.
- Compute actual portfolio return and verify it meets the target within a small tolerance (e.g., `1e-6`).
- Verify the sum of weights equals 1 and all weights are within bounds.

### Step 4 - Provide Structured Output
- On success, return a dictionary with keys: `status`, `variance`, `return`, `weights`.
- On solver failure, return a dictionary with `status`, `reason`, `solver_status`, and `termination_condition`.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Assume model built according to Modeling stage
solver = pyo.SolverFactory("ipopt")
if solver is None:
    raise RuntimeError("IPOPT solver not available.")
solver.options["tol"] = 1e-7
solver.options["max_iter"] = 500
solver.options["acceptable_tol"] = 1e-5
solver.options["print_level"] = -1

try:
    results = solver.solve(model, tee=False)
    status = results.solver.status
    term = results.solver.termination_condition

    ok_terms = {TerminationCondition.optimal, TerminationCondition.locallyOptimal, TerminationCondition.feasible}
    if status == SolverStatus.ok and term in ok_terms:
        obj_val = pyo.value(model.obj)
        weights = [pyo.value(model.x[i]) for i in model.I]
        # Use original data arrays for validation
        port_return = sum(ret_data[i] * weights[i] for i in range(len(ret_data)))
        # Constraint verification
        if abs(sum(weights) - 1.0) > 1e-6 or port_return < target_return - 1e-6:
            # Flag warning
            pass
        output = {"status": "success", "variance": obj_val, "return": port_return, "weights": weights}
    else:
        output = {"status": "solver_failed", "solver_status": str(status), "termination": str(term)}
except Exception as e:
    output = {"status": "error", "reason": str(e)}
```

### Common Pitfalls
- Not setting `print_level` or `acceptable_tol`, leading to excessive output or premature stopping.
- Failing to verify solver availability before the solve call, causing cryptic errors.
- Not recalculating the portfolio return from original data, potentially missing discrepancies due to model parameter rounding.
