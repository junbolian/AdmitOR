---
name: Resource Minimization Assignment
description: |
  Model and solve binary assignment problems with capacity constraints and resource activation costs using CP-SAT or MILP solvers.

---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, designed for combinatorial problems with Boolean logic and linear constraints. It is ideal for problems where the primary decision variables are binary and the constraints include logical implications between assignment and usage.

### Step 1 - Define Core Variables
- Create binary assignment variables `assign[i][j]` for each item `i` and resource `j`.
- Create binary usage variables `used[j]` for each resource `j` to indicate activation.

### Step 2 - Enforce Assignment and Capacity Rules
- Add a constraint for each item `i`: `sum(assign[i][j] for all j) == 1`. This ensures each item is assigned exactly once.
- For each resource `j`, add a knapsack constraint: `sum(weight[i] * assign[i][j] for all i) <= capacity[j]`.

### Step 3 - Link Assignment to Resource Usage
- Add implication constraints: `assign[i][j] <= used[j]` for all `i, j`. This forces a resource to be marked as used if any item is assigned to it.
- Add a reverse implication: `used[j] <= sum(assign[i][j] for all i)` for all `j`. This ensures a resource is only marked used if at least one item is assigned.

### Step 4 - Set Minimization Objective
- Define the objective to minimize the total number of used resources: `minimize sum(used[j] for all j)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of items"},
    {"name": "J", "description": "Set of resources"}
  ],
  "parameters": [
    {"name": "weight_i", "for_set": "I", "description": "Weight/demand of item i"},
    {"name": "capacity_j", "for_set": "J", "description": "Capacity of resource j"}
  ],
  "decision_variables": [
    {"name": "assign_ij", "for_sets": ["I", "J"], "type": "binary", "description": "1 if item i assigned to resource j"},
    {"name": "used_j", "for_set": "J", "type": "binary", "description": "1 if resource j is activated"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(used_j for j in J)"
  },
  "constraints": [
    {"name": "assignment_cover", "expression": "sum(assign_ij for j in J) == 1", "for_set": "I"},
    {"name": "capacity_knapsack", "expression": "sum(weight_i * assign_ij for i in I) <= capacity_j", "for_set": "J"},
    {"name": "linking_implication", "expression": "assign_ij <= used_j", "for_sets": ["I", "J"]},
    {"name": "linking_reverse", "expression": "used_j <= sum(assign_ij for i in I)", "for_set": "J"}
  ]
}
```

### Common Pitfalls
- Forgetting the reverse linking constraint (`used_j <= sum(assign_ij)`), which can lead to `used_j` being 1 with zero assignments.
- Not setting a time limit or optimality gap, causing the solver to run indefinitely on large instances.
- Using integer multiplication for the capacity constraint instead of linear expressions, which CP-SAT handles natively.

## Solving stage

### Strategy Overview
The solving stage involves configuring the CP-SAT solver, executing the model, and rigorously checking the solution status before extracting and validating results. Emphasis is placed on proof of optimality through infeasibility testing.

### Step 1 - Configure Solver Parameters
- Instantiate the `CpSolver` and set key parameters: `max_time_in_seconds` for runtime control, `num_search_workers` for parallelism, and `relative_gap_limit = 0.0` for exact solutions.
- Set a `random_seed` for reproducible results across runs.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)` and capture the status.
- Proceed only if the status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. Handle `cp_model.UNKNOWN` or `cp_model.INFEASIBLE` appropriately with logging.

### Step 3 - Extract and Validate Solution
- For each resource `j`, check if `solver.Value(used_j) == 1` to count used resources.
- For each item `i`, find the resource `j` where `solver.Value(assign_ij) == 1` to build the assignment map.
- Programmatically verify that the extracted assignments satisfy all capacity and coverage constraints as a sanity check.

### Step 4 - Prove Optimality (Optional)
- If an optimal solution with `k` used resources is found, add a constraint `sum(used_j for all j) <= k-1` and re-solve.
- If the model becomes infeasible, it proves `k` is the true minimum.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... (create variables and constraints as per Modeling Stage)

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Objective value: {solver.ObjectiveValue()}")
    # Extract solution
    assignment = {}
    for i in I:
        for j in J:
            if solver.Value(assign[i, j]) > 0.5:
                assignment[i] = j
    used_resources = [j for j in J if solver.Value(used[j]) > 0.5]
    # Validate
    # ... (check capacity and coverage)
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Misinterpreting `cp_model.FEASIBLE` as optimal; always check the status explicitly.
- Not using a threshold (e.g., `> 0.5`) when reading binary variable values from the solver, which returns floating-point numbers.
- Omitting solution validation, which can mask modeling errors if the solver returns an incorrect feasible solution.

# Workflow 2 (MILP with Pyomo and CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to build a Mixed-Integer Linear Program (MILP). It is solved with the CBC solver, suitable for traditional linear formulations with binary variables and knapsack constraints. This approach separates model construction from solver execution.

### Step 1 - Structure Model with Sets and Variables
- Define Pyomo `Set` objects for items `I` and resources `J`.
- Declare binary decision variables: `model.x[i,j]` for assignment and `model.y[j]` for resource usage.

### Step 2 - Implement Constraints Algebraically
- Add assignment cover constraint: `sum(model.x[i,j] for j in J) == 1` for each `i` in `I`.
- Add capacity constraint: `sum(weight[i] * model.x[i,j] for i in I) <= capacity[j]` for each `j` in `J`.
- Add linking constraints: `model.x[i,j] <= model.y[j]` for all `i,j` and `model.y[j] <= sum(model.x[i,j] for i in I)` for all `j`.

### Step 3 - Define Linear Objective
- Set the objective to minimize total resource usage: `minimize sum(model.y[j] for j in J)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of items"},
    {"name": "J", "description": "Set of resources"}
  ],
  "parameters": [
    {"name": "weight_i", "for_set": "I", "description": "Weight/demand of item i"},
    {"name": "capacity_j", "for_set": "J", "description": "Capacity of resource j"}
  ],
  "decision_variables": [
    {"name": "x_ij", "for_sets": ["I", "J"], "type": "binary", "description": "1 if item i assigned to resource j"},
    {"name": "y_j", "for_set": "J", "type": "binary", "description": "1 if resource j is activated"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y_j for j in J)"
  },
  "constraints": [
    {"name": "assignment_cover", "expression": "sum(x_ij for j in J) == 1", "for_set": "I"},
    {"name": "capacity_knapsack", "expression": "sum(weight_i * x_ij for i in I) <= capacity_j", "for_set": "J"},
    {"name": "linking_implication", "expression": "x_ij <= y_j", "for_sets": ["I", "J"]},
    {"name": "linking_reverse", "expression": "y_j <= sum(x_ij for i in I)", "for_set": "J"}
  ]
}
```

### Common Pitfalls
- Using Pyomo's `Constraint` rule incorrectly by not passing the model instance (`m`) as the first argument.
- Defining parameters as Python variables outside the Pyomo model, which can cause issues during expression construction.
- Neglecting to set the objective sense (`minimize` or `maximize`), defaulting to minimization but risking confusion.

## Solving stage

### Strategy Overview
The solving stage focuses on interfacing Pyomo with the CBC solver via a standardized API. It involves configuring solver options, executing the solve, and meticulously checking termination conditions before extracting results.

### Step 1 - Configure Solver and Options
- Instantiate the solver using `SolverFactory('cbc')`.
- Set critical options: `seconds` for time limit, `ratio` for optimality gap (use `0.0` for exact), and `threads` for parallel processing.

### Step 2 - Execute Solve and Inspect Results
- Call `solver.solve(model, tee=False)` to run without verbose output. Capture the results object.
- Check both `results.solver.status` (must be `ok`) and `results.solver.termination_condition` (should be `optimal` or `feasible`).

### Step 3 - Extract and Post-Process Solution
- Access the objective value via `pyo.value(model.obj)`.
- Iterate over variables `model.x` and `model.y`, using `pyo.value(var) > 0.5` to determine their binary state.
- Build data structures (e.g., lists, dictionaries) representing the assignment and used resources for downstream use.

### Step 4 - Validate Against Model Bounds
- Compute a simple lower bound (e.g., `ceil(total_weight / max_capacity)`) and compare it to the objective value to spot potential suboptimality.
- Programmatically re-evaluate all constraints with the extracted solution to ensure feasibility.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
def build_model():
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=range(num_items))
    model.J = pyo.Set(initialize=range(num_resources))
    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)
    model.y = pyo.Var(model.J, domain=pyo.Binary)
    # ... (add constraints and objective as per Modeling Stage)
    return model

model = build_model()

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = -1.0  # Use 0.0 for optimality gap, -1.0 for default
solver.options['threads'] = 4

results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    print(f"Objective: {pyo.value(model.obj)}")
    # Extract solution
    assignment = [(i, j) for i in model.I for j in model.J if pyo.value(model.x[i, j]) > 0.5]
    used_resources = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
else:
    print("Solve failed or did not converge.")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (found optimal solution); both checks are necessary.
- Using `pyo.value()` on a variable that was not part of the solved model instance.
- Not setting an appropriate `ratio` (optimality gap), leading CBC to stop at a suboptimal solution.
