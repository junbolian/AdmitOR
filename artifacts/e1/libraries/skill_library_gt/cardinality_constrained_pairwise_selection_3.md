---
name: Cardinality-Constrained Pairwise Selection
description: |
  Model and solve combinatorial selection problems with pairwise interaction objectives under a strict cardinality constraint.

---

# Workflow 1 (Linearized MILP with Auxiliary Pairwise Variables)

## Modeling stage

### Strategy Overview
This workflow linearizes the quadratic pairwise objective by introducing auxiliary binary variables for each pair, enabling solution with standard MILP solvers. It is robust and solver-agnostic.

### Step 1 - Define Core Selection Variables
- Create a binary decision variable `x[i]` for each element `i` in the set `N`. `x[i] = 1` indicates the element is selected.
- This directly implements the `binary_selection` requirement.

### Step 2 - Enforce Cardinality Constraint
- Add a single linear constraint: `sum_{i in N} x[i] == K`, where `K` is the required number of selected elements.
- This enforces the `cardinality_constraint`.

### Step 3 - Linearize Pairwise Interactions
- For each ordered pair `(i, j)` where `i != j`, create an auxiliary binary variable `y[i,j]`.
- Add three linear `pairwise_consistency` constraints to enforce `y[i,j] = x[i] * x[j]`:
  - `y[i,j] <= x[i]`
  - `y[i,j] <= x[j]`
  - `y[i,j] >= x[i] + x[j] - 1`

### Step 4 - Formulate Linear Objective
- Define the objective to `maximize sum_{i != j} w[i,j] * y[i,j]`, where `w[i,j]` is the given pairwise weight.
- This achieves `maximize_weighted_pairwise_sum` as a linear expression.

### Formulation Template
```json
{
  "sets": [
    "N: Set of all candidate elements.",
    "P: Set of ordered pairs (i,j) where i in N, j in N, i != j."
  ],
  "parameters": [
    "K: Integer, exact number of elements to select.",
    "w[i,j]: Float, weight for the contribution of pair (i,j)."
  ],
  "decision_variables": [
    "x[i]: Binary, 1 if element i is selected.",
    "y[i,j]: Binary, 1 if both i and j are selected (i != j)."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{(i,j) in P} w[i,j] * y[i,j]"
  },
  "constraints": [
    "cardinality: sum_{i in N} x[i] == K",
    "link_lower_i: y[i,j] <= x[i] for all (i,j) in P",
    "link_lower_j: y[i,j] <= x[j] for all (i,j) in P",
    "link_upper: y[i,j] >= x[i] + x[j] - 1 for all (i,j) in P"
  ]
}
```

### Common Pitfalls
- Creating `y` variables for `i == j`, which is unnecessary and adds model bloat.
- Forgetting the `link_upper` constraint, which incorrectly allows `y[i,j] = 0` when both `x[i]` and `x[j]` are 1.
- Using ordered pairs when weights are symmetric, which doubles the variable count unnecessarily; use unordered pairs `i < j` and adjust the objective coefficient to `(w[i,j] + w[j,i])`.

## Solving stage

### Strategy Overview
Solve the linearized MILP using a high-performance MIP solver (e.g., CP-SAT, CBC, Gurobi) with appropriate configuration for optimality and runtime control.

### Step 1 - Instantiate Model and Variables
- Create a solver-specific model object.
- Add `x[i]` and `y[i,j]` as binary variables.

### Step 2 - Add Constraints and Objective
- Add the cardinality and pairwise consistency constraints as defined in the model.
- Set the maximization objective using the linear expression of `y` variables.

### Step 3 - Configure and Execute Solver
- Set solver parameters: `time_limit` for runtime control, `mip_gap` (or `rel_gap`) to 0.0 for exact optimality, and `threads` for parallel processing.
- Call the solver's `solve` method.

### Step 4 - Validate and Extract Solution
- Check the solver status is `OPTIMAL` or `FEASIBLE` before extracting results.
- Extract selected elements where `x[i].solution_value() > 0.5`.
- Compute the objective value from the raw `x` values as a verification step: `sum_{i != j} w[i,j] * x[i] * x[j]`.
- For small `N`, perform brute-force enumeration to confirm optimality.

### Code Usage
```python
# Example using OR-Tools CP-SAT
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# 1. Create variables
x = {i: model.NewBoolVar(f"x_{i}") for i in N}
y = {}
for i in N:
    for j in N:
        if i != j:
            y[(i, j)] = model.NewBoolVar(f"y_{i}_{j}")
# 2. Add cardinality constraint
model.Add(sum(x.values()) == K)
# 3. Add pairwise consistency constraints
for (i, j), var in y.items():
    model.Add(var <= x[i])
    model.Add(var <= x[j])
    model.Add(var >= x[i] + x[j] - 1)
# 4. Set objective
objective_terms = [w[(i, j)] * var for (i, j), var in y.items()]
model.Maximize(sum(objective_terms))
# 5. Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = time_limit
solver.parameters.num_search_workers = threads
status = solver.Solve(model)
# 6. Check status and extract solution
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected = [i for i in N if solver.Value(x[i]) > 0.5]
    # Verification: compute objective from x values
    computed_obj = sum(w[(i, j)] * solver.Value(x[i]) * solver.Value(x[j]) for i in N for j in N if i != j)
```

### Common Pitfalls
- Not checking solver status, leading to errors when trying to access values from an infeasible or error state.
- Setting an insufficient `time_limit` for larger instances, causing premature termination without a good solution.
- Assuming the solver's reported objective value is correct without verification against the original quadratic formula.

# Workflow 2 (Native Quadratic Formulation)

## Modeling stage

### Strategy Overview
This workflow models the pairwise objective directly as a quadratic function of the binary selection variables, leveraging solvers that support quadratic binary programming (e.g., Gurobi, CP-SAT). It is more concise and can be more efficient for supported solvers.

### Step 1 - Define Selection Variables
- Create binary decision variables `x[i]` for each element `i` in `N`.

### Step 2 - Enforce Cardinality Constraint
- Add the linear constraint: `sum_{i in N} x[i] == K`.

### Step 3 - Formulate Quadratic Objective
- Define the objective directly as `maximize sum_{i != j} w[i,j] * x[i] * x[j]`.
- This is a direct implementation of `maximize_weighted_pairwise_sum` without auxiliary variables.

### Formulation Template
```json
{
  "sets": [
    "N: Set of all candidate elements."
  ],
  "parameters": [
    "K: Integer, exact number of elements to select.",
    "w[i,j]: Float, weight for the contribution of pair (i,j) where i != j."
  ],
  "decision_variables": [
    "x[i]: Binary, 1 if element i is selected."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in N} sum_{j in N, j != i} w[i,j] * x[i] * x[j]"
  },
  "constraints": [
    "cardinality: sum_{i in N} x[i] == K"
  ]
}
```

### Common Pitfalls
- Using a solver that does not support non-convex quadratic objectives, resulting in an error or incorrect solution.
- Forgetting to exclude the `i == j` terms from the objective sum if self-interaction weights are not defined or are zero.
- Incorrectly handling symmetric weights by double-counting; the formulation `sum_{i<j} (w[i,j] + w[j,i]) * x[i] * x[j]` is equivalent and more efficient.

## Solving stage

### Strategy Overview
Solve the quadratic binary program using a solver with explicit support for this problem class (e.g., Gurobi with `NonConvex=2`, or OR-Tools CP-SAT which internally handles quadratic objectives). Configure the solver for binary quadratic optimization.

### Step 1 - Build Model with Quadratic Expression
- Instantiate a model from a framework that supports quadratic objectives (e.g., Pyomo, Gurobi direct API).
- Add variables and the cardinality constraint.
- Define the objective using a native quadratic expression.

### Step 2 - Configure Quadratic Solver Settings
- For solvers like Gurobi, set the parameter `NonConvex=2` to handle non-convex quadratic terms.
- Set standard MIP parameters: `TimeLimit`, `MIPGap=0.0`, `Threads`, and optionally `Seed` for reproducibility.

### Step 3 - Solve and Check Status
- Invoke the solver.
- Check the termination condition is `OPTIMAL` or `FEASIBLE`.

### Step 4 - Extract and Verify Solution
- Retrieve the values of `x[i]` to determine selected elements.
- Manually compute the quadratic objective value from the selected `x` values as a critical verification step.
- For validation, compare against brute-force enumeration for small instances.

### Code Usage
```python
# Example using Pyomo with Gurobi
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=N)
model.x = pyo.Var(model.N, domain=pyo.Binary)
# Cardinality constraint
model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.N) == K)
# Quadratic objective
def obj_rule(m):
    total = 0.0
    for i in m.N:
        for j in m.N:
            if i != j:
                total += w[(i, j)] * m.x[i] * m.x[j]
    return total
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)
# Solve
solver = pyo.SolverFactory('gurobi')
solver.options['NonConvex'] = 2
solver.options['TimeLimit'] = time_limit
solver.options['MIPGap'] = 0.0
results = solver.solve(model, tee=False)
# Check status and extract
status = results.solver.status
term = results.solver.termination_condition
if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    # Verification: compute objective from x values
    computed_obj = sum(w[(i, j)] * pyo.value(model.x[i]) * pyo.value(model.x[j]) for i in model.N for j in model.N if i != j)
```

### Common Pitfalls
- Failing to set the `NonConvex` parameter for Gurobi, leading to an error for non-convex quadratic problems.
- Not verifying the solver's objective value against a manual calculation, which can reveal modeling errors in the quadratic expression.
- Assuming all solvers accept the same quadratic expression syntax; always consult the specific solver's documentation.
