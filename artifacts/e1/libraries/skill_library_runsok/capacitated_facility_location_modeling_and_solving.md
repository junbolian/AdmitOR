---
name: Capacitated Facility Location Modeling and Solving
description: |
  Model fixed-cost capacitated facility location as MILP with binary selection and continuous flow variables, then solve with open-source or commercial solvers using robust verification protocols.
---

# Workflow 1 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract modeling capabilities. This approach cleanly separates data, variables, and constraints, enabling solver-agnostic formulation and easy integration with open-source solvers like CBC or HiGHS.

### Step 1 - Define Sets and Parameters
- Declare `facilities` and `customers` as Pyomo Sets for indexing.
- Create Pyomo Parameters for `fixed_cost`, `capacity`, `demand`, and `shipping_cost` using dictionaries or arrays.
- Use `pyo.Param` within a rule or initialize with a data dictionary for clarity and maintainability.

### Step 2 - Declare Decision Variables
- Create binary variables `y[i]` for facility selection (`pyo.Binary`).
- Create continuous non-negative variables `x[i,j]` for flow allocation (`pyo.NonNegativeReals`).
- Use descriptive variable names and attach them to the appropriate model sets.

### Step 3 - Formulate Objective Function
- Construct the objective as the sum of fixed and variable costs.
- Use `pyo.Objective` with `sense=pyo.minimize`.
- The expression should be `sum(fixed_cost[i] * y[i]) + sum(shipping_cost[i,j] * x[i,j])`.

### Step 4 - Implement Core Constraints
- **Demand Satisfaction**: Add a constraint for each customer `j`: `sum(x[i,j] for i in facilities) == demand[j]`.
- **Capacity-Linking**: Add a constraint for each facility `i`: `sum(x[i,j] for j in customers) <= capacity[i] * y[i]`.
- **Optional Strengthening**: Add per-arc constraints `x[i,j] <= capacity[i] * y[i]` to tighten the formulation.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["fixed_cost[facilities]", "capacity[facilities]", "demand[customers]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i]) + sum(shipping_cost[i,j] * x[i,j])"
  },
  "constraints": [
    "sum(x[i,j] for i in facilities) == demand[j] ∀ j ∈ customers",
    "sum(x[i,j] for j in customers) <= capacity[i] * y[i] ∀ i ∈ facilities"
  ]
}
```

### Common Pitfalls
- Using arbitrary large `M` values in linking constraints instead of the natural bound `capacity[i]`.
- Forgetting to check total demand against total capacity for feasibility before solving.
- Defining `shipping_cost` as a dense matrix when a sparse representation would be more efficient for large problems.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source MILP solver (CBC or HiGHS). Configure solver options for performance and reliability, and implement a robust protocol for checking solver status, extracting results, and verifying solution correctness.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory("cbc")` or `pyo.SolverFactory("highs")`.
- Set practical options: `solver.options["seconds"] = 30` (time limit), `solver.options["mip_rel_gap"] = 0.0` (optimality gap), `solver.options["threads"] = 4` (parallel threads).
- Execute the solve: `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Solver Status
- Check if the solver run was technically successful: `pyo.SolverStatus.ok`.
- Check the termination condition: `pyo.TerminationCondition.optimal` or `.feasible`.
- If status is not ok or termination is not acceptable, handle the failure (e.g., log error, try different solver settings).

### Step 3 - Extract and Verify Solution
- Extract facility decisions: `[i for i in model.F if pyo.value(model.y[i]) > 0.5]`.
- Extract flow values: `pyo.value(model.x[i,j])`.
- Programmatically verify all constraints: recalculate demand satisfaction and capacity usage with a small tolerance (e.g., `1e-6`).
- Recompute the objective value from extracted variables to validate against the solver-reported value.

### Step 4 - Analyze and Report Results
- Calculate cost breakdown: total fixed cost and total variable cost.
- Compute facility utilization: `sum(flow[i,:]) / capacity[i]` for open facilities.
- Output key metrics in a structured format for decision support.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (following modeling stage steps)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, objective, constraints

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

status = pyo.SolverStatus.ok
term = pyo.TerminationCondition.optimal

if status == pyo.SolverStatus.ok and term in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    # Extract and verify solution
    open_facilities = [i for i in model.F if pyo.value(model.y[i]) > 0.5]
    total_cost = pyo.value(model.obj)
    # ... further verification and analysis
else:
    print(f"Solver failed: status={status}, termination={term}")
```

### Common Pitfalls
- Extracting variable values without checking solver status first, leading to errors on failed solves.
- Setting `mip_rel_gap = -1.0` (invalid) instead of `0.0` for optimality.
- Using `tee=True` in production, which can clutter logs; reserve for debugging.

# Workflow 2 (OR-Tools with SCIP/CBC Backend)

## Modeling stage

### Strategy Overview
Model the problem directly using the OR-Tools CP-SAT or MPSolver API. This imperative style builds the model variable-by-variable and constraint-by-constraint, offering fine-grained control and direct access to solver-specific features, suitable for embedding in applications.

### Step 1 - Initialize Solver and Data Structures
- Create solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")` or `"CBC_MIXED_INTEGER_PROGRAMMING"`.
- Store input data in Python dictionaries or lists: `fixed_cost`, `capacity`, `demand`, `shipping_cost`.
- Use descriptive key patterns (e.g., `(i, j)` tuples for shipping costs).

### Step 2 - Create Decision Variables
- Create binary variables for facility selection: `y[i] = solver.IntVar(0, 1, f'y_{i}')`.
- Create continuous flow variables: `x[i,j] = solver.NumVar(0, solver.infinity(), f'x_{i}_{j}')`.
- Use `solver.infinity()` for upper bounds where appropriate.

### Step 3 - Build Objective Function
- Instantiate the objective: `objective = solver.Objective()`.
- Add fixed cost coefficients: `objective.SetCoefficient(y[i], fixed_cost[i])`.
- Add variable shipping cost coefficients: `objective.SetCoefficient(x[i,j], shipping_cost[i][j])`.
- Set minimization: `objective.SetMinimization()`.

### Step 4 - Add Constraints
- **Demand Satisfaction**: For each customer `j`, create a constraint with bounds `[demand[j], demand[j]]` and add coefficients `x[i,j]` with weight 1.
- **Capacity-Linking**: For each facility `i`, create a constraint with upper bound `0`. Add coefficients `x[i,j]` with weight 1 and `y[i]` with weight `-capacity[i]` (form: `sum(x) - capacity*y <= 0`).
- **Optional Per-Arc Bounds**: Add constraints `x[i,j] <= capacity[i] * y[i]` to strengthen the formulation.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["fixed_cost[facilities]", "capacity[facilities]", "demand[customers]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i]) + sum(shipping_cost[i,j] * x[i,j])"
  },
  "constraints": [
    "sum(x[i,j] for i in facilities) == demand[j] ∀ j ∈ customers",
    "sum(x[i,j] for j in customers) - capacity[i] * y[i] <= 0 ∀ i ∈ facilities"
  ]
}
```

### Common Pitfalls
- Incorrectly implementing the capacity-linking constraint as `0 <= expr <= capacity[i]` instead of `expr - capacity[i]*y[i] <= 0`.
- Forgetting to set the objective sense (`SetMinimization` or `SetMaximization`).
- Using `solver.IntVar(0, 1)` for binary variables but treating the solution value as boolean without a threshold check (`> 0.5`).

## Solving stage

### Strategy Overview
Solve the built model using the OR-Tools wrapper for SCIP or CBC. Configure time limits and other parameters directly on the solver object. Implement solution extraction with careful handling of floating-point values and verification of constraint satisfaction.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.SetTimeLimit(30000)` (milliseconds).
- Enable parallel processing: `solver.SetNumThreads(4)`.
- Set a seed for reproducibility: `solver.SetSolverSpecificParametersAsString("random_seed=42")` if supported.

### Step 2 - Execute Solve and Check Status
- Execute the solve: `status = solver.Solve()`.
- Check the result status: `status == pywraplp.Solver.OPTIMAL` or `FEASIBLE`.
- If status is `INFEASIBLE` or `NOT_SOLVED`, analyze the problem (e.g., check data consistency, relax constraints).

### Step 3 - Extract Solution with Verification
- Extract facility openings: `y[i].solution_value() > 0.5`.
- Extract flow values: `x[i,j].solution_value()`.
- Programmatically verify demand satisfaction and capacity constraints using the extracted values and a small tolerance.
- Recalculate the total cost from extracted values to validate against `solver.Objective().Value()`.

### Step 4 - Perform Combinatorial Verification (Optional)
- For small problems, enumerate facility combinations to verify global optimality.
- Force specific `y[i]` values and re-solve to explore alternative solutions and understand cost trade-offs.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... create variables, objective, constraints

# Solve with status / termination checks
solver.SetTimeLimit(30000)
status = solver.Solve()

if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    # Extract solution
    open_facilities = [i for i in facilities if y[i].solution_value() > 0.5]
    total_cost = solver.Objective().Value()
    # ... verification and analysis
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Directly comparing `y[i].solution_value() == 1` due to floating-point precision; use `> 0.5` instead.
- Not setting a time limit, potentially allowing the solver to run indefinitely on large instances.
- Misinterpreting the status code (e.g., `FEASIBLE` vs. `OPTIMAL`).
