---
name: AssignmentWithShortageSkill
description: |
  Model and solve resource-to-task assignment problems with explicit shortage tracking using binary assignment and integer shortage variables, minimizing combined preference and penalty costs.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Formulate the assignment-with-shortage problem for a solver accepting linear constraints over Boolean and integer variables (e.g., OR-Tools CP-SAT). Use binary assignment variables for each resource-task pair and integer shortage variables per task, with linear inequality constraints for availability, skill, and at-most-one assignment, and equality constraints for demand fulfillment.

### Step 1 - Define Sets and Parameters
- Define index sets for `RESOURCES`, `TASKS`, and optional `PERIODS` if the problem has a time dimension.
- Define parameters: `demand[t]` (integer), `availability[r, t]` (binary), `has_skill[r]` (binary), `preference_cost[r, t]` (numeric), and `shortage_penalty[t]` (numeric, typically large).

### Step 2 - Create Decision Variables
- Create binary decision variable `x[r, t]` for each resource `r` and task `t`.
- Create integer decision variable `shortage[t]` for each task `t`, with a lower bound of 0 and an upper bound of `demand[t]`.

### Step 3 - Formulate Constraints
- **Demand Fulfillment**: For each task `t`, add `sum(x[r, t] for r in RESOURCES) + shortage[t] == demand[t]`.
- **Availability**: For each resource `r` and task `t`, add `x[r, t] <= availability[r, t]`.
- **Skill Requirement**: For each resource `r` and task `t`, add `x[r, t] <= has_skill[r]`.
- **At-Most-One Assignment**: For each resource `r`, add `sum(x[r, t] for t in TASKS) <= 1`.

### Step 4 - Construct Objective
- Formulate objective as `minimize sum(preference_cost[r, t] * x[r, t]) + sum(shortage_penalty[t] * shortage[t])`.
- Ensure `shortage_penalty` values are set significantly higher than the maximum `preference_cost` to prioritize demand fulfillment.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    "demand: TASKS -> integer",
    "availability: RESOURCES x TASKS -> binary",
    "has_skill: RESOURCES -> binary",
    "preference_cost: RESOURCES x TASKS -> numeric",
    "shortage_penalty: TASKS -> numeric"
  ],
  "decision_variables": [
    "x: RESOURCES x TASKS -> binary",
    "shortage: TASKS -> integer in [0, demand]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(preference_cost[r,t] * x[r,t]) + sum(shortage_penalty[t] * shortage[t])"
  },
  "constraints": [
    "demand_fulfillment[t]: sum(x[r,t]) + shortage[t] == demand[t]",
    "availability[r,t]: x[r,t] <= availability[r,t]",
    "skill[r,t]: x[r,t] <= has_skill[r]",
    "at_most_one[r]: sum(x[r,t]) <= 1"
  ]
}
```

### Common Pitfalls
- Forgetting to bound `shortage` variables, which can lead to unbounded solutions.
- Setting `shortage_penalty` too low, causing the solver to prefer shortages over assignments.
- Using a multi-dimensional `x[r, p, t]` variable but incorrectly flattening indices in constraints.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, configuring it for exact or time-limited search, verifying solution status, and extracting assignments and shortages.

### Step 1 - Configure Solver
- Instantiate a `CpModel`.
- Set solver parameters: `solver.parameters.max_time_in_seconds = TIME_LIMIT`, `solver.parameters.num_search_workers = NUM_WORKERS`, `solver.parameters.random_seed = SEED`.
- For exact solutions, set `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status code: `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, or `UNKNOWN`.
- Proceed only if status is `OPTIMAL` or `FEASIBLE`.

### Step 3 - Extract and Verify Solution
- For each variable `x[r,t]`, check if `solver.Value(x_var) == 1` to build assignment list.
- For each variable `shortage[t]`, record `solver.Value(s_var)`.
- Optionally, verify constraints programmatically (e.g., sum of assignments plus shortage equals demand).

### Step 4 - Output Results
- Output a JSON structure containing solver status, objective value, list of assignments `(resource, task)`, and dictionary of shortages per task.
- If solver failed, output a failure payload with the status and termination reason.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... create variables and constraints as per formulation ...
# solve with status / termination checks
solver = cp_model.CpSolver()
# Apply parameter settings
solver.parameters.max_time_in_seconds = TIME_LIMIT
solver.parameters.num_search_workers = NUM_WORKERS
status = solver.Solve(model)
# Check status and output
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    assignments = [(r,t) for (r,t), var in x_vars.items() if solver.Value(var) > 0.5]
    shortages = {t: solver.Value(var) for t, var in shortage_vars.items()}
    result_payload = {"status": status, "objective": solver.ObjectiveValue(),
                     "assignments": assignments, "shortages": shortages}
    print(f"RESULT_JSON:{json.dumps(result_payload)}")
else:
    failure_payload = {"status": status, "message": "Solver did not find a feasible solution."}
    print(f"RESULT_JSON:{json.dumps(failure_payload)}")
```

### Common Pitfalls
- Accessing `solver.Value()` on variables before checking solver status, which may cause errors.
- Not using `> 0.5` check for binary variable values due to solver internal tolerances.
- Omitting runtime limits for large instances, potentially causing long, unresponsive runs.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem using Pyomo's abstract or concrete modeling for use with external MIP solvers (e.g., Gurobi, HiGHS). Structure uses Pyomo `Set`, `Param`, `Var`, `Constraint`, and `Objective` components for clarity and solver portability.

### Step 1 - Define Pyomo Sets and Parameters
- Create Pyomo `Set` objects for `model.RESOURCES` and `model.TASKS`.
- Define `model.demand`, `model.availability`, `model.has_skill`, `model.preference_cost`, and `model.shortage_penalty` as `Param` objects, potentially indexed over the sets.

### Step 2 - Declare Decision Variables
- Declare `model.x` as `Var(model.RESOURCES, model.TASKS, within=pyo.Binary)`.
- Declare `model.shortage` as `Var(model.TASKS, within=pyo.NonNegativeIntegers, bounds=(0, demand))`.

### Step 3 - Build Constraints via Rules
- Define a rule for demand constraint: `def demand_rule(m, t): return sum(m.x[r, t] for r in m.RESOURCES) + m.shortage[t] == m.demand[t]`. Create `model.demand_con = Constraint(model.TASKS, rule=demand_rule)`.
- Similarly, create rules and constraints for availability, skill, and at-most-one assignment.

### Step 4 - Construct Objective Expression
- Define objective expression: `sum(m.preference_cost[r,t] * m.x[r,t] for r in m.RESOURCES for t in m.TASKS) + sum(m.shortage_penalty[t] * m.shortage[t] for t in m.TASKS)`.
- Set as `model.obj = Objective(expr=expr, sense=minimize)`.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    "demand: TASKS -> integer",
    "availability: RESOURCES x TASKS -> binary",
    "has_skill: RESOURCES -> binary",
    "preference_cost: RESOURCES x TASKS -> numeric",
    "shortage_penalty: TASKS -> numeric"
  ],
  "decision_variables": [
    "x: RESOURCES x TASKS -> Binary",
    "shortage: TASKS -> NonNegativeInteger"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(preference_cost[r,t] * x[r,t]) + sum(shortage_penalty[t] * shortage[t])"
  },
  "constraints": [
    "demand_fulfillment[t]: sum(x[r,t]) + shortage[t] == demand[t]",
    "availability[r,t]: x[r,t] <= availability[r,t]",
    "skill[r,t]: x[r,t] <= has_skill[r]",
    "at_most_one[r]: sum(x[r,t]) <= 1"
  ]
}
```

### Common Pitfalls
- Using `bounds=(0, None)` for `shortage` without linking to `demand`, risking unboundedness.
- Incorrectly indexing parameters in constraint rules, causing `KeyError`.
- Forgetting to initialize all parameters before creating a `ConcreteModel`, leading to missing data errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external MIP solver via `SolverFactory`, configure solver options, check termination conditions, and extract the solution.

### Step 1 - Configure and Run Solver
- Instantiate solver: `solver = pyo.SolverFactory('SOLVER_NAME')` (e.g., 'gurobi', 'highs').
- Set options: `solver.options['MIPGap'] = 0.0` for exact optimality, `solver.options['TimeLimit'] = TIME_LIMIT`, `solver.options['Threads'] = NUM_THREADS`, `solver.options['Seed'] = SEED`.
- Solve with `results = solver.solve(model, tee=VERBOSE_FLAG)`.

### Step 2 - Check Solver Status and Termination
- Check `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition` for `optimal`, `feasible`, or other conditions.
- Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Extract Solution Values
- Retrieve objective value: `pyo.value(model.obj)`.
- Iterate over `model.x` and `model.shortage` variables: if `pyo.value(var) > 0.5` for binary `x`, record assignment; for `shortage`, record its integer value.
- Store results in structured dictionaries or lists.

### Step 4 - Output and Handle Failures
- Output a JSON containing status, objective, assignments, and shortages.
- If solver fails, output a JSON with failure details (status, termination condition, and message).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.RESOURCES = pyo.Set(initialize=RESOURCES_LIST)
model.TASKS = pyo.Set(initialize=TASKS_LIST)
# ... define parameters, variables, constraints, objective ...
# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = TIME_LIMIT
results = solver.solve(model, tee=False)
from pyomo.opt import SolverStatus, TerminationCondition
status_ok = results.solver.status == SolverStatus.ok
termination_ok = results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]
if status_ok and termination_ok:
    assignments = [(r,t) for (r,t), var in model.x.items() if pyo.value(var) > 0.5]
    shortages = {t: int(pyo.value(model.shortage[t])) for t in model.TASKS if pyo.value(model.shortage[t]) > 1e-6}
    result_payload = {"status": "success", "objective": pyo.value(model.obj),
                     "assignments": assignments, "shortages": shortages}
    print(f"RESULT_JSON:{json.dumps(result_payload)}")
else:
    failure_payload = {"status": results.solver.status, "termination": results.solver.termination_condition}
    print(f"RESULT_JSON:{json.dumps(failure_payload)}")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (solution quality).
- Not converting `shortage` variable values to integers before output, leading to floating-point representation.
- Using `tee=True` in production without log management, causing cluttered output.
