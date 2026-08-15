---
name: Generalized Continuous Assignment Solver
description: |
  Model and solve resource allocation problems with supply, demand, and per-assignment limits using continuous variables, producing optimal fractional assignments.
---

# Workflow 1 (OR-Tools LP/MIP Solver)

## Modeling stage

### Strategy Overview
Model the problem as a linear program using OR-Tools' `pywraplp` API, defining variables and constraints directly via solver methods. This approach is procedural and solver-agnostic, suitable for both LP (`GLOP`) and MIP (`CBC`) backends.

### Step 1 - Define Data Structures
- Organize input data into lists or dictionaries for resources, tasks, availability, requirements, costs, and per-assignment capacities.
- Use zero-based indexing for compatibility with solver loops.

### Step 2 - Create Decision Variables
- Instantiate a solver object (`pywraplp.Solver`).
- Create a dictionary of decision variables `x[i][j]` using `solver.NumVar` for continuous or `solver.IntVar` for integer problems.
- Set variable bounds from `0` to the per-assignment capacity limit.

### Step 3 - Formulate Constraints
- **Resource Capacity**: For each resource `i`, sum of `x[i][j]` over all tasks `j` ≤ `availability[i]`.
- **Demand Satisfaction**: For each task `j`, sum of `x[i][j]` over all resources `i` = `requirement[j]`.
- **Assignment Capacity**: For each pair `(i, j)`, `x[i][j]` ≤ `capacity_limit[i][j]`.

### Step 4 - Set Objective
- Define a linear minimization objective: sum of `cost[i][j] * x[i][j]` over all `i`, `j`.
- Use `solver.Objective().SetMinimization()` and `SetCoefficient()` for each variable.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "tasks"
  ],
  "parameters": [
    {"name": "availability", "index": "resources", "type": "float"},
    {"name": "requirement", "index": "tasks", "type": "float"},
    {"name": "cost", "index": ["resources", "tasks"], "type": "float"},
    {"name": "capacity_limit", "index": ["resources", "tasks"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["resources", "tasks"], "type": "continuous_nonnegative"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in resources for j in tasks)"
  },
  "constraints": [
    {"name": "resource_capacity", "expression": "sum(x[i][j] for j in tasks) <= availability[i]", "index": "resources"},
    {"name": "demand_satisfaction", "expression": "sum(x[i][j] for i in resources) == requirement[j]", "index": "tasks"},
    {"name": "assignment_capacity", "expression": "x[i][j] <= capacity_limit[i][j]", "index": ["resources", "tasks"]}
  ]
}
```

### Common Pitfalls
- Forgetting to set upper bounds on variables, leading to unbounded problems.
- Mixing `NumVar` and `IntVar` incorrectly when switching between LP and MIP.
- Not using consistent indexing when populating constraints, causing `KeyError`.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' wrapper, check the solution status rigorously, extract results, and perform post-solve validation to ensure feasibility.

### Step 1 - Configure and Execute Solver
- Call `solver.Solve()` to execute the optimization.
- For MIP problems, consider setting solver time limits or optimality gaps via `solver.SetTimeLimit()` or `solver.SetNumThreads()`.

### Step 2 - Check Solver Status
- Capture the return status from `Solve()`.
- Verify success by checking if `status` is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`.
- Handle unsuccessful statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) with appropriate error messages.

### Step 3 - Extract and Validate Solution
- If successful, retrieve the objective value via `solver.Objective().Value()`.
- Iterate through decision variables, using `variable.solution_value()` to get assignments.
- Programmatically verify that all constraints are satisfied within a small tolerance (e.g., 1e-6).

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Create solver (choose 'GLOP' for LP, 'CBC' for MIP)
solver = pywraplp.Solver.CreateSolver('GLOP')

# 2. Build model (follow Modeling Stage steps)
# ... [Variable and constraint creation code] ...

# 3. Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    # Extract variable values
    assignments = {}
    for i in resources:
        for j in tasks:
            val = x[i, j].solution_value()
            if val > 1e-6:  # Store non-zero assignments
                assignments[(i, j)] = val
    # Validate constraints
    # ... [Validation code] ...
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; it may only indicate a feasible solution was found.
- Not checking variable bounds in the solution, leading to misinterpretation of fractional assignments.
- Omitting post-solve validation, which can miss subtle infeasibilities due to numerical tolerances.

# Workflow 2 (Pyomo with HiGHS/CBC Solver)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo, defining abstract sets, parameters, variables, and constraints. This approach separates problem formulation from solver execution and leverages Pyomo's integration with open-source solvers like HiGHS (LP) and CBC (MIP).

### Step 1 - Define Abstract Model
- Create a Pyomo `ConcreteModel` or `AbstractModel`.
- Define `Set` objects for resources and tasks.
- Define `Param` objects for availability, requirement, cost, and capacity data.

### Step 2 - Declare Decision Variables
- Add a `Var` indexed over resource and task sets with domain `pyo.NonNegativeReals` for continuous problems.
- For integer assignments, use domain `pyo.NonNegativeIntegers`.

### Step 3 - Declare Constraints via Rules
- **Resource Capacity**: Define a `Constraint` indexed over resources using a rule that sums over tasks.
- **Demand Satisfaction**: Define a `Constraint` indexed over tasks using a rule that sums over resources.
- **Assignment Capacity**: Define a `Constraint` indexed over both resources and tasks.

### Step 4 - Define Objective
- Create an `Objective` with sense `minimize`.
- Use a summation expression over all cost parameters and variables.

### Formulation Template
```json
{
  "sets": [
    {"name": "R", "description": "Set of resources"},
    {"name": "T", "description": "Set of tasks"}
  ],
  "parameters": [
    {"name": "availability", "index": "R", "type": "float"},
    {"name": "requirement", "index": "T", "type": "float"},
    {"name": "cost", "index": ["R", "T"], "type": "float"},
    {"name": "capacity", "index": ["R", "T"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["R", "T"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum(cost[i,j] * x[i,j] for i in R for j in T)"
  },
  "constraints": [
    {"name": "resource_capacity", "rule": "sum(x[i,j] for j in T) <= availability[i]", "index": "R"},
    {"name": "demand_satisfaction", "rule": "sum(x[i,j] for i in R) == requirement[j]", "index": "T"},
    {"name": "assignment_capacity", "rule": "x[i,j] <= capacity[i,j]", "index": ["R", "T"]}
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters in constraint rules, leading to `KeyError` or silent rule skipping.
- Using mutable default arguments (like lists) in Pyomo rule functions.
- Forgetting to initialize all parameters before solving, which causes model instantiation errors.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with data, solve it using a solver factory (HiGHS for LP, CBC for MIP), rigorously check termination conditions, and extract the solution for validation and reporting.

### Step 1 - Instantiate Model and Select Solver
- If using an `AbstractModel`, create a data dictionary and instantiate it.
- Create a solver object via `SolverFactory('highs')` for LP or `SolverFactory('cbc')` for MIP.

### Step 2 - Configure Solver and Solve
- Set solver options such as time limit (`seconds`), optimality gap (`ratio`), and number of threads.
- Call `solver.solve(model, tee=False)` to execute the optimization, capturing the results object.

### Step 3 - Verify Solution Status
- Import `SolverStatus` and `TerminationCondition` from `pyomo.opt`.
- Check if `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.
- Handle other termination conditions (e.g., `infeasible`, `unbounded`) appropriately.

### Step 4 - Extract and Verify Solution
- If successful, retrieve the objective value via `pyo.value(model.obj)`.
- Iterate through model variables to extract non-zero assignments.
- Programmatically verify constraint satisfaction within tolerance.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build model (follow Modeling Stage steps)
model = pyo.ConcreteModel()
# ... [Model definition code] ...

# 2. Select and configure solver
solver = pyo.SolverFactory('highs')  # Use 'cbc' for MIP
solver.options['time_limit'] = 30
# solver.options['ratio'] = 1e-8  # Optional: tighten optimality gap

# 3. Solve and check status
results = solver.solve(model, tee=False)
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = float(pyo.value(model.obj))
    # Extract variable values
    assignments = {}
    for i in model.R:
        for j in model.T:
            val = model.x[i, j].value
            if val is not None and val > 1e-6:
                assignments[(i, j)] = val
    # Validate constraints
    # ... [Validation code] ...
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (found optimal solution).
- Not converting the objective value to a float, leaving it as a Pyomo expression type.
- Attempting to access `.value` on variables before checking if a solution exists, leading to `AttributeError`.
