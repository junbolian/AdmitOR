---
name: Pairwise Selection Maximization
description: |
  Model and solve cardinality-constrained selection problems where the objective is to maximize the sum of pairwise weights among selected items, using either linearized MIP or direct quadratic formulations.

---

# Workflow 1 (Linearized MIP with CP-SAT)

## Modeling stage

### Strategy Overview
Transform the quadratic pairwise interaction objective into a linear one by introducing auxiliary binary variables for each pair, linked to the primary selection variables via logical AND constraints. This yields a pure binary linear program suitable for CP-SAT solvers.

### Step 1 - Define Core Sets and Parameters
- Define a set `N` for all candidate items.
- Define a set `P` for ordered or unordered pairs `(i, j)` where `i != j`.
- Define a parameter `weight[i][j]` representing the pairwise contribution (e.g., distance, similarity) for each pair in `P`.
- Define a scalar parameter `K` for the exact number of items to select.

### Step 2 - Create Decision Variables
- Create binary variable `x[i]` for each `i` in `N`, where `1` indicates selection.
- Create auxiliary binary variable `y[(i, j)]` for each pair in `P`, intended to equal `x[i] * x[j]`.

### Step 3 - Formulate Linear Consistency Constraints
- For each pair `(i, j)` in `P`, add constraints to enforce `y[(i, j)] = x[i] ∧ x[j]`:
  - `y[(i, j)] <= x[i]`
  - `y[(i, j)] <= x[j]`
  - `y[(i, j)] >= x[i] + x[j] - 1`

### Step 4 - Impose Cardinality and Objective
- Add a single cardinality constraint: `sum(x[i] for i in N) == K`.
- Formulate the linear objective: Maximize `sum(weight[i][j] * y[(i, j)] for (i, j) in P)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all candidate items"},
    {"name": "P", "description": "Set of ordered or unordered pairs (i,j) where i != j"}
  ],
  "parameters": [
    {"name": "weight", "index": "P", "description": "Pairwise weight for each pair"},
    {"name": "K", "description": "Exact number of items to select"}
  ],
  "decision_variables": [
    {"name": "x", "index": "N", "domain": "binary", "description": "1 if item is selected"},
    {"name": "y", "index": "P", "domain": "binary", "description": "1 if both items in pair are selected"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i,j] * y[i,j] for (i,j) in P)"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum(x[i] for i in N) == K"},
    {"name": "pairwise_lower1", "index": "P", "expression": "y[i,j] <= x[i]"},
    {"name": "pairwise_lower2", "index": "P", "expression": "y[i,j] <= x[j]"},
    {"name": "pairwise_lower3", "index": "P", "expression": "y[i,j] >= x[i] + x[j] - 1"}
  ]
}
```

### Common Pitfalls
- Defining the pair set `P` incorrectly (e.g., including `i=j` or missing ordered pairs for asymmetric weights).
- Forgetting to set `K` to a positive integer less than or equal to `|N|`.
- Using symmetric pair sets with asymmetric weights, which may undercount contributions.

## Solving stage

### Strategy Overview
Use the OR-Tools CP-SAT solver, configured for reproducibility and exact solutions, to solve the linearized binary model. Verify results by recalculating the objective from the selected set.

### Step 1 - Initialize Model and Solver
- Import `ortools.sat.python.cp_model`.
- Create a `CpModel()` instance for the model and a `CpSolver()` instance for solving.

### Step 2 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` to control runtime.
- Set `solver.parameters.num_search_workers` for parallel search.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to require optimality proof.

### Step 3 - Build and Solve Model
- Instantiate variables using `model.NewBoolVar()`.
- Add constraints using `model.Add()` with the linearized expressions.
- Call `solver.Solve(model)` and capture the status.

### Step 4 - Extract and Validate Solution
- Check if `status` is `OPTIMAL` or `FEASIBLE`.
- Retrieve selected items: `[i for i in N if solver.Value(x[i]) == 1]`.
- Recompute the objective by summing `weight[i][j]` over all selected pairs and compare with `solver.ObjectiveValue()`.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... create variables and constraints as per formulation ...

# Solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters as needed
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = -0.0  # Negative value forces exact gap

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in N if solver.Value(x[i]) == 1]
    print(f"Selected items: {selected}")
    print(f"Objective value (from solver): {solver.ObjectiveValue()}")
    # Manual verification
    manual_obj = sum(weight[i][j] for i in selected for j in selected if i != j)
    print(f"Objective value (manual): {manual_obj}")
else:
    print("No solution found.")
```

### Common Pitfalls
- Not setting `relative_gap_limit` correctly for exact solutions.
- Failing to verify the solver's objective against a manual calculation.
- Overlooking that CP-SAT requires constraints to be added with `model.Add`, not direct assignment.

# Workflow 2 (Direct Quadratic MIQP with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem directly as a Mixed-Integer Quadratic Program (MIQP) using binary selection variables and a quadratic objective summing pairwise products. This avoids auxiliary variables but requires a solver supporting non-convex quadratic objectives.

### Step 1 - Define Sets and Parameters
- Define a set `N` for all candidate items.
- Define a set `P` for unordered pairs `(i, j)` where `i < j` (or ordered pairs if weights are asymmetric).
- Define a parameter `weight[i][j]` for the pairwise contribution.
- Define a scalar parameter `K` for the selection cardinality.

### Step 2 - Create Decision Variables
- Create binary variable `x[i]` for each `i` in `N`, where `1` indicates selection.

### Step 3 - Formulate Quadratic Objective and Constraint
- Formulate the objective directly: Maximize `sum(weight[i][j] * x[i] * x[j] for (i, j) in P)`.
- Add the cardinality constraint: `sum(x[i] for i in N) == K`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all candidate items"},
    {"name": "P", "description": "Set of unordered pairs (i,j) where i < j"}
  ],
  "parameters": [
    {"name": "weight", "index": "P", "description": "Pairwise weight for each pair"},
    {"name": "K", "description": "Exact number of items to select"}
  ],
  "decision_variables": [
    {"name": "x", "index": "N", "domain": "binary", "description": "1 if item is selected"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i,j] * x[i] * x[j] for (i,j) in P)"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum(x[i] for i in N) == K"}
  ]
}
```

### Common Pitfalls
- Using a solver that does not support non-convex quadratic objectives (requires `NonConvex=2` in Gurobi).
- Incorrectly defining the pair set for asymmetric weights (should use ordered pairs).
- Overlooking that the quadratic term `x[i]*x[j]` is only counted once per unordered pair in the objective.

## Solving stage

### Strategy Overview
Use Pyomo with a MIQP-capable solver like Gurobi, configured to handle non-convex quadratics. Validate the solution by comparing the solver's objective with a brute-force calculation for small instances.

### Step 1 - Build Pyomo Model
- Import `pyomo.environ` and `SolverFactory`.
- Create a `ConcreteModel()`.
- Define sets, parameters, variables, objective, and constraint as per the formulation.

### Step 2 - Configure Solver for MIQP
- Instantiate the solver (e.g., `SolverFactory('gurobi')`).
- Set solver options:
  - `'NonConvex' = 2` to handle quadratic terms.
  - `'MIPGap' = 0.0` for exact optimality.
  - `'TimeLimit'` to bound runtime.
  - `'Seed'` and `'Threads'` for reproducibility and performance.

### Step 3 - Solve and Check Status
- Call `solver.solve(model, tee=True)`.
- Check `SolverStatus.ok` and `TerminationCondition.optimal` or `.feasible`.

### Step 4 - Extract and Verify Solution
- Extract selected items: `[i for i in N if pyo.value(model.x[i]) > 0.5]`.
- Manually compute the objective by summing `weight[i][j]` over selected pairs.
- For small `n`, optionally validate against brute-force enumeration.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=N)
model.P = pyo.Set(initialize=P, dimen=2)
model.weight = pyo.Param(model.P, initialize=weight)
model.x = pyo.Var(model.N, domain=pyo.Binary)

model.obj = pyo.Objective(expr=sum(model.weight[i,j] * model.x[i] * model.x[j] for (i,j) in model.P), sense=pyo.maximize)
model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.N) == K)

# Solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['NonConvex'] = 2
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 30
solver.options['Seed'] = 42
solver.options['Threads'] = 4

results = solver.solve(model, tee=True)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    print(f"Selected items: {selected}")
    print(f"Objective value (from solver): {pyo.value(model.obj)}")
    # Manual verification
    manual_obj = sum(weight[i][j] for i in selected for j in selected if i != j)
    print(f"Objective value (manual): {manual_obj}")
else:
    print(f"Solver failed: status={status}, termination={term}")
```

### Common Pitfalls
- Forgetting to set `NonConvex=2` for quadratic objectives in Gurobi.
- Not verifying the solver's objective against a manual calculation, especially for asymmetric weights.
- Assuming all MIQP solvers support non-convex quadratics without configuration.
