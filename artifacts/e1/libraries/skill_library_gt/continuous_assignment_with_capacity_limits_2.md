---
name: Continuous Assignment with Capacity Limits
description: |
  Model and solve linear assignment problems with continuous flow variables, supply/demand balance constraints, and per-assignment capacity limits to minimize linear cost.
---

# Workflow 1 (Pyomo with LP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define a pure linear program, suitable for problems where fractional assignments are acceptable. It leverages high-performance LP solvers like HiGHS or CBC.

### Step 1 - Define Sets and Indexed Parameters
- Declare two sets: `I` for sources (e.g., employees) and `J` for destinations (e.g., projects).
- Create indexed parameters for `availability[i]`, `requirement[j]`, `cost[i,j]`, and `capacity[i,j]` to store problem data.

### Step 2 - Create Bounded Decision Variables
- Define continuous, non-negative decision variables `x[i,j]` representing the assigned amount from source `i` to destination `j`.
- Directly incorporate per-assignment capacity limits by setting the variable's upper bound to `capacity[i,j]`.

### Step 3 - Formulate Supply and Demand Balance Constraints
- For each source `i`, add a supply constraint: the sum of all outgoing assignments equals the total availability (`sum(x[i,j] for j in J) == availability[i]`).
- For each destination `j`, add a demand constraint: the sum of all incoming assignments exactly meets the requirement (`sum(x[i,j] for i in I) == requirement[j]`).

### Step 4 - Define Linear Cost Minimization Objective
- Formulate the objective as the sum of assignment amounts multiplied by their unit costs: `min sum(cost[i,j] * x[i,j] for i in I, j in J)`.

### Formulation Template
```json
{
  "sets": ["I (sources)", "J (destinations)"],
  "parameters": ["availability[i]", "requirement[j]", "cost[i,j]", "capacity[i,j]"],
  "decision_variables": ["x[i,j] ∈ ℝ⁺, bounded by [0, capacity[i,j]]"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I, j in J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "supply_balance[i]: sum_{j in J} x[i,j] == availability[i], ∀i ∈ I",
    "demand_satisfaction[j]: sum_{i in I} x[i,j] == requirement[j], ∀j ∈ J"
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand before solving, which can cause infeasibility.
- Hard-coding parameter values within constraint rules instead of using Pyomo `Param` objects, reducing model reusability.
- Using inequality (`<=`) for demand constraints when exact fulfillment is required, leading to incorrect solutions.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured LP solver, with robust checks for solution status and post-solution validation of all constraints and bounds.

### Step 1 - Configure and Execute Solver
- Instantiate a solver factory (e.g., `SolverFactory("highs")`).
- Set practical options like `time_limit` and `threads`.
- Solve the model with `tee=False` for clean output unless debugging.

### Step 2 - Validate Solver Status and Termination Condition
- Check that `solver.status` is `SolverStatus.ok`.
- Verify `termination_condition` is either `TerminationCondition.optimal` or `TerminationCondition.feasible` before proceeding.

### Step 3 - Extract and Verify the Solution
- Load the solution into the model instance.
- Extract the objective value and iterate over variables to collect non-zero assignments (e.g., `value > 1e-6`).
- Programmatically recalculate constraint left-hand sides to verify supply/demand balance and capacity limits are satisfied within a small tolerance.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model building code as per Formulation Template)

solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    # Load solution
    model.solutions.load_from(results)
    objective_value = pyo.value(model.obj)
    # Extract non-zero assignments
    assignments = []
    for i in model.I:
        for j in model.J:
            val = pyo.value(model.x[i,j])
            if val > 1e-6:
                assignments.append(((i,j), val))
    # ... (verification logic)
else:
    print(f"Solver failed: Status={status}, Termination={term}")
```

### Common Pitfalls
- Assuming a solution is valid without checking both `solver.status` and `termination_condition`.
- Not using `model.solutions.load_from(results)` before accessing variable values, leading to `None` or default values.
- Using an absolute tolerance of zero (`==`) for floating-point comparisons in verification, which can fail due to numerical precision.

# Workflow 2 (ORTools GLOP with Direct API)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools linear solver wrapper (GLOP) via a direct, imperative API. It is suited for rapid prototyping and environments where Pyomo is not available, offering explicit control over variable and constraint creation.

### Step 1 - Initialize Solver and Define Data Structures
- Create a solver instance (`pywraplp.Solver.CreateSolver('GLOP')`).
- Store problem parameters (cost, capacity, availability, requirement) in nested lists or dictionaries indexed by `(i, j)`.

### Step 2 - Create Variables with Integrated Bounds
- In a nested loop over all source-destination pairs, create continuous variables `x[i][j]`.
- Set the variable's lower bound to 0 and its upper bound directly to the `capacity[i][j]` value.

### Step 3 - Add Supply and Demand Constraints
- For each source `i`, create a constraint: `sum(x[i][j] for all j) <= availability[i]`.
- For each destination `j`, create a constraint: `sum(x[i][j] for all i) == requirement[j]`.
- Use the solver's `Add()` method with sum expressions built via list comprehension.

### Step 4 - Set Linear Objective
- Initialize the objective function for minimization.
- In a nested loop, call `objective.SetCoefficient(x[i][j], cost[i][j])` for each variable.

### Formulation Template
```json
{
  "sets": ["I (sources)", "J (destinations)"],
  "parameters": ["availability[i]", "requirement[j]", "cost[i,j]", "capacity[i,j]"],
  "decision_variables": ["x[i,j] (solver.NumVar) with bounds [0, capacity[i,j]]"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I, j in J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "supply_limit[i]: sum_{j in J} x[i,j] <= availability[i], ∀i ∈ I",
    "demand_equality[j]: sum_{i in I} x[i,j] == requirement[j], ∀j ∈ J"
  ]
}
```

### Common Pitfalls
- Accidentally using inequality (`<=`) for supply constraints when the problem requires exact utilization (`==`).
- Creating variables without explicitly setting their upper bounds, missing the per-assignment capacity limits.
- Mismatching indices between cost, capacity, and variable matrices, leading to incorrect objective or infeasibility.

## Solving stage

### Strategy Overview
Solve the model using the GLOP solver, extract results, and perform comprehensive verification. The direct API requires manual construction but offers straightforward solution access.

### Step 1 - Invoke Solver and Check Result Status
- Call `solver.Solve()`.
- Check the result status is either `OPTIMAL` or `FEASIBLE` before extracting values.

### Step 2 - Extract Solution and Filter Non-Zero Assignments
- Retrieve the objective value via `solver.Objective().Value()`.
- Iterate over all variables, obtain their solution value with `x[i][j].solution_value()`.
- Collect assignments where the value exceeds a small epsilon (e.g., `1e-6`) to avoid numerical noise.

### Step 3 - Programmatically Verify All Constraints
- Recompute the sum of assignments for each source and compare against `availability[i]` (with tolerance for inequality constraints).
- Recompute the sum for each destination and verify exact equality with `requirement[j]` within tolerance.
- Check that each individual assignment does not exceed its `capacity[i,j]` upper bound.

### Code Usage
```python
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation as per Formulation Template)

status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    assignments = []
    for i in range(num_sources):
        for j in range(num_destinations):
            val = x[i][j].solution_value()
            if val > 1e-6:
                assignments.append(((i, j), val))
    # ... (verification logic)
else:
    print('The problem does not have an optimal solution.')
```

### Common Pitfalls
- Confusing `solver.FEASIBLE` with `solver.OPTIMAL` and not reporting the difference to the user.
- Forgetting that `solution_value()` returns a float; comparing it directly to an integer target without tolerance.
- Not verifying that supply constraints are satisfied as inequalities (`<=`), potentially missing violations if the solver's tolerance is loose.
