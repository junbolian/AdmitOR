---
name: Weighted Set Cover Optimization
description: |
  Model and solve weighted set cover problems using binary selection variables, coverage constraints, and a minimize weighted sum objective, with implementation options for different solver backends.
---

# Workflow 1 (MIP Solver via OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the weighted set cover problem as a Mixed-Integer Program (MIP) using the OR-Tools `pywraplp` interface. It is designed for direct, imperative model construction and solving with open-source MIP solvers like SCIP or CBC.

### Step 1 - Define Sets and Parameters
- Identify the set of selectable items (e.g., vehicles, facilities) and the set of coverage requirements (e.g., routes, demand points).
- Define a cost parameter `cost[i]` for each selectable item `i`.
- Create a coverage mapping `covers[j]` for each requirement `j`, listing the items that can satisfy it.

### Step 2 - Create Binary Decision Variables
- For each selectable item `i`, create a binary variable `x[i]` where `1` indicates selection.
- Use `solver.IntVar(0, 1, f"x_{i}")` to instantiate each variable.

### Step 3 - Formulate Coverage Constraints
- For each coverage requirement `j`, create a linear constraint with a lower bound of 1.
- For each item `i` in `covers[j]`, add the variable `x[i]` with a coefficient of 1 to the constraint.

### Step 4 - Define the Objective Function
- Formulate the objective as minimizing the total weighted sum: `min sum(cost[i] * x[i] for i in items)`.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "items",
    "requirements"
  ],
  "parameters": [
    "cost[items]",
    "covers[requirements] -> list of items"
  ],
  "decision_variables": [
    "x[items] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    "sum(x[i] for i in covers[j]) >= 1 for all j in requirements"
  ]
}
```

### Common Pitfalls
- Forgetting to add all covering items to their respective constraint, leading to incorrect coverage.
- Using floating-point equality (`== 1`) instead of inequality (`>= 1`) for coverage constraints, which can make the model infeasible if an element is covered by multiple selected items.
- Not using a sparse representation for the coverage mapping, which causes inefficiency with large, sparse problems.

## Solving stage

### Strategy Overview
This stage involves building the model using OR-Tools' solver factory, configuring solver options, executing the solve, and rigorously checking the solution status before extracting results.

### Step 1 - Initialize Solver and Build Model
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Execute the modeling steps (Define Sets, Create Variables, Formulate Constraints, Define Objective) to populate the solver object.

### Step 2 - Configure Solver and Execute Solve
- Set a time limit if needed: `solver.SetTimeLimit(time_limit_ms)`.
- Call `solver.Solve()` to initiate the optimization.

### Step 3 - Verify Solution Status and Extract Results
- Check the solver status: `status = solver.Objective().Value()` is not sufficient; verify `solver.OPTIMAL` or `solver.FEASIBLE`.
- If the status is acceptable, extract variable values: `selected_items = [i for i in items if x[i].solution_value() > 0.5]`.
- Calculate the objective value from the solver or by summing `cost[i] * x[i].solution_value()`.

### Step 4 - Validate Solution Feasibility
- For each requirement `j`, verify that at least one item in `covers[j]` is in `selected_items`.
- For small instances, optionally validate optimality via brute-force enumeration.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (modeling steps: create variables, constraints, objective)

# solve with status / termination checks
result_status = solver.Solve()
if result_status == pywraplp.Solver.OPTIMAL or result_status == pywraplp.Solver.FEASIBLE:
    objective_value = solver.Objective().Value()
    selected = [i for i in items if x[i].solution_value() > 0.5]
    # ... (proceed with solution validation and output)
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Assuming a non-`OPTIMAL` status (e.g., `FEASIBLE`) means the solution is optimal, potentially leading to suboptimal decisions.
- Not handling solver failures (e.g., time limit, memory error) gracefully, causing the program to crash.
- Extracting variable values without checking the solver status first, which may lead to accessing undefined values.

# Workflow 2 (Declarative Modeling with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a declarative, algebraic modeling approach. It separates model definition from solver execution, promoting clean, maintainable code and easy switching between solvers like CBC or GLPK.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `items` and `requirements`.
- Declare a `Param` dictionary `cost` indexed by `items`.
- Define a sparse coverage parameter or rule, such as a dictionary `covers` mapping each requirement to a list of items.

### Step 2 - Declare Binary Decision Variables
- Create a Pyomo `Var` object `model.x` indexed by `items` with `domain=pyo.Binary`.

### Step 3 - Formulate Objective and Constraints Declaratively
- Define the objective using a `sum` expression: `model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.items), sense=pyo.minimize)`.
- Create a `Constraint` list indexed by `requirements` using a rule that sums `model.x[i]` for `i` in `model.covers[req]`.

### Step 4 - Instantiate the Concrete Model
- Populate the abstract sets and parameters with actual data to create a `ConcreteModel`.

### Formulation Template
```json
{
  "sets": [
    "model.items",
    "model.requirements"
  ],
  "parameters": [
    "model.cost[model.items]",
    "model.covers[model.requirements] (sparse mapping)"
  ],
  "decision_variables": [
    "model.x[model.items] ∈ pyo.Binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[i] * model.x[i] for i in model.items)"
  },
  "constraints": [
    "sum(model.x[i] for i in model.covers[r]) >= 1 for all r in model.requirements"
  ]
}
```

### Common Pitfalls
- Confusing abstract model definition with concrete data instantiation, leading to uninitialized parameters or sets.
- Using dense matrices for coverage in Pyomo rules, which can drastically increase model generation time for large, sparse problems.
- Incorrectly indexing parameters or variables within constraint rules, causing `KeyError` or incorrect model logic.

## Solving stage

### Strategy Overview
This stage focuses on solving the instantiated Pyomo model with a configured solver, checking termination conditions rigorously, and extracting the solution in a robust manner.

### Step 1 - Select and Configure Solver
- Create a solver factory: `solver = pyo.SolverFactory("cbc")`.
- Set solver options such as time limit (`seconds`) and optimality gap (`ratio`).

### Step 2 - Execute Solve and Check Results
- Call `results = solver.solve(model, tee=False)` to solve.
- Inspect both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`).

### Step 3 - Load and Validate Solution
- Only load solution values if the status is `ok` and termination is `optimal` or `feasible`.
- Extract selected items: `selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]`.
- Verify coverage constraints are satisfied by the extracted selection.

### Step 4 - Implement Fallback and Validation
- For small instances, implement a brute-force verification to confirm optimality.
- If the solver fails, implement a heuristic fallback (e.g., select all items that uniquely cover a requirement) to find a feasible solution.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (declarative modeling steps)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    # Load results
    selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
    obj_val = pyo.value(model.obj)
    # ... (proceed with solution validation and output)
elif results.solver.termination_condition == TerminationCondition.feasible:
    print("Feasible but not proven optimal solution found.")
else:
    print("Solver failed.")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially misinterpreting suboptimal or failed solves as optimal.
- Accessing variable values (`pyo.value`) before ensuring the solution is loaded, which may raise an error or return `None`.
- Omitting a time limit for large instances, causing the solve to run indefinitely.
