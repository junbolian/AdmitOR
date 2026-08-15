---
name: BinaryKnapsackSolver
description: |
  Solve 0-1 knapsack problems via specialized solvers or general MILP frameworks, maximizing total value under a single weight capacity constraint.
---

# Workflow 1 (Specialized Knapsack Solver)

## Modeling stage

### Strategy Overview
Directly map the problem to a pure 0-1 knapsack formulation and use a dedicated, efficient algorithm (e.g., OR-Tools KnapsackSolver) designed for this specific structure.

### Step 1 - Recognize Problem Structure
- Identify the classic 0-1 knapsack pattern: a set of items, each with a value and weight, a single capacity limit, and binary selection decisions.
- Ensure the objective is to maximize total value and the only constraint is a linear sum of weights.

### Step 2 - Organize Input Data
- Store item values in a list `profits`.
- Store item weights in a list `weights`.
- Define a scalar `capacity` parameter.
- Ensure data arrays are parallel and correctly indexed.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": ["profits[I]", "weights[I]", "capacity"],
  "decision_variables": ["x[I] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(profits[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(weights[i] * x[i] for i in I) <= capacity"
  ]
}
```

### Common Pitfalls
- Using the wrong solver type for multi-dimensional problems; for single capacity, use a 1D weight list wrapped in a 2D structure.
- Forgetting to call `solver.init()` with the correct argument format (`profits`, `[weights]`, `[capacity]`).
- Assuming the solver returns a solution vector; you must query `best_solution_contains(i)` for each item.

## Solving stage

### Strategy Overview
Instantiate a specialized knapsack solver, initialize it with data, solve, and extract the binary solution with robust verification.

### Step 1 - Solver Initialization
- Import the specialized solver module (e.g., `ortools.algorithms.python.knapsack_solver`).
- Create a solver instance with an appropriate algorithm type (e.g., `KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER`).
- Initialize the solver using `solver.init(profits, [weights], [capacity])`. Note the list-of-lists format for weights and capacity.

### Step 2 - Solve and Check Status
- Call `solver.solve()` (takes no arguments).
- The solver computes the optimal value internally; no explicit status code is returned. Wrap the call in a try-except block to catch API errors.

### Step 3 - Solution Extraction and Verification
- Retrieve the optimal objective value via `solver.best_solution_total_value()` or similar method.
- For each item index `i`, determine selection using `solver.best_solution_contains(i)`.
- Independently verify the solution: sum the weights and values of selected items to confirm feasibility and objective match.

### Code Usage
```python
from ortools.algorithms.python import knapsack_solver

# Data
profits = [value_1, value_2, ...]
weights = [weight_1, weight_2, ...]
capacity = capacity_value

# Solver setup
solver = knapsack_solver.KnapsackSolver(
    knapsack_solver.SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
    "KnapsackExample"
)
try:
    solver.init(profits, [weights], [capacity])
    computed_value = solver.solve()
    selected_items = [i for i in range(len(profits)) if solver.best_solution_contains(i)]
    # Verification
    total_weight = sum(weights[i] for i in selected_items)
    total_value = sum(profits[i] for i in selected_items)
except Exception as e:
    # Handle solver errors
    print(f"Solver failed: {e}")
```

### Common Pitfalls
- Not providing weights and capacity as lists of lists, causing initialization errors.
- Assuming the solver handles infeasibility gracefully; manual checks on input data (e.g., all weights > capacity) are recommended.
- Omitting solution verification, which can hide subtle solver or data errors.

# Workflow 2 (General MILP with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the knapsack as a Mixed-Integer Linear Program (MILP) using a modeling framework (Pyomo), enabling flexibility for future constraint additions and use of various open-source solvers.

### Step 1 - Define Model Components
- Create a Pyomo `ConcreteModel`.
- Define a Set `I` for items.
- Define Parameters `value` and `weight` indexed by `I`, and a scalar `capacity` parameter.
- Define Binary Variables `x` indexed by `I`.

### Step 2 - Formulate Objective and Constraint
- Create an Objective to maximize `sum(value[i] * x[i] for i in I)`.
- Add a single Constraint: `sum(weight[i] * x[i] for i in I) <= capacity`.

### Step 3 - Structure for Reusability
- Separate data preparation from model construction.
- Use lambda functions or dictionaries to initialize parameters cleanly.
- Avoid reserved words (e.g., `values`, `weights`) for parameter names to prevent conflicts.

### Formulation Template
```json
{
  "sets": ["I (items)"],
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
- Using Pyomo reserved names for model attributes, leading to unexpected behavior.
- Forgetting to set the objective sense to `maximize`.
- Hard-coding data inside the model, reducing reusability for different instances.

## Solving stage

### Strategy Overview
Configure a MILP solver (e.g., CBC, HiGHS, SCIP) via Pyomo's SolverFactory, solve with performance options, and rigorously check status before extracting and verifying the solution.

### Step 1 - Solver Configuration
- Instantiate the solver: `SolverFactory("solver_name")` (e.g., `"cbc"`, `"highs"`).
- Set key options: time limit (`seconds` or `time_limit`), optimality gap (`ratio` or `mip_rel_gap`), and threads for parallelism.

### Step 2 - Solve and Validate Status
- Execute `solver.solve(model, tee=False)`.
- Check `SolverStatus` is `ok` and `TerminationCondition` is `optimal` or `feasible`. Proceed only if both checks pass.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value via `pyo.value(model.obj)`.
- Identify selected items by checking `pyo.value(model.x[i]) > 0.5` for each `i` in `I`.
- Recalculate total weight and value from selected items to verify constraint satisfaction and objective accuracy.

### Step 4 - Handle Failures
- If solver status is not ok or termination is not acceptable, output a structured error payload with status details.
- Consider fallback methods (e.g., dynamic programming) for small instances if the solver fails.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Data
values = [value_1, value_2, ...]
weights = [weight_1, weight_2, ...]
capacity = capacity_value
items = range(len(values))

# Model construction
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.value = pyo.Param(model.I, initialize=lambda m, i: values[i])
model.weight = pyo.Param(model.I, initialize=lambda m, i: weights[i])
model.capacity = pyo.Param(initialize=capacity)
model.x = pyo.Var(model.I, domain=pyo.Binary)
model.obj = pyo.Objective(
    expr=sum(model.value[i] * model.x[i] for i in model.I),
    sense=pyo.maximize
)
model.weight_limit = pyo.Constraint(
    expr=sum(model.weight[i] * model.x[i] for i in model.I) <= model.capacity
)

# Solver execution
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

# Status check and extraction
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    # Verification
    total_weight = sum(weights[i] for i in selected_items)
else:
    # Handle failure
    print(f"Solver failed: status={status}, termination={term}")
```

### Common Pitfalls
- Extracting solution without checking solver status, potentially reading invalid variable values.
- Using a loose optimality gap when an exact solution is required.
- Not verifying the solution against the original data, which can miss rounding errors or modeling mistakes.
