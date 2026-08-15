---
name: Bin Packing with Activation Variables
description: |
  Model and solve assignment problems with capacity constraints to minimize resource count using binary assignment and activation variables, with workflows for CP-SAT and MIP solvers.
---

# Workflow 1 (CP-SAT via OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses the OR-Tools CP-SAT solver, which is designed for constraint programming and integer problems. The model employs binary variables for assignment and resource activation, with linear constraints linking them. The CP-SAT API is direct and efficient for this problem class.

### Step 1 - Define Core Variables
- Create a binary decision variable `assign[i][j]` for each item `i` and resource `j` to indicate assignment.
- Create a binary variable `use[j]` for each resource `j` to track whether it is utilized.

### Step 2 - Enforce Assignment Exclusivity
- For each item `i`, add a constraint that the sum of `assign[i][j]` over all resources `j` equals 1. This ensures each item is assigned to exactly one resource.

### Step 3 - Link Capacity and Activation
- For each resource `j`, add a capacity constraint: the sum of `weight[i] * assign[i][j]` over all items `i` must be less than or equal to `capacity * use[j]`. This deactivates the constraint for unused resources.
- Optionally, add explicit linking constraints `assign[i][j] <= use[j]` for all `i, j` to improve solver performance, though they are logically implied.

### Step 4 - Set Objective
- Formulate the objective to minimize the sum of `use[j]` over all resources `j`.

### Formulation Template
```json
{
  "sets": [
    {"name": "items", "description": "Set of items to be assigned."},
    {"name": "resources", "description": "Set of available resources (e.g., bins, trucks)."}
  ],
  "parameters": [
    {"name": "weight_i", "description": "Weight/size of item i.", "index": "i in items"},
    {"name": "capacity", "description": "Capacity limit per resource."}
  ],
  "decision_variables": [
    {"name": "assign_ij", "description": "1 if item i is assigned to resource j.", "type": "binary", "index": "i in items, j in resources"},
    {"name": "use_j", "description": "1 if resource j is used.", "type": "binary", "index": "j in resources"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(use_j for j in resources)"
  },
  "constraints": [
    {"name": "assignment", "expression": "sum(assign_ij for j in resources) == 1", "index": "i in items"},
    {"name": "capacity", "expression": "sum(weight_i * assign_ij for i in items) <= capacity * use_j", "index": "j in resources"},
    {"name": "linking", "expression": "assign_ij <= use_j", "index": "i in items, j in resources"}
  ]
}
```

### Common Pitfalls
- Forgetting to multiply `capacity` by `use[j]` in the capacity constraint, which incorrectly imposes a capacity limit on unused resources.
- Using an insufficient number of resources as an upper bound, which can make the problem infeasible; a safe bound is the number of items.
- Omitting explicit linking constraints (`assign[i][j] <= use[j]`) can sometimes slow down the solver's search.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver. Configure search parameters for performance and reproducibility, solve, and then extract and validate the solution.

### Step 1 - Instantiate Model and Variables
- Create a CP-SAT model instance.
- Instantiate the `assign` and `use` variables as Boolean variables using `model.NewBoolVar()`.

### Step 2 - Add Constraints and Objective
- Add the assignment, capacity, and optional linking constraints using `model.Add()`.
- Set the objective using `model.Minimize()`.

### Step 3 - Configure and Run Solver
- Set a time limit with `model.Proto().max_time_in_seconds`.
- Set the number of parallel search workers with `model.Proto().num_search_workers`.
- Set a fixed random seed for reproducibility.
- Call the solver with `solver.Solve(model)`.

### Step 4 - Extract and Verify Solution
- Check the solver status (`OPTIMAL`, `FEASIBLE`, etc.).
- For each resource `j`, check if `use[j]` is true (value > 0.5) to identify used resources.
- For each item `i`, find the resource `j` where `assign[i][j]` is true to reconstruct assignments.
- Validate the solution by checking all constraints are satisfied (e.g., capacity limits, assignment exclusivity).

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
num_items = len(items)
num_resources = len(resources)
assign = [[model.NewBoolVar(f"assign_{i}_{j}") for j in range(num_resources)] for i in range(num_items)]
use = [model.NewBoolVar(f"use_{j}") for j in range(num_resources)]

# assignment constraints
for i in range(num_items):
    model.Add(sum(assign[i][j] for j in range(num_resources)) == 1)
# capacity and linking constraints
for j in range(num_resources):
    model.Add(sum(weight[i] * assign[i][j] for i in range(num_items)) <= capacity * use[j])
    for i in range(num_items):
        model.Add(assign[i][j] <= use[j])
# objective
model.Minimize(sum(use[j] for j in range(num_resources)))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    used_resources = [j for j in range(num_resources) if solver.Value(use[j]) > 0.5]
    assignments = {}
    for i in range(num_items):
        for j in range(num_resources):
            if solver.Value(assign[i][j]) > 0.5:
                assignments[i] = j
                break
    # validation and output
else:
    # handle failure
```

### Common Pitfalls
- Not checking solver status before extracting solution values, which can lead to errors.
- Using floating-point comparison (`==`) for binary variable values; use a tolerance (e.g., `> 0.5`).
- Setting an overly restrictive time limit that prevents finding a feasible solution.

# Workflow 2 (MIP via Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to model the problem as a Mixed-Integer Program (MIP) and solves it with a commercial or open-source MIP solver (e.g., Gurobi, CBC). Pyomo provides an algebraic modeling interface suitable for larger-scale or more complex variants.

### Step 1 - Define Abstract Sets and Parameters
- Declare sets for `items` and `resources`.
- Declare parameters for `weight` (indexed by items) and `capacity`.

### Step 2 - Define Binary Variables
- Define `assign[i,j]` as a binary variable for assignment.
- Define `use[j]` as a binary variable for resource activation.

### Step 3 - Formulate Constraints
- Add assignment constraints: sum of `assign[i,j]` over `j` equals 1 for each `i`.
- Add capacity constraints: sum of `weight[i] * assign[i,j]` over `i` is less than or equal to `capacity * use[j]` for each `j`.
- Optionally add linking constraints `assign[i,j] <= use[j]` for all `i,j`.

### Step 4 - Set Objective
- Minimize the sum of `use[j]` over all resources `j`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of items."},
    {"name": "J", "description": "Set of resources."}
  ],
  "parameters": [
    {"name": "w_i", "description": "Weight of item i.", "index": "i in I"},
    {"name": "C", "description": "Capacity per resource."}
  ],
  "decision_variables": [
    {"name": "x_ij", "description": "Assignment variable.", "type": "binary", "index": "i in I, j in J"},
    {"name": "y_j", "description": "Resource usage variable.", "type": "binary", "index": "j in J"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y_j for j in J)"
  },
  "constraints": [
    {"name": "assign_each", "expression": "sum(x_ij for j in J) == 1", "index": "i in I"},
    {"name": "capacity_limit", "expression": "sum(w_i * x_ij for i in I) <= C * y_j", "index": "j in J"},
    {"name": "link", "expression": "x_ij <= y_j", "index": "i in I, j in J"}
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters or variables, leading to model construction errors.
- Using a MIP solver without setting appropriate optimality gap (`MIPGap`), which may return suboptimal solutions.
- Not providing an initial upper bound for the number of resources, which can slow down the solver.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver. Configure solver options for performance and determinism, solve, and then extract results with robust checks for solver status and solution feasibility.

### Step 1 - Build Concrete Model
- Instantiate a concrete Pyomo model.
- Populate the model with data (sets, parameters).

### Step 2 - Select and Configure Solver
- Choose a MIP solver (e.g., `'gurobi'`, `'cbc'`).
- Set solver options: time limit (`TimeLimit`), optimality gap (`MIPGap`), number of threads (`Threads`), and random seed (`Seed`) for reproducibility.

### Step 3 - Solve and Check Status
- Invoke the solver.
- Check the solver status (`SolverStatus`) and termination condition (`TerminationCondition`). Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 4 - Extract and Validate Solution
- Retrieve variable values using `model.x_ij.get_values()` and `model.y_j.get_values()`.
- Identify used resources where `y_j > 0.5`.
- Reconstruct assignments from `x_ij` values.
- Validate by recalculating constraint satisfaction (e.g., total weight per resource <= capacity).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_items))
model.J = pyo.Set(initialize=range(num_resources))
model.w = pyo.Param(model.I, initialize=lambda m, i: weight[i])
model.C = pyo.Param(initialize=capacity)
model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)
model.y = pyo.Var(model.J, domain=pyo.Binary)

def assign_rule(m, i):
    return sum(m.x[i, j] for j in m.J) == 1
model.assign_con = pyo.Constraint(model.I, rule=assign_rule)

def capacity_rule(m, j):
    return sum(m.w[i] * m.x[i, j] for i in m.I) <= m.C * m.y[j]
model.capacity_con = pyo.Constraint(model.J, rule=capacity_rule)

def link_rule(m, i, j):
    return m.x[i, j] <= m.y[j]
model.link_con = pyo.Constraint(model.I, model.J, rule=link_rule)

model.obj = pyo.Objective(expr=sum(model.y[j] for j in model.J), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition
if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    used_resources = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
    assignments = {}
    for i in model.I:
        for j in model.J:
            if pyo.value(model.x[i, j]) > 0.5:
                assignments[i] = j
                break
    # validation and output
else:
    # handle failure
```

### Common Pitfalls
- Not checking both `SolverStatus` and `TerminationCondition`, which can mask solver failures.
- Assuming variable values exist when the solver did not find a feasible solution.
- Using default solver settings that may be suboptimal for the problem size or structure.
