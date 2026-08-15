---
name: Bin Packing with Binary Assignment
description: |
  Model and solve bin packing problems using binary assignment and usage variables to minimize the number of bins used, with workflows for both CP-SAT and MIP solvers.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses OR-Tools' CP-SAT solver, which is efficient for binary assignment problems. The model employs binary variables for item-bin assignment and bin usage, with constraints for assignment exclusivity and capacity. Symmetry-breaking constraints are added to reduce the search space.

### Step 1 - Define Variables and Parameters
- Define sets for items `I` and a maximum set of potential bins `J_max`.
- Define parameters: item weights `weight[i]` and bin capacity `capacity`.
- Create binary decision variable `x[i][j]` (1 if item `i` is assigned to bin `j`).
- Create binary decision variable `y[j]` (1 if bin `j` is used).

### Step 2 - Formulate Core Constraints
- **Assignment Constraint**: For each item `i`, enforce `sum(x[i][j] for j in J_max) == 1`.
- **Capacity & Linking Constraint**: For each bin `j`, enforce `sum(weight[i] * x[i][j] for i in I) <= capacity * y[j]`. This also ensures an unused bin (`y[j]=0`) cannot have items.

### Step 3 - Set Objective and Symmetry Breaking
- Set the objective to minimize the total number of used bins: `minimize sum(y[j] for j in J_max)`.
- Add symmetry-breaking constraints, e.g., `y[j] >= y[j+1]` for `j` in `J_max[:-1]`, to order bins and prune equivalent solutions.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "J_max: set of potential bins (size = |I| as upper bound)"
  ],
  "parameters": [
    "weight[i ∈ I]: weight of item i",
    "capacity: capacity of each bin"
  ],
  "decision_variables": [
    "x[i ∈ I, j ∈ J_max] ∈ {0, 1}",
    "y[j ∈ J_max] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in J_max)"
  },
  "constraints": [
    "assignment: for i in I: sum(x[i][j] for j in J_max) == 1",
    "capacity: for j in J_max: sum(weight[i] * x[i][j] for i in I) <= capacity * y[j]",
    "symmetry_break (optional): for j in J_max[:-1]: y[j] >= y[j+1]"
  ]
}
```

### Common Pitfalls
- Not providing a tight upper bound for `J_max` (e.g., using the number of items) can lead to an oversized model.
- Forgetting symmetry-breaking constraints can result in excessive solve times for symmetric problems.
- Misinterpreting the linking constraint; the capacity constraint `sum(weight[i]*x[i][j]) <= capacity * y[j]` is sufficient, separate `x[i][j] <= y[j]` constraints are redundant.

## Solving stage

### Strategy Overview
Solve using OR-Tools' CP-SAT interface. Configure solver parameters for time limits, parallelism, and optimality. After solving, verify solution feasibility and optionally test for optimality by attempting to find a solution with fewer bins.

### Step 1 - Initialize Solver and Configure
- Create a CP-SAT model: `model = cp_model.CpModel()`.
- Set solver parameters: `solver.parameters.max_time_in_seconds`, `solver.parameters.num_search_workers`, `solver.parameters.random_seed`.
- Enforce exact solution by setting `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status: `status in (cp_model.OPTIMAL, cp_model.FEASIBLE)`. Handle `INFEASIBLE` status by verifying model correctness or relaxing bounds.

### Step 3 - Extract and Validate Solution
- Extract used bins where `solver.Value(y[j]) == 1`.
- For each used bin, collect items where `solver.Value(x[i][j]) == 1`.
- Validate that the total weight per bin does not exceed `capacity`.
- Optionally, to confirm optimality, add a constraint `sum(y[j]) <= k-1` (where `k` is the found objective) and re-solve; infeasibility proves optimality.

### Code Usage
```python
from ortools.sat.python import cp_model
import math

# Data placeholders
weights = [...]  # item weights
capacity = ...
items = range(len(weights))
max_bins = len(items)  # upper bound

model = cp_model.CpModel()

# Create variables
x = {}
for i in items:
    for j in range(max_bins):
        x[(i, j)] = model.NewBoolVar(f'x_{i}_{j}')
y = [model.NewBoolVar(f'y_{j}') for j in range(max_bins)]

# Assignment constraints
for i in items:
    model.Add(sum(x[(i, j)] for j in range(max_bins)) == 1)

# Capacity and linking constraints
for j in range(max_bins):
    model.Add(sum(weights[i] * x[(i, j)] for i in items) <= capacity * y[j])

# Symmetry breaking (optional)
for j in range(max_bins - 1):
    model.Add(y[j] >= y[j + 1])

# Objective
model.Minimize(sum(y))

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 8
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

# Check status and extract solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    used_bins = [j for j in range(max_bins) if solver.Value(y[j]) == 1]
    assignments = {}
    for j in used_bins:
        assigned_items = [i for i in items if solver.Value(x[(i, j)]) == 1]
        assignments[j] = assigned_items
    # Validate
    for j, item_list in assignments.items():
        total_weight = sum(weights[i] for i in item_list)
        assert total_weight <= capacity, f"Bin {j} exceeds capacity"
    print(f"Used bins: {len(used_bins)}")
else:
    print("No feasible solution found")
```

### Common Pitfalls
- Not setting `relative_gap_limit = 0.0` may result in the solver returning a non-optimal solution for a minimization problem.
- Loading a solution without checking the solver status first can cause runtime errors.
- Forgetting to scale the `max_time_in_seconds` parameter appropriately for larger instances.

# Workflow 2 (MIP with Pyomo and HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to model the problem as a Mixed-Integer Program (MIP) and solves it with the open-source HiGHS solver. It focuses on a clean algebraic formulation, starting with a lower bound for the number of bins to reduce model size, and includes robust handling of solver statuses.

### Step 1 - Initialize Model with Bounded Bin Set
- Calculate a lower bound for bins: `lb_bins = ceil(total_weight / capacity)`.
- Define the initial bin set `J` with size `lb_bins`. Be prepared to incrementally increase this set if the model is infeasible.
- Define sets for items `I` and parameters `weight[i]`, `capacity`.

### Step 2 - Declare Variables and Objective
- Create binary variable `x[i,j]` for assignment and `y[j]` for bin usage using Pyomo's `Var` object with `domain=pyo.Binary`.
- Set the objective to minimize the sum of `y[j]`.

### Step 3 - Implement Constraints
- **Assignment Constraint**: For each `i` in `I`, `sum(x[i,j] for j in J) == 1`.
- **Capacity Constraint**: For each `j` in `J`, `sum(weight[i] * x[i,j] for i in I) <= capacity * y[j]`. This also handles linking.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "J: set of potential bins (initial size = ceil(total_weight / capacity))"
  ],
  "parameters": [
    "weight[i ∈ I]: weight of item i",
    "capacity: capacity of each bin"
  ],
  "decision_variables": [
    "x[i ∈ I, j ∈ J] ∈ {0, 1}",
    "y[j ∈ J] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in J)"
  },
  "constraints": [
    "assignment: for i in I: sum(x[i,j] for j in J) == 1",
    "capacity: for j in J: sum(weight[i] * x[i,j] for i in I) <= capacity * y[j]"
  ]
}
```

### Common Pitfalls
- Starting with too few bins (`J`) can lead to infeasibility; implement a loop to incrementally add bins.
- Using `pyo.value()` on variables before loading a solution raises an error.
- Not setting the MIP relative gap to zero (`mip_rel_gap=0.0`) may yield suboptimal solutions.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via `SolverFactory`. Configure for exact solutions and parallel processing. Implement careful status checking and solution loading to handle infeasibility gracefully. Validate the solution against theoretical bounds.

### Step 1 - Configure and Run Solver
- Instantiate solver: `solver = pyo.SolverFactory("highs")`.
- Set solver options: `solver.options["mip_rel_gap"] = 0.0` and `solver.options["threads"] = -1` for all cores.
- Solve with `load_solutions=False` to first check termination status.

### Step 2 - Check Termination and Load Solution
- Check `results.solver.termination_condition`. If `optimal` or `feasible`, load the solution into the model using `model.solutions.load_from(results)`.
- If `infeasible`, analyze the cause (e.g., insufficient bins) and potentially re-solve with an expanded bin set.

### Step 3 - Extract and Validate Results
- Extract used bins where `pyo.value(y[j]) > 0.5`.
- For each used bin, collect items where `pyo.value(x[i,j]) > 0.5`.
- Validate bin weights against capacity.
- Compare the optimal number of bins to the lower bound `ceil(total_weight/capacity)` to understand packing efficiency.

### Code Usage
```python
import pyomo.environ as pyo
import math

# Data placeholders
weights = [...]  # item weights
capacity = ...
total_weight = sum(weights)
items = range(len(weights))
initial_bin_count = math.ceil(total_weight / capacity)  # lower bound
bins = range(initial_bin_count)

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=bins)

# Variables
model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)
model.y = pyo.Var(model.J, domain=pyo.Binary)

# Objective
model.obj = pyo.Objective(expr=sum(model.y[j] for j in model.J), sense=pyo.minimize)

# Constraints
def assignment_rule(m, i):
    return sum(m.x[i, j] for j in m.J) == 1
model.assign = pyo.Constraint(model.I, rule=assignment_rule)

def capacity_rule(m, j):
    return sum(weights[i] * m.x[i, j] for i in m.I) <= capacity * m.y[j]
model.capacity = pyo.Constraint(model.J, rule=capacity_rule)

# Solver configuration
solver = pyo.SolverFactory("highs")
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = -1

# Solve with status handling
results = solver.solve(model, tee=False, load_solutions=False)

def status_ok_and_feasible(results):
    return str(results.solver.termination_condition) in ("optimal", "feasible")

if status_ok_and_feasible(results):
    model.solutions.load_from(results)
    # Extract solution
    used_bins = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
    assignments = {}
    for j in used_bins:
        assigned_items = [i for i in model.I if pyo.value(model.x[i, j]) > 0.5]
        assignments[j] = assigned_items
        # Validate
        total_weight_in_bin = sum(weights[i] for i in assigned_items)
        assert total_weight_in_bin <= capacity, f"Bin {j} exceeds capacity"
    print(f"Used bins: {len(used_bins)}")
    print(f"Theoretical lower bound: {initial_bin_count}")
else:
    print(f"Solver terminated: {results.solver.termination_condition}")
    # Potential recovery: increase bin set and re-solve
```

### Common Pitfalls
- Calling `pyo.value()` on a variable before `load_solutions` results in an error.
- Not checking the termination condition may lead to incorrectly assuming optimality.
- Setting `tee=True` in production can clutter logs; use only for debugging.
