---
name: Bin Packing with Activation Variables
description: |
  A skill for modeling and solving bin packing problems using binary activation variables for bins and assignment variables for items, with strategies for verifying optimality and handling solver-specific configurations.
---

# Workflow 1 (CP-SAT / OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, which is designed for discrete optimization problems. The modeling approach leverages native CP-SAT constructs like `OnlyEnforceIf` for logical implications and focuses on efficient constraint propagation.

### Step 1 - Define Variables and Upper Bound
- Define binary decision variables for bin activation (`bin_used[j]`) and item-to-bin assignment (`assign[i][j]`).
- Set the initial upper bound for the number of bins (`n_bins`) to the number of items (`n_items`) to guarantee feasibility.
- Use `model.NewBoolVar` for all binary variables.

### Step 2 - Formulate Core Constraints
- **Assignment Exclusivity**: For each item `i`, enforce `sum(assign[i][j] for j in bins) == 1`.
- **Capacity Linking**: For each bin `j`, create a linear constraint: `sum(weight[i] * assign[i][j] for i in items) <= capacity * bin_used[j]`.
- **Logical Implication**: Optionally add `assign[i][j] <= bin_used[j]` for all `i, j` to strengthen the model, though it may be redundant with the capacity linking constraint.

### Step 3 - Set Objective and Symmetry Breaking
- Set the objective to minimize the total number of bins used: `minimize(sum(bin_used[j] for j in bins))`.
- Add symmetry-breaking constraints, such as `bin_used[j-1] >= bin_used[j]`, to reduce the search space by ordering bin activations.

### Formulation Template
```json
{
  "sets": [
    "items",
    "bins"
  ],
  "parameters": [
    {"name": "weight", "index": "items"},
    {"name": "capacity", "type": "scalar"}
  ],
  "decision_variables": [
    {"name": "assign", "type": "binary", "indices": ["items", "bins"]},
    {"name": "bin_used", "type": "binary", "indices": ["bins"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(bin_used[j] for j in bins)"
  },
  "constraints": [
    {"name": "assign_once", "expression": "sum(assign[i][j] for j in bins) == 1", "index": "items"},
    {"name": "capacity", "expression": "sum(weight[i] * assign[i][j] for i in items) <= capacity * bin_used[j]", "index": "bins"},
    {"name": "symmetry", "expression": "bin_used[j-1] >= bin_used[j]", "index": "bins", "for": "j > 0"}
  ]
}
```

### Common Pitfalls
- Forgetting to link `assign` variables to `bin_used` variables, which can lead to assignments to inactive bins.
- Setting an insufficient upper bound for `bins`, which makes the model infeasible.
- Adding redundant constraints that unnecessarily increase model size and slow down solving.

## Solving stage

### Strategy Overview
The solving stage configures the CP-SAT solver for performance and reliability, extracts solutions, and implements a verification loop to confirm optimality by testing tighter bin counts.

### Step 1 - Configure and Solve
- Instantiate the CP-SAT solver.
- Set key parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 8`, `solver.parameters.random_seed = 42`.
- Solve the model and capture the status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).

### Step 2 - Extract and Validate Solution
- If status is `OPTIMAL` or `FEASIBLE`, extract variable values using `solver.Value(var)`.
- Compute derived metrics: total bins used, bin loads, and total packed weight.
- Validate the solution against the original constraints (e.g., capacity, assignment exclusivity).

### Step 3 - Verify Optimality via Feasibility Testing
- Calculate the theoretical lower bound: `lower_bound = ceil(total_weight / capacity)`.
- If the solution uses `k` bins and `k > lower_bound`, test for feasibility with `k-1` bins.
- Create a feasibility model by fixing the maximum number of active bins (e.g., `sum(bin_used) <= k-1`) and solving with a dummy objective. If infeasible, `k` is optimal.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (build variables and constraints as per Modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set solver parameters
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

# Check status and extract solution
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    used_bins = [j for j in bins if solver.Value(bin_used[j]) > 0.5]
    assignments = {(i, j): solver.Value(assign[i][j]) for i in items for j in bins}
    # ... (compute validation metrics)
else:
    # Handle infeasible or unknown status
    pass
```

### Common Pitfalls
- Not checking solver status before extracting variable values, leading to runtime errors.
- Setting `relative_gap_limit` incorrectly; use `0.0` for exact solutions.
- Omitting the feasibility test for optimality verification, potentially accepting suboptimal solutions.

# Workflow 2 (MIP / Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for algebraic modeling and a Mixed-Integer Programming (MIP) solver like HiGHS. It emphasizes a clean separation of model components (sets, parameters, variables) and uses Pyomo's `Constraint` and `Objective` objects.

### Step 1 - Declare Model Components
- Define Pyomo `Set` objects for `items` and `bins` (with `bins` sized to `len(items)`).
- Define `Param` objects for `weight` (indexed by items) and scalar `capacity`.
- Define binary `Var` objects: `x[i,b]` for assignment and `y[b]` for bin activation.

### Step 2 - Build Constraints Algebraically
- **Assignment**: For each item `i`, add constraint `sum(x[i,b] for b in bins) == 1`.
- **Capacity**: For each bin `b`, add constraint `sum(weight[i] * x[i,b] for i in items) <= capacity * y[b]`.
- **Linking**: For all `i, b`, add constraint `x[i,b] <= y[b]` to explicitly enforce the logical relationship.

### Step 3 - Define Objective and Add Symmetry Breaking
- Define the objective: `minimize sum(y[b] for b in bins)`.
- Optionally add symmetry-breaking constraints, e.g., `y[b-1] >= y[b] for b in bins if b > 0`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "bins"
  ],
  "parameters": [
    {"name": "weight", "index": "items"},
    {"name": "capacity", "type": "scalar"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["items", "bins"]},
    {"name": "y", "type": "binary", "indices": ["bins"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[b] for b in bins)"
  },
  "constraints": [
    {"name": "assign_once", "expression": "sum(x[i,b] for b in bins) == 1", "index": "items"},
    {"name": "capacity", "expression": "sum(weight[i] * x[i,b] for i in items) <= capacity * y[b]", "index": "bins"},
    {"name": "linking", "expression": "x[i,b] <= y[b]", "indices": ["items", "bins"]}
  ]
}
```

### Common Pitfalls
- Using `=` instead of `==` in Pyomo constraint expressions.
- Not initializing the `bins` set with a sufficiently large upper bound.
- Creating constraints with incorrect indexing, leading to model building errors.

## Solving stage

### Strategy Overview
This stage uses Pyomo's `SolverFactory` to interface with the HiGHS solver, carefully manages solution loading to avoid errors, and implements a bound-tightening loop for optimality verification.

### Step 1 - Configure Solver and Solve
- Create solver instance: `solver = SolverFactory('highs')`.
- Set solver options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`. For exact solution, set `mip_rel_gap = 0.0` or `-1.0` depending on solver.
- Solve with `load_solutions=False` to first check termination status.

### Step 2 - Check Status and Load Solution
- Check `results.solver.status` and `results.solver.termination_condition`.
- If status indicates `optimal` or `feasible`, load the solution into the model using `model.solutions.load_from(results)`.
- Extract variable values using `pyo.value(var)` with a threshold (e.g., `> 0.5`) for binary variables.

### Step 3 - Iterative Bound Verification
- Calculate the theoretical lower bound `LB = ceil(total_weight / capacity)`.
- If the solution uses `k` bins, test if a solution with `k-1` bins exists.
- Build a feasibility model with an additional constraint `sum(y[b]) <= test_bins` and a dummy objective (e.g., `0`). Solve and check feasibility to prove optimality.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items)
model.bins = pyo.Set(initialize=range(n_items))
# ... (define parameters, variables, constraints, objective as per Modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, load_solutions=False)

# Check termination condition
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    model.solutions.load_from(results)
    used_bins = [b for b in model.bins if pyo.value(model.y[b]) > 0.5]
    # ... (extract assignments and validate)
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    # Handle feasible but not proven optimal
    model.solutions.load_from(results)
else:
    # Handle infeasible or other status
    pass
```

### Common Pitfalls
- Loading solutions without checking termination condition, risking `NoFeasibleSolutionError`.
- Incorrectly interpreting solver status codes; always compare against `TerminationCondition` enums.
- Not using a threshold when reading binary variable values, leading to floating-point comparison issues.
