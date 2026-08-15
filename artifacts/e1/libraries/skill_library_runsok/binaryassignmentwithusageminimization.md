---
name: BinaryAssignmentWithUsageMinimization
description: |
  Model and solve assignment problems with capacity constraints and binary usage indicators to minimize the number of used resources.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses OR-Tools' CP-SAT solver, designed for discrete optimization with logical constraints. It is well-suited for problems where all decision variables are binary and the constraints are linear.

### Step 1 - Define Core Variables
- Create binary assignment variables `x[i][j]` for each item `i` and resource `j`.
- Create binary usage variables `y[j]` for each resource `j` to indicate if it is active.

### Step 2 - Formulate Assignment and Capacity Constraints
- Add a constraint for each item `i` ensuring it is assigned to exactly one resource: `sum(x[i][j] for j in resources) == 1`.
- For each resource `j`, add a knapsack constraint: `sum(weight[i] * x[i][j] for i in items) <= capacity[j]`.

### Step 3 - Link Assignment and Usage Variables
- Add constraints to enforce logical equivalence: `x[i][j] <= y[j]` for all `i`, `j` (assignment implies usage).
- Optionally, add constraints `y[j] <= sum(x[i][j] for i in items)` for all `j` (usage implies at least one assignment). This can strengthen the formulation.

### Step 4 - Set Objective
- Define the objective to minimize the total number of used resources: `minimize sum(y[j] for j in resources)`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "resources"
  ],
  "parameters": [
    {"name": "weight", "index": "items", "type": "float"},
    {"name": "capacity", "index": "resources", "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["items", "resources"], "type": "binary"},
    {"name": "y", "index": "resources", "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in resources)"
  },
  "constraints": [
    {"name": "assignment_cover", "expression": "sum(x[i][j] for j in resources) == 1 for each i in items"},
    {"name": "capacity_knapsack", "expression": "sum(weight[i] * x[i][j] for i in items) <= capacity[j] for each j in resources"},
    {"name": "usage_linking", "expression": "x[i][j] <= y[j] for each i in items, j in resources"}
  ]
}
```

### Common Pitfalls
- Forgetting to link usage variables in the capacity constraint (`capacity[j] * y[j]`), which is optional but can improve performance.
- Creating an excessive number of linking constraints for large instances; ensure the model size remains manageable.
- Not providing a time limit for the solver, which can lead to long runtimes on difficult instances.

## Solving stage

### Strategy Overview
The solving stage involves configuring the CP-SAT solver, executing the model, and extracting the solution with proper status checks and validation.

### Step 1 - Initialize Solver and Variables
- Create a CP-SAT model.
- Instantiate variables using the model's `NewBoolVar` method for `x` and `y`.

### Step 2 - Add Constraints and Objective
- Add constraints using `model.Add` methods, translating the linear expressions.
- Set the objective using `model.Minimize`.

### Step 3 - Configure and Execute Solver
- Set solver parameters: `solver.parameters.max_time_in_seconds`, `solver.parameters.num_search_workers`, and `solver.parameters.random_seed`.
- Solve the model and capture the status.

### Step 4 - Extract and Validate Solution
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- Extract values for `y[j]` and `x[i][j]` using `solver.Value()`.
- Post-solve, verify that each item is assigned exactly once and that capacity constraints hold.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# Variables
x = {}
for i in items:
    for j in resources:
        x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")
y = {j: model.NewBoolVar(f"y_{j}") for j in resources}

# Constraints
for i in items:
    model.Add(sum(x[(i, j)] for j in resources) == 1)
for j in resources:
    model.Add(sum(weight[i] * x[(i, j)] for i in items) <= capacity[j])
    # Optional linking: model.Add(sum(x[(i, j)] for i in items) >= y[j])
for i in items:
    for j in resources:
        model.Add(x[(i, j)] <= y[j])

# Objective
model.Minimize(sum(y[j] for j in resources))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = max_time
solver.parameters.num_search_workers = num_workers
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    used_resources = [j for j in resources if solver.Value(y[j]) == 1]
    assignments = {j: [i for i in items if solver.Value(x[(i, j)]) == 1] for j in used_resources}
    # Validate capacity constraints
    for j in used_resources:
        total_weight = sum(weight[i] for i in assignments[j])
        assert total_weight <= capacity[j]
else:
    # Handle no solution found
    pass
```

### Common Pitfalls
- Misinterpreting solver status; `FEASIBLE` does not guarantee optimality.
- Not using `solver.Value()` correctly, leading to type errors.
- Overlooking the need to scale weights/capacities to integers for CP-SAT.

# Workflow 2 (MIP with Pyomo and CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for algebraic modeling and CBC as the MIP solver. It is ideal for problems requiring a flexible, equation-based interface and integration with open-source solvers.

### Step 1 - Declare Sets and Parameters
- Define Pyomo sets for `items` and `resources`.
- Define parameters for `weight` (indexed by items) and `capacity` (indexed by resources).

### Step 2 - Create Binary Variables
- Declare a binary variable `model.x` indexed over `(items, resources)` for assignments.
- Declare a binary variable `model.y` indexed over `resources` for usage.

### Step 3 - Build Constraints Algebraically
- Add assignment cover constraint using a Pyomo `Constraint` rule.
- Add capacity knapsack constraint, optionally multiplied by `model.y[j]`.
- Add linking constraints `model.x[i,j] <= model.y[j]`.

### Step 4 - Define Objective
- Set the objective to minimize the sum of `model.y` variables.

### Formulation Template
```json
{
  "sets": [
    "I (items)",
    "J (resources)"
  ],
  "parameters": [
    {"name": "weight", "index": "I", "type": "float"},
    {"name": "capacity", "index": "J", "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["I", "J"], "type": "binary"},
    {"name": "y", "index": "J", "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in J)"
  },
  "constraints": [
    {"name": "assign_each", "expression": "sum(x[i,j] for j in J) == 1 for each i in I"},
    {"name": "respect_capacity", "expression": "sum(weight[i] * x[i,j] for i in I) <= capacity[j] * y[j] for each j in J"},
    {"name": "link_assign_to_use", "expression": "x[i,j] <= y[j] for each i in I, j in J"}
  ]
}
```

### Common Pitfalls
- Using `capacity[j] * y[j]` in the knapsack constraint can make the model non-convex for some solvers; CBC handles it, but verify solver compatibility.
- Incorrectly indexing parameters within Pyomo rule functions.
- Not pre-calculating a lower bound (e.g., `ceil(total_weight / max_capacity)`) to validate solver results.

## Solving stage

### Strategy Overview
The solving stage involves instantiating the Pyomo model, configuring the CBC solver, solving, and rigorously checking termination conditions before extracting results.

### Step 1 - Instantiate Model and Solve
- Build the ConcreteModel using the defined formulation.
- Create a solver instance (e.g., `pyo.SolverFactory('cbc')`).

### Step 2 - Configure Solver Options
- Set solver options such as time limit (`seconds`), optimality gap (`ratio`), and number of threads (`threads`).

### Step 3 - Execute and Check Status
- Call `solver.solve(model)` and capture the results object.
- Check both the solver status (`SolverStatus.ok`) and termination condition (`optimal` or `feasible`).

### Step 4 - Extract and Package Solution
- Extract variable values using `pyo.value(var)`.
- Package the solution into a structured format (e.g., dictionary) for verification and reporting.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=resources)

model.weight = pyo.Param(model.I, initialize=weight_dict)
model.capacity = pyo.Param(model.J, initialize=capacity_dict)

model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)
model.y = pyo.Var(model.J, domain=pyo.Binary)

def assign_rule(m, i):
    return sum(m.x[i, j] for j in m.J) == 1
model.assign = pyo.Constraint(model.I, rule=assign_rule)

def capacity_rule(m, j):
    return sum(m.weight[i] * m.x[i, j] for i in m.I) <= m.capacity[j] * m.y[j]
model.capacity_con = pyo.Constraint(model.J, rule=capacity_rule)

def link_rule(m, i, j):
    return m.x[i, j] <= m.y[j]
model.link = pyo.Constraint(model.I, model.J, rule=link_rule)

model.obj = pyo.Objective(expr=sum(model.y[j] for j in model.J), sense=pyo.minimize)

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = time_limit
solver.options['ratio'] = optimality_gap
solver.options['threads'] = num_threads

results = solver.solve(model)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    used_resources = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
    assignments = {j: [i for i in model.I if pyo.value(model.x[i, j]) > 0.5] for j in used_resources}
    # Validate objective value
    assert len(used_resources) == pyo.value(model.obj)
else:
    # Handle solver failure or infeasibility
    pass
```

### Common Pitfalls
- Confusing `SolverStatus` with `TerminationCondition`; both must be checked.
- Using `pyo.value()` on variables before solving, which raises an error.
- Not setting an optimality gap (`ratio`) when seeking exact solutions.
