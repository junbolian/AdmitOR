---
name: Binary Set Cover with Multiple Coverage Constraints
description: |
  A skill for modeling and solving binary selection problems with linear costs and multiple coverage constraints, applicable to team deployment, facility location, and resource allocation scenarios.

---

# Workflow 1 (CP-SAT via ortools)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, a high-performance constraint programming solver for integer problems. It is well-suited for binary selection models with linear constraints and objectives, offering fast, exact solutions with robust parameter control.

### Step 1 - Define Selection Variables
- Create a binary decision variable for each selectable item (e.g., team, facility, asset) using `model.NewBoolVar()`.
- Store variables in a dictionary keyed by item identifier for easy reference in constraints and objective.

### Step 2 - Formulate Linear Cost Objective
- Define a linear objective to minimize total selection cost: `sum(cost[item] * variable[item] for item in items)`.
- Use a parameter dictionary `cost` mapping item identifiers to their selection cost.

### Step 3 - Implement Coverage Constraints
- For each coverage requirement, create a linear constraint: `sum(variables in subset) >= required_coverage`.
- Group identical constraint patterns (same subset and RHS) to avoid adding redundant constraints to the model.

### Step 4 - Analyze Constraint Redundancy
- Before finalizing the model, analyze constraints for logical implications (e.g., a constraint forcing all variables to 1 makes individual variable constraints redundant).
- This step is a manual check to simplify the model and aid debugging.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items"
  ],
  "parameters": [
    "cost_i: Cost of selecting item i ∈ I",
    "coverage_requirements: List of tuples (subset_j ⊆ I, min_coverage_j)"
  ],
  "decision_variables": [
    "x_i ∈ {0,1}: 1 if item i is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} cost_i * x_i"
  },
  "constraints": [
    "∑_{i ∈ subset_j} x_i >= min_coverage_j, for each coverage requirement j"
  ]
}
```

### Common Pitfalls
- Adding multiple identical constraints, which wastes solver presolve time without changing the feasible region.
- Using 0-based indexing for item IDs when parameters are 1-based, leading to key errors.
- Forgetting to convert constraint logic (e.g., "at least 2 from {A,B,C}") into the correct linear inequality.

## Solving stage

### Strategy Overview
Solving involves configuring the CP-SAT solver for performance and determinism, executing the solve, and rigorously checking the status before extracting and validating the solution.

### Step 1 - Configure Solver Parameters
- Instantiate `cp_model.CpSolver()`.
- Set key parameters: `max_time_in_seconds` for runtime limit, `num_search_workers` for parallelism, `random_seed` for reproducibility, and `relative_gap_limit = 0.0` for exact optimality.

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve(model)`.
- Check the returned status against `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. If neither, the model is infeasible or the solver timed out.

### Step 3 - Extract and Verify Solution
- If solve was successful, extract selected items: `solver.Value(variable[item]) == 1`.
- Retrieve the objective value via `solver.ObjectiveValue()`.
- Programmatically verify all coverage constraints using the extracted values to catch modeling errors.

### Step 4 - Debug Infeasibility
- If the model is infeasible, create a minimal test case (e.g., a single constraint) to verify solver behavior.
- For small problems (n ≤ 10), implement brute-force enumeration to validate the constraint logic independently of the solver.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... define variables, objective, constraints as per modeling stage

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected_items = [i for i in items if solver.Value(x[i]) == 1]
    total_cost = solver.ObjectiveValue()
    # ... verify constraints with selected_items
else:
    print("Model is infeasible or solver timed out.")
    # ... implement debugging steps
```

### Common Pitfalls
- Not checking solver status before accessing `ObjectiveValue()`, which can cause runtime errors.
- Setting `relative_gap_limit` to a non-zero value when an exact optimum is required.
- Overlooking the need for manual solution verification, which can hide modeling mistakes.

# Workflow 2 (MIP via Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo as a modeling language to formulate the problem as a Mixed-Integer Program (MIP), which can be solved by various backends like HiGHS, Gurobi, or CBC. It emphasizes model clarity, separation of data and logic, and solver-agnostic formulation.

### Step 1 - Declare Sets and Parameters
- Define a Pyomo `Set` for the selectable items.
- Define a Pyomo `Param` (or a simple dictionary) for the cost of each item.

### Step 2 - Create Binary Variables
- Declare a Pyomo `Var` indexed by the item set with `domain=pyo.Binary`.

### Step 3 - Build Objective Function
- Define a `pyo.Objective` with `sense=pyo.minimize` and expression `sum(cost[i] * x[i] for i in items)`.

### Step 4 - Add Unique Constraint Types
- For each unique coverage requirement (distinct subset and RHS), add a single `pyo.Constraint`.
- Avoid adding multiple constraints with identical mathematical forms.

### Formulation Template
```json
{
  "sets": [
    "I: Pyomo Set of selectable items"
  ],
  "parameters": [
    "cost: Pyomo Param or dict mapping i ∈ I to cost"
  ],
  "decision_variables": [
    "x[i] ∈ {0,1}: Pyomo Binary variable"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(x[i] for i in subset_j) >= min_coverage_j: Pyomo Constraint for each unique requirement j"
  ]
}
```

### Common Pitfalls
- Creating a separate Pyomo `Constraint` object for each named instance when they are mathematically identical, leading to unnecessary model bloat.
- Attempting to directly evaluate constraint expressions post-solve, which may cause `AttributeError`; instead, use `pyo.value(x[i])`.
- Confusing Pyomo's `SolverStatus` (solver communication) with `TerminationCondition` (solution quality).

## Solving stage

### Strategy Overview
Solving involves selecting a MIP solver, configuring it for exact solutions, executing the solve with proper status handling, and loading/verifying the solution only if the solve was successful.

### Step 1 - Instantiate and Configure Solver
- Use `pyo.SolverFactory('solver_name')` (e.g., 'highs', 'gurobi').
- Set solver-specific options: `time_limit`, `mip_rel_gap=0.0` for exact optimum, and `threads` for parallelism.

### Step 2 - Solve with `load_solutions=False`
- Call `solver.solve(model, tee=False, load_solutions=False)` to avoid loading an invalid solution if the solve fails.
- Capture the results object.

### Step 3 - Check Status and Load Solution
- Verify `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.
- Only then call `model.solutions.load_from(results)`.

### Step 4 - Extract Results and Verify
- Extract variable values using `pyo.value(model.x[i])`.
- Compute the objective value via `pyo.value(model.obj)`.
- Manually compute the left-hand side of all constraints with the extracted values to ensure satisfaction.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.cost = pyo.Param(model.I, initialize=cost_dict)
model.x = pyo.Var(model.I, domain=pyo.Binary)
model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)
# ... add unique constraints

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = —0.0
results = solver.solve(model, tee=False, load_solutions=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
    model.solutions.load_from(results)
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = float(pyo.value(model.obj))
    # ... verify constraints
else:
    print("Solve failed or was infeasible.")
    # ... debug infeasibility
```

### Common Pitfalls
- Loading solutions (`load_solutions=True`) without checking termination condition, potentially loading an invalid or suboptimal solution.
- Using an invalid value for solver options (e.g., `threads=-1`).
- Forgetting to convert `pyo.value` outputs to native Python types (int/float) for further processing.
