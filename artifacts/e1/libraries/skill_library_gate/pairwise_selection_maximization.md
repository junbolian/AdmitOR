---
name: Pairwise Selection Maximization
description: |
  Model and solve selection problems where the objective sums weighted pairwise interactions among selected items, subject to a cardinality constraint.
---

# Workflow 1 (Pyomo-HiGHS MILP)

## Modeling stage

### Strategy Overview
This workflow formulates the pairwise selection problem as a Mixed-Integer Linear Program (MILP) using Pyomo. It linearizes the quadratic interaction terms via auxiliary binary variables and standard linear constraints, suitable for open-source solvers like HiGHS.

### Step 1 - Define Core Selection Variables
- Create a set `I` representing all candidate items.
- Define binary decision variables `x[i]` for each `i` in `I`, where `x[i] = 1` indicates item `i` is selected.

### Step 2 - Define Pairwise Interaction Variables
- For each unordered pair `(i, j)` where `i < j`, define an auxiliary binary variable `y[(i, j)]`.
- This variable will be forced to `1` only if both `x[i]` and `x[j]` are `1`, capturing the pairwise interaction.

### Step 3 - Enforce Cardinality Constraint
- Add a linear constraint `sum(x[i] for i in I) == k`, where `k` is the exact number of items to select.

### Step 4 - Link Interaction to Selection Variables
- Add three linear constraints for each pair `(i, j)` to enforce `y[(i, j)] = x[i] * x[j]`:
  - `y[(i, j)] <= x[i]`
  - `y[(i, j)] <= x[j]`
  - `y[(i, j)] >= x[i] + x[j] - 1`

### Step 5 - Formulate Weighted Objective
- Define a parameter `weight[(i, j)]` representing the benefit (e.g., distance, utility) for the pair `(i, j)`.
- For asymmetric problems, ensure the parameter captures the total interaction for the unordered pair (e.g., `d_ij + d_ji`).
- Set the objective to `maximize sum(weight[(i, j)] * y[(i, j)] for all i < j)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of candidate items"},
    {"name": "P", "description": "Set of unordered pairs (i,j) where i < j"}
  ],
  "parameters": [
    {"name": "k", "description": "Cardinality (number of items to select)", "type": "integer"},
    {"name": "weight", "description": "Weight for unordered pair (i,j)", "indexed": "P", "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "description": "1 if item i is selected", "indexed": "I", "type": "binary"},
    {"name": "y", "description": "1 if both i and j are selected", "indexed": "P", "type": "binary"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[p] * y[p] for p in P)"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum(x[i] for i in I) == k"},
    {"name": "link_y_to_x1", "indexed": "P", "expression": "y[p] <= x[i]"},
    {"name": "link_y_to_x2", "indexed": "P", "expression": "y[p] <= x[j]"},
    {"name": "link_y_to_x3", "indexed": "P", "expression": "y[p] >= x[i] + x[j] - 1"}
  ]
}
```

### Common Pitfalls
- Assuming symmetric weights when problem data is asymmetric. Ensure the `weight` parameter sums contributions from both directions for each unordered pair.
- Attempting to use quadratic expressions (`x[i] * x[j]`) directly in the objective or constraints without linearization.
- Using complex or solver-specific linearization methods when the standard three-constraint approach is sufficient and portable.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via the `highs` interface. Configure solver parameters for optimality and runtime control, then extract and verify the solution.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver object using `SolverFactory('highs')`.
- Configure key parameters:
  - Set `time_limit` to control runtime.
  - Set `mip_rel_gap` to `0.0` to require proof of optimality.
  - Set `threads` to leverage parallel processing.

### Step 2 - Solve and Check Status
- Call the solver's `solve` method on the model.
- Check both `solver.status` and the model's `termination_condition`.
- Accept solutions with `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract and Verify Solution
- Extract selected items by iterating over `x[i]` variables and applying a threshold (e.g., `value > 0.5`).
- Retrieve the objective value from the model.
- Optionally, perform a manual verification by recalculating the objective from the selected items and pairwise weights to ensure model correctness.

### Step 4 - Handle Results and Errors
- Report the solution status (e.g., "OPTIMAL") and objective value.
- For result serialization (e.g., to JSON), convert tuple keys (like `(i, j)`) to strings if necessary to avoid serialization errors.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (model defined as per template)
# ...

# Instantiate solver
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
solver.options['threads'] = 4

# Solve
results = solver.solve(model)

# Check status and termination condition
from pyomo.opt import TerminationCondition
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    print("OPTIMAL")
elif results.solver.termination_condition == TerminationCondition.feasible:
    print("FEASIBLE")
else:
    print("SOLVE FAILED")

# Extract solution
selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
obj_val = pyo.value(model.obj)
print(f"Selected: {selected}")
print(f"Objective: {obj_val}")

# Optional verification
# ...
```

### Common Pitfalls
- Ignoring the distinction between `solver.status` and `termination_condition`; both must be checked to correctly interpret the solution.
- Using incorrect parameter names or values for the solver (e.g., `MIPGap` for HiGHS instead of `mip_rel_gap`).
- Not verifying the objective calculation manually, which can hide modeling errors in weight aggregation or variable linking.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
This workflow models the problem using Google OR-Tools CP-SAT solver, a constraint programming solver for integer problems. It employs the same linearization technique but uses CP-SAT's native variable and constraint API, which is efficient for large-scale binary optimization.

### Step 1 - Initialize Model and Create Selection Variables
- Create a `CpModel` object.
- For each item `i` in set `I`, create a binary variable `x[i]` using `model.NewBoolVar('x_i')`.

### Step 2 - Create Pairwise Interaction Variables
- For each unordered pair `(i, j)` where `i < j`, create an auxiliary binary variable `y[(i, j)]` using `model.NewBoolVar('y_ij')`.

### Step 3 - Add Cardinality Constraint
- Create a linear expression `sum(x[i] for i in I)`.
- Add the equality constraint `sum_expr == k` using `model.Add(sum_expr == k)`.

### Step 4 - Linearize Interaction with Linear Constraints
- For each pair `(i, j)`, add the three classic linearization constraints:
  - `model.Add(y[(i, j)] <= x[i])`
  - `model.Add(y[(i, j)] <= x[j])`
  - `model.Add(y[(i, j)] >= x[i] + x[j] - 1)`

### Step 5 - Define Maximization Objective
- Create a linear objective expression `sum(weight[(i, j)] * y[(i, j)] for all i < j)`.
- Use `model.Maximize(objective_expr)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of candidate items"},
    {"name": "P", "description": "Set of unordered pairs (i,j) where i < j"}
  ],
  "parameters": [
    {"name": "k", "description": "Cardinality (number of items to select)", "type": "integer"},
    {"name": "weight", "description": "Weight for unordered pair (i,j)", "indexed": "P", "type": "integer"}
  ],
  "decision_variables": [
    {"name": "x", "description": "1 if item i is selected", "indexed": "I", "type": "binary"},
    {"name": "y", "description": "1 if both i and j are selected", "indexed": "P", "type": "binary"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[p] * y[p] for p in P)"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum(x[i] for i in I) == k"},
    {"name": "link_y_to_x1", "indexed": "P", "expression": "y[p] <= x[i]"},
    {"name": "link_y_to_x2", "indexed": "P", "expression": "y[p] <= x[j]"},
    {"name": "link_y_to_x3", "indexed": "P", "expression": "y[p] >= x[i] + x[j] - 1"}
  ]
}
```

### Common Pitfalls
- Attempting to multiply variables directly (e.g., `x[i] * x[j]`) in constraints or the objective, which causes a `TypeError` in CP-SAT.
- Overcomplicating the linearization by using `AddMultiplicationEquality` when the standard three-constraint method is simpler and more robust.
- Using non-integer weights; CP-SAT requires the objective coefficients to be integers. Scale float weights appropriately.

## Solving stage

### Strategy Overview
Solve the CP-SAT model, handle solver statuses, and extract the binary variable assignments. CP-SAT provides detailed status codes that must be interpreted correctly.

### Step 1 - Create Solver and Set Parameters
- Instantiate a `CpSolver()` object.
- Optionally, set solver parameters like `CpSolver().parameters.max_time_in_seconds` for time limits.

### Step 2 - Solve and Interpret Status
- Call `solver.Solve(model)`.
- Check the returned status against `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, or `MODEL_INVALID`.
- A status of `MODEL_INVALID` indicates a modeling error (e.g., an invalid constraint), not a solver failure.

### Step 3 - Extract Solution Values
- If the status is `OPTIMAL` or `FEASIBLE`, iterate over `x` and `y` variables.
- Use `solver.Value(variable)` to get the solution value (0 or 1).
- Collect selected items where `solver.Value(x[i]) == 1`.

### Step 4 - Verify and Report Results
- Compute the objective value from the extracted `y` values and weights for verification.
- Report the solution status, selected items, and objective value.

### Code Usage
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Build model from formulation
# Create variables
x = {i: model.NewBoolVar(f'x_{i}') for i in I}
y = {}
for i, j in P:  # P is list of (i,j) tuples with i<j
    y[(i, j)] = model.NewBoolVar(f'y_{i}_{j}')

# Cardinality constraint
model.Add(sum(x[i] for i in I) == k)

# Linearization constraints
for (i, j) in P:
    model.Add(y[(i, j)] <= x[i])
    model.Add(y[(i, j)] <= x[j])
    model.Add(y[(i, j)] >= x[i] + x[j] - 1)

# Objective
objective_expr = sum(weight[p] * y[p] for p in P)
model.Maximize(objective_expr)

# Solve
solver = cp_model.CpSolver()
# Set time limit if needed
solver.parameters.max_time_in_seconds = 30.0

status = solver.Solve(model)

# Check status
if status == cp_model.OPTIMAL:
    print("OPTIMAL")
elif status == cp_model.FEASIBLE:
    print("FEASIBLE")
elif status == cp_model.MODEL_INVALID:
    print("MODEL_INVALID - check model logic")
    exit(1)
else:
    print("SOLVE FAILED")

# Extract solution
selected = [i for i in I if solver.Value(x[i]) == 1]
obj_val = solver.ObjectiveValue()
print(f"Selected: {selected}")
print(f"Objective: {obj_val}")

# Verification (optional)
# ...
```

### Common Pitfalls
- Misinterpreting `MODEL_INVALID` as a solver failure; it signals a problem in the model definition that requires debugging.
- Not using integer coefficients in the objective; CP-SAT requires integer weights. Convert floats to integers by scaling.
- Ignoring the need to verify the objective calculation, especially for asymmetric weights, to ensure the model correctly captures the problem intent.
