---
name: Cardinality-Constrained Pairwise Selection
description: |
  Model and solve selection problems with exact cardinality and pairwise interaction rewards using binary variables and linearized logic.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
This workflow models the problem using the OR-Tools CP-SAT solver, which natively handles Boolean variables and linear constraints efficiently. It is well-suited for medium to large instances where a dedicated integer programming solver is preferred.

### Step 1 - Define Selection Variables
- Create a binary variable `x[i]` for each element `i` in the universal set `N`.
- `x[i] = 1` indicates the element is selected; `0` otherwise.

### Step 2 - Define Pairwise Interaction Variables
- For each ordered pair `(i, j)` where `i != j`, create an auxiliary binary variable `z[(i, j)]`.
- This variable will be forced to represent the logical AND of `x[i]` and `x[j]`.

### Step 3 - Enforce Exact Selection Count
- Add a linear equality constraint: `sum_{i in N} x[i] == K`, where `K` is the required number of selected elements.

### Step 4 - Linearize Pairwise Logic
- For each ordered pair `(i, j)`, add three linear constraints to enforce `z[(i, j)] = x[i] AND x[j]`:
  1. `z[(i, j)] <= x[i]`
  2. `z[(i, j)] <= x[j]`
  3. `z[(i, j)] >= x[i] + x[j] - 1`

### Step 5 - Formulate Objective
- Define a parameter `d[(i, j)]` representing the directed weight for pair `(i, j)`.
- Set the objective to maximize the total weighted pairwise sum: `maximize sum_{i, j, i != j} d[(i, j)] * z[(i, j)]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Universal set of candidate elements"}
  ],
  "parameters": [
    {"name": "K", "description": "Exact number of elements to select", "type": "integer"},
    {"name": "d", "description": "Dictionary mapping ordered pair (i,j) to its weight/score", "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "description": "Binary selection variable for each element i in N", "type": "binary"},
    {"name": "z", "description": "Binary variable for ordered pair (i,j), i != j, representing x[i] AND x[j]", "type": "binary"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in N} sum_{j in N, j != i} d[(i,j)] * z[(i,j)]"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum_{i in N} x[i] == K"},
    {"name": "logic_upper_i", "expression": "z[(i,j)] <= x[i] for all i, j in N, i != j"},
    {"name": "logic_upper_j", "expression": "z[(i,j)] <= x[j] for all i, j in N, i != j"},
    {"name": "logic_lower", "expression": "z[(i,j)] >= x[i] + x[j] - 1 for all i, j in N, i != j"}
  ]
}
```

### Common Pitfalls
- Defining `z` variables for `i == j` is unnecessary and increases model size.
- Forgetting to enforce the `i != j` condition in the objective sum can lead to incorrect scores if `d[(i,i)]` is defined.
- Using a single `z` variable per unordered pair for symmetric problems (`d[(i,j)] == d[(j,i)]`) can reduce variables but requires adjusting the objective and constraints accordingly.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, configuring it for a balance of speed and optimality. Extract and verify the solution.

### Step 1 - Instantiate Model and Variables
- Create a `CpModel` object.
- Instantiate `x` and `z` variables using `NewBoolVar`.

### Step 2 - Add Constraints and Objective
- Add the cardinality constraint using `Add`.
- Add the pairwise logic constraints via loops.
- Set the objective using `Maximize`.

### Step 3 - Configure and Run Solver
- Create a `CpSolver` and set key parameters: time limit, number of workers, random seed, and optimality gap.
- Execute the solver on the model.

### Step 4 - Extract and Validate Solution
- Check the solver status (`OPTIMAL` or `FEASIBLE`).
- Extract selected elements where `solver.Value(x[i]) == 1`.
- Retrieve the objective value.
- Optionally, verify the logical consistency of `z` variables for small instances.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model
model = cp_model.CpModel()
N = range(num_elements)
x = {i: model.NewBoolVar(f"x_{i}") for i in N}
z = {(i, j): model.NewBoolVar(f"z_{i}_{j}") for i in N for j in N if i != j}

# Cardinality constraint
model.Add(sum(x[i] for i in N) == K)

# Pairwise logic constraints
for i in N:
    for j in N:
        if i != j:
            model.Add(z[(i, j)] <= x[i])
            model.Add(z[(i, j)] <= x[j])
            model.Add(z[(i, j)] >= x[i] + x[j] - 1)

# Objective
model.Maximize(sum(d[(i, j)] * z[(i, j)] for i in N for j in N if i != j))

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

# Extract solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in N if solver.Value(x[i]) == 1]
    objective_value = solver.ObjectiveValue()
    # ... proceed with solution
else:
    # Handle no solution found
    pass
```

### Common Pitfalls
- Not setting a time limit for large instances can lead to excessive runtime.
- Assuming `FEASIBLE` status implies optimality; check if a non-zero gap was allowed.
- Directly using `solver.Value()` on a variable before checking solver status may raise an error.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model formulation, which is then solved by an external Mixed-Integer Programming (MIP) solver like Gurobi, HiGHS, or CBC. This approach is portable and leverages advanced commercial/open-source solvers.

### Step 1 - Define Abstract Sets and Parameters
- Declare a Pyomo `Set` for the element universe `N`.
- Declare a `Param` for the cardinality `K` and a dictionary-based parameter for pairwise weights `d`.

### Step 2 - Declare Decision Variables
- Define a `Var` indexed by `N` with `domain=Binary` for selection variables `x`.
- Define a `Var` indexed by ordered pairs `(i, j)` where `i != j` with `domain=Binary` for pairwise variables `z`.

### Step 3 - Enforce Cardinality Constraint
- Add a `Constraint` enforcing `sum_{i in N} x[i] == K`.

### Step 4 - Linearize Pairwise Logic
- Add three constraint rules for each ordered pair to enforce `z[i,j] = x[i] * x[j]` using the standard linearization.

### Step 5 - Define Maximization Objective
- Create an `Objective` with `sense=maximize` and expression `sum_{i in N} sum_{j in N, j != i} d[i,j] * z[i,j]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Universal set of candidate elements"}
  ],
  "parameters": [
    {"name": "K", "description": "Exact number of elements to select", "type": "integer"},
    {"name": "d", "description": "Pyomo Param or external dictionary for pairwise weights", "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "description": "Binary selection variable for each i in N", "type": "binary", "domain": "Binary"},
    {"name": "z", "description": "Binary variable for ordered pair (i,j), i != j", "type": "binary", "domain": "Binary"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in N} sum_{j in N, j != i} d[i,j] * z[i,j]"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum_{i in N} x[i] == K"},
    {"name": "logic_upper_i", "expression": "z[i,j] <= x[i] for all i, j in N, i != j"},
    {"name": "logic_upper_j", "expression": "z[i,j] <= x[j] for all i, j in N, i != j"},
    {"name": "logic_lower", "expression": "z[i,j] >= x[i] + x[j] - 1 for all i, j in N, i != j"}
  ]
}
```

### Common Pitfalls
- Attempting to use `d[i,j]` directly in Pyomo rules if `d` is a plain Python dictionary; it must be accessible within the rule's scope.
- Defining `z` over a `Set` that includes `i == j` will create invalid constraints.
- For solvers like HiGHS, forgetting to set `load_solutions=False` and manually load the solution can cause errors.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model, send it to a MIP solver via a solver factory, configure solver options, and handle the solution loading process robustly.

### Step 1 - Build Concrete Model
- Instantiate a `ConcreteModel()`.
- Populate the model with the defined sets, parameters, variables, constraints, and objective.

### Step 2 - Select and Configure Solver
- Use `SolverFactory('solver_name')` (e.g., 'gurobi', 'highs', 'cbc').
- Set solver options: time limit, optimality gap, thread count, and random seed.

### Step 3 - Solve and Check Status
- Execute `solve()` with appropriate flags (e.g., `tee=False`, `load_solutions=False` for HiGHS).
- Check the solver status and termination condition to determine success.

### Step 4 - Load and Extract Solution
- If successful, load the solution into the model instance.
- Extract selected elements by evaluating `value(x[i]) > 0.5`.
- Compute the achieved objective value.

### Code Usage
```python
import pyomo.environ as pyo

# Build model
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=range(num_elements))
model.K = pyo.Param(initialize=K)
# Assume `d_dict` is a pre-defined dictionary of weights

model.x = pyo.Var(model.N, domain=pyo.Binary)
model.z = pyo.Var([(i, j) for i in model.N for j in model.N if i != j], domain=pyo.Binary)

def cardinality_rule(m):
    return sum(m.x[i] for i in m.N) == m.K
model.cardinality = pyo.Constraint(rule=cardinality_rule)

def logic_upper_i_rule(m, i, j):
    if i == j:
        return pyo.Constraint.Skip
    return m.z[i, j] <= m.x[i]
model.logic_upper_i = pyo.Constraint(model.N, model.N, rule=logic_upper_i_rule)

def logic_upper_j_rule(m, i, j):
    if i == j:
        return pyo.Constraint.Skip
    return m.z[i, j] <= m.x[j]
model.logic_upper_j = pyo.Constraint(model.N, model.N, rule=logic_upper_j_rule)

def logic_lower_rule(m, i, j):
    if i == j:
        return pyo.Constraint.Skip
    return m.z[i, j] >= m.x[i] + m.x[j] - 1
model.logic_lower = pyo.Constraint(model.N, model.N, rule=logic_lower_rule)

def objective_rule(m):
    return sum(d_dict[i, j] * m.z[i, j] for i in m.N for j in m.N if i != j)
model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

# Solve
solver = pyo.SolverFactory('highs')  # or 'gurobi', 'cbc'
solver.options['time_limit'] = 30
solver.options['threads'] = 4
# For HiGHS, load_solutions=False is often needed
results = solver.solve(model, tee=False, load_solutions=False)

# Check status and extract
from pyomo.opt import SolverStatus, TerminationCondition
status_ok = (results.solver.status == SolverStatus.ok and
             results.solver.termination_condition in
             [TerminationCondition.optimal, TerminationCondition.feasible])
if status_ok:
    model.solutions.load_from(results)
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    objective_value = pyo.value(model.obj)
    # ... proceed with solution
else:
    # Handle solver failure
    pass
```

### Common Pitfalls
- Using `load_solutions=True` with HiGHS may cause an error; use `load_solutions=False` and manually load.
- Not checking both `solver.status` and `termination_condition` can misclassify suboptimal or failed runs.
- Forgetting to filter `i != j` in constraint rules can create invalid constraints for `z[i,i]`.
