---
name: Continuous Assignment with Supply-Demand Balance
description: |
  Model and solve continuous resource allocation between sources and destinations with supply limits, demand requirements, per-assignment capacities, and linear cost minimization.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Use Pyomo's structured modeling to define sets, parameters, and constraints declaratively, then solve with open-source LP solvers (HiGHS or CBC) for robust, scalable solutions.

### Step 1 - Define Sets and Parameters
- Create Pyomo `Set` objects for sources and destinations to index all model components.
- Define `Param` objects for supply, demand, cost, and per-assignment capacity, using dictionaries or arrays for initialization.

### Step 2 - Create Continuous Decision Variables
- Declare a non-negative continuous variable `x[i,j]` indexed over source and destination sets.
- Optionally embed per-assignment upper bounds directly in variable domain or via separate constraints.

### Step 3 - Formulate Supply and Demand Balance Constraints
- Add a supply constraint for each source: total outflow equals (or is less than or equal to) supply availability.
- Add a demand constraint for each destination: total inflow equals demand requirement.

### Step 4 - Add Per-Assignment Capacity Constraints
- For each source-destination pair, add an inequality constraint limiting `x[i,j]` to its maximum allowed value.
- Handle sentinel values (e.g., -1 for 'no limit') by conditionally skipping the constraint.

### Step 5 - Set Linear Minimization Objective
- Define the objective as the sum of `cost[i,j] * x[i,j]` over all pairs, with sense set to minimize.

### Formulation Template
```json
{
  "sets": ["SOURCES", "DESTINATIONS"],
  "parameters": ["supply[i]", "demand[j]", "cost[i,j]", "capacity[i,j]"],
  "decision_variables": ["x[i,j] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in SOURCES for j in DESTINATIONS)"
  },
  "constraints": [
    "supply_constraint[i]: sum(x[i,j] for j in DESTINATIONS) <= supply[i]",
    "demand_constraint[j]: sum(x[i,j] for i in SOURCES) == demand[j]",
    "capacity_constraint[i,j]: x[i,j] <= capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Forgetting to verify total supply meets total demand, which can cause infeasibility.
- Using sentinel values (like -1) in cost/capacity without proper handling, leading to unintended constraints.
- Not checking for solver availability before attempting solve, causing runtime errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using HiGHS or CBC with appropriate options, rigorously check solver status and termination conditions, then extract and verify the solution.

### Step 1 - Instantiate Solver with Options
- Create solver via `SolverFactory("highs")` or `SolverFactory("cbc")`.
- Set practical options: `time_limit`, `threads`, and for CBC `ratio=0.0` for optimality.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model)`.
- Verify `solver.status == SolverStatus.ok` and `termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Extract and Verify Solution
- Retrieve objective value via `pyo.value(model.obj)`.
- Iterate over variables `model.x[i,j]`, collect values above a small tolerance (e.g., 1e-6).
- Programmatically recompute supply/demand totals and check against original parameters to validate constraints.

### Step 4 - Output Structured Results
- Print total cost and a table of non-zero assignments with source, destination, amount, and cost contribution.
- Optionally output verification summaries for each constraint group.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (model definition from formulation steps)
model = pyo.ConcreteModel()
model.SOURCES = pyo.Set(initialize=sources_list)
model.DESTINATIONS = pyo.Set(initialize=destinations_list)
model.supply = pyo.Param(model.SOURCES, initialize=supply_dict)
model.demand = pyo.Param(model.DESTINATIONS, initialize=demand_dict)
model.cost = pyo.Param(model.SOURCES, model.DESTINATIONS, initialize=cost_dict)
model.capacity = pyo.Param(model.SOURCES, model.DESTINATIONS, initialize=capacity_dict)
model.x = pyo.Var(model.SOURCES, model.DESTINATIONS, domain=pyo.NonNegativeReals)
model.obj = pyo.Objective(
    expr=sum(model.cost[i,j] * model.x[i,j] for i in model.SOURCES for j in model.DESTINATIONS),
    sense=pyo.minimize
)
def supply_rule(m, i):
    return sum(m.x[i,j] for j in m.DESTINATIONS) <= m.supply[i]
model.supply_con = pyo.Constraint(model.SOURCES, rule=supply_rule)
def demand_rule(m, j):
    return sum(m.x[i,j] for i in m.SOURCES) == m.demand[j]
model.demand_con = pyo.Constraint(model.DESTINATIONS, rule=demand_rule)
def capacity_rule(m, i, j):
    return m.x[i,j] <= m.capacity[i,j]
model.capacity_con = pyo.Constraint(model.SOURCES, model.DESTINATIONS, rule=capacity_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = pyo.value(model.obj)
    # Extract non-zero assignments
    for i in model.SOURCES:
        for j in model.DESTINATIONS:
            val = pyo.value(model.x[i,j])
            if val > 1e-6:
                print(f"{i}->{j}: {val:.2f}")
    print(f"Total cost: {total_cost:.2f}")
else:
    print(f"Solver failed: status={status}, termination={term}")
```

### Common Pitfalls
- Assuming solver status 'ok' alone guarantees a valid solution; must also check termination condition.
- Not using a tolerance when checking variable values, leading to false positives from floating-point noise.
- Omitting solution verification, which can miss constraint violations due to numerical tolerances.

# Workflow 2 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
Use Google OR-Tools' linear solver API (GLOP) for a procedural, coefficient-based model build, ideal for straightforward LP formulations and integration with other OR-Tools components.

### Step 1 - Initialize Solver and Data Structures
- Create solver instance with `pywraplp.Solver.CreateSolver("GLOP")`.
- Organize input data as lists or dictionaries indexed by source and destination.

### Step 2 - Create Variables with Bounds
- For each source-destination pair, create a continuous variable `x[i][j]` via `solver.NumVar(lower_bound, upper_bound, name)`.
- Set upper bound directly to the per-assignment capacity limit, incorporating this constraint at variable creation.

### Step 3 - Build Supply Constraints
- For each source, create a constraint object with upper bound equal to supply availability.
- Add coefficient 1 for all variables `x[i][j]` where j varies, using `constraint.SetCoefficient(x[i][j], 1)`.

### Step 4 - Build Demand Constraints
- For each destination, create an equality constraint with bound equal to demand requirement.
- Add coefficient 1 for all variables `x[i][j]` where i varies.

### Step 5 - Set Linear Minimization Objective
- Create objective with `solver.Objective()`.
- For each variable `x[i][j]`, set its coefficient to `cost[i][j]` using `objective.SetCoefficient()`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["sources_list", "destinations_list"],
  "parameters": ["supply[i]", "demand[j]", "cost[i][j]", "capacity[i][j]"],
  "decision_variables": ["x[i][j] in [0, capacity[i][j]]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "supply_constraint[i]: sum(x[i][j] for j) <= supply[i]",
    "demand_constraint[j]: sum(x[i][j] for i) == demand[j]"
  ]
}
```

### Common Pitfalls
- Forgetting to check if solver creation succeeded (returns None if backend unavailable).
- Building constraints inefficiently with nested loops, causing slow model construction for large problems.
- Not leveraging variable upper bounds for per-assignment limits, adding unnecessary constraints.

## Solving stage

### Strategy Overview
Solve the linear program with GLOP, check for optimal/feasible status, extract solution values, and perform post-solve validation of all constraints.

### Step 1 - Solve and Check Result Status
- Execute `solver.Solve()`.
- Check returned status against `pywraplp.Solver.OPTIMAL` or `FEASIBLE`.

### Step 2 - Extract Objective and Variable Values
- Retrieve objective value via `objective.Value()`.
- For each variable, get solution value with `x[i][j].solution_value()`.

### Step 3 - Validate Constraint Satisfaction
- Recompute total outflow per source and inflow per destination from solution values.
- Verify each is within tolerance of supply/demand values.
- Check each variable value against its per-assignment capacity bound.

### Step 4 - Output Assignment Breakdown
- Print total cost and a detailed list of all non-zero assignments (source, destination, amount, cost contribution).
- Include summary totals per source and per destination for quick verification.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
if not solver:
    raise RuntimeError("Solver backend not available")

# Create variables with upper bounds
x = {}
for i in sources_list:
    for j in destinations_list:
        x[i, j] = solver.NumVar(0, capacity[i][j], f"x_{i}_{j}")

# Supply constraints
for i in sources_list:
    constraint = solver.Constraint(0, supply[i])
    for j in destinations_list:
        constraint.SetCoefficient(x[i, j], 1)

# Demand constraints
for j in destinations_list:
    constraint = solver.Constraint(demand[j], demand[j])
    for i in sources_list:
        constraint.SetCoefficient(x[i, j], 1)

# Objective
objective = solver.Objective()
for i in sources_list:
    for j in destinations_list:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# Solve with status / termination checks
status = solver.Solve()
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = objective.Value()
    # Extract non-zero assignments
    for i in sources_list:
        for j in destinations_list:
            val = x[i, j].solution_value()
            if val > 1e-6:
                print(f"{i}->{j}: {val:.2f}")
    print(f"Total cost: {total_cost:.2f}")
    # Verification (optional)
    for i in sources_list:
        total_out = sum(x[i, j].solution_value() for j in destinations_list)
        print(f"Source {i} total: {total_out:.2f} <= {supply[i]}")
else:
    print(f"No optimal/feasible solution found. Status: {status}")
```

### Common Pitfalls
- Confusing solver status codes (OPTIMAL vs. FEASIBLE) and not handling both.
- Not using a tolerance when checking variable values, causing false zero assignments.
- Skipping post-solve validation, potentially missing subtle constraint violations.
