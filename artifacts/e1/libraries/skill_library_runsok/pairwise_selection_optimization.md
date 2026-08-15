---
name: Pairwise Selection Optimization
description: |
  Model and solve selection problems where the objective is a weighted sum over pairs of selected items, subject to a fixed selection count, using binary variables and linearized pairwise logic.

---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Formulate the problem for Google's CP-SAT solver, a constraint programming and SAT-based tool designed for discrete optimization. The model uses native Boolean variables and linear constraints to enforce selection logic and pairwise relationships.

### Step 1 - Define Core Variables
- Create a binary selection variable `x[i]` for each element `i` in the set `N` using `model.NewBoolVar()`.
- Create an auxiliary binary pairwise variable `z[(i, j)]` for each ordered pair `(i, j)` where `i != j` to represent the conjunction of two selections.

### Step 2 - Enforce Selection Cardinality
- Add a linear equality constraint to fix the total number of selected elements: `sum(x[i] for i in N) == K`, where `K` is the required count.

### Step 3 - Linearize Pairwise Logic
- For each pair `(i, j)`, add three linear constraints to enforce `z[(i, j)] == x[i] * x[j]`:
  - `z[(i, j)] <= x[i]`
  - `z[(i, j)] <= x[j]`
  - `z[(i, j)] >= x[i] + x[j] - 1`

### Step 4 - Formulate Objective
- Define the objective as maximizing the sum of weighted pairwise contributions: `sum(d[(i, j)] * z[(i, j)] for all (i, j) in P)`, where `d` is a dictionary of pairwise weights.

### Formulation Template
```json
{
  "sets": [
    "N: List of candidate elements.",
    "P: List of ordered pairs (i, j) where i, j in N and i != j."
  ],
  "parameters": [
    "d: Dictionary mapping pair (i, j) to its weight/value.",
    "K: Integer, the exact number of elements to select."
  ],
  "decision_variables": [
    "x[i]: Binary, 1 if element i is selected.",
    "z[(i, j)]: Binary, 1 if both i and j are selected."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(d[(i, j)] * z[(i, j)] for (i, j) in P)"
  },
  "constraints": [
    "Cardinality: sum(x[i] for i in N) == K",
    "Pairwise Upper Bound 1: z[(i, j)] <= x[i] for all (i, j) in P",
    "Pairwise Upper Bound 2: z[(i, j)] <= x[j] for all (i, j) in P",
    "Pairwise Lower Bound: z[(i, j)] >= x[i] + x[j] - 1 for all (i, j) in P"
  ]
}
```

### Common Pitfalls
- Forgetting to define `z` for both ordered pairs `(i, j)` and `(j, i)` if the objective is symmetric; define the set `P` accordingly.
- Creating an excessive number of `z` variables for large `N`; consider symmetry reduction if weights are symmetric (`d[(i,j)] == d[(j,i)]`).
- Not pre-computing the set of pairs `P`, leading to repeated generation during model building.

## Solving stage

### Strategy Overview
Solve the model using the `ortools.sat.python.cp_model` interface. Configure the solver for optimality, set resource limits, and implement robust solution extraction and verification.

### Step 1 - Configure Solver Parameters
- Instantiate `cp_model.CpSolver()`.
- Set `solver.parameters.max_time_in_seconds` to a reasonable limit.
- Set `solver.parameters.num_search_workers` for parallel search.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to search for proven optimal solutions.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the result status against `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. Handle `cp_model.INFEASIBLE` or `cp_model.MODEL_INVALID` appropriately.

### Step 3 - Extract and Verify Solution
- Extract selected elements: `selected = [i for i in N if solver.Value(x[i]) == 1]`.
- Verify cardinality: `len(selected) == K`.
- Optionally, recompute the objective value from the extracted `selected` list and the weight dictionary `d` to cross-validate the solver's reported objective value.

### Step 4 - Validate with Enumeration (Small Instances)
- For small `N` and `K`, implement brute-force enumeration using `itertools.combinations` to verify optimality and build confidence in the model.

### Code Usage
```python
from ortools.sat.python import cp_model
import itertools

# Build model
model = cp_model.CpModel()
# ... implement modeling steps using the Formulation Template ...

# Solve
solver = cp_model.CpSolver()
# Set parameters
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

# Check status and extract solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in N if solver.Value(x[i]) == 1]
    objective_value = solver.ObjectiveValue()
    # Verification logic...
else:
    # Handle infeasible or error status
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Misinterpreting `FEASIBLE` as `OPTIMAL`; for reporting, distinguish between "best found" and "proven optimal".
- Setting an unrealistic time limit for the instance size; monitor solve time and adjust.

# Workflow 2 (MIP via Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using the Pyomo modeling library. This approach provides a declarative, solver-agnostic interface, suitable for use with commercial (e.g., Gurobi) and open-source (e.g., HiGHS, GLPK) solvers.

### Step 1 - Declare Sets and Parameters
- Define Pyomo `Set` objects for the element list `N` and the pair set `P`.
- Declare a `Param` or Python dictionary `d` for pairwise weights.
- Define parameter `K` for the selection count.

### Step 2 - Define Decision Variables
- Create binary variable `m.x[i]` for `i in N` using `pyo.Var(domain=pyo.Binary)`.
- Create binary variable `m.z[i, j]` for `(i, j) in P` similarly.

### Step 3 - Enforce Cardinality Constraint
- Add a single linear constraint: `sum(m.x[i] for i in m.N) == K`.

### Step 4 - Linearize Pairwise Product
- Add three constraint rules to the pair set `P` to enforce `m.z[i,j] == m.x[i] * m.x[j]`:
  - Lower bound: `m.z[i,j] >= m.x[i] + m.x[j] - 1`
  - Upper bound 1: `m.z[i,j] <= m.x[i]`
  - Upper bound 2: `m.z[i,j] <= m.x[j]`

### Step 5 - Set Objective
- Define the objective as `m.obj = pyo.Objective(expr=sum(d[i,j] * m.z[i,j] for (i,j) in m.P), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": [
    "N: Pyomo Set of candidate elements.",
    "P: Pyomo Set of ordered pairs (i, j), dimen=2."
  ],
  "parameters": [
    "d: Python dictionary or Pyomo Param for pairwise weights.",
    "K: Integer parameter for selection count."
  ],
  "decision_variables": [
    "x[i]: Pyomo Binary variable for element selection.",
    "z[i, j]: Pyomo Binary variable for pairwise selection."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(d[i,j] * z[i,j] for (i,j) in P)"
  },
  "constraints": [
    "cardinality: sum(x[i] for i in N) == K",
    "pairwise_lower: z[i,j] >= x[i] + x[j] - 1 for (i,j) in P",
    "pairwise_upper1: z[i,j] <= x[i] for (i,j) in P",
    "pairwise_upper2: z[i,j] <= x[j] for (i,j) in P"
  ]
}
```

### Common Pitfalls
- Defining the pair set `P` incorrectly (e.g., including `(i,i)`); ensure the rule uses `i != j`.
- Passing the weight dictionary `d` inside Pyomo rule expressions; it must be accessible in the rule's namespace.
- Creating the model inside a function but not returning necessary data (like `d`, `N`) for solution verification.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver interface. Configure solver options for optimality and runtime, check termination conditions rigorously, and extract solution values for validation.

### Step 1 - Select and Configure Solver
- Instantiate a solver object, e.g., `solver = pyo.SolverFactory('gurobi')`.
- Set solver options via `solver.options['MIPGap'] = 0.0` for optimality, `solver.options['TimeLimit']` for runtime, and `solver.options['Threads']` for parallelism.

### Step 2 - Solve and Inspect Results
- Execute `results = solver.solve(model, tee=False)`.
- Check the termination condition: `results.solver.termination_condition`. Proceed only if it is `pyo.TerminationCondition.optimal` or `pyo.TerminationCondition.feasible`.

### Step 3 - Extract and Validate Solution
- Access variable values: `selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]`.
- Validate cardinality and pairwise logic manually.
- Recompute the objective from extracted selections to verify against `pyo.value(model.obj)`.

### Step 4 - Cross-validate with Enumeration
- For small instances, implement exhaustive search to confirm the MIP solver found the true optimum.

### Code Usage
```python
import pyomo.environ as pyo
import itertools

def build_model():
    # Define data
    N = [...]  # List of elements
    P = [(i, j) for i in N for j in N if i != j]
    d = {...}  # Dictionary of weights
    K = ...    # Selection count

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=N)
    model.P = pyo.Set(initialize=P, dimen=2)

    # Variables
    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.z = pyo.Var(model.P, domain=pyo.Binary)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(d[i, j] * model.z[i, j] for (i, j) in model.P),
        sense=pyo.maximize
    )

    # Constraints
    model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.N) == K)

    def lower_rule(m, i, j):
        return m.z[i, j] >= m.x[i] + m.x[j] - 1
    model.pairwise_lower = pyo.Constraint(model.P, rule=lower_rule)

    def upper1_rule(m, i, j):
        return m.z[i, j] <= m.x[i]
    model.pairwise_upper1 = pyo.Constraint(model.P, rule=upper1_rule)

    def upper2_rule(m, i, j):
        return m.z[i, j] <= m.x[j]
    model.pairwise_upper2 = pyo.Constraint(model.P, rule=upper2_rule)

    return model, d, N, K

# Build, solve, and verify
model, d, N, K = build_model()
solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 30
results = solver.solve(model, tee=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    # ... verification steps ...
else:
    # Handle non-optimal termination
    print(f"Solver terminated: {results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming `pyo.value(var)` returns an integer; it returns a float, so use `> 0.5` for binary checks.
- Not checking `termination_condition` and relying solely on `results.solver.status`, which may not indicate solution quality.
- Forgetting to pass the weight dictionary `d` out of the build function, causing NameError during verification.
