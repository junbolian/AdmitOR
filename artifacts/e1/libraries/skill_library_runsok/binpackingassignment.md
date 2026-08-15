---
name: BinPackingAssignment
description: |
  Model and solve assignment problems with capacity constraints and binary usage indicators to minimize resource count.

---

# Workflow 1 (CP-SAT with Explicit Linking)

## Modeling stage

### Strategy Overview
This workflow models the problem using Google OR-Tools CP-SAT, emphasizing explicit linking constraints between assignment and usage variables for clarity and solver performance. It is well-suited for problems where the number of potential bins is known and can be bounded.

### Step 1 - Define Variables
- Create binary assignment variables `x[i][j]` for each item `i` and potential bin `j`.
- Create binary usage variables `y[j]` for each potential bin `j`.

### Step 2 - Enforce Exclusive Assignment
- For each item `i`, add a constraint that the sum of `x[i][j]` over all bins `j` equals 1.

### Step 3 - Enforce Capacity and Link Usage
- For each bin `j`, add a knapsack constraint: the sum of `weight[i] * x[i][j]` over all items `i` must be less than or equal to `capacity * y[j]`.
- For each item `i` and bin `j`, add an explicit linking constraint: `x[i][j] <= y[j]`.

### Step 4 - Define Objective and Symmetry Breaking
- Set the objective to minimize the sum of all `y[j]` variables.
- Optionally, add symmetry-breaking constraints like `y[j] >= y[j+1]` to reduce search space.

### Formulation Template
```json
{
  "sets": [
    "items",
    "bins"
  ],
  "parameters": [
    "weight[items]",
    "capacity"
  ],
  "decision_variables": [
    "x[items][bins] ∈ {0,1}",
    "y[bins] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in bins)"
  },
  "constraints": [
    "assignment_exclusive: for i in items: sum(x[i][j] for j in bins) == 1",
    "capacity_knapsack: for j in bins: sum(weight[i] * x[i][j] for i in items) <= capacity * y[j]",
    "linking: for i in items, j in bins: x[i][j] <= y[j]"
  ]
}
```

### Common Pitfalls
- Forgetting to add explicit linking constraints, which can lead to incorrect solutions if the capacity constraint alone is used.
- Using an insufficient upper bound for the number of bins, causing infeasibility.
- Not adding symmetry-breaking constraints, which can significantly increase solve time for symmetric problems.

## Solving stage

### Strategy Overview
Solve using the CP-SAT solver with configuration for optimality. The focus is on extracting and verifying the solution, handling infeasibility gracefully, and optionally performing progressive feasibility checks to confirm optimality.

### Step 1 - Configure Solver
- Instantiate `cp_model.CpSolver()`.
- Set parameters: `max_time_in_seconds`, `num_search_workers`, and `relative_gap_limit=0.0` for optimality.

### Step 2 - Solve and Check Status
- Invoke the solver on the model.
- Check if the status is `OPTIMAL` or `FEASIBLE` before proceeding.

### Step 3 - Extract and Verify Solution
- Extract used bins where `solver.Value(y[j]) == 1`.
- Extract assignments where `solver.Value(x[i][j]) == 1`.
- Post-solve, verify that capacity constraints are satisfied by summing weights per used bin.

### Step 4 - Handle Infeasibility and Confirm Optimality
- For infeasible cases, return a structured error with the solver status.
- Optionally, test feasibility with a smaller number of bins by adding a constraint `sum(y[j]) <= k` to confirm the optimal bin count.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract solution
    used_bins = [j for j in bins if solver.Value(y[j]) == 1]
    assignments = {(i, j): solver.Value(x[i][j]) for i in items for j in bins if solver.Value(x[i][j]) == 1}
    # ... (verification logic)
else:
    # Handle infeasibility
    print(f"Solver status: {status}")
```

### Common Pitfalls
- Not checking solver status before extracting variable values, leading to runtime errors.
- Using floating-point comparisons for binary variable values; use integer equality checks instead.
- Omitting solution verification, which can miss modeling errors.

# Workflow 2 (MIP with Progressive Bound Tightening)

## Modeling stage

### Strategy Overview
This workflow uses a Mixed-Integer Programming (MIP) solver (e.g., SCIP, CBC) and employs a strategy of progressive bound tightening. It starts with a theoretical lower bound for the number of bins and iteratively tests feasibility, making it efficient when the optimal number of bins is unknown or the problem is tight.

### Step 1 - Define Variables and Basic Constraints
- Create binary assignment variables `x[i][j]` and binary usage variables `y[j]`.
- Enforce exclusive assignment: `sum(x[i][j] for j in bins) == 1` for each item `i`.
- Enforce capacity: `sum(weight[i] * x[i][j] for i in items) <= capacity * y[j]` for each bin `j`.

### Step 2 - Calculate Initial Bounds
- Compute a theoretical lower bound: `lower_bound = ceil(total_weight / capacity)`.
- Set an initial upper bound, e.g., `upper_bound = number_of_items`.

### Step 3 - Implement Iterative Feasibility Core
- The core model does not include the objective initially. A constraint `sum(y[j]) <= current_bin_limit` is added to test feasibility for a specific bin count.

### Step 4 - Define Optimization Objective
- Once a feasible bin count `k` is found, the full model's objective is to minimize `sum(y[j])`, with the added constraint `sum(y[j]) <= k` to find the optimal assignment for that count.

### Formulation Template
```json
{
  "sets": [
    "items",
    "bins"
  ],
  "parameters": [
    "weight[items]",
    "capacity",
    "bin_limit"
  ],
  "decision_variables": [
    "x[items][bins] ∈ {0,1}",
    "y[bins] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in bins)"
  },
  "constraints": [
    "assignment_exclusive: for i in items: sum(x[i][j] for j in bins) == 1",
    "capacity_knapsack: for j in bins: sum(weight[i] * x[i][j] for i in items) <= capacity * y[j]",
    "bin_limit: sum(y[j] for j in bins) <= bin_limit"
  ]
}
```

### Common Pitfalls
- Not calculating a proper lower bound, leading to unnecessary iterations.
- Using the same variable set for all iterations without reinitializing the model, which can cause constraint accumulation.
- Forgetting to relax the `bin_limit` constraint between feasibility tests.

## Solving stage

### Strategy Overview
Solve using a MIP solver in an iterative loop. Start with the lower bound and increment the bin limit until feasibility is achieved, then solve the optimization model to find the optimal assignment for that bin count.

### Step 1 - Initialize Solver and Model
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Build the base model with variables, assignment, and capacity constraints.

### Step 2 - Iterative Feasibility Search
- For `k` from `lower_bound` to `upper_bound`:
    - Add or modify the constraint `sum(y[j]) <= k`.
    - Solve the feasibility model (initially without objective).
    - If feasible, set `feasible_bin_count = k` and break.

### Step 3 - Solve Optimization Model
- Using the feasible bin count `k`, set the objective to minimize `sum(y[j])` and solve the model again to get the optimal assignment.

### Step 4 - Extract and Validate Solution
- Extract solution values using a tolerance (e.g., `variable.solution_value() > 0.5`).
- Validate assignments and capacity constraints.
- Optionally, verify that no solution exists for `k-1` by solving a final feasibility test.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (build base model variables and constraints as per modeling stage)

# solve with status / termination checks
lower_bound = ceil(total_weight / capacity)
upper_bound = num_items
feasible_count = None

for k in range(lower_bound, upper_bound + 1):
    # Add bin limit constraint for this iteration
    constraint = solver.Constraint(0, k)
    for j in bins:
        constraint.SetCoefficient(y[j], 1)
    
    solver.SetTimeLimit(30000)
    status = solver.Solve()
    
    if status in (solver.OPTIMAL, solver.FEASIBLE):
        feasible_count = k
        break
    # Remove or deactivate constraint for next iteration (requires model reset or new constraint object)

if feasible_count is not None:
    # Now solve the optimization model with the objective
    objective = solver.Objective()
    for j in bins:
        objective.SetCoefficient(y[j], 1)
    objective.SetMinimization()
    # Ensure the bin limit constraint is still active for `feasible_count`
    solver.Solve()
    # Extract and verify solution
```

### Common Pitfalls
- Not properly resetting or managing constraints between iterations, leading to incorrect models.
- Using the same solver instance without clearing previous solutions or constraints.
- Relying solely on the solver's status without post-solution validation.
