---
name: SetCoverSolver
description: |
  Model and solve binary selection problems with coverage requirements and cost minimization using MIP solvers.
---

# Workflow 1 (OR-Tools MIP)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using the OR-Tools linear solver wrapper. This approach is efficient for standard set cover problems and leverages fast, open-source solvers like SCIP or CBC.

### Step 1 - Define Data Structures
- Map the problem elements: define a set of selectable items and a set of requirements to be covered.
- Create dictionaries for item costs and for coverage relationships (mapping each requirement to the list of items that can cover it).

### Step 2 - Create Binary Variables
- For each selectable item, create a binary decision variable (0 or 1) indicating its selection status.

### Step 3 - Formulate Coverage Constraints
- For each requirement, add a linear constraint ensuring the sum of the binary variables for the items that can cover it is at least one.

### Step 4 - Define Linear Objective
- Define the objective as the minimization of the total cost, calculated as the sum of each item's cost multiplied by its binary variable.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items (e.g., teams, facilities).",
    "J: Set of requirements to be covered (e.g., locations, tasks)."
  ],
  "parameters": [
    "cost_i: Cost of selecting item i ∈ I.",
    "coverage_j: List of items i ∈ I that can cover requirement j ∈ J."
  ],
  "decision_variables": [
    "x_i: Binary variable, 1 if item i ∈ I is selected, 0 otherwise."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} cost_i * x_i"
  },
  "constraints": [
    "Coverage: For each j in J: sum_{i in coverage_j} x_i >= 1"
  ]
}
```

### Common Pitfalls
- Forgetting to ensure the `coverage_j` lists are non-empty for all requirements `j`, which would make the problem trivially infeasible.
- Using floating-point costs that are not precisely represented, which can lead to unexpected numerical issues in the solver.

## Solving stage

### Strategy Overview
Solve the formulated MIP using the OR-Tools wrapper, configuring the underlying solver for performance and reliability. Extract and rigorously verify the solution.

### Step 1 - Initialize Solver
- Instantiate a solver object (e.g., `SCIP` or `CBC`) via `pywraplp.Solver.CreateSolver`.
- Set practical limits such as time limit and number of threads.

### Step 2 - Build and Solve Model
- Programmatically add variables, constraints, and the objective as defined in the modeling stage.
- Call the solver's `Solve()` method and capture the status.

### Step 3 - Check Status and Extract Solution
- Check if the solver returned an `OPTIMAL` or `FEASIBLE` status.
- If successful, extract the solution by evaluating each variable's value (using a threshold, e.g., > 0.5, to account for solver tolerances).
- Compute the achieved objective value.

### Step 4 - Verify Solution Correctness
- Independently verify that all coverage constraints are satisfied by the extracted set of selected items.
- Optionally, prove optimality by attempting to solve a modified problem with a stricter cost bound.

### Code Usage
```python
# 1. Data Preparation (using placeholders)
items = list(range(num_items))
requirements = list(range(num_reqs))
cost = {i: cost_value for i in items}
coverage = {j: [list_of_covering_items] for j in requirements}

# 2. Solver Setup
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(time_limit_ms)
solver.SetNumThreads(num_threads)

# 3. Variables
x = {i: solver.IntVar(0, 1, f'x_{i}') for i in items}

# 4. Constraints
for j in requirements:
    solver.Add(sum(x[i] for i in coverage[j]) >= 1)

# 5. Objective
objective = solver.Objective()
for i in items:
    objective.SetCoefficient(x[i], cost[i])
objective.SetMinimization()

# 6. Solve and Verify
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected_items = [i for i in items if x[i].solution_value() > 0.5]
    obj_value = objective.Value()
    # Verification
    all_covered = all(any(i in selected_items for i in coverage[j]) for j in requirements)
    if not all_covered:
        raise AssertionError("Solution verification failed.")
    # Output result
    result = {"objective": obj_value, "selected": selected_items}
else:
    # Handle infeasible or error status
    result = {"error": f"Solver status: {status}"}
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Relying solely on the solver's reported feasibility without independent verification of coverage constraints.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo, which provides a clean, algebraic interface. This approach enhances model readability, maintainability, and allows easy switching between solvers like HiGHS or CBC.

### Step 1 - Define Abstract Sets and Parameters
- Use Pyomo's `Set` and `Param` components to formally define the index sets (items, requirements) and input data (costs, coverage).

### Step 2 - Declare Binary Variables
- Declare a Pyomo `Var` with `domain=pyo.Binary` for each selectable item.

### Step 3 - Construct Constraints via Rules
- Define a `Constraint` component for the coverage requirements, using a rule function that iterates over the set of requirements.

### Step 4 - Specify the Objective
- Define an `Objective` component with `sense=pyo.minimize` and the linear cost expression.

### Formulation Template
```json
{
  "sets": [
    "model.I: Pyomo Set of selectable items.",
    "model.J: Pyomo Set of requirements."
  ],
  "parameters": [
    "model.cost: Pyomo Param indexed by I, defining selection costs.",
    "model.coverage: Pyomo Param (or a rule) defining, for each j in J, the subset of I that covers it."
  ],
  "decision_variables": [
    "model.x: Pyomo Var indexed by I, with domain=Binary."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[i] * model.x[i] for i in model.I)"
  },
  "constraints": [
    "Coverage: For each j in model.J: sum(model.x[i] for i in model.coverage[j]) >= 1"
  ]
}
```

### Common Pitfalls
- Defining Pyomo `Set` or `Param` objects with mutable Python data structures inside rule functions, which can lead to initialization errors.
- Using overly complex rule functions for coverage that obscure the simple "sum over a subset" logic.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., `highs` or `cbc`). Leverage Pyomo's standardized interface for solver configuration, status checking, and solution extraction.

### Step 1 - Instantiate Solver Factory
- Create a solver object using `SolverFactory(solver_name)`.

### Step 2 - Configure Solver Options
- Set solver-specific options such as time limit (`seconds`), optimality gap (`ratio`), and thread count (`threads`) via `solver.options`.

### Step 3 - Execute Solve and Capture Results
- Call `solver.solve(model, tee=False)` and store the returned `results` object.

### Step 4 - Validate Solver Termination
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 5 - Extract and Verify Solution
- Extract variable values using `pyo.value(model.x[i])` and apply a threshold (e.g., > 0.5) to determine selection.
- Compute the objective value and perform an independent verification of all coverage constraints.

### Code Usage
```python
# 1. Build Model
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items_list)
model.J = pyo.Set(initialize=requirements_list)
model.cost = pyo.Param(model.I, initialize=cost_dict)
# Assume coverage_dict[j] returns list of items i
model.coverage = pyo.Param(model.J, initialize=coverage_dict)

model.x = pyo.Var(model.I, domain=pyo.Binary)

def coverage_rule(model, j):
    return sum(model.x[i] for i in model.coverage[j]) >= 1
model.cover = pyo.Constraint(model.J, rule=coverage_rule)

model.obj = pyo.Objective(
    expr=sum(model.cost[i] * model.x[i] for i in model.I),
    sense=pyo.minimize
)

# 2. Solve
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['seconds'] = time_limit
solver.options['threads'] = num_threads
results = solver.solve(model, tee=False)

# 3. Check Status and Extract
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    obj_value = pyo.value(model.obj)
    # Verification
    all_covered = all(any(i in selected_items for i in model.coverage[j]) for j in model.J)
    if not all_covered:
        raise AssertionError("Solution verification failed.")
    result = {"objective": obj_value, "selected": selected_items}
else:
    result = {"error": f"Solver failed: {results.solver.termination_condition}"}
```

### Common Pitfalls
- Confusing Pyomo's `SolverStatus` (process status) with `TerminationCondition` (solution quality), leading to incorrect interpretation of results.
- Not using `pyo.value()` to extract numeric values from Pyomo components, which returns the underlying object instead.
