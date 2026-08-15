---
name: Binary Set Cover with Multiple Coverage Constraints
description: |
  Model and solve binary selection problems with linear costs and multiple coverage constraints using CP-SAT or Pyomo MIP solvers.

---

# Workflow 1 (CP-SAT / ortools)

## Modeling stage

### Strategy Overview
This workflow uses Google's CP-SAT solver via OR-Tools, ideal for combinatorial problems with binary variables. The model is built directly in Python with explicit variable and constraint objects.

### Step 1 - Define Selection Variables
- Create a binary decision variable for each selectable item using `model.NewBoolVar()`.
- Use descriptive variable names, e.g., `x[i]`, where `i` is a unique identifier from a set of items.
- Store variables in a dictionary for easy access: `x = {i: model.NewBoolVar(f"x_{i}") for i in items}`.

### Step 2 - Formulate Linear Cost Objective
- Define a cost parameter `c[i]` for each item.
- Set the objective to minimize total cost: `model.Minimize(sum(c[i] * x[i] for i in items))`.

### Step 3 - Enforce Coverage Constraints
- For each coverage requirement, create a linear inequality summing selected variables.
- For a constraint requiring at least `k` items from a subset `S` to be selected: `model.Add(sum(x[i] for i in S) >= k)`.
- Group identical mathematical constraints (same `S` and `k`) to avoid redundancy, even if they have different logical names.

### Step 4 - Analyze and Simplify Constraints
- Before implementation, check for logical implications (e.g., sum >= total variables forces all to 1).
- Remove constraints that are dominated by or identical to others to reduce model size.

### Formulation Template
```json
{
  "sets": [
    "items",
    "constraint_groups"
  ],
  "parameters": [
    {"name": "cost", "index": "items"},
    {"name": "required_coverage", "index": "constraint_groups"},
    {"name": "covered_items", "index": "constraint_groups", "subindex": "items"}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "coverage", "expression": "sum(x[i] for i in covered_items[g]) >= required_coverage[g]", "index": "constraint_groups"}
  ]
}
```

### Common Pitfalls
- Adding duplicate constraints for each named requirement, which unnecessarily increases model size.
- Not verifying that constraint indices and parameters align correctly, leading to missing or incorrect constraints.
- Overlooking forced variable values from constraint logic, which can simplify the model.

## Solving stage

### Strategy Overview
Solve using `cp_model.CpSolver` with configured time limits and optimality tolerances. Always verify solver status and validate the solution against constraints.

### Step 1 - Configure Solver Parameters
- Instantiate `CpSolver()` and set key parameters: `solver.parameters.max_time_in_seconds = time_limit`, `solver.parameters.num_search_workers = threads`, `solver.parameters.random_seed = seed`.
- Set `solver.parameters.relative_gap_limit = 0.0` for exact optimal solutions.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if a feasible solution was found: `if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):`.
- If infeasible, output a structured error: `{"status": "failed", "reason": "no_feasible_solution", "solver_status": int(status)}`.

### Step 3 - Extract and Validate Solution
- If feasible, extract variable values: `solution = {i: solver.Value(x[i]) for i in items}`.
- Optionally, validate by recomputing constraint left-hand sides and comparing to requirements.
- For debugging, print summaries: `print(f"Coverage group {g}: {sum_s} >= {k}: {sum_s >= k}")`.

### Step 4 - Implement Sanity Checks (Small Problems)
- For problems with few items (e.g., ≤10), implement exhaustive enumeration via `itertools.product` to verify solver optimality.
- Compare brute-force optimal cost with solver result.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
items = [...]  # list of item identifiers
cost = {...}   # dict: item -> cost
x = {i: model.NewBoolVar(f"x_{i}") for i in items}
model.Minimize(sum(cost[i] * x[i] for i in items))
# Add coverage constraints: for each group g, subset S_g, requirement k_g
for g, (S_g, k_g) in coverage_requirements.items():
    model.Add(sum(x[i] for i in S_g) >= k_g)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    solution = {i: solver.Value(x[i]) for i in items}
    objective_value = solver.ObjectiveValue()
    # validation and output
else:
    result = {"status": "failed", "reason": "no_feasible_solution", "solver_status": int(status)}
```

### Common Pitfalls
- Forgetting to check for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing suboptimal but valid solutions.
- Using invalid solver parameter values (e.g., negative threads).
- Not setting a random seed, leading to non-reproducible results.

---

# Workflow 2 (Pyomo / MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model definition, separating data from structure. It can interface with various MIP solvers (e.g., Gurobi, HiGHS, CBC) and is suited for maintainable, data-driven implementations.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` components for items and constraint groups.
- Define `Param` components for costs and coverage requirements, indexed appropriately.
- This separation allows easy swapping of problem data.

### Step 2 - Declare Binary Decision Variables
- Create a `Var` component with `domain=pyo.Binary`, indexed by the items set.
- Use a meaningful variable name, e.g., `model.x`.

### Step 3 - Construct Linear Objective
- Define an `Objective` rule that returns `sum(model.cost[i] * model.x[i] for i in model.items)`.
- Set the sense to minimize.

### Step 4 - Build Coverage Constraints with Rule Functions
- Define a `Constraint` component indexed by constraint groups.
- For each group, the rule should sum `model.x[i]` over the relevant subset and enforce `>= required_coverage`.
- Use a dictionary or parameter to map groups to their item subsets and requirements.

### Step 5 - Consolidate Identical Constraint Forms
- Pre-process data to group constraints with identical mathematical forms (same subset and RHS).
- Add only one Pyomo constraint per unique form to improve solver performance.

### Formulation Template
```json
{
  "sets": [
    "items",
    "constraint_groups"
  ],
  "parameters": [
    {"name": "cost", "index": "items"},
    {"name": "required_coverage", "index": "constraint_groups"},
    {"name": "covered_items", "index": "constraint_groups", "subindex": "items", "type": "sparse"}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "coverage", "expression": "sum(x[i] for i in covered_items[g]) >= required_coverage[g]", "index": "constraint_groups"}
  ]
}
```

### Common Pitfalls
- Creating duplicate Pyomo constraints by iterating over raw data without deduplication.
- Incorrectly indexing parameters within constraint rules, causing `KeyError` or silent constraint omission.
- Mixing abstract model definition with solver-specific options too early.

## Solving stage

### Strategy Overview
Use a Pyomo `SolverFactory` with appropriate solver options. Carefully manage solution loading and verify termination conditions.

### Step 1 - Select Solver and Set Options
- Instantiate solver: `solver = pyo.SolverFactory('solver_name')` (e.g., 'gurobi', 'highs').
- Set options: `solver.options['TimeLimit'] = time_limit`, `solver.options['MIPGap'] = 0.0`, `solver.options['Threads'] = threads`, `solver.options['Seed'] = seed`.

### Step 2 - Solve with Robust Status Checking
- Execute `results = solver.solve(model, tee=False, load_solutions=False)`.
- Check solver status: `if results.solver.status == pyo.SolverStatus.ok:`.
- Check termination condition: `if results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:`.
- Only then load the solution into the model: `model.solutions.load_from(results)`.

### Step 3 - Extract Solution and Verify Constraints
- Extract variable values: `solution = {i: pyo.value(model.x[i]) for i in model.items}`.
- Manually compute constraint left-hand sides using the extracted values to ensure all coverage requirements are met.
- Log any violated constraints for debugging.

### Step 4 - Perform Incremental Debugging if Needed
- If the model is infeasible, create a minimal test by adding constraints one at a time.
- Fix variables to values deduced from constraints to test logical consistency.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items_list)
model.constraint_groups = pyo.Set(initialize=groups_list)
model.cost = pyo.Param(model.items, initialize=cost_dict)
model.required_coverage = pyo.Param(model.constraint_groups, initialize=coverage_req_dict)
# covered_items is a sparse parameter: (g,i) -> 1 if item i in group g
model.covered_items = pyo.Param(model.constraint_groups, model.items, initialize=covered_items_dict, default=0)
model.x = pyo.Var(model.items, domain=pyo.Binary)
def obj_rule(m):
    return sum(m.cost[i] * m.x[i] for i in m.items)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
def coverage_rule(m, g):
    return sum(m.x[i] for i in m.items if m.covered_items[g, i] == 1) >= m.required_coverage[g]
model.coverage = pyo.Constraint(model.constraint_groups, rule=coverage_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30.0
solver.options['mip_rel_gap'] = -1.0  # exact optimality for some solvers
results = solver.solve(model, tee=False, load_solutions=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                              pyo.TerminationCondition.feasible)):
    model.solutions.load_from(results)
    solution = {i: pyo.value(model.x[i]) for i in model.items}
    objective_value = pyo.value(model.obj)
else:
    result = {"status": "failed", "solver_status": str(results.solver.status),
              "termination_condition": str(results.solver.termination_condition)}
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) without checking termination condition first.
- Using incorrect parameter names or keys in constraint rules, leading to runtime errors.
- Setting invalid solver options (e.g., `threads = -1`) that cause the solver to fail silently.
