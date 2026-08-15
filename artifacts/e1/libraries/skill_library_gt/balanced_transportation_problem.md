---
name: Balanced Transportation Problem
description: |
  Model bipartite flow networks with supply-demand balance and linear costs, then solve with LP/MIP solvers using Pyomo or OR-Tools.
---

# Workflow 1 (Pyomo with LP/MIP Solver)

## Modeling stage

### Strategy Overview
Model the problem as a bipartite flow network using Pyomo's algebraic modeling capabilities. Define sets for origins and destinations, parameters for data, and non-negative continuous flow variables. Enforce exact flow conservation at supply and demand nodes using equality constraints.

### Step 1 - Define Sets and Parameters
- Create Pyomo `Set` objects for the origin indices (`I`) and destination indices (`J`).
- Create Pyomo `Param` objects to store `supply[i]`, `demand[j]`, and `cost[i,j]` data, initialized from input dictionaries or lists.

### Step 2 - Create Flow Variables
- Define a Pyomo `Var` object `x[i,j]` with domain `pyo.NonNegativeReals` to represent the flow from origin `i` to destination `j`.
- Optionally, add upper bounds via a `capacity` parameter within a constraint; do not embed bounds directly in the variable domain for clarity in the standard formulation.

### Step 3 - Formulate Supply and Demand Constraints
- For each origin `i`, add a `Constraint`: `sum(x[i,j] for j in J) == supply[i]`.
- For each destination `j`, add a `Constraint`: `sum(x[i,j] for i in I) == demand[j]`.

### Step 4 - Define Linear Cost Objective
- Create an `Objective` with expression `sum(cost[i,j] * x[i,j] for i in I for j in J)` and `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["I (origins)", "J (destinations)"],
  "parameters": ["supply[i]", "demand[j]", "cost[i,j]"],
  "decision_variables": ["x[i,j] (non-negative continuous flow)"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I, j in J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "sum_{j in J} x[i,j] = supply[i], for all i in I",
    "sum_{i in I} x[i,j] = demand[j], for all j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand before solving, which is necessary for feasibility of the equality constraints.
- Embedding arc capacity limits directly in variable bounds, which can obscure the model structure; instead, add explicit `x[i,j] <= capacity[i,j]` constraints.
- Using raw Python data structures inside Pyomo expressions, which breaks abstraction; always use Pyomo `Param` objects.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured LP or MIP solver (e.g., CBC, HiGHS, GLPK). Check solver status and termination condition rigorously, then extract and verify the solution.

### Step 1 - Configure and Execute Solver
- Instantiate a solver via `pyo.SolverFactory("solver_name")` (e.g., "cbc", "highs", "glpk").
- Set practical options: `seconds` for time limit, `ratio` for optimality gap tolerance (0.0 for LP), and `threads` for parallelism.
- Call `results = solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Verify `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value: `float(pyo.value(model.obj))`.
- Iterate over `model.x` to get non-zero flows (value > tolerance, e.g., 1e-6).
- Programmatically verify constraint satisfaction: recompute sums and compare to supply/demand values within tolerance.

### Step 4 - Handle Failures Gracefully
- If status is not ok or termination is not acceptable, output a structured JSON payload with solver status, termination condition, and error reason.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (example snippet)
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=origins)
model.J = pyo.Set(initialize=destinations)
model.supply = pyo.Param(model.I, initialize=supply_dict)
model.demand = pyo.Param(model.J, initialize=demand_dict)
model.cost = pyo.Param(model.I, model.J, initialize=cost_dict)
model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
model.obj = pyo.Objective(
    expr=sum(model.cost[i,j] * model.x[i,j] for i in model.I for j in model.J),
    sense=pyo.minimize
)
model.supply_con = pyo.Constraint(model.I, rule=lambda m, i: sum(m.x[i,j] for j in m.J) == m.supply[i])
model.demand_con = pyo.Constraint(model.J, rule=lambda m, j: sum(m.x[i,j] for i in m.I) == m.demand[j])

# Solve with status/termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_cost = float(pyo.value(model.obj))
    # Extract and verify solution...
else:
    # Output failure JSON...
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of suboptimal or failed solutions.
- Extracting variable values without verifying the solve was successful, causing runtime errors.
- Using inconsistent numerical tolerances when checking constraint satisfaction, leading to false infeasibility reports.

# Workflow 2 (OR-Tools LP Solver)

## Modeling stage

### Strategy Overview
Model the bipartite flow problem directly using the OR-Tools linear solver API. Create variables with explicit lower and upper bounds, add constraints via coefficient setting, and define a linear objective for minimization.

### Step 1 - Initialize Solver and Create Variables
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("GLOP")` for LP or `"CBC"` for MIP.
- For each origin `i` and destination `j`, create a variable `x[i,j] = solver.NumVar(0, capacity[i][j], name)` where `capacity[i][j]` can be `solver.infinity()` if unbounded.

### Step 2 - Add Supply Constraints
- For each origin `i`, create a constraint: `constraint = solver.Constraint(supply[i], supply[i])`.
- For each destination `j` connected to origin `i`, set coefficient: `constraint.SetCoefficient(x[i,j], 1)`.

### Step 3 - Add Demand Constraints
- For each destination `j`, create a constraint: `constraint = solver.Constraint(demand[j], demand[j])`.
- For each origin `i` connected to destination `j`, set coefficient: `constraint.SetCoefficient(x[i,j], 1)`.

### Step 4 - Set Linear Objective
- Create objective: `objective = solver.Objective()`.
- For each variable `x[i,j]`, set coefficient: `objective.SetCoefficient(x[i,j], cost[i][j])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["origins (index i)", "destinations (index j)"],
  "parameters": ["supply[i]", "demand[j]", "cost[i,j]", "capacity[i,j] (optional upper bound)"],
  "decision_variables": ["x[i,j] (continuous, bounded [0, capacity[i,j]])"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i,j} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "sum_{j} x[i,j] = supply[i], for all i",
    "sum_{i} x[i,j] = demand[j], for all j"
  ]
}
```

### Common Pitfalls
- Using `solver.infinity()` for unbounded variables when realistic capacity limits exist, which can hide model errors.
- Incorrectly ordering constraint coefficient assignment, leading to constraint mismatch.
- Not verifying that the solver was successfully created (`if solver is None:`).

## Solving stage

### Strategy Overview
Solve the built OR-Tools model, check the status, extract the objective value and variable solutions, and perform post-solution validation.

### Step 1 - Solve and Check Status
- Execute `status = solver.Solve()`.
- Verify `status` is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`.

### Step 2 - Extract Objective and Variable Values
- Retrieve total cost: `total_cost = objective.Value()`.
- For each variable `x[i,j]`, get flow value: `val = x[i,j].solution_value()`.

### Step 3 - Verify Solution Feasibility
- Recompute total outflow for each origin and compare to `supply[i]` within tolerance (e.g., 1e-6).
- Recompute total inflow for each destination and compare to `demand[j]`.
- Check that each flow respects its upper bound `capacity[i][j]`.

### Step 4 - Output Results
- Print or return the total cost and a list of non-zero flows (value > tolerance).
- For failed solves, provide the solver status and any available infeasibility information.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
x = {}
for i in range(num_origins):
    for j in range(num_destinations):
        ub = capacity[i][j] if capacity else solver.infinity()
        x[i, j] = solver.NumVar(0, ub, f'x_{i}_{j}')

# Supply constraints
for i in range(num_origins):
    constraint = solver.Constraint(supply[i], supply[i])
    for j in range(num_destinations):
        constraint.SetCoefficient(x[i, j], 1)

# Demand constraints
for j in range(num_destinations):
    constraint = solver.Constraint(demand[j], demand[j])
    for i in range(num_origins):
        constraint.SetCoefficient(x[i, j], 1)

# Objective
objective = solver.Objective()
for i in range(num_origins):
    for j in range(num_destinations):
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# Solve with status / termination checks
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    total_cost = objective.Value()
    # Extract and verify solution...
else:
    # Handle failure...
```

### Common Pitfalls
- Confusing `solver.Solve()` return status with the solver's internal state; always use the defined constants (`OPTIMAL`, `FEASIBLE`).
- Not handling the case where `solver` creation fails (returns `None`).
- Omitting post-solution verification, assuming the solver's feasibility report is numerically exact.
