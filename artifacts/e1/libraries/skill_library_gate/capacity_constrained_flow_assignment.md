---
name: Capacity-Constrained Flow Assignment
description: |
  Model and solve integer flow problems with capacity constraints, vehicle conservation, and demand satisfaction using linear programming backends.
---

# Workflow 1 (MIP with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the system as a flow network with explicit vehicle inventory tracking at each location. It uses integer variables for flows and idle counts, enforcing conservation and capacity constraints via linear inequalities, suitable for MIP solvers like SCIP or CBC via the OR-Tools wrapper.

### Step 1 - Define Core Flow and State Variables
- Create integer decision variables for the number of trips between each origin-destination pair for each vehicle type (e.g., `trips[p,i,j]`).
- Create integer state variables to track the number of idle vehicles of each type at each location at the start and end of the planning period (e.g., `idle_start[p,l]`, `idle_end[p,l]`).

### Step 2 - Enforce Demand Satisfaction
- For each demand requirement (e.g., from origin `o` to destination `d`), sum the capacity-providing flow variables: `sum_over_p( capacity[p] * trips[p,o,d] ) >= demand[o,d]`.

### Step 3 - Implement Flow Conservation
- For each vehicle type `p` and location `l`, enforce inventory balance: `idle_end[p,l] = idle_start[p,l] - departures[p,l] + arrivals[p,l]`. Departures are the sum of trips originating at `l`; arrivals are the sum of trips terminating at `l`.

### Step 4 - Set Initial Fleet and Availability Constraints
- Ensure the total idle vehicles at the start sums to the initial fleet size for each type: `sum_over_l( idle_start[p,l] ) == initial_fleet[p]`.
- Optionally, add constraints to limit trips from a location by the available idle vehicles at the start: `sum_over_j( trips[p,l,j] ) <= idle_start[p,l]`.

### Step 5 - Formulate Linear Cost Objective
- Minimize total operational cost: `sum_over_p,i,j( cost_per_trip[p,i,j] * trips[p,i,j] )`. Set cost to zero for intra-location movements if needed.

### Formulation Template
```json
{
  "sets": [
    "P: set of vehicle types",
    "L: set of locations",
    "OD: set of origin-destination pairs with demand"
  ],
  "parameters": [
    "capacity[P]: units per trip",
    "cost_per_trip[P, L, L]: cost of a trip",
    "demand[OD]: required units",
    "initial_fleet[P]: total vehicles available",
    "max_trips[P, L, L]: upper bound on trips (optional)"
  ],
  "decision_variables": [
    "trips[P, L, L]: integer, number of trips",
    "idle_start[P, L]: integer, idle vehicles at start",
    "idle_end[P, L]: integer, idle vehicles at end"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost_per_trip[p,i,j] * trips[p,i,j] for p in P, i in L, j in L )"
  },
  "constraints": [
    "demand_satisfaction[o,d]: sum( capacity[p] * trips[p,o,d] for p in P ) >= demand[o,d] for each (o,d) in OD",
    "flow_conservation[p,l]: idle_end[p,l] == idle_start[p,l] - sum( trips[p,l,j] for j in L ) + sum( trips[p,i,l] for i in L ) for each p in P, l in L",
    "initial_fleet_distribution[p]: sum( idle_start[p,l] for l in L ) == initial_fleet[p] for each p in P",
    "variable_bounds: 0 <= trips[p,i,j] <= max_trips[p,i,j] (if provided)"
  ]
}
```

### Common Pitfalls
- Forgetting to include flow conservation for all locations, leading to vehicle creation or destruction.
- Setting overly restrictive upper bounds on trip variables that make the problem infeasible.
- Neglecting to set costs for intra-location "trips" to zero, which can distort the objective.

## Solving stage

### Strategy Overview
Solve the MIP model using the OR-Tools linear solver wrapper, which provides a uniform interface to SCIP, CBC, and other backends. Focus on configuring solver limits, extracting solutions, and performing post-solve validation.

### Step 1 - Initialize Solver and Create Variables
- Instantiate a MIP-capable solver: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Create integer variables with appropriate bounds using `solver.IntVar(lb, ub, name)`.

### Step 2 - Add Constraints and Objective
- Build constraints using `solver.Add(linear_expr)`.
- Set the objective coefficients via `objective.SetCoefficient(var, coeff)` and call `objective.SetMinimization()`.

### Step 3 - Configure Solver Parameters
- Set a time limit: `solver.SetTimeLimit(ms)`.
- Enable parallel solving if supported: `solver.SetNumThreads(num_threads)`.

### Step 4 - Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:`.

### Step 5 - Extract and Validate Solution
- Extract variable values using `var.solution_value()`.
- Programmatically verify key constraints (e.g., recompute total delivered capacity) to ensure solution integrity.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# Example variable creation
trips = {}
for p in vehicle_types:
    for i in locations:
        for j in locations:
            trips[p,i,j] = solver.IntVar(0, max_trips.get((p,i,j), solver.infinity()), f'trips_{p}_{i}_{j}')
# ... add constraints and objective as per formulation

# Solve with status / termination checks
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    solution = {var.name(): var.solution_value() for var in solver.variables()}
    # Optional validation
    total_capacity = sum(capacity[p] * trips[p,o,d].solution_value() for p in vehicle_types)
    assert total_capacity >= demand, "Demand not satisfied in solution."
    print(f"Optimal cost: {objective_value}")
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing good solutions.
- Forgetting to convert solution values to integers for integer variables, leading to type issues downstream.
- Omitting solver time limits for large instances, causing unpredictable runtimes.

# Workflow 2 (Pyomo with High-Level Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define sets, parameters, and constraints declaratively. It separates problem specification from data, making it easy to swap solvers (e.g., HiGHS, CBC) and handle larger, more structured instances.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for indices (vehicle types, locations, demand pairs).
- Define Pyomo `Param` objects for all input data (capacities, costs, demand, fleet sizes).

### Step 2 - Define Decision Variables with Domains
- Use `pyo.Var` with `domain=pyo.NonNegativeIntegers` for flow and state variables.
- Apply bounds directly in the variable declaration (e.g., `bounds=(0, max_trips)`).

### Step 3 - Write Constraint Rules
- Create `pyo.Constraint` objects using rule functions that reference model parameters and variables.
- Implement flow conservation, demand satisfaction, and initial fleet distribution as separate constraint rules.

### Step 4 - Formulate Objective Expression
- Define a `pyo.Objective` with `sense=pyo.minimize` and an expression summing cost terms.

### Step 5 - Instantiate Model with Concrete Data
- Create a `ConcreteModel` and populate the abstract sets and parameters with actual data dictionaries.

### Formulation Template
```json
{
  "sets": [
    "P: pyo.Set, vehicle types",
    "L: pyo.Set, locations",
    "OD: pyo.Set, demand pairs"
  ],
  "parameters": [
    "capacity: pyo.Param(P)",
    "cost: pyo.Param(P, L, L)",
    "demand: pyo.Param(OD)",
    "initial_fleet: pyo.Param(P)",
    "max_trips: pyo.Param(P, L, L, optional)"
  ],
  "decision_variables": [
    "trips: pyo.Var(P, L, L, domain=pyo.NonNegativeIntegers)",
    "idle_start: pyo.Var(P, L, domain=pyo.NonNegativeIntegers)",
    "idle_end: pyo.Var(P, L, domain=pyo.NonNegativeIntegers)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[p,i,j] * trips[p,i,j] for p in P, i in L, j in L )"
  },
  "constraints": [
    "demand_constr[o,d]: sum( capacity[p] * trips[p,o,d] for p in P ) >= demand[o,d]",
    "flow_constr[p,l]: idle_end[p,l] == idle_start[p,l] - sum( trips[p,l,j] for j in L ) + sum( trips[p,i,l] for i in L )",
    "initial_constr[p]: sum( idle_start[p,l] for l in L ) == initial_fleet[p]"
  ]
}
```

### Common Pitfalls
- Mixing up abstract and concrete model creation, leading to uninitialized parameters.
- Writing constraint rules that inadvertently modify global data.
- Forgetting to index parameters correctly when used inside indexed constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., HiGHS, CBC). Leverage Pyomo's status reporting for robust solution extraction and validation. This approach is portable across computing environments.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory('highs')`.
- Set options: `solver.options['time_limit'] = timeout`, `solver.options['threads'] = num_threads`. For MIP, set `solver.options['mip_rel_gap'] = 0.0` for exact solutions.

### Step 2 - Solve and Capture Results
- Call `results = solver.solve(model, tee=False)`.
- Access termination condition: `term = results.solver.termination_condition`.
- Access solver status: `status = results.solver.status`.

### Step 3 - Check Solution Availability
- Verify success: `if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:`.

### Step 4 - Extract and Process Solution Values
- Use `pyo.value(var)` to get variable values, casting to `int` for integer variables.
- Compile solution into a structured dictionary for downstream use.

### Step 5 - Perform Post-Solution Analysis
- Recompute constraint left-hand sides to validate the solution.
- Optionally, fix the objective to its optimal value and solve again with a secondary objective to explore alternative optimal solutions.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation (example uses abstract then concrete data)
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=vehicle_types)
model.L = pyo.Set(initialize=locations)
# ... define parameters, variables, constraints, objective as per abstract formulation

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    objective_value = pyo.value(model.obj)
    # Extract solution
    trips_sol = {(p,i,j): int(pyo.value(model.trips[p,i,j])) for p in model.P for i in model.L for j in model.L}
    print(f"Optimal cost: {objective_value}")
    # Validation
    total_cap = sum(capacity[p] * trips_sol[p,o,d] for p in vehicle_types)
    assert total_cap >= demand, "Validation failed."
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Relying solely on the solver's termination condition without checking the solver status, which may mask errors.
- Not handling the case where the solver returns a feasible but non-optimal solution.
- Attempting to extract variable values from an unsolved or infeasible model, causing runtime errors.
