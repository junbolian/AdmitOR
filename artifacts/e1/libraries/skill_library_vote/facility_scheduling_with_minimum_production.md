---
name: Facility Scheduling with Minimum Production
description: |
  Model and solve multi-period production planning with fixed costs, minimum/maximum production per facility, and demand satisfaction using binary-continuous linking constraints.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a clean, declarative MILP. It leverages Pyomo's native integration with solvers like HiGHS and CBC, focusing on a structured, equation-based approach suitable for rapid prototyping and analysis.

### Step 1 - Define Sets and Parameters
- Declare sets for facilities and time periods as Pyomo `Set` objects.
- Define scalar parameters for costs, production bounds, and demand as Pyomo `Param` objects, indexed by the appropriate sets.

### Step 2 - Create Decision Variables
- Create binary variables `operate[f,t]` to indicate if a facility is open in a period.
- Create non-negative continuous variables `production[f,t]` for the output quantity.

### Step 3 - Formulate Linking Constraints
- Implement minimum production if open: `production[f,t] >= min_production[f] * operate[f,t]`.
- Implement maximum capacity: `production[f,t] <= max_production[f] * operate[f,t]`.

### Step 4 - Formulate Demand and Objective
- Add a demand satisfaction constraint per period: `sum(production[f,t] for f in facilities) >= demand[t]`.
- Define a linear objective to minimize total cost: `sum(fixed_cost[f] * operate[f,t] + variable_cost[f] * production[f,t])`.

### Formulation Template
```json
{
  "sets": ["facilities", "time_periods"],
  "parameters": [
    {"name": "fixed_cost", "index": "facilities"},
    {"name": "variable_cost", "index": "facilities"},
    {"name": "min_production", "index": "facilities"},
    {"name": "max_production", "index": "facilities"},
    {"name": "demand", "index": "time_periods"}
  ],
  "decision_variables": [
    {"name": "operate", "type": "binary", "index": ["facilities", "time_periods"]},
    {"name": "production", "type": "continuous", "index": ["facilities", "time_periods"], "bounds": [0, null]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[f] * operate[f,t] + variable_cost[f] * production[f,t] for f in facilities for t in time_periods)"
  },
  "constraints": [
    {"name": "min_production_linking", "expression": "production[f,t] >= min_production[f] * operate[f,t]"},
    {"name": "max_production_linking", "expression": "production[f,t] <= max_production[f] * operate[f,t]"},
    {"name": "demand_satisfaction", "expression": "sum(production[f,t] for f in facilities) >= demand[t]"}
  ]
}
```

### Common Pitfalls
- Using a non-tight `M` value (like an arbitrary large number) for the maximum production linking constraint, which weakens the LP relaxation. Instead, use the actual `max_production[f]` parameter.
- Forgetting to verify that the sum of all `max_production` values can meet demand in each period, which can lead to silent infeasibility.
- Defining parameters with incorrect indices, causing runtime errors when building constraints.

## Solving stage

### Strategy Overview
This solving stage focuses on configuring the Pyomo solver interface, executing the solve with robust status checks, and implementing post-solution validation to ensure correctness and feasibility.

### Step 1 - Configure Solver and Solve
- Instantiate the solver factory (e.g., `SolverFactory('highs')` or `SolverFactory('cbc')`).
- Set practical options: `time_limit`, `mip_rel_gap` (e.g., 0.0 for optimality), `threads` for parallelism, and `presolve='on'`.

### Step 2 - Check Solver Status and Termination
- After solving, check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible` before extracting values.

### Step 3 - Extract and Validate Solution
- Retrieve variable values using `pyo.value(model.var[...])`.
- Implement a verification loop to check all constraints: demand satisfaction, production bounds when operating, and zero production when closed (within a small tolerance).
- Recompute the total cost from variable values as a sanity check against the solver's objective.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (example using ConcreteModel)
model = pyo.ConcreteModel()
model.F = pyo.Set(initialize=facilities_list)
model.T = pyo.Set(initialize=periods_list)
# ... define parameters, variables, constraints, objective as per modeling stage

# Solve
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model)

# Status / termination checks
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    # Extract and process solution
    for f in model.F:
        for t in model.T:
            op_val = pyo.value(model.operate[f,t])
            prod_val = pyo.value(model.production[f,t])
            # ... store or analyze values
else:
    # Handle infeasible or error status
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Attempting to access `pyo.value()` on a variable before confirming the solver status is `ok`, which may raise errors.
- Setting conflicting solver options (e.g., `threads` when a global scheduler is active) leading to unexpected behavior.
- Omitting post-solution validation, potentially missing subtle constraint violations due to numerical tolerances.

# Workflow 2 (OR-Tools with SCIP/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT or MPSolver API for a more procedural, code-driven modeling style. It is well-suited for deployment environments and offers fine-grained control over variable and constraint creation.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance (e.g., `solver = pywraplp.Solver.CreateSolver('SCIP')`).
- Prepare data dictionaries for costs, bounds, and demand.

### Step 2 - Create Variables with Bounds
- Create binary variables `operate[i][t]` using `solver.BoolVar()` or `solver.IntVar(0,1)`.
- Create continuous production variables `production[i][t]` with an upper bound of `max_production[i]` using `solver.NumVar(0, max_production[i], ...)`.

### Step 3 - Add Linking Constraints
- Add the minimum production constraint: `production[i][t] >= min_production[i] * operate[i][t]`.
- Add the maximum production constraint: `production[i][t] <= max_production[i] * operate[i][t]`. The variable's upper bound already helps the solver.

### Step 4 - Add Demand Constraints and Objective
- For each period, create a constraint: `sum(production[i][t] for i in facilities) >= demand[t]`.
- Build the objective by summing coefficients: `solver.Objective().SetCoefficient()` for each variable term, then set minimization.

### Formulation Template
```json
{
  "sets": ["facilities", "time_periods"],
  "parameters": [
    {"name": "fixed_cost", "index": "facilities"},
    {"name": "variable_cost", "index": "facilities"},
    {"name": "min_production", "index": "facilities"},
    {"name": "max_production", "index": "facilities"},
    {"name": "demand", "index": "time_periods"}
  ],
  "decision_variables": [
    {"name": "operate", "type": "binary", "index": ["facilities", "time_periods"]},
    {"name": "production", "type": "continuous", "index": ["facilities", "time_periods"], "bounds": [0, "max_production[i]"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * operate[i,t] + variable_cost[i] * production[i,t] for i in facilities for t in time_periods)"
  },
  "constraints": [
    {"name": "min_production_linking", "expression": "production[i,t] >= min_production[i] * operate[i,t]"},
    {"name": "max_production_linking", "expression": "production[i,t] <= max_production[i] * operate[i,t]"},
    {"name": "demand_satisfaction", "expression": "sum(production[i,t] for i in facilities) >= demand[t]"}
  ]
}
```

### Common Pitfalls
- Using `solver.IntVar(0, 1)` for binary variables instead of `solver.BoolVar()` which is semantically clearer and may be more efficient in some solvers.
- Manually constructing large linear expressions in loops without using helper functions, which can make the code verbose and error-prone.
- Neglecting to set an upper bound on continuous production variables, missing an opportunity to provide the solver with better bounds.

## Solving stage

### Strategy Overview
This stage focuses on the OR-Tools solving process: setting solver parameters, executing the solve, handling results, and extracting the schedule. It emphasizes efficient variable indexing and result verification.

### Step 1 - Set Solver Parameters and Solve
- Set a time limit: `solver.SetTimeLimit(time_limit_ms)`.
- Enable logging if needed: `solver.EnableOutput()`.
- Call `solver.Solve()`.

### Step 2 - Interpret Solver Result Status
- Check the result status: `if result_status == pywraplp.Solver.OPTIMAL or result_status == pywraplp.Solver.FEASIBLE`.
- For optimality confirmation, compare `solver.Objective().Value()` and `solver.Objective().BestBound()` if available.

### Step 3 - Extract Solution and Verify
- Iterate through all variable indices and retrieve values using `.solution_value()`.
- Implement verification checks for demand satisfaction and linking constraints.
- Compute the total cost from extracted values to validate against the solver's reported objective.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver('SCIP')
operate = {}
production = {}
# ... create variables in nested loops over facilities and periods
# ... add constraints as per modeling stage

# Set objective
objective = solver.Objective()
# ... set coefficients for operate and production variables
objective.SetMinimization()

# Solve with status / termination checks
solver.SetTimeLimit(30000)  # 30 seconds in milliseconds
result_status = solver.Solve()

if result_status in [solver.OPTIMAL, solver.FEASIBLE]:
    print(f'Objective value = {solver.Objective().Value()}')
    # Extract solution
    for i in facilities:
        for t in periods:
            op_val = operate[i,t].solution_value()
            prod_val = production[i,t].solution_value()
            # ... process values
else:
    print('The solver could not find a feasible solution.')
```

### Common Pitfalls
- Misinterpreting the solver status codes (e.g., `FEASIBLE` vs. `OPTIMAL`), leading to incorrect assumptions about solution quality.
- Not using a tolerance (e.g., `1e-6`) when checking if a binary variable is "on" (e.g., `value > 0.5`), which can be problematic due to floating-point results from some solvers.
- Forgetting to convert time units correctly when setting `SetTimeLimit` (milliseconds in OR-Tools).
