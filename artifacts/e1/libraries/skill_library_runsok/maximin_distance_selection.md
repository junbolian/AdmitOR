---
name: Maximin Distance Selection
description: |
  Model and solve selection problems where exactly K items must be chosen to maximize the minimum distance between any selected pair, using binary selection and pairwise consistency constraints.
---

# Workflow 1 (CP-SAT with Big-M Relaxation)

## Modeling stage

### Strategy Overview
This workflow formulates the maximin distance (p-dispersion) problem as a Mixed-Integer Linear Program (MILP) suitable for CP-SAT solvers. It uses binary selection variables, auxiliary pairwise variables linked via consistency constraints, and a big-M relaxation to enforce the minimum distance bound.

### Step 1 - Define Core Selection Variables
- Create a binary decision variable `x[i]` for each candidate item `i` in the set `I`, where `x[i] = 1` indicates the item is selected.
- This forms the basis for the cardinality constraint.

### Step 2 - Enforce Exact Selection Cardinality
- Add a linear equality constraint: `sum_{i in I} x[i] == K`, where `K` is the required number of items to select.
- This ensures the solution contains exactly the specified number of selections.

### Step 3 - Create Pairwise Selection Variables
- For each unordered pair `(i,j)` where `i < j`, create a binary decision variable `y[i,j]`.
- This variable will indicate if both items `i` and `j` are selected.

### Step 4 - Link Pairwise to Individual Variables
- Add three linear constraints for each pair `(i,j)` to enforce logical consistency: `y[i,j] <= x[i]`, `y[i,j] <= x[j]`, and `y[i,j] >= x[i] + x[j] - 1`.
- This ensures `y[i,j] = 1` if and only if `x[i] = 1` and `x[j] = 1`.

### Step 5 - Model Minimum Distance with Big-M
- Create a continuous or integer variable `z` representing the minimum distance to be maximized.
- For each pair `(i,j)`, add a constraint: `z <= d[i,j] + M * (1 - y[i,j])`, where `d[i,j]` is the precomputed distance and `M` is a sufficiently large constant.
- When `y[i,j] = 1`, this forces `z <= d[i,j]`; otherwise, the constraint is relaxed.

### Step 6 - Set Maximization Objective
- Define the objective as `maximize z`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of candidate items.",
    "P: Set of unordered pairs (i,j) where i<j."
  ],
  "parameters": [
    "K: Exact number of items to select (integer).",
    "d[i,j]: Distance between items i and j (non-negative).",
    "M: Big-M constant, larger than max(d[i,j])."
  ],
  "decision_variables": [
    "x[i] ∈ {0,1}: 1 if item i is selected.",
    "y[i,j] ∈ {0,1}: 1 if both i and j are selected.",
    "z: Minimum distance among selected pairs (continuous or integer)."
  ],
  "objective": {
    "sense": "max",
    "expression": "z"
  },
  "constraints": [
    "sum_{i in I} x[i] == K",
    "y[i,j] <= x[i] for all (i,j) in P",
    "y[i,j] <= x[j] for all (i,j) in P",
    "y[i,j] >= x[i] + x[j] - 1 for all (i,j) in P",
    "z <= d[i,j] + M * (1 - y[i,j]) for all (i,j) in P"
  ]
}
```

### Common Pitfalls
- Setting `M` too small, which can incorrectly cut off feasible solutions. Ensure `M > max(d[i,j])`.
- Using a non-symmetric or incomplete distance matrix. Distances should be defined for all `i<j`.
- Forgetting to enforce `i<j` when creating pair sets, leading to duplicate variables and constraints.

## Solving stage

### Strategy Overview
Solve the MILP formulation using the OR-Tools CP-SAT solver, which is efficient for problems dominated by binary variables and linear constraints. The process involves building the model, setting solver parameters, solving, and rigorously checking the solution status.

### Step 1 - Instantiate Model and Define Variables
- Create a `cp_model.CpModel()` object.
- Add `x[i]` as `NewBoolVar`, `y[i,j]` as `NewBoolVar`, and `z` as `NewIntVar` with bounds `[0, max_distance]` (or `NewLinearExpr` for continuous in other solvers).

### Step 2 - Add Constraints to Model
- Translate each constraint from the formulation into the solver's API (e.g., `model.Add(sum(x) == K)`).
- For big-M constraints, use `model.Add(z <= d[i,j] + M * (1 - y[i,j]))`.

### Step 3 - Set Solver Parameters and Solve
- Instantiate a CP-SAT solver.
- Set runtime limits (`max_time_in_seconds`), parallelism (`num_search_workers`), and random seed for reproducibility.
- Call the solver's `Solve` method.

### Step 4 - Check Solver Status and Extract Solution
- Check if the solver returned `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNKNOWN` statuses appropriately.
- If feasible, extract the values of `x[i]` and `z`. Verify which `y[i,j]` are active.

### Step 5 - Validate Solution Integrity
- Confirm the number of selected items equals `K`.
- Compute the actual minimum distance among selected pairs from the distance matrix and compare it to the solver's `z` value.
- For small instances, validate against a brute-force enumeration.

### Code Usage
```python
# Example using OR-Tools CP-SAT (conceptual)
from ortools.sat.python import cp_model
import itertools

# Build model
model = cp_model.CpModel()
# ... define variables and constraints as per formulation ...

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
status = solver.Solve(model)

# Check status and extract solution
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected = [i for i in I if solver.Value(x[i]) > 0.5]
    obj_value = solver.Value(z)
    # ... validation logic ...
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking solver status, leading to errors when trying to extract values from an infeasible model.
- Using an integer variable for `z` with too coarse a granularity when distances are continuous. Ensure bounds and scaling are appropriate.
- Assuming `y[i,j]` values are exactly 0 or 1; use a tolerance (e.g., `> 0.5`) when extracting solutions from MIP solvers.

# Workflow 2 (Pyomo with MILP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling to build the same maximin distance MILP formulation, targeting external solvers like Gurobi, HiGHS, or CBC. It emphasizes a clean separation of model structure from data.

### Step 1 - Define Model Sets and Parameters
- Declare an abstract `Set` for items `I` and a `Set` for unordered pairs `P`.
- Define `Param` for `K`, `d[i,j]`, and the big-M constant.

### Step 2 - Create Decision Variables
- Declare `Var` objects: `x[i]` as `Binary`, `y[i,j]` as `Binary`, and `z` as a non-negative continuous or integer variable.

### Step 3 - Build Cardinality Constraint
- Construct a `Constraint` object representing `sum(x[i] for i in I) == K`.

### Step 4 - Enforce Pairwise Consistency
- Add three constraint families for each pair `(i,j)`: `y[i,j] <= x[i]`, `y[i,j] <= x[j]`, and `y[i,j] >= x[i] + x[j] - 1`.

### Step 5 - Implement Minimum Distance Constraints
- For each pair `(i,j)`, add a constraint: `z <= d[i,j] + M * (1 - y[i,j])`.

### Step 6 - Set Maximization Objective
- Define an `Objective` rule to maximize `z`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of candidate items.",
    "P: Set of unordered pairs (i,j) where i<j."
  ],
  "parameters": [
    "K: Exact number of items to select (integer).",
    "d[i,j]: Distance between items i and j (non-negative).",
    "M: Big-M constant, larger than max(d[i,j])."
  ],
  "decision_variables": [
    "x[i] ∈ {0,1}: 1 if item i is selected.",
    "y[i,j] ∈ {0,1}: 1 if both i and j are selected.",
    "z ≥ 0: Minimum distance among selected pairs."
  ],
  "objective": {
    "sense": "max",
    "expression": "z"
  },
  "constraints": [
    "sum_{i in I} x[i] == K",
    "y[i,j] <= x[i] for all (i,j) in P",
    "y[i,j] <= x[j] for all (i,j) in P",
    "y[i,j] >= x[i] + x[j] - 1 for all (i,j) in P",
    "z <= d[i,j] + M * (1 - y[i,j]) for all (i,j) in P"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing pairs, leading to key errors. Ensure the pair set `P` is defined before creating variables indexed by it.
- Using an inappropriate big-M value that is not strictly greater than all distances, causing model errors or incorrect relaxations.
- Defining the objective or constraints in the wrong rule scope in abstract models.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured external MILP solver. The workflow involves instantiating the model with data, setting solver options, executing the solve, and performing thorough post-solution checks and validation.

### Step 1 - Instantiate Model with Data
- Create a model instance by binding the abstract model to concrete data (sets `I`, `P`, parameters `K`, `d`, `M`).

### Step 2 - Select and Configure Solver
- Use `SolverFactory('solver_name')` (e.g., 'gurobi', 'highs', 'cbc').
- Set solver options such as `TimeLimit`, `MIPGap`, `Threads`, and `Seed` for reproducibility and performance.

### Step 3 - Execute Solve and Check Status
- Call `solver.solve(model)`.
- Check the solver status (`model.solutions.status`) and termination condition (`model.solutions.termination_condition`). Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 4 - Extract and Process Solution
- Load the solution into the model instance.
- Retrieve variable values using `value(x[i])` or `model.x[i].value`.
- Collect selected items and the objective value.

### Step 5 - Validate Against Problem Data
- Recompute the minimum distance among the selected items using the original distance matrix `d`.
- Verify this matches the solver's objective value `z` within a small tolerance.
- Ensure the number of selected items equals `K`.

### Code Usage
```python
# Example using Pyomo with a generic solver (conceptual)
from pyomo.environ import *
import itertools

# Build model instance
model = ConcreteModel()
model.I = Set(initialize=item_list)
model.P = Set(initialize=pair_list, dimen=2)
# ... define parameters, variables, constraints, objective ...

# Solve
solver = SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model)

# Check status and extract solution
if results.solver.status == SolverStatus.ok and \
   results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]:
    selected = [i for i in model.I if value(model.x[i]) > 0.5]
    obj_value = value(model.z)
    # ... validation logic ...
else:
    print("Solve failed or no solution found.")
```

### Common Pitfalls
- Not checking both the solver status and termination condition, potentially interpreting a time-limit feasible solution as optimal.
- Attempting to access variable values before loading the solution into the model.
- Using a distance matrix with missing entries for some pairs in `P`, causing evaluation errors in constraints.
