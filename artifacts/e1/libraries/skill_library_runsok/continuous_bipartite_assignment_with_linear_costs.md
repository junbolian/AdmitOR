---
name: Continuous Bipartite Assignment with Linear Costs
description: |
  Model and solve resource-to-task allocation problems with continuous flows, supply/demand constraints, and per-assignment upper bounds to minimize linear cost.
---

# Workflow 1 (OR-Tools / GLOP)

## Modeling stage

### Strategy Overview
Model the problem as a linear program using Google's OR-Tools, leveraging its efficient `GLOP` solver for continuous problems. Variables and constraints are built imperatively via the solver's API.

### Step 1 - Define Data Structures
- Organize resources, tasks, capacities, demands, costs, and per-assignment upper bounds into lists or dictionaries.
- Ensure data dimensions align (e.g., `cost[resource][task]`).

### Step 2 - Create Solver and Variables
- Instantiate the linear solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Create continuous, non-negative decision variables `x[i][j]` with lower bound 0 and upper bound `max_assignment[i][j]` in a single step.

### Step 3 - Formulate Objective
- Build a linear objective expression by summing `cost[i][j] * x[i][j]` across all `i`, `j`.
- Set the objective for minimization using `solver.Minimize()`.

### Step 4 - Add Demand Satisfaction Constraints
- For each task `j`, create a linear equality constraint: `sum(x[i][j] for i in resources) == demand[j]`.
- Use `solver.Add(sum_expr == demand[j])`.

### Step 5 - Add Supply Capacity Constraints
- For each resource `i`, create a linear inequality constraint: `sum(x[i][j] for j in tasks) <= capacity[i]`.
- Use `solver.Add(sum_expr <= capacity[i])`.

### Formulation Template
```json
{
  "sets": ["resources", "tasks"],
  "parameters": ["capacity[resource]", "demand[task]", "unit_cost[resource][task]", "max_assignment[resource][task]"],
  "decision_variables": ["x[resource][task] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(unit_cost[i][j] * x[i][j] for i in resources for j in tasks)"
  },
  "constraints": [
    "demand_satisfaction: sum(x[i][j] for i in resources) == demand[j], for each task j",
    "supply_capacity: sum(x[i][j] for j in tasks) <= capacity[i], for each resource i",
    "assignment_limit: x[i][j] <= max_assignment[i][j], for each resource i, task j"
  ]
}
```

### Common Pitfalls
- Forgetting to set variable upper bounds during creation, leading to unbounded variables.
- Mismatching indices when building constraint expressions, causing incorrect sums.
- Not handling the case where a resource's capacity is zero; the model remains valid but explicit zero-sum constraints can improve clarity.

## Solving stage

### Strategy Overview
Solve the built model using the `GLOP` backend, check solution status rigorously, and extract results with validation against original parameters.

### Step 1 - Invoke Solver
- Call `result_status = solver.Solve()` to execute the optimization.

### Step 2 - Check Solution Status
- Verify the result status is `OPTIMAL` or `FEASIBLE` before proceeding.
- If status is not `OPTIMAL` or `FEASIBLE`, log an error and handle the infeasible/unbounded case appropriately.

### Step 3 - Extract and Validate Solution
- Extract the objective value: `solver.Objective().Value()`.
- For each variable `x[i][j]`, retrieve its solution value: `x[i][j].solution_value()`.
- Compute actual allocations per task and per resource, compare against demands and capacities to validate feasibility.

### Step 4 - Report Results
- Print a summary including objective value, resource utilization percentages, and task fulfillment.
- Optionally, list individual assignments above a small tolerance (e.g., > 1e-6).

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# Create variables with bounds
x = {}
for i in resources:
    for j in tasks:
        x[i, j] = solver.NumVar(0, max_assignment[i][j], f'x_{i}_{j}')
# Set objective
objective = solver.Objective()
for i in resources:
    for j in tasks:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()
# Add constraints
for j in tasks:
    ct = solver.Constraint(demand[j], demand[j])
    for i in resources:
        ct.SetCoefficient(x[i, j], 1)
for i in resources:
    ct = solver.Constraint(0, capacity[i])
    for j in tasks:
        ct.SetCoefficient(x[i, j], III)
# solve with status / termination checks
result_status = solver.Solve()
if result_status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'Objective value: {solver.Objective().Value()}')
    # Extract and validate solution
else:
    print('No optimal or feasible solution found.')
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; for critical applications, prefer `OPTIMAL`.
- Not accounting for floating-point precision when checking constraint satisfaction; use a tolerance (e.g., 1e-6).
- Overlooking solver time limits for larger instances; set `solver.SetTimeLimit()` if needed.

# Workflow 2 (Pyomo / HiGHS)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo, defining sets, variables, objectives, and constraints via rules. Use the open-source `HiGHS` solver via Pyomo's `SolverFactory` for reliable LP solving.

### Step 1 - Define Abstract Sets
- Declare Pyomo `Set` objects for the index sets `model.resources` and `model.tasks`.

### Step 2 - Define Continuous Variables
- Create a Pyomo `Var` indexed over both sets with domain `pyo.NonNegativeReals`.
- Apply per-assignment upper bounds via variable initialization or separate constraints.

### Step 3 - Formulate Linear Objective
- Define an `Objective` rule that sums `cost[i][j] * model.x[i,j]` across all indices.
- Set the sense to `minimize`.

### Step 4 - Implement Constraint Rules
- Create a `Constraint` for demand satisfaction, indexed by tasks, enforcing equality with `demand[j]`.
- Create a `Constraint` for supply capacity, indexed by resources, enforcing `<= capacity[i]`.
- Create a `Constraint` for assignment limits, indexed by both sets, enforcing `<= max_assignment[i][j]`.

### Step 5 - Handle Edge Cases
- Explicitly add constraints for zero-capacity resources if needed for model clarity, though the capacity constraint suffices.

### Formulation Template
```json
{
  "sets": ["R (resources)", "T (tasks)"],
  "parameters": ["capacity[R]", "demand[T]", "cost[R][T]", "max_assign[R][T]"],
  "decision_variables": ["x[R, T] in NonNegativeReals"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i,j] for i in R for j in T)"
  },
  "constraints": [
    "demand_constr: sum(x[i,j] for i in R) == demand[j], ∀j ∈ T",
    "capacity_constr: sum(x[i,j] for j in T) <= capacity[i], ∀i ∈ R",
    "limit_constr: x[i,j] <= max_assign[i][j], ∀i ∈ R, ∀j ∈ T"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters within constraint rules, leading to `KeyError`.
- Forgetting to initialize all required parameters before creating the concrete model.
- Using mutable default arguments in rule functions; use lambda functions or separate def statements.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver interface, configure solver options for performance, and implement robust checks for solution status and termination conditions.

### Step 1 - Configure and Execute Solver
- Instantiate solver: `solver = pyo.SolverFactory('highs')`.
- Set practical options: time limit, thread count, tolerances.
- Solve the model: `results = solver.solve(model, tee=False)`.

### Step 2 - Verify Solver Status
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `feasible`.

### Step 3 - Extract Solution Safely
- If status checks pass, retrieve the objective value: `pyo.value(model.obj)`.
- Iterate over variables `model.x[i,j]` to get solution values: `pyo.value(model.x[i,j])`.

### Step 4 - Post-Solve Validation
- Recompute totals per task and per resource from the solution.
- Compare against original demands and capacities within a tolerance.
- Print a utilization summary and identify binding constraints.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.R = pyo.Set(initialize=resources)
model.T = pyo.Set(initialize=tasks)
model.x = pyo.Var(model.R, model.T, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, max_assign[i][j]))
def obj_rule(m):
    return sum(cost[i][j] * m.x[i, j] for i in m.R for j in m.T)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
def demand_rule(m, j):
    return sum(m.x[i, j] for i in m.R) == demand[j]
model.demand_constr = pyo.Constraint(model.T, rule=demand_rule)
def capacity_rule(m, i):
    return sum(m.x[i, j] for j in m.T) <= capacity[i]
model.capacity_constr = pyo.Constraint(model.R, rule=capacity_rule)
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    print(f'Objective: {pyo.value(model.obj)}')
    # Extract and validate solution
else:
    print('Solve failed or no feasible solution found.')
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to extraction from failed solves.
- Ignoring solver logs (`tee=True` can help debug during development).
- Using `pyo.value()` on variables before verifying the solution exists, which may raise errors.
