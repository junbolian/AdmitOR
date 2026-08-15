---
name: Generalized Bin Packing / Facility Location Minimization
description: |
  Model and solve assignment problems with capacity constraints to minimize the number of used facilities, using either a CP-SAT or a MIP (Pyomo) approach.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Constraint Programming (CP) or Boolean Satisfiability (SAT) problem using binary variables, suitable for exact solving via OR-Tools' CP-SAT solver. It emphasizes explicit variable linking and capacity constraints.

### Step 1 - Define Core Sets and Parameters
- Define a set of `items` (or resources) and a set of `bins` (or centers/facilities).
- Define a parameter `weight[i]` for each item `i` and a scalar `capacity` for each bin.
- Determine an upper bound `M` for the number of bins (e.g., `len(items)`).

### Step 2 - Create Binary Decision Variables
- Create binary assignment variable `assign[i][j]` for each item `i` and bin `j`.
- Create binary usage variable `used[j]` for each bin `j`.

### Step 3 - Formulate Constraints
- **Single Assignment**: For each item `i`, `sum(assign[i][j] for j in bins) == 1`.
- **Capacity Limit**: For each bin `j`, `sum(weight[i] * assign[i][j] for i in items) <= capacity`.
- **Usage Linking**: For each item `i` and bin `j`, `used[j] >= assign[i][j]`. This ensures `used[j]` is 1 if any item is assigned to bin `j`.

### Step 4 - Define Objective
- Minimize the total number of used bins: `minimize sum(used[j] for j in bins)`.

### Formulation Template
```json
{
  "sets": [
    "items: list of item identifiers",
    "bins: list of bin identifiers (size M)"
  ],
  "parameters": [
    "weight: dict mapping item -> numeric weight",
    "capacity: numeric capacity per bin"
  ],
  "decision_variables": [
    "assign: dict of (item, bin) -> cp_model.BoolVar",
    "used: dict of bin -> cp_model.BoolVar"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(used[j] for j in bins)"
  },
  "constraints": [
    "single_assignment: for i in items: sum(assign[i][j] for j in bins) == 1",
    "capacity_limit: for j in bins: sum(weight[i] * assign[i][j] for i in items) <= capacity",
    "usage_linking: for i in items, j in bins: used[j] >= assign[i][j]"
  ]
}
```

### Common Pitfalls
- Forgetting to set a sufficient upper bound `M` for the number of bins, which can make the model infeasible if too small.
- Omitting the explicit linking constraint (`used[j] >= assign[i][j]`), which can weaken propagation and slow solving.
- Not verifying that total weight exceeds `(k-1)*capacity` to provide a quick lower bound check for the optimal number of bins `k`.

## Solving stage

### Strategy Overview
Solve the CP-SAT model using Google OR-Tools, configuring for exact solutions with runtime limits and parallel search. Extract and verify the solution.

### Step 1 - Instantiate and Configure Solver
- Create a `cp_model.CpModel()`.
- Add variables and constraints as per the modeling stage.
- Configure the solver with `CpSolver()` and set parameters: `max_time_in_seconds`, `num_search_workers`, `random_seed` for reproducibility, and `relative_gap_limit=0.0` for exact solutions.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status: `OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`. For `INFEASIBLE`, verify input data and model logic.

### Step 3 - Extract and Validate Solution
- If status is `OPTIMAL` or `FEASIBLE`, retrieve the objective value from `solver.ObjectiveValue()`.
- Extract `used[j]` values by checking `solver.Value(used[j]) == 1`.
- For each used bin, list items where `solver.Value(assign[i][j]) == 1`.
- Perform a quick feasibility check: verify no bin's total assigned weight exceeds capacity.

### Step 4 - Output Results
- Return the objective value in a structured format (e.g., `RESULT:{objective_value}`).
- Optionally, print the assignment mapping for verification.

### Code Usage
```python
from ortools.sat.python import cp_model

# 1. Build model from formulation
model = cp_model.CpModel()
# ... define sets, parameters, variables, constraints, objective as per modeling stage

# 2. Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    obj_value = int(solver.ObjectiveValue())
    # Extract used bins and assignments
    used_bins = [j for j in bins if solver.Value(used[j]) == 1]
    assignment = {}
    for j in used_bins:
        assignment[j] = [i for i in items if solver.Value(assign[i][j]) == 1]
    print(f"RESULT:{obj_value}")
    # Optional detailed output
else:
    print("INFEASIBLE or UNKNOWN")
```

### Common Pitfalls
- Not setting `relative_gap_limit=0.0`, which can lead to early termination with a suboptimal solution.
- Misinterpreting `FEASIBLE` status as optimal; always check for `OPTIMAL` if an exact solution is required.
- Forgetting to convert solver values to integers for binary variables, leading to incorrect comparisons.

# Workflow 2 (MIP with Pyomo and HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Program (MIP) using Pyomo, suitable for solvers like HiGHS or CBC. It uses a capacity-linked activation constraint to tighten the formulation and improve LP relaxation.

### Step 1 - Define Sets and Parameters
- Define Pyomo `Set` objects for `items` and `bins`.
- Define a `Param` `weight` indexed by items and a scalar `capacity`.

### Step 2 - Create Binary Variables
- Define `Var` `x[i,j]` within `pyo.Binary` for assignment.
- Define `Var` `y[j]` within `pyo.Binary` for bin activation.

### Step 3 - Formulate Constraints
- **Single Assignment**: For each item `i`, `sum(x[i,j] for j in bins) == 1`.
- **Capacity-Linked Activation**: For each bin `j`, `sum(weight[i] * x[i,j] for i in items) <= capacity * y[j]`. This both enforces capacity and links usage.
- **Explicit Linking (Optional but Recommended)**: For each `i,j`, `x[i,j] <= y[j]`. This strengthens the formulation.

### Step 4 - Define Objective
- Minimize total activated bins: `minimize sum(y[j] for j in bins)`.

### Formulation Template
```json
{
  "sets": [
    "items: pyo.Set()",
    "bins: pyo.Set()"
  ],
  "parameters": [
    "weight: pyo.Param(items, within=pyo.NonNegativeReals)",
    "capacity: pyo.Param(within=pyo.NonNegativeReals)"
  ],
  "decision_variables": [
    "x: pyo.Var(items, bins, within=pyo.Binary)",
    "y: pyo.Var(bins, within=pyo.Binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in bins)"
  },
  "constraints": [
    "single_assignment: for i in items: sum(x[i,j] for j in bins) == 1",
    "capacity_linked: for j in bins: sum(weight[i] * x[i,j] for i in items) <= capacity * y[j]",
    "explicit_link: for i in items, j in bins: x[i,j] <= y[j]"
  ]
}
```

### Common Pitfalls
- Using only the capacity-linked constraint without the explicit link (`x[i,j] <= y[j]`), which can result in a weaker LP relaxation and slower solving.
- Incorrectly indexing parameters or variables, leading to model construction errors.
- Not providing a reasonable upper bound for the `bins` set, which can cause memory issues for large instances.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external MIP solver (HiGHS or CBC), configured for exact solutions with time limits and optimality gaps. Robustly check solver status and extract the solution.

### Step 1 - Build Model and Configure Solver
- Instantiate a `pyo.ConcreteModel()`.
- Add sets, parameters, variables, constraints, and objective as per the modeling stage.
- Use `pyo.SolverFactory('highs')` or `pyo.SolverFactory('cbc')`.
- Set solver options: `time_limit`, `mip_rel_gap=0.0` (for exact), `threads` for parallelism.

### Step 2 - Solve and Check Termination
- Execute `solver.solve(model, tee=False)`.
- Check both `solver.status` (should be `SolverStatus.ok`) and `model.solutions[0].termination_condition` (should be `optimal` or `feasible`).

### Step 3 - Extract and Verify Solution
- If solve was successful, retrieve the objective value from `pyo.value(model.obj)`.
- Extract `y[j]` values by thresholding (`pyo.value(y[j]) > 0.5`).
- For each active bin, find items where `pyo.value(x[i,j]) > 0.5`.
- Manually verify capacity constraints and single assignment for the extracted solution.

### Step 4 - Output and Validate Optimality
- Output the objective value and assignment details.
- Optionally, solve a restricted model with the number of bins fixed to `objective_value - 1` to prove optimality via infeasibility.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build model from formulation
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items_list)
model.bins = pyo.Set(initialize=bins_list)
model.weight = pyo.Param(model.items, initialize=weight_dict)
model.capacity = pyo.Param(initialize=capacity_value)

model.x = pyo.Var(model.items, model.bins, within=pyo.Binary)
model.y = pyo.Var(model.bins, within=pyo.Binary)

def obj_rule(m):
    return pyo.sum(m.y[j] for j in m.bins)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Add constraints (single_assignment, capacity_linked, explicit_link)
# ...

# 2. Solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['time_limit'] = 30.0
solver.options['mip_rel_gap'] = 0.0
solver.options['threads'] = 8

results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    obj_value = pyo.value(model.obj)
    used_bins = [j for j in model.bins if pyo.value(model.y[j]) > 0.5]
    assignment = {j: [i for i in model.items if pyo.value(model.x[i, j]) > 0.5] for j in used_bins}
    print(f"RESULT:{int(obj_value)}")
else:
    print("Solver did not return a feasible solution.")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of incomplete or failed solves.
- Using a non-zero optimality gap (`mip_rel_gap`) when an exact solution is required.
- Forgetting to convert Pyomo variable values to floats or integers before comparison, causing incorrect assignment extraction.
