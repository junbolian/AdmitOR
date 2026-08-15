---
name: Facility Activation Scheduling
description: |
  Model and solve production scheduling problems with fixed activation costs, minimum/maximum production levels, and time-varying demand using MILP with binary-continuous variable linking.

---

# Workflow 1 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to build a concrete MILP model, linking binary activation variables to continuous production quantities via direct multiplication constraints. It is designed for use with open-source solvers like CBC or HiGHS, emphasizing clear set and parameter definitions.

### Step 1 - Define Sets and Parameters
- Define a set `F` for entities (e.g., factories) and a set `M` for time periods (e.g., months).
- Store all cost and capacity parameters as dictionaries indexed by the entity set: `fixed_cost[f]`, `variable_cost[f]`, `min_production[f]`, `max_production[f]`.
- Store demand as a dictionary indexed by the time period set: `demand[m]`.

### Step 2 - Create Decision Variables
- Create binary variables `run[f, m] ∈ {0,1}` to represent the activation decision for each entity and period.
- Create continuous, non-negative variables `production[f, m] ≥ 0` to represent the production quantity.

### Step 3 - Formulate Linking Constraints
- Implement the **minimum production if active** constraint: `production[f, m] >= min_production[f] * run[f, m]`.
- Implement the **maximum production if active** constraint: `production[f, m] <= max_production[f] * run[f, m]`. This also forces production to zero when inactive.

### Step 4 - Add Demand and Objective
- For each time period `m`, add a demand satisfaction constraint: `sum(production[f, m] for f in F) >= demand[m]`.
- Formulate the objective to minimize total cost: `sum(fixed_cost[f] * run[f, m] + variable_cost[f] * production[f, m] for f in F, m in M)`.

### Formulation Template
```json
{
  "sets": ["F", "M"],
  "parameters": {
    "fixed_cost": {"index": "F"},
    "variable_cost": {"index": "F"},
    "min_production": {"index": "F"},
    "max_production": {"index": "F"},
    "demand": {"index": "M"}
  },
  "decision_variables": [
    {"name": "run", "type": "binary", "index": ["F", "M"]},
    {"name": "production", "type": "continuous", "index": ["F", "M"], "bounds": [0, null]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[f] * run[f,m] + variable_cost[f] * production[f,m] for f in F, m in M)"
  },
  "constraints": [
    {"name": "min_prod", "expression": "production[f,m] >= min_production[f] * run[f,m]", "index": ["F", "M"]},
    {"name": "max_prod", "expression": "production[f,m] <= max_production[f] * run[f,m]", "index": ["F", "M"]},
    {"name": "demand_sat", "expression": "sum(production[f,m] for f in F) >= demand[m]", "index": ["M"]}
  ]
}
```

### Common Pitfalls
- Using Pyomo reserved keywords (e.g., `activate`) for variable names, which causes attribute conflicts. Use generic names like `run` or `y`.
- Forgetting to attach parameter dictionaries to the model instance, leading to scope errors in constraint rule functions.
- Creating redundant `production_zero_if_inactive` constraints; the maximum production linking constraint already enforces this.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source MILP solver (CBC or HiGHS), configuring key performance options. Implement robust status checking and post-solution verification to ensure correctness.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = SolverFactory("cbc")` or `SolverFactory("highs")`.
- Set practical options: `solver.options["seconds"] = 30` for a time limit, `solver.options["ratio"] = 0.0` for optimality gap, and `solver.options["threads"] = 4` for parallelism.
- Solve the model with `results = solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status
- Verify `results.solver.status == SolverStatus.ok`.
- Check that `results.solver.termination_condition` is either `TerminationCondition.optimal` or `TerminationCondition.feasible`. Proceed only if true.

### Step 3 - Extract and Verify Solution
- Extract the objective value: `total_cost = pyo.value(model.obj)`.
- Iterate over `run[f,m]` variables, interpreting values `> 0.5` as active (1).
- Retrieve corresponding `production[f,m]` values.
- Perform post-solution verification: confirm demand satisfaction, production bounds for active entities, and zero production for inactive ones.

### Step 4 - Output Results
- Provide a structured output, such as a JSON payload, containing the total cost, activation schedule, production plan, and solver status.
- For failed solves, output error details including the termination condition.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build model (model) using the formulation steps above.
# 2. Solve
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model)

# 3. Check status and extract solution
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = pyo.value(model.obj)
    # Extract variable values and verify constraints
    schedule = {}
    for f in model.F:
        for m in model.M:
            if pyo.value(model.run[f, m]) > 0.5:
                schedule[(f, m)] = pyo.value(model.production[f, m])
    # Output results
else:
    # Handle failure: output results.solver.termination_condition
```

### Common Pitfalls
- Not checking both solver status and termination condition before extracting variable values, which can lead to errors on infeasible or error solves.
- Setting invalid solver options (e.g., incorrect parameter names for HiGHS) causing the solve to fail; use defaults if uncertain.
- Manually re-calculating the objective or verifying all constraint combinations after solving, which is redundant if the solver's optimality/feasibility status is trusted.

# Workflow 2 (OR-Tools with SCIP/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools (`pywraplp`) to construct a MILP model with explicit variable and constraint creation via loops. It is suited for solvers like SCIP or the built-in CBC, focusing on procedural model building and lower-level control.

### Step 1 - Initialize Solver and Data Structures
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Define lists or dictionaries for parameters: `fixed_cost[i]`, `variable_cost[i]`, `min_production[i]`, `max_production[i]`, `demand[t]`.

### Step 2 - Create Indexed Variables
- Use nested loops over entities `i` and time periods `t`.
- Create binary variables: `activate[i,t] = solver.IntVar(0, 1, f"activate_{i}_{t}")`.
- Create continuous variables with an upper bound: `production[i,t] = solver.NumVar(0, max_production[i], f"production_{i}_{t}")`.

### Step 3 - Add Linking Constraints via Loops
- In the same nested loops, add constraints:
    - `solver.Add(production[i,t] >= min_production[i] * activate[i,t])`
    - `solver.Add(production[i,t] <= max_production[i] * activate[i,t])`

### Step 4 - Add Aggregate Demand Constraints and Objective
- For each time period `t`, add: `solver.Add(sum(production[i,t] for i in entities) >= demand[t])`.
- Create the objective: `objective = solver.Objective()`.
- In nested loops, set coefficients: `objective.SetCoefficient(activate[i,t], fixed_cost[i])` and `objective.SetCoefficient(production[i,t], variable_cost[i])`.
- Set minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["entities", "periods"],
  "parameters": {
    "fixed_cost": {"index": "entities"},
    "variable_cost": {"index": "entities"},
    "min_production": {"index": "entities"},
    "max_production": {"index": "entities"},
    "demand": {"index": "periods"}
  },
  "decision_variables": [
    {"name": "activate", "type": "binary", "index": ["entities", "periods"]},
    {"name": "production", "type": "continuous", "index": ["entities", "periods"], "bounds": [0, "max_production[i]"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * activate[i,t] + variable_cost[i] * production[i,t] for i in entities, t in periods)"
  },
  "constraints": [
    {"name": "min_prod", "expression": "production[i,t] >= min_production[i] * activate[i,t]", "index": ["entities", "periods"]},
    {"name": "max_prod", "expression": "production[i,t] <= max_production[i] * activate[i,t]", "index": ["entities", "periods"]},
    {"name": "demand_sat", "expression": "sum(production[i,t] for i in entities) >= demand[t]", "index": ["periods"]}
  ]
}
```

### Common Pitfalls
- Using `solver.NumVar` without an upper bound, which can weaken the LP relaxation; use `max_production[i]` as the natural upper bound.
- Building the objective by manually summing terms instead of using `SetCoefficient`, which is error-prone and less efficient.
- Not using descriptive variable names, making debugging difficult in larger models.

## Solving stage

### Strategy Overview
Solve the OR-Tools model, set performance parameters like time limits and threads, and implement verification by checking solution values against the original constraints.

### Step 1 - Set Solver Parameters and Solve
- Set a time limit: `solver.SetTimeLimit(30000)` (in milliseconds).
- Set the number of threads: `solver.SetNumThreads(4)`.
- Call `solver.Solve()` and check the result status.

### Step 2 - Validate Solution Status
- Check `solver.ResultStatus()` for `OPTIMAL` or `FEASIBLE`. If not, handle as a failure.

### Step 3 - Extract and Verify Solution Values
- Iterate over all variables, using `.solution_value()` to get activation and production quantities.
- For binary variables, apply a tolerance (e.g., `> 0.5`) to determine the active state.
- Compute total production per period and verify it meets demand.
- Verify that for active entities, production is between `min_production` and `max_production`, and for inactive entities, production is zero.

### Step 4 - Analyze and Report
- Compute cost breakdowns: total fixed cost and total variable cost.
- Output a summary including the objective value, activation schedule, and verification results.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Build model (solver, variables, constraints) using the formulation steps above.
# 2. Solve with parameters
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)
status = solver.Solve()

# 3. Check status and extract solution
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    # Verification loop
    for i in entities:
        for t in periods:
            act_val = activate[i, t].solution_value()
            prod_val = production[i, t].solution_value()
            if act_val > 0.5:
                # Check min/max bounds
                assert min_production[i] <= prod_val <= max_production[i]
            else:
                assert abs(prod_val) < 1e-6
    # Output results
else:
    # Handle failure: output status
```

### Common Pitfalls
- Not verifying solution feasibility post-solve, assuming the solver's status is always correct; always run verification checks.
- Running multiple solver instances with minor modifications for verification, which is redundant and inefficient; trust the single optimal solve.
- Manually calculating break-even analyses or testing all entity combinations, which the MILP formulation already optimizes globally.
