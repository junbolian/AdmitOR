---
name: Set Cover with Linear Cost Minimization
description: |
  Model and solve binary set covering problems with linear cost objectives using MILP solvers, ensuring all elements are covered by at least one selected set.
---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' MIP solver interface (`pywraplp`) for a direct, low-level modeling approach. It is suitable for users who prefer a solver-native API with explicit control over variable and constraint creation, and who value the performance of compiled solvers like SCIP or CBC.

### Step 1 - Define Sets and Parameters
- Identify the set of elements to be covered (e.g., `segments`) and the set of covering items (e.g., `strategies`).
- Define a linear cost parameter for each covering item (e.g., `cost[strategy]`).
- Construct a coverage mapping: for each element, list the covering items that can cover it (e.g., `coverage[element] = [list_of_items]`).

### Step 2 - Create Binary Decision Variables
- Instantiate a solver object (e.g., `solver = pywraplp.Solver.CreateSolver("SCIP")`).
- Create a binary decision variable for each covering item (e.g., `x[item] = solver.IntVar(0, 1, f"x_{item}")`).

### Step 3 - Formulate Linear Objective
- Initialize the objective function (e.g., `objective = solver.Objective()`).
- For each covering item, set the coefficient of its variable to its cost (e.g., `objective.SetCoefficient(x[item], cost[item])`).
- Set the objective sense to minimization (e.g., `objective.SetMinimization()`).

### Step 4 - Enforce Coverage Constraints
- For each element in the coverage set, create a linear constraint with a lower bound of 1.
- For each covering item listed for that element, add its binary variable with a coefficient of 1 to the constraint.
- This ensures the sum of selected covering items for each element is at least 1.

### Formulation Template
```json
{
  "sets": [
    "E": "Set of elements to be covered.",
    "I": "Set of items (strategies) that can cover elements."
  ],
  "parameters": [
    "cost_i": "Linear cost of selecting item i ∈ I.",
    "a_ei": "Binary parameter: 1 if item i ∈ I covers element e ∈ E, 0 otherwise."
  ],
  "decision_variables": [
    "x_i": "Binary variable: 1 if item i ∈ I is selected, 0 otherwise."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} cost_i * x_i"
  },
  "constraints": [
    "coverage_e": "sum_{i in I} a_ei * x_i >= 1, for all e in E"
  ]
}
```

### Common Pitfalls
- Forgetting to check if the solver was created successfully, leading to runtime errors.
- Incorrectly populating the coverage mapping, which can result in infeasible models.
- Not setting a time limit for large instances, potentially causing the solve to hang.

## Solving stage

### Strategy Overview
The solving stage focuses on executing the model with the OR-Tools wrapper, configuring solver parameters for performance, rigorously checking the solution status, and extracting and validating the results.

### Step 1 - Configure Solver and Solve
- Set performance parameters such as a time limit (e.g., `solver.SetTimeLimit(time_limit_ms)`) and number of threads.
- Call the solver's `Solve()` method to initiate the optimization.

### Step 2 - Check Solution Status
- Retrieve the solver status (e.g., `status = solver.OPTIMAL`).
- Check if the status indicates optimality or feasibility. Handle infeasible or unbounded statuses with clear error messages.

### Step 3 - Extract and Validate Solution
- If the status is acceptable, extract the objective value (e.g., `objective.Value()`).
- Iterate over the decision variables to collect selected items where `x[item].solution_value() > 0.5`.
- Implement a post-solve verification: for each element, check that at least one selected item appears in its coverage list.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    raise Exception("Solver initialization failed.")
# ... (variable, objective, constraint creation as per modeling stage)

# solve with status / termination checks
solver.SetTimeLimit(30000)  # 30-second limit
result_status = solver.Solve()

if result_status == solver.OPTIMAL or result_status == solver.FEASIBLE:
    print(f"Objective value: {solver.Objective().Value()}")
    selected_items = [i for i in items if x[i].solution_value() > 0.5]
    print(f"Selected items: {selected_items}")
    # Validation loop
    for e in elements:
        if not any(i in selected_items for i in coverage[e]):
            print(f"ERROR: Element {e} is not covered.")
else:
    print("Solver did not find an optimal/feasible solution.")
```

### Common Pitfalls
- Accessing solution values without first confirming the solver status is optimal or feasible.
- Using a loose tolerance (like `> 0.5`) for binary variables, which is generally safe but should be documented.
- Omitting solution validation, which can mask modeling errors in the coverage definition.

# Workflow 2 (PuLP Modeling Library)

## Modeling stage

### Strategy Overview
This workflow employs the PuLP modeling library, which provides a high-level, Pythonic syntax for defining optimization problems. It abstracts solver communication and is ideal for rapid prototyping, readability, and ease of integration with Python data structures.

### Step 1 - Define Problem and Sets
- Create a PuLP minimization problem (e.g., `prob = pulp.LpProblem("SetCover", pulp.LpMinimize)`).
- Define the sets of covering items and elements as Python lists or sets.

### Step 2 - Create Variables and Parameters
- Create a dictionary of binary decision variables indexed by the covering items using `pulp.LpVariable.dicts`.
- Store costs in a dictionary with the same keys as the variables.
- Define the coverage relationship, preferably as a dictionary mapping each element to a list of covering items.

### Step 3 - Formulate Objective and Constraints
- Build the objective by summing `cost[item] * variable[item]` over all items using `pulp.lpSum`.
- For each element, add a constraint that sums the variables of its covering items and sets the sum `>= 1`.

### Formulation Template
```json
{
  "sets": [
    "E": "List of elements to be covered.",
    "I": "List of items (strategies) that can cover elements."
  ],
  "parameters": [
    "cost": "Dictionary: cost[i] for i in I.",
    "covers": "Dictionary: covers[e] = list of items i in I that cover element e."
  ],
  "decision_variables": [
    "x": "Dictionary of pulp.LpVariable objects with cat='Binary'."
  ],
  "objective": {
    "sense": "min",
    "expression": "lpSum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "cover_e": "lpSum(x[i] for i in covers[e]) >= 1, for all e in E"
  ]
}
```

### Common Pitfalls
- Using inconsistent keys between the cost dictionary, variable dictionary, and coverage mapping.
- Not leveraging `pulp.lpSum` for large summations, which is more efficient than Python's built-in `sum`.
- Forgetting to set the `cat='Binary'` argument when creating variables, defaulting to continuous.

## Solving stage

### Strategy Overview
The solving stage uses PuLP's built-in solver manager to call a backend solver (default is CBC). It focuses on clean solver invocation, result extraction, and automated feasibility verification of the coverage constraints.

### Step 1 - Invoke Solver
- Call `prob.solve()` with optional solver arguments (e.g., `prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=30))`).
- PuLP automatically handles the translation to the solver's input format.

### Step 2 - Check Status and Extract Solution
- Check the problem status via `pulp.LpStatus[prob.status]`. Ensure it is 'Optimal' or 'Feasible'.
- Extract the objective value from `prob.objective.value()`.
- Collect selected items by iterating over variables where `pulp.value(var) > 0.5`.

### Step 3 - Verify Solution and Output
- Implement a verification function that checks if every element is covered by at least one selected item.
- Output results in a structured format (e.g., JSON) for potential downstream processing.

### Code Usage
```python
# build model from formulation
import pulp
prob = pulp.LpProblem("SetCover", pulp.LpMinimize)
x = pulp.LpVariable.dicts("x", items, cat='Binary')
prob += pulp.lpSum(cost[i] * x[i] for i in items)
for e in elements:
    prob += pulp.lpSum(x[i] for i in covers[e]) >= 1

# solve with status / termination checks
solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=30)
prob.solve(solver)

status = pulp.LpStatus[prob.status]
if status in ['Optimal', 'Feasible']:
    print(f"Objective: {prob.objective.value()}")
    selected = [i for i in items if pulp.value(x[i]) > 0.5]
    print(f"Selected: {selected}")
    # Validation
    for e in elements:
        if not any(i in selected for i in covers[e]):
            print(f"Validation failed for element {e}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Interpreting the string status incorrectly; 'Optimal' and 'Feasible' are both acceptable for solution extraction.
- Not specifying a solver command, which may lead to unexpected default solver behavior across environments.
- Assuming the model is infeasible if the solver fails, without checking for other errors like missing solver executables.
