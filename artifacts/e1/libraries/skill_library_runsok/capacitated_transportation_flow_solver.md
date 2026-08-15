---
name: Capacitated Transportation Flow Solver
description: |
  Model and solve capacitated transportation problems with supply-demand balance and arc capacity constraints using linear programming.

---
# Workflow 1 (OR-Tools LP with GLOP)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using Google OR-Tools' linear solver wrapper. This approach is efficient for pure LP formulations with continuous flow variables, leveraging GLOP's optimized algorithms. The model is built procedurally by creating variables and constraints directly within the solver object.

### Step 1 - Define Sets and Parameters
- Define sets `origins` and `destinations` as lists of identifiers.
- Create dictionaries for `supply[origin]`, `demand[destination]`, `cost[(origin, destination)]`, and `capacity[(origin, destination)]`.

### Step 2 - Create Flow Variables with Bounds
- For each `(i, j)` in `origins × destinations`, create a continuous variable `flow[i][j]`.
- Set the variable's lower bound to `0` and its upper bound directly to `capacity[i][j]` to implicitly enforce arc capacities.

### Step 3 - Add Supply and Demand Balance Constraints
- For each origin `i`, create a linear constraint: `sum(flow[i][j] for j in destinations) == supply[i]`.
- For each destination `j`, create a linear constraint: `sum(flow[i][j] for i in origins) == demand[j]`.

### Step 4 - Formulate Linear Cost Objective
- Define the objective as the sum of `cost[i][j] * flow[i][j]` over all origin-destination pairs.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": ["origins", "destinations"],
  "parameters": [
    {"name": "supply", "index": "origins"},
    {"name": "demand", "index": "destinations"},
    {"name": "cost", "index": ["origins", "destinations"]},
    {"name": "capacity", "index": ["origins", "destinations"]}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["origins", "destinations"], "type": "continuous", "bounds": "[0, capacity]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * flow[i][j] for i in origins for j in destinations)"
  },
  "constraints": [
    {"name": "supply_balance", "index": "origins", "expression": "sum(flow[i][j] for j in destinations) == supply[i]"},
    {"name": "demand_balance", "index": "destinations", "expression": "sum(flow[i][j] for i in origins) == demand[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to include zero-supply origins or zero-demand destinations in the sets, which can break constraint indexing.
- Using inequality (`<=`) for supply/demand constraints when exact balance is required.
- Not using capacity values as variable upper bounds, resulting in unnecessary explicit constraints and larger model size.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' `GLOP` linear solver. The workflow involves building the model within the solver API, invoking solve, rigorously checking termination status, and extracting/validating the solution.

### Step 1 - Initialize Solver and Build Model
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Build the model by executing the modeling steps, adding variables and constraints to the solver object.

### Step 2 - Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: accept `solver.OPTIMAL` or `solver.FEASIBLE`; handle `solver.INFEASIBLE` or `solver.ABNORMAL` with appropriate error messages.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value: `total_cost = solver.Objective().Value()`.
- For each variable `flow[i][j]`, get `flow_value = flow[i][j].solution_value()`.
- Verify supply/demand balances by recomputing sums and comparing to parameters within a numerical tolerance (e.g., `1e-6`).
- Ensure no flow value exceeds its capacity upper bound.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
flow = {}
for i in origins:
    for j in destinations:
        flow[i, j] = solver.NumVar(0, capacity[i, j], f'flow_{i}_{j}')
# Add constraints
for i in origins:
    ct = solver.Constraint(supply[i], supply[i])
    for j in destinations:
        ct.SetCoefficient(flow[i, j], 1)
for j in destinations:
    ct = solver.Constraint(demand[j], demand[j])
    for i in origins:
        ct.SetCoefficient(flow[i, j], 1)
# Set objective
objective = solver.Objective()
for i in origins:
    for j in destinations:
        objective.SetCoefficient(flow[i, j], cost[i, j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    solution_flows = {(i, j): flow[i, j].solution_value() for i in origins for j in destinations}
    # Validation checks here
else:
    raise Exception(f'Solver failed with status: {status}')
```

### Common Pitfalls
- Not checking solver status before reading solution values, leading to runtime errors.
- Using integer-specific solvers (e.g., CBC) for pure LP problems, sacrificing performance.
- Ignoring numerical tolerances when validating constraint satisfaction.

# Workflow 2 (Pyomo with Highs/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling syntax to create a structured, declarative mathematical program. This approach separates model definition from solver interaction, improving readability and maintainability. It supports multiple solvers like `highs` for LP or `cbc` for MILP.

### Step 1 - Declare Sets and Parameters
- Define Pyomo `Set` objects for `model.origins` and `model.destinations`.
- Define `Param` objects for `model.supply`, `model.demand`, `model.cost`, and `model.capacity`, indexed appropriately.

### Step 2 - Define Flow Variables
- Create a `Var` object `model.flow` indexed over `model.origins × model.destinations`.
- Set the domain to `NonNegativeReals` and optionally initialize bounds using `model.capacity` within a rule.

### Step 3 - Construct Balance Constraints
- Define a constraint rule for supply: for each `i` in `model.origins`, `sum(model.flow[i, j] for j in model.destinations) == model.supply[i]`.
- Define a constraint rule for demand: for each `j` in `model.destinations`, `sum(model.flow[i, j] for i in model.origins) == model.demand[j]`.

### Step 4 - Formulate Objective Function
- Define the objective expression as `sum(model.cost[i, j] * model.flow[i, j] for i in model.origins for j in model.destinations)`.
- Use `pyo.minimize` to set the sense.

### Formulation Template
```json
{
  "sets": ["origins", "destinations"],
  "parameters": [
    {"name": "supply", "index": "origins"},
    {"name": "demand", "index": "destinations"},
    {"name": "cost", "index": ["origins", "destinations"]},
    {"name": "capacity", "index": ["origins", "destinations"]}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["origins", "destinations"], "type": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * flow[i, j] for i in origins for j in destinations)"
  },
  "constraints": [
    {"name": "supply_balance", "index": "origins", "expression": "sum(flow[i, j] for j in destinations) == supply[i]"},
    {"name": "demand_balance", "index": "destinations", "expression": "sum(flow[i, j] for i in origins) == demand[j]"},
    {"name": "arc_capacity", "index": ["origins", "destinations"], "expression": "flow[i, j] <= capacity[i, j]"}
  ]
}
```

### Common Pitfalls
- Defining constraints with incorrect indexing, leading to `KeyError` or missing constraints.
- Using mutable default arguments (like lists) in Pyomo rule functions.
- Not specifying `within` domain for variables, defaulting to `Any` and causing solver compatibility issues.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., `highs` for LP, `cbc` for MILP). Configure solver options for performance, check termination conditions rigorously, and extract results using Pyomo's value functions.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory('highs')`.
- Set options like `time_limit` or `threads` if needed.

### Step 2 - Solve and Inspect Termination
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` and `results.solver.termination_condition`. Accept `optimal` or `feasible`; handle `infeasible` or `other` accordingly.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value: `pyo.value(model.obj)`.
- Extract variable values: `pyo.value(model.flow[i, j])` for all pairs.
- Programmatically verify all constraints are satisfied within tolerance, including capacity constraints if not enforced via variable bounds.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.origins = pyo.Set(initialize=origins)
model.destinations = pyo.Set(initialize=destinations)
model.supply = pyo.Param(model.origins, initialize=supply_data)
model.demand = pyo.Param(model.destinations, initialize=demand_data)
model.cost = pyo.Param(model.origins, model.destinations, initialize=cost_data)
model.capacity = pyo.Param(model.origins, model.destinations, initialize=capacity_data)
model.flow = pyo.Var(model.origins, model.destinations, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, m.capacity[i, j]))
def supply_rule(m, i):
    return sum(m.flow[i, j] for j in m.destinations) == m.supply[i]
model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)
def demand_rule(m, j):
    return sum(m.flow[i, j] for i in m.origins) == m.demand[j]
model.demand_con = pyo.Constraint(model.destinations, rule=demand_rule)
model.obj = pyo.Objective(expr=sum(m.cost[i, j] * m.flow[i, j] for i in m.origins for j in m.destinations), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)
if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:
    total_cost = pyo.value(model.obj)
    solution_flows = {(i, j): pyo.value(model.flow[i, j]) for i in model.origins for j in model.destinations}
    # Validation checks here
else:
    raise Exception(f'Solver failed: {results.solver.termination_condition}')
```

### Common Pitfalls
- Confusing `solver.status` with `termination_condition`; both must be checked for a complete solution status.
- Not using `pyo.value()` to extract parameter or variable values, leading to Pyomo expression objects.
- Forgetting to pass the model instance to the solver's `solve` method.
