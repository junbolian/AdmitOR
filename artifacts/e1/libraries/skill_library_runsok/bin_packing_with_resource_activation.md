---
name: Bin Packing with Resource Activation
description: |
  Model and solve assignment problems where items with weights must be assigned to capacity-limited resources, minimizing the count of resources used, using binary assignment and activation variables.
---

# Workflow 1 (CP-SAT for Exact Bin Packing)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Program (MIP) and solves it using a Constraint Programming/SAT (CP-SAT) solver, which is effective for combinatorial problems with binary variables and logical constraints. The core idea is to separate assignment decisions from resource activation.

### Step 1 - Define Variables
- Create binary assignment variables `assign[i][j]` for each item `i` and resource `j`. `assign[i][j] = 1` indicates the item is assigned to that resource.
- Create binary usage variables `used[j]` for each resource `j`. `used[j] = 1` indicates the resource is activated.

### Step 2 - Enforce Exclusive Assignment
- For each item `i`, add a constraint ensuring it is assigned to exactly one resource: `sum(assign[i][j] for all j) == 1`.

### Step 3 - Link Assignment to Capacity and Activation
- For each resource `j`, add a capacity constraint: `sum(weight[i] * assign[i][j] for all i) <= capacity * used[j]`. This forces `used[j]` to be 1 if any item is assigned and sets capacity to zero if the resource is unused.
- Optionally, add a logical linkage constraint for each `i`, `j`: `used[j] >= assign[i][j]` to strengthen the formulation.

### Step 4 - Formulate Objective
- Define the objective to minimize the total number of resources used: `minimize sum(used[j] for all j)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "J: set of resources"
  ],
  "parameters": [
    "weight[i ∈ I]: weight of item i",
    "capacity: capacity limit per resource"
  ],
  "decision_variables": [
    "assign[i ∈ I][j ∈ J] ∈ {0,1}",
    "used[j ∈ J] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(used[j] for j in J)"
  },
  "constraints": [
    "assignment: sum(assign[i][j] for j in J) == 1, for all i in I",
    "capacity: sum(weight[i] * assign[i][j] for i in I) <= capacity * used[j], for all j in J",
    "linkage: used[j] >= assign[i][j], for all i in I, j in J (optional)"
  ]
}
```

### Common Pitfalls
- Forgetting to link assignment variables to usage variables, which can lead to solutions where `used[j]=0` but `assign[i][j]=1`.
- Not calculating a lower bound (e.g., `ceil(total_weight / capacity)`) to quickly assess problem feasibility and solution quality.
- Using a resource count `J` that is too small, guaranteeing infeasibility; start with a generous upper bound.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, configured for optimality with time and resource limits. The focus is on robust solution extraction and validation.

### Step 1 - Instantiate Model and Variables
- Create a `CpModel` object.
- Instantiate `assign` and `used` as `NewBoolVar` variables.

### Step 2 - Add Constraints and Objective
- Add the assignment, capacity, and optional linkage constraints as defined in the modeling stage.
- Set the minimization objective using `model.Minimize()`.

### Step 3 - Configure and Run Solver
- Create a `CpSolver` instance.
- Set parameters: `max_time_in_seconds` for time limit, `num_search_workers` for parallelism, and `random_seed` for reproducibility.
- Call `solver.Solve(model)` and capture the status.

### Step 4 - Extract and Validate Solution
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- Extract the objective value and the values of `assign` and `used` variables (using `solver.Value()`).
- Programmatically verify all constraints: each item assigned once, capacity not exceeded, and `used[j]=1` iff any `assign[i][j]=1`.

### Code Usage
```python
from ortools.sat.python import cp_model

# Data placeholders
weights = [...]  # item weights
capacity = ...
n_items = len(weights)
n_resources = ...  # upper bound on resources needed

model = cp_model.CpModel()

# Variables
assign = [[model.NewBoolVar(f"assign_{i}_{j}") for j in range(n_resources)] for i in range(n_items)]
used = [model.NewBoolVar(f"used_{j}") for j in range(n_resources)]

# Constraints
for i in range(n_items):
    model.Add(sum(assign[i][j] for j in range(n_resources)) == 1)

for j in range(n_resources):
    model.Add(sum(weights[i] * assign[i][j] for i in range(n_items)) <= capacity * used[j])
    # Optional linkage
    for i in range(n_items):
        model.Add(used[j] >= assign[i][j])

# Objective
model.Minimize(sum(used[j] for j in range(n_resources)))

# Solver
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = -1
solver.parameters.random_seed = 42

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"RESULT:{solver.ObjectiveValue()}")
    # Extract and print assignment details
else:
    print("RESULT:INFEASIBLE_OR_UNKNOWN")
```

### Common Pitfalls
- Not handling the solver status correctly; `FEASIBLE` may be acceptable if optimality is not required.
- Extracting variable values without checking the solve status first, leading to errors.
- Setting an insufficient time limit for large instances; consider progressive solving or providing a good initial upper bound.

# Workflow 2 (Pyomo MIP for Flexible Backend Use)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for algebraic modeling, providing solver-agnostic formulation. It targets MIP solvers like Gurobi or CBC, offering flexibility for production environments with existing solver licenses. The modeling logic mirrors the first workflow but uses Pyomo's declarative syntax.

### Step 1 - Define Model and Sets
- Create a Pyomo `ConcreteModel`.
- Define `Set` objects for items `I` and resources `J`.

### Step 2 - Define Parameters and Variables
- Define `Param` for item `weight[i]` and scalar `capacity`.
- Define binary variables `x[i,j]` for assignment and `y[j]` for resource usage using `Var(within=Binary)`.

### Step 3 - Formulate Constraints
- Add assignment constraints: `sum(x[i,j] for j in J) == 1` for each `i`.
- Add capacity constraints: `sum(weight[i] * x[i,j] for i in I) <= capacity * y[j]` for each `j`.
- Optionally add activation constraints: `sum(x[i,j] for i in I) >= y[j]` for each `j`.

### Step 4 - Define Objective
- Set the objective to minimize total resource usage: `minimize sum(y[j] for j in J)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "J: set of resources"
  ],
  "parameters": [
    "weight[i ∈ I]: weight of item i",
    "capacity: capacity limit per resource"
  ],
  "decision_variables": [
    "x[i ∈ I, j ∈ J] ∈ {0,1}",
    "y[j ∈ J] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in J)"
  },
  "constraints": [
    "assignment: sum(x[i,j] for j in J) == 1, for all i in I",
    "capacity: sum(weight[i] * x[i,j] for i in I) <= capacity * y[j], for all j in J",
    "activation: sum(x[i,j] for i in I) >= y[j], for all j in J (optional)"
  ]
}
```

### Common Pitfalls
- Using Pyomo's `Set` initialization incorrectly (e.g., not providing an explicit index), which can lead to silent errors.
- Defining parameters or variables with incorrect domains (e.g., `Reals` instead of `Binary`).
- Forgetting to deactivate the optional `activation` constraint if it conflicts with the `capacity` constraint's logic (though both are generally compatible).

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver backend (e.g., Gurobi, CBC). The process involves configuring the solver, executing the solve, and robustly handling different termination conditions.

### Step 1 - Instantiate Solver and Set Options
- Use `SolverFactory` to instantiate the desired solver (e.g., `'gurobi'`, `'cbc'`).
- Set solver options: `MIPGap` for optimality tolerance, `TimeLimit` for runtime, `Threads` for parallelism, and `Seed` for reproducibility.

### Step 2 - Solve and Check Termination
- Call `solver.solve(model, tee=False)`.
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Validate Solution
- If the solve was successful, extract variable values using `value(x[i,j])` and `value(y[j])`.
- Validate the solution: check assignment exclusivity, capacity limits, and the link between `x` and `y`.
- Output the objective value and a structured assignment map.

### Step 4 - Handle Infeasibility or Errors
- If the solver reports infeasibility, output a clear error message and suggest checking the lower bound or constraint logic.
- Log solver statistics and termination details for debugging.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Data placeholders
weights = {...}  # dict i: weight
capacity = ...
I = list(weights.keys())
J = list(range(n_resources))  # upper bound

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I)
model.J = pyo.Set(initialize=J)

model.weight = pyo.Param(model.I, initialize=weights)
model.capacity = pyo.Param(initialize=capacity, mutable=True)

model.x = pyo.Var(model.I, model.J, within=pyo.Binary)
model.y = pyo.Var(model.J, within=pyo.Binary)

def assignment_rule(model, i):
    return sum(model.x[i, j] for j in model.J) == 1
model.assignment = pyo.Constraint(model.I, rule=assignment_rule)

def capacity_rule(model, j):
    return sum(model.weight[i] * model.x[i, j] for i in model.I) <= model.capacity * model.y[j]
model.capacity_con = pyo.Constraint(model.J, rule=capacity_rule)

def activation_rule(model, j):
    return sum(model.x[i, j] for i in model.I) >= model.y[j]
model.activation = pyo.Constraint(model.J, rule=activation_rule)  # Optional

model.obj = pyo.Objective(expr=sum(model.y[j] for j in model.J), sense=pyo.minimize)

solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 30
solver.options['Threads'] = -1
solver.options['Seed'] = 42

results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    print(f"RESULT:{pyo.value(model.obj)}")
    # Extract and print assignment details
else:
    print("RESULT:INFEASIBLE_OR_UNKNOWN")
    # Log results for debugging
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or limit-hit solutions.
- Extracting variable values with `value()` without first verifying the solve was successful.
- Using a solver name (e.g., `'gurobi'`) without the corresponding solver being installed or licensed in the environment.
