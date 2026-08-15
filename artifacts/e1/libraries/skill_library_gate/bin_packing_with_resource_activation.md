---
name: Bin Packing with Resource Activation
description: |
  Model and solve resource minimization problems with capacity constraints using binary assignment and activation variables, producing exact or feasible solutions with clear verification steps.
---

# Workflow 1 (CP-SAT with Explicit Linkage)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, which is designed for discrete optimization with Boolean logic. It models the problem with separate binary variables for assignment and resource usage, linking them via simple linear constraints. The capacity constraint is applied to all resources, regardless of usage status, simplifying the formulation.

### Step 1 - Define Core Variables
- Create binary assignment variables `x[i][j]` for each item `i` and resource `j` using `model.NewBoolVar()`.
- Create binary usage variables `y[j]` for each resource `j` using `model.NewBoolVar()` to track activation.

### Step 2 - Enforce Assignment and Capacity
- Add an exclusive assignment constraint for each item `i`: `sum(x[i][j] for j in resources) == 1`.
- Add a capacity constraint for each resource `j`: `sum(weight[i] * x[i][j] for i in items) <= capacity`.

### Step 3 - Link Assignment to Usage
- For each item `i` and resource `j`, add a logical implication constraint: `x[i][j] <= y[j]`. This ensures a resource is marked as used if any item is assigned to it.

### Step 4 - Formulate Objective
- Set the objective to minimize the total number of used resources: `minimize sum(y[j] for j in resources)`.

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
    "x[items][resources] ∈ {0,1}",
    "y[resources] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in resources)"
  },
  "constraints": [
    "sum(x[i][j] for j in resources) == 1, for all i in items",
    "sum(weight[i] * x[i][j] for i in items) <= capacity, for all j in resources",
    "x[i][j] <= y[j], for all i in items, j in resources"
  ]
}
```

### Common Pitfalls
- Forgetting to link assignment to usage, which can lead to unused resources being counted in the objective.
- Setting an insufficient number of resources, causing infeasibility; initialize with a safe upper bound like the number of items.
- Applying capacity constraints only to used resources adds unnecessary complexity; applying them universally is simpler and correct.

## Solving stage

### Strategy Overview
Solve the model using the CP-SAT solver, configuring it for exact solutions with time and resource limits. Focus on robust solution status checking and detailed result extraction for validation.

### Step 1 - Configure Solver
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds = time_limit`, `solver.parameters.num_search_workers = num_threads`, `solver.parameters.random_seed = seed`. For exact solutions, ensure `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Execute the solve: `status = solver.Solve(model)`.
- Verify the result: check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. If not, handle infeasibility by checking lower bounds (e.g., `ceil(total_weight / capacity)`).

### Step 3 - Extract and Verify Solution
- Retrieve the objective value: `obj_value = solver.ObjectiveValue()`.
- For each resource `j`, get usage status: `used = solver.Value(y[j])`.
- For each item `i`, find its assigned resource by checking `solver.Value(x[i][j])`.
- Optionally, compute the total weight per resource to validate against capacity constraints.

### Step 4 - Report Results
- Output the minimal number of resources used and the detailed assignment mapping.
- If optimal, test with one fewer resource to confirm minimality (e.g., reduce the resource set and re-solve).

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... variable and constraint creation ...

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters as needed
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Objective: {solver.ObjectiveValue()}")
    # Extract and process variable values using solver.Value(var)
else:
    print("No feasible solution found.")
    # Provide diagnostic info, e.g., lower bound
```

### Common Pitfalls
- Not checking both `OPTIMAL` and `FEASIBLE` statuses, potentially missing good solutions.
- Misinterpreting solver parameters (e.g., `relative_gap_limit` vs. `absolute_gap_limit`).
- Failing to provide a time limit for large instances, risking excessive runtime.

# Workflow 2 (MIP with Capacity-Activation Coupling)

## Modeling stage

### Strategy Overview
This workflow employs a Mixed-Integer Programming (MIP) solver (e.g., CBC, SCIP) via a wrapper like OR-Tools linear solver. It explicitly multiplies the capacity by the usage variable, which can provide tighter linear relaxations and may improve solver performance for some instances.

### Step 1 - Define Variables and Parameters
- Create binary assignment variables `x[i][j]` and binary usage variables `y[j]` using `solver.IntVar(0, 1, name)`.
- Define item weights `w[i]` and resource capacity `C` as parameters.

### Step 2 - Formulate Coupled Capacity Constraints
- For each resource `j`, add the capacity constraint: `sum(w[i] * x[i][j] for i in items) <= C * y[j]`. This enforces capacity only if the resource is used (`y[j]=1`).

### Step 3 - Enforce Assignment and Linkage
- Add exclusive assignment constraints: `sum(x[i][j] for j in resources) == 1` for all items `i`.
- The constraint `x[i][j] <= y[j]` is implicitly enforced by the coupled capacity constraint but can be added for clarity or solver performance.

### Step 4 - Set Objective
- Minimize the total number of used resources: `minimize sum(y[j] for j in resources)`.

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
    "x[items][resources] ∈ {0,1}",
    "y[resources] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in resources)"
  },
  "constraints": [
    "sum(x[i][j] for j in resources) == 1, for all i in items",
    "sum(weight[i] * x[i][j] for i in items) <= capacity * y[j], for all j in resources"
  ]
}
```

### Common Pitfalls
- Incorrectly setting the MIP gap tolerance (e.g., using a negative value); use `MIPGap = 0.0` for exact solutions.
- Creating an excessive number of resources, which unnecessarily increases problem size; use a tight upper bound like `ceil(total_weight / capacity)`.
- Omitting the explicit linkage constraint `x[i][j] <= y[j]` may be acceptable but can sometimes lead to weaker formulations.

## Solving stage

### Strategy Overview
Solve using a MIP solver, configuring it for optimality with appropriate tolerances and runtime limits. Emphasize solution verification through derived metrics and comparison to theoretical bounds.

### Step 1 - Initialize Solver and Set Parameters
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Configure: `solver.SetTimeLimit(time_limit_ms)`, `solver.SetNumThreads(num_threads)`, `solver.SetSolverSpecificParametersAsString('random_seed=value')`. For exact solutions, set `solver.MIPGap = 0.0`.

### Step 2 - Solve and Interpret Termination
- Invoke the solve: `status = solver.Solve()`.
- Check both solver status (`solver.ok`) and termination condition. Accept solutions where `status` is `OPTIMAL` or `FEASIBLE`.

### Step 3 - Extract and Validate Solution
- Get the objective value: `obj_value = solver.Objective().Value()`.
- Determine used resources by checking `y[j].solution_value() > 0.5`.
- Build the assignment list by iterating over `x[i][j]` variables with `solution_value() > 0.5`.
- Validate by calculating the total weight per resource and ensuring it does not exceed capacity.

### Step 4 - Output and Sanity Check
- Report the minimal resource count and the assignment details.
- Compare the objective value to a simple lower bound (e.g., `ceil(total_weight / capacity)`) as a quick optimality plausibility check.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... variable and constraint creation ...

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f"Objective: {solver.Objective().Value()}")
    # Extract variable values using var.solution_value()
else:
    print("Solver did not find a feasible solution.")
    # Check solver.ok() and provide error context
```

### Common Pitfalls
- Confusing solver status codes between different wrapper libraries; always refer to the specific solver's constants.
- Not setting a time limit, which can cause the solver to run indefinitely on difficult instances.
- Using a loose tolerance for `MIPGap` when an exact solution is required.
