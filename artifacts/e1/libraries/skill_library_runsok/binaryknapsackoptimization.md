---
name: BinaryKnapsackOptimization
description: |
  Model and solve 0-1 knapsack problems with binary selection variables, a single capacity constraint, and a value-maximization objective using both dedicated algorithms and general-purpose MIP solvers.
---

# Workflow 1 (Dedicated Knapsack Algorithm)

## Modeling stage

### Strategy Overview
This workflow uses a specialized knapsack algorithm, which is efficient for pure 0-1 selection problems with a single resource constraint. The formulation is a direct mapping of the canonical knapsack structure.

### Step 1 - Define Item Data
- Create parallel arrays for item values and resource weights, ensuring consistent indexing.
- Define a scalar capacity parameter representing the total resource limit.

### Step 2 - Recognize the Algorithmic Pattern
- Identify the problem as a 0-1 knapsack: each item is either fully included or excluded.
- Confirm the objective is to maximize total value and the constraint is a single linear sum of weights.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": ["values[items]", "weights[items]", "capacity"],
  "decision_variables": ["x[items] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(values[i] * x[i] for i in items)"
  },
  "constraints": [
    "sum(weights[i] * x[i] for i in items) <= capacity"
  ]
}
```

### Common Pitfalls
- Using a general-purpose MIP solver when a dedicated, more efficient algorithm exists.
- Mismatching indices between value and weight arrays, leading to incorrect solutions.
- Forgetting to wrap weight arrays in an extra list dimension as required by some solver APIs.

## Solving stage

### Strategy Overview
Solve using a dedicated knapsack solver (e.g., OR-Tools KnapsackSolver) which implements optimized branch-and-bound. This approach is typically faster for standard knapsack problems.

### Step 1 - Initialize Specialized Solver
- Instantiate the solver with the appropriate algorithm type (e.g., `KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER`).
- Call the solver's initialization method with the value array, weight array (wrapped as a list of lists), and capacity.

### Step 2 - Solve and Extract Solution
- Invoke the solver's solve method.
- Check that the returned objective value is not `None`.
- Extract selected items by querying `solver.best_solution_contains(i)` for each item index.

### Step 3 - Validate and Report Results
- Calculate the total weight of selected items to verify the capacity constraint is satisfied.
- Output the objective value, selected item indices, and total weight in a structured format.

### Code Usage
```python
# build model from formulation
from ortools.algorithms.python import knapsack_solver

profits = [...]  # values
weights = [...]  # resource consumption
capacity = ...   # resource limit

solver = knapsack_solver.KnapsackSolver(
    knapsack_solver.SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
    "KnapsackSolver"
)
# solve with status / termination checks
try:
    # Note: weights must be a list of lists for a single dimension.
    solver.init(profits, [weights], [capacity])
    computed_value = solver.solve()
except Exception as e:
    # Handle API errors
    computed_value = None

if computed_value is not None:
    selected_items = [i for i in range(len(profits)) if solver.best_solution_contains(i)]
    total_weight = sum(weights[i] for i in selected_items)
    # Verify feasibility
    if total_weight <= capacity:
        print(f"Objective: {computed_value}, Selected: {selected_items}, Weight Used: {total_weight}")
```

### Common Pitfalls
- Not handling exceptions from the solver's initialization or solve methods.
- Assuming the solver returns an optimal solution without checking for errors or `None` results.
- Incorrectly formatting the weight input (e.g., not wrapping a single weight list in another list).

# Workflow 2 (General-Purpose MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses a general-purpose Mixed-Integer Programming (MIP) solver via a modeling framework (e.g., Pyomo or OR-Tools `pywraplp`). It provides flexibility for future model extensions beyond the pure knapsack structure.

### Step 1 - Structure the Model
- Define a set representing all items.
- Create indexed parameters for item value and weight.
- Define a scalar parameter for the capacity.

### Step 2 - Declare Binary Variables
- Create one binary decision variable per item, representing its selection status (1 for selected, 0 otherwise).

### Step 3 - Formulate Objective and Constraint
- Set the objective to maximize the sum of item values multiplied by their corresponding binary variables.
- Add a single linear constraint ensuring the sum of selected item weights does not exceed the capacity.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": ["value[I]", "weight[I]", "capacity"],
  "decision_variables": ["x[I] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(value[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(weight[i] * x[i] for i in I) <= capacity"
  ]
}
```

### Common Pitfalls
- Using reserved keywords (e.g., `values`, `weights`) as parameter names in certain modeling frameworks, causing attribute conflicts.
- Not aligning the indices of parameters and variables, leading to model construction errors.
- Forgetting to set the objective sense to maximization.

## Solving stage

### Strategy Overview
Solve the formulated MIP model using an open-source solver like CBC or SCIP, accessed through a modeling framework's solver factory. This approach includes robust status checking and solution validation.

### Step 1 - Configure and Invoke Solver
- Instantiate the solver via the framework's factory (e.g., `SolverFactory("cbc")`).
- Set practical solver options: time limit, optimality gap tolerance (e.g., 0.0 for exact), and number of threads.
- Call the solver's `solve` method on the model.

### Step 2 - Check Solver Status
- Verify the solver status is `ok`.
- Check the termination condition is `optimal` or `feasible` before attempting to extract results.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value from the model.
- Identify selected items by checking if the binary variable's value exceeds a threshold (e.g., > 0.5).
- Manually compute the total weight of selected items to verify constraint satisfaction.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(n_items))
model.value = pyo.Param(model.I, initialize=value_dict)
model.weight = pyo.Param(model.I, initialize=weight_dict)
model.capacity = pyo.Param(initialize=capacity)
model.x = pyo.Var(model.I, domain=pyo.Binary)
model.obj = pyo.Objective(
    expr=sum(model.value[i] * model.x[i] for i in model.I),
    sense=pyo.maximize
)
model.capacity_con = pyo.Constraint(
    expr=sum(model.weight[i] * model.x[i] for i in model.I) <= model.capacity
)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False)
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_weight = sum(weight_dict[i] for i in selected_items)
    # Verify feasibility
    if total_weight <= capacity:
        print(f"Objective: {objective_value}, Selected: {selected_items}, Weight Used: {total_weight}")
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Extracting variable values without first confirming a successful solver status, which may cause errors.
- Using a strict equality (== 1) to check binary variable values, ignoring solver numerical tolerances; use a threshold (> 0.5) instead.
- Not setting a time limit, which can cause the solver to run indefinitely on large or difficult instances.
