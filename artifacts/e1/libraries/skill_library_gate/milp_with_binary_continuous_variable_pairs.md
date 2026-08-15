---
name: MILP with Binary-Continuous Variable Pairs
description: |
  Model and solve mixed-integer linear problems where binary activation variables control continuous production levels, linking them via big-M constraints to enforce conditional bounds and fixed costs.

---

# Workflow 1 (OR-Tools / SCIP-CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools to build a Mixed-Integer Linear Programming (MILP) model directly via its Python API. It is suited for rapid prototyping and deployment in environments where a lightweight, programmatic modeling interface is preferred over a declarative framework.

### Step 1 - Define Index Sets and Parameters
- Declare sets for entities (e.g., `facilities`) and time periods (e.g., `periods`) as lists or ranges.
- Define parameter dictionaries for `max_production`, `min_production`, `fixed_cost`, `variable_cost`, and `demand`, indexed by the appropriate sets.

### Step 2 - Create Binary-Continuous Variable Pairs
- For each entity-period pair, create a binary variable `run[i, t]` using `solver.IntVar(0, 1, ...)`.
- For each pair, create a continuous variable `production[i, t]` using `solver.NumVar(0, max_production[i], ...)`.

### Step 3 - Link Production to Run Status with Big-M Constraints
- Add upper bound constraint: `production[i, t] <= max_production[i] * run[i, t]`. This forces production to zero when `run` is 0.
- Add lower bound constraint: `production[i, t] >= min_production[i] * run[i, t]`. This enforces minimum output when the entity is active.

### Step 4 - Enforce Aggregate Demand Satisfaction
- For each time period, create a constraint summing `production[i, t]` across all entities, requiring it to be `>= demand[t]`.

### Step 5 - Formulate Linear Cost Objective
- Build the objective expression as the sum of `fixed_cost[i] * run[i, t]` and `variable_cost[i] * production[i, t]` across all indices.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": ["entities", "periods"],
  "parameters": [
    "max_production[entity]",
    "min_production[entity]",
    "fixed_cost[entity]",
    "variable_cost[entity]",
    "demand[period]"
  ],
  "decision_variables": [
    "run[entity, period] ∈ {0,1}",
    "production[entity, period] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( fixed_cost[entity] * run[entity, period] + variable_cost[entity] * production[entity, period] )"
  },
  "constraints": [
    "production[entity, period] ≤ max_production[entity] * run[entity, period]",
    "production[entity, period] ≥ min_production[entity] * run[entity, period]",
    "sum( production[entity, period] for entity in entities ) ≥ demand[period]"
  ]
}
```

### Common Pitfalls
- Using an incorrect or overly large value for the big-M constant in the linking constraints, which can weaken the linear relaxation and slow down solving.
- Forgetting to set a finite upper bound (e.g., `max_production`) for the continuous variable when creating it with `NumVar`.
- Creating variables or constraints inside incorrect nested loops, leading to missing or duplicate model elements.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools wrapper for SCIP or CBC. The focus is on configuring practical solver limits, executing the solve, and robustly extracting and verifying the solution.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')` or `'CBC'`.
- Set a time limit: `solver.SetTimeLimit(30000)` (in milliseconds).
- Optionally set the number of threads: `solver.SetNumThreads(4)`.

### Step 2 - Build Model from Formulation
- Follow the modeling steps to create variables, constraints, and the objective using the solver's API methods (`solver.Add`, `solver.Objective().SetCoefficient`, etc.).

### Step 3 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `status = solver.optimal` or `solver.feasible`. Proceed only if status indicates success.

### Step 4 - Extract and Validate Solution
- Retrieve variable values using `.solution_value()` for both `run` and `production` variables.
- Compute the objective value via `solver.Objective().Value()`.
- Optionally, post-process to verify all constraints (demand, bounds, linkage) are satisfied within tolerance.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (variable and constraint creation loops)
objective = solver.Objective()
# ... (set coefficients)
objective.SetMinimization()

# solve with status / termination checks
result_status = solver.Solve()
if result_status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_value = objective.Value()
    # Extract solution values
    for i in entities:
        for t in periods:
            run_val = run[i, t].solution_value()
            prod_val = production[i, t].solution_value()
            # ... process values
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good feasible solutions when a proven optimum isn't required.
- Misinterpreting the solver's time limit as a guarantee of termination; the solver may stop early for other reasons.
- Attempting to access `.solution_value()` on variables before checking the solve status, which can cause errors.

# Workflow 2 (Pyomo / HiGHS-CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, a declarative modeling language in Python, to abstract the model formulation. It separates model definition from solver choice, enabling easy switching between solvers like HiGHS and CBC and promoting clean, maintainable code.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for `model.entities` and `model.periods`.
- Define Pyomo `Param` objects for `model.max_production`, `model.min_production`, `model.fixed_cost`, `model.variable_cost`, and `model.demand`, indexed by the appropriate sets.

### Step 2 - Define Binary and Continuous Variables
- Create a Pyomo `Var` for `model.run`, indexed over the sets, with `domain=pyo.Binary`.
- Create a Pyomo `Var` for `model.production`, indexed over the sets, with `domain=pyo.NonNegativeReals`.

### Step 3 - Implement Conditional Production Constraints
- Define a `Constraint` rule for the minimum production: `model.production[entity, period] >= model.min_production[entity] * model.run[entity, period]`.
- Define a `Constraint` rule for the maximum production: `model.production[entity, period] <= model.max_production[entity] * model.run[entity, period]`.

### Step 4 - Enforce Demand with Aggregate Constraint
- Define a `Constraint` rule for each period, summing `model.production` across entities and requiring it to be `>= model.demand[period]`.

### Step 5 - Construct Separable Cost Objective
- Define an `Objective` with the expression summing `model.fixed_cost[entity] * model.run[entity, period] + model.variable_cost[entity] * model.production[entity, period]` over all indices, setting `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["entities", "periods"],
  "parameters": [
    "max_production[entity]",
    "min_production[entity]",
    "fixed_cost[entity]",
    "variable_cost[entity]",
    "demand[period]"
  ],
  "decision_variables": [
    "run[entity, period] ∈ {0,1}",
    "production[entity, period] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( fixed_cost[entity] * run[entity, period] + variable_cost[entity] * production[entity, period] )"
  },
  "constraints": [
    "production[entity, period] ≤ max_production[entity] * run[entity, period]",
    "production[entity, period] ≥ min_production[entity] * run[entity, period]",
    "sum( production[entity, period] for entity in entities ) ≥ demand[period]"
  ]
}
```

### Common Pitfalls
- Shadowing iterator variable names (e.g., using `t` in both an outer loop and a constraint rule) within Pyomo's rule functions, leading to incorrect indexing.
- Forgetting to initialize Pyomo parameters with concrete data before solving, resulting in an abstract model that cannot be instantiated.
- Using `-1` to represent an unlimited value in solver options (like `mip_rel_gap`), which may be interpreted differently by each solver; prefer explicit values like `0.0`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., for HiGHS or CBC). The workflow emphasizes robust solver configuration, structured error handling, and systematic solution verification.

### Step 1 - Instantiate Model and Load Data
- Create a concrete Pyomo model instance: `model = pyo.ConcreteModel()`.
- Populate the model sets and parameters with the actual problem data.

### Step 2 - Configure and Execute Solver
- Create a solver object: `solver = pyo.SolverFactory('appsi_highs')` or `'cbc'`.
- Set solver options: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0`.
- Call `results = solver.solve(model, tee=False)` to execute the solve.

### Step 3 - Check Solution Status and Termination Condition
- Verify the solver status: `pyo.check_optimal_termination(results)` or check `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 4 - Extract and Verify Solution Values
- Access variable values using `pyo.value(model.run[entity, period])` and `pyo.value(model.production[entity, period])`.
- Compute the objective value via `pyo.value(model.obj)` or `results.problem.lower_bound`.
- Optionally, implement a post-solve validation function to check constraint satisfaction.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.entities = pyo.Set(initialize=entities_list)
model.periods = pyo.Set(initialize=periods_list)
# ... (parameter and variable definitions)
model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
# ... (constraint definitions)

# solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1  # Use -1 for default, 0.0 for optimality
try:
    results = solver.solve(model)
    if (results.solver.status == pyo.SolverStatus.ok and
        results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                                 pyo.TerminationCondition.feasible)):
        obj_val = pyo.value(model.obj)
        # Extract solution values
        for i in model.entities:
            for t in model.periods:
                run_val = pyo.value(model.run[i, t])
                prod_val = pyo.value(model.production[i, t])
                # ... process values
    else:
        print(f"Solver terminated with status: {results.solver.termination_condition}")
except Exception as e:
    print(f"Solver error: {e}")
```

### Common Pitfalls
- Setting conflicting solver options (e.g., `threads` in CBC when a global scheduler is active) which can cause unexpected behavior or errors.
- Assuming `pyo.check_optimal_termination` returns `True` for feasible solutions; it is designed for optimal termination. Check termination condition explicitly for feasibility acceptance.
- Not catching exceptions during the solve call, which can crash the application if the solver encounters an error.
