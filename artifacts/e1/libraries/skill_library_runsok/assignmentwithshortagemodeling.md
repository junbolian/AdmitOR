---
name: AssignmentWithShortageModeling
description: |
  Model and solve assignment problems with optional shortages using binary assignment variables, integer shortage variables, and linear constraints, minimizing combined preference and penalty costs.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, which is designed for discrete optimization problems with integer and Boolean variables. The modeling approach directly maps binary assignment decisions and integer shortage quantities to the solver's native variable types, leveraging its efficient constraint propagation.

### Step 1 - Define Variable Structure
- Create a 3D binary variable `x[(e, r, s)]` for each employee-location-shift combination using `model.NewBoolVar()`.
- Create an integer variable `shortage[(r, s)]` for each location-shift pair, bounded between 0 and the demand, using `model.NewIntVar(0, demand[(r, s)], ...)`.

### Step 2 - Implement Core Constraints
- **Demand Fulfillment:** For each location `r` and shift `s`, add `sum(x[(e, r, s)] for e) + shortage[(r, s)] == demand[(r, s)]`.
- **At-Most-One Assignment:** For each employee `e`, add `sum(x[(e, r, s)] for r, s) <= 1`.
- **Availability:** For each employee `e` and shift `s`, add `x[(e, r, s)] <= availability[(e, s)]` for all locations `r`.
- **Skill Requirement:** For each employee `e`, add `x[(e, r, s)] <= has_skill[e]` for all locations `r` and shifts `s`.

### Step 3 - Formulate Objective
- Construct a linear objective to minimize: `sum(preference_cost[e] * x[(e, r, s)]) + penalty_cost * sum(shortage[(r, s)])`.

### Formulation Template
```json
{
  "sets": [
    "employees",
    "locations",
    "shifts"
  ],
  "parameters": [
    "demand[location, shift] (int)",
    "availability[employee, shift] (binary)",
    "has_skill[employee] (binary)",
    "preference_cost[employee] (float)",
    "penalty_cost (float)"
  ],
  "decision_variables": [
    "x[employee, location, shift] (binary)",
    "shortage[location, shift] (integer, 0 <= shortage <= demand)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(preference_cost[e] * x[e, r, s]) + penalty_cost * sum(shortage[r, s])"
  },
  "constraints": [
    "demand_fulfillment: sum(x[e, r, s] for e) + shortage[r, s] == demand[r, s]",
    "at_most_one_assignment: sum(x[e, r, s] for r, s) <= 1 for each e",
    "availability: x[e, r, s] <= availability[e, s] for each e, r, s",
    "skill_requirement: x[e, r, s] <= has_skill[e] for each e, r, s"
  ]
}
```

### Common Pitfalls
- Forgetting to bound the integer shortage variable by the demand, which can lead to unbounded or nonsensical solutions.
- Creating overly verbose variable names that make constraint expressions difficult to read and debug.
- Not leveraging tuple-keyed dictionaries for multi-dimensional parameters, leading to inefficient data access in constraints.

## Solving stage

### Strategy Overview
Solving involves configuring the CP-SAT solver with appropriate limits for time and optimality, executing the solve, rigorously checking the termination status, and extracting variable values in a structured format for validation and downstream use.

### Step 1 - Configure and Execute Solver
- Instantiate `cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 8`, `solver.parameters.random_seed = 42`, and `solver.parameters.relative_gap_limit = 0.0` for an exact solution.
- Call `status = solver.Solve(model)`.

### Step 2 - Verify Solution Status and Extract Results
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. If not, output the status code and reason for failure.
- If feasible, retrieve the objective value using `solver.ObjectiveValue()`.
- Extract assignment values by iterating over all `x` variables and checking `if solver.Value(x_var) == 1`.
- Extract shortage values by iterating over all `shortage` variables and reading `solver.Value(shortage_var)`.

### Step 3 - Output and Validate
- Package the results (status, objective value, list of assignments, shortage quantities) into a structured format like JSON.
- Optionally, implement a verification function that re-calculates the objective and checks all constraints against the extracted solution to ensure correctness.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... (variable and constraint creation as per Modeling Stage)

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Objective value: {solver.ObjectiveValue()}")
    # Extract and store variable values
    assignments = []
    for e in employees:
        for r in locations:
            for s in shifts:
                if solver.Value(x[(e, r, s)]) == 1:
                    assignments.append({'employee': e, 'location': r, 'shift': s})
    shortages = {(r, s): solver.Value(shortage[(r, s)]) for r in locations for s in shifts}
    # Output structured result
    result = {'status': status, 'objective': solver.ObjectiveValue(), 'assignments': assignments, 'shortages': shortages}
else:
    print(f"Solver failed with status: {status}")
    result = {'status': status, 'error': 'No feasible solution found'}
```

### Common Pitfalls
- Failing to check for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid but suboptimal solutions.
- Not setting a random seed, leading to non-reproducible results across runs.
- Attempting to access `solver.Value()` on a variable before confirming the solve status is feasible, which may cause runtime errors.

# Workflow 2 (MIP Solver via Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo modeling library to formulate the problem as a Mixed-Integer Program (MIP), which can then be solved by various backend solvers (e.g., CBC, Gurobi). The abstraction separates model construction from solver execution, promoting clarity and solver interchangeability.

### Step 1 - Declare Model Components
- Define index sets for `employees`, `locations`, and `shifts` using `pyo.Set()`.
- Declare parameters (demand, availability, skill, costs) as `pyo.Param` objects, initialized with multi-dimensional dictionaries.
- Create binary decision variable `model.x[e, r, s]` using `pyo.Var(within=pyo.Binary)`.
- Create non-negative integer decision variable `model.shortage[r, s]` using `pyo.Var(within=pyo.NonNegativeIntegers, bounds=(0, demand))`.

### Step 2 - Construct Constraints and Objective
- **Demand Constraint:** `model.demand_rule[r, s] = sum(model.x[e, r, s] for e) + model.shortage[r, s] == demand[r, s]`.
- **Assignment Limit:** `model.assign_limit[e] = sum(model.x[e, r, s] for r, s) <= 1`.
- **Availability & Skill:** Implement as inequality constraints: `model.avail_rule[e, r, s] = model.x[e, r, s] <= availability[e, s]` and `model.skill_rule[e, r, s] = model.x[e, r, s] <= has_skill[e]`.
- **Objective:** `model.obj = pyo.Objective(expr=sum(preference_cost[e] * model.x[e, r, s]) + penalty_cost * sum(model.shortage[r, s]), sense=pyo.minimize)`.

### Step 3 - Prepare Model for Solver
- Ensure the model is fully instantiated with all variables, constraints, and the objective.
- The model object is now ready to be passed to a solver interface.

### Formulation Template
```json
{
  "sets": [
    "model.employees",
    "model.locations",
    "model.shifts"
  ],
  "parameters": [
    "model.demand[location, shift] (pyo.Param)",
    "model.availability[employee, shift] (pyo.Param)",
    "model.has_skill[employee] (pyo.Param)",
    "model.preference_cost[employee] (pyo.Param)",
    "model.penalty_cost (pyo.Param)"
  ],
  "decision_variables": [
    "model.x[employee, location, shift] (pyo.Var, Binary)",
    "model.shortage[location, shift] (pyo.Var, NonNegativeIntegers)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.preference_cost[e] * model.x[e, r, s]) + model.penalty_cost * sum(model.shortage[r, s])"
  },
  "constraints": [
    "demand_rule: sum(model.x[e, r, s] for e) + model.shortage[r, s] == model.demand[r, s]",
    "assign_limit: sum(model.x[e, r, s] for r, s) <= 1",
    "avail_rule: model.x[e, r, s] <= model.availability[e, s]",
    "skill_rule: model.x[e, r, s] <= model.has_skill[e]"
  ]
}
```

### Common Pitfalls
- Using `pyo.Var` without specifying `within` domain or `bounds`, which can lead to solver errors or incorrect variable types.
- Defining constraints inside a loop without properly adding them to the model object.
- Confusing Pyomo's 1-based indexing convention if data is 0-based, leading to index errors.

## Solving stage

### Strategy Overview
The solving stage involves selecting a MIP solver, configuring it with time and optimality gaps, executing the optimization, and meticulously checking both the solver status and termination condition before interpreting results.

### Step 1 - Select and Configure Solver
- Use `pyo.SolverFactory('solver_name')` (e.g., 'cbc', 'gurobi').
- Pass solver options via `opt.options`: e.g., `{'timeLimit': 30, 'threads': 4, 'MIPGap': 0.0, 'seed': 42}`.

### Step 2 - Solve and Check Termination
- Execute `results = solver.solve(model, tee=False)`.
- Check if the solver process completed successfully: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `results.solver.termination_condition` should be `pyo.TerminationCondition.optimal` or `.feasible`.

### Step 3 - Extract and Validate Solution
- If feasible, retrieve the objective value: `pyo.value(model.obj)`.
- Extract variable values: For binary `model.x`, use `if pyo.value(model.x[e, r, s]) > 0.5:`. For integer `model.shortage`, use `int(pyo.value(model.shortage[r, s]))`.
- Perform a post-solve verification by evaluating key constraints with the extracted values to ensure solution integrity.

### Code Usage
```python
import pyomo.environ as pyo

# build model from formulation
model = pyo.ConcreteModel()
# ... (set, parameter, variable, constraint, objective creation as per Modeling Stage)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')  # or 'gurobi', 'glpk'
solver.options = {'timeLimit': 30, 'threads': 4, 'MIPGap': 0.0}
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    print(f"Objective value: {pyo.value(model.obj)}")
    # Extract assignments
    assignments = []
    for e in model.employees:
        for r in model.locations:
            for s in model.shifts:
                if pyo.value(model.x[e, r, s]) > 0.5:
                    assignments.append({'employee': e, 'location': r, 'shift': s})
    # Extract shortages
    shortages = {(r, s): int(pyo.value(model.shortage[r, s])) for r in model.locations for s in model.shifts}
    result = {'status': 'success', 'objective': pyo.value(model.obj), 'assignments': assignments, 'shortages': shortages}
else:
    print(f"Solver failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
    result = {'status': 'failure', 'solver_status': str(results.solver.status), 'termination': str(results.solver.termination_condition)}
```

### Common Pitfalls
- Assuming `SolverStatus.ok` alone indicates a feasible solution; it only means the solver ran without error. Always check the `termination_condition`.
- Comparing floating-point values of binary variables to exactly 1.0; use a tolerance (e.g., `> 0.5`) to avoid precision issues.
- Not catching exceptions when a solver is not available (e.g., `SolverFactory` returns `None`), causing later steps to fail.
