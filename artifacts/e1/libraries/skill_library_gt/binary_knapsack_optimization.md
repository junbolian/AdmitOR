---
name: Binary Knapsack Optimization
description: |
  Model and solve binary selection problems with a single capacity constraint using either specialized knapsack solvers or general-purpose MILP frameworks.

---

# Workflow 1 (Specialized Knapsack Solver)

## Modeling stage

### Strategy Overview
This workflow leverages a dedicated, efficient algorithm for the classic 0-1 knapsack problem, bypassing the need for a full MILP model. It is ideal for pure binary selection problems with a single linear constraint.

### Step 1 - Recognize the Problem Pattern
- Identify a selection problem where each item is either fully included or excluded (binary decision).
- Confirm the objective is to maximize total value and the only constraint is a sum of weights not exceeding a capacity.
- Ensure data consists of parallel lists or arrays for item values and weights, plus a scalar capacity.

### Step 2 - Structure Data for Solver Input
- Organize item data into two lists: `profits` for values and `weights` for resource consumption.
- Note that the capacity is a single numerical limit.
- The specialized solver expects weights as a 2D list `[weights]` even for a single dimension.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": ["profits", "weights", "capacity"],
  "decision_variables": ["binary_selection"],
  "objective": {
    "sense": "max",
    "expression": "sum(profits[i] * binary_selection[i] for i in items)"
  },
  "constraints": [
    {
      "name": "capacity_limit",
      "expression": "sum(weights[i] * binary_selection[i] for i in items) <= capacity"
    }
  ]
}
```

### Common Pitfalls
- Providing weights as a 1D list instead of the required 2D list `[weights]`.
- Using a generic MIP solver for a pure knapsack problem, missing performance benefits.
- Not validating that all weights are non-negative, which is a requirement for the algorithm.

## Solving stage

### Strategy Overview
Use a dedicated knapsack solver (e.g., OR-Tools KnapsackSolver) for exact solutions. This stage focuses on correct API usage, solution extraction, and validation.

### Step 1 - Initialize the Specialized Solver
- Select the appropriate solver type, such as `KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER` for exact solutions.
- Instantiate the solver with a descriptive problem name.

### Step 2 - Load Data and Solve
- Call the solver's initialization method with the correct signature: `solver.init(profits, [weights], [capacity])`.
- Execute the solve method, which returns the optimal objective value.
- Wrap the solve call in a try-except block to handle potential API errors gracefully.

### Step 3 - Extract and Verify the Solution
- Retrieve the selection status for each item using `solver.best_solution_contains(i)`.
- Recompute the total weight and value from the selected items to verify feasibility and correctness.
- Perform a sanity check, such as ensuring no unselected item with a higher value-to-weight ratio could fit in the remaining capacity.

### Code Usage
```python
# Example using OR-Tools KnapsackSolver
from ortools.algorithms.python import knapsack_solver

# 1. Build model from formulation
profits = [...]  # List of item values
weights = [...]  # List of item weights
capacity = ...   # Scalar capacity

# 2. Initialize and solve
solver = knapsack_solver.KnapsackSolver(
    knapsack_solver.SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
    "KnapsackProblem"
)
solver.init(profits, [weights], [capacity])
try:
    computed_value = solver.solve()
except Exception as e:
    # Handle solver error
    computed_value = None

# 3. Extract and verify solution
if computed_value is not None:
    selected_items = [i for i in range(len(profits)) if solver.best_solution_contains(i)]
    total_weight = sum(weights[i] for i in selected_items)
    # Verify constraint
    assert total_weight <= capacity
```

### Common Pitfalls
- Forgetting to wrap weights in an extra list dimension for the `init` method.
- Assuming the solver returns a status code; it returns the objective value directly.
- Not verifying the solution against the original problem data, leading to silent errors.

# Workflow 2 (General-Purpose MILP with Pyomo)

## Modeling stage

### Strategy Overview
Model the problem as a Mixed-Integer Linear Program (MILP) using a modeling language (Pyomo). This approach is flexible, portable across solvers, and easily extensible to more complex variants.

### Step 1 - Define Model Structure
- Create a ConcreteModel to hold all components.
- Define a Set `I` to index the items.
- Create Parameters for item values and weights, and a scalar for capacity.

### Step 2 - Declare Variables and Relationships
- Declare binary decision variables `x[i]` over the set `I`.
- Formulate the objective as the sum of value[i] * x[i] to maximize.
- Add a single linear constraint summing weight[i] * x[i] <= capacity.

### Step 3 - Parameterize for Reuse
- Use lambda functions or dictionaries to initialize parameters from external data lists.
- Avoid using Pyomo reserved words (e.g., `value`, `weight`) as attribute names; use alternatives like `val`, `wgt`.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": ["val", "wgt", "cap"],
  "decision_variables": ["x"],
  "objective": {
    "sense": "max",
    "expression": "sum(val[i] * x[i] for i in I)"
  },
  "constraints": [
    {
      "name": "weight_limit",
      "expression": "sum(wgt[i] * x[i] for i in I) <= cap"
    }
  ]
}
```

### Common Pitfalls
- Using common Python or Pyomo keywords as parameter or variable names, causing conflicts.
- Hard-coding data inside the model definition, reducing reusability.
- Forgetting to set the objective sense to `maximize`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver (e.g., CBC, SCIP, HiGHS). This stage emphasizes solver configuration, robust status checking, and solution validation.

### Step 1 - Configure the Solver
- Instantiate the solver via `SolverFactory("solver_name")` (e.g., "cbc", "scip", "highs").
- Set key options: a time limit (`seconds` or `time_limit`), an optimality gap tolerance (`ratio` or `mip_rel_gap`), and the number of threads for parallel processing.

### Step 2 - Solve and Check Status
- Execute the solve method, optionally suppressing the log output (`tee=False`).
- Immediately check the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`). Proceed only if both checks pass.

### Step 3 - Extract and Validate Results
- Retrieve the objective value via `pyo.value(model.obj)`.
- Determine selected items by checking `pyo.value(model.x[i]) > 0.5` for each variable.
- Recalculate total weight and value from the extracted solution to verify constraint satisfaction and objective correctness.

### Code Usage
```python
# Example using Pyomo with CBC
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build model from formulation
def build_knapsack_model(values, weights, capacity):
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=range(len(values)))
    model.val = pyo.Param(model.I, initialize=lambda m, i: values[i])
    model.wgt = pyo.Param(model.I, initialize=lambda m, i: weights[i])
    model.cap = pyo.Param(initialize=capacity)
    model.x = pyo.Var(model.I, domain=pyo.Binary)
    model.obj = pyo.Objective(
        expr=sum(model.val[i] * model.x[i] for i in model.I),
        sense=pyo.maximize
    )
    model.weight_limit = pyo.Constraint(
        expr=sum(model.wgt[i] * model.x[i] for i in model.I) <= model.cap
    )
    return model

model = build_knapsack_model(values, weights, capacity)

# 2. Solve with status / termination checks
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
    # Verification
    total_weight = sum(weights[i] for i in selected_items)
    assert total_weight <= capacity
else:
    # Handle solver failure
    objective_value = None
    selected_items = []
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to processing of invalid solutions.
- Using a loose threshold (e.g., `== 1.0`) for binary variable values, which can fail due to floating-point precision; use `> 0.5`.
- Omitting the verification step, which can miss infeasibilities introduced by solver rounding.
