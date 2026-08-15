---
name: Binary Assignment with Capacity and Demand
description: |
  Model and solve binary assignment problems with resource limits and demand satisfaction using mixed-integer programming.

---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Program (MIP) using the OR-Tools CP-SAT or MIP solver APIs, which are designed for fast, large-scale optimization with binary variables. The formulation is built directly via a solver object, focusing on computational efficiency and straightforward constraint addition.

### Step 1 - Define Sets and Parameters
- Define the index sets for `RESOURCES` and `TASKS`.
- Organize parameters into dictionaries or lists: `availability[i]`, `demand[j]`, `cost[i][j]`, and `capacity[i][j]`.
- Validate data integrity, ensuring all parameter arrays are dimensionally consistent.

### Step 2 - Create Binary Decision Variables
- Create a binary decision variable `x[i][j]` for each resource-task pair using `solver.IntVar(0, 1, name)` or `solver.BoolVar(name)`.
- Use descriptive naming conventions (e.g., `f"x_{i}_{j}"`) for easier debugging and solution interpretation.

### Step 3 - Formulate Assignment Limit Constraints
- For each resource `i`, add a linear constraint: `sum(x[i][j] for j in TASKS) <= availability[i]`.
- Use `solver.Add()` with Python's `sum()` function for clear, readable constraint construction.

### Step 4 - Formulate Demand Satisfaction Constraints
- For each task `j`, add a linear constraint: `sum(capacity[i][j] * x[i][j] for i in RESOURCES) >= demand[j]`.
- Use `>=` to allow over-satisfaction of demand, which can be beneficial for cost minimization.

### Step 5 - Define the Linear Objective
- Formulate the total cost as `sum(cost[i][j] * x[i][j] for i in RESOURCES for j in TASKS)`.
- Set the objective to minimization using `solver.Minimize()` or `solver.Objective().SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    {"name": "availability", "index": "RESOURCES"},
    {"name": "demand", "index": "TASKS"},
    {"name": "cost", "index": ["RESOURCES", "TASKS"]},
    {"name": "capacity", "index": ["RESOURCES", "TASKS"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["RESOURCES", "TASKS"], "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    {"name": "assignment_limit", "expression": "sum(x[i][j]) <= availability[i]", "index": "RESOURCES"},
    {"name": "demand_satisfaction", "expression": "sum(capacity[i][j] * x[i][j]) >= demand[j]", "index": "TASKS"}
  ]
}
```

### Common Pitfalls
- Forgetting to scale cost or capacity parameters, leading to numerical issues or unintended objective dominance.
- Using `==` for demand constraints, which can make the model infeasible when over-satisfaction is permissible.
- Creating variables with incorrect bounds or types, such as using continuous variables instead of binary.

## Solving stage

### Strategy Overview
This stage focuses on configuring and executing the OR-Tools solver (SCIP or CBC), handling the solution process, and rigorously verifying the results. Emphasis is placed on solver settings, status checking, and post-solution validation.

### Step 1 - Select and Configure Solver
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('SCIP')` or `solver = cp_model.CpSolver()`.
- Set performance parameters: `solver.SetTimeLimit(seconds)` and `solver.SetNumThreads(thread_count)` for larger instances.
- For CP-SAT, set `cp_model.MaxTimeInSeconds(seconds)`.

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve()` or `cp_solver.Solve(model)`.
- Immediately check the solver status: `status = solver.Solve()` (returns `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.).
- For CP-SAT, check `cp_solver.StatusName()`.

### Step 3 - Extract and Validate Solution
- If status is `OPTIMAL` or `FEASIBLE`, extract the objective value: `objective_value = solver.Objective().Value()`.
- Extract variable values using `x[i][j].solution_value()` or `cp_solver.Value(x[i][j])`.
- Programmatically verify all constraints are satisfied by recalculating sums with the solution values.

### Step 4 - Report Results and Handle Failures
- Print the objective value and a summary of assignments.
- If status indicates `INFEASIBLE` or `UNBOUNDED`, analyze model data (e.g., total capacity vs. total demand) and constraints for errors.
- Consider enabling solver logging (`solver.EnableOutput()`) for difficult instances to diagnose issues.

### Code Usage
```python
# Example using OR-Tools MIP solver (simplified)
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
# ... Build model as per Modeling Stage steps ...

# Solve
status = solver.Solve()

# Check status and extract solution
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    print(f'Objective value = {solver.Objective().Value()}')
    # Extract and print assignments
    for i in RESOURCES:
        for j in TASKS:
            if x[i][j].solution_value() > 0.5:
                print(f'Resource {i} assigned to Task {j}')
else:
    print('The problem does not have an optimal solution.')
```

### Common Pitfalls
- Not checking solver status before extracting solution values, leading to runtime errors.
- Setting overly restrictive time limits for large problems, causing premature termination before a good solution is found.
- Assuming `FEASIBLE` status implies optimality; always check the optimality gap if available.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language in Python, to declaratively define the optimization model. It separates the model definition from the solver, allowing for clean, maintainable code and easy switching between solvers like HiGHS and CBC.

### Step 1 - Declare Abstract Sets
- Define Pyomo `Set` objects for `model.RESOURCES` and `model.TASKS`.
- Initialize sets with the list of indices. This provides a clear structure for indexing parameters and variables.

### Step 2 - Declare Parameters
- Define Pyomo `Param` objects for `availability`, `demand`, `cost`, and `capacity`.
- Initialize parameters using dictionaries keyed by the appropriate indices for efficient lookup.

### Step 3 - Declare Binary Variables
- Define a Pyomo `Var` object `model.x` indexed over `RESOURCES × TASKS` with `domain=pyo.Binary`.
- This creates all necessary binary decision variables in one declarative statement.

### Step 4 - Define Objective Function
- Define a Pyomo `Objective` object using a sum expression: `sum(model.cost[i,j] * model.x[i,j] for i in model.RESOURCES for j in model.TASKS)`.
- Set `sense=pyo.minimize`.

### Step 5 - Define Constraints via Rules
- Define an assignment limit constraint using a `Constraint` object with a rule function indexed by `RESOURCES`.
- Define a demand satisfaction constraint using a `Constraint` object with a rule function indexed by `TASKS`.
- The rule-based approach keeps the model definition modular and readable.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    {"name": "availability", "index": "RESOURCES"},
    {"name": "demand", "index": "TASKS"},
    {"name": "cost", "index": ["RESOURCES", "TASKS"]},
    {"name": "capacity", "index": ["RESOURCES", "TASKS"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["RESOURCES", "TASKS"], "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j])"
  },
  "constraints": [
    {"name": "resource_limit", "expression": "sum(x[i,j] for j in TASKS) <= availability[i]", "index": "RESOURCES"},
    {"name": "demand_fulfillment", "expression": "sum(capacity[i,j] * x[i,j] for i in RESOURCES) >= demand[j]", "index": "TASKS"}
  ]
}
```

### Common Pitfalls
- Incorrectly nesting sum comprehensions within Pyomo rule functions, leading to syntax errors or incorrect expressions.
- Using Python data types (lists, dicts) directly in Pyomo expressions instead of Pyomo components (`Param`, `Var`).
- Forgetting to initialize all required parameters before model instantiation, causing runtime errors.

## Solving stage

### Strategy Overview
This stage involves selecting a solver backend (e.g., HiGHS, CBC), configuring it with appropriate options for MIP solving, executing the solve, and implementing robust checks on the solver's status and termination condition before processing results.

### Step 1 - Instantiate and Configure Solver
- Create a solver object: `solver = pyo.SolverFactory('highs')` or `solver = pyo.SolverFactory('cbc')`.
- Set solver options: `solver.options['mip_rel_gap'] = 0.0` for optimality, `solver.options['time_limit'] = 30` for runtime control.
- Avoid setting conflicting options (e.g., `threads` for HiGHS if it self-manages).

### Step 2 - Execute Solve with Logging
- Call `results = solver.solve(model, tee=True)` to solve and print the solver log. Use `tee=False` for silent operation.
- The `results` object contains the solver return status and solution data.

### Step 3 - Check Solver Status and Termination
- Import `SolverStatus` and `TerminationCondition` from `pyomo.opt`.
- Check: `if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:`.
- This two-part check is crucial to confirm the solver ran successfully *and* found a valid solution.

### Step 4 - Extract and Verify Solution
- Extract the objective value: `pyo.value(model.obj)`.
- Extract binary variable values using a threshold (e.g., `pyo.value(model.x[i,j]) > 0.5`) due to potential numerical precision.
- Programmatically verify all constraints are satisfied by recalculating sums with the extracted values.

### Step 5 - Standardize Output and Handle Failures
- Print the objective value in a consistent, parseable format (e.g., `RESULT: {value}`).
- Provide a detailed assignment summary for verification.
- If the solver failed, analyze the `termination_condition` and model data for infeasibility or unboundedness.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... Build model as per Modeling Stage steps ...

solver = pyo.SolverFactory('highs')
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    print(f'RESULT: {pyo.value(model.obj)}')
    # Extract assignments
    for i in model.RESOURCES:
        for j in model.TASKS:
            if pyo.value(model.x[i,j]) > 0.5:
                print(f'Assignment: {i} -> {j}')
else:
    print(f'Solver failed. Status: {status}, Termination: {term}')
```

### Common Pitfalls
- Only checking `SolverStatus.ok` without verifying `TerminationCondition`, potentially accepting suboptimal or incomplete solutions.
- Extracting variable values without a numerical tolerance check, misinterpreting near-zero values as assignments.
- Setting invalid solver option values (e.g., negative time limits) which may be silently ignored or cause errors.
