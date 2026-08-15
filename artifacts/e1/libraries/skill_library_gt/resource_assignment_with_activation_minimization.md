---
name: Resource Assignment with Activation Minimization
description: |
  Model and solve assignment problems where items must be assigned to resources with capacity, minimizing the number of resources used, using binary assignment and activation variables.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
This workflow models the problem using OR-Tools' CP-SAT solver, which is designed for constraint programming and integer problems. It leverages native boolean logic for binary variables and linear constraints, focusing on a clean formulation with explicit variable linking.

### Step 1 - Define Variables
- Create a binary decision variable `assign[i][j]` for each item `i` and resource `j`, indicating assignment.
- Create a binary activation variable `used[j]` for each resource `j`, indicating if the resource is utilized.

### Step 2 - Formulate Constraints
- Add an **Assignment Exclusivity** constraint: `sum(assign[i][j] for j in resources) == 1` for each item `i`.
- Add a **Capacity Limit** constraint: `sum(weight[i] * assign[i][j] for i in items) <= capacity` for each resource `j`.
- Add **Linking Constraints**: `assign[i][j] <= used[j]` for all `i,j` to ensure usage is activated by any assignment. Optionally add `used[j] <= sum(assign[i][j] for i in items)` for clarity, though minimization often enforces this.

### Step 3 - Define Objective
- Set the objective to minimize the total number of used resources: `minimize sum(used[j] for j in resources)`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "resources"
  ],
  "parameters": [
    "weight[items]",
    "capacity"
  ],
  "decision_variables": [
    "assign[items][resources] ∈ {0,1}",
    "used[resources] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(used[j] for j in resources)"
  },
  "constraints": [
    "for i in items: sum(assign[i][j] for j in resources) == 1",
    "for j in resources: sum(weight[i] * assign[i][j] for i in items) <= capacity",
    "for i in items, j in resources: assign[i][j] <= used[j]"
  ]
}
```

### Common Pitfalls
- Forgetting to link assignment variables to usage variables, which can lead to incorrect objective values.
- Using an insufficient number of resources in the model, causing infeasibility; ensure the resource set is large enough (e.g., equal to number of items).
- Not adding the reverse linking constraint (`used[j] <= sum(assign[i][j])`) can sometimes be acceptable due to the minimization objective, but its absence may affect solver propagation.

## Solving stage

### Strategy Overview
This stage involves configuring the CP-SAT solver with practical limits for time and parallelism, solving the model, and rigorously extracting and validating the solution.

### Step 1 - Configure Solver
- Instantiate the CP-SAT solver.
- Set practical parameters: `max_time_in_seconds` (e.g., 30), `num_search_workers` (e.g., 8), `random_seed` (e.g., 42), and `relative_gap_limit` (e.g., 0.0 for optimality).

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the solver status (`OPTIMAL` or `FEASIBLE`) before proceeding to solution extraction.

### Step 3 - Extract Solution
- For each resource `j`, check if `used[j]` is true (value > 0.5) to identify active resources.
- For each active resource, iterate over items `i` and check if `assign[i][j]` is true to build the assignment list.
- Calculate derived metrics (e.g., total weight per resource) for verification.

### Step 4 - Validate and Output
- Validate the solution: ensure no capacity violations and each item is assigned exactly once.
- Output a human-readable summary (objective value, assignments) and a structured JSON payload for automated processing.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... create variables, add constraints, set objective ...

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = -0.0  # For optimality

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    used_resources = [j for j in resources if solver.Value(used[j]) > 0.5]
    assignments = {}
    for j in used_resources:
        assigned_items = [i for i in items if solver.Value(assign[i][j]) > 0.5]
        assignments[j] = assigned_items
    # ... validation and output ...
else:
    # Handle no solution found
    print("No solution found.")
```

### Common Pitfalls
- Extracting variable values without checking solver status first, leading to errors.
- Using a loose optimality gap (`relative_gap_limit > 0`) when proof of optimality is required.
- Not performing post-solution validation, which can miss subtle constraint violations.

# Workflow 2 (MIP Solver via Pyomo)

## Modeling stage

### Strategy Overview
This workflow models the problem using Pyomo, an algebraic modeling language, targeting Mixed-Integer Programming (MIP) solvers like CBC or SCIP. It emphasizes a declarative constraint style and integration with the broader Pyomo ecosystem.

### Step 1 - Define Sets and Parameters
- Define Pyomo sets for `items` and `resources`.
- Define parameters for `weight` (indexed by items) and `capacity`.

### Step 2 - Create Variables
- Create a binary variable `x[i,j]` for assignment decisions.
- Create a binary variable `y[j]` for resource activation.

### Step 3 - Formulate Constraints
- Add **Assignment Constraint**: `sum(x[i,j] for j in resources) == 1` for each item `i`.
- Add **Capacity Constraint**: `sum(weight[i] * x[i,j] for i in items) <= capacity * y[j]` for each resource `j`. This makes capacity conditional on activation.
- Add **Linking Constraints**: `y[j] >= x[i,j]` for all `i,j` and `y[j] <= sum(x[i,j] for i in items)` for all `j` to fully couple variables.

### Step 4 - Define Objective
- Define the objective to minimize total activation: `minimize sum(y[j] for j in resources)`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "resources"
  ],
  "parameters": [
    "weight[items]",
    "capacity"
  ],
  "decision_variables": [
    "x[items][resources] ∈ Binary",
    "y[resources] ∈ Binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in resources)"
  },
  "constraints": [
    "for i in items: sum(x[i,j] for j in resources) == 1",
    "for j in resources: sum(weight[i] * x[i,j] for i in items) <= capacity * y[j]",
    "for i in items, j in resources: y[j] >= x[i,j]",
    "for j in resources: y[j] <= sum(x[i,j] for i in items)"
  ]
}
```

### Common Pitfalls
- Using `capacity * y[j]` in the capacity constraint without ensuring `y[j]` is binary, which is automatically handled by Pyomo but must be verified in custom implementations.
- Omitting the upper-bound linking constraint (`y[j] <= sum(x[i,j])`), which can allow `y[j]=1` with no assignments, wasting resources without affecting feasibility.
- Defining sets or parameters incorrectly, leading to indexing errors during model construction.

## Solving stage

### Strategy Overview
This stage involves sending the Pyomo model to a MIP solver, configuring solver options, and handling the solution with checks for optimality and feasibility.

### Step 1 - Select and Configure Solver
- Instantiate a solver object (e.g., `SolverFactory('cbc')`).
- Set solver options: `seconds` for time limit, `ratio` (e.g., 0.0) for optimality gap, and `threads` for parallel processing.

### Step 2 - Solve and Check Termination
- Invoke the solver's `solve(model, ...)` method.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Process Solution
- Access variable values via `value(var)` or `var.value`.
- Use a threshold (e.g., `> 0.5`) to determine binary variable states.
- Build the assignment mapping and calculate per-resource utilization.

### Step 4 - Validate and Report
- Perform sanity checks: verify capacity limits and assignment completeness.
- Format results into a standard output structure for reporting and downstream use.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
# Set options
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
solver.options['threads'] = -1  # Use all available threads

results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                              pyo.TerminationCondition.feasible]):
    # Extract solution
    used_resources = [j for j in model.resources if pyo.value(model.y[j]) > 0.5]
    assignments = {}
    for j in used_resources:
        assigned_items = [i for i in model.items if pyo.value(model.x[i,j]) > 0.5]
        assignments[j] = assigned_items
    # ... validation and output ...
else:
    # Handle no solution found
    print("No solution found.")
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`/`feasible`); both must be checked.
- Not using a threshold when checking binary variable values due to floating-point precision.
- Failing to set appropriate solver options (like time limit or gap), which can lead to excessively long runs.
