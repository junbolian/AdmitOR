---
name: AssignmentProblemWithCardinalityAndExclusion
description: |
  Model and solve binary assignment problems with cardinality constraints, pairwise exclusions, and linear cost minimization using MIP solvers.
---

# Workflow 1 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Formulate the problem as a Constraint Programming (CP) model using OR-Tools' CP-SAT solver, which is efficient for combinatorial problems with binary variables and linear constraints.

### Step 1 - Define Binary Assignment Variables
- Create a binary decision variable `x[i, j]` for each potential assignment from set `I` to set `J`.
- Use `model.NewBoolVar(f"x_{i}_{j}")` to instantiate each variable.

### Step 2 - Enforce Cardinality Constraints
- For each element `i` in set `I`, add a constraint `sum(x[i, j] for j in J) <= 1` to enforce at most one assignment per `i`.
- For each element `j` in set `J`, add a constraint `sum(x[i, j] for i in I) <= 1` to enforce at most one assignment per `j`.
- Add a global constraint `sum(x[i, j] for i in I for j in J) == K` to enforce exactly `K` total assignments.

### Step 3 - Add Pairwise Exclusion Constraints
- For each pairwise exclusion rule `(i1, j1, i2, j2, max_sum)`, add a linear constraint `x[i1, j1] + x[i2, j2] <= max_sum`.

### Step 4 - Define Linear Cost Objective
- Define a cost parameter `cost[i, j]` for each potential assignment.
- Set the objective to minimize `sum(cost[i, j] * x[i, j] for i in I for j in J)`.

### Formulation Template
```json
{
  "sets": [
    "I = [...]",
    "J = [...]"
  ],
  "parameters": [
    "K = <integer>",
    "cost = {(i, j): <float> for i in I for j in J}",
    "pairwise_exclusions = [(i1, j1, i2, j2, max_sum), ...]"
  ],
  "decision_variables": [
    "x[i, j] ∈ {0, 1} for i in I, j in J"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j])"
  },
  "constraints": [
    "sum(x[i, j] for j in J) <= 1 for each i in I",
    "sum(x[i, j] for i in I) <= 1 for each j in J",
    "sum(x[i, j] for all i, j) == K",
    "x[i1, j1] + x[i2, j2] <= max_sum for each (i1, j1, i2, j2, max_sum) in pairwise_exclusions"
  ]
}
```

### Common Pitfalls
- Forgetting to define the global assignment count constraint `K`, leading to trivial zero-assignment solutions.
- Incorrectly indexing the cost dictionary or pairwise exclusion list, causing KeyErrors.
- Setting `max_sum` values greater than 2 in pairwise constraints, which is redundant for binary variables but should be included for model completeness.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with appropriate parameters for performance and reproducibility, then extract and validate the solution.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.parameters.max_time_in_seconds = <time_limit>`.
- Enable parallel search: `solver.parameters.num_search_workers = <num_workers>`.
- Set a random seed for reproducibility: `solver.parameters.random_seed = <seed>`.

### Step 2 - Solve and Check Status
- Invoke the solver: `status = solver.Solve(model)`.
- Check for optimal or feasible status: `if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):`.

### Step 3 - Extract and Validate Solution
- Iterate over all variables `x[i, j]` and collect assignments where `solver.Value(x[i, j]) == 1`.
- Calculate the total cost from the extracted assignments and verify it matches the solver's objective value.
- Programmatically verify all cardinality and pairwise exclusion constraints are satisfied by the extracted assignments.

### Step 4 - Handle Incomplete Data Scenarios
- If cost data is incomplete, run multiple scenarios (e.g., using interpolated costs, exact costs with penalties, min/max bounds) and compare solutions for robustness.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... (create variables, add constraints, set objective)

# Solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters as described
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = []
    total_cost = 0
    for i in I:
        for j in J:
            if solver.Value(x[i, j]) == 1:
                assignments.append((i, j))
                total_cost += cost[i, j]
    print(f"RESULT:{total_cost}")
    # Optional: Print assignments for debugging
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing good solutions when time limit is reached.
- Extracting assignments incorrectly by comparing `solver.Value(x[i, j]) > 0.5` instead of `== 1` for boolean variables.
- Omitting post-solution validation, which can mask modeling errors.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Programming (MIP) model using Pyomo's abstract or concrete modeling, targeting solvers like Gurobi or SCIP.

### Step 1 - Define Sets and Parameters
- Declare sets `model.I` and `model.J` for the assignment dimensions.
- Define parameter `model.cost` as a dictionary mapping `(i, j)` to a numeric cost.
- Define parameter `model.K` for the total assignment count and list `model.pairwise_exclusions`.

### Step 2 - Create Binary Variables
- Instantiate binary variables `model.x[i, j]` for all `i` in `I`, `j` in `J` using `pyo.Var(domain=pyo.Binary)`.

### Step 3 - Enforce Assignment Constraints
- Add constraints `sum(model.x[i, j] for j in J) <= 1` for each `i` in `I`.
- Add constraints `sum(model.x[i, j] for i in I) <= 1` for each `j` in `J`.
- Add a global constraint `sum(model.x[i, j] for i in I for j in J) == model.K`.

### Step 4 - Incorporate Pairwise Exclusions
- For each entry in `model.pairwise_exclusions`, add a constraint `model.x[i1, j1] + model.x[i2, j2] <= max_sum`.

### Step 5 - Define Objective Function
- Set the objective to minimize `sum(model.cost[i, j] * model.x[i, j] for i in I for j in J)`.

### Formulation Template
```json
{
  "sets": [
    "I = [...]",
    "J = [...]"
  ],
  "parameters": [
    "K = <integer>",
    "cost = {(i, j): <float> for i in I for j in J}",
    "pairwise_exclusions = [(i1, j1, i2, j2, max_sum), ...]"
  ],
  "decision_variables": [
    "x[i, j] ∈ {0, 1} for i in I, j in J"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j])"
  },
  "constraints": [
    "sum(x[i, j] for j in J) <= 1 for each i in I",
    "sum(x[i, j] for i in I) <= 1 for each j in J",
    "sum(x[i, j] for all i, j) == K",
    "x[i1, j1] + x[i2, j2] <= max_sum for each (i1, j1, i2, j2, max_sum) in pairwise_exclusions"
  ]
}
```

### Common Pitfalls
- Using Pyomo's `Set` initialization incorrectly, leading to unindexed variables or parameters.
- Adding pairwise exclusion constraints with an incorrect `max_sum` value (e.g., 0) that makes the model infeasible.
- Not pre-processing the cost dictionary to ensure all `(i, j)` pairs have a defined numeric value, causing solver errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MIP solver, check termination conditions, and extract the solution with robust error handling.

### Step 1 - Instantiate and Configure Solver
- Create a solver object: `solver = pyo.SolverFactory('<solver_name>')` (e.g., 'gurobi', 'scip').
- Set solver parameters: `solver.options['TimeLimit'] = <time_limit>`, `solver.options['MIPGap'] = 0.0`, `solver.options['Threads'] = <threads>`, `solver.options['Seed'] = <seed>`.

### Step 2 - Solve and Check Status
- Invoke the solver: `results = solver.solve(model, tee=False)`.
- Check solver status: `if results.solver.status == pyo.SolverStatus.ok:`.
- Check termination condition: `if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):`.

### Step 3 - Extract Solution and Validate
- Iterate over `model.x` and collect assignments where `pyo.value(model.x[i, j]) > 0.5`.
- Calculate the total cost from the extracted assignments.
- Programmatically verify all constraints are satisfied by the solution.

### Step 4 - Output Standardized Results
- For a successful solve, print the objective value in a standard format: `print(f"RESULT:{pyo.value(model.obj)})`.
- For failures, output an error payload: `print(f"RESULT_JSON:{{'error': '<details>'}}")`.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, parameters, variables, constraints, objective)

# Solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'scip'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = -1.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    print(f"RESULT:{total_cost}")
    # Optional: Extract and print assignments
else:
    print(f"RESULT_JSON:{{'error': 'Solver failed', 'status': {results.solver.status}, 'termination': {results.solver.termination_condition}}}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially interpreting an infeasible or error state as a success.
- Extracting variable values using `model.x[i, j].value` without first checking if a solution is available, leading to `None` errors.
- Using a `TimeLimit` value of `-1` or other invalid parameters, causing the solver to fail silently or behave unexpectedly.
