---
name: Balanced Transportation Problem
description: |
  Model and solve bipartite flow problems with equal total supply and total demand using linear programming to minimize total cost.

---

# Workflow 1 (Pyomo with LP Solver)

## Modeling stage

### Strategy Overview
Model the problem as a balanced bipartite flow network using Pyomo's abstract modeling capabilities. Define sets for origins and destinations, parameters for supply, demand, and costs, and continuous flow variables. Use equality constraints for both supply and demand balances.

### Step 1 - Define Sets and Parameters
- Define index sets for supply nodes (`origins`) and demand nodes (`destinations`).
- Store supply capacities as a parameter indexed by origin.
- Store demand requirements as a parameter indexed by destination.
- Define a 2D cost parameter `cost[i,j]` representing the unit transportation cost from origin `i` to destination `j`.

### Step 2 - Create Decision Variables
- Create a continuous, non-negative decision variable `flow[i,j]` for each origin-destination pair.
- Use `pyo.NonNegativeReals` domain to enforce non-negativity.

### Step 3 - Formulate Constraints
- **Supply Balance**: For each origin `i`, sum of outgoing flows must equal its supply: `sum(flow[i,j] for j in destinations) == supply[i]`.
- **Demand Balance**: For each destination `j`, sum of incoming flows must equal its demand: `sum(flow[i,j] for i in origins) == demand[j]`.

### Step 4 - Define Objective
- Formulate a linear cost minimization objective: `minimize sum(cost[i,j] * flow[i,j] for all i,j)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "origins", "description": "Set of supply nodes"},
    {"name": "destinations", "description": "Set of demand nodes"}
  ],
  "parameters": [
    {"name": "supply", "index": "origins", "description": "Available supply at each origin"},
    {"name": "demand", "index": "destinations", "description": "Required demand at each destination"},
    {"name": "cost", "index": ["origins", "destinations"], "description": "Unit transportation cost matrix"}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["origins", "destinations"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * flow[i,j] for i in origins, j in destinations)"
  },
  "constraints": [
    {"name": "supply_balance", "index": "origins", "expression": "sum(flow[i,j] for j in destinations) == supply[i]"},
    {"name": "demand_balance", "index": "destinations", "expression": "sum(flow[i,j] for i in origins) == demand[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand before solving, which is required for feasibility with equality constraints.
- Using inefficient data structures for large cost matrices; prefer dictionary or array-based parameter initialization.
- Defining variable bounds (like capacity limits) as separate constraints instead of using the variable's upper bound attribute.

## Solving stage

### Strategy Overview
Solve the linear program using an open-source solver (e.g., CBC, HiGHS) via Pyomo's `SolverFactory`. Configure solver options for performance, check termination status rigorously, and validate the solution against the original constraints.

### Step 1 - Initialize Solver and Set Options
- Create a solver instance using `SolverFactory("solver_name")` (e.g., "cbc" or "highs").
- Set practical options: time limit (`seconds`), optimality tolerance (`ratio`), and thread count for parallel processing.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model, tee=False)`.
- Check that the solver status is `SolverStatus.ok`.
- Verify the termination condition is either `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract and Validate Results
- Extract the objective value using `float(pyo.value(model.obj))`.
- For each origin and destination, compute the sum of flow values and compare to supply/demand parameters within a small tolerance (e.g., 1e-6).
- Optionally, filter and report only non-zero flows for clarity.

### Step 4 - Handle Failure Cases
- If solver status is not ok or termination is not acceptable, output a structured error message (e.g., JSON) indicating infeasibility, unboundedness, or other failure reasons.
- Consider providing diagnostic information like total supply vs. total demand.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# ... (model built as per formulation)

# Solve
solver = pyo.SolverFactory("cbc")  # or "highs"
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False)

# Check status
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = float(pyo.value(model.obj))
    # Validation loops
    for i in model.origins:
        total_out = sum(pyo.value(model.flow[i, j]) for j in model.destinations)
        assert abs(total_out - model.supply[i]) < 1e-6, f"Supply balance violated for origin {i}"
    print(f"RESULT:{total_cost}")
else:
    error_info = {"status": "failed", "reason": f"solver status: {status}, termination: {term}"}
    print(f"RESULT_JSON:{json.dumps(error_info)}")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to extraction of invalid results.
- Omitting solution validation, which can mask numerical issues or solver errors.
- Setting solver options (like `threads`) that conflict with the solver's initialization, causing crashes.

# Workflow 2 (OR-Tools with GLOP)

## Modeling stage

### Strategy Overview
Model the balanced transportation problem directly using OR-Tools' linear solver wrapper. Create variables with implicit lower bounds, add equality constraints for supply and demand balances via coefficient setting, and define a linear objective.

### Step 1 - Prepare Data Structures
- Store supply and demand as lists or arrays.
- Store costs as a 2D list `cost[i][j]`.
- Verify that `sum(supply) == sum(demand)`.

### Step 2 - Create Solver and Variables
- Instantiate a linear solver (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Create a continuous variable `flow[i][j]` for each origin-destination pair, with lower bound 0 and infinite upper bound (or explicit capacity if present).

### Step 3 - Add Balance Constraints
- **Supply Constraints**: For each origin `i`, create a constraint with lower and upper bound equal to `supply[i]`. Set coefficient 1 for all variables `flow[i][j]` where `j` ranges over destinations.
- **Demand Constraints**: For each destination `j`, create a constraint with lower and upper bound equal to `demand[j]`. Set coefficient 1 for all variables `flow[i][j]` where `i` ranges over origins.

### Step 4 - Set Objective
- Create an objective object and set minimization sense.
- For each variable `flow[i][j]`, set its coefficient to `cost[i][j]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "origins", "description": "List of supply node indices"},
    {"name": "destinations", "description": "List of demand node indices"}
  ],
  "parameters": [
    {"name": "supply", "index": "origins", "description": "List of supply amounts"},
    {"name": "demand", "index": "destinations", "description": "List of demand amounts"},
    {"name": "cost", "index": ["origins", "destinations"], "description": "2D list of unit costs"}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["origins", "destinations"], "domain": "continuous, >=0"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * flow[i][j] for i in origins, j in destinations)"
  },
  "constraints": [
    {"name": "supply_constraint", "index": "origins", "expression": "sum(flow[i][j] for j in destinations) == supply[i]"},
    {"name": "demand_constraint", "index": "destinations", "expression": "sum(flow[i][j] for i in origins) == demand[j]"}
  ]
}
```

### Common Pitfalls
- Creating variables with explicit upper bounds (capacity) as separate constraints instead of using the variable's upper bound argument, which can be more efficient.
- Incorrectly ordering loops when setting constraint coefficients, leading to wrong constraint definitions.
- Not handling the case where solver creation fails (e.g., `solver` is `None`).

## Solving stage

### Strategy Overview
Solve the linear program using OR-Tools' GLOP solver. After solving, verify the solution's feasibility and optimality status, extract the objective value, and perform post-solution validation of constraints.

### Step 1 - Solve and Check Status
- Call `solver.Solve()`.
- Check if the result status is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`.

### Step 2 - Extract Objective and Variable Values
- Retrieve the objective value via `objective.Value()`.
- For each variable, get its solution value via `flow[i][j].solution_value()`.

### Step 3 - Validate Solution
- For each origin, sum the outgoing flows and compare to its supply within tolerance.
- For each destination, sum the incoming flows and compare to its demand within tolerance.
- Report any violations.

### Step 4 - Output Results
- Print the total cost with a `RESULT:` prefix for easy parsing.
- Optionally, output a summary of non-zero flows.

### Code Usage
```python
from ortools.linear_solver import pywraplp
import math

# ... (data prepared)

# Create solver
solver = pywraplp.Solver.CreateSolver("GLOP")
if solver is None:
    raise RuntimeError("Solver creation failed")

# Create variables
flow = {}
for i in range(num_origins):
    for j in range(num_destinations):
        # Use infinity for unbounded upper bound, or set capacity[i][j] if present
        flow[i, j] = solver.NumVar(0, solver.infinity(), f"flow_{i}_{j}")

# Supply constraints
for i in range(num_origins):
    constraint = solver.Constraint(supply[i], supply[i])
    for j in range(num_destinations):
        constraint.SetCoefficient(flow[i, j], 1)

# Demand constraints
for j in range(num_destinations):
    constraint = solver.Constraint(demand[j], demand[j])
    for i in range(num_origins):
        constraint.SetCoefficient(flow[i, j], 1)

# Objective
objective = solver.Objective()
for i in range(num_origins):
    for j in range(num_destinations):
        objective.SetCoefficient(flow[i, j], cost[i][j])
objective.SetMinimization()

# Solve
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    total_cost = objective.Value()
    # Validation
    for i in range(num_origins):
        total_out = sum(flow[i, j].solution_value() for j in range(num_destinations))
        assert abs(total_out - supply[i]) < 1e-6
    print(f"RESULT:{total_cost}")
else:
    print(f"RESULT:failed (solver status: {status})")
```

### Common Pitfalls
- Assuming `OPTIMAL` is the only acceptable status; `FEASIBLE` is also acceptable for a valid solution.
- Not using a tolerance when validating constraint satisfaction due to floating-point arithmetic.
- Forgetting to check if the solver object was created successfully (`solver is None`).
