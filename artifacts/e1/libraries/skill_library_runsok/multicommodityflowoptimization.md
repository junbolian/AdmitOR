---
name: MultiCommodityFlowOptimization
description: |
  Model and solve multi-commodity flow problems with shared arc capacities using linear programming, focusing on cost minimization and robust solution validation.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a multi-commodity flow problem, separating model logic from data. It is well-suited for maintainable, equation-based modeling and integrates with open-source solvers like HiGHS and CBC.

### Step 1 - Define Sets and Data Structures
- Declare three fundamental sets: origins, destinations, and products.
- Organize parameters (supply, demand, cost, capacity) as dictionaries keyed by tuples (e.g., `(origin, product)`, `(origin, destination, product)`).
- Use Pyomo's `Set` and `Param` components for clean integration with constraint rules.

### Step 2 - Create Flow Variables
- Define a three-dimensional, continuous, non-negative variable `x[i, j, p]` representing the flow of product `p` from origin `i` to destination `j`.
- Use `pyo.Var(model.I, model.J, model.P, domain=pyo.NonNegativeReals)`.

### Step 3 - Formulate Supply and Demand Constraints
- For each origin `i` and product `p`, enforce `sum_{j} x[i, j, p] == supply[i, p]` (exact supply consumption).
- For each destination `j` and product `p`, enforce `sum_{i} x[i, j, p] == demand[j, p]` (exact demand satisfaction).
- Implement as Pyomo `Constraint` objects using rule functions.

### Step 4 - Implement Bundle Capacity Constraints
- For each origin-destination pair `(i, j)`, enforce `sum_{p} x[i, j, p] <= capacity[i, j]`.
- This aggregates all commodity flows on a shared arc.

### Step 5 - Define Linear Cost Objective
- Formulate the objective as `minimize sum_{i, j, p} cost[i, j, p] * x[i, j, p]`.
- Use `pyo.Objective(rule=obj_rule, sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations", "products"],
  "parameters": [
    {"name": "supply", "index": ["origin", "product"]},
    {"name": "demand", "index": ["destination", "product"]},
    {"name": "cost", "index": ["origin", "destination", "product"]},
    {"name": "capacity", "index": ["origin", "destination"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["origin", "destination", "product"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in origins, j in destinations, p in products} cost[i,j,p] * x[i,j,p]"
  },
  "constraints": [
    {"name": "supply", "expression": "sum_{j in destinations} x[i,j,p] == supply[i,p]", "for_all": ["i in origins", "p in products"]},
    {"name": "demand", "expression": "sum_{i in origins} x[i,j,p] == demand[j,p]", "for_all": ["j in destinations", "p in products"]},
    {"name": "capacity", "expression": "sum_{p in products} x[i,j,p] <= capacity[i,j]", "for_all": ["i in origins", "j in destinations"]}
  ]
}
```

### Common Pitfalls
- Using inconsistent indexing between parameters and variables, leading to KeyErrors.
- Forgetting to check total supply equals total demand, which can cause infeasibility with equality constraints.
- Defining constraint rules with side effects or incorrect scope, causing model building errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver via the `SolverFactory` interface. Focus on robust status checking, solution validation, and structured error handling.

### Step 1 - Instantiate Solver and Configure Options
- Create a solver instance: `solver = SolverFactory('highs')` (or `'cbc'`).
- Set practical options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`. Use `tee=True` for debugging output.

### Step 2 - Solve and Check Status
- Execute `results = solver.solve(model, tee=False)`.
- Check both high-level status and termination condition:
  - `if results.solver.status == SolverStatus.ok and results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:`

### Step 3 - Extract and Validate Solution
- Extract the objective value: `objective_value = float(pyo.value(model.obj))`.
- Programmatically verify all constraints by recomputing flows and comparing to original parameters with a tolerance (e.g., `1e-6`).
- Filter and report non-zero flows (`value > 1e-6`) for clarity.

### Step 4 - Handle Failures Gracefully
- For infeasible or unbounded problems, output a structured JSON error message containing the solver status and termination condition.
- Avoid accessing solution values before confirming a feasible status.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# Build model (model defined previously)
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective

# Solve
solver = SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

# Status / termination checks
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
    objective_value = float(pyo.value(model.obj))
    print(f"RESULT:{objective_value}")
    # Extract and validate flows
    for i in model.I:
        for j in model.J:
            for p in model.P:
                val = pyo.value(model.x[i, j, p])
                if val > 1e-6:
                    print(f"x[{i},{j},{p}] = {val}")
else:
    # Handle failure
    error_info = {
        "status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
    print(f"ERROR:{error_info}")
```

### Common Pitfalls
- Setting solver options (like `threads`) that conflict with the solver's internal initialization, causing crashes.
- Assuming `SolverStatus.ok` alone guarantees a feasible solution; always check the termination condition.
- Not using a tolerance when checking constraint satisfaction post-solve, leading to false failures due to numerical precision.

# Workflow 2 (OR-Tools LP with GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools LP API for a procedural, direct construction of the multi-commodity flow model. It is ideal for embedding in scripts or applications requiring fine-grained control over variable and constraint creation.

### Step 1 - Initialize Solver and Data Structures
- Create a linear solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Define data as nested lists or dictionaries: `supply[origin][product]`, `demand[destination][product]`, `cost[origin][destination][product]`, `capacity[origin][destination]`.

### Step 2 - Create Flow Variables with Bounds
- Use nested loops over origins, destinations, and products to create variables: `x[i][j][p] = solver.NumVar(0, solver.infinity(), f'x_{i}_{j}_{p}')`.
- Store variables in a dictionary with tuple keys `(i, j, p)` for efficient access.

### Step 3 - Build Supply and Demand Constraints as Equalities
- For each origin `i` and product `p`, create an equality constraint with right-hand side `supply[i][p]`.
- Add coefficients of `1` for all variables `x[i][j][p]` across destinations `j`.
- Repeat symmetrically for demand constraints per destination `j` and product `p`.

### Step 4 - Build Bundle Capacity Constraints as Inequalities
- For each origin-destination pair `(i, j)`, create a `<= capacity[i][j]` constraint.
- Sum coefficients of `1` for all variables `x[i][j][p]` across products `p`.

### Step 5 - Set Linear Cost Objective
- Initialize the objective: `objective = solver.Objective()`.
- Iterate over all variable indices and set coefficients using `objective.SetCoefficient(x[i][j][p], cost[i][j][p])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations", "products"],
  "parameters": [
    {"name": "supply", "index": ["origin", "product"], "type": "float"},
    {"name": "demand", "index": ["destination", "product"], "type": "float"},
    {"name": "cost", "index": ["origin", "destination", "product"], "type": "float"},
    {"name": "capacity", "index": ["origin", "destination"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["origin", "destination", "product"], "domain": [0, INF]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i,j,p} cost[i][j][p] * x[i][j][p]"
  },
  "constraints": [
    {"name": "supply", "expression": "sum_j x[i][j][p] = supply[i][p]", "for_all": ["i", "p"], "type": "equality"},
    {"name": "demand", "expression": "sum_i x[i][j][p] = demand[j][p]", "for_all": ["j", "p"], "type": "equality"},
    {"name": "capacity", "expression": "sum_p x[i][j][p] <= capacity[i][j]", "for_all": ["i", "j"], "type": "inequality"}
  ]
}
```

### Common Pitfalls
- Creating constraints inside incorrect loop nests, leading to missing or duplicate constraints.
- Using `solver.infinity()` for variable upper bounds when finite capacities exist, which is acceptable but can obscure model structure.
- Not verifying that the sum of supply equals the sum of demand, causing infeasibility with strict equality constraints.

## Solving stage

### Strategy Overview
Solve the model using GLOP, a pure linear programming solver. Emphasize systematic solution verification and extraction of non-zero flows, with clear handling of solver status codes.

### Step 1 - Invoke Solver and Check Status
- Execute `status = solver.Solve()`.
- Check for successful status: `if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):`.

### Step 2 - Extract Objective and Variable Values
- Retrieve the objective value: `objective_value = solver.Objective().Value()`.
- Iterate over all variable indices and use `.solution_value()` to get flow values.
- Apply a threshold (e.g., `1e-6`) to filter and report only non-zero flows.

### Step 3 - Programmatically Verify Solution
- Recompute total outflow per origin-product and compare to supply.
- Recompute total inflow per destination-product and compare to demand.
- Recompute total flow per arc and compare to capacity.
- Use a tolerance (e.g., `1e-6`) for comparisons to account for numerical precision.

### Step 4 - Implement Error Handling
- For non-optimal/feasible statuses (e.g., INFEASIBLE, UNBOUNDED), output a structured message containing the solver status code.
- Avoid attempting to extract variable values on failed solves.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... define data arrays: supply, demand, cost, capacity
x = {}
for i in origins:
    for j in destinations:
        for p in products:
            x[(i, j, p)] = solver.NumVar(0, solver.infinity(), f'x_{i}_{j}_{p}')

# Add constraints
for i in origins:
    for p in products:
        constraint = solver.Constraint(supply[i][p], supply[i][p])
        for j in destinations:
            constraint.SetCoefficient(x[(i, j, p)], 1)
# ... similarly for demand and capacity constraints

# Set objective
objective = solver.Objective()
for i in origins:
    for j in destinations:
        for p in products:
            objective.SetCoefficient(x[(i, j, p)], cost[i][j][p])
objective.SetMinimization()

# Solve with status / termination checks
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    objective_value = objective.Value()
    print(f"RESULT:{objective_value}")
    # Verify and extract non-zero flows
    for (i, j, p), var in x.items():
        val = var.solution_value()
        if val > 1e-6:
            print(f"x[{i},{j},{p}] = {val}")
    # Optional: call a verification function
else:
    print(f"ERROR:Solver failed with status: {status}")
```

### Common Pitfalls
- Confusing `solver.Solve()` return status codes with `solver.OPTIMAL`/`solver.FEASIBLE` constants.
- Not using a tolerance when filtering non-zero flows, resulting in excessive output from near-zero values.
- Forgetting to set the objective sense (`SetMinimization`), defaulting to minimization but best practice is explicit.
