---
name: Minimum Contributor Allocation with Binary Linking
description: |
  Model and solve allocation problems with minimum contributor requirements using binary-continuous variable linking and big-M constraints, with robust solver handling and verification.

---

# Workflow 1 (Pyomo with High-Performance MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling to define a Mixed-Integer Linear Program (MILP) with clear separation of sets, parameters, and constraints, suitable for solvers like Gurobi, CPLEX, or HiGHS.

### Step 1 - Define Sets and Parameters
- Define index sets for sources (e.g., `sources`) and sinks (e.g., `sinks`) as `pyo.Set()` objects.
- Create parameter dictionaries for `cost`, `capacity`, `demand`, `min_contributors`, and `min_delivery`, ensuring they are indexed appropriately (e.g., `cost[i, j]`).

### Step 2 - Create Decision Variables
- Declare a continuous allocation variable `x[i, j]` with domain `pyo.NonNegativeReals`.
- Declare a binary assignment variable `y[i, j]` with domain `pyo.Binary` to indicate participation.

### Step 3 - Formulate Linking Constraints
- Add a lower-bound linking constraint: `x[i, j] >= min_delivery[i] * y[i, j]` for all `(i, j)` to enforce minimum allocation if selected.
- Add an upper-bound linking constraint: `x[i, j] <= capacity[i] * y[i, j]` for all `(i, j)` to ensure zero allocation if not selected (using capacity as the big-M value).

### Step 4 - Add Core Problem Constraints
- Implement capacity limits: `sum(x[i, j] for j in sinks) <= capacity[i]` for each source `i`.
- Implement demand satisfaction: `sum(x[i, j] for i in sources) >= demand[j]` for each sink `j`.
- Implement minimum contributor requirements: `sum(y[i, j] for i in sources) >= min_contributors[j]` for each sink `j`.

### Step 5 - Set Linear Objective
- Define the objective to minimize total linear cost: `sum(cost[i, j] * x[i, j] for i in sources for j in sinks)`.

### Formulation Template
```json
{
  "sets": ["sources", "sinks"],
  "parameters": [
    "cost[sources, sinks]",
    "capacity[sources]",
    "demand[sinks]",
    "min_contributors[sinks]",
    "min_delivery[sources]"
  ],
  "decision_variables": [
    "x[sources, sinks] (continuous, non-negative)",
    "y[sources, sinks] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in sources for j in sinks)"
  },
  "constraints": [
    "capacity_limit[i]: sum(x[i, j] for j in sinks) <= capacity[i] for each i in sources",
    "demand_satisfaction[j]: sum(x[i, j] for i in sources) >= demand[j] for each j in sinks",
    "minimum_contributors[j]: sum(y[i, j] for i in sources) >= min_contributors[j] for each j in sinks",
    "minimum_allocation_if_selected[i, j]: x[i, j] >= min_delivery[i] * y[i, j] for each (i, j)",
    "upper_bound_linking[i, j]: x[i, j] <= capacity[i] * y[i, j] for each (i, j)"
  ]
}
```

### Common Pitfalls
- Forgetting the upper-bound linking constraint (`x[i, j] <= capacity[i] * y[i, j]`), which can lead to incorrect solutions where `y[i, j] = 0` but `x[i, j] > 0`.
- Using an overly large big-M value in the linking constraints, which can weaken the LP relaxation and slow down the solver; use the tightest valid bound (e.g., `capacity[i]`).
- Not verifying that the total system capacity (`sum(capacity[i])`) can meet total demand (`sum(demand[j])`) while respecting minimum delivery and contributor rules, leading to infeasibility.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a high-performance MIP solver with explicit configuration for time limits, optimality gaps, and parallel threads, followed by systematic solution verification.

### Step 1 - Configure and Execute Solver
- Instantiate the solver using `pyo.SolverFactory("solver_name")` (e.g., `"gurobi"`, `"cplex"`, `"highs"`).
- Set solver options: `TimeLimit` to a positive integer (e.g., 30), `MIPGap` to a small tolerance (e.g., 0.0001), `Threads` to a reasonable number (e.g., 4), and `Seed` for reproducibility if supported.
- Call `solver.solve(model, tee=True)` to solve and display solver log.

### Step 2 - Check Solver Status and Termination
- After solving, check `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `ok` and termination condition is `optimal` or `feasible`. For `optimal`, the best proven solution is available; for `feasible`, a valid but not necessarily optimal solution is available.

### Step 3 - Extract and Verify Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Load variable values and iterate through all constraints to verify satisfaction within a numerical tolerance (e.g., 1e-6).
- Specifically check: capacity limits per source, demand satisfaction per sink, minimum contributor counts per sink, and minimum delivery for active assignments.

### Step 4 - Output Results and Handle Failures
- Print the objective value with a clear prefix (e.g., `RESULT:{total_cost}`) for automated parsing.
- If the solver fails or returns `unknown`/`infeasible`, output a structured JSON payload with status and termination details for debugging (e.g., `RESULT_JSON:{"status": "...", "termination_condition": "..."}`).

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (assuming 'model' is defined)
solver = pyo.SolverFactory("gurobi")
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = -1e-6
solver.options['Threads'] = 4

results = solver.solve(model, tee=True)

# Solve with status / termination checks
if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                            pyo.TerminationCondition.feasible]:
    total_cost = pyo.value(model.obj)
    print(f"RESULT:{total_cost}")
    # Additional verification and output...
else:
    import json
    error_info = {
        "status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
    print(f"RESULT_JSON:{json.dumps(error_info)}")
```

### Common Pitfalls
- Not setting `tee=True` during initial runs, missing crucial solver output for debugging.
- Assuming `optimal` termination without checking, potentially missing suboptimal or feasible-only solutions.
- Extracting variable values without first checking solver status, which can lead to errors if no solution exists.
- Using exact equality (`==`) for constraint verification; always use tolerance-based comparisons (e.g., `abs(value - bound) <= 1e-6`).

---

# Workflow 2 (OR-Tools/SCIP with Direct API)

## Modeling stage

### Strategy Overview
This workflow uses the OR-Tools CP-SAT or SCIP backend via a direct API (e.g., `ortools.linear_solver.pywraplp`) for fine-grained control over variable and constraint creation, ideal for embedding in applications or when using open-source solvers.

### Step 1 - Initialize Solver and Create Variables
- Create a solver instance (e.g., `solver = pywraplp.Solver.CreateSolver('SCIP')`).
- Define continuous allocation variables `x[i][j]` with bounds `[0, infinity]` using `solver.NumVar()`.
- Define binary assignment variables `y[i][j]` using `solver.BoolVar()` or `solver.IntVar(0, 1)`.

### Step 2 - Build Linking Constraints via Linear Expressions
- For each `(i, j)`, create a constraint `x[i][j] >= min_delivery[i] * y[i][j]` by expressing `x[i][j] - min_delivery[i] * y[i][j] >= 0`.
- For each `(i, j)`, create a constraint `x[i][j] <= capacity[i] * y[i][j]` by expressing `x[i][j] - capacity[i] * y[i][j] <= 0`.

### Step 3 - Add Aggregate Constraints
- For each source `i`, create a capacity constraint: `sum(x[i][j] for j in sinks) <= capacity[i]`.
- For each sink `j`, create a demand constraint: `sum(x[i][j] for i in sources) >= demand[j]`.
- For each sink `j`, create a minimum contributor constraint: `sum(y[i][j] for i in sources) >= min_contributors[j]`.

### Step 4 - Set Linear Objective
- Build the objective expression: `sum(cost[i][j] * x[i][j] for i in sources for j in sinks)`.
- Set the solver objective to minimize this expression using `solver.Minimize()`.

### Formulation Template
```json
{
  "sets": ["sources", "sinks"],
  "parameters": [
    "cost[sources][sinks]",
    "capacity[sources]",
    "demand[sinks]",
    "min_contributors[sinks]",
    "min_delivery[sources]"
  ],
  "decision_variables": [
    "x[sources][sinks] (continuous, lower=0)",
    "y[sources][sinks] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in sources for j in sinks)"
  },
  "constraints": [
    "capacity_limit[i]: sum_j x[i][j] <= capacity[i]",
    "demand_satisfaction[j]: sum_i x[i][j] >= demand[j]",
    "minimum_contributors[j]: sum_i y[i][j] >= min_contributors[j]",
    "minimum_allocation_if_selected[i][j]: x[i][j] - min_delivery[i] * y[i][j] >= 0",
    "upper_bound_linking[i][j]: x[i][j] - capacity[i] * y[i][j] <= 0"
  ]
}
```

### Common Pitfalls
- Incorrectly building linear expressions for linking constraints (e.g., not moving terms to one side), causing solver errors.
- Using `solver.IntVar(0, 1)` for binary variables without setting the correct solver property, which may treat them as general integers.
- Not naming variables and constraints for easier debugging; use the `name` parameter when creating them.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools wrapper with performance tuning (time limits, threads) and implement post-solution verification to ensure all business rules are met.

### Step 1 - Configure Solver Performance
- Set a time limit using `solver.SetTimeLimit(limit_in_milliseconds)` (e.g., 60000 for 60 seconds).
- Set the number of threads with `solver.SetNumThreads(num_threads)` (e.g., 4).
- Enable verbose output if needed for debugging.

### Step 2 - Solve and Check Result Status
- Call `solver.Solve()` and capture the result status.
- Check if the status is `OPTIMAL` or `FEASIBLE`; treat both as successful solves that provide a feasible solution.

### Step 3 - Extract and Validate Solution
- Extract the objective value using `solver.Objective().Value()`.
- Iterate through all variables `x[i][j]` and `y[i][j]`, retrieving their solution values via `.solution_value()`.
- Programmatically verify all constraints: compute sums and compare against bounds with a tolerance.

### Step 4 - Output and Error Handling
- Print the total cost in a parseable format (e.g., `RESULT:{total_cost}`).
- If the solver fails to find a feasible solution, output a JSON with the solver status and any available incumbent information.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... create variables x, y and add constraints ...

# solve with status / termination checks
solver.SetTimeLimit(60000)
solver.SetNumThreads(4)
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    print(f"RESULT:{total_cost}")
    # Verify constraints...
else:
    import json
    error_info = {"status": status}
    print(f"RESULT_JSON:{json.dumps(error_info)}")
```

### Common Pitfalls
- Confusing `OPTIMAL` (best proven solution) with `FEASIBLE` (a valid solution found, but optimality not proven); both are acceptable for feasibility.
- Not using `.solution_value()` to get variable values, incorrectly accessing them directly.
- Forgetting to set a time limit for large instances, potentially causing the solver to run indefinitely.
- Assuming the solver's internal constraint verification is sufficient; always implement independent verification of business rules.
