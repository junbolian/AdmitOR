---
name: Cardinality-Constrained Pairwise Selection
description: |
  Model and solve problems where exactly K items are selected to maximize a weighted sum over ordered or unordered pairs of selected items, using either auxiliary activation variables or direct quadratic objectives.
---

# Workflow 1 (Auxiliary Variable Linearization)

## Modeling stage

### Strategy Overview
This workflow linearizes the pairwise product of binary selection variables by introducing auxiliary activation variables and consistency constraints. It yields a pure linear integer program, compatible with any MIP solver.

### Step 1 - Define Core Selection Variables
- Create a binary decision variable `x[i]` for each candidate element `i` in set `N`.
- `x[i] = 1` indicates the element is selected.

### Step 2 - Enforce Cardinality
- Add a linear constraint `sum(x[i] for i in N) == K` to select exactly `K` elements.

### Step 3 - Define Pairwise Activation Variables
- For each relevant ordered pair `(i, j)` (or unordered pair `(i, j) with i < j`), create an auxiliary binary variable `y[(i, j)]`.
- This variable will represent the logical AND `x[i] * x[j]`.

### Step 4 - Link Activation to Selection
- Add three linear constraints for each pair `(i, j)` to enforce `y[(i, j)] == x[i] * x[j]`:
  1. `y[(i, j)] <= x[i]`
  2. `y[(i, j)] <= x[j]`
  3. `y[(i, j)] >= x[i] + x[j] - 1`

### Step 5 - Formulate Linear Objective
- Define the objective as the sum of weights `w[(i, j)]` multiplied by the corresponding activation variable `y[(i, j)]`.
- Maximize `sum(w[(i, j)] * y[(i, j)] for (i, j) in Pairs)`.

### Formulation Template
```json
{
  "sets": [
    "N: Set of candidate elements.",
    "Pairs: Set of ordered (or unordered) pairs (i, j) contributing to the objective."
  ],
  "parameters": [
    "K: Integer, exact number of elements to select.",
    "w[(i, j)]: Numeric weight for pair (i, j)."
  ],
  "decision_variables": [
    "x[i] ∈ {0, 1} ∀ i ∈ N: Selection indicator.",
    "y[(i, j)] ∈ {0, 1} ∀ (i, j) ∈ Pairs: Pairwise activation indicator."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(w[(i, j)] * y[(i, j)] for (i, j) in Pairs)"
  },
  "constraints": [
    "sum(x[i] for i in N) == K",
    "y[(i, j)] <= x[i] ∀ (i, j) ∈ Pairs",
    "y[(i, j)] <= x[j] ∀ (i, j) ∈ Pairs",
    "y[(i, j)] >= x[i] + x[j] - 1 ∀ (i, j) ∈ Pairs"
  ]
}
```

### Common Pitfalls
- Defining `Pairs` incorrectly (e.g., including self-pairs `(i,i)` or double-counting unordered pairs).
- Forgetting the `y[(i, j)] >= x[i] + x[j] - 1` constraint, which forces activation when both are selected.
- Using non-integer coefficients in the linear constraints, which can cause solver errors.

## Solving stage

### Strategy Overview
Build the linearized model using a solver-agnostic modeling library (e.g., OR-Tools CP-SAT) and solve as a MIP with standard optimality and time-limit parameters.

### Step 1 - Model Construction
- Instantiate the model object.
- Create `x` and `y` variables as Boolean/Binary types.
- Add the cardinality constraint as a linear sum equality.
- Add the three linear linking constraints for each pair in a loop.

### Step 2 - Solver Configuration
- Initialize the solver (e.g., `CpSolver`).
- Set key parameters: `max_time_in_seconds` (e.g., 30), `num_search_workers` (e.g., -1 for all cores), `random_seed` (e.g., 42), and `relative_gap_limit` (e.g., 0.0 for optimality).

### Step 3 - Solve and Check Status
- Call the solver's `Solve` method on the model.
- Check the status is `OPTIMAL` or `FEASIBLE` before extracting a solution. If not, return a structured error payload.

### Step 4 - Extract and Verify Solution
- Retrieve selected elements: `[i for i in N if solver.Value(x[i]) == 1]`.
- Compute the objective value from the solver.
- Optionally, verify by manually calculating the weighted sum from the selected elements to ensure consistency.

### Code Usage
```python
# Example using OR-Tools CP-SAT
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# 1. Create variables
x = {i: model.NewBoolVar(f"x_{i}") for i in N}
y = {(i, j): model.NewBoolVar(f"y_{i}_{j}") for (i, j) in Pairs}

# 2. Add cardinality constraint
model.Add(sum(x[i] for i in N) == K)

# 3. Add pairwise consistency constraints
for (i, j) in Pairs:
    model.Add(y[(i, j)] <= x[i])
    model.Add(y[(i, j)] <= x[j])
    model.Add(y[(i, j)] >= x[i] + x[j] - 1)

# 4. Set objective
model.Maximize(sum(w[(i, j)] * y[(i, j)] for (i, j) in Pairs))

# 5. Configure and solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = -1
solver.parameters.random_seed = 42
status = solver.Solve(model)

# 6. Handle result
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in N if solver.Value(x[i]) == 1]
    obj_value = solver.ObjectiveValue()
    # Output results
else:
    # Output error payload with status
```

### Common Pitfalls
- Not setting a time limit, risking excessive runtime for large instances.
- Misinterpreting solver status codes (e.g., `FEASIBLE` vs. `OPTIMAL`).
- Forgetting to enable multi-threading for performance.

# Workflow 2 (Direct Quadratic Formulation)

## Modeling stage

### Strategy Overview
This workflow models the pairwise product directly in the objective as a quadratic term `x[i] * x[j]`, avoiding auxiliary variables. It requires a solver capable of handling non-convex quadratic objectives with binary variables.

### Step 1 - Define Binary Selection Variables
- Create a binary decision variable `x[i]` for each candidate element `i` in set `N`.
- `x[i] = 1` indicates selection.

### Step 2 - Enforce Cardinality
- Add a linear constraint `sum(x[i] for i in N) == K` to select exactly `K` elements.

### Step 3 - Formulate Quadratic Objective
- Define the objective as the sum over all relevant pairs `(i, j)` of `w[i][j] * x[i] * x[j]`.
- For unordered pairs and symmetric weights, adjust the sum to avoid double-counting.

### Formulation Template
```json
{
  "sets": [
    "N: Set of candidate elements."
  ],
  "parameters": [
    "K: Integer, exact number of elements to select.",
    "w[i][j]: Numeric weight for pair (i, j)."
  ],
  "decision_variables": [
    "x[i] ∈ {0, 1} ∀ i ∈ N: Selection indicator."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(w[i][j] * x[i] * x[j] for i in N for j in N if i != j)"
  },
  "constraints": [
    "sum(x[i] for i in N) == K"
  ]
}
```

### Common Pitfalls
- Using this formulation with a solver that does not support non-convex quadratic objectives.
- Incorrectly handling the quadratic term for `i == j` if self-pairs are not intended.
- Overlooking the need to set a specific solver option (e.g., `NonConvex=2` for Gurobi).

## Solving stage

### Strategy Overview
Build the quadratic model using a modeling library (e.g., Pyomo) and solve with a compatible solver (e.g., Gurobi, CPLEX) configured to handle non-convex quadratics.

### Step 1 - Model Construction
- Instantiate a concrete model.
- Define the set `N` and binary variables `x[i]`.
- Add the cardinality constraint as a linear sum equality.
- Define the objective using a quadratic expression.

### Step 2 - Solver Selection and Configuration
- Select a solver that supports quadratic binary programming (e.g., `gurobi`).
- Set necessary options: `NonConvex=2` (for Gurobi), `TimeLimit` (e.g., 30), `MIPGap` (e.g., 0.0), `Threads` (e.g., 4), `Seed` (e.g., 42).

### Step 3 - Solve and Check Termination
- Call the solver.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`optimal` or `feasible`).

### Step 4 - Extract and Verify Solution
- Retrieve selected elements: `[i for i in N if pyo.value(x[i]) > 0.5]`.
- Obtain the objective value from the model.
- For small instances, validate optimality via brute-force enumeration of all K-combinations.

### Code Usage
```python
# Example using Pyomo with Gurobi
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
# 1. Define sets and variables
model.N = pyo.Set(initialize=N)
model.x = pyo.Var(model.N, domain=pyo.Binary)

# 2. Add cardinality constraint
model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.N) == K)

# 3. Define quadratic objective
def obj_rule(m):
    return sum(w[i][j] * m.x[i] * m.x[j] for i in m.N for j in m.N if i != j)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# 4. Solve
solver = pyo.SolverFactory('gurobi')
solver.options['NonConvex'] = 2
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = III
results = solver.solve(model, tee=False)

# 5. Handle result
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    obj_value = pyo.value(model.obj)
    # Output results
else:
    # Output error payload with termination condition
```

### Common Pitfalls
- Forgetting to set the `NonConvex` parameter, causing the solver to reject the model.
- Not setting a time limit, which can lead to long runtimes on difficult instances.
- Assuming the solver's default gap tolerance is zero; always set `MIPGap` explicitly for optimality.
