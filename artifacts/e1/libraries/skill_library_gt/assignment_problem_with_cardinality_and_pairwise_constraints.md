---
name: Assignment Problem with Cardinality and Pairwise Constraints
description: |
  Model and solve constrained assignment problems with binary variables, cardinality limits, pairwise exclusions, and linear cost minimization using modern MIP/CP-SAT solvers.

---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem using the CP-SAT solver from Google OR-Tools, which natively handles binary variables and linear constraints efficiently. This approach is well-suited for problems where pairwise constraints are directly expressed as linear sums without requiring big-M formulations.

### Step 1 - Define Sets and Parameters
- Define the two sets of elements to be matched (e.g., `items` and `slots`).
- Define a cost parameter `cost[(i, j)]` for each potential assignment, using interpolation or default values for incomplete data.
- Define the required total number of assignments `k`.
- Define a list of pairwise exclusion constraints, each as a tuple `(i1, j1, i2, j2, max_sum)`.

### Step 2 - Create Binary Decision Variables
- Create a binary decision variable `x[(i, j)]` for each potential assignment using `model.NewBoolVar()`.
- Store variables in a dictionary keyed by `(i, j)` for clarity and easy access.

### Step 3 - Formulate Cardinality Constraints
- Add `assignment_cardinality`: For each item `i`, `sum(x[(i, j)] for j in slots) <= 1`.
- Add `matching_cardinality`: For each slot `j`, `sum(x[(i, j)] for i in items) <= 1`.
- Add global cardinality: `sum(x[(i, j)] for all i,j) == k`.

### Step 4 - Add Pairwise Exclusion Constraints
- For each pairwise constraint `(i1, j1, i2, j2, max_sum)`, add `x[(i1, j1)] + x[(i2, j2)] <= max_sum` directly to the model.

### Step 5 - Set Linear Objective
- Define the objective as the minimization of total cost: `sum(cost[(i, j)] * x[(i, j)] for all i,j)`.
- Use `model.Minimize()` to set the objective.

### Formulation Template
```json
{
  "sets": ["items", "slots"],
  "parameters": [
    {"name": "cost", "type": "dict", "keys": ["item", "slot"], "description": "Cost of assignment"},
    {"name": "k", "type": "int", "description": "Required total number of assignments"},
    {"name": "pairwise_constraints", "type": "list", "description": "List of (i1, j1, i2, j2, max_sum)"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["item", "slot"], "description": "1 if item assigned to slot"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j] * x[i][j] for i in items for j in slots )"
  },
  "constraints": [
    {"name": "assign_once", "expression": "sum( x[i][j] for j in slots ) <= 1 for each i in items"},
    {"name": "receive_once", "expression": "sum( x[i][j] for i in items ) <= 1 for each j in slots"},
    {"name": "total_assign", "expression": "sum( x[i][j] for i in items for j in slots ) == k"},
    {"name": "pairwise_excl", "expression": "x[i1][j1] + x[i2][j2] <= max_sum for each (i1,j1,i2,j2,max_sum) in pairwise_constraints"}
  ]
}
```

### Common Pitfalls
- Forgetting to define a cost for every `(i, j)` pair; use interpolation or a large penalty for unknown/infeasible assignments.
- Setting `max_sum` to 2 in pairwise constraints, which is redundant for binary variables; only `max_sum = 1` is meaningful for exclusion.
- Not handling solver status correctly; always check for `OPTIMAL` or `FEASIBLE` before extracting a solution.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with appropriate performance parameters, extract the solution, and validate it against the problem constraints. Ensure robust handling of incomplete data and solver failures.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.parameters.max_time_in_seconds = <time_limit>`.
- Enable parallelism: `solver.parameters.num_search_workers = <num_workers>`.
- Set a random seed for reproducibility: `solver.parameters.random_seed = <seed>`.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status: `status = solver.Status()`.
- Proceed only if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`.

### Step 3 - Extract Solution
- Iterate over all `(i, j)` pairs. If `solver.Value(x[(i, j)]) == 1`, record the assignment.
- Compute the total cost from the objective value: `total_cost = solver.ObjectiveValue()`.

### Step 4 - Validate Solution
- Verify the total number of assignments equals `k`.
- Check that no item is assigned to more than one slot.
- Check that no slot receives more than one item.
- Verify all pairwise exclusion constraints are satisfied.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... define variables, constraints, objective as per Modeling stage

# Solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
solver.parameters.random_seed = 42

status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Objective value: {solver.ObjectiveValue()}")
    assignments = []
    for i in items:
        for j in slots:
            if solver.Value(x[(i, j)]) == 1:
                assignments.append((i, j))
    # Validate assignments (optional)
    # ...
    print(f"RESULT:{solver.ObjectiveValue()}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not setting a time limit, which can cause the solver to run indefinitely on large or infeasible instances.
- Assuming the solver always finds an optimal solution; always handle the `FEASIBLE` status for suboptimal results.
- Misinterpreting the objective value when costs are interpolated or estimated; it may represent a bound rather than an exact cost.

# Workflow 2 (MIP with Pyomo and Gurobi)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Programming (MIP) model using Pyomo, targeting solvers like Gurobi. This approach provides fine-grained control over solver parameters and is ideal for users familiar with algebraic modeling languages.

### Step 1 - Define Abstract Sets and Parameters
- Define Pyomo `Set` objects for `items` and `slots`.
- Define a `Param` for costs, indexed over the Cartesian product of the sets.
- Define scalar parameter `k` for the total assignment count.
- Define a structured list for pairwise constraints.

### Step 2 - Create Binary Variables
- Create a Pyomo `Var` `model.x` indexed by `(item, slot)` with domain `pyo.Binary`.

### Step 3 - Implement Standard Assignment Constraints
- Add constraint for assignment cardinality: `sum(model.x[i, j] for j in slots) <= 1` for each `i`.
- Add constraint for matching cardinality: `sum(model.x[i, j] for i in items) <= 1` for each `j`.
- Add global cardinality constraint: `sum(model.x[i, j] for i,j) == k`.

### Step 4 - Incorporate Pairwise Constraints
- For each pairwise constraint `(i1, j1, i2, j2, max_sum)`, add `model.x[i1, j1] + model.x[i2, j2] <= max_sum` using a rule or a direct loop.

### Step 5 - Define Linear Objective
- Define the objective to minimize total cost: `sum(cost[i, j] * model.x[i, j] for i,j)`.

### Formulation Template
```json
{
  "sets": ["items", "slots"],
  "parameters": [
    {"name": "cost", "type": "Param", "indices": ["item", "slot"], "description": "Cost matrix"},
    {"name": "k", "type": "Param", "description": "Exact number of assignments required"},
    {"name": "pairwise_constraints", "type": "list", "description": "List of dicts with keys i1, j1, i2, j2, max_sum"}
  ],
  "decision_variables": [
    {"name": "x", "type": "Binary", "indices": ["item", "slot"], "description": "Assignment decision"}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum( cost[i,j] * x[i,j] for i in items for j in slots )"
  },
  "constraints": [
    {"name": "assign_once", "expression": "sum( x[i,j] for j in slots ) <= 1, forall i in items"},
    {"name": "receive_once", "expression": "sum( x[i,j] for i in items ) <= 1, forall j in slots"},
    {"name": "total_assign", "expression": "sum( x[i,j] for i in items for j in slots ) == k"},
    {"name": "pairwise", "expression": "x[i1,j1] + x[i2,j2] <= max_sum, for each pairwise constraint"}
  ]
}
```

### Common Pitfalls
- Using `<= 1` constraints for both sets without the global `== k` constraint, which may lead to zero assignments.
- Incorrectly indexing parameters or variables in Pyomo rules, leading to runtime errors.
- Not preprocessing pairwise constraints where `max_sum > 1`, which are redundant for binary variables.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external MIP solver (e.g., Gurobi), configure solver options for performance and reproducibility, and implement robust solution extraction and validation.

### Step 1 - Select Solver and Set Options
- Instantiate a solver object: `solver = pyo.SolverFactory('gurobi')`.
- Set solver options: `TimeLimit`, `MIPGap`, `Threads`, `Seed`.

### Step 2 - Solve and Check Termination Condition
- Call `results = solver.solve(model, tee=False)`.
- Check the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`).
- Proceed if status is `SolverStatus.ok` and termination is `optimal` or `feasible`.

### Step 3 - Extract and Validate Assignments
- Iterate over `model.x`. If `pyo.value(model.x[i, j]) > 0.5`, record the assignment.
- Compute the total cost from the objective value: `obj_val = pyo.value(model.obj)`.
- Programmatically verify all cardinality and pairwise constraints are satisfied by the extracted solution.

### Step 4 - Handle Incomplete Data Scenarios
- If costs were estimated (e.g., using lower bounds), note that the objective value is an optimistic bound.
- For robust validation, resolve with different cost assumptions (e.g., upper bounds) to test solution stability.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items)
model.slots = pyo.Set(initialize=slots)
model.x = pyo.Var(model.items, model.slots, domain=pyo.Binary)
# ... add constraints and objective as per Modeling stage

# Solve with status / termination checks
solver = SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    obj_val = pyo.value(model.obj)
    assignments = []
    for i in model.items:
        for j in model.slots:
            if pyo.value(model.x[i, j]) > 0.5:
                assignments.append((i, j))
    # Validate assignments
    # ...
    print(f"RESULT:{obj_val}")
else:
    print("Solver failed to find a feasible solution.")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, which can lead to interpreting infeasible or error states as successes.
- Extracting variable values without comparing to `0.5` due to floating-point precision in some solvers.
- Forgetting to set `MIPGap` to `0.0` when an optimal solution is required, potentially accepting suboptimal results.
