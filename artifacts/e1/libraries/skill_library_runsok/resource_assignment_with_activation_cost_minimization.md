---
name: Resource Assignment with Activation Cost Minimization
description: |
  Model and solve assignment problems with resource activation costs using binary variables for assignments and resource usage, with constraints for exclusivity, capacity, and logical linking.
---

# Workflow 1 (CP-SAT via OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, designed for combinatorial problems with Boolean and integer variables. It leverages the solver's native efficiency for binary decision logic and linear constraints, making it suitable for problems where direct minimization of resource count is the primary goal.

### Step 1 - Define Core Variables
- Create a binary decision variable `assign[i][j]` for each item `i` and resource `j` to represent the assignment.
- Create a binary indicator variable `used[j]` for each resource `j` to track its activation status.

### Step 2 - Implement Assignment and Capacity Logic
- Enforce assignment exclusivity: For each item `i`, the sum of `assign[i][j]` over all resources `j` must equal 1.
- Enforce capacity limits: For each resource `j`, the sum of `weight[i] * assign[i][j]` over all items `i` must be less than or equal to the `capacity`.
- Add linking constraints: For each item `i` and resource `j`, add `assign[i][j] <= used[j]`. Optionally, add `used[j] <= sum(assign[i][j] for i)` to tighten the formulation.

### Step 3 - Formulate the Objective
- Define the objective to minimize the total number of activated resources: `minimize sum(used[j] for j in resources)`.

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
    "expression": "sum(used[resources])"
  },
  "constraints": [
    "assignment_exclusivity: for i in items: sum(assign[i][j] for j in resources) == 1",
    "capacity_limit: for j in resources: sum(weight[i] * assign[i][j] for i in items) <= capacity",
    "linking_lower: for i in items, j in resources: assign[i][j] <= used[j]",
    "linking_upper (optional): for j in resources: used[j] <= sum(assign[i][j] for i in items)"
  ]
}
```

### Common Pitfalls
- Forgetting the linking constraints, which can lead to `used[j] = 0` even when assignments exist for resource `j`.
- Using a large, fixed number of potential resources without an upper bound heuristic, which can increase solve time unnecessarily.
- Not setting a time limit or optimality gap, which may cause the solver to run indefinitely on large instances.

## Solving stage

### Strategy Overview
The solving stage involves configuring the CP-SAT solver with performance-oriented parameters, executing the solve, and rigorously extracting and validating the solution. Emphasis is placed on checking solver status and verifying logical consistency of the results.

### Step 1 - Configure Solver and Solve
- Instantiate the CP-SAT solver.
- Set key parameters: `max_time_in_seconds` for a time limit, `num_search_workers` for parallel solving, and `random_seed` for reproducibility.
- Invoke the solver's `Solve()` method.

### Step 2 - Extract and Validate Solution
- Check the solver status (`OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`).
- If feasible, extract values for `used[j]` and `assign[i][j]` using a threshold (e.g., `> 0.5`).
- Perform verification: Ensure each item is assigned exactly once, capacity limits are respected, and `used[j]` is 1 if and only if at least one `assign[i][j]` is 1.

### Step 3 - Report Results
- Output a human-readable summary listing active resources and their assigned items.
- Provide a structured output (e.g., JSON) containing the solution status, objective value, and detailed assignments for automated processing.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# Create variables: assign_vars[i][j], used_vars[j] as BoolVar
# Add constraints: assignment_exclusivity, capacity_limit, linking
# Set objective: model.Minimize(sum(used_vars))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    active_resources = [j for j in resources if solver.Value(used_vars[j]) > 0.5]
    assignments = {(i,j): solver.Value(assign_vars[i][j]) for i in items for j in resources}
    # ... validation and reporting
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Assuming `OPTIMAL` status without checking, potentially missing suboptimal feasible solutions.
- Not using a threshold when extracting binary variable values from the solver's floating-point representation.
- Omitting solution verification, which can lead to downstream errors if the solver returns an inconsistent solution.

# Workflow 2 (MIP via Pyomo with CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for algebraic modeling and the CBC solver via a generic MIP interface. It is suited for environments where a high-level, equation-based modeling language is preferred, and integration with a broader optimization ecosystem is needed.

### Step 1 - Declare Model Components
- Define abstract sets for `items` and `resources`.
- Declare parameters: `weight` for each item and scalar `capacity`.
- Define binary decision variables: `assign[i,j]` and `used[j]` using Pyomo's `Var` object with domain `Binary`.

### Step 2 - Construct Constraints Algebraically
- Build the assignment exclusivity constraint using a `ConstraintList` or a rule over the `items` set.
- Formulate the capacity constraint as a linear inequality for each resource `j`.
- Implement the linking constraint using inequality rules: `model.used[j] >= model.assign[i,j]` for all `i,j`.

### Step 3 - Set the Objective
- Define the objective expression as the summation of `used[j]` over all resources.
- Set the model's objective sense to minimize.

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
    "expression": "sum(used[resources])"
  },
  "constraints": [
    "assignment_exclusivity: for i in items: sum(assign[i][j] for j in resources) == 1",
    "capacity_limit: for j in resources: sum(weight[i] * assign[i][j] for i in items) <= capacity",
    "linking: for i in items, j in resources: assign[i][j] <= used[j]"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters or variables within Pyomo constraint rules, leading to runtime errors.
- Creating a concrete model with a very large number of potential resources without providing an upper bound, resulting in a bloated model.
- Neglecting to deactivate the solver output log (`tee=False`) when running in automated pipelines, causing excessive console output.

## Solving stage

### Strategy Overview
The solving stage focuses on using Pyomo's solver manager to interface with CBC, configuring solver options for performance, and handling the solver results object to extract and verify the solution.

### Step 1 - Configure and Execute Solver
- Instantiate a solver object (e.g., `SolverFactory('cbc')`).
- Set solver options: `seconds` for time limit, `ratio` for optimality gap tolerance, and `threads` for parallel processing.
- Call `solve(model, options=...)` and capture the results object.

### Step 2 - Check Status and Extract Solution
- Inspect both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`).
- If optimal or feasible, load the solution into the model instance.
- Extract variable values using a threshold (e.g., `value(model.used[j]) > 0.5`) and build the assignment mapping.

### Step 3 - Validate and Package Output
- Perform feasibility checks: verify assignment completeness and capacity adherence.
- Compute derived metrics, such as total weight per resource, for reporting.
- Structure the output into a dictionary or JSON-serializable object containing key results.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items)
model.resources = pyo.Set(initialize=resources)
model.weight = pyo.Param(model.items, initialize=weight_dict)
model.capacity = pyo.Param(initialize=capacity)
model.assign = pyo.Var(model.items, model.resources, domain=pyo.Binary)
model.used = pyo.Var(model.resources, domain=pyo.Binary)
# Define constraints via rules or ConstraintList
# Set objective: model.obj = pyo.Objective(expr=sum(model.used[j] for j in model.resources), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, options={'seconds': 30, 'ratio': 0.0, 'threads': -1})

if results.solver.termination_condition == pyo.TerminationCondition.optimal and results.solver.status == pyo.SolverStatus.ok:
    # Extract solution
    for j in model.resources:
        if pyo.value(model.used[j]) > 0.5:
            # ... find assigned items
    # ... validation and reporting
else:
    print("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Confusing `solver.status` (checkpoint) with `termination_condition` (result), leading to incorrect interpretation of solve outcomes.
- Forgetting to load the solution (`model.solutions.load_from(results)`) before querying variable values in some Pyomo workflows.
- Not providing an absolute path or ensuring the solver executable (CBC) is in the system PATH, causing a `SolverFactory` error.
