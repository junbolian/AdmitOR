---
name: Capacitated Transportation Problem Solver
description: |
  Model and solve capacitated transportation problems with supply-demand balance and arc capacity constraints using linear programming.
---

# Workflow 1 (Pyomo with Highs/CBC Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model definition, separating problem logic from solver specifics. It is well-suited for structured, maintainable code and leverages open-source solvers like Highs or CBC for linear problems.

### Step 1 - Define Sets and Parameters
- Define index sets for `origins` and `destinations` to structure the model.
- Create parameter dictionaries for `supply`, `demand`, `cost`, and `capacity`, indexed appropriately.

### Step 2 - Create Decision Variables
- Define a continuous, non-negative decision variable `flow_amount` indexed by `(origin, destination)`.
- Optionally, set variable upper bounds directly using the `capacity` parameter.

### Step 3 - Formulate Supply and Demand Balance Constraints
- For each `origin`, add a constraint that the sum of outgoing flows equals its `supply`.
- For each `destination`, add a constraint that the sum of incoming flows equals its `demand`.

### Step 4 - Apply Arc Capacity Constraints
- For each `(origin, destination)` pair, add a constraint that `flow_amount` is less than or equal to the `capacity`. (This may be redundant if variable bounds are used).

### Step 5 - Define Linear Cost Objective
- Formulate the objective to minimize the total cost: sum of `flow_amount[i,j] * cost[i,j]` over all arcs.

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
    {"name": "flow_amount", "index": ["origins", "destinations"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * flow_amount[i,j] for i in origins for j in destinations)"
  },
  "constraints": [
    {"name": "supply_balance", "index": "origins", "expression": "sum(flow_amount[i,j] for j in destinations) == supply[i]"},
    {"name": "demand_balance", "index": "destinations", "expression": "sum(flow_amount[i,j] for i in origins) == demand[j]"},
    {"name": "arc_capacity", "index": ["origins", "destinations"], "expression": "flow_amount[i,j] <= capacity[i,j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to define all required index sets before using them in parameters or variables.
- Using equality constraints for supply/demand when the problem might have slack; ensure the problem is balanced or use inequalities.
- Not verifying that capacity values are non-negative.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver factory, focusing on robust status checking and post-solution validation to ensure correctness and feasibility.

### Step 1 - Instantiate Solver with Options
- Create a solver object using `SolverFactory('solver_name')` (e.g., `'highs'` or `'cbc'`).
- Set solver options such as `time_limit` and `threads` for performance control.

### Step 2 - Solve and Check Status
- Execute the `solve` method on the model instance.
- Check both `solver.status` and `solver.termination_condition` to confirm optimal or acceptable feasible solution.

### Step 3 - Extract and Validate Solution
- Retrieve variable values using a small tolerance (e.g., `1e-6`) to filter near-zero flows.
- Recompute total flows from each origin and to each destination to verify supply/demand balance constraints.
- Check each active flow against its capacity limit.

### Step 4 - Output Structured Results
- Output the objective value and a summary of non-zero flows.
- For failures, output a clear status message and reason.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (build model using sets, variables, constraints, objective as per steps)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['time_limit'] = 30
results = solver.solve(model)

# Check solution status
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    # Extract and validate solution
    for i in model.origins:
        for j in model.destinations:
            flow_val = pyo.value(model.flow_amount[i, j])
            if flow_val > 1e-6:
                # Check capacity
                assert flow_val <= model.capacity[i, j] + 1e-6
    print(f"Optimal cost: {pyo.value(model.objective)}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or infeasible results.
- Extracting variable values without checking if a solution exists.
- Using loose tolerances for feasibility checks, which may mask constraint violations.

# Workflow 2 (Ortools Linear Solver Wrapper)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools linear solver wrapper (e.g., `GLOP`, `CBC_MIXED_INTEGER_PROGRAMMING`) for a more direct, imperative modeling style. It is efficient for prototyping and leverages solver-specific features like variable bounds.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver('GLOP')`).
- Store problem data (`supply`, `demand`, `cost`, `capacity`) in nested dictionaries or lists for fast access.

### Step 2 - Create Variables with Bounds
- Create a continuous variable for each `(origin, destination)` pair using `solver.NumVar`.
- Set the variable lower bound to 0 and upper bound directly to the `capacity` value.

### Step 3 - Add Supply and Demand Constraints
- For each `origin`, create a linear constraint where the sum of outgoing flow variables equals `supply[origin]`.
- For each `destination`, create a linear constraint where the sum of incoming flow variables equals `demand[destination]`.

### Step 4 - Set Linear Minimization Objective
- Create the objective expression by summing `flow_amount[i][j] * cost[i][j]` for all arcs.
- Call `solver.Minimize()` with the expression.

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
    {"name": "flow_amount", "index": ["origins", "destinations"], "domain": "continuous", "lower_bound": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * flow_amount[i][j])"
  },
  "constraints": [
    {"name": "supply_balance", "index": "origins", "expression": "sum(flow_amount[i][j] for j in destinations) == supply[i]"},
    {"name": "demand_balance", "index": "destinations", "expression": "sum(flow_amount[i][j] for i in origins) == demand[j]"}
  ]
}
```
*Note: Arc capacity is enforced via variable upper bounds in this imperative style.*

### Common Pitfalls
- Creating variables without setting upper bounds, effectively ignoring capacity constraints.
- Adding redundant capacity constraints when variable bounds already enforce them.
- Using integer solver types (e.g., `CBC_MIXED_INTEGER_PROGRAMMING`) for continuous problems, which is less efficient.

## Solving stage

### Strategy Overview
Solve using the OR-Tools solver's native methods, with explicit time limits and direct solution value retrieval. Emphasize efficient model building and straightforward result parsing.

### Step 1 - Configure Solver and Solve
- Set a time limit on the solver instance using `solver.SetTimeLimit()`.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Interpret Solver Result
- Check the result status (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).
- For optimal/feasible status, proceed to solution extraction.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value via `solver.Objective().Value()`.
- Iterate over all variables, extract their solution values, and verify they satisfy supply/demand balances and capacity bounds within tolerance.

### Step 4 - Output Results
- Print the optimal cost and a matrix of significant flows.
- For non-optimal results, provide the solver status and any available information.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (create variables, add constraints, set objective as per steps)

# solve with status / termination checks
solver.SetTimeLimit(30000)  # milliseconds
result_status = solver.Solve()

if result_status == pywraplp.Solver.OPTIMAL:
    # Verification loop
    total_cost = 0
    for i in origins:
        shipped = 0
        for j in destinations:
            flow_val = flow_amount[i][j].solution_value()
            if flow_val > 1e-6:
                shipped += flow_val
                total_cost += flow_val * cost[i][j]
                # Check capacity bound
                assert flow_val <= capacity[i][j] + 1e-6
        # Check supply balance
        assert abs(shipped - supply[i]) < 1e-6
    print(f"Optimal cost: {solver.Objective().Value()}")
    print(f"Independent cost calc: {total_cost}")
else:
    print(f"Solver did not find optimal solution. Status: {result_status}")
```

### Common Pitfalls
- Not setting a time limit, risking long runtimes for large or difficult instances.
- Assuming `FEASIBLE` status implies optimality; always check for `OPTIMAL` if the exact solution is required.
- Forgetting to convert time limits to the correct unit (milliseconds for OR-Tools).
