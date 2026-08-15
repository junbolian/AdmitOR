---
name: Bin Packing with Activation Cost
description: |
  Model and solve bin packing problems with activation costs using binary variables for bin usage and item assignment, with workflows for exact optimality proofs and heuristic-driven search.
---

# Workflow 1 (Exact Optimality via Feasibility Testing)

## Modeling stage

### Strategy Overview
This workflow focuses on proving optimality by iteratively testing feasibility with decreasing bin counts. The model is built once with a safe upper bound, then solved repeatedly with additional constraints to force a specific number of active bins, seeking the smallest feasible count.

### Step 1 - Define Sets and Parameters
- Define the set of items `I` and a set of potential bins `B` sized to a safe upper bound (e.g., `|I|`).
- Define the weight parameter `weight_i` for each item `i` and the scalar bin capacity `capacity`.

### Step 2 - Create Decision Variables
- Create a binary variable `y_b` for each bin `b` in `B` indicating if the bin is activated.
- Create a binary variable `x_i_b` for each item `i` and bin `b` indicating the assignment.

### Step 3 - Formulate Core Constraints
- **Assignment Exclusivity**: For each item `i`, enforce `sum(x_i_b for b in B) == 1`.
- **Linking**: For each item `i` and bin `b`, enforce `x_i_b <= y_b`.
- **Capacity**: For each bin `b`, enforce `sum(weight_i * x_i_b for i in I) <= capacity * y_b`.

### Step 4 - Add Symmetry Breaking (Optional)
- Add constraints `y_{b-1} >= y_b` for bins `b > 1` to force bins to be used in sequence, reducing the solution space.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of items"},
    {"name": "B", "description": "Set of potential bins (indexed 1..M)"}
  ],
  "parameters": [
    {"name": "weight_i", "index": "i in I", "description": "Weight of item i"},
    {"name": "capacity", "description": "Maximum weight capacity per bin"}
  ],
  "decision_variables": [
    {"name": "y_b", "index": "b in B", "type": "binary", "description": "1 if bin b is used"},
    {"name": "x_i_b", "index": "i in I, b in B", "type": "binary", "description": "1 if item i is assigned to bin b"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y_b for b in B)"
  },
  "constraints": [
    {"name": "assign_once", "expression": "sum(x_i_b for b in B) == 1", "index": "i in I"},
    {"name": "link", "expression": "x_i_b <= y_b", "index": "i in I, b in B"},
    {"name": "capacity", "expression": "sum(weight_i * x_i_b for i in I) <= capacity * y_b", "index": "b in B"}
  ]
}
```

### Common Pitfalls
- Forgetting the linking constraint `x_i_b <= y_b`, which can lead to items assigned to inactive bins.
- Setting the initial bin set `B` too small, making the model infeasible. Use `|B| = |I|` as a safe default.
- Using a non-exact solver gap tolerance when aiming for a proof of optimality.

## Solving stage

### Strategy Overview
Solve the full model to get an initial solution, then iteratively test if a solution exists with fewer bins by solving a feasibility model (no objective) with a constraint limiting the total number of active bins. Start from a theoretical lower bound.

### Step 1 - Calculate Bounds and Initial Solve
- Calculate a theoretical lower bound: `LB = ceil(total_weight / capacity)`.
- Build and solve the full model (with objective) to obtain an initial solution value `k`.
- If the solver proves optimality and `k == LB`, optimality is immediately proven.

### Step 2 - Iterative Feasibility Testing
- For `target_bins` from `LB` to `k-1`:
    - Clone the model or rebuild it.
    - Add a constraint: `sum(y_b for b in B) <= target_bins`.
    - Remove or ignore the objective (solve as a feasibility problem).
    - Solve the model.
    - If feasible, a new best solution with `target_bins` is found. Update `k = target_bins`.
    - If infeasible, `k` is optimal; break the loop.

### Step 3 - Extract and Validate Solution
- Extract the final solution: active bins where `y_b > 0.5` and assignments where `x_i_b > 0.5`.
- Validate by checking total assigned weight equals total item weight and no bin exceeds capacity.

### Code Usage
```python
# build model from formulation
model = build_bin_packing_model(items, weights, capacity, max_bins)
# solve with status / termination checks
solver = SolverFactory('gurobi')  # or 'cbc', 'cplex'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
results = solver.solve(model, load_solutions=False)

if results.solver.termination_condition == TerminationCondition.optimal:
    model.solutions.load_from(results)
    k = value(model.obj)  # initial best bin count
    # Iterative feasibility testing loop
    for target in range(LB, k):
        # Add constraint: sum(model.y[:]) <= target
        # Solve feasibility model
        # Check feasibility and update k if feasible
else:
    # Handle non-optimal termination
    print("Initial solve failed:", results.solver.termination_condition)
```

### Common Pitfalls
- Not setting `MIPGap=0.0` (or equivalent) for the solver, leading to early termination with a suboptimal solution.
- Failing to handle infeasible subproblems gracefully; ensure the solver status is checked after each feasibility solve.
- Forgetting to disable the objective during feasibility tests, which wastes computational effort.

# Workflow 2 (Direct Optimization with CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google's CP-SAT solver via the `ortools` library, leveraging its native support for logical constraints and efficient search. The model is built directly in the CP-SAT API, using linear constraints and boolean variables, and solved once with the goal of finding a proven optimal solution directly.

### Step 1 - Initialize Model and Variable Sets
- Create a CP-SAT model instance.
- Define the set of items `I` and potential bins `B` (size = `|I|`).
- Create a list of Boolean variables `y_b` for bin activation.
- Create a 2D list of Boolean variables `x_i_b` for item-bin assignment.

### Step 2 - Enforce Assignment Constraints
- For each item `i`, add an `ExactlyOne` constraint on the list `[x_i_b for b in B]` to ensure assignment to exactly one bin.

### Step 3 - Enforce Linking and Capacity Constraints
- For each item `i` and bin `b`, add the linear inequality `x_i_b <= y_b`.
- For each bin `b`, create a linear expression `sum(weight_i * x_i_b for i in I)` and add the constraint that it must be `<= capacity * y_b`. This is implemented as `sum(weight_i * x_i_b) - capacity * y_b <= 0`.

### Step 4 - Define Objective
- Set the objective to minimize `sum(y_b for b in B)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of items"},
    {"name": "B", "description": "Set of potential bins (indexed 1..M)"}
  ],
  "parameters": [
    {"name": "weight_i", "index": "i in I", "description": "Weight of item i"},
    {"name": "capacity", "description": "Maximum weight capacity per bin"}
  ],
  "decision_variables": [
    {"name": "y_b", "index": "b in B", "type": "cp_model.BoolVar", "description": "True if bin b is used"},
    {"name": "x_i_b", "index": "i in I, b in B", "type": "cp_model.BoolVar", "description": "True if item i is assigned to bin b"}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum(y_b for b in B)"
  },
  "constraints": [
    {"name": "assign_once", "expression": "ExactlyOne(x_i_b for b in B)", "index": "i in I"},
    {"name": "link", "expression": "x_i_b <= y_b", "index": "i in I, b in B"},
    {"name": "capacity", "expression": "sum(weight_i * x_i_b for i in I) <= capacity * y_b", "index": "b in B"}
  ]
}
```

### Common Pitfalls
- Using integer variables instead of Boolean variables for `x_i_b` and `y_b`, which reduces solver performance.
- Incorrectly scaling the capacity constraint; ensure the right-hand side is `capacity * y_b`, not just `capacity`.
- Omitting the `ExactlyOne` constraint and using `sum(...) == 1`, which is valid but `ExactlyOne` is more explicit for CP-SAT.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for an exact, reproducible search. Solve the model once and interpret the results. If optimality is not proven within time limits, the best bound can be used to assess solution quality.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.parameters.max_time_in_seconds = 30`.
- Enable parallelism: `solver.parameters.num_search_workers = 8`.
- Set a random seed for reproducibility: `solver.parameters.random_seed = 42`.
- Enforce exact solving: `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Invoke `solver.Solve(model)`.
- Check the status: `status == cp_model.OPTIMAL`, `cp_model.FEASIBLE`, or `cp_model.UNKNOWN`.

### Step 3 - Extract and Analyze Solution
- If optimal or feasible, extract the objective value and variable values.
- Reconstruct bin loads by iterating over assignments.
- Validate constraints programmatically as a sanity check.

### Step 4 - Post-Solve Optimality Gap Analysis (if not optimal)
- If status is `FEASIBLE`, access `solver.BestObjectiveBound()` to compute the optimality gap.
- Use this gap to decide if further computation (e.g., increasing time limit) is warranted.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# Create variables y[b], x[i][b] as model.NewBoolVar()
# Add constraints: model.AddExactlyOne(x[i][:] for each i)
# Add linking: model.Add(x[i][b] <= y[b])
# Add capacity: model.Add(sum(weight[i] * x[i][b] for i) <= capacity * y[b])
# Set objective: model.Minimize(sum(y[:]))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    print(f"Optimal bins: {solver.ObjectiveValue()}")
    # Extract assignments
    for i in I:
        for b in B:
            if solver.Value(x[i][b]) > 0.5:
                # Record assignment
elif status == cp_model.FEASIBLE:
    print(f"Feasible bins: {solver.ObjectiveValue()}, Best bound: {solver.BestObjectiveBound()}")
else:
    print("No solution found.")
```

### Common Pitfalls
- Not setting `relative_gap_limit = 0.0`, causing the solver to stop early if a small gap is reached.
- Misinterpreting `UNKNOWN` status as infeasible; it often means the time limit was hit.
- Forgetting to check `solver.Value()` against a tolerance (e.g., `> 0.5`) when reading Boolean variable values.
