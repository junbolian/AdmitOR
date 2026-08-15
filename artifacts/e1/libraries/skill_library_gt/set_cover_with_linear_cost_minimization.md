---
name: Set Cover with Linear Cost Minimization
description: |
  Model and solve binary selection problems with coverage requirements and linear costs using MIP solvers, with robust verification and cross-validation.
---

# Workflow 1 (OR-Tools SCIP MIP)

## Modeling stage

### Strategy Overview
This workflow models the set cover problem using the OR-Tools linear solver wrapper, defining binary variables for each set and coverage constraints for each element. It is suited for direct solver interaction and performance tuning.

### Step 1 - Define Data Structures
- Map the coverage relationship from each element to the list of sets that cover it, using a dictionary for efficient access.
- Store the linear cost associated with selecting each set in a list or dictionary.

### Step 2 - Create Binary Variables
- For each set `j`, create a binary decision variable `x_j ∈ {0,1}` using `solver.IntVar(0, 1, name)`.
- Use descriptive naming (e.g., `x_{j}`) for traceability.

### Step 3 - Formulate Linear Objective
- Define the objective as minimizing the sum of costs of selected sets: `min Σ cost_j * x_j`.
- Set the objective sense to minimization using the solver's API.

### Step 4 - Enforce Coverage Constraints
- For each element `i`, create a constraint ensuring at least one covering set is selected: `Σ x_j ≥ 1` for all `j` covering `i`.
- Use the pre-mapped coverage dictionary to add coefficients efficiently.

### Formulation Template
```json
{
  "sets": [
    "S = {set1, set2, ..., set_m}",
    "E = {element1, element2, ..., element_n}"
  ],
  "parameters": [
    "cost_j: cost of selecting set j, for j in S",
    "coverage_i: list of sets j that cover element i, for i in E"
  ],
  "decision_variables": [
    "x_j ∈ {0,1} for j in S"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_j * x_j for j in S)"
  },
  "constraints": [
    "sum(x_j for j in coverage_i) >= 1, for each i in E"
  ]
}
```

### Common Pitfalls
- Forgetting to map coverage both ways (element-to-sets) can lead to incorrect constraint building.
- Using floating-point costs without proper scaling can cause numerical issues for the solver.
- Not verifying that every element has at least one covering set in the input data, which makes the problem infeasible.

## Solving stage

### Strategy Overview
Solve the MIP model using the SCIP solver via OR-Tools, configure performance settings, and implement rigorous solution verification and optimality checks.

### Step 1 - Initialize Solver and Set Parameters
- Create a SCIP solver instance: `pywraplp.Solver.CreateSolver("SCIP")`.
- Set practical limits: time limit (e.g., `SetTimeLimit(30000)`), optimality gap, and number of threads (`SetNumThreads(4)`).

### Step 2 - Solve and Check Status
- Execute `solver.Solve()` and capture the result status.
- Check for optimality: `status == pywraplp.Solver.OPTIMAL`. Handle feasible and infeasible statuses appropriately.

### Step 3 - Extract and Validate Solution
- For each binary variable, retrieve its solution value and apply a threshold (e.g., `> 0.5`) to determine selection.
- Verify coverage: for each element, confirm at least one selected set covers it. Log any violations.
- For small instances, optionally cross-validate by exhaustive enumeration to confirm optimality.

### Step 4 - Report Results
- Output the total cost, list of selected sets, and verification status.
- Include solver statistics like solve time and objective bound if available.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Create variables
x = {j: solver.IntVar(0, 1, f"x_{j}") for j in sets}

# Set objective
objective = solver.Objective()
for j in sets:
    objective.SetCoefficient(x[j], cost[j])
objective.SetMinimization()

# Add coverage constraints
for i in elements:
    constraint = solver.Constraint(1, solver.infinity(), f"cover_{i}")
    for j in coverage[i]:
        constraint.SetCoefficient(x[j], 1)

# solve with status / termination checks
status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL:
    selected = [j for j in sets if x[j].solution_value() > 0.5]
    total_cost = objective.Value()
    # Verification loop
    for i in elements:
        if not any(x[j].solution_value() > 0.5 for j in coverage[i]):
            print(f"Warning: Element {i} not covered.")
    print(f"Optimal cost: {total_cost}, Selected sets: {selected}")
elif status == pywraplp.Solver.FEASIBLE:
    print("Feasible solution found, not proven optimal.")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Assuming binary variables are exactly 0 or 1; always use a tolerance (e.g., `> 0.5`) for comparison.
- Omitting solution verification, which may miss solver errors or modeling mistakes.

# Workflow 2 (PuLP with CBC Backend)

## Modeling stage

### Strategy Overview
This workflow uses the PuLP modeling library to declaratively define the set cover model, leveraging its clean syntax and reliable CBC solver backend. It emphasizes separation of data and model for clarity.

### Step 1 - Structure Problem Data
- Define the list of sets and elements as Python sets or lists.
- Store costs in a dictionary keyed by set identifier.
- Represent coverage as a dictionary mapping each element to a list of covering sets.

### Step 2 - Declare Binary Variables
- Use `pulp.LpVariable.dicts` to create a dictionary of binary variables for each set, e.g., `x = pulp.LpVariable.dicts('x', sets, cat='Binary')`.

### Step 3 - Define LP Problem and Objective
- Instantiate a `pulp.LpProblem` with a descriptive name and sense (`pulp.LpMinimize`).
- Set the objective as the sum of costs multiplied by the corresponding variables.

### Step 4 - Add Coverage Constraints Declaratively
- For each element, add a constraint using `prob += pulp.lpSum([x[s] for s in coverage[element]]) >= 1`.
- This directly mirrors the mathematical formulation.

### Formulation Template
```json
{
  "sets": [
    "S = {set1, set2, ..., set_m}",
    "E = {element1, element2, ..., element_n}"
  ],
  "parameters": [
    "cost_j: cost of selecting set j, for j in S",
    "coverage_i: list of sets j that cover element i, for i in E"
  ],
  "decision_variables": [
    "x_j ∈ {0,1} for j in S"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_j * x_j for j in S)"
  },
  "constraints": [
    "sum(x_j for j in coverage_i) >= 1, for each i in E"
  ]
}
```

### Common Pitfalls
- Using list comprehensions that inadvertently reference undefined variables due to scope issues.
- Not ensuring the coverage dictionary is complete for all elements, leading to KeyError during constraint building.
- Confusing PuLP's `lpSum` with Python's built-in `sum`, which can cause performance and syntax problems.

## Solving stage

### Strategy Overview
Solve the model using the default CBC solver integrated with PuLP, implement error handling for solution loading, and perform post-solution verification and minimality tests.

### Step 1 - Solve with Configured Solver
- Call `prob.solve(pulp.PULP_CBC_CMD(timeLimit=30, gapRel=0.0, threads=4))` to execute with performance settings.
- The `PULP_CBC_CMD` interface allows passing solver-specific arguments.

### Step 2 - Check Solution Status and Termination
- Check `pulp.LpStatus[prob.status]` for 'Optimal', 'Feasible', or 'Infeasible'.
- For optimal status, proceed to extract values; for others, handle appropriately (e.g., log infeasibility).

### Step 3 - Extract and Process Solution
- Use `pulp.value(var)` to get the value of each binary variable, comparing to a tolerance (e.g., `> 0.5`) to determine selection.
- Store selected sets and compute total cost from the objective or by summation.

### Step 4 - Verify and Test Solution
- Validate coverage: for each element, check if any covering set is selected.
- Optionally, test minimality by attempting to remove each selected set and checking if coverage breaks.
- Output results in a structured format (e.g., JSON) for downstream use.

### Code Usage
```python
# build model from formulation
import pulp

prob = pulp.LpProblem("SetCover", pulp.LpMinimize)
x = pulp.LpVariable.dicts('x', sets, cat='Binary')

# Objective
prob += pulp.lpSum([cost[j] * x[j] for j in sets])

# Coverage constraints
for i in elements:
    prob += pulp.lpSum([x[s] for s in coverage[i]]) >= 1, f"cover_{i}"

# solve with status / termination checks
prob.solve(pulp.PULP_CBC_CMD(timeLimit=30, gapRel=0.0, threads=4))

status = pulp.LpStatus[prob.status]
if status == 'Optimal':
    selected = [j for j in sets if pulp.value(x[j]) > 0.5]
    total_cost = pulp.value(prob.objective)
    # Verification
    for i in elements:
        if not any(pulp.value(x[s]) > 0.5 for s in coverage[i]):
            print(f"Coverage violation for element {i}")
    # Optional minimality test
    for j in selected:
        temp_selected = [s for s in selected if s != j]
        if all(any(s in coverage[i] for s in temp_selected) for i in elements):
            print(f"Set {j} is redundant.")
    print(f"Solution verified. Cost: {total_cost}")
else:
    print(f"Solver status: {status}")
```

### Common Pitfalls
- Assuming the solver always returns an optimal solution without checking the status.
- Not using a tolerance when reading binary variable values, leading to incorrect selection due to numerical noise.
- Forgetting to pass solver options (like time limit) when calling `solve`, which may cause long runtimes for large instances.
