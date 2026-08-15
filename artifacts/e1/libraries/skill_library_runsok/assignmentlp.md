---
name: AssignmentLP
description: |
  Model and solve linear assignment problems with supply, demand, and per-assignment capacity limits using continuous decision variables to minimize linear cost.
---

# Workflow 1 (OR-Tools LP)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using Google OR-Tools' linear solver wrapper. This approach directly embeds variable bounds and uses coefficient-based constraint building for efficient model construction.

### Step 1 - Define Sets and Parameters
- Identify the source set (e.g., `sources`) and destination set (e.g., `destinations`).
- Collect parameters: `availability` per source, `requirement` per destination, `cost` and `limit` per source-destination pair.

### Step 2 - Create Decision Variables
- Instantiate a continuous decision variable for each source-destination pair.
- Set the variable's lower bound to 0 and its upper bound directly to the `limit[i][j]` parameter.

### Step 3 - Formulate Constraints
- Add a **Supply Constraint** for each source: the sum of outgoing assignments must be ≤ its `availability`.
- Add a **Demand Constraint** for each destination: the sum of incoming assignments must equal its `requirement`.
- Note: The individual capacity limits are already enforced via variable upper bounds.

### Step 4 - Define Objective
- Define a linear objective to minimize the total cost, summing `cost[i][j] * variable[i][j]` over all pairs.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "availability", "index": "sources"},
    {"name": "requirement", "index": "destinations"},
    {"name": "cost", "index": ["sources", "destinations"]},
    {"name": "limit", "index": ["sources", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "type": "continuous", "lb": 0, "ub": "limit"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in sources for j in destinations)"
  },
  "constraints": [
    {"name": "supply", "index": "sources", "expression": "sum(x[i][j] for j in destinations) <= availability[i]"},
    {"name": "demand", "index": "destinations", "expression": "sum(x[i][j] for i in sources) == requirement[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to check if total supply ≥ total demand, which can lead to infeasibility.
- Using a MIP solver for a pure LP problem, which is less efficient than a dedicated LP solver like `GLOP`.
- Not verifying that each `limit[i][j]` is non-negative, which can cause solver errors.

## Solving stage

### Strategy Overview
Use the OR-Tools `pywraplp` API to build and solve the model. Focus on systematic solution validation and clear result extraction.

### Step 1 - Initialize Solver
- Create a solver instance (e.g., `solver = pywraplp.Solver.CreateSolver('GLOP')`).
- For problems requiring integer extensions, use `SCIP` or `CBC`.

### Step 2 - Build Model from Formulation
- Create variables using `solver.NumVar(lb, ub, name)`.
- Add constraints using `solver.Add(linear_expr <=/== value)`.
- Set the objective using `solver.Minimize()` or `solver.Maximize()` with `SetCoefficient()`.

### Step 3 - Solve and Check Status
- Execute `solver.Solve()`.
- Check the result status (`solver.ResultStatus()`). Accept `OPTIMAL` or `FEASIBLE` statuses.

### Step 4 - Validate and Extract Solution
- Extract variable values using `variable.solution_value()`.
- Programmatically verify all constraints (supply, demand, individual limits) are satisfied within a small tolerance (e.g., 1e-6).
- Compute and report the total cost and a breakdown of non-zero assignments.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('GLOP')
# Assume sets and parameters are defined
x = {}
for i in sources:
    for j in destinations:
        x[i,j] = solver.NumVar(0, limit[i][j], f'x_{i}_{j}')

# Supply constraints
for i in sources:
    ct = solver.Constraint(0, availability[i])
    for j in destinations:
        ct.SetCoefficient(x[i,j], 1)

# Demand constraints
for j in destinations:
    ct = solver.Constraint(requirement[j], requirement[j])
    for i in sources:
        ct.SetCoefficient(x[i,j], 1)

# Objective
obj = solver.Objective()
for i in sources:
    for j in destinations:
        obj.SetCoefficient(x[i,j], cost[i][j])
obj.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = obj.Value()
    # Extract and validate solution
    for i in sources:
        for j in destinations:
            val = x[i,j].solution_value()
            if val > 1e-6:
                print(f'{i}->{j}: {val}')
else:
    print('No optimal/feasible solution found.')
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Using a loose tolerance for equality constraints, potentially missing significant violations.
- Overlooking the need to pre-check feasibility conditions (e.g., `sum(availability) >= sum(requirement)`).

# Workflow 2 (Pyomo LP)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model API, which provides a high-level, declarative syntax. This approach cleanly separates model structure from data and leverages Pyomo's rule-based constraint definitions.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `sources` and `destinations`.
- Declare `Param` objects for `availability`, `requirement`, `cost`, and `limit` with appropriate indexing.

### Step 2 - Define Decision Variables
- Create a `Var` indexed over the Cartesian product of sources and destinations.
- Specify `domain=pyo.NonNegativeReals`. The individual upper bounds (`limit`) are enforced via a separate constraint.

### Step 3 - Define Constraints via Rules
- Implement a **Supply Constraint** rule: for each source, sum of outgoing variables ≤ its availability.
- Implement a **Demand Constraint** rule: for each destination, sum of incoming variables == its requirement.
- Implement an **Individual Limit Constraint** rule: for each pair, variable ≤ corresponding limit.

### Step 4 - Define Objective
- Define an `Objective` rule that sums `cost[i,j] * variable[i,j]` over all indices, with sense `minimize`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "availability", "index": "sources"},
    {"name": "requirement", "index": "destinations"},
    {"name": "cost", "index": ["sources", "destinations"]},
    {"name": "limit", "index": ["sources", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "type": "continuous", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in sources for j in destinations)"
  },
  "constraints": [
    {"name": "supply", "index": "sources", "expression": "sum(x[i,j] for j in destinations) <= availability[i]"},
    {"name": "demand", "index": "destinations", "expression": "sum(x[i,j] for i in sources) == requirement[j]"},
    {"name": "limit", "index": ["sources", "destinations"], "expression": "x[i,j] <= limit[i,j]"}
  ]
}
```

### Common Pitfalls
- Storing input data outside the model, making it inaccessible for post-solution validation.
- Using `ConcreteModel` without first initializing all sets and parameters, leading to build errors.
- Defining constraints with incorrect indexing in the rule's return statement.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with LP solvers like `cbc` or `highs`. Emphasize robust solution status checking and systematic validation of results.

### Step 1 - Instantiate Solver
- Create a solver object: `solver = SolverFactory('cbc')`.
- Configure solver options if needed (e.g., `seconds` for time limit).

### Step 2 - Solve and Inspect Termination Condition
- Execute `results = solver.solve(model, load_solutions=False)`.
- Check `results.solver.status` and `results.solver.termination_condition`. Accept `optimal` or `feasible`.

### Step 3 - Load and Validate Solution
- If the solve was successful, load the solution into the model: `model.solutions.load_from(results)`.
- Extract the objective value via `pyo.value(model.obj)`.
- Programmatically loop through all constraints to verify satisfaction within tolerance.

### Step 4 - Report and Handle Failures
- Print a detailed assignment breakdown for non-zero variable values.
- For failed solves, output the solver status and termination condition for debugging.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=sources_list)
model.destinations = pyo.Set(initialize=destinations_list)
# Define parameters (data can be supplied via `initialize` dict)
model.availability = pyo.Param(model.sources, initialize=availability_dict)
model.requirement = pyo.Param(model.destinations, initialize=requirement_dict)
model.cost = pyo.Param(model.sources, model.destinations, initialize=cost_dict)
model.limit = pyo.Param(model.sources, model.destinations, initialize=limit_dict)

model.x = pyo.Var(model.sources, model.destinations, domain=pyo.NonNegativeReals)

def supply_rule(m, i):
    return sum(m.x[i, j] for j in m.destinations) <= m.availability[i]
model.supply = pyo.Constraint(model.sources, rule=supply_rule)

def demand_rule(m, j):
    return sum(m.x[i, j] for i in m.sources) == m.requirement[j]
model.demand = pyo.Constraint(model.destinations, rule=demand_rule)

def limit_rule(m, i, j):
    return m.x[i, j] <= m.limit[i, j]
model.limit_con = pyo.Constraint(model.sources, model.destinations, rule=limit_rule)

def obj_rule(m):
    return sum(m.cost[i, j] * m.x[i, j] for i in m.sources for j in m.destinations)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, load_solutions=False)

if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    model.solutions.load_from(results)
    total_cost = pyo.value(model.obj)
    # Validate and report
    for i in model.sources:
        for j in model.destinations:
            val = pyo.value(model.x[i, j])
            if val > 1e-6:
                print(f'{i}->{j}: {val}')
else:
    print(f'Solve failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}')
```

### Common Pitfalls
- Loading the solution automatically (`load_solutions=True`) without checking termination condition first.
- Not using `pyo.value()` to access variable and parameter values post-solution.
- Assuming the solver interface automatically handles infeasibility; always implement pre-feasibility checks.
