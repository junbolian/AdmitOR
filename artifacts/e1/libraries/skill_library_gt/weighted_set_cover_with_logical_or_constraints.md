---
name: Weighted Set Cover with Logical OR Constraints
description: |
  Model and solve binary selection problems where items cover requirements via logical OR, minimizing weighted cost, using either CP-SAT or MILP frameworks.

---

# Workflow 1 (CP-SAT / OR-Tools)

## Modeling stage

### Strategy Overview
Model the problem using Google's OR-Tools CP-SAT solver, which is designed for discrete optimization with Boolean logic. This approach directly encodes binary selection and logical OR constraints into a constraint programming model for efficient solving.

### Step 1 - Define Data Structures
- Map the problem data into Python dictionaries or lists for clean separation of model logic.
- Create a list of all selectable `items`.
- Create a dictionary `cost` mapping each item to its selection cost/weight.
- Create a dictionary `coverage_requirements` mapping each requirement (e.g., region, task) to a list of items that can satisfy it.

### Step 2 - Instantiate Model and Variables
- Instantiate a CP-SAT model: `model = cp_model.CpModel()`.
- For each item `i` in `items`, create a binary decision variable: `x[i] = model.NewBoolVar(f"x_{i}")`.

### Step 3 - Add Set Cover Constraints
- For each requirement `r` and its corresponding list of covering items `cover_items` from `coverage_requirements`, add a constraint: `model.Add(sum(x[v] for v in cover_items) >= 1)`. This enforces the logical OR condition that at least one eligible item is selected.

### Step 4 - Define Weighted Sum Objective
- Formulate the minimization objective: `model.Minimize(sum(cost[i] * x[i] for i in items))`.

### Formulation Template
```json
{
  "sets": ["items", "requirements"],
  "parameters": ["cost[items]", "coverage_map[requirements -> items]"],
  "decision_variables": ["x[items] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": ["sum(x[v] for v in coverage_map[r]) >= 1, ∀ r in requirements"]
}
```

### Common Pitfalls
- Forgetting to ensure the `coverage_map` lists are non-empty for each requirement, which can lead to trivial infeasibility.
- Using Python's built-in `sum` on large lists within the model methods; while acceptable, be mindful of performance for very large-scale problems.
- Not using unique, descriptive names for variables, which complicates debugging.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver to find an optimal or feasible solution, then rigorously check the solver status and validate the extracted solution against the original problem constraints.

### Step 1 - Configure Solver and Solve
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set key parameters for control and reproducibility:
  - `solver.parameters.max_time_in_seconds = TIME_LIMIT`
  - `solver.parameters.num_search_workers = NUM_THREADS` (for parallel search)
  - `solver.parameters.random_seed = SEED_VALUE`
  - `solver.parameters.relative_gap_limit = 0.0` (for exact optimality).
- Execute the solver: `status = solver.Solve(model)`.

### Step 2 - Check Status and Extract Solution
- Check the result status: `if status == cp_model.OPTIMAL:` or `if status == cp_model.FEASIBLE:`.
- If optimal or feasible, extract the set of selected items: `selected = [i for i in items if solver.Value(x[i]) == 1]`.
- Extract the objective value: `total_cost = solver.ObjectiveValue()`.

### Step 3 - Validate Solution
- Implement a post-solution verification loop to ensure all coverage constraints are satisfied.
- For each requirement `r` in `coverage_requirements`, check: `covered = any(solver.Value(x[v]) == 1 for v in coverage_requirements[r])`. Log or raise an error if any requirement is uncovered.

### Code Usage
```python
from ortools.sat.python import cp_model
import json

# 1. Define problem data (placeholders)
items = [...]  # list of item indices
cost = {...}  # dict: item -> cost
coverage_requirements = {...}  # dict: requirement -> list of covering items

# 2. Build model
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in items}

# 3. Add constraints
for r, cover_items in coverage_requirements.items():
    model.Add(sum(x[v] for v in cover_items) >= 1)

# 4. Set objective
model.Minimize(sum(cost[i] * x[i] for i in items))

# 5. Configure and run solver
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

# 6. Check status and extract results
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected = [i for i in items if solver.Value(x[i]) == 1]
    objective_value = solver.ObjectiveValue()
    # 7. Validate
    for r, cover_items in coverage_requirements.items():
        if not any(solver.Value(x[v]) == 1 for v in cover_items):
            raise ValueError(f"Requirement {r} not covered.")
    print(f"RESULT:{objective_value}")
    # Optionally print selected items
else:
    print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'reason': 'infeasible_or_error'})}")
```

### Common Pitfalls
- Misinterpreting `cp_model.FEASIBLE` as optimal; always check for `OPTIMAL` if an exact solution is required.
- Not setting `relative_gap_limit = 0.0`, which can cause the solver to return a suboptimal solution if a non-zero gap is tolerated.
- Extracting variable values without checking the solver status first, leading to undefined behavior.

# Workflow 2 (MILP / Pyomo)

## Modeling stage

### Strategy Overview
Model the problem as a Mixed-Integer Linear Program (MILP) using Pyomo, a Python-based optimization modeling language. This approach provides a declarative, algebraic formulation that can be solved by various MILP solvers (e.g., Gurobi, HiGHS).

### Step 1 - Define Abstract Sets and Parameters
- Define Pyomo `Set` objects for the collection of selectable `SUBSETS` (items) and the `ELEMENTS` (requirements) to be covered.
- Define a `Param` `cost` indexed over `SUBSETS` to hold the weight for each item.
- Define a dictionary `coverage_dict` mapping each element to a list of eligible subsets.

### Step 2 - Declare Decision Variables
- Declare a binary decision variable `x` indexed over `SUBSETS` using `pyo.Var(..., domain=pyo.Binary)`.

### Step 3 - Formulate Objective Function
- Define the objective to minimize the weighted sum: `pyo.Objective(expr=sum(cost[s] * x[s] for s in SUBSETS), sense=pyo.minimize)`.

### Step 4 - Formulate Coverage Constraints
- Define a constraint rule `coverage_rule` that, for each element `e`, sums the variables of its eligible subsets and enforces the sum >= 1.
- Add this rule as a `pyo.Constraint` indexed over the `ELEMENTS` set.

### Formulation Template
```json
{
  "sets": ["SUBSETS", "ELEMENTS"],
  "parameters": ["cost[SUBSETS]", "coverage_map[ELEMENTS -> SUBSETS]"],
  "decision_variables": ["x[SUBSETS] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s] * x[s] for s in SUBSETS)"
  },
  "constraints": ["sum(x[s] for s in coverage_map[e]) >= 1, ∀ e in ELEMENTS"]
}
```

### Common Pitfalls
- Defining the `coverage_rule` inside the Pyomo model scope incorrectly, leading to variable scope issues; define it as a standalone function using the model `m` as the first argument.
- Using Python lists instead of Pyomo Sets for indexing, which can limit model introspection and reusability.
- Not initializing parameters completely, which causes errors during expression construction.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with a MILP solver. Configure solver options for optimality and performance, then solve the model. Crucially, check both the solver status and termination condition before extracting and validating the solution.

### Step 1 - Select Solver and Configure
- Instantiate a solver object: `solver = pyo.SolverFactory('SOLVER_NAME')` (e.g., `'highs'`, `'gurobi'`).
- Set solver-specific options for a deterministic, optimal solve:
  - `solver.options['time_limit'] = TIME_LIMIT`
  - `solver.options['mip_rel_gap'] = 0.0`
  - `solver.options['threads'] = NUM_THREADS`
  - `solver.options['seed'] = SEED_VALUE` (if supported).

### Step 2 - Solve and Check Status
- Execute the solver: `results = solver.solve(model, tee=False)`.
- Import status enums: `from pyomo.opt import SolverStatus, TerminationCondition`.
- Check if the solve was successful and resulted in a valid solution: `if results.solver.status == SolverStatus.ok and results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:`.

### Step 3 - Extract and Verify Solution
- If the status checks pass, extract the objective value: `objective_value = float(pyo.value(model.obj))`.
- Extract selected subsets: `selected = [s for s in model.SUBSETS if pyo.value(model.x[s]) > 0.5]`.
- Optionally, verify coverage by iterating through `coverage_dict` and checking if any selected subset appears in each element's list.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# 1. Define problem data (placeholders)
SUBSETS = [...]  # list of subset indices
ELEMENTS = [...]  # list of element indices
cost_dict = {...}  # dict: subset -> cost
coverage_dict = {...}  # dict: element -> list of eligible subsets

# 2. Build Pyomo Concrete Model
m = pyo.ConcreteModel()
m.SUBSETS = pyo.Set(initialize=SUBSETS)
m.ELEMENTS = pyo.Set(initialize=ELEMENTS)
m.cost = pyo.Param(m.SUBSETS, initialize=cost_dict)
m.x = pyo.Var(m.SUBSETS, domain=pyo.Binary)

# 3. Define objective
m.obj = pyo.Objective(expr=sum(m.cost[s] * m.x[s] for s in m.SUBSETS), sense=pyo.minimize)

# 4. Define constraints
def coverage_rule(model, e):
    return sum(model.x[s] for s in coverage_dict[e]) >= 1
m.coverage_con = pyo.Constraint(m.ELEMENTS, rule=coverage_rule)

# 5. Select solver and configure
solver = pyo.SolverFactory('highs')  # or 'gurobi', 'cbc'
solver.options['time_limit'] = 30.0
solver.options['mip_rel_gap'] = 0.0
solver.options['threads'] = 4
# solver.options['seed'] = 42  # if using Gurobi

# 6. Solve
results = solver.solve(m, tee=False)

# 7. Check status and extract results
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(m.obj))
    selected = [s for s in m.SUBSETS if pyo.value(m.x[s]) > 0.5]
    # 8. Validate (optional)
    for e in m.ELEMENTS:
        if not any(s in selected for s in coverage_dict[e]):
            raise ValueError(f"Element {e} not covered.")
    print(f"RESULT:{objective_value}")
else:
    print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'reason': 'infeasible_or_error', 'solver_status': str(status), 'termination': str(term)})}")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (which indicates the solver ran) with `TerminationCondition.optimal` (which indicates optimality). Both must be checked.
- Using `pyo.value()` on variables or expressions before verifying the solve was successful, which may raise exceptions or return `None`.
- Not setting `mip_rel_gap=0.0`, allowing the solver to stop early with a gap, potentially returning a suboptimal solution.
