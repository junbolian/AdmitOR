---
name: Assignment Maximization with Compatibility Constraints
description: |
  Model and solve binary assignment problems with capacity and preference constraints to maximize total assignments.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, designed for constraint programming with Boolean and integer variables. It is well-suited for pure binary assignment problems where the objective is to maximize the count of selected assignments under at-most-one capacity and binary compatibility rules.

### Step 1 - Define Sets and Parameters
- Define the two sets of entities to be matched (e.g., `set_A`, `set_B`).
- Create a binary compatibility matrix `compatible[a][b]` (1 if assignment is allowed, 0 otherwise) as input data.

### Step 2 - Create Binary Decision Variables
- For each pair `(a, b)` in the Cartesian product of the sets, create a binary variable `assign[a][b]` using `model.NewBoolVar()`.
- Use descriptive naming (e.g., `f"assign_{a}_{b}"`) for debugging clarity.

### Step 3 - Add Capacity Constraints
- For each element `a` in `set_A`, add a constraint: `sum(assign[a][b] for b in set_B) <= 1`.
- For each element `b` in `set_B`, add a constraint: `sum(assign[a][b] for a in set_A) <= 1`.

### Step 4 - Enforce Compatibility Constraints
- For each pair `(a, b)`, add a linear inequality: `assign[a][b] <= compatible[a][b]`. This ensures an assignment variable can only be 1 if the corresponding compatibility parameter is 1.

### Step 5 - Define Maximization Objective
- Set the objective to maximize the sum of all assignment variables: `sum(assign[a][b] for a in set_A for b in set_B)`.

### Formulation Template
```json
{
  "sets": ["set_A", "set_B"],
  "parameters": [
    {"name": "compatible", "type": "binary_matrix", "dimensions": ["set_A", "set_B"]}
  ],
  "decision_variables": [
    {"name": "assign", "type": "binary", "dimensions": ["set_A", "set_B"]}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(assign[a][b] for a in set_A for b in set_B)"
  },
  "constraints": [
    {"name": "capacity_a", "expression": "sum(assign[a][b] for b in set_B) <= 1 for each a in set_A"},
    {"name": "capacity_b", "expression": "sum(assign[a][b] for a in set_A) <= 1 for each b in set_B"},
    {"name": "compatibility", "expression": "assign[a][b] <= compatible[a][b] for each a in set_A, b in set_B"}
  ]
}
```

### Common Pitfalls
- Forgetting to enforce both capacity constraints (one for each set), leading to invalid multiple assignments.
- Using a non-binary (e.g., integer) compatibility parameter, which can cause the constraint `assign <= compatible` to be incorrectly restrictive.
- Creating assignment variables for all pairs without filtering, which can increase model size unnecessarily for large, sparse compatibility matrices.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configurable time and parallel search. Extract the solution by checking variable values, and handle different solver statuses appropriately.

### Step 1 - Configure Solver Parameters
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set practical limits: `solver.parameters.max_time_in_seconds = 30.0`.
- Enable parallel search: `solver.parameters.num_search_workers = 8`.
- Set a random seed for reproducibility: `solver.parameters.random_seed = 42`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check for acceptable status: `status in (cp_model.OPTIMAL, cp_model.FEASIBLE)`. If not, proceed to error handling.

### Step 3 - Extract and Validate Solution
- If status is acceptable, retrieve the objective value: `total_assignments = solver.ObjectiveValue()`.
- Iterate over all assignment variables. If `solver.Value(assign[a][b]) == 1`, record the assignment `(a, b)`.
- Optionally, perform a sanity check: verify that the number of assignments matches the objective value and that no capacity or compatibility constraints are violated.

### Step 4 - Handle Non-Optimal Results
- If status is `cp_model.UNKNOWN` (often due to time limit), report the best solution found and note the limit was hit.
- If status is `cp_model.INFEASIBLE`, analyze the compatibility matrix and capacity constraints for obvious conflicts.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... [Variable and constraint creation steps as per modeling stage] ...
# solve with status / termination checks
solver = cp_model.CpSolver()
# Apply parameter settings
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)
# Check status and extract results
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Total assignments: {solver.ObjectiveValue()}")
    assignments = []
    for a in set_A:
        for b in set_B:
            if solver.Value(assign[a][b]) == 1:
                assignments.append((a, b))
    print(f"Assignments: {assignments}")
else:
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Not checking for `cp_model.FEASIBLE` in addition to `OPTIMAL`, which can cause valid solutions to be missed when a time limit is set.
- Misinterpreting `solver.ObjectiveValue()` for feasibility problems; it is only defined for optimization objectives.
- Attempting to access `solver.Value()` on variables before checking the solver status, which may raise an error.

# Workflow 2 (MIP with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for model declaration and a Mixed-Integer Programming (MIP) solver (e.g., HiGHS, CBC) via a generic interface. It is suitable for users familiar with algebraic modeling languages and offers flexibility in solver choice and advanced solution analysis.

### Step 1 - Declare Abstract Sets and Parameters
- Define the index sets `set_A` and `set_B` as `pyo.Set()` objects.
- Declare the binary compatibility parameter `model.compatible` as a `pyo.Param()` indexed over both sets.

### Step 2 - Define Binary Variables with Pyomo Rule
- Create a `pyo.Var()` indexed over `(set_A, set_B)`, within `model.assign`, with domain `pyo.Binary`.
- Use a rule or initialize the variable bounds directly during construction.

### Step 3 - Build Capacity Constraints via Rules
- Define a constraint rule for each `a` in `set_A`: `sum(model.assign[a, b] for b in set_B) <= 1`.
- Define a constraint rule for each `b` in `set_B`: `sum(model.assign[a, b] for a in set_A) <= 1`.
- Add these constraints to the model using `pyo.Constraint()` with index rules.

### Step 4 - Apply Compatibility Constraints
- Add a constraint for each `(a, b)` pair: `model.assign[a, b] <= model.compatible[a, b]`. This can be implemented efficiently using a `ConstraintList` or a rule.

### Step 5 - Set Maximization Objective
- Define the objective: `pyo.Objective(expr=sum(model.assign[a, b] for a in set_A for b in set_B), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["set_A", "set_B"],
  "parameters": [
    {"name": "compatible", "type": "Param", "domain": "Binary", "indexed_by": ["set_A", "set_B"]}
  ],
  "decision_variables": [
    {"name": "assign", "type": "Var", "domain": "Binary", "indexed_by": ["set_A", "set_B"]}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(assign[a, b] for a in set_A for b in set_B)"
  },
  "constraints": [
    {"name": "cap_a", "expression": "sum(assign[a, b] for b in set_B) <= 1 for each a in set_A"},
    {"name": "cap_b", "expression": "sum(assign[a, b] for a in set_A) <= 1 for each b in set_B"},
    {"name": "comp", "expression": "assign[a, b] <= compatible[a, b] for each a in set_A, b in set_B"}
  ]
}
```

### Common Pitfalls
- Using `pyo.ConcreteModel` and initializing data after variable creation, which can lead to out-of-order errors.
- Defining constraints with Python loops that modify the model inside the loop, instead of using Pyomo's rule-based construction for cleaner, more maintainable code.
- Not setting `domain=pyo.Binary` on variables, which defaults to `Reals` and breaks the binary assignment semantics.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MIP solver. Carefully manage solution loading and status checks to robustly handle different termination conditions.

### Step 1 - Select and Configure Solver
- Instantiate a solver object: `solver = pyo.SolverFactory('highs')` (or 'cbc', 'glpk').
- Set solver options, such as time limit: `solver.options['time_limit'] = 30`.

### Step 2 - Solve with Explicit Solution Loading
- Call `results = solver.solve(model, tee=False, load_solutions=False)`. Setting `load_solutions=False` prevents automatic loading, allowing status inspection first.
- Check the solver status: `results.solver.status == pyo.SolverStatus.ok`.

### Step 3 - Check Termination Condition
- Inspect the termination condition: `results.solver.termination_condition`.
- Acceptable conditions are `pyo.TerminationCondition.optimal` or `pyo.TerminationCondition.feasible`. Handle other conditions (e.g., `maxTimeLimit`, `infeasible`) appropriately.

### Step 4 - Load and Extract Solution
- If status and termination are acceptable, load the solution: `model.solutions.load_from(results)`.
- Iterate over the assignment variable index. If `pyo.value(model.assign[a, b]) > 0.5`, record the assignment.
- Retrieve the objective value from `pyo.value(model.obj)`.

### Step 5 - Implement Solver Fallback
- If the primary solver fails or returns an unknown status, implement a fallback to an alternative solver (e.g., switch from 'highs' to 'cbc').

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... [Set, parameter, variable, constraint, and objective creation as per modeling stage] ...
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False, load_solutions=False)
# Check solver status
if results.solver.status == pyo.SolverStatus.ok:
    # Check termination condition
    term_cond = results.solver.termination_condition
    if term_cond in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
        model.solutions.load_from(results)
        print(f"Objective value: {pyo.value(model.obj)}")
        assignments = []
        for a in model.set_A:
            for b in model.set_B:
                if pyo.value(model.assign[a, b]) > 0.5:
                    assignments.append((a, b))
        print(f"Assignments: {assignments}")
    else:
        print(f"Solver stopped with condition: {term_cond}")
else:
    print("Solver failed. Attempting fallback...")
    # Fallback solver logic here
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) without checking termination condition, which can lead to errors when accessing variable values from an incomplete or infeasible solve.
- Comparing floating-point variable values directly to 1.0; use a tolerance (e.g., `> 0.5`) due to solver numerical precision.
- Not using `pyo.value()` to extract scalar values from Pyomo components, leading to incorrect comparisons or output.
