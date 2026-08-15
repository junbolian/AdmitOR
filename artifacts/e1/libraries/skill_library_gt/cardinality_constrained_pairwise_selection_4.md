---
name: Cardinality-Constrained Pairwise Selection
description: |
  Model and solve binary selection problems with cardinality constraints and pairwise activation, maximizing a weighted sum of directed or undirected pairwise contributions.
---

# Workflow 1 (CP-SAT for Logical Constraints)

## Modeling stage

### Strategy Overview
This workflow uses a constraint programming (CP) / SAT approach, ideal for models dominated by binary variables and logical (if-then) linking constraints. It leverages the OR-Tools CP-SAT solver for efficient combinatorial search.

### Step 1 - Define Core Selection Variables
- Create a binary variable `x[i]` for each element `i` in the set `N` to represent its selection status.
- Use a list or dictionary for variable storage, keyed by element index.

### Step 2 - Define Pairwise Activation Variables
- Create a binary variable `y[(i, j)]` for each ordered pair `(i, j)` where `i != j`.
- Store these variables in a dictionary keyed by tuple `(i, j)` for efficient constraint building.

### Step 3 - Enforce Cardinality Constraint
- Add a linear constraint: `sum(x[i] for i in N) == K`, where `K` is the required number of selected elements.

### Step 4 - Link Activation to Selection Logically
- For each ordered pair `(i, j)`, add three linear constraints to enforce `y[(i, j)] == x[i] AND x[j]`:
  1. `y[(i, j)] <= x[i]` (activation requires first element selected).
  2. `y[(i, j)] <= x[j]` (activation requires second element selected).
  3. `y[(i, j)] >= x[i] + x[j] - 1` (if both are selected, activation is forced).

### Step 5 - Formulate the Objective
- Define the objective as `maximize sum( w[(i, j)] * y[(i, j)] for all i != j )`, where `w[(i, j)]` is the directed weight for pair `(i, j)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all candidate elements."},
    {"name": "P", "description": "Set of ordered pairs (i, j) where i, j in N and i != j."}
  ],
  "parameters": [
    {"name": "K", "description": "Exact number of elements to select (cardinality)."},
    {"name": "w", "description": "Directed weight for each ordered pair in P."}
  ],
  "decision_variables": [
    {"name": "x", "domain": "Binary", "index": "i in N", "description": "1 if element i is selected."},
    {"name": "y", "domain": "Binary", "index": "(i, j) in P", "description": "1 if both i and j are selected (activated pair)."}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum( w[(i, j)] * y[(i, j)] for (i, j) in P )"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum(x[i] for i in N) == K"},
    {"name": "link_first", "expression": "y[(i, j)] <= x[i] for (i, j) in P"},
    {"name": "link_second", "expression": "y[(i, j)] <= x[j] for (i, j) in P"},
    {"name": "force_activation", "expression": "y[(i, j)] >= x[i] + x[j] - 1 for (i, j) in P"}
  ]
}
```

### Common Pitfalls
- Forgetting to create `y` variables for both ordered directions `(i, j)` and `(j, i)` when weights are asymmetric, which leads to missing objective contributions.
- Using an unordered pair set `(i<j)` but applying directed weights, causing a mismatch between variable indexing and parameter indexing.
- Adding redundant constraints; the three linking constraints are the minimal set to enforce the logical AND.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, configured for deterministic, bounded-time search. Focus on extracting the solution and verifying correctness for small instances.

### Step 1 - Instantiate Model and Variables
- Create a `CpModel` object.
- Use `model.NewBoolVar` or `model.NewIntVar(0, 1)` to create `x` and `y` variables, storing references.

### Step 2 - Add Constraints and Objective
- Use `model.Add(sum(vars) == K)` for the cardinality constraint.
- Add the three linking constraints for each pair using linear inequalities.
- Set the objective with `model.Maximize(sum(weight * var for ...))`.

### Step 3 - Configure and Run Solver
- Create a `CpSolver` and set key parameters: `max_time_in_seconds`, `num_search_workers`, `random_seed`, and `relative_gap_limit = 0.0` for optimality.
- Execute `solver.Solve(model)` and capture the status.

### Step 4 - Extract and Validate Solution
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- Extract selected elements where `solver.Value(x_var) == 1`.
- Extract activated pairs where `solver.Value(y_var) == 1`.
- Compute the objective value from `solver.ObjectiveValue()`.

### Step 5 - (Optional) Brute-Force Verification
- For small `N` and `K`, generate all `combinations(N, K)` to verify the solver's solution is optimal.
- This confirms the model's interpretation of asymmetric weights.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
import itertools

model = cp_model.CpModel()
# ... create variables, add constraints, set objective as per formulation

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set solver parameters (e.g., time limit, threads)
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    objective_value = solver.ObjectiveValue()
    selected = [i for i in N if solver.Value(x[i]) == 1]
    activated = [(i, j) for (i, j) in P if solver.Value(y[(i, j)]) == 1]
    # ... proceed with solution
else:
    # Handle no solution found
    pass
```

### Common Pitfalls
- Not setting `relative_gap_limit = 0.0`, causing the solver to stop early with a suboptimal solution.
- Misinterpreting solver status codes; `FEASIBLE` may not be optimal if a time limit is hit.
- Forgetting to store variable references, leading to errors during solution value retrieval.

# Workflow 2 (MILP with Algebraic Modeling)

## Modeling stage

### Strategy Overview
This workflow uses a Mixed-Integer Linear Programming (MILP) approach via an algebraic modeling language (e.g., Pyomo). It is suitable for integration into larger linear models and leverages powerful MILP solvers (e.g., Gurobi, HiGHS).

### Step 1 - Define Sets and Parameters
- Declare a set `N` for elements and a set `P` for pairs (ordered or unordered based on problem context).
- Declare parameters: cardinality `K` and a weight parameter `w` indexed over `P`.

### Step 2 - Declare Decision Variables
- Create binary variable `x[i]` for `i in N` for selection.
- Create binary variable `y[i, j]` for `(i, j) in P` for pairwise activation.

### Step 3 - Enforce Selection Cardinality
- Add a constraint: `sum(x[i] for i in N) == K`.

### Step 4 - Link Variables with Linear Constraints
- For each `(i, j) in P`, add constraints:
  1. `y[i, j] <= x[i]`
  2. `y[i, j] <= x[j]`
  3. `y[i, j] >= x[i] + x[j] - 1`

### Step 5 - Define Maximization Objective
- Set objective to `maximize sum( w[i, j] * y[i, j] for (i, j) in P )`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all candidate elements."},
    {"name": "P", "description": "Set of pairs, defined as ordered (i,j) or unordered (i<j) based on weight structure."}
  ],
  "parameters": [
    {"name": "K", "description": "Exact number of elements to select."},
    {"name": "w", "description": "Weight for each pair in P."}
  ],
  "decision_variables": [
    {"name": "x", "domain": "Binary", "index": "i in N", "description": "Selection indicator for element i."},
    {"name": "y", "domain": "Binary", "index": "(i, j) in P", "description": "Activation indicator for pair (i, j)."}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum( w[i, j] * y[i, j] for (i, j) in P )"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum(x[i] for i in N) == K"},
    {"name": "activation_requires_first", "expression": "y[i, j] <= x[i] for (i, j) in P"},
    {"name": "activation_requires_second", "expression": "y[i, j] <= x[j] for (i, j) in P"},
    {"name": "activation_if_both_selected", "expression": "y[i, j] >= x[i] + x[j] - 1 for (i, j) in P"}
  ]
}
```

### Common Pitfalls
- Defining set `P` as unordered (`i < j`) but providing a full square weight matrix, leading to key errors when accessing `w[i, j]`.
- Using the same variable name `y` for both ordered and unordered interpretations within the same model, causing confusion.
- Omitting the third linking constraint (`y >= x_i + x_j - 1`), which allows `y` to be 0 even when both `x` are 1, potentially underestimating the objective.

## Solving stage

### Strategy Overview
Solve the algebraic model using a MILP solver via a modeling framework interface. Configure solver parameters for optimality, manage runtime limits, and rigorously check solution status.

### Step 1 - Build Model Instance
- Instantiate a concrete model.
- Populate sets, parameters, variables, constraints, and objective as defined in the formulation.

### Step 2 - Select and Configure Solver
- Choose a solver (e.g., `'gurobi'`, `'highs'`, `'cbc'`).
- Set solver options: `TimeLimit`, `MIPGap` (or `mip_rel_gap`) to 0.0, `Threads`, and `Seed` for reproducibility.

### Step 3 - Solve and Check Status
- Invoke the solver on the model instance.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`optimal`, `feasible`, `maxTimeLimit`).

### Step 4 - Extract and Verify Solution
- If solved successfully, retrieve the objective value and variable values.
- Optionally, compute the sum of activated weights from the solution as a sanity check against the reported objective.

### Step 5 - (Optional) Brute-Force Benchmark
- For small instances, enumerate all combinations to validate optimality and confirm the correct interpretation of pair weights (ordered vs. unordered).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=range(N_elements))
# Define P as ordered pairs or unordered pairs based on context
model.P = pyo.Set(initialize=all_pairs, dimen=2)

model.K = pyo.Param(initialize=K)
model.w = pyo.Param(model.P, initialize=weight_dict)

model.x = pyo.Var(model.N, domain=pyo.Binary)
model.y = pyo.Var(model.P, domain=pyo.Binary)

def obj_rule(m):
    return sum(m.w[i, j] * m.y[i, j] for (i, j) in m.P)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# Add constraints (cardinality and linking)
# ... constraint definitions

# solve with status / termination checks
solver = SolverFactory('solver_name')  # e.g., 'highs'
solver.options['time_limit'] = 30.0
solver.options['mip_rel_gap'] = 0.0
# Set other solver-specific options

results = solver.solve(model)

status = results.solver.status
termination = results.solver.termination_condition

if status == SolverStatus.ok and termination in (TerminationCondition.optimal, TerminationCondition.feasible):
    objective_value = pyo.value(model.obj)
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    # ... proceed with solution
else:
    # Handle solver failure or time limit
    pass
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to incorrect interpretation of suboptimal or incomplete solutions.
- Using a `MIPGap` > 0 without awareness, accepting suboptimal solutions as optimal.
- Incorrectly indexing the weight parameter with pairs not present in set `P`, causing runtime errors.
