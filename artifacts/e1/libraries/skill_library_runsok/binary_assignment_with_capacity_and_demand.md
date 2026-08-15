---
name: Binary Assignment with Capacity and Demand
description: |
  Model and solve binary assignment problems with resource availability limits and task demand satisfaction, minimizing total cost.

---

# Workflow 1 (OR-Tools MPSolver)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' MPSolver for a direct, low-level API approach. It is ideal for prototyping and deployment where a compiled C++ backend (SCIP, CBC) is preferred for performance on medium-sized problems.

### Step 1 - Define Sets and Parameters
- Define the index sets for resources (`RESOURCES`) and tasks (`TASKS`) as lists of identifiers.
- Create parameter dictionaries: `cost[resource][task]`, `capacity[resource][task]`, `availability[resource]`, and `demand[task]`.

### Step 2 - Create Binary Decision Variables
- Instantiate a binary decision variable `x[resource][task]` for each resource-task pair using `solver.IntVar(0, 1, name)`.

### Step 3 - Formulate Assignment Limit Constraints
- For each resource `i`, add a constraint: `sum(x[i][j] for j in TASKS) <= availability[i]`.

### Step 4 - Formulate Demand Satisfaction Constraints
- For each task `j`, add a constraint: `sum(capacity[i][j] * x[i][j] for i in RESOURCES) >= demand[j]`.

### Step 5 - Define Cost Minimization Objective
- Build the objective expression: `sum(cost[i][j] * x[i][j] for i in RESOURCES for j in TASKS)` and set it for minimization.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    {"name": "cost", "dim": ["RESOURCES", "TASKS"]},
    {"name": "capacity", "dim": ["RESOURCES", "TASKS"]},
    {"name": "availability", "dim": ["RESOURCES"]},
    {"name": "demand", "dim": ["TASKS"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "dim": ["RESOURCES", "TASKS"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in RESOURCES for j in TASKS)"
  },
  "constraints": [
    {"name": "assignment_limit", "expression": "sum(x[i][j] for j in TASKS) <= availability[i] for each i in RESOURCES"},
    {"name": "demand_satisfaction", "expression": "sum(capacity[i][j] * x[i][j] for i in RESOURCES) >= demand[j] for each j in TASKS"}
  ]
}
```

### Common Pitfalls
- Forgetting to name variables uniquely, which complicates debugging.
- Mismatching indices between parameter dictionaries and variable loops.
- Using floating-point equality checks on binary variable values post-solve; use a tolerance (e.g., `> 0.5`).

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools MPSolver wrapper, configuring SCIP or CBC for mixed-integer programming. Focus on setting solver parameters, checking statuses rigorously, and validating the solution.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `SCIP` or `CBC`).
- Set a time limit (`solver.SetTimeLimit(timeout_ms)`) and number of threads (`solver.SetNumThreads(n)`).

### Step 2 - Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `result_status = solver.Solve()`.
- Verify the solution is optimal (`result_status == MPSolver.OPTIMAL`) or feasible (`result_status == MPSolver.FEASIBLE`).

### Step 3 - Extract and Validate Solution
- Retrieve variable values using `x[i][j].solution_value()`.
- Programmatically verify all assignment limit and demand satisfaction constraints are satisfied.
- Compute the achieved objective value.

### Step 4 - Report Results
- Print the optimal objective value and a summary of assignments (where `x[i][j].solution_value() > 0.5`).
- If the solver fails, output a structured JSON with solver status and termination reason.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Variable creation
x = {}
for i in RESOURCES:
    for j in TASKS:
        x[i, j] = solver.IntVar(0, 1, f'x_{i}_{j}')

# Constraints
for i in RESOURCES:
    solver.Add(sum(x[i, j] for j in TASKS) <= availability[i])
for j in TASKS:
    solver.Add(sum(capacity[i][j] * x[i, j] for i in RESOURCES) >= demand[j])

# Objective
objective = solver.Objective()
for i in RESOURCES:
    for j in TASKS:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# Solve with status / termination checks
result_status = solver.Solve()
if result_status == pywraplp.Solver.OPTIMAL or result_status == pywraplp.Solver.FEASIBLE:
    print(f'Objective value = {objective.Value()}')
    # Extract and validate assignments...
else:
    print(f'Solver failed with status: {result_status}')
```

### Common Pitfalls
- Not setting a time limit, leading to indefinite runs on difficult instances.
- Assuming `OPTIMAL` status without checking; `FEASIBLE` may also be acceptable.
- Neglecting to verify constraints post-solve, which can miss numerical issues.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a high-level, declarative modeling style, separating model definition from solver backend. It is suitable for maintainable, research-oriented code and leverages open-source solvers like HiGHS or CBC.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for `model.RESOURCES` and `model.TASKS`.
- Declare `Param` objects for `model.cost`, `model.capacity` (indexed by `(resource, task)`), `model.availability` (indexed by resource), and `model.demand` (indexed by task).

### Step 2 - Define Binary Decision Variables
- Declare a Pyomo `Var` object `model.x`, indexed over `(RESOURCES, TASKS)`, with `within=Binary`.

### Step 3 - Implement Assignment Limit Rule
- Define a `Constraint` rule: for each resource `i`, `sum(model.x[i, j] for j in model.TASKS) <= model.availability[i]`.

### Step 4 - Implement Demand Satisfaction Rule
- Define a `Constraint` rule: for each task `j`, `sum(model.capacity[i, j] * model.x[i, j] for i in model.RESOURCES) >= model.demand[j]`.

### Step 5 - Construct Minimization Objective
- Define an `Objective` rule: `sum(model.cost[i, j] * model.x[i, j] for i in model.RESOURCES for j in model.TASKS)`.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    {"name": "cost", "dim": ["RESOURCES", "TASKS"]},
    {"name": "capacity", "dim": ["RESOURCES", "TASKS"]},
    {"name": "availability", "dim": ["RESOURCES"]},
    {"name": "demand", "dim": ["TASKS"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "dim": ["RESOURCES", "TASKS"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in RESOURCES for j in TASKS)"
  },
  "constraints": [
    {"name": "assignment_limit", "expression": "sum(x[i][j] for j in TASKS) <= availability[i] for each i in RESOURCES"},
    {"name": "demand_satisfaction", "expression": "sum(capacity[i][j] * x[i][j] for i in RESOURCES) >= demand[j] for each j in TASKS"}
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's `ConcreteModel` (immediate data) with `AbstractModel` (deferred data); use `ConcreteModel` for clarity.
- Using Python floats in parameter dictionaries when integers are required; ensure data types match.
- Incorrectly indexing parameters within constraint rules, leading to `KeyError`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the SolverFactory interface, configuring HiGHS or CBC with appropriate optimality gaps and time limits. Emphasize dual status checks and structured solution extraction.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set options: `opt['time_limit'] = 30`, `opt['mip_rel_gap'] = 0.0` (for exact optimality).

### Step 2 - Solve and Inspect Termination
- Call `results = solver.solve(model, tee=False)`.
- Check both `results.solver.status` (`SolverStatus.ok`) and `results.solver.termination_condition` (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Load and Verify Solution
- Load results into the model: `model.solutions.load_from(results)`.
- Iterate through `model.x` to extract assignments where `value(model.x[i, j]) > 0.5`.
- Validate all constraints by recomputing sums and comparing against parameters.

### Step 4 - Output Structured Results
- Print the objective value (`value(model.objective)`), assignment summary, and demand coverage.
- If the solver fails, output a JSON with `solver_status` and `termination_condition` for diagnostics.

### Code Usage
```python
from pyomo.environ import ConcreteModel, Set, Param, Var, Binary, Constraint, Objective, SolverFactory, value
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = ConcreteModel()
model.RESOURCES = Set(initialize=RESOURCES_LIST)
model.TASKS = Set(initialize=TASKS_LIST)

model.cost = Param(model.RESOURCES, model.TASKS, initialize=cost_dict)
model.capacity = Param(model.RESOURCES, model.TASKS, initialize=capacity_dict)
model.availability = Param(model.RESOURCES, initialize=availability_dict)
model.demand = Param(model.TASKS, initialize=demand_dict)

model.x = Var(model.RESOURCES, model.TASKS, within=Binary)

def assignment_limit_rule(model, i):
    return sum(model.x[i, j] for j in model.TASKS) <= model.availability[i]
model.assignment_limit = Constraint(model.RESOURCES, rule=assignment_limit_rule)

def demand_satisfaction_rule(model, j):
    return sum(model.capacity[i, j] * model.x[i, j] for i in model.RESOURCES) >= model.demand[j]
model.demand_satisfaction = Constraint(model.TASKS, rule=demand_satisfaction_rule)

def obj_rule(model):
    return sum(model.cost[i, j] * model.x[i, j] for i in model.RESOURCES for j in model.TASKS)
model.objective = Objective(rule=obj_rule, sense=minimize)

# Solve with status / termination checks
solver = SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0

results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    print(f'Objective value = {value(model.objective)}')
    # Extract and validate assignments...
else:
    print(f'RESULT_JSON: {{"status": "failed", "reason": "solver_error", "solver_status": "{results.solver.status}", "termination_condition": "{results.solver.termination_condition}"}}')
```

### Common Pitfalls
- Setting `mip_rel_gap=0.0` on large instances without a time limit, causing long solves.
- Not checking both `solver.status` and `termination_condition`, missing infeasible or error states.
- Forgetting to load the solution (`model.solutions.load_from(results)`) before accessing variable values.
