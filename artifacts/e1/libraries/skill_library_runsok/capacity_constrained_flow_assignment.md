---
name: Capacity-Constrained Flow Assignment
description: |
  Model and solve integer flow problems with heterogeneous capacities, flow conservation, and linear costs using MIP solvers.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem as a flow network with distinct resource types, tracking inventory at locations and movements between them. Use Pyomo's expressive syntax to define sets, parameters, and constraints declaratively.

### Step 1 - Define Resource and Network Structure
- Identify resource types (e.g., vehicle/plane types) and their attributes: capacity per trip, cost per trip, and total available count.
- Define the network nodes (e.g., locations) and the allowed directed arcs (e.g., routes) between them.
- Use Pyomo `Set` objects for resource types and locations to create a structured model foundation.

### Step 2 - Create Flow and Inventory Variables
- Define integer decision variables for the number of trips of each resource type on each allowed arc: `model.trips[type, origin, destination]`.
- Define integer variables for idle resource counts at each location at the start and end of the planning period: `model.idle_start[type, location]`, `model.idle_end[type, location]`.
- Apply variable bounds directly during declaration to enforce operational limits (e.g., `bounds=(0, max_trips)`).

### Step 3 - Enforce Flow Conservation and Availability
- For each resource type and location, enforce flow conservation: `idle_end[type, loc] == idle_start[type, loc] - departures + arrivals`.
- Ensure trips from a location do not exceed idle resources present at the start: `sum(trips[type, loc, *]) <= idle_start[type, loc]`.
- Optionally, allow the initial distribution of idle resources to be a decision variable, subject only to a total count constraint.

### Step 4 - Formulate Demand and Objective
- Formulate demand satisfaction as a capacity-weighted sum of incoming trips to the demand node: `sum(capacity[type] * trips[type, *, demand_loc]) >= demand`.
- Define a linear minimization objective: `sum(cost_per_trip[type] * trips[type, i, j])`.

### Formulation Template
```json
{
  "sets": [
    "resource_types",
    "locations",
    "arcs (subset of locations × locations)"
  ],
  "parameters": [
    "capacity[resource_type]",
    "cost_per_trip[resource_type]",
    "total_available[resource_type]",
    "demand",
    "max_trips[resource_type, arc] (optional)"
  ],
  "decision_variables": [
    "trips[resource_type, origin, destination] (integer, non-negative)",
    "idle_start[resource_type, location] (integer, non-negative)",
    "idle_end[resource_type, location] (integer, non-negative)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_per_trip[type] * trips[type, i, j] for type, (i,j) in arcs)"
  },
  "constraints": [
    "total_resources: sum(idle_start[type, loc] for loc in locations) == total_available[type] for each type",
    "flow_conservation: idle_end[type, loc] == idle_start[type, loc] - sum(trips[type, loc, dest]) + sum(trips[type, orig, loc]) for each type, loc",
    "availability: sum(trips[type, loc, dest]) <= idle_start[type, loc] for each type, loc",
    "demand_satisfaction: sum(capacity[type] * trips[type, orig, demand_loc]) >= demand",
    "route_restrictions: trips[type, i, j] == 0 for prohibited arcs"
  ]
}
```

### Common Pitfalls
- Forgetting to balance flow for all resource types at all locations, leading to infeasible or nonsensical solutions.
- Mis-specifying the sign in flow conservation (departures subtract, arrivals add).
- Applying overly restrictive bounds on `idle_start` variables when initial distribution should be flexible.
- Omitting route restriction constraints for arcs where trips are not allowed.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` with a MIP solver (HiGHS or CBC) to solve the integer flow model. Configure solver parameters for performance and reliability, and implement robust solution extraction and validation.

### Step 1 - Configure Solver and Solve
- Instantiate the solver: `solver = SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set key parameters: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0` for exact solutions, and `solver.options['threads'] = 4`.
- Execute the solve: `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Solution Status
- Check the solver status: `assert results.solver.status == SolverStatus.ok`.
- Check the termination condition: `assert results.solver.termination_condition == TerminationCondition.optimal` (or `.feasible` for suboptimal solutions).
- If status is not optimal/feasible, output a structured error with solver details for debugging.

### Step 3 - Extract and Verify Solution
- Extract variable values using `pyo.value(model.var)` and convert to native Python types (e.g., `int(pyo.value(model.trips[type, i, j]))`).
- Store the solution in a structured dictionary for analysis and reporting.
- Programmatically verify key constraints: total resource counts, flow balance, demand satisfaction, and variable bounds.

### Step 4 - Report and Analyze
- Print the objective value and a summary of key decision variables (e.g., total trips per type).
- Compute and report derived metrics (e.g., total capacity delivered, resource utilization).
- Optionally, fix the objective to its optimal value and solve a secondary objective to explore alternative optimal solutions.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation (using template structure)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective ...

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1.0  # Use -1 for HiGHS to set gap to 0
results = solver.solve(model, tee=False)

# Validate solution
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    print(f"Objective: {pyo.value(model.obj):.2f}")
    # Extract and process solution
    solution = {}
    for var in model.component_objects(pyo.Var, active=True):
        solution[var.name] = {idx: int(pyo.value(var[idx])) for idx in var}
    # ... further analysis ...
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to incorrect interpretation of suboptimal or failed solves.
- Forgetting to convert Pyomo variable values to native types, causing type errors in subsequent calculations.
- Setting an optimality gap (`mip_rel_gap`) that is too loose, potentially missing the exact integer optimum.
- Omitting the `tee=False` argument, which can clutter output with verbose solver logs.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Formulate the problem using Google's OR-Tools CP-SAT solver, which is designed for integer programming with logical constraints. Use a more procedural, builder-style API to define variables and constraints incrementally.

### Step 1 - Initialize Model and Define Variables
- Create a CP-SAT model instance: `model = cp_model.CpModel()`.
- Define integer flow variables for each resource type and arc: `trips[type, i, j] = model.NewIntVar(lb, ub, name)`.
- Define integer inventory variables for idle counts at each location and time: `idle_start[type, loc]`, `idle_end[type, loc]`.

### Step 2 - Add Core Constraints via Linear Expressions
- Enforce flow conservation by building linear expressions for departures and arrivals and adding equality constraints: `model.Add(idle_end == idle_start - departures + arrivals)`.
- Add demand satisfaction constraint using `model.Add(sum(capacity[type] * trips[type, *, demand_loc]) >= demand)`.
- Enforce vehicle availability at origin: `model.Add(sum(trips[type, loc, *]) <= idle_start[type, loc])`.

### Step 3 - Enforce Global and Logical Constraints
- Add constraints for total resource count: `model.Add(sum(idle_start[type, loc] for loc) == total_available[type])`.
- Forbid trips on prohibited routes by either not creating the variable or fixing it to zero.
- Optionally, add implied constraints (e.g., total trips bound) to improve solving performance.

### Step 4 - Set Linear Objective
- Build a linear expression for the total cost: `sum(cost_per_trip[type] * trips[type, i, j])`.
- Set the minimization objective: `model.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": [
    "resource_types",
    "locations",
    "arcs"
  ],
  "parameters": [
    "capacity[resource_type]",
    "cost_per_trip[resource_type]",
    "total_available[resource_type]",
    "demand",
    "max_trips_per_arc (optional)"
  ],
  "decision_variables": [
    "trips[resource_type, origin, destination] (CpModel.NewIntVar)",
    "idle_start[resource_type, location] (CpModel.NewIntVar)",
    "idle_end[resource_type, location] (CpModel.NewIntVar)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_per_trip[type] * trips[type, i, j])"
  },
  "constraints": [
    "total_resources: sum(idle_start[type, loc]) == total_available[type] for each type",
    "flow_conservation: idle_end[type, loc] == idle_start[type, loc] - sum(trips[type, loc, dest]) + sum(trips[type, orig, loc])",
    "availability: sum(trips[type, loc, dest]) <= idle_start[type, loc]",
    "demand: sum(capacity[type] * trips[type, orig, demand_loc]) >= demand",
    "route_bounds: 0 <= trips[type, i, j] <= max_trips_per_arc"
  ]
}
```

### Common Pitfalls
- Using `model.NewIntVar` without appropriate lower and upper bounds, which can reduce solver performance.
- Incorrectly building linear expressions for flow conservation, leading to unbalanced equations.
- Forgetting to add the demand constraint as a linear inequality (`>=`) rather than an equality.
- Not leveraging CP-SAT's ability to handle logical constraints (e.g., `OnlyOne`) when applicable.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' CP-SAT solver, which integrates a SAT-based MIP solver. Configure time limits and optional solution callbacks, then extract and validate the solution.

### Step 1 - Configure and Execute Solver
- Create a solver instance: `solver = cp_model.CpSolver()`.
- Set solver parameters: `solver.parameters.max_time_in_seconds = 30.0`, `solver.parameters.num_search_workers = 4`.
- Execute the solve: `status = solver.Solve(model)`.

### Step 2 - Interpret Solver Status
- Check the status: `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`.
- If status is `OPTIMAL`, the best possible solution was found. If `FEASIBLE`, a suboptimal solution was found within limits.
- Handle `INFEASIBLE` or `MODEL_INVALID` statuses by reporting the error and analyzing constraint conflicts.

### Step 3 - Extract Solution Values
- For each decision variable, retrieve its value in the solution: `value = solver.Value(var)`.
- Store values in a structured format (e.g., nested dictionaries).
- Compute derived metrics (total cost, capacity delivered) for validation and reporting.

### Step 4 - Validate and Report
- Programmatically verify that all constraints are satisfied by the extracted values.
- Print a clear summary: objective value, number of trips per resource type, and final idle distribution.
- For large models, consider logging intermediate solution details during the solve using a solution callback.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... define variables and constraints using model.Add() and model.NewIntVar() ...
# Set objective: model.Minimize(objective_expr)

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print(f"Objective: {solver.ObjectiveValue()}")
    # Extract solution
    solution = {}
    # Assuming 'trips_var_dict' is a mapping from (type,i,j) to the CpModel variable
    for key, var in trips_var_dict.items():
        solution[key] = solver.Value(var)
    # ... verify constraints and report ...
elif status == cp_model.INFEASIBLE:
    print("Model is infeasible.")
else:
    print(f"Solver returned status: {status}")
```

### Common Pitfalls
- Confusing `cp_model.OPTIMAL` (proven optimal) with `cp_model.FEASIBLE` (feasible but not proven optimal).
- Not setting `max_time_in_seconds`, allowing the solver to run indefinitely on difficult instances.
- Attempting to extract variable values (`solver.Value(var)`) when the status is not `OPTIMAL` or `FEASIBLE`, which raises an error.
- Overlooking the `num_search_workers` parameter for parallel search, which can significantly speed up solving.
