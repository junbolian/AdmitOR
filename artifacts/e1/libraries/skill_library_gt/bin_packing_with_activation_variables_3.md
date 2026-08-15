---
name: Bin Packing with Activation Variables
description: |
  Model capacity-constrained assignment as a bin packing problem with activation variables to minimize used bins, then solve via CP-SAT or MIP solvers with explicit status checks and solution validation.
---

# Workflow 1 (CP-SAT for Exact Optimization)

## Modeling stage

### Strategy Overview
Formulate the problem as a MILP suitable for CP-SAT solvers, focusing on binary variables and linear constraints to minimize the count of activated centers, with an emphasis on a tight, solver-friendly formulation.

### Step 1 - Define Variables and Upper Bound
- Define a safe upper bound for the number of centers (e.g., `max_centers = n_resources` or `ceil(total_weight / capacity)`).
- Create binary assignment variables `assign[i][j]` (1 if resource `i` is assigned to center `j`).
- Create binary activation variables `used[j]` (1 if center `j` is utilized).

### Step 2 - Implement Core Constraints
- **Single Assignment**: For each resource `i`, enforce `sum(assign[i][j] for j in centers) == 1`.
- **Capacity Limit**: For each center `j`, enforce `sum(weight[i] * assign[i][j] for i in resources) <= capacity`.
- **Usage Linking**: For all `i, j`, add `used[j] >= assign[i][j]` to ensure activation reflects any assignment.

### Step 3 - Set Objective
- Minimize the total number of used centers: `minimize sum(used[j] for j in centers)`.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "centers"
  ],
  "parameters": [
    "weight[resource]",
    "capacity"
  ],
  "decision_variables": [
    "assign[resource, center] ∈ {0,1}",
    "used[center] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(used[center] for center in centers)"
  },
  "constraints": [
    "single_assignment: for resource in resources: sum(assign[resource, center] for center in centers) == 1",
    "capacity_limit: for center in centers: sum(weight[resource] * assign[resource, center] for resource in resources) <= capacity",
    "usage_linking: for resource in resources, center in centers: used[center] >= assign[resource, center]"
  ]
}
```

### Common Pitfalls
- Forgetting to define a sufficiently large upper bound for `centers`, which can lead to infeasibility.
- Omitting the linking constraint, which can allow `used[j]=0` while `assign[i][j]=1`, breaking the objective.
- Using a loose upper bound (like `n_resources`) for large instances, which unnecessarily increases model size.

## Solving stage

### Strategy Overview
Solve the model using Google's OR-Tools CP-SAT solver, configured for exact optimization with parallel search and time limits, followed by robust solution extraction and validation.

### Step 1 - Configure Solver
- Instantiate the CP-SAT solver.
- Set key parameters: `max_time_in_seconds` for runtime control, `num_search_workers` for parallelism, `random_seed` for reproducibility, and `relative_gap_limit = 0.0` for exact optimization.

### Step 2 - Solve and Check Status
- Call the solver and capture the status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.).
- If status is not `OPTIMAL` or `FEASIBLE`, output a structured failure message and terminate.

### Step 3 - Extract and Validate Solution
- Extract the objective value.
- For each center `j` where `used[j]` is 1, collect the list of assigned resources.
- Optionally, verify that the total weight per center does not exceed capacity.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (variable and constraint creation as per Modeling stage)
model.Minimize(sum(used[j] for j in centers))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"RESULT:{solver.ObjectiveValue()}")
    # Extract assignment details
    for j in range(max_centers):
        if solver.Value(used[j]) == 1:
            assigned = [i for i in resources if solver.Value(assign[(i, j)]) == 1]
            total = sum(weight[i] for i in assigned)
            print(f"Center {j}: resources {assigned}, total weight {total}")
else:
    print(f'RESULT_JSON:{{"status":"failed","reason":"no_feasible_solution","solver_status":{int(status)}}}')
```

### Common Pitfalls
- Not checking solver status before extracting variable values, which can cause runtime errors.
- Setting `relative_gap_limit` too high, accepting suboptimal solutions when exact optimum is required.
- Overlooking solver time limits for large instances, potentially returning no solution.

# Workflow 2 (MIP via Pyomo/High-Level API)

## Modeling stage

### Strategy Overview
Model the problem using a high-level modeling language (Pyomo) to abstract the formulation, focusing on the `capacity * y[j]` linking pattern and leveraging MIP solver capabilities for medium to large instances.

### Step 1 - Define Model and Sets
- Create an abstract or concrete Pyomo model.
- Define sets: `resources` (items) and `centers` (bins) with a safe upper bound.

### Step 2 - Create Variables and Parameters
- Declare parameters: `weight[resource]` and `capacity`.
- Declare binary decision variables: `x[resource, center]` for assignment and `y[center]` for center activation.

### Step 3 - Add Constraints with Capacity-Activation Link
- **Single Assignment**: For each resource, `sum(x[resource, center] for center in centers) == 1`.
- **Capacity with Activation**: For each center, `sum(weight[resource] * x[resource, center] for resource in resources) <= capacity * y[center]`. This directly enforces the link.
- **Redundant Linking (Optional)**: Add `x[resource, center] <= y[center]` for all pairs to strengthen the formulation.

### Step 4 - Define Objective
- Minimize the sum of activation variables: `minimize sum(y[center] for center in centers)`.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "centers"
  ],
  "parameters": [
    "weight[resource]",
    "capacity"
  ],
  "decision_variables": [
    "x[resource, center] ∈ {0,1}",
    "y[center] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[center] for center in centers)"
  },
  "constraints": [
    "single_assignment: for resource in resources: sum(x[resource, center] for center in centers) == 1",
    "capacity_activation: for center in centers: sum(weight[resource] * x[resource, center] for resource in resources) <= capacity * y[center]"
  ]
}
```

### Common Pitfalls
- Using the `capacity * y[center]` constraint without the `y[center]` variable being properly declared as binary.
- Defining the `centers` set with an unreasonably large cardinality, slowing down the solver.
- Forgetting to deactivate the `capacity_activation` constraint for unused centers via `y[center]=0`; the formulation handles this automatically.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external MIP solver (e.g., HiGHS, CBC), configure it for performance and optimality, and implement a structured pattern for result extraction and validation.

### Step 1 - Select and Configure Solver
- Instantiate a solver object (e.g., `SolverFactory('highs')`).
- Set options: `time_limit`, `mip_rel_gap=0.0` (for exact), `threads` for parallel search.

### Step 2 - Solve and Inspect Termination
- Execute the solve command and capture the results object.
- Check both `SolverStatus` (e.g., `ok`) and `TerminationCondition` (e.g., `optimal`, `feasible`). Proceed only if the solve was successful.

### Step 3 - Process and Verify Solution
- Retrieve the objective value.
- Iterate through `y[center]` variables to identify used centers.
- For each used center, find resources where `x[resource, center]` > 0.5 (accounting for solver tolerance).
- Calculate aggregate metrics (e.g., total weight per center) to verify capacity constraints.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.resources = pyo.Set(initialize=resources)
model.centers = pyo.Set(initialize=centers)
model.weight = pyo.Param(model.resources, initialize=weight_dict)
model.capacity = pyo.Param(initialize=capacity)
model.x = pyo.Var(model.resources, model.centers, within=pyo.Binary)
model.y = pyo.Var(model.centers, within=pyo.Binary)
# ... (constraint and objective rules as per Modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -0.0001  # Forces near-exact
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    print(f"RESULT:{pyo.value(model.obj)}")
    for j in model.centers:
        if pyo.value(model.y[j]) > 0.5:
            assigned = [i for i in model.resources if pyo.value(model.x[i, j]) > 0.5]
            total = sum(weight_dict[i] for i in assigned)
            print(f"Center {j}: resources {assigned}, total weight {total}")
else:
    print(f'RESULT_JSON:{{"status":"failed","reason":"solver_failure","termination_condition":"{results.solver.termination_condition}"}}')
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`); both must be checked.
- Not using a tolerance (e.g., `> 0.5`) when checking binary variable values due to solver numerical precision.
- Omitting solver time limits, which can cause the process to hang on difficult instances.
