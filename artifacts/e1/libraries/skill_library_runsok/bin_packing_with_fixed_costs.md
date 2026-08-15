---
name: Bin Packing with Fixed Costs
description: |
  Model and solve assignment problems with capacity constraints and fixed resource costs using binary variables and linking constraints, producing exact or feasible solutions with clear status handling.
---

# Workflow 1 (CP-SAT for Exact Bin Packing)

## Modeling stage

### Strategy Overview
Use a Constraint Programming (CP) model with Boolean variables to encode binary assignments and resource activation, leveraging the CP-SAT solver's strength in combinatorial search for optimal solutions.

### Step 1 - Define Decision Variables
- Create binary assignment variables `assign[i][j]` for each item `i` and potential resource `j`.
- Create auxiliary binary usage variables `use[j]` for each resource `j` to indicate activation.

### Step 2 - Enforce Assignment Logic
- Add a constraint for each item `i`: `sum(assign[i][j] for j in resources) == 1`. This ensures each item is assigned to exactly one resource.
- Add linking constraints for each item `i` and resource `j`: `assign[i][j] <= use[j]`. This forces the usage variable to be 1 if any item is assigned.

### Step 3 - Impose Capacity Limits
- For each resource `j`, add a capacity constraint: `sum(weight[i] * assign[i][j] for i in items) <= capacity * use[j]`. This deactivates the constraint for unused resources.

### Step 4 - Formulate Objective
- Minimize the total number of used resources: `Minimize(sum(use[j] for j in resources))`.

### Formulation Template
```json
{
  "sets": ["items", "resources"],
  "parameters": ["weight[items]", "capacity"],
  "decision_variables": [
    {"name": "assign", "type": "binary", "indices": ["items", "resources"]},
    {"name": "use", "type": "binary", "indices": ["resources"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(use[j] for j in resources)"
  },
  "constraints": [
    "for i in items: sum(assign[i][j] for j in resources) == 1",
    "for j in resources: sum(weight[i] * assign[i][j] for i in items) <= capacity * use[j]",
    "for i in items, j in resources: assign[i][j] <= use[j]"
  ]
}
```

### Common Pitfalls
- Forgetting to link assignment variables to usage variables, which can lead to solutions where a resource is used but `use[j]=0`.
- Setting an insufficient number of `resources` (too small upper bound), causing model infeasibility.
- Using floating-point weights in a CP-SAT model; ensure weights are integers or scaled appropriately.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for exact optimization with runtime and parallelism controls, then extract and validate the solution, providing structured outputs for success and failure cases.

### Step 1 - Configure Solver Parameters
- Instantiate `cp_model.CpSolver()`.
- Set `solver.parameters.max_time_in_seconds` for runtime control.
- Set `solver.parameters.num_search_workers` for parallel search.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to seek optimality.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before proceeding. For `cp_model.INFEASIBLE` or `cp_model.MODEL_INVALID`, output a structured failure payload.

### Step 3 - Extract and Validate Solution
- Identify used resources: `used = [j for j in resources if solver.Value(use[j]) == 1]`.
- For each used resource `j`, collect assigned items: `items_assigned = [i for i in items if solver.Value(assign[i][j]) == 1]`.
- Calculate derived metrics (e.g., total weight per resource) for verification.

### Step 4 - Output Standardized Results
- Print a simple `RESULT:{objective_value}` for automated parsing.
- Output a detailed `RESULT_JSON` payload containing status, objective value, assignments, and validation metrics.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (variable and constraint creation as per modeling stage)
model.Minimize(sum(use[j] for j in resources))

# solve with status / termination checks
solver = cp_model.CpSolver()
# Apply parameter settings
solver.parameters.max_time_in_seconds = max_time
solver.parameters.num_search_workers = num_workers
solver.parameters.random_seed = seed
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    objective_value = int(solver.ObjectiveValue())
    # ... extraction logic
    print(f"RESULT:{objective_value}")
    # ... print JSON payload
else:
    print("RESULT:INFEASIBLE")
    # ... output error details
```

### Common Pitfalls
- Not checking solver status before accessing solution values, causing runtime errors.
- Misinterpreting `FEASIBLE` as `OPTIMAL`; distinguish for accurate optimality reporting.
- Overlooking the need to convert solver values (`solver.Value(var)`) for comparison.

# Workflow 2 (MIP for Scalable Bin Packing)

## Modeling stage

### Strategy Overview
Formulate as a Mixed-Integer Program using a linear solver backend, employing classic two-layer binary variables and linear constraints suitable for larger instances where CP search may be less efficient.

### Step 1 - Define Binary Variables
- Define `x[i,j]` as binary assignment variables.
- Define `y[j]` as binary usage/activation variables for resources.

### Step 2 - Enforce Assignment Exclusivity
- For each item `i`, add constraint: `sum(x[i,j] for j in resources) == 1`.

### Step 3 - Link Assignment to Usage
- For each item `i` and resource `j`, add constraint: `x[i,j] <= y[j]`. This ensures the resource is marked as used if any item is assigned.

### Step 4 - Apply Capacity Constraints
- For each resource `j`, add constraint: `sum(weight[i] * x[i,j] for i in items) <= capacity * y[j]`. This combines activation and capacity limit.

### Step 5 - Set Objective
- Minimize total resource usage: `Minimize(sum(y[j] for j in resources))`.

### Formulation Template
```json
{
  "sets": ["items", "resources"],
  "parameters": ["weight[items]", "capacity"],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["items", "resources"]},
    {"name": "y", "type": "binary", "indices": ["resources"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in resources)"
  },
  "constraints": [
    "for i in items: sum(x[i,j] for j in resources) == 1",
    "for j in resources: sum(weight[i] * x[i,j] for i in items) <= capacity * y[j]",
    "for i in items, j in resources: x[i,j] <= y[j]"
  ]
}
```

### Common Pitfalls
- Using a single capacity constraint without the `y[j]` multiplier, which incorrectly constrains unused resources.
- Omitting the direct linking constraints (`x[i,j] <= y[j]`), relying solely on the capacity constraint, which can lead to suboptimal presolve.
- Not providing a sufficiently large upper bound for the set of `resources`, causing model infeasibility.

## Solving stage

### Strategy Overview
Utilize a MIP solver (e.g., SCIP, CBC) via a linear programming wrapper, configure it for performance, solve, and then extract and verify the solution against known lower bounds.

### Step 1 - Initialize Solver and Set Parameters
- Create solver instance, e.g., `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set time limit: `solver.SetTimeLimit(timeout_ms)`.
- Set number of threads: `solver.SetNumThreads(num_threads)`.
- Optionally set other parameters like tolerances.

### Step 2 - Build and Solve Model
- Construct variables and constraints as per the modeling stage.
- Define the objective function and call `solver.Solve()`.

### Step 3 - Verify Solution Status and Optimality
- Check solver status: `status in (solver.OPTIMAL, solver.FEASIBLE)`.
- Compute a simple lower bound: `lower_bound = ceil(total_weight / capacity)`.
- Compare the found objective value to the lower bound; if equal, optimality is confirmed.

### Step 4 - Extract and Interpret Solution
- Identify used resources: `used = [j for j in resources if y[j].solution_value() > 0.5]`.
- For each used resource, list assigned items: `assignments = {j: [i for i in items if x[i,j].solution_value() > 0.5] for j in used}`.
- Calculate utilization metrics per resource for validation.

### Step 5 - Output Structured Results
- Print objective value and assignment summary.
- For programmatic use, output a JSON structure with status, objective, and assignments.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(timeout_ms)
solver.SetNumThreads(num_threads)

# Variable creation
x = {}
for i in items:
    for j in resources:
        x[i, j] = solver.IntVar(0, 1, f'x_{i}_{j}')
y = {j: solver.IntVar(0, 1, f'y_{j}') for j in resources}

# Constraints
for i in items:
    solver.Add(sum(x[i, j] for j in resources) == 1)
for j in resources:
    solver.Add(sum(weight[i] * x[i, j] for i in items) <= capacity * y[j])
    for i in items:
        solver.Add(x[i, j] <= y[j])

# Objective
objective = solver.Objective()
for j in resources:
    objective.SetCoefficient(y[j], 1)
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = objective.Value()
    # ... extraction and output
else:
    # ... handle infeasible or error status
```

### Common Pitfalls
- Accessing `.solution_value()` on variables before checking solver status, leading to errors.
- Setting invalid solver parameters (e.g., negative time limit) causing immediate failure.
- Not scaling large integral weights, which can degrade solver performance.
