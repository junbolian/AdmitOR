---
name: Binary Selection with Capacity Constraint
description: |
  Model and solve binary selection problems with a single linear capacity constraint, using either a dedicated MIP solver or a fallback exact algorithm for small instances.
---

# Workflow 1 (MIP Solver with OR-Tools / Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem as a standard 0-1 knapsack using a Mixed-Integer Programming (MIP) framework. This approach leverages efficient, general-purpose solvers and is suitable for a wide range of problem sizes.

### Step 1 - Define Sets and Parameters
- Define a set `ITEMS` to index all selectable items.
- Create parallel data structures: a parameter `value_i` for benefit and `weight_i` for resource consumption for each item `i` in `ITEMS`.
- Define a scalar parameter `capacity` representing the total available resource.

### Step 2 - Declare Decision Variables
- Create a binary decision variable `x_i` for each item `i` in `ITEMS`. `x_i = 1` if item `i` is selected, `0` otherwise.

### Step 3 - Formulate Objective and Constraint
- Formulate the linear objective: Maximize `sum(value_i * x_i for i in ITEMS)`.
- Formulate the linear capacity constraint: `sum(weight_i * x_i for i in ITEMS) <= capacity`.

### Formulation Template
```json
{
  "sets": ["ITEMS"],
  "parameters": ["value_i", "weight_i", "capacity"],
  "decision_variables": ["x_i ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(value_i * x_i for i in ITEMS)"
  },
  "constraints": ["sum(weight_i * x_i for i in ITEMS) <= capacity"]
}
```

### Common Pitfalls
- Using inconsistent indexing between parameters and variables, leading to incorrect model construction.
- Forgetting to set the objective sense to `max`, resulting in a minimization problem.
- Not documenting the units of `weight_i` and `capacity`, which can cause constraint violation errors.

## Solving stage

### Strategy Overview
Use an open-source MIP solver (e.g., CBC, SCIP) via a modeling interface (OR-Tools or Pyomo). Configure the solver for optimality, implement robust status checking, and extract the solution for validation and reporting.

### Step 1 - Instantiate Solver and Build Model
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("CBC")` or `pyo.SolverFactory("cbc")`).
- Programmatically build the model using the formulation: create variables, set the objective, and add the constraint.

### Step 2 - Configure Solver and Solve
- Set practical solver limits: a time limit (`solver.SetTimeLimit(ms)` or `options["seconds"]`) and the number of threads.
- For proven optimality, set the relative optimality gap to zero (`solver.SetSolverSpecificParametersAsString("ratio 0")` or `options["ratio"] = 0.0`).
- Call the solver's `Solve()` or `solve()` method.

### Step 3 - Check Status and Extract Solution
- Check the solver status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`). Proceed only if status indicates a feasible solution was found.
- Extract the objective value from the solver.
- Identify selected items by filtering variables where `solution_value() > 0.5` or `pyo.value() > 0.5`.
- Compute derived metrics (total weight used, remaining capacity) from the selected subset for validation.

### Step 4 - Validate and Report
- Recompute the total value and weight from the selected items to verify against the solver's objective and constraint.
- Report the solution: selected items, total value, total weight, capacity utilization, and solver status/metadata.

### Code Usage
```python
# Example using OR-Tools (conceptual)
from ortools.linear_solver import pywraplp

# 1. Instantiate Solver
solver = pywraplp.Solver.CreateSolver("CBC")
# 2. Build Model (using placeholder data: values, weights, capacity)
x = {}
for i in ITEMS:
    x[i] = solver.IntVar(0, 1, f'x_{i}')
# Capacity constraint
solver.Add(solver.Sum([weights[i] * x[i] for i in ITEMS]) <= capacity)
# Objective
objective = solver.Objective()
for i in ITEMS:
    objective.SetCoefficient(x[i], values[i])
objective.SetMaximization()
# 3. Configure and Solve
solver.SetTimeLimit(30000)  # 30 seconds in ms
status = solver.Solve()
# 4. Check Status and Extract
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    selected = [i for i in ITEMS if x[i].solution_value() > 0.5]
    total_value = objective.Value()
    # ... validation and reporting
else:
    # Handle infeasible or error status
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Accessing solution values without first checking the solver status, which may cause runtime errors.
- Using a loose optimality gap, which may return a suboptimal solution.
- Not setting a time limit, allowing the solver to run indefinitely on large or difficult instances.

# Workflow 2 (Exact Algorithm Fallback)

## Modeling stage

### Strategy Overview
Model the problem using the same canonical 0-1 knapsack formulation, but prepare for solving via exact algorithms (brute-force enumeration or dynamic programming). This workflow is specifically designed for small to moderate instances or as a verification/fallback method when a MIP solver is unavailable or fails.

### Step 1 - Structure Problem Data
- Organize item data (`values`, `weights`) into lists or arrays indexed from `0` to `n_items-1`.
- Define the `capacity` as an integer or float.

### Step 2 - Adopt Algorithm-Compatible Form
- The model remains identical: binary selection variables, a linear objective, and a linear capacity constraint.
- Recognize that the solving algorithm will implicitly handle these model components.

### Formulation Template
```json
{
  "sets": ["ITEMS"],
  "parameters": ["value_i", "weight_i", "capacity"],
  "decision_variables": ["x_i ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(value_i * x_i for i in ITEMS)"
  },
  "constraints": ["sum(weight_i * x_i for i in ITEMS) <= capacity"]
}
```

### Common Pitfalls
- Attempting to use exhaustive search (`2^n` subsets) for large `n` (>25), leading to prohibitive runtime.
- Not ensuring that `weights` and `capacity` are of compatible numeric types (e.g., integers for DP), which can cause algorithm failure.

## Solving stage

### Strategy Overview
Solve the problem using a Python-native exact algorithm. For very small `n` (≤20), use brute-force enumeration. For moderate `n` where weights are integer, use dynamic programming (DP). Always include a verification step.

### Step 1 - Select and Apply Algorithm
- If `n <= 20`: Enumerate all `2^n` subsets using `itertools.combinations` or bitmask iteration. Evaluate each subset's weight and value, keeping the feasible subset with maximum value.
- If `n > 20` and weights are integers: Implement a DP algorithm. Build a table `dp[i][w]` representing the maximum value achievable with the first `i` items and capacity `w`. Backtrack to find the optimal subset.

### Step 2 - Verify Solution Feasibility and Optimality
- For the returned subset, compute the total weight and verify it is ≤ `capacity`.
- For DP, the optimal value is given by `dp[n_items][capacity]`. Verify the backtracked subset matches this value.
- For small `n`, cross-validate the brute-force result with a greedy heuristic (e.g., sorting by value-to-weight ratio) as a sanity check.

### Step 3 - Report Results
- Report the selected items, total value, total weight used, and remaining capacity.
- Include the method used (e.g., "Brute-Force", "DP") and its runtime characteristics in the output.

### Code Usage
```python
# Example using Dynamic Programming (for integer weights)
def solve_knapsack_dp(values, weights, capacity):
    n = len(values)
    # DP table initialization
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        val, wt = values[i-1], weights[i-1]
        for w in range(capacity + 1):
            if wt > w:
                dp[i][w] = dp[i-1][w]
            else:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt] + val)
    # Backtrack to find selected items
    optimal_value = dp[n][capacity]
    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(i-1)
            w -= weights[i-1]
    selected.reverse()
    total_weight = sum(weights[i] for i in selected)
    return optimal_value, selected, total_weight

# Usage with placeholder data
# values = [...], weights = [...], capacity = ...
opt_val, selected_items, used_weight = solve_knapsack_dp(values, weights, capacity)
# Verification
assert used_weight <= capacity
assert opt_val == sum(values[i] for i in selected_items)
```

### Common Pitfalls
- Using DP with non-integer weights, requiring scaling which can lead to precision errors or large tables.
- Forgetting to reverse the backtracking list, resulting in selected items in reverse order.
- Not adding a verification step, potentially missing errors in the algorithm implementation.
