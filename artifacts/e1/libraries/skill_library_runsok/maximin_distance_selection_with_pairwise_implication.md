---
name: Maximin Distance Selection with Pairwise Implication
description: |
  Model and solve maximin distance selection problems with pairwise implication constraints using binary selection and pairwise variables, implementing cardinality and distance lower bounds via Big-M.

---

# Workflow 1 (CP-SAT with Integer Scaling)

## Modeling stage

### Strategy Overview
This workflow models the problem for integer-only solvers like Google OR-Tools CP-SAT. It scales floating-point distances to integers and uses a Big-M formulation to enforce the minimum distance bound only for selected pairs.

### Step 1 - Define Core Selection Variables
- Create a binary decision variable `x[i]` for each candidate item `i` to indicate selection.
- Create a binary decision variable `y[i,j]` for each unordered pair `(i, j)` where `i < j` to indicate if both items in the pair are selected.

### Step 2 - Link Pairwise and Individual Variables
- Enforce logical implication: `y[i,j] <= x[i]` and `y[i,j] <= x[j]` to ensure the pair variable is zero if either item is not selected.
- Enforce logical conjunction: `y[i,j] >= x[i] + x[j] - 1` to force the pair variable to one if both items are selected.

### Step 3 - Enforce Selection Cardinality
- Add a constraint `sum(x[i] for i in items) == K` to select exactly `K` items.

### Step 4 - Model Maximin Objective with Scaled Big-M
- Introduce an integer variable `z` to represent the scaled minimum distance.
- For each pair `(i, j)`, add a constraint: `z + M * y[i,j] <= M + d_scaled[i,j]`. When `y[i,j]=1`, this enforces `z <= d_scaled[i,j]`; otherwise, it is relaxed.
- Define the objective as `maximize z`.

### Formulation Template
```json
{
  "sets": [
    {"name": "items", "description": "Set of candidate items."},
    {"name": "pairs", "description": "Set of unordered pairs (i,j) where i < j."}
  ],
  "parameters": [
    {"name": "K", "description": "Number of items to select."},
    {"name": "d_scaled", "description": "Integer-scaled distance matrix for pairs."},
    {"name": "M", "description": "Large constant, greater than max(d_scaled)."}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "index": "items"},
    {"name": "y", "type": "binary", "index": "pairs"},
    {"name": "z", "type": "integer", "lower_bound": "0"}
  ],
  "objective": {
    "sense": "max",
    "expression": "z"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum(x[i] for i in items) == K"},
    {"name": "pair_lower", "expression": "y[i,j] >= x[i] + x[j] - 1 for (i,j) in pairs"},
    {"name": "pair_upper_i", "expression": "y[i,j] <= x[i] for (i,j) in pairs"},
    {"name": "pair_upper_j", "expression": "y[i,j] <= x[j] for (i,j) in pairs"},
    {"name": "distance_bound", "expression": "z + M * y[i,j] <= M + d_scaled[i,j] for (i,j) in pairs"}
  ]
}
```

### Common Pitfalls
- Scaling the Big-M constant `M` alongside distances, which breaks the constraint logic. Keep `M` unscaled.
- Using an insufficiently large `M` value, failing to properly relax constraints for non-selected pairs.
- Forgetting to enforce symmetry `y[i,j] = y[j,i]`; define pairs only for `i < j` to avoid duplication.

## Solving stage

### Strategy Overview
Solve the integer model using CP-SAT, focusing on proper scaling of input distances, solver configuration for performance, and verification of results.

### Step 1 - Preprocess and Scale Distances
- Read floating-point distance matrix `d_float`.
- Define a scaling factor (e.g., 1000), multiply distances, and round to integers to create `d_scaled`.
- Set `M` to a value larger than `max(d_scaled)` (e.g., `max(d_scaled) + 1`).

### Step 2 - Configure and Run Solver
- Instantiate the CP-SAT solver.
- Set `solver.parameters.max_time_in_seconds` for a runtime limit.
- Set `solver.parameters.num_search_workers` for parallelism.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to search for proven optimality.

### Step 3 - Extract and Validate Solution
- Check the solver status (`OPTIMAL` or `FEASIBLE`).
- Retrieve the objective value `z_solution` and rescale it by dividing by the scaling factor to obtain the true minimum distance.
- Extract selected items where `x[i].solution_value() > 0.5`.
- For small instances, validate by brute-force checking the minimum distance among selected items matches the rescaled objective.

### Code Usage
```python
# Preprocess: scale distances
scaling_factor = 1000
d_scaled = {(i,j): int(round(d_float[i][j] * scaling_factor)) for i,j in pairs}
M = max(d_scaled.values()) + 1

# Build CP-SAT model from formulation
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in items}
y = {(i,j): model.NewBoolVar(f"y_{i}_{j}") for (i,j) in pairs}
z = model.NewIntVar(0, M, "z")

# Add constraints (cardinality, pairwise implication, distance bound)
# ... (implement constraints as per formulation)

model.Maximize(z)

# Solve with configuration
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 8
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

# Check status and extract solution
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    objective_value = solver.Value(z) / scaling_factor
    selected = [i for i in items if solver.Value(x[i]) > 0.5]
    # Validation logic (optional)
```

### Common Pitfalls
- Not checking solver status before extracting solution values, leading to runtime errors.
- Using an excessively large scaling factor causing integer overflow in the solver.
- Misinterpreting the scaled objective value as the true distance without dividing by the scaling factor.

# Workflow 2 (MILP Solver with Continuous Big-M)

## Modeling stage

### Strategy Overview
This workflow models the problem for MILP solvers (e.g., Gurobi, HiGHS) supporting continuous variables. It uses a standard Big-M formulation where the minimum distance variable is continuous, and constraints are relaxed for non-selected pairs.

### Step 1 - Define Selection Variables
- Create binary variable `x[i]` for each item `i`.
- Create binary variable `y[i,j]` for each unordered pair `(i, j)`.

### Step 2 - Enforce Pairwise Implication
- Add constraints: `y[i,j] <= x[i]`, `y[i,j] <= x[j]`, and `y[i,j] >= x[i] + x[j] - 1` to link pair and individual selections.

### Step 3 - Enforce Selection Count
- Add constraint `sum(x[i] for i in items) == K`.

### Step 4 - Model Maximin with Continuous Variable
- Introduce a continuous variable `d_min` with a lower bound of 0.
- For each pair `(i, j)`, add constraint: `d_min <= d[i,j] + M * (1 - y[i,j])`. When `y[i,j]=1`, this becomes `d_min <= d[i,j]`; otherwise, the large `M` relaxes it.
- Define the objective as `maximize d_min`.

### Formulation Template
```json
{
  "sets": [
    {"name": "items", "description": "Set of candidate items."},
    {"name": "pairs", "description": "Set of unordered pairs (i,j) where i < j."}
  ],
  "parameters": [
    {"name": "K", "description": "Number of items to select."},
    {"name": "d", "description": "Distance matrix for pairs (continuous)."},
    {"name": "M", "description": "Large constant, greater than max(d)."}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "index": "items"},
    {"name": "y", "type": "binary", "index": "pairs"},
    {"name": "d_min", "type": "continuous", "lower_bound": "0"}
  ],
  "objective": {
    "sense": "max",
    "expression": "d_min"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum(x[i] for i in items) == K"},
    {"name": "pair_lower", "expression": "y[i,j] >= x[i] + x[j] - 1 for (i,j) in pairs"},
    {"name": "pair_upper_i", "expression": "y[i,j] <= x[i] for (i,j) in pairs"},
    {"name": "pair_upper_j", "expression": "y[i,j] <= x[j] for (i,j) in pairs"},
    {"name": "distance_bound", "expression": "d_min <= d[i,j] + M * (1 - y[i,j]) for (i,j) in pairs"}
  ]
}
```

### Common Pitfalls
- Using an excessively large `M` value, causing numerical instability and slow convergence.
- Incorrectly formulating the distance bound as `d_min + M*y <= M + d[i,j]`, which does not correctly enforce the maximin condition.
- Omitting the symmetry reduction by defining `y` for `i < j`, resulting in redundant variables and constraints.

## Solving stage

### Strategy Overview
Solve the MILP model using a solver like Gurobi or HiGHS via a modeling library (e.g., Pyomo). Configure solver parameters for optimality and runtime, and implement robust solution extraction and validation.

### Step 1 - Build Model with Modeling Library
- Instantiate a concrete model.
- Define sets, parameters, and variables as per the formulation.
- Add constraints and objective using the modeling library's syntax.

### Step 2 - Configure Solver Parameters
- Set optimality tolerance, e.g., `opt_tol = 0.0` or `MIPGap = 0.0`.
- Set a time limit via `time_limit` parameter.
- Set the number of threads for parallel processing.
- Set a random seed for reproducibility if supported.

### Step 3 - Solve and Check Termination
- Invoke the solver on the model.
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- If the solution is not optimal or feasible, analyze logs and adjust parameters or model.

### Step 4 - Extract and Verify Solution
- Retrieve the objective value `d_min.value`.
- Extract selected items where `x[i].value > 0.5`.
- Optionally, compute the actual minimum distance among selected items from the original distance matrix to validate the model's `d_min`.

### Code Usage
```python
# Build model using Pyomo
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items)
model.pairs = pyo.Set(initialize=pairs, dimen=2)

model.K = pyo.Param(initialize=K)
model.d = pyo.Param(model.pairs, initialize=d)
model.M = pyo.Param(initialize=M)

model.x = pyo.Var(model.items, domain=pyo.Binary)
model.y = pyo.Var(model.pairs, domain=pyo.Binary)
model.d_min = pyo.Var(bounds=(0, None))

# Define constraints (cardinality, pairwise implication, distance bound)
# ... (implement constraints as per formulation)

model.obj = pyo.Objective(expr=model.d_min, sense=pyo.maximize)

# Solve with HiGHS
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 300
solver.options['threads'] = 8
# HiGHS does not support a direct MIPGap=0.0; use mip_rel_gap=0.0
solver.options['mip_rel_gap'] = -1.0  # Note: -1.0 may be invalid; use 0.0 instead.

results = solver.solve(model, tee=True)

# Check status and extract
if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
        objective_value = pyo.value(model.d_min)
        selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
        # Validation logic (optional)
```

### Common Pitfalls
- Setting invalid solver options (e.g., `mip_rel_gap = -1.0` for HiGHS) causing solver errors.
- Not checking both solver status and termination condition, potentially accepting invalid solutions.
- Failing to rescale or validate the objective value, especially if distances were preprocessed.
