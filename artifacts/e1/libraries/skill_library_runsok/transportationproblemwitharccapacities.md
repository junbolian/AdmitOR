---
name: TransportationProblemWithArcCapacities
description: |
  Model and solve balanced transportation problems with per-arc capacity limits and linear costs using continuous non-negative flow variables.
---

# Workflow 1 (Linear Programming with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using the OR-Tools `pywraplp` API. The model is built directly in the solver's native object structure, defining variables with explicit bounds and constraints via coefficient setting.

### Step 1 - Define Data Structures
- Organize supply, demand, cost, and capacity data as lists or 2D arrays for clear indexing.
- Ensure total supply equals total demand for feasibility.
- Use placeholders like `SUPPLY_LIST`, `DEMAND_LIST`, `COST_MATRIX`, and `CAPACITY_MATRIX`.

### Step 2 - Create Decision Variables
- Define continuous, non-negative decision variables `x[i][j]` for flow from source `i` to sink `j`.
- Set the variable's upper bound directly to the per-arc capacity limit `cap[i][j]` using `solver.NumVar(0, cap[i][j], name)`.

### Step 3 - Formulate Supply and Demand Constraints
- For each source `i`, add an equality constraint: `sum_j x[i][j] == supply[i]`.
- For each sink `j`, add an equality constraint: `sum_i x[i][j] == demand[j]`.

### Step 4 - Define Linear Objective
- Minimize total linear cost: `sum_i sum_j cost[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    "sources: list of source indices",
    "sinks: list of sink indices"
  ],
  "parameters": [
    "supply[sources]: amount available at each source",
    "demand[sinks]: amount required at each sink",
    "cost[sources][sinks]: unit cost of flow from i to j",
    "capacity[sources][sinks]: maximum flow allowed from i to j"
  ],
  "decision_variables": [
    "x[sources][sinks]: continuous, non-negative flow from source i to sink j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_i sum_j cost[i][j] * x[i][j]"
  },
  "constraints": [
    "supply_balance[i]: sum_j x[i][j] == supply[i] for all i",
    "demand_balance[j]: sum_i x[i][j] == demand[j] for all j",
    "arc_capacity[i][j]: x[i][j] <= capacity[i][j] for all i, j"
  ]
}
```

### Common Pitfalls
- Forgetting to set the variable's upper bound, leaving it unbounded and violating capacity limits.
- Creating constraints with incorrect right-hand side values, breaking the supply-demand balance.
- Not verifying that total supply equals total demand, leading to an infeasible model.

## Solving stage

### Strategy Overview
Use the OR-Tools `GLOP` linear programming solver. Initialize the solver, build the model using the steps above, solve, and then rigorously check the solution status and feasibility.

### Step 1 - Solver Initialization
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- For mixed-integer problems, use `'CBC'` or `'SCIP'`.

### Step 2 - Build Model and Solve
- Execute the modeling steps (Define Data Structures, Create Variables, Formulate Constraints, Define Objective).
- Call `status = solver.Solve()` to run the optimization.

### Step 3 - Check Solution Status
- Verify the solver status: `if status in (solver.OPTIMAL, solver.FEASIBLE):`.
- If the status is not optimal or feasible, handle the error and do not extract solution values.

### Step 4 - Extract and Validate Results
- Extract the objective value: `total_cost = solver.Objective().Value()`.
- Retrieve variable values using `x[i,j].solution_value()`.
- Programmatically verify all supply, demand, and capacity constraints are satisfied within a small tolerance (e.g., 1e-6).

### Code Usage
```python
# build model from formulation
import pywraplp

# 1. Data definition (placeholders)
num_supply = len(SUPPLY_LIST)
num_demand = len(DEMAND_LIST)

# 2. Solver initialization
solver = pywraplp.Solver.CreateSolver('GLOP')

# 3. Variable creation
x = {}
for i in range(num_supply):
    for j in range(num_demand):
        x[i, j] = solver.NumVar(0, CAPACITY_MATRIX[i][j], f'x_{i}_{j}')

# 4. Supply constraints
for i in range(num_supply):
    constraint = solver.Constraint(SUPPLY_LIST[i], SUPPLY_LIST[i])
    for j in range(num_demand):
        constraint.SetCoefficient(x[i, j], 1)

# 5. Demand constraints
for j in range(num_demand):
    constraint = solver.Constraint(DEMAND_LIST[j], DEMAND_LIST[j])
    for i in range(num_supply):
        constraint.SetCoefficient(x[i, j], 1)

# 6. Objective
objective = solver.Objective()
for i in range(num_supply):
    for j in range(num_demand):
        objective.SetCoefficient(x[i, j], COST_MATRIX[i][j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # Extract and verify assignments
    for i in range(num_supply):
        for j in range(num_demand):
            flow = x[i, j].solution_value()
            if flow > 1e-6:
                print(f'x[{i},{j}] = {flow}')
    print(f'Total cost: {total_cost}')
else:
    print('Solver did not find an optimal or feasible solution.')
```

### Common Pitfalls
- Extracting solution values without checking the solver status first, leading to errors.
- Not setting a time limit (`solver.SetTimeLimit`) for large problems, risking long runtimes.
- Using loose tolerances for validation, missing subtle constraint violations.

# Workflow 2 (Pyomo with CBC Solver)

## Modeling stage

### Strategy Overview
Formulate the problem using the Pyomo modeling language, creating an abstract `ConcreteModel`. This approach separates problem specification from solver interaction, improving clarity and reusability.

### Step 1 - Define Model Sets and Parameters
- Declare Pyomo `Set` objects for sources and sinks.
- Define `Param` objects for supply, demand, cost, and capacity, indexed over the appropriate sets.

### Step 2 - Declare Decision Variables
- Create a `Var` indexed over source-sink pairs, with domain `pyo.NonNegativeReals`.
- Optionally, set variable bounds using the `bounds` argument to enforce per-arc capacity.

### Step 3 - Construct Objective Rule
- Define a rule function that returns the linear cost expression: `sum(cost[i,j] * model.x[i,j] for i in sources for j in sinks)`.
- Attach it to the model as a minimization objective.

### Step 4 - Construct Constraint Rules
- Define a rule for supply balance: `sum(model.x[i,j] for j in sinks) == supply[i]`.
- Define a rule for demand balance: `sum(model.x[i,j] for i in sources) == demand[j]`.
- Define a rule for arc capacity: `model.x[i,j] <= capacity[i,j]`.

### Formulation Template
```json
{
  "sets": [
    "model.I: set of sources",
    "model.J: set of sinks"
  ],
  "parameters": [
    "model.supply[I]: amount available at each source",
    "model.demand[J]: amount required at each sink",
    "model.cost[I][J]: unit cost of flow from i to j",
    "model.cap[I][J]: maximum flow allowed from i to j"
  ],
  "decision_variables": [
    "model.x[I][J]: continuous, non-negative flow from source i to sink j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[i,j] * model.x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "supply_rule[i]: sum(model.x[i,j] for j in J) == model.supply[i]",
    "demand_rule[j]: sum(model.x[i,j] for i in I) == model.demand[j]",
    "capacity_rule[i,j]: model.x[i,j] <= model.cap[i,j]"
  ]
}
```

### Common Pitfalls
- Defining constraint rules with incorrect indexing, leading to missing or duplicate constraints.
- Using mutable Python data structures (like lists) directly within Pyomo rules; use `model.Param` instead.
- Not handling incomplete cost matrices, which can cause key errors; use a default high penalty cost for missing arcs.

## Solving stage

### Strategy Overview
Use the Pyomo `SolverFactory` to interface with the CBC solver. Configure solver options, solve the model, and perform comprehensive checks on the solver status and termination condition.

### Step 1 - Instantiate Solver
- Create a solver object: `solver = pyo.SolverFactory('cbc')`.
- Configure options, e.g., `solver.options['seconds'] = TIME_LIMIT`.

### Step 2 - Solve and Capture Results
- Execute `results = solver.solve(model, tee=False)`.
- The `results` object contains the solver status and termination condition.

### Step 3 - Validate Solver Outcome
- Check if the solver ran successfully: `assert results.solver.status == SolverStatus.ok`.
- Check the termination condition: `if results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:`.

### Step 4 - Extract and Verify Solution
- Access the objective value: `model.obj.expr()` or `pyo.value(model.obj)`.
- Iterate over the variable index to retrieve flows with `pyo.value(model.x[i,j])`.
- Programmatically verify all constraints are satisfied within a numerical tolerance.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()

# Define sets
model.I = pyo.Set(initialize=SOURCE_INDICES)  # placeholder
model.J = pyo.Set(initialize=SINK_INDICES)    # placeholder

# Define parameters
model.supply = pyo.Param(model.I, initialize=SUPPLY_DICT)  # placeholder
model.demand = pyo.Param(model.J, initialize=DEMAND_DICT)  # placeholder
model.cost = pyo.Param(model.I, model.J, initialize=COST_DICT)  # placeholder
model.cap = pyo.Param(model.I, model.J, initialize=CAP_DICT)    # placeholder

# Define variable
model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, m.cap[i,j]))

# Define objective
def obj_rule(m):
    return sum(m.cost[i,j] * m.x[i,j] for i in m.I for j in m.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Define constraints
def supply_rule(m, i):
    return sum(m.x[i,j] for j in m.J) == m.supply[i]
model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

def demand_rule(m, j):
    return sum(m.x[i,j] for i in m.I) == m.demand[j]
model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = SOLVER_TIME_LIMIT  # placeholder

results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if results.solver.status == SolverStatus.ok:
    if results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible):
        total_cost = pyo.value(model.obj)
        print(f'RESULT:{total_cost}')
        # Optional: Extract and verify variable values
        for i in model.I:
            for j in model.J:
                val = pyo.value(model.x[i,j])
                if val > 1e-6:
                    print(f'  x[{i},{j}] = {val}')
    else:
        print(f'{{"error": "Solver terminated with condition: {results.solver.termination_condition}"}}')
else:
    print('{"error": "Solver failed to run."}')
```

### Common Pitfalls
- Not importing `SolverStatus` and `TerminationCondition` before checking results.
- Setting solver options incorrectly (e.g., `solver.options['timeLimit']` instead of `solver.options['seconds']` for CBC).
- Failing to handle the case where the solver finds a feasible but non-optimal solution, leading to missed results.
