---
name: Fixed-Charge Production Planning
description: |
  Model and solve production planning with fixed activation costs and variable production costs using binary-continuous linking constraints and MILP solvers.
---

# Workflow 1 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Model the problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract modeling capabilities. The formulation uses binary variables for activation decisions and continuous variables for production quantities, linked via direct multiplication constraints to enforce capacity bounds and zero production when inactive.

### Step 1 - Define Sets and Indexed Parameters
- Define a set `F` for production entities (e.g., factories) and a set `T` for time periods (e.g., months).
- Store all problem data as dictionaries indexed by these sets: `fixed_cost[f]`, `variable_cost[f]`, `min_production[f]`, `max_production[f]`, and `demand[t]`.

### Step 2 - Create Binary and Continuous Variables
- Create binary variables `run[f,t] ∈ {0,1}` to represent the activation decision for each entity-period pair.
- Create continuous, non-negative variables `production[f,t] ≥ 0` to represent the production quantity.

### Step 3 - Link Activation to Production with Logical Constraints
- Enforce minimum production if active: `production[f,t] >= min_production[f] * run[f,t]`.
- Enforce maximum production if active: `production[f,t] <= max_production[f] * run[f,t]`. This also forces production to zero when inactive.

### Step 4 - Impose Aggregate Demand Satisfaction
- For each time period `t`, ensure total production meets demand: `sum(production[f,t] for f in F) >= demand[t]`.

### Step 5 - Formulate Linear Cost Objective
- Minimize total cost: `sum(fixed_cost[f] * run[f,t] + variable_cost[f] * production[f,t] for f in F, t in T)`.

### Formulation Template
```json
{
  "sets": ["F", "T"],
  "parameters": [
    "fixed_cost[F]",
    "variable_cost[F]",
    "min_production[F]",
    "max_production[F]",
    "demand[T]"
  ],
  "decision_variables": [
    "run[F,T] ∈ {0,1}",
    "production[F,T] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[f] * run[f,t] + variable_cost[f] * production[f,t] for f in F, t in T)"
  },
  "constraints": [
    "production[f,t] >= min_production[f] * run[f,t] for f in F, t in T",
    "production[f,t] <= max_production[f] * run[f,t] for f in F, t in T",
    "sum(production[f,t] for f in F) >= demand[t] for t in T"
  ]
}
```

### Common Pitfalls
- Using reserved keywords like `activate` as variable names in Pyomo, which can conflict with internal attributes.
- Adding redundant constraints (e.g., separate `production_zero_if_inactive`) when the maximum production linking constraint already enforces it.
- Storing data in local variables not accessible within Pyomo constraint rule functions, causing scope errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source MILP solver (CBC or HiGHS) with appropriate configuration for time limit, optimality gap, and parallel processing. Implement robust status checking and solution verification.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory("cbc")` or `solver = pyo.SolverFactory("highs")`.
- Set key options: `solver.options["seconds"] = <time_limit>`, `solver.options["ratio"] = 0.0` (for exact optimality), `solver.options["threads"] = <num_threads>`.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Check solver status: `status = results.solver.status`.
- Check termination condition: `term = results.solver.termination_condition`.
- Proceed only if `status == SolverStatus.ok` and `term in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value: `total_cost = pyo.value(model.obj)`.
- Extract variable values using `pyo.value()`; for binary variables, use a threshold (e.g., `> 0.5`) to determine activation status.
- Programmatically verify constraint satisfaction: check demand met, production bounds for active entities, and zero production for inactive entities.

### Step 4 - Analyze and Output Results
- Compute cost breakdowns: fixed cost total from `run` variables and variable cost total from `production` variables.
- Output results in a standardized format (e.g., `RESULT:{total_cost}`) or a structured JSON payload for failures.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (following modeling steps)
model = pyo.ConcreteModel()
model.F = pyo.Set(initialize=entities)
model.T = pyo.Set(initialize=periods)
model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
model.production = pyo.Var(model.F, model.T, domain=pyo.NonNegativeReals)
# ... add objective and constraints

# Solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = pyo.value(model.obj)
    # Extract and verify solution
else:
    # Handle failure, output error details
```

### Common Pitfalls
- Not checking both solver status and termination condition before extracting results, leading to runtime errors.
- Setting thread counts that conflict with the solver's global scheduler, causing performance issues.
- Performing redundant post-solution manual analysis (e.g., break-even calculations) that the optimization model already encapsulates.

# Workflow 2 (OR-Tools with SCIP/CBC Backend)

## Modeling stage

### Strategy Overview
Formulate the problem directly using the OR-Tools linear solver wrapper (`pywraplp`). This imperative API requires explicit variable and constraint creation via loops, suitable for prototyping and deployment in environments favoring direct solver control.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")` or `"CBC_MIXED_INTEGER_PROGRAMMING"`.
- Store parameters in dictionaries or lists indexed by entity and time period.

### Step 2 - Create Indexed Decision Variables
- Use nested loops over entities `i` and time periods `t` to create binary activation variables: `activate[i,t] = solver.IntVar(0, 1, "")`.
- Create continuous production variables with an upper bound of `max_production[i]`: `production[i,t] = solver.NumVar(0, max_production[i], "")`.

### Step 3 - Add Linking Constraints via Direct Multiplication
- For each `(i,t)` pair, add constraint: `production[i,t] >= min_production[i] * activate[i,t]`.
- Add constraint: `production[i,t] <= max_production[i] * activate[i,t]`.

### Step 4 - Impose Period-Wise Demand Constraints
- For each time period `t`, create a constraint: `solver.Add(sum(production[i,t] for i in entities) >= demand[t])`.

### Step 5 - Build Linear Objective Function
- Create an objective: `objective = solver.Objective()`.
- In loops over `(i,t)`, set coefficients: `objective.SetCoefficient(activate[i,t], fixed_cost[i])` and `objective.SetCoefficient(production[i,t], variable_cost[i])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["entities", "time_periods"],
  "parameters": [
    "fixed_cost[entities]",
    "variable_cost[entities]",
    "min_production[entities]",
    "max_production[entities]",
    "demand[time_periods]"
  ],
  "decision_variables": [
    "activate[entities,time_periods] ∈ {0,1}",
    "production[entities,time_periods] ∈ [0, max_production[entities]]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * activate[i,t] + variable_cost[i] * production[i,t] for i in entities, t in time_periods)"
  },
  "constraints": [
    "production[i,t] >= min_production[i] * activate[i,t] for i in entities, t in time_periods",
    "production[i,t] <= max_production[i] * activate[i,t] for i in entities, t in time_periods",
    "sum(production[i,t] for i in entities) >= demand[t] for t in time_periods"
  ]
}
```

### Common Pitfalls
- Using arbitrary large Big-M constants when entity-specific maximum production provides a natural, tighter bound.
- Creating variables with inconsistent indexing, making constraint assembly error-prone.
- Forgetting to set the objective sense to minimization.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' solver interface, configure performance parameters (time limit, threads), and implement solution extraction with verification against constraints.

### Step 1 - Configure Solver Performance
- Set a time limit: `solver.SetTimeLimit(<time_limit_milliseconds>)`.
- Enable parallel processing: `solver.SetNumThreads(<num_threads>)`.

### Step 2 - Invoke Solve and Check Status
- Call `status = solver.Solve()`.
- Accept solutions where `status` is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`.

### Step 3 - Extract Solution and Verify Feasibility
- Retrieve the objective value: `total_cost = objective.Value()`.
- Access variable values via `.solution_value()`.
- Verify constraints programmatically: check demand satisfaction per period, production bounds for active entities, and zero production for inactive entities (within a small tolerance).

### Step 4 - Output Results and Cost Breakdown
- Compute separate fixed and variable cost totals from the solution values.
- Output the production schedule and activation pattern for validation.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
activate = {}
production = {}
for i in entities:
    for t in periods:
        activate[i,t] = solver.IntVar(0, 1, f"activate_{i}_{t}")
        production[i,t] = solver.NumVar(0, max_production[i], f"production_{i}_{t}")
        # Add linking constraints
        solver.Add(production[i,t] >= min_production[i] * activate[i,t])
        solver.Add(production[i,t] <= max_production[i] * activate[i,t])
for t in periods:
    solver.Add(sum(production[i,t] for i in entities) >= demand[t])
objective = solver.Objective()
for i in entities:
    for t in periods:
        objective.SetCoefficient(activate[i,t], fixed_cost[i])
        objective.SetCoefficient(production[i,t], variable_cost[i])
objective.SetMinimization()

# Solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # Extract and verify solution
else:
    # Handle failure
```

### Common Pitfalls
- Not setting a time limit, leading to excessively long runs for large instances.
- Misinterpreting near-zero production values (e.g., 1e-14) as activation; use a tolerance threshold for binary variables.
- Running redundant verification solves after obtaining an optimal solution, wasting computational resources.
