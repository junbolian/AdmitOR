---
name: Maximum Dispersion Selection
description: |
  Model and solve selection problems where the goal is to maximize the minimum distance between selected items, using binary selection variables, pairwise logic constraints, and a big-M distance linking formulation.

---

# Workflow 1 (MIP with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Program (MIP) using the OR-Tools Python wrapper. It directly creates variables and constraints via a solver API, focusing on a procedural, solver-agnostic construction suitable for SCIP or CBC backends.

### Step 1 - Define Core Variables
- Create a binary variable `x[i]` for each candidate item `i` to indicate selection.
- Create a binary variable `y[(i, j)]` for each ordered pair `(i, j)` to indicate the joint selection of both items.
- Create a continuous, non-negative variable `z` to represent the minimum distance to be maximized.

### Step 2 - Enforce Selection Logic
- Add a cardinality constraint: `sum(x[i] for i in items) == K`, where `K` is the required number of selections.
- For each pair `(i, j)`, add three linear constraints to enforce `y[(i, j)] == x[i] AND x[j]`:
  - `y[(i, j)] <= x[i]`
  - `y[(i, j)] <= x[j]`
  - `y[(i, j)] >= x[i] + x[j] - 1`

### Step 3 - Link Distance to Selection
- For each pair `(i, j)` with a known distance `d[i, j]`, add a big-M constraint: `z <= d[i, j] + M * (1 - y[(i, j)])`.
- Choose `M` as a sufficiently large constant (e.g., `max(d[i, j]) * 2` or a fixed large number) to deactivate the constraint when the pair is not selected.

### Step 4 - Formulate Objective
- Set the objective to maximize the continuous variable `z`.

### Formulation Template
```json
{
  "sets": [
    "items: set of candidate items",
    "pairs: set of ordered pairs (i, j) where i != j"
  ],
  "parameters": [
    "K: integer, number of items to select",
    "d: dict, distance for each pair (i, j)",
    "M: large constant for big-M relaxation"
  ],
  "decision_variables": [
    "x[i]: binary, 1 if item i is selected",
    "y[(i, j)]: binary, 1 if both i and j are selected",
    "z: continuous, non-negative, represents minimum distance"
  ],
  "objective": {
    "sense": "max",
    "expression": "z"
  },
  "constraints": [
    "cardinality: sum(x[i] for i in items) == K",
    "pairwise_logic_upper1: y[(i, j)] <= x[i] for all (i, j) in pairs",
    "pairwise_logic_upper2: y[(i, j)] <= x[j] for all (i, j) in pairs",
    "pairwise_logic_lower: y[(i, j)] >= x[i] + x[j] - 1 for all (i, j) in pairs",
    "distance_linking: z <= d[(i, j)] + M * (1 - y[(i, j)]) for all (i, j) in pairs"
  ]
}
```

### Common Pitfalls
- Choosing an insufficiently large `M` value, which can cut off valid solutions. Use a value safely larger than any possible distance.
- Forgetting to define `y` variables for both ordered pairs `(i, j)` and `(j, i)` if the distance matrix is not symmetric, which can miss constraints.
- Not setting variable bounds, leaving `z` unbounded, which can cause solver errors.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' linear solver wrapper, configuring time limits and threads. Extract and verify the solution, ensuring proper handling of solver statuses.

### Step 1 - Initialize Solver and Model
- Instantiate a solver object (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set performance parameters: `SetTimeLimit(milliseconds)` and `SetNumThreads(integer)`.

### Step 2 - Build and Solve Model
- Programmatically create variables and constraints as defined in the modeling stage.
- Set the objective and call `solver.Solve()`.

### Step 3 - Extract and Verify Solution
- Check the solver status: accept `OPTIMAL` or `FEASIBLE`.
- Collect selected items where `x[i].solution_value() > 0.5`.
- Retrieve the objective value from `z.solution_value()`.
- Optionally, verify the result by computing the actual minimum distance among selected items.

### Code Usage
```python
# build model from formulation
import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Define parameters
K = 2
M = 1000000
items = ["item1", "item2", "item3"]
pairs = [("item1", "item2"), ("item1", "item3"), ("item2", "item3")]
d = {("item1", "item2"): 5.0, ("item1", "item3"): 8.0, ("item2", "item3"): 3.0}

# Create variables
x = {}
for i in items:
    x[i] = solver.IntVar(0, 1, f"x_{i}")
y = {}
for (i, j) in pairs:
    y[(i, j)] = solver.IntVar(0, 1, f"y_{i}_{j}")
z = solver.NumVar(0, solver.infinity(), "z")

# Add constraints
solver.Add(sum(x[i] for i in items) == K)
for (i, j) in pairs:
    solver.Add(y[(i, j)] <= x[i])
    solver.Add(y[(i, j)] <= x[j])
    solver.Add(y[(i, j)] >= x[i] + x[j] - 1)
    solver.Add(z <= d[(i, j)] + M * (1 - y[(i, j)]))

# Set objective
objective = solver.Objective()
objective.SetCoefficient(z, 1)
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [i for i in items if x[i].solution_value() > 0.5]
    min_dist = z.solution_value()
    print(f"Selected: {selected}, Minimum Distance: {min_dist}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good solutions from time-limited runs.
- Using `> 0.5` for binary variable solution value checks to avoid floating-point precision issues.
- Omitting solver resource limits, which can cause indefinite runtime for large instances.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to define the problem declaratively. It separates model specification from solver execution, enabling easy switching between solvers like HiGHS or CBC and leveraging Pyomo's set and parameter abstractions.

### Step 1 - Declare Model Components
- Create a `ConcreteModel`.
- Define `Set` objects for `items` and `pairs`.
- Define `Param` objects for distances `d[pair]`, selection count `K`, and big-M constant `M`.

### Step 2 - Define Variables and Objective
- Create `Var` objects: `model.x` (Binary, indexed by items), `model.y` (Binary, indexed by pairs), and `model.z` (NonNegativeReals).
- Define the objective to maximize `model.z` using `Objective(expr=model.z, sense=maximize)`.

### Step 3 - Implement Constraints as Rules
- Create a cardinality constraint rule summing `model.x[i]` to equal `K`.
- For pairwise logic, create three constraint rules per pair linking `model.y[p]` to `model.x[i]` and `model.x[j]`.
- Create a distance linking constraint rule using the big-M formulation for each pair.

### Formulation Template
```json
{
  "sets": [
    "model.I: set of candidate items",
    "model.P: set of ordered pairs (i, j)"
  ],
  "parameters": [
    "model.K: integer, number of items to select",
    "model.d: parameter, distance for each pair in P",
    "model.M: large constant for big-M relaxation"
  ],
  "decision_variables": [
    "model.x[i]: binary, 1 if item i is selected",
    "model.y[p]: binary, 1 if both nodes in pair p are selected",
    "model.z: continuous, non-negative, represents minimum distance"
  ],
  "objective": {
    "sense": "max",
    "expression": "model.z"
  },
  "constraints": [
    "cardinality: sum(model.x[i] for i in I) == model.K",
    "pairwise_logic_upper1: model.y[(i, j)] <= model.x[i] for all (i, j) in P",
    "pairwise_logic_upper2: model.y[(i, j)] <= model.x[j] for all (i, j) in P",
    "pairwise_logic_lower: model.y[(i, j)] >= model.x[i] + model.x[j] - 1 for all (i, j) in P",
    "distance_linking: model.z <= model.d[(i, j)] + model.M * (1 - model.y[(i, j)]) for all (i, j) in P"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters or variables within Pyomo rule functions, leading to construction errors.
- Defining the `pairs` set without considering symmetry, which may duplicate constraints unnecessarily if distances are symmetric.
- Using an overly large `M` in Pyomo can lead to numerical instability; scale distances appropriately.

## Solving stage

### Strategy Overview
Instantiate a solver via Pyomo's `SolverFactory`, configure it with time limits and optimality gaps, solve the model, and parse the results using Pyomo's value functions and status checks.

### Step 1 - Configure and Execute Solver
- Create a solver object: `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set solver options: `time_limit`, `mip_rel_gap` (e.g., 0.0 for optimality), `threads`.
- Call `solver.solve(model, tee=False)` to execute.

### Step 2 - Validate Solution Status
- Check if the solver returned `SolverStatus.ok`.
- Check the termination condition: `TerminationCondition.optimal` or `.feasible`.
- If not acceptable, handle the failure (e.g., return infeasibility message).

### Step 3 - Extract and Format Results
- Retrieve selected items where `pyo.value(model.x[i]) > 0.5`.
- Obtain the objective value via `pyo.value(model.z)`.
- Optionally, compute verification metrics and output a structured result (e.g., JSON).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()

# Sets and Parameters
model.I = pyo.Set(initialize=["item1", "item2", "item3"])
model.P = pyo.Set(initialize=[("item1", "item2"), ("item1", "item3"), ("item2", "item3")], dimen=2)
model.d = pyo.Param(model.P, initialize={("item1", "item2"): 5.0, ("item1", "item3"): 8.0, ("item2", "item3"): 3.0})
model.K = pyo.Param(initialize=2, within=pyo.PositiveIntegers)
model.M = pyo.Param(initialize=1000000)

# Variables
model.x = pyo.Var(model.I, within=pyo.Binary)
model.y = pyo.Var(model.P, within=pyo.Binary)
model.z = pyo.Var(within=pyo.NonNegativeReals)

# Objective
model.obj = pyo.Objective(expr=model.z, sense=pyo.maximize)

# Constraints
def cardinality_rule(m):
    return sum(m.x[i] for i in m.I) == m.K
model.cardinality_con = pyo.Constraint(rule=cardinality_rule)

def pairwise_upper1_rule(m, i, j):
    return m.y[(i, j)] <= m.x[i]
model.pairwise_upper1_con = pyo.Constraint(model.P, rule=pairwise_upper1_rule)

def pairwise_upper2_rule(m, i, j):
    return m.y[(i, j)] <= m.x[j]
model.pairwise_upper2_con = pyo.Constraint(model.P, rule=pairwise_upper2_rule)

def pairwise_lower_rule(m, i, j):
    return m.y[(i, j)] >= m.x[i] + m.x[j] - 1
model.pairwise_lower_con = pyo.Constraint(model.P, rule=pairwise_lower_rule)

def distance_linking_rule(m, i, j):
    return m.z <= m.d[(i, j)] + m.M * (1 - m.y[(i, j)])
model.distance_linking_con = pyo.Constraint(model.P, rule=distance_linking_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
        selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
        min_dist = pyo.value(model.z)
        print(f"Selected: {selected}, Minimum Distance: {min_dist}")
    else:
        print(f"Solver terminated with condition: {results.solver.termination_condition}")
else:
    print("Solver failed.")
```

### Common Pitfalls
- Misinterpreting Pyomo's `SolverStatus.ok` (only indicates solver ran) without checking `TerminationCondition`.
- Forgetting to call `pyo.value()` on variables when extracting solutions, which returns the variable object instead of its value.
- Not setting `within` domains for parameters, which can lead to unexpected type errors during model construction.
