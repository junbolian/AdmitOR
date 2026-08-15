---
name: Pairwise Selection Maximization
description: |
  Model and solve binary selection problems with pairwise interaction rewards, using linearization of quadratic terms and cardinality constraints, implemented via MIP or CP-SAT solvers.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as a linearized binary program suitable for constraint programming solvers. Use auxiliary variables to represent pairwise selections, enforcing logic with linear constraints, and maximize a weighted sum over these pairs under a cardinality constraint.

### Step 1 - Define Core Selection Variables
- Create a binary variable `x[i]` for each element `i` in the candidate set `N`. `x[i] = 1` indicates selection.
- Example: `x = {i: model.NewBoolVar(f'x_{i}') for i in N}`

### Step 2 - Define Pairwise Auxiliary Variables
- For each relevant pair `(i, j)` (e.g., all unordered pairs `i<j`), create a binary variable `z[(i, j)]`.
- This variable should be `1` if and only if both `x[i]` and `x[j]` are `1`.
- Example: `z = {(i, j): model.NewBoolVar(f'z_{i}_{j}') for (i, j) in pairs}`

### Step 3 - Enforce Cardinality Constraint
- Add a linear equality constraint to select exactly `K` elements.
- Example: `model.Add(sum(x[i] for i in N) == K)`

### Step 4 - Linearize Pairwise Logic
- For each pair `(i, j)`, add three linear constraints to enforce `z[(i, j)] = x[i] ∧ x[j]`:
  - `z[(i, j)] <= x[i]`
  - `z[(i, j)] <= x[j]`
  - `z[(i, j)] >= x[i] + x[j] - 1`
- Example: Loop over pairs and add each constraint to the model.

### Step 5 - Formulate the Objective
- Maximize the weighted sum of the pairwise variables: `sum(weight[(i, j)] * z[(i, j)] for (i, j) in pairs)`.
- Ensure the weight dictionary `weight` is correctly defined for the relevant pair set.

### Formulation Template
```json
{
  "sets": [
    "N: Set of candidate elements.",
    "P: Set of relevant pairs (e.g., unordered i<j)."
  ],
  "parameters": [
    "K: Exact number of elements to select.",
    "weight[p]: Reward for selecting pair p."
  ],
  "decision_variables": [
    "x[i] ∈ {0,1}: Selection of element i.",
    "z[p] ∈ {0,1}: Selection of pair p (auxiliary)."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[p] * z[p] for p in P)"
  },
  "constraints": [
    "sum(x[i] for i in N) == K",
    "z[p] <= x[i] for all p=(i,j) in P",
    "z[p] <= x[j] for all p=(i,j) in P",
    "z[p] >= x[i] + x[j] - 1 for all p=(i,j) in P"
  ]
}
```

### Common Pitfalls
- Using unordered pairs in `P` but having asymmetric weights; ensure the pair set matches the weight dictionary structure.
- Forgetting to add all three linearization constraints, which can lead to incorrect `z` values.
- Not verifying that the defined pair set `P` aligns with the problem's semantics (directed vs. undirected interactions).

## Solving stage

### Strategy Overview
Solve the formulated model using OR-Tools' CP-SAT solver. Configure for deterministic, bounded search, extract the solution, and perform verification checks.

### Step 1 - Configure the Solver
- Instantiate `CpSolver()` and set key parameters for performance and reproducibility.
- Example:
```python
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0
```

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve(model)` and capture the status.
- Check if the result is `OPTIMAL` or `FEASIBLE` before proceeding.
- Example: `status = solver.Solve(model)`

### Step 3 - Extract and Verify Solution
- Extract values for `x[i]` using `solver.Value(x[i])`.
- Collect selected elements where the value is 1.
- Optionally, verify that extracted `z` values satisfy the logical AND relationship with the selected `x` values.
- Compute the objective value from the extracted solution for cross-checking.

### Step 4 - Output Results
- Print or return the objective value and the list of selected elements.
- Include the solver status for debugging.

### Code Usage
```python
import ortools.sat.python.cp_model as cp

# Build model from formulation
model = cp.CpModel()
N = range(num_elements)
P = [(i, j) for i in N for j in N if i < j]  # Example: unordered pairs
x = {i: model.NewBoolVar(f'x_{i}') for i in N}
z = {p: model.NewBoolVar(f'z_{p[0]}_{p[1]}') for p in P}
model.Add(sum(x[i] for i in N) == K)
for (i, j) in P:
    model.Add(z[(i, j)] <= x[i])
    model.Add(z[(i, j)] <= x[j])
    model.Add(z[(i, j)] >= x[i] + x[j] - 1)
model.Maximize(sum(weight[p] * z[p] for p in P))

# Solve with status / termination checks
solver = cp.CpSolver()
# ... set parameters as above
status = solver.Solve(model)
if status in (cp.OPTIMAL, cp.FEASIBLE):
    selected = [i for i in N if solver.Value(x[i]) == 1]
    obj_value = solver.ObjectiveValue()
    print(f"Objective: {obj_value}, Selected: {selected}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.
- Misinterpreting solver status codes; only `OPTIMAL` and `FEASIBLE` indicate a valid solution.
- Failing to verify the logical consistency of the extracted solution, especially for the auxiliary `z` variables.

# Workflow 2 (MIP with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program using Pyomo's abstract or concrete modeling. Employ the same linearization technique for pairwise interactions, defining ordered pairs to handle potential asymmetry, and solve with a high-performance MIP solver like Gurobi or HiGHS.

### Step 1 - Define Abstract Sets and Parameters
- Declare a Pyomo `Set` `N` for elements and a `Set` `P` for ordered pairs `(i,j)` where `i != j`.
- Define a `Param` `w` over `P` to hold pairwise weights.
- Example: `m.P = pyo.Set(initialize=[(i,j) for i in N for j in N if i != j], dimen=2)`

### Step 2 - Create Decision Variables
- Create binary variable `x[i]` for element selection.
- Create auxiliary binary variable `z[i,j]` for each ordered pair in `P`.
- Example: `m.x = pyo.Var(m.N, domain=pyo.Binary)`

### Step 3 - Enforce Exact Selection Count
- Add a cardinality constraint using a `Constraint` object: `sum(m.x[i] for i in m.N) == k`.
- Example: `m.cardinality = pyo.Constraint(expr=sum(m.x[i] for i in m.N) == k)`

### Step 4 - Linearize Pairwise Product
- For each ordered pair `(i,j)`, add the three standard linearization constraints via `Constraint` rules.
- Example rules: `m.z_le_xi = pyo.Constraint(m.P, rule=lambda m, i, j: m.z[i,j] <= m.x[i])`

### Step 5 - Define Maximization Objective
- Create an `Objective` to maximize `sum(m.w[i,j] * m.z[i,j] for (i,j) in m.P)`.

### Formulation Template
```json
{
  "sets": [
    "N: Set of candidate elements.",
    "P: Set of ordered pairs (i,j) where i != j."
  ],
  "parameters": [
    "k: Exact number of elements to select.",
    "w[p]: Reward for selecting ordered pair p."
  ],
  "decision_variables": [
    "x[i] ∈ {0,1}: Selection of element i.",
    "z[p] ∈ {0,1}: Selection of ordered pair p (auxiliary)."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(w[p] * z[p] for p in P)"
  },
  "constraints": [
    "sum(x[i] for i in N) == k",
    "z[i,j] <= x[i] for all (i,j) in P",
    "z[i,j] <= x[j] for all (i,j) in P",
    "z[i,j] >= x[i] + x[j] - 1 for all (i,j) in P"
  ]
}
```

### Common Pitfalls
- Defining the pair set `P` as unordered when weights are asymmetric, leading to an incorrect objective.
- Using inefficient `Constraint` rules that slow down model construction for large sets.
- Not leveraging Pyomo's `Param` for weights, which can cause errors if weights are missing for some pairs.

## Solving stage

### Strategy Overview
Instantiate a MIP solver (e.g., HiGHS, Gurobi) via Pyomo's `SolverFactory`. Configure for optimality and reproducibility, solve the model, and rigorously verify the solution's logical consistency.

### Step 1 - Select and Configure Solver
- Use `SolverFactory` to create a solver instance (e.g., `'highs'`, `'gurobi'`).
- Set key options: time limit, optimality gap (`MIPGap`), thread count, and random seed.
- Example: `solver.options['time_limit'] = 30`

### Step 2 - Solve and Capture Termination Condition
- Call `solver.solve(model, tee=False)`.
- Check the solver status (`status`) and termination condition (`termination_condition`) from the results object.
- Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Extract and Validate Solution Values
- Extract `x[i]` values using `pyo.value(m.x[i]) > 0.5`.
- Collect the list of selected elements.
- Manually compute the objective from selected elements and the weight matrix to verify against `pyo.value(m.obj)`.
- Optionally, verify that `z[i,j]` equals the product of the corresponding `x` values.

### Step 4 - Implement Fallback Verification
- For small problem instances, implement a brute-force enumeration using `itertools.combinations` to verify the MIP solution's optimality.
- This serves as a powerful debugging tool and validation step.

### Code Usage
```python
import pyomo.environ as pyo
import itertools

# Build model from formulation
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=range(num_elements))
model.P = pyo.Set(initialize=[(i,j) for i in model.N for j in model.N if i != j], dimen=2)
model.w = pyo.Param(model.P, initialize=weight_dict)
model.x = pyo.Var(model.N, domain=pyo.Binary)
model.z = pyo.Var(model.P, domain=pyo.Binary)
model.obj = pyo.Objective(expr=sum(model.w[p] * model.z[p] for p in model.P), sense=pyo.maximize)
model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.N) == k)
def rule_le1(m, i, j):
    return m.z[i,j] <= m.x[i]
model.con_le1 = pyo.Constraint(model.P, rule=rule_le1)
# ... similarly add rule_le2 and rule_ge

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)
if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    obj_value = pyo.value(model.obj)
    print(f"Objective: {obj_value}, Selected: {selected}")
    # Optional brute-force verification for small n,k
    if len(model.N) <= 20:
        best_val, best_combo = max((sum(weight_dict.get((i,j),0) for i in combo for j in combo if i!=j), combo) for combo in itertools.combinations(model.N, k))
        print(f"Brute-force verification: Best={best_val}, Combo={best_combo}")
else:
    print("Solver failed to find a feasible solution.")
```

### Common Pitfalls
- Not checking both `solver.status` and `solver.termination_condition`, leading to acceptance of failed solves.
- Using `pyo.value()` on variables before ensuring the solver has populated a solution, which may raise errors.
- Overlooking the need for manual objective verification, which can catch modeling errors in the weight parameter assignment.
