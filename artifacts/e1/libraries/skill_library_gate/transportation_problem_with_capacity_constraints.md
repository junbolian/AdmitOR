---
name: Transportation Problem with Capacity Constraints
description: |
  Model and solve resource allocation problems with supply limits, demand requirements, per-assignment capacities, and linear costs using linear or integer programming.
---

# Workflow 1 (Linear Programming with OR-Tools pywraplp)

## Modeling stage

### Strategy Overview
Model the problem as a continuous linear program using the OR-Tools pywraplp API. This workflow is suitable when fractional allocations are acceptable and focuses on clarity and direct translation of the mathematical model.

### Step 1 - Define Sets and Parameters
- Define index sets for sources (`I`) and destinations (`J`).
- Organize parameters into arrays: `availability[i]`, `requirement[j]`, `cost[i][j]`, and `max_hours[i][j]`.
- Validate that all arrays have consistent dimensions matching the index sets.

### Step 2 - Create Decision Variables
- Create a 2D array of continuous decision variables `x[i][j]` representing the flow from source `i` to destination `j`.
- Set variable bounds directly: `0 <= x[i][j] <= max_hours[i][j]`. This embeds the per-assignment capacity constraint.

### Step 3 - Formulate Constraints
- **Supply Constraints**: For each source `i`, add `sum(x[i][j] for j in J) <= availability[i]`.
- **Demand Constraints**: For each destination `j`, add `sum(x[i][j] for i in I) == requirement[j]`. Use `>=` if only minimum demand must be met.

### Step 4 - Define Objective
- Formulate a linear objective: `minimize sum(cost[i][j] * x[i][j] for i in I for j in J)`.

### Formulation Template
```json
{
  "sets": ["I (sources)", "J (destinations)"],
  "parameters": [
    "availability[i] (total supply per source)",
    "requirement[j] (total demand per destination)",
    "cost[i][j] (unit cost per assignment)",
    "max_hours[i][j] (maximum flow per source-destination pair)"
  ],
  "decision_variables": ["x[i][j] (continuous flow from i to j)"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "sum_{j in J} x[i][j] <= availability[i], for all i in I",
    "sum_{i in I} x[i][j] == requirement[j], for all j in J",
    "0 <= x[i][j] <= max_hours[i][j], for all i in I, j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to check if total supply meets total demand (`sum(availability) >= sum(requirement)`), which can cause infeasibility.
- Using `==` for demand constraints when the problem allows for over-supply, which may be overly restrictive.
- Not setting variable upper bounds from `max_hours`, which can lead to unbounded variables if `availability` is large.

## Solving stage

### Strategy Overview
Solve the LP model using the OR-Tools GLOP solver via the pywraplp interface. This involves building the model, setting parameters, solving, and rigorously checking the solution status.

### Step 1 - Instantiate Solver and Build Model
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Build the model by following the modeling steps, using `solver.NumVar()` for variables and `solver.Add()` for constraints.

### Step 2 - Solve and Check Status
- Invoke `solver.Solve()`.
- Check the result status: `status = solver.VerifySolution(...)` or check `solver.OPTIMAL`/`solver.FEASIBLE`. Do not extract values if status is not optimal or feasible.

### Step 3 - Extract and Validate Solution
- Extract variable values using `x[i][j].solution_value()`.
- Programmatically verify all constraints by recalculating sums and comparing against parameter values.
- Recompute the objective value from the extracted flows to ensure consistency with the solver's reported value.

### Step 4 - Report Results
- Output the total objective value and a structured breakdown of the assignments (e.g., non-zero flows).

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... create variables x[i][j] with solver.NumVar(lb, ub, name)
# ... add constraints with solver.Add()
# ... set objective with solver.Minimize() or solver.Maximize()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'Objective value = {solver.Objective().Value()}')
    # Extract and process solution
    for i in I:
        for j in J:
            val = x[i][j].solution_value()
            if val > 1e-6:  # Filter near-zero values
                print(f'x[{i}][{j}] = {val}')
else:
    print('The problem does not have an optimal solution.')
```

### Common Pitfalls
- Attempting to access `solution_value()` without first checking the solver status, which may cause errors.
- Not setting a time limit for large problems, which can cause the solver to run indefinitely.
- Assuming the solver's internal solution verification is sufficient; always perform independent validation.

# Workflow 2 (Integer Programming with OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Model the problem as an integer program using the OR-Tools CP-SAT solver. This workflow is necessary when allocations must be in whole units (e.g., whole hours) or when integrality constraints are inherent to the problem.

### Step 1 - Define Scaled Parameters
- If input data (availability, requirement, costs) contains fractions, decide on a scaling factor (e.g., 10, 100) to convert to integers.
- Scale all parameters (`availability`, `requirement`, `max_hours`, `cost`) by this factor. Note: Scaling costs may affect the objective value.

### Step 2 - Create Integer Decision Variables
- Create a 2D array of integer decision variables `x[i][j]` representing the integer flow.
- Define variable domain: `0 <= x[i][j] <= scaled_max_hours[i][j]`, where the upper bound is the scaled capacity.

### Step 3 - Formulate Scaled Constraints
- **Supply Constraints**: `sum(x[i][j] for j in J) <= scaled_availability[i]`.
- **Demand Constraints**: `sum(x[i][j] for i in I) == scaled_requirement[j]`. Use `>=` for minimum demand.

### Step 4 - Define Scaled Objective
- Formulate the objective: `minimize sum(scaled_cost[i][j] * x[i][j] for i in I for j in J)`.
- Remember that the final objective value must be divided by the scaling factor (if costs were scaled).

### Formulation Template
```json
{
  "sets": ["I (sources)", "J (destinations)"],
  "parameters": [
    "scaled_availability[i] (integer supply per source)",
    "scaled_requirement[j] (integer demand per destination)",
    "scaled_cost[i][j] (integer unit cost per assignment)",
    "scaled_max_hours[i][j] (integer max flow per pair)"
  ],
  "decision_variables": ["x[i][j] (integer flow from i to j)"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} scaled_cost[i][j] * x[i][j]"
  },
  "constraints": [
    "sum_{j in J} x[i][j] <= scaled_availability[i], for all i in I",
    "sum_{i in I} x[i][j] == scaled_requirement[j], for all j in J",
    "0 <= x[i][j] <= scaled_max_hours[i][j], for all i in I, j in J"
  ]
}
```

### Common Pitfalls
- Scaling parameters inconsistently (e.g., scaling `max_hours` but not `availability`), leading to an incorrect model.
- Using an unnecessarily large scaling factor, which can cause integer overflow or slow down the solver.
- Forgetting to divide the final objective value by the scaling factor squared if both flows and costs were scaled.

## Solving stage

### Strategy Overview
Solve the integer program using the OR-Tools CP-SAT solver. Configure solver parameters for performance, handle solution loading carefully, and verify integrality and constraint satisfaction.

### Step 1 - Configure CP-SAT Solver
- Create a `CpModel()`.
- Set solver parameters: `model.Proto.max_time_in_seconds`, `model.Proto.num_search_workers`.
- Optionally set an optimality gap: `model.Proto.solution_hint`.

### Step 2 - Build and Solve Model
- Build the model using `model.NewIntVar()` and `model.Add()` methods.
- Call `solver.Solve(model)` where `solver` is `CpSolver()`.
- Check the status: `solver.StatusName(status)` for `OPTIMAL` or `FEASIBLE`.

### Step 3 - Extract and Validate Integer Solution
- Extract values using `solver.Value(x[i][j])`.
- Validate that all values are integers and all constraints are satisfied with the scaled parameters.
- If scaling was applied, descale the flows and objective value for reporting.

### Step 4 - Implement Robustness Checks
- If the solver returns an unclear status (e.g., `UNKNOWN`), try simplifying the model or adjusting parameters.
- For infeasibility, create a feasibility-only model (no objective) to debug constraint conflicts.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... create variables x[i][j] = model.NewIntVar(lb, ub, name)
# ... add constraints with model.Add()
# ... set objective with model.Minimize(expr)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 8
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f'Objective value = {solver.ObjectiveValue()}')
    # Remember to descale if scaling was used
    for i in I:
        for j in J:
            val = solver.Value(x[i][j])
            if val > 0:
                print(f'x[{i}][{j}] = {val}')
else:
    print(f'Solver finished with status: {solver.StatusName(status)}')
```

### Common Pitfalls
- Not setting `max_time_in_seconds`, which may cause the solver to run longer than desired.
- Using `solver.Value()` on a variable before checking the solve status.
- Overlooking the need to descale the solution and objective value for interpretation in the original units.
