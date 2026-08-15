---
name: Binary Selection with Single Knapsack Constraint
description: |
  Model and solve binary selection problems with a single capacity constraint using either specialized knapsack solvers or general-purpose MIP frameworks.
---

# Workflow 1 (Specialized Knapsack Solver)

## Modeling stage

### Strategy Overview
This workflow uses a dedicated knapsack algorithm, which is highly efficient for the canonical 0-1 knapsack problem. It directly maps the problem to a solver API expecting profit and weight arrays.

### Step 1 - Map Problem Elements
- Identify each selectable item and its associated value (profit) and resource consumption (weight).
- Organize these into parallel arrays `profits` and `weights`, ensuring they share the same indexing order.
- Define the total available resource as the `capacity`.

### Step 2 - Validate Data Structure
- Confirm the lengths of `profits` and `weights` arrays are identical.
- Ensure all values are non-negative integers or floats, as required by the target solver.
- Verify the `capacity` is a single numerical value.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": ["profits[items]", "weights[items]", "capacity"],
  "decision_variables": ["x[items] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(profits[i] * x[i] for i in items)"
  },
  "constraints": [
    "sum(weights[i] * x[i] for i in items) <= capacity"
  ]
}
```

### Common Pitfalls
- Providing a single-dimensional list for `weights` when the solver API requires a list of lists (e.g., `[[w1, w2, ...]]`).
- Mismatching indices between profit and weight arrays, leading to incorrect solutions.
- Not checking solver availability or compatibility for the problem size (e.g., very large profits/weights).

## Solving stage

### Strategy Overview
Utilize a specialized knapsack solver (e.g., OR-Tools' `KnapsackSolver`) for optimal performance. The process involves initializing the solver with data, executing it, and extracting the binary selection pattern.

### Step 1 - Initialize and Configure Solver
- Instantiate the solver object (e.g., `KnapsackSolver`).
- Select the appropriate algorithm type (e.g., `KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER`).
- Set optional parameters like time limit or number of threads if supported.

### Step 2 - Solve and Check Status
- Call the solver's `init` method with `profits`, `weights` (as list of lists), and `[capacity]`.
- Execute the `solve()` method.
- Immediately check the solver's status or whether a solution was found before proceeding.

### Step 3 - Extract and Verify Solution
- For each item index `i`, use `solver.best_solution_contains(i)` or equivalent to get the binary selection.
- Compute the total achieved value and total used resource by summing over selected items.
- Validate feasibility by confirming total used resource <= capacity.

### Code Usage
```python
# Example using a generic knapsack solver API
solver = KnapsackSolver(KnapsackSolver.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER)
# weights must be a list of lists for a single dimension
solver.init(profits, [weights], [capacity])
solver.solve()

selected_items = []
total_value = 0
total_weight = —0
for i in range(len(profits)):
    if solver.best_solution_contains(i):
        selected_items.append(i)
        total_value += profits[i]
        total_weight += weights[i]

# Verify feasibility
if total_weight > capacity:
    raise Exception("Solution violates capacity constraint")
print(f"Objective: {total_value}, Selected: {selected_items}")
```

### Common Pitfalls
- Assuming `solve()` returns a solution object; often the result is stored internally.
- Forgetting to wrap `weights` in an extra list for single-constraint problems.
- Not handling cases where the solver might return no feasible solution (status check is critical).

# Workflow 2 (General-Purpose MIP Solver)

## Modeling stage

### Strategy Overview
This workflow employs a general-purpose Mixed-Integer Programming (MIP) solver via a modeling library (e.g., Pyomo, PuLP). It is flexible and allows for easy future extension with additional constraints or objective terms.

### Step 1 - Define Model Structure
- Create a model object (e.g., `ConcreteModel`, `LpProblem`).
- Define an index set for all selectable items.
- Add parameters: value and cost for each item, and the budget capacity.

### Step 2 - Create Decision Variables and Objective
- Create one binary decision variable for each item in the set.
- Define the objective function as the sum of (value * selection variable) and set its sense to maximize.

### Step 3 - Add Capacity Constraint
- Add a single linear constraint: the sum of (cost * selection variable) for all items must be less than or equal to the budget.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": ["value[items]", "cost[items]", "budget"],
  "decision_variables": ["select[items] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(value[i] * select[i] for i in items)"
  },
  "constraints": [
    "sum(cost[i] * select[i] for i in items) <= budget"
  ]
}
```

### Common Pitfalls
- Using incorrect variable domain (e.g., `Integer` instead of `Binary`).
- Mismatching the index used in variable creation and parameter dictionaries.
- Forgetting to set the objective sense, leading to a default minimization.

## Solving stage

### Strategy Overview
Solve the formulated MIP model using an appropriate backend solver (e.g., HiGHS, CBC, SCIP). The focus is on robustly handling solver execution, status checking, and solution loading.

### Step 1 - Configure and Execute Solver
- Select a solver backend compatible with the modeling library.
- Set solver options such as time limit (`time_limit`), optimality gap (`mip_rel_gap`), and number of threads (`threads`).
- Call the `solve()` method on the model, ensuring solution loading is controlled (e.g., `load_solutions=False`).

### Step 2 - Validate Solver Status
- Retrieve the solver status and termination condition.
- Proceed only if status is `ok` and termination is `optimal` or `feasible`. Handle other cases (infeasible, unbounded, error) appropriately.

### Step 3 - Load and Extract Solution
- If solutions are not loaded automatically, load them manually from the results object.
- Iterate through the decision variables to determine which are selected (value > 0.5).
- Compute derived metrics: total value, total cost, and remaining budget.

### Code Usage
```python
# Example using a generic MIP modeling library
solver = SolverFactory('appsi_highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, load_solutions=False)

if results.solver.status == SolverStatus.ok and results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]:
    model.solutions.load_from(results)
    selected_items = []
    total_value = 0
    total_cost = 0
    for i in model.items:
        if model.select[i].value > 0.5:
            selected_items.append(i)
            total_value += model.value[i]
            total_cost += model.cost[i]
    print(f"Status: Optimal, Objective: {total_value}, Selected: {selected_items}, Cost: {total_cost}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Attempting to access variable values before checking solver status or loading the solution.
- Misinterpreting solver termination conditions (e.g., `maxIterations` vs `optimal`).
- Not setting `load_solutions=False` when the solver interface has issues with automatic loading, leading to attribute errors.
