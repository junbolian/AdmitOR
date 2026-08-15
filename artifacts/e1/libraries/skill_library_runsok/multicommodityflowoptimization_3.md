---
name: MultiCommodityFlowOptimization
description: |
  Model and solve multi-commodity flow problems with arc capacities, supply limits, and demand satisfaction to minimize total cost.
---

# Workflow 1 (LP Solver with Direct API)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using a direct solver API (e.g., OR-Tools, HiGHS). This approach is procedural, building the model by explicitly creating variables and constraints in nested loops, suitable for rapid prototyping and integration into non-Pyomo environments.

### Step 1 - Define Sets and Indexed Parameters
- Declare the fundamental sets: origins, destinations, and commodities.
- Organize all input data into indexed dictionaries or lists for clear access: supply per origin-commodity, demand per destination-commodity, cost per origin-destination-commodity, and capacity per origin-destination pair.

### Step 2 - Create Decision Variables
- Instantiate continuous, non-negative flow variables for each combination of origin, destination, and commodity.
- Use a consistent naming convention (e.g., `x[o][d][c]`) and set lower bound to 0 and upper bound to infinity.

### Step 3 - Formulate Constraints
- **Supply Constraints:** For each origin and commodity, sum of outgoing flows must be less than or equal to available supply.
- **Demand Constraints:** For each destination and commodity, sum of incoming flows must exactly equal the required demand.
- **Arc Capacity Constraints:** For each origin-destination pair, sum of flows across all commodities must be less than or equal to the arc capacity.

### Step 4 - Define Objective Function
- Construct a linear objective to minimize the total cost, summing the product of flow variables and their respective per-unit costs over all arcs and commodities.

### Formulation Template
```json
{
  "sets": ["origins", "destinations", "commodities"],
  "parameters": [
    {"name": "supply", "index": ["origin", "commodity"]},
    {"name": "demand", "index": ["destination", "commodity"]},
    {"name": "cost", "index": ["origin", "destination", "commodity"]},
    {"name": "capacity", "index": ["origin", "destination"]}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["origin", "destination", "commodity"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[o][d][c] * flow[o][d][c] for o in origins for d in destinations for c in commodities)"
  },
  "constraints": [
    {"name": "supply_limit", "expression": "sum(flow[o][d][c] for d in destinations) <= supply[o][c]", "index": ["origin", "commodity"]},
    {"name": "demand_satisfaction", "expression": "sum(flow[o][d][c] for o in origins) == demand[d][c]", "index": ["destination", "commodity"]},
    {"name": "arc_capacity", "expression": "sum(flow[o][d][c] for c in commodities) <= capacity[o][d]", "index": ["origin", "destination"]}
  ]
}
```

### Common Pitfalls
- Forgetting to sum over the correct index in capacity constraints (e.g., summing over commodities, not origins).
- Using inequality (`<=`) for demand constraints when exact fulfillment is required.
- Not verifying total supply meets or exceeds total demand for each commodity before solving, which can lead to infeasibility.

## Solving stage

### Strategy Overview
Solve the LP using a dedicated solver (e.g., GLOP, HiGHS) configured for performance. Implement robust post-solve verification to check constraint satisfaction and handle solver statuses appropriately.

### Step 1 - Configure and Run Solver
- Instantiate the solver (e.g., `GLOP` for LP) and set practical limits like time limit and verbosity.
- Invoke the solver and capture the status code.

### Step 2 - Validate Solution Status
- Check if the status is `OPTIMAL` or `FEASIBLE`. If not, exit with a structured error message detailing the solver status.
- Extract the objective value only after confirming a successful status.

### Step 3 - Verify Solution Feasibility
- Programmatically recompute the left-hand side of each constraint family (supply, demand, capacity) using the solved variable values.
- Compare against the right-hand side with a numerical tolerance (e.g., 1e-6). Log any violations for diagnostics.

### Step 4 - Extract and Report Solution
- Iterate through all flow variables and collect only those with a value greater than a small epsilon.
- Generate a summary report showing total cost, supply utilization, demand fulfillment, and capacity usage.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
solver.SetTimeLimit(30000)

# Define sets and data structures
origins = list(range(num_origins))
destinations = list(range(num_destinations))
commodities = list(range(num_commodities))

# Create variables
flow = {}
for o in origins:
    for d in destinations:
        for c in commodities:
            flow[o, d, c] = solver.NumVar(0, solver.infinity(), f'flow_{o}_{d}_{c}')

# Add constraints
# Supply constraints
for o in origins:
    for c in commodities:
        constraint = solver.Constraint(0, supply[o][c])
        for d in destinations:
            constraint.SetCoefficient(flow[o, d, c], 1)

# Demand constraints (equality)
for d in destinations:
    for c in commodities:
        constraint = solver.Constraint(demand[d][c], demand[d][c])
        for o in origins:
            constraint.SetCoefficient(flow[o, d, c], 1)

# Capacity constraints
for o in origins:
    for d in destinations:
        constraint = solver.Constraint(0, capacity[o][d])
        for c in commodities:
            constraint.SetCoefficient(flow[o, d, c], 1)

# Set objective
objective = solver.Objective()
for o in origins:
    for d in destinations:
        for c in commodities:
            objective.SetCoefficient(flow[o, d, c], cost[o][d][c])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Verification and output logic
    total_cost = objective.Value()
    # ... implement verification and reporting
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming an `OPTIMAL` status guarantees numerical feasibility without a tolerance check.
- Not setting a time limit, allowing the solver to run indefinitely on large instances.
- Extracting variable values without checking the solver status first, leading to errors.

# Workflow 2 (AML with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem using an Algebraic Modeling Language (Pyomo). This declarative approach separates model definition from solver interaction, promoting readability, maintainability, and easier constraint debugging through rule-based definitions.

### Step 1 - Declare Abstract Sets
- Define Pyomo `Set` components for origins, destinations, and commodities. This establishes the indexing domain for all model elements.

### Step 2 - Declare Parameters
- Define `Param` components for supply, demand, cost, and capacity, indexed by the appropriate sets. Use `initialize` with a dictionary for efficient data loading.

### Step 3 - Define Decision Variables
- Create a `Var` component for flow, indexed over the Cartesian product of the three sets, with a domain of `NonNegativeReals`.

### Step 4 - Construct Constraints via Rules
- Define three `Constraint` components, each indexed by the relevant sets.
- Write separate `rule` functions that, given the model and indices, return the algebraic expression for the supply limit, demand satisfaction, and arc capacity constraints.

### Step 5 - Formulate Objective
- Define an `Objective` component with a rule that sums the product of cost parameters and flow variables over all indices, set to minimize.

### Formulation Template
```json
{
  "sets": ["model.O", "model.D", "model.C"],
  "parameters": [
    {"name": "model.supply", "index": ["O", "C"]},
    {"name": "model.demand", "index": ["D", "C"]},
    {"name": "model.cost", "index": ["O", "D", "C"]},
    {"name": "model.capacity", "index": ["O", "D"]}
  ],
  "decision_variables": [
    {"name": "model.flow", "index": ["O", "D", "C"], "type": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum(model.cost[o, d, c] * model.flow[o, d, c] for o in model.O for d in model.D for c in model.C)"
  },
  "constraints": [
    {"name": "model.supply_limit", "expression": "sum(model.flow[o, d, c] for d in model.D) <= model.supply[o, c]", "index": ["O", "C"]},
    {"name": "model.demand_satisfaction", "expression": "sum(model.flow[o, d, c] for o in model.O) == model.demand[d, c]", "index": ["D", "C"]},
    {"name": "model.arc_capacity", "expression": "sum(model.flow[o, d, c] for c in model.C) <= model.capacity[o, d]", "index": ["O", "D"]}
  ]
}
```

### Common Pitfalls
- Incorrectly scoping indices within constraint rules, leading to `KeyError`.
- Using mutable default arguments (like lists) in rule functions.
- Not initializing all required parameters before creating the instance, causing instantiation errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a compatible solver (e.g., CBC, HiGHS) via a standard interface. Leverage Pyomo's utilities for solution loading and status checking, and implement a reusable verification function.

### Step 1 - Instantiate Model and Solve
- Create a concrete model instance with the provided data.
- Use `SolverFactory` to configure the solver (e.g., `'cbc'`) with options like time limit and threads.
- Call `solve()` on the model instance.

### Step 2 - Check Solver Termination Condition
- Inspect both the `SolverStatus` and `TerminationCondition` of the results object.
- Proceed only if the status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Validate Solution Against Constraints
- Write a function that iterates over all constraints in the model instance.
- For each constraint, evaluate its body expression using the solved variable values and compare it to the bound with a tolerance.
- Log any constraint violations for analysis.

### Step 4 - Generate Solution Report
- Extract the objective value via `pyo.value(model.obj)`.
- Iterate through the flow variable and print non-zero shipments, optionally aggregating by origin or commodity.
- Calculate and report high-level metrics like supply utilization and arc capacity usage.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.O = pyo.Set(initialize=origins)
model.D = pyo.Set(initialize=destinations)
model.C = pyo.Set(initialize=commodities)

model.supply = pyo.Param(model.O, model.C, initialize=supply_data)
model.demand = pyo.Param(model.D, model.C, initialize=demand_data)
model.cost = pyo.Param(model.O, model.D, model.C, initialize=cost_data)
model.capacity = pyo.Param(model.O, model.D, initialize=capacity_data)

model.flow = pyo.Var(model.O, model.D, model.C, domain=pyo.NonNegativeReals)

def supply_rule(m, o, c):
    return sum(m.flow[o, d, c] for d in m.D) <= m.supply[o, c]
model.supply_con = pyo.Constraint(model.O, model.C, rule=supply_rule)

def demand_rule(m, d, c):
    return sum(m.flow[o, d, c] for o in m.O) == m.demand[d, c]
model.demand_con = pyo.Constraint(model.D, model.C, rule=demand_rule)

def capacity_rule(m, o, d):
    return sum(m.flow[o, d, c] for c in m.C) <= m.capacity[o, d]
model.capacity_con = pyo.Constraint(model.O, model.D, rule=capacity_rule)

model.obj = pyo.Objective(
    expr=sum(model.cost[o, d, c] * model.flow[o, d, c] for o in model.O for d in model.D for c in model.C),
    sense=pyo.minimize
)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    # ... implement verification and reporting
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus` (ok/warning/error) with `TerminationCondition` (optimal/infeasible/etc.).
- Not using `pyo.value()` to evaluate expressions post-solve, leading to symbolic objects instead of numbers.
- Assuming the model is solved in-place; the `solve` command returns a results object but does not modify the original model unless the solution is loaded.
