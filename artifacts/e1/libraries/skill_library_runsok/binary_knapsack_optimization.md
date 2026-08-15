---
name: Binary Knapsack Optimization
description: |
  Model and solve binary selection problems with a single capacity constraint using specialized solvers or general-purpose MIP frameworks.
---

# Workflow 1 (Specialized Knapsack Solver)

## Modeling stage

### Strategy Overview
This workflow leverages a dedicated, efficient algorithm for the pure 0-1 knapsack problem, bypassing the need to construct a general MIP model. It is ideal for large-scale instances where performance is critical.

### Step 1 - Recognize Pure Knapsack Pattern
- Identify the problem as a 0-1 knapsack: each item can be selected at most once, subject to a single resource capacity.
- Confirm the objective is to maximize total value (or minimize total cost) of selected items.
- Ensure all problem data (values, weights, capacity) are integer or can be scaled to integers for the solver.

### Step 2 - Map Problem Data
- Define `values` as a list of item benefits (e.g., profit, utility).
- Define `weights` as a list of item resource consumptions (e.g., cost, weight).
- Define `capacity` as the total available resource limit.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": [
    {"name": "values", "indexed_by": "items", "type": "numeric"},
    {"name": "weights", "indexed_by": "items", "type": "numeric"},
    {"name": "capacity", "type": "numeric"}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": "items", "domain": "binary"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(values[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "capacity_constraint", "expression": "sum(weights[i] * x[i] for i in items) <= capacity"}
  ]
}
```

### Common Pitfalls
- Forgetting to format weights as a list of lists (`[[w1, w2, ...]]`) for solvers expecting multi-dimensional input, even for a single dimension.
- Using non-integer data without proper scaling, which can cause solver errors or incorrect results.
- Assuming the solver returns a model object; it directly returns the objective value and solution vector.

## Solving stage

### Strategy Overview
Use a specialized knapsack solver API (e.g., OR-Tools `KnapsackSolver`) for direct, efficient solution. The workflow focuses on correct data formatting, solver configuration, and robust solution extraction.

### Step 1 - Initialize Solver
- Create a solver instance, specifying an exact algorithm (e.g., `KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER`).
- Set optional parameters like time limit if supported by the solver API.

### Step 2 - Load Data and Solve
- Format the weights parameter as a list of lists: `solver_weights = [weights]`.
- Call `solver.init(values, solver_weights, [capacity])` to load the problem.
- Execute `solver.solve()` to compute the optimal solution. No arguments are passed to this method.

### Step 3 - Extract and Validate Solution
- Retrieve the optimal objective value directly from the solver.
- Determine selected items by checking `solver.best_solution_contains(i)` for each item `i`.
- Validate feasibility by recomputing the total weight of selected items and ensuring it does not exceed capacity.

### Code Usage
```python
# Example using OR-Tools KnapsackSolver
from ortools.algorithms import pywrapknapsack_solver

# 1. Initialize solver
solver = pywrapknapsack_solver.KnapsackSolver(
    pywrapknapsack_solver.KnapsackSolver.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
    'Knapsack'
)

# 2. Prepare data (use placeholders)
values = [value_i for i in items]
weights = [[weight_i for i in items]]  # Critical: list of lists
capacity = [capacity_value]

# 3. Solve
solver.init(values, weights, capacity)
computed_value = solver.solve()

# 4. Extract solution
selected_items = []
total_weight = 0
for i in range(len(values)):
    if solver.best_solution_contains(i):
        selected_items.append(i)
        total_weight += weights[0][i]

# 5. Validate
if total_weight > capacity[0]:
    raise ValueError("Solution violates capacity constraint.")
```

### Common Pitfalls
- Calling `solver.solve()` with arguments, which is incorrect for this API.
- Not handling potential solver failures; wrap the solve call in a try-except block.
- Misinterpreting the returned objective value type (often integer).

# Workflow 2 (General-Purpose MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses a standard Mixed-Integer Programming (MIP) modeling framework (e.g., Pyomo, OR-Tools `pywraplp`) to formulate the knapsack problem. It provides flexibility for future model extensions and leverages robust, widely-available solvers.

### Step 1 - Define Model Structure
- Create a concrete model object.
- Define a set `items` to index all selectable items.
- Declare parameters `value` and `weight` as dictionaries indexed by `items`.
- Declare parameter `capacity` as a scalar.

### Step 2 - Create Decision Variables
- Create binary decision variables `x[i]` for each item `i`, representing selection (`1`) or exclusion (`0`).

### Step 3 - Formulate Objective and Constraint
- Set the objective to maximize `sum(value[i] * x[i] for i in items)`.
- Add the capacity constraint: `sum(weight[i] * x[i] for i in items) <= capacity`.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": [
    {"name": "value", "indexed_by": "items", "type": "numeric"},
    {"name": "weight", "indexed_by": "items", "type": "numeric"},
    {"name": "capacity", "type": "numeric"}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": "items", "domain": "binary"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(value[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "budget", "expression": "sum(weight[i] * x[i] for i in items) <= capacity"}
  ]
}
```

### Common Pitfalls
- Using inconsistent indexing between parameters and variables.
- Forgetting to set the objective sense (maximize/minimize).
- Defining the capacity constraint with a strict equality (`==`) instead of inequality (`<=`).

## Solving stage

### Strategy Overview
Solve the formulated MIP model using a compatible solver (e.g., CBC, SCIP, HiGHS). The workflow emphasizes solver interface patterns, solution status checking, and result extraction with numerical tolerance handling.

### Step 1 - Select and Configure Solver
- Instantiate a solver object compatible with the modeling framework (e.g., `SolverFactory('cbc')` in Pyomo, `pywraplp.Solver.CreateSolver("SCIP")` in OR-Tools).
- Set practical options: time limit, optimality gap tolerance, and number of threads.

### Step 2 - Solve and Check Status
- Execute the solve command with `load_solutions=False` (if applicable) to separate solving from solution loading.
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`). Proceed only if acceptable.

### Step 3 - Extract and Verify Solution
- Load the solution values into the model variables.
- Extract selected items by checking `x[i].value` (or `solution_value()`) with a numerical tolerance (e.g., `> 0.5`).
- Recompute total weight and value from the extracted solution to verify feasibility and objective value.

### Code Usage
```python
# Example using Pyomo with HiGHS
import pyomo.environ as pyo

# 1. Build model from formulation
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=range(n_items))
model.value = pyo.Param(model.items, initialize=value_dict)
model.weight = pyo.Param(model.items, initialize=weight_dict)
model.capacity = pyo.Param(initialize=capacity_value)

model.x = pyo.Var(model.items, domain=pyo.Binary)

def obj_rule(model):
    return pyo.sum_product(model.value, model.x)
model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

def budget_rule(model):
    return pyo.sum_product(model.weight, model.x) <= model.capacity
model.budget = pyo.Constraint(rule=budget_rule)

# 2. Solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs')
results = solver.solve(model, load_solutions=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    model.solutions.load_from(results)

    # 3. Extract solution
    selected_items = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
    total_value = sum(pyo.value(model.value[i]) for i in selected_items)
    total_weight = sum(pyo.value(model.weight[i]) for i in selected_items)

    # 4. Validate
    if total_weight > pyo.value(model.capacity) + 1e-6:
        print("Warning: Solution may violate capacity constraint.")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Loading solutions without checking termination condition, potentially using invalid results.
- Using exact equality (`== 1.0`) to interpret binary variable values, which can fail due to solver tolerances.
- Not setting a time limit, allowing the solver to run indefinitely on difficult instances.
