---
name: Pairwise Selection with Cardinality
description: |
  Model and solve binary selection problems with pairwise interactions under exact cardinality constraints, using linearized AND constraints and maximizing weighted pairwise sums.

---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT solver, designed for combinatorial problems with Boolean logic. It directly encodes binary variables and linearized logical constraints, suitable for medium to large instances.

### Step 1 - Define Sets and Parameters
- Define the set of candidate elements `N` (e.g., nodes, items).
- Define the set of relevant ordered pairs `P`. For asymmetric weights, use all `(i, j)` where `i != j`. For symmetric problems, consider using `i < j` to reduce variables.
- Create a weight parameter `w[(i, j)]` for each pair in `P`. Ensure the dictionary is keyed by the same tuple format used for variables.

### Step 2 - Create Decision Variables
- Create binary selection variable `x[i]` for each element `i` in `N`.
- Create auxiliary binary pairwise variable `z[(i, j)]` for each ordered pair in `P`.

### Step 3 - Formulate Cardinality Constraint
- Add a linear equality constraint to select exactly `k` elements: `sum(x[i] for i in N) == k`.

### Step 4 - Linearize Pairwise Logic
- For each pair `(i, j)` in `P`, add three linear constraints to enforce `z[(i, j)] = x[i] AND x[j]`:
  - `z[(i, j)] <= x[i]`
  - `z[(i, j)] <= x[j]`
  - `z[(i, j)] >= x[i] + x[j] - 1`

### Step 5 - Define Objective
- Formulate the objective to maximize the weighted sum of active pairwise variables: `maximize sum(w[(i, j)] * z[(i, j)] for (i, j) in P)`.

### Formulation Template
```json
{
  "sets": [
    "N = ['list', 'of', 'element', 'ids']",
    "P = ['list', 'of', 'ordered', 'pairs', '(i,j)']"
  ],
  "parameters": [
    "k = exact_number_of_selections",
    "w = dictionary mapping (i,j) to weight"
  ],
  "decision_variables": [
    "x[i] ∈ {0,1} ∀ i ∈ N",
    "z[(i,j)] ∈ {0,1} ∀ (i,j) ∈ P"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{ (i,j) ∈ P } w[(i,j)] * z[(i,j)]"
  },
  "constraints": [
    "sum_{ i ∈ N } x[i] == k",
    "z[(i,j)] <= x[i] ∀ (i,j) ∈ P",
    "z[(i,j)] <= x[j] ∀ (i,j) ∈ P",
    "z[(i,j)] >= x[i] + x[j] - 1 ∀ (i,j) ∈ P"
  ]
}
```

### Common Pitfalls
- Defining `P` incorrectly for the problem semantics (ordered vs. unordered pairs).
- Forgetting to add all three linearization constraints, which can lead to incorrect `z` values.
- Using floating-point weights that cause numerical issues; CP-SAT prefers integer coefficients.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT interface, configuring search parameters for performance and reproducibility, then extract and validate the solution.

### Step 1 - Instantiate Model and Solver
- Create a `CpModel` object.
- Instantiate a `CpSolver` and configure its parameters.

### Step 2 - Configure Solver Parameters
- Set a time limit: `solver.parameters.max_time_in_seconds = time_limit`.
- Enable parallel search: `solver.parameters.num_search_workers = num_workers`.
- Set a random seed for reproducibility: `solver.parameters.random_seed = seed`.
- Optionally, set `solver.parameters.relative_gap_limit = 0.0` to seek optimality.

### Step 3 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before proceeding.

### Step 4 - Extract and Validate Solution
- Extract selected elements: `[i for i in N if solver.Value(x[i]) == 1]`.
- Recalculate the objective value from the selected elements to verify consistency with the model's reported objective.
- Optionally, verify that active `z` variables correspond exactly to selected pairs.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f'x_{i}') for i in N}
z = {(i, j): model.NewBoolVar(f'z_{i}_{j}') for (i, j) in P}

model.Add(sum(x[i] for i in N) == k)
for (i, j) in P:
    model.Add(z[(i, j)] <= x[i])
    model.Add(z[(i, j)] <= x[j])
    model.Add(z[(i, j)] >= x[i] + x[j] - 1)

model.Maximize(sum(w[(i, j)] * z[(i, j)] for (i, j) in P)))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = III
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected = [i for i in N if solver.Value(x[i]) == 1]
    objective_value = solver.ObjectiveValue()
    # Validation: Recalculate objective from selected list
    # ...
else:
    print("Solver did not find a solution.")
```

### Common Pitfalls
- Not checking solver status before accessing `solver.Value()` or `solver.ObjectiveValue()`.
- Misinterpreting `cp_model.FEASIBLE` as optimal when a time limit is set.
- Forgetting that CP-SAT requires integer coefficients; scale float weights if necessary.

# Workflow 2 (MIP with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for algebraic modeling with a backend MIP solver (e.g., Gurobi, CBC). It is well-suited for integration into larger optimization frameworks and offers detailed solver control and reporting.

### Step 1 - Define Abstract Sets and Parameters
- Define an abstract set `model.N` for elements.
- Define an abstract set `model.P` for ordered pairs, typically as a `Set(within=model.N*model.N)` with a rule to filter `i != j`.
- Declare parameter `model.k` for the cardinality and `model.w` for the weight matrix, indexed by `model.P`.

### Step 2 - Create Concrete Variables
- Create binary variable `model.x` indexed by `model.N`.
- Create binary variable `model.z` indexed by `model.P`.

### Step 3 - Formulate Cardinality Constraint
- Add a constraint: `sum(model.x[i] for i in model.N) == model.k`.

### Step 4 - Linearize Pairwise Logic
- For each `(i,j)` in `model.P`, add three constraints:
  - `model.z[i,j] <= model.x[i]`
  - `model.z[i,j] <= model.x[j]`
  - `model.z[i,j] >= model.x[i] + model.x[j] - 1`

### Step 5 - Define Objective
- Define the objective: `maximize sum(model.w[i,j] * model.z[i,j] for (i,j) in model.P)`.

### Formulation Template
```json
{
  "sets": [
    "N = Set()",
    "P = Set(within=N*N, filter=(i,j) => i != j)"
  ],
  "parameters": [
    "k = Param(within=NonNegativeIntegers)",
    "w = Param(P)"
  ],
  "decision_variables": [
    "x = Var(N, within=Binary)",
    "z = Var(P, within=Binary)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum( w[i,j] * z[i,j] for (i,j) in P )"
  },
  "constraints": [
    "cardinality: sum( x[i] for i in N ) == k",
    "logic1: z[i,j] <= x[i] forall (i,j) in P",
    "logic2: z[i,j] <= x[j] forall (i,j) in P",
    "logic3: z[i,j] >= x[i] + x[j] - 1 forall (i,j) in P"
  ]
}
```

### Common Pitfalls
- Using Pyomo's `AbstractModel` without properly instantiating it with data before solving.
- Incorrectly defining the pair set `P`, leading to missing or duplicate variables.
- Not scaling large float weights, which can cause numerical instability in some MIP solvers.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with data, select a MIP solver, configure it with appropriate settings, solve, and perform rigorous solution validation.

### Step 1 - Instantiate Model with Data
- Create a `ConcreteModel` or instantiate an `AbstractModel` with a `DataPortal`.
- Populate sets `N` and `P`, and parameters `k` and `w`.

### Step 2 - Select and Configure Solver
- Use `SolverFactory('solver_name')` (e.g., 'gurobi', 'cbc').
- Set solver options: `TimeLimit`, `MIPGap` (to 0 for optimality), `Threads`, and `Seed`.

### Step 3 - Solve and Check Termination Status
- Execute `solver.solve(model, options=options)`.
- Check both `model.solutions.solver.status == SolverStatus.ok` and `model.solutions.solver.termination_condition` (e.g., `optimal`, `feasible`).

### Step 4 - Extract and Verify Solution
- Extract selected elements: `[i for i in model.N if pyo.value(model.x[i]) > 0.5]`.
- Manually recalculate the objective from the selected elements to catch modeling errors.
- For small `N`, implement a brute-force check using `itertools.combinations` to verify optimality.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# build model from formulation
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=['list', 'of', 'ids'])
# Define P as ordered pairs i != j
model.P = pyo.Set(initialize=[(i,j) for i in model.N for j in model.N if i != j], dimen=II)
model.k = pyo.Param(initialize=exact_selection_count, within=pyo.NonNegativeIntegers)
model.w = pyo.Param(model.P, initialize=weight_dict)

model.x = pyo.Var(model.N, within=pyo.Binary)
model.z = pyo.Var(model.P, within=pyo.Binary)

def cardinality_rule(m):
    return sum(m.x[i] for i in m.N) == m.k
model.cardinality = pyo.Constraint(rule=cardinality_rule)

def logic1_rule(m, i, j):
    return m.z[i,j] <= m.x[i]
model.logic1 = pyo.Constraint(model.P, rule=logic1_rule)

def logic2_rule(m, i, j):
    return m.z[i,j] <= m.x[j]
model.logic2 = pyo.Constraint(model.P, rule=logic2_rule)

def logic3_rule(m, i, j):
    return m.z[i,j] >= m.x[i] + m.x[j] - I
model.logic3 = pyo.Constraint(model.P, rule=logic3_rule)

model.obj = pyo.Objective(expr=sum(model.w[i,j] * model.z[i,j] for (i,j) in model.P), sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
results = solver.solve(model)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    obj_val = pyo.value(model.obj)
    # Validation and output
else:
    print(f"Solver failed: Status={status}, Termination={term}")
```

### Common Pitfalls
- Confusing `SolverStatus` with `TerminationCondition`; both must be checked.
- Accessing `pyo.value()` on variables before verifying a solution exists.
- Not using a tolerance (e.g., `> 0.5`) when interpreting binary variable values due to solver numerical precision.
