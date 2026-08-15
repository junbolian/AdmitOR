---
name: Resource-Constrained Linear Production Planning
description: |
  Model and solve linear maximization problems with nonnegative continuous variables, linear inequality constraints, and individual upper bounds, using either direct solver APIs or algebraic modeling frameworks.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' direct solver API for a procedural, solver-centric modeling approach. It is ideal for rapid prototyping and when solver-specific performance tuning is required.

### Step 1 - Define Problem Data
- Store all input parameters as separate lists or dictionaries, decoupled from the model logic.
- Key parameters include: `profit_per_unit`, `resource_consumption_per_unit`, `max_production_per_item`, and `total_resource_limit`.

### Step 2 - Initialize Solver and Create Variables
- Instantiate a solver object (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Create decision variables in a loop, setting their lower bound (0) and individual upper bound (`max_production_per_item[i]`) directly in the constructor (e.g., `solver.NumVar(0, ub, name)`). This reduces the number of explicit constraints.

### Step 3 - Formulate Global Resource Constraint
- Create a linear expression summing the total resource consumption: `sum(resource_consumption_per_unit[i] * x[i])`.
- Add this as a single inequality constraint (`<= total_resource_limit`) to the solver.

### Step 4 - Set Linear Maximization Objective
- Build the objective function as a linear expression: `sum(profit_per_unit[i] * x[i])`.
- Set the objective sense to maximization and attach it to the solver.

### Formulation Template
```json
{
  "sets": ["Items"],
  "parameters": {
    "profit_per_unit": {"index": "Items", "type": "float"},
    "resource_consumption_per_unit": {"index": "Items", "type": "float"},
    "max_production_per_item": {"index": "Items", "type": "float"},
    "total_resource_limit": {"type": "float"}
  },
  "decision_variables": {
    "production_quantity": {"index": "Items", "type": "continuous", "lower_bound": 0, "upper_bound": "max_production_per_item"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[i] * production_quantity[i] for i in Items)"
  },
  "constraints": {
    "global_resource": "sum(resource_consumption_per_unit[i] * production_quantity[i] for i in Items) <= total_resource_limit"
  }
}
```

### Common Pitfalls
- Forgetting to set variable bounds in the constructor and adding them as separate constraints, which unnecessarily increases model size.
- Using integer variable types (`IntVar`) when the problem only requires continuous relaxation, which slows down solving.
- Not using a tolerance when checking if a variable's solution value is zero, leading to incorrect post-solution analysis.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' wrapper for LP/MIP solvers (GLOP for LP, CBC/SCIP for MIP). Focus on extracting results, validating feasibility, and performing post-solution analysis.

### Step 1 - Solve and Check Status
- Execute `solver.Solve()`.
- Check the returned status against `pywraplp.Solver.OPTIMAL` or `FEASIBLE` to determine success.

### Step 2 - Extract and Validate Solution
- If successful, retrieve the objective value via `solver.Objective().Value()`.
- Iterate through variables to get their solution values (`var.solution_value()`).
- Compute derived metrics (e.g., total resource used) from the solution to verify all constraints are satisfied.

### Step 3 - Perform Post-Optimality Analysis
- Calculate key ratios like profit per unit resource (`profit_per_unit[i] / resource_consumption_per_unit[i]`) for all items.
- Compare these ratios against the solution to build intuition about the solver's decisions (e.g., items with higher ratios are prioritized).

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

# 1. Data Preparation
profit = [...]  # list of profit_per_unit
resource_cons = [...]  # list of resource_consumption_per_unit
max_prod = [...]  # list of max_production_per_item
resource_limit = ...  # total_resource_limit
n_items = len(profit)

# 2. Solver and Variable Creation
solver = pywraplp.Solver.CreateSolver("GLOP")  # Use "CBC" for MIP
x = [solver.NumVar(0, max_prod[i], f'x_{i}') for i in range(n_items)]

# 3. Global Constraint
resource_expr = sum(resource_cons[i] * x[i] for i in range(n_items))
solver.Add(resource_expr <= resource_limit)

# 4. Objective
objective = solver.Objective()
for i in range(n_items):
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
TOLERANCE = 1e-6

if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_profit = objective.Value()
    total_resource_used = sum(resource_cons[i] * x[i].solution_value() for i in range(n_items))
    # Validation and analysis
    print(f"RESULT:{total_profit}")
    # Optional: Print detailed variable values and ratios
else:
    print("SOLVE_FAILED")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid but non-optimal solutions.
- Assuming the solver automatically loads the solution; extraction always requires calling `.solution_value()` on variables.
- Setting an inappropriate time limit or solver parameters for the problem size, leading to premature termination.

# Workflow 2 (Algebraic Modeling - Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo algebraic modeling language to create a declarative, solver-independent model. It emphasizes separation of data and model logic, improving maintainability and scalability.

### Step 1 - Define Abstract Sets and Parameters
- Declare a Pyomo `Set` (e.g., `model.I`) to index all items/products.
- Use Pyomo `Param` objects to inject problem data (`profit`, `resource_rate`, `max_production`, `resource_limit`) into the model, keeping the formulation clean.

### Step 2 - Create Non-Negative Continuous Variables
- Define a Pyomo `Var` object (e.g., `model.x`) indexed over the set, with `domain=pyo.NonNegativeReals`.

### Step 3 - Formulate Objective and Constraints
- Define the objective using a `pyo.Objective` rule that sums `profit[i] * model.x[i]` with `sense=pyo.maximize`.
- Create two constraint types:
    1. A single global resource constraint using a `pyo.Constraint` rule summing `resource_rate[i] * model.x[i]`.
    2. Indexed individual upper bound constraints (`model.x[i] <= max_production[i]`) using a rule or a construction loop.

### Formulation Template
```json
{
  "sets": ["Items"],
  "parameters": {
    "profit": {"index": "Items", "type": "float"},
    "resource_rate": {"index": "Items", "type": "float"},
    "max_production": {"index": "Items", "type": "float"},
    "resource_limit": {"type": "float"}
  },
  "decision_variables": {
    "x": {"index": "Items", "type": "continuous", "domain": "NonNegativeReals"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in Items)"
  },
  "constraints": {
    "resource": "sum(resource_rate[i] * x[i] for i in Items) <= resource_limit",
    "upper_bounds": "x[i] <= max_production[i] for i in Items"
  }
}
```

### Common Pitfalls
- Mixing Python data structures (lists/dicts) directly in Pyomo expression rules without using `model.Param`, which breaks model abstraction.
- Forgetting to deactivate the `load_solutions` option when debugging or performing advanced solve procedures, leading to unexpected behavior.
- Creating constraints with incorrect indexing, resulting in missing or extra constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external LP solver (e.g., HiGHS, CBC) via Pyomo's `SolverFactory`. The focus is on robust solver status checking, solution loading, and validation.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")`.
- Set solver options like `time_limit` and `threads` for performance control.
- Call `results = solver.solve(model, tee=False)`.

### Step 2 - Rigorous Status and Termination Checking
- Inspect `results.solver.status` (should be `SolverStatus.ok`) and `results.solver.termination_condition` (should be `optimal` or `feasible`).
- If `load_solutions=False` was used, explicitly load the solution with `model.solutions.load_from(results)`.

### Step 3 - Extract, Validate, and Analyze
- Retrieve the objective value using `pyo.value(model.obj)`.
- Recompute derived quantities (e.g., total resource used) from the variable values (`pyo.value(model.x[i])`) to validate constraint adherence.
- Perform post-optimality analysis by calculating profit-to-resource ratios.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

# 1. Data (external to model)
profit_data = {...}  # dict: item -> profit
resource_data = {...}  # dict: item -> resource_rate
max_prod_data = {...}  # dict: item -> max_production
resource_limit = ...

# 2. Concrete Model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=profit_data.keys())  # Set of Items

# 3. Parameters
model.profit = pyo.Param(model.I, initialize=profit_data)
model.resource_rate = pyo.Param(model.I, initialize=resource_data)
model.max_production = pyo.Param(model.I, initialize=max_prod_data)
model.resource_limit = pyo.Param(initialize=resource_limit)

# 4. Variables
model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)

# 5. Objective
def obj_rule(m):
    return sum(m.profit[i] * m.x[i] for i in m.I)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# 6. Constraints
def resource_constraint_rule(m):
    return sum(m.resource_rate[i] * m.x[i] for i in m.I) <= m.resource_limit
model.resource_constraint = pyo.Constraint(rule=resource_constraint_rule)

def upper_bound_rule(m, i):
    return m.x[i] <= m.max_production[i]
model.upper_bounds = pyo.Constraint(model.I, rule=upper_bound_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    total_profit = pyo.value(model.obj)
    # Validation
    total_used = sum(pyo.value(model.x[i]) * resource_data[i] for i in model.I)
    print(f"RESULT:{total_profit}")
else:
    print("SOLVE_FAILED")
    # Optional: Output structured failure info
```

### Common Pitfalls
- Assuming a successful `solve()` call automatically means an optimal solution was found; always check the termination condition.
- Accessing variable values (`pyo.value(model.x[i])`) before ensuring the solution is loaded, which raises an error.
- Not using `pyo.Param` for data, which makes the model less flexible and harder to update with new data.
