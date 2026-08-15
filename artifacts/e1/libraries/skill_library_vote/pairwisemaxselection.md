---
name: PairwiseMaxSelection
description: |
  Model and solve binary selection problems with pairwise interaction objectives and cardinality constraints using either linearization with CP-SAT or direct quadratic formulation with MIQP.
---

# Workflow 1 (Linearized CP-SAT)

## Modeling stage

### Strategy Overview
This workflow linearizes the quadratic pairwise interaction objective by introducing auxiliary binary variables, making it compatible with linear solvers like OR-Tools CP-SAT. It is robust for exact solving and handles asymmetric weights directly.

### Step 1 - Define Data Structures
- Define a set `N` of selectable items (e.g., nodes, facilities).
- Define a set `P` of ordered or unordered pairs `(i,j)` for which interaction weights are defined.
- Create a parameter `d` mapping each pair `(i,j)` to its weight (e.g., distance, affinity).
- Define a scalar parameter `K` for the exact selection cardinality.

### Step 2 - Create Decision Variables
- Create a binary variable `x[i]` for each item `i` in `N` to indicate selection.
- Create an auxiliary binary variable `y[(i,j)]` for each pair in `P` to represent the product `x[i] * x[j]`.

### Step 3 - Formulate Linearization Constraints
- For each pair `(i,j)` in `P`, add three constraints to enforce `y[(i,j)] = x[i] * x[j]`:
  - `y[(i,j)] <= x[i]`
  - `y[(i,j)] <= x[j]`
  - `y[(i,j)] >= x[i] + x[j] - 1`

### Step 4 - Impose Cardinality Constraint
- Add a single constraint: `sum(x[i] for i in N) == K`.

### Step 5 - Define Linear Objective
- Maximize the sum of weighted pairwise interactions: `sum(d[(i,j)] * y[(i,j)] for (i,j) in P)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of selectable items"},
    {"name": "P", "description": "Set of ordered/unordered pairs (i,j) with defined weights"}
  ],
  "parameters": [
    {"name": "d", "domain": "P -> real", "description": "Weight for each pair"},
    {"name": "K", "domain": "integer", "description": "Exact number of items to select"}
  ],
  "decision_variables": [
    {"name": "x", "domain": "binary", "index": "N", "description": "1 if item i is selected"},
    {"name": "y", "domain": "binary", "index": "P", "description": "1 if both i and j are selected"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{ (i,j) in P } d[(i,j)] * y[(i,j)]"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum_{ i in N } x[i] == K"},
    {"name": "linearization_lower1", "expression": "y[(i,j)] <= x[i]", "for_all": "(i,j) in P"},
    {"name": "linearization_lower2", "expression": "y[(i,j)] <= x[j]", "for_all": "(i,j) in P"},
    {"name": "linearization_upper", "expression": "y[(i,j)] >= x[i] + x[j] - 1", "for_all": "(i,j) in P"}
  ]
}
```

### Common Pitfalls
- Creating unnecessary pairwise variables for symmetric pairs when weights are symmetric; define `P` as unordered pairs to reduce model size.
- Using `-1.0` for relative gap limit; use `0.0` to require optimality in CP-SAT.
- Forgetting to handle asymmetric weights correctly; sum both directions `(i,j)` and `(j,i)` if the problem counts all directed interactions.

## Solving stage

### Strategy Overview
Solve the linearized binary model using OR-Tools CP-SAT with configuration for deterministic, exact optimization. Extract and verify the solution.

### Step 1 - Instantiate Model and Variables
- Create a `CpModel`.
- Create `x[i]` as `NewBoolVar(f"x_{i}")`.
- Create `y[(i,j)]` as `NewBoolVar(f"y_{i}_{j}")`.

### Step 2 - Add Constraints
- Add the cardinality constraint using `Add(sum(x[i] for i in N) == K)`.
- For each pair, add the three linearization constraints using `Add(y[(i,j)] <= x[i])`, etc.

### Step 3 - Set Objective and Configure Solver
- Set the objective with `Maximize(sum(d[(i,j)] * y[(i,j)] for (i,j) in P))`.
- Configure `CpSolver` parameters: set `max_time_in_seconds`, `num_search_workers`, `random_seed`, and `relative_gap_limit = 0.0`.

### Step 4 - Solve and Check Status
- Call `Solve(model)` and capture the status.
- Check if status is `OPTIMAL` or `FEASIBLE`; otherwise, handle failure.

### Step 5 - Extract and Verify Solution
- Collect selected items where `solver.Value(x[i]) == 1`.
- Optionally, recompute the objective by summing weights for all selected pairs to verify against `solver.ObjectiveValue()`.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in N}
y = {(i,j): model.NewBoolVar(f"y_{i}_{j}") for (i,j) in P}

# Cardinality
model.Add(sum(x[i] for i in N) == K)

# Linearization
for (i,j) in P:
    model.Add(y[(i,j)] <= x[i])
    model.Add(y[(i,j)] <= x[j])
    model.Add(y[(i,j)] >= x[i] + x[j] - 1)

# Objective
model.Maximize(sum(d[(i,j)] * y[(i,j)] for (i,j) in P))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = -1  # Use all cores
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = -1.0  # Disable early termination

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in N if solver.Value(x[i]) == 1]
    objective_value = solver.ObjectiveValue()
    print(f"Selected: {selected}")
    print(f"Objective: {objective_value}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Setting `relative_gap_limit = -1.0` incorrectly; CP-SAT uses `-1.0` to disable early termination, but verify solver documentation.
- Not using `num_search_workers` for parallel search, impacting performance on multi-core machines.
- Failing to verify the solution by manual recomputation, which can catch modeling errors in the linearization.

# Workflow 2 (Direct MIQP with Pyomo)

## Modeling stage

### Strategy Overview
This workflow models the quadratic pairwise interaction objective directly, leveraging modern MIQP solvers (e.g., Gurobi) that handle non-convex quadratic terms. It avoids auxiliary variables, simplifying the model structure.

### Step 1 - Define Sets and Parameters
- Define set `N` of selectable items.
- Define set `P` of ordered pairs `(i,j)` where `i != j`.
- Create parameter `d[(i,j)]` for the weight of each ordered pair.
- Define scalar parameter `K` for the exact selection cardinality.

### Step 2 - Create Selection Variables
- Create a binary variable `x[i]` for each item `i` in `N`.

### Step 3 - Formulate Quadratic Objective
- Maximize the sum of weighted pairwise products: `sum(d[(i,j)] * x[i] * x[j] for (i,j) in P)`.

### Step 4 - Impose Cardinality Constraint
- Add constraint: `sum(x[i] for i in N) == K`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of selectable items"},
    {"name": "P", "description": "Set of ordered pairs (i,j) with i != j"}
  ],
  "parameters": [
    {"name": "d", "domain": "P -> real", "description": "Weight for each ordered pair"},
    {"name": "K", "domain": "integer", "description": "Exact number of items to select"}
  ],
  "decision_variables": [
    {"name": "x", "domain": "binary", "index": "N", "description": "1 if item i is selected"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{ (i,j) in P } d[(i,j)] * x[i] * x[j]"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum_{ i in N } x[i] == K"}
  ]
}
```

### Common Pitfalls
- Assuming symmetric weights and incorrectly defining `P`; use ordered pairs for asymmetric data.
- Forgetting to set the `NonConvex` parameter to 2 when using Gurobi for non-convex quadratic objectives.
- Creating the quadratic objective over all `i,j` including `i=j`, which may introduce unintended self-interaction terms.

## Solving stage

### Strategy Overview
Solve the MIQP model using a solver like Gurobi via Pyomo, configured to handle non-convex quadratics. Check solver status and extract the solution.

### Step 1 - Build Pyomo Model
- Create a `ConcreteModel`.
- Define `Set`s for `N` and `P`.
- Define `Param` `d` initialized from the weight dictionary.
- Define `Var` `x` as `Binary`.

### Step 2 - Define Objective and Constraint
- Set the objective using `Objective(expr=sum(d[i,j] * x[i] * x[j] for (i,j) in P), sense=maximize)`.
- Add the cardinality constraint.

### Step 3 - Configure and Run Solver
- Use `SolverFactory("gurobi")`.
- Set solver options: `"NonConvex"=2`, `"MIPGap"=0.0`, `"TimeLimit"`, `"Threads"`, and `"Seed"`.
- Solve with `tee=False` for quiet operation.

### Step 4 - Validate Solution Status
- Check `SolverStatus.ok` and `TerminationCondition.optimal` or `.feasible`.
- If not optimal/feasible, handle failure with appropriate error reporting.

### Step 5 - Extract Solution
- Retrieve selected items where `value(x[i]) > 0.5`.
- Obtain objective value from `value(model.obj)`.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=N)
model.P = pyo.Set(initialize=P, dimen=2)
model.d = pyo.Param(model.P, initialize=d)
model.x = pyo.Var(model.N, domain=pyo.Binary)

model.obj = pyo.Objective(
    expr=sum(model.d[i,j] * model.x[i] * model.x[j] for (i,j) in model.P),
    sense=pyo.maximize
)
model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.N) == K)

# Solve with status / termination checks
solver = pyo.SolverFactory("gurobi")
solver.options["NonConvex"] = 2
solver.options["MIPGap"] = 0.0
solver.options["TimeLimit"] = 30
solver.options["Threads"] = 0  # Use all available threads
solver.options["Seed"] = 42

results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    objective_value = pyo.value(model.obj)
    print(f"Selected: {selected}")
    print(f"Objective: {objective_value}")
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Not setting `"NonConvex"=2` for Gurobi, causing the solver to reject the non-convex quadratic objective.
- Using `MIPGap = -1.0` which is invalid; use `0.0` for exact optimality.
- Failing to check both `SolverStatus` and `TerminationCondition`, leading to incorrect interpretation of solver results.
