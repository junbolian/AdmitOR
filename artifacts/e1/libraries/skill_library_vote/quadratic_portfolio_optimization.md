---
name: Quadratic Portfolio Optimization
description: |
  Model and solve portfolio allocation problems with variance minimization, budget, return target, and upper bound constraints using quadratic programming techniques.

---

# Workflow 1 (Pyomo with Commercial/High-Performance Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model definition, interfacing with high-performance solvers like Gurobi or CPLEX. It emphasizes explicit quadratic objective construction, parameterization for reusability, and efficient constraint handling via variable bounds.

### Step 1 - Define Model Structure
- Declare a Pyomo `ConcreteModel` and a `Set` for assets to index all model components.
- Define all input data (returns, variances, covariances, target return, upper bound) as Pyomo `Param` objects for easy swapping.

### Step 2 - Declare Decision Variables
- Create a continuous variable for each asset's allocation, bounded between 0 and the maximum allocation per asset.
- Use `bounds=(0, max_allocation)` directly on the variable to enforce upper limits without extra constraints.

### Step 3 - Formulate Quadratic Objective
- Construct the portfolio variance objective as the sum of diagonal (variance * x_i²) and off-diagonal (2 * covariance_ij * x_i * x_j) terms.
- Use a rule function that loops over assets and a pre-defined set of asset pairs (i<j) for efficiency and clarity.

### Step 4 - Impose Linear Constraints
- Add a budget constraint enforcing the sum of allocations equals 1.
- Add a return target constraint ensuring the weighted sum of asset returns meets or exceeds a minimum threshold.

### Formulation Template
```json
{
  "sets": ["assets", "asset_pairs"],
  "parameters": ["returns", "variances", "covariances", "target_return", "max_allocation"],
  "decision_variables": ["x[assets] (continuous, bounds=(0, max_allocation))"],
  "objective": {
    "sense": "min",
    "expression": "sum(variances[i] * x[i]**2 for i in assets) + 2 * sum(covariances[i,j] * x[i] * x[j] for (i,j) in asset_pairs where i < j)"
  },
  "constraints": [
    "budget: sum(x[i] for i in assets) == 1",
    "return_target: sum(returns[i] * x[i] for i in assets) >= target_return"
  ]
}
```

### Common Pitfalls
- Defining the quadratic objective incorrectly by omitting the factor of 2 for off-diagonal covariance terms.
- Adding redundant upper-bound constraints instead of using the variable's built-in `bounds` argument.
- Using hard-coded numerical values within constraint rules, which reduces model reusability.

## Solving stage

### Strategy Overview
This stage focuses on configuring a commercial-grade solver (e.g., Gurobi) for quadratic problems, implementing robust solution status checks, and extracting and validating results.

### Step 1 - Configure Solver
- Instantiate the solver factory (e.g., `SolverFactory("gurobi")`).
- Set key options: `MIPGap=0.0` for exact solution, `TimeLimit` for runtime control, `Threads` for parallelism, and `Seed` for reproducibility.

### Step 2 - Execute Solve and Check Status
- Call `solver.solve(model, tee=False)` (use `tee=True` for debugging).
- Check both `SolverStatus.ok` and `TerminationCondition.optimal` (or `feasible`) before proceeding. If not met, handle the error and exit gracefully.

### Step 3 - Extract and Validate Solution
- Retrieve variable values using `pyo.value(model.x[i])` and store allocations.
- Compute the achieved portfolio return and total allocation to verify constraint satisfaction.
- Output key results (objective value, allocations) in a structured format (e.g., JSON).

### Code Usage
```python
import pyomo.environ as pyo

# Build model (follow Modeling stage steps)
model = build_quadratic_portfolio_model(asset_data, target_return, max_alloc)

# Configure and run solver
solver = pyo.SolverFactory("gurobi")
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = 0.0
results = solver.solve(model, tee=False)

# Check status and extract results
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    allocations = {i: pyo.value(model.x[i]) for i in model.assets}
    portfolio_variance = pyo.value(model.obj)
    # Validate and output...
else:
    print("Solver failed:", results.solver.termination_condition)
```

### Common Pitfalls
- Assuming `SolverStatus.ok` alone guarantees an optimal solution; always check the termination condition.
- Not verifying post-solve that constraints (e.g., sum of allocations == 1) are numerically satisfied within tolerance.
- Forgetting to set a `Seed` for deterministic results when reproducibility is required.

# Workflow 2 (Matrix-based Formulation with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses a matrix-oriented approach, defining the quadratic objective as xᵀQx, and interfaces with open-source solvers like HiGHS or SciPy. It is suitable for environments without commercial licenses and leverages efficient linear algebra.

### Step 1 - Structure Data Matrices
- Organize input data as NumPy arrays: a vector of asset returns and a square covariance matrix Q (variances on diagonal).
- Verify the covariance matrix is symmetric. Check for positive semi-definiteness if convexity is required by the solver.

### Step 2 - Define Variables and Bounds
- Define a vector of continuous decision variables for allocations.
- Apply bounds directly: lower bound 0, upper bound `max_allocation` per asset.

### Step 3 - Formulate Objective and Constraints
- Express the objective as the quadratic form `x @ Q @ x` (matrix multiplication).
- Formulate the budget constraint as a linear equality (sum(x) == 1).
- Formulate the return target constraint as a linear inequality (returns @ x >= target_return).

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["returns_vector", "covariance_matrix_Q", "target_return", "max_allocation"],
  "decision_variables": ["x[assets] (continuous, bounds=(0, max_allocation))"],
  "objective": {
    "sense": "min",
    "expression": "xᵀ @ Q @ x"
  },
  "constraints": [
    "budget: sum(x) == 1",
    "return_target: returns_vector @ x >= target_return"
  ]
}
```

### Common Pitfalls
- Using a covariance matrix that is not symmetric, leading to an incorrect quadratic form.
- Forgetting to check matrix properties (e.g., PSD) which can cause solver failures for convex QP algorithms.
- Manually building the quadratic objective with nested loops when a simple matrix operation suffices, reducing code clarity.

## Solving stage

### Strategy Overview
This stage involves using an open-source solver (e.g., HiGHS via Pyomo or SciPy's `minimize`) configured for quadratic or general nonlinear problems, with emphasis on handling potential non-convexity and solution validation.

### Step 1 - Select and Configure Solver
- For convex QP, use `SolverFactory("highs")` in Pyomo. Set options like `time_limit` and feasibility tolerances.
- For non-convex QP or general nonlinear problems, use SciPy's `minimize` with the SLSQP method.

### Step 2 - Solve and Interpret Results
- Execute the solver. For HiGHS, check `SolverStatus.ok` and termination condition. For SciPy, check the `success` flag and `message`.
- Be aware that solvers like HiGHS may handle non-convex QPs but only guarantee local optimality.

### Step 3 - Post-Solve Validation and Output
- Extract the solution vector of allocations.
- Recompute the achieved return and total allocation to ensure numerical satisfaction of constraints.
- Output the minimal variance and the allocation percentages.

### Code Usage
```python
import numpy as np
import pyomo.environ as pyo  # For HiGHS
# Alternative: from scipy.optimize import minimize, LinearConstraint, Bounds

# Build a simple Pyomo model for HiGHS
model = pyo.ConcreteModel()
model.assets = pyo.Set(initialize=range(n_assets))
model.x = pyo.Var(model.assets, bounds=(0, max_alloc))
model.obj = pyo.Objective(expr=sum(Q[i,j] * model.x[i] * model.x[j] for i in model.assets for j in model.assets))
model.budget = pyo.Constraint(expr=sum(model.x[i] for i in model.assets) == 1)
model.return_con = pyo.Constraint(expr=sum(returns[i] * model.x[i] for i in model.assets) >= target)

# Solve with HiGHS
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    sol_vector = [pyo.value(model.x[i]) for i in model.assets]
    # Validate and output...
```

### Common Pitfalls
- Assuming an open-source QP solver (like HiGHS) will fail on non-convex problems; it may proceed but without global optimality guarantees.
- Not providing a feasible initial guess for nonlinear solvers (e.g., SLSQP), which can lead to convergence failures.
- Ignoring solver tolerances, potentially resulting in solutions that violate constraints by a small but financially significant margin.
