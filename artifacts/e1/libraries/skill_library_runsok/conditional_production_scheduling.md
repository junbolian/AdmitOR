---
name: Conditional Production Scheduling
description: |
  Model and solve production planning with fixed costs, minimum operating levels, and demand satisfaction using binary-continuous variable pairs and linear constraints.

---

# Workflow 1 (OR-Tools MILP)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using the OR-Tools Python library. This approach directly maps binary activation and continuous production variables to the solver's native variable objects, enabling efficient solving with SCIP or CBC.

### Step 1 - Define Index Sets and Parameters
- Identify the sets of production entities (e.g., `factories`) and time periods (e.g., `periods`).
- Define all cost and capacity parameters: `fixed_cost`, `variable_cost`, `min_production`, `max_production`, and `demand`.

### Step 2 - Create Binary-Continuous Variable Pairs
- For each entity `i` and period `t`, create a binary variable `run[i,t]` (0/1).
- For each entity `i` and period `t`, create a continuous variable `production[i,t]` (non-negative).

### Step 3 - Enforce Conditional Production Logic
- Add minimum production constraint: `production[i,t] >= min_production[i] * run[i,t]`.
- Add maximum production and zero-if-off constraint: `production[i,t] <= max_production[i] * run[i,t]`.

### Step 4 - Formulate Demand and Objective
- For each period `t`, add demand satisfaction: `sum(production[i,t] for i in entities) >= demand[t]`.
- Define the objective to minimize total cost: `sum(fixed_cost[i] * run[i,t] + variable_cost[i] * production[i,t])`.

### Formulation Template
```json
{
  "sets": ["entities", "periods"],
  "parameters": {
    "fixed_cost": "map entity -> value",
    "variable_cost": "map entity -> value",
    "min_production": "map entity -> value",
    "max_production": "map entity -> value",
    "demand": "map period -> value"
  },
  "decision_variables": [
    {"name": "run", "type": "binary", "indices": ["entities", "periods"]},
    {"name": "production", "type": "continuous", "indices": ["entities", "periods"], "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in entities, t in periods} (fixed_cost[i] * run[i,t] + variable_cost[i] * production[i,t])"
  },
  "constraints": [
    {"name": "min_prod", "expression": "production[i,t] >= min_production[i] * run[i,t]", "indices": ["entities", "periods"]},
    {"name": "max_prod", "expression": "production[i,t] <= max_production[i] * run[i,t]", "indices": ["entities", "periods"]},
    {"name": "demand_sat", "expression": "sum_{i in entities} production[i,t] >= demand[t]", "indices": ["periods"]}
  ]
}
```

### Common Pitfalls
- Forgetting to set an upper bound for the continuous `production` variable, which can lead to unbounded models.
- Incorrectly using the same index variable name in nested loops when adding constraints, causing silent errors.
- Not scaling the objective coefficients (costs) if they differ by orders of magnitude, which can degrade solver performance.

## Solving stage

### Strategy Overview
Use the `ortools.linear_solver` (`pywraplp`) interface to build the model, configure the SCIP or CBC solver with performance settings, solve, and rigorously verify the solution's feasibility.

### Step 1 - Initialize Solver and Create Variables
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- In nested loops over entities and periods, create `solver.IntVar(0, 1, ...)` for `run` and `solver.NumVar(0, solver.infinity(), ...)` for `production`. Store them in dictionaries for easy access.

### Step 2 - Add Constraints via Loops
- Loop over entities and periods to add the `min_prod` and `max_prod` constraints using `solver.Add()`.
- Loop over periods to add the `demand_sat` constraint, summing the relevant production variables.

### Step 3 - Build and Solve the Objective
- Initialize the objective: `objective = solver.Objective()`.
- For each variable, set its coefficient using `objective.SetCoefficient(var, cost)`.
- Call `objective.SetMinimization()`.
- Set solver parameters: `solver.SetTimeLimit(60000)`, `solver.SetNumThreads(4)`.
- Call `solver.Solve()`.

### Step 4 - Verify and Extract Solution
- Check the solve status: `status = solver.Solve()`.
- If `status` is `solver.OPTIMAL` or `solver.FEASIBLE`, extract variable values using `.solution_value()`.
- Programmatically verify key constraints: total production per period meets demand, and production for inactive entities is zero.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (Create variables, add constraints, set objective as per steps)

# Solve with status / termination checks
solver.SetTimeLimit(60000)  # Time limit in milliseconds
status = solver.Solve()

if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    # Extract and verify solution details
    for i in entities:
        for t in periods:
            run_val = run_vars[i,t].solution_value()
            prod_val = prod_vars[i,t].solution_value()
            # Verification logic...
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good solutions.
- Assuming variable indices exist in dictionaries without proper initialization, leading to KeyErrors.
- Neglecting to set a time limit for large instances, causing indefinite runs.

# Workflow 2 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling environment, leveraging its set-based, declarative syntax. This approach cleanly separates model structure from data and interfaces seamlessly with the HiGHS solver for open-source MILP solving.

### Step 1 - Declare Model Sets and Parameters
- Define Pyomo `Set` objects for `model.entities` and `model.periods`.
- Define `Param` objects for all cost, capacity, and demand data, initialized from external dictionaries.

### Step 2 - Define Binary and Continuous Variables
- Declare `model.run` as a `Var` indexed over `(entities, periods)` with `domain=pyo.Binary`.
- Declare `model.production` as a `Var` indexed over `(entities, periods)` with `domain=pyo.NonNegativeReals`.

### Step 3 - Implement Conditional Constraints via Rules
- Create a `Constraint` for minimum production: `model.production[f,t] >= model.min_prod[f] * model.run[f,t]`.
- Create a `Constraint` for maximum production: `model.production[f,t] <= model.max_prod[f] * model.run[f,t]`.
- Both constraints are defined for all `(f,t)` using a rule function.

### Step 4 - Formulate Demand Constraint and Objective
- Create a `Constraint` for demand satisfaction per period: `sum(model.production[f,t] for f in entities) >= model.demand[t]`.
- Define an `Objective` to minimize the sum of fixed and variable costs across all entities and periods.

### Formulation Template
```json
{
  "sets": ["entities", "periods"],
  "parameters": {
    "fixed_cost": "pyo.Param(entities)",
    "variable_cost": "pyo.Param(entities)",
    "min_production": "pyo.Param(entities)",
    "max_production": "pyo.Param(entities)",
    "demand": "pyo.Param(periods)"
  },
  "decision_variables": [
    {"name": "run", "type": "pyo.Var", "domain": "Binary", "indices": ["entities", "periods"]},
    {"name": "production", "type": "pyo.Var", "domain": "NonNegativeReals", "indices": ["entities", "periods"]}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum(fixed_cost[f] * run[f,t] + variable_cost[f] * production[f,t] for f in entities for t in periods)"
  },
  "constraints": [
    {"name": "min_prod", "rule": "production[f,t] >= min_production[f] * run[f,t]", "indices": ["entities", "periods"]},
    {"name": "max_prod", "rule": "production[f,t] <= max_production[f] * run[f,t]", "indices": ["entities", "periods"]},
    {"name": "demand_sat", "rule": "sum(production[f,t] for f in entities) >= demand[t]", "indices": ["periods"]}
  ]
}
```

### Common Pitfalls
- Shadowing Pyomo set names (e.g., using `for f in model.F` inside a rule where `F` is the set) causing confusion.
- Forgetting to initialize `Param` objects, leading to runtime errors when building constraints.
- Using Python's built-in `sum` instead of Pyomo's summation in rule expressions, which fails to build proper expressions.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with concrete data, configure the HiGHS solver via `SolverFactory`, solve with robust error handling, and extract results while checking solver status and termination conditions.

### Step 1 - Build Model and Configure Solver
- Instantiate the concrete model with all parameters initialized.
- Create a solver object: `solver = pyo.SolverFactory('highs')`.
- Set solver options: `solver.options['mip_rel_gap'] = 0.0`, `solver.options['time_limit'] = 30`.

### Step 2 - Solve with Error Handling
- Wrap the solve call in a try-except block to catch any solver or interface errors.
- Execute `results = solver.solve(model, tee=False)`.

### Step 3 - Validate Solver Status
- Import `SolverStatus` and `TerminationCondition` from `pyomo.opt`.
- Check if `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 4 - Extract and Verify Solution
- If the status is valid, retrieve the objective value: `total_cost = pyo.value(model.obj)`.
- Iterate through model variables to extract the schedule, using a tolerance (e.g., `> 0.5`) for binary variable values.
- Programmatically verify that all constraints are satisfied by the extracted values.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# build model from formulation
model = pyo.ConcreteModel()
model.entities = pyo.Set(initialize=entities_list)
model.periods = pyo.Set(initialize=periods_list)
# ... (Define parameters, variables, constraints, objective as per modeling steps)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['mip_rel_gap'] = 0.0
solver.options['time_limit'] = 30

try:
    results = solver.solve(model, tee=False)
    status = results.solver.status
    term = results.solver.termination_condition

    if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
        total_cost = float(pyo.value(model.obj))
        # Extract and verify solution details
    else:
        print(f"Solver terminated with status: {status}, condition: {term}")
except Exception as e:
    print(f"Solver error: {e}")
```

### Common Pitfalls
- Setting `mip_rel_gap` to `-1` in HiGHS (which means 'default') instead of `0.0` for optimality, leading to early termination.
- Not using `pyo.value()` to extract objective and variable values, resulting in Pyomo expression objects.
- Overlooking the need to check both `SolverStatus` and `TerminationCondition` for a complete status picture.
