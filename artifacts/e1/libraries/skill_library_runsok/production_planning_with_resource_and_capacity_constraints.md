---
name: Production Planning with Resource and Capacity Constraints
description: |
  Model and solve production planning problems with linear profit, individual capacity bounds, and a shared resource constraint using continuous or integer decision variables.
---

# Workflow 1 (OR-Tools Backend)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program (LP) or integer program (IP) using the OR-Tools Python wrapper. Leverage efficient variable creation with built-in bounds and a direct API for adding constraints and setting objectives.

### Step 1 - Define Data Structures
- Organize problem parameters as parallel lists or arrays indexed by item/product ID.
- Store profit per unit, resource consumption per unit, and individual production capacity limits.
- Define the total available resource as a scalar.

### Step 2 - Create Decision Variables
- Use `solver.NumVar(lower_bound, upper_bound, name)` for continuous production quantities.
- Use `solver.IntVar(lower_bound, upper_bound, name)` for integer production quantities.
- Set the lower bound to 0 for non-negativity and the upper bound to the individual capacity limit.

### Step 3 - Formulate the Objective
- Create an objective object: `objective = solver.Objective()`.
- For each variable, set its coefficient to the corresponding profit per unit: `objective.SetCoefficient(x[i], profit[i])`.
- Specify maximization: `objective.SetMaximization()`.

### Step 4 - Add Constraints
- **Shared Resource Constraint**: Create a linear expression summing `resource_consumption[i] * x[i]` across all items. Add the constraint: `solver.Add(sum_expr <= total_resource)`.
- Individual upper bounds are already enforced via variable creation; avoid adding redundant constraints.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": ["profit_i", "resource_consumption_i", "max_production_i", "total_resource"],
  "decision_variables": ["x_i"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_i * x_i for i in I)"
  },
  "constraints": [
    "sum(resource_consumption_i * x_i for i in I) <= total_resource"
  ]
}
```

### Common Pitfalls
- Adding explicit `x[i] <= max_production[i]` constraints when these bounds are already set in `NumVar`/`IntVar`, which creates unnecessary model overhead.
- Forgetting to check if the solver was created successfully (`solver` is not `None`).
- Using the wrong solver backend (e.g., `GLOP` for integer problems).

## Solving stage

### Strategy Overview
Select the appropriate OR-Tools solver backend, solve the model, and rigorously check the solution status before extracting and validating results.

### Step 1 - Initialize Solver
- For continuous LP: `solver = pywraplp.Solver.CreateSolver("GLOP")`.
- For integer IP/MIP: `solver = pywraplp.Solver.CreateSolver("CBC")` or `"SCIP"`.
- Configure performance settings: `solver.SetTimeLimit(time_limit_ms)` and `solver.SetNumThreads(num_threads)`.

### Step 2 - Solve and Check Status
- Execute the solve: `status = solver.Solve()`.
- Verify the status is `solver.OPTIMAL` or `solver.FEASIBLE` before proceeding. Handle other statuses (e.g., `INFEASIBLE`) with structured error output.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value: `total_profit = objective.Value()`.
- Extract production quantities: `production_quantities = [x[i].solution_value() for i in range(n_items)]`.
- Calculate derived metrics (e.g., total resource used) to verify constraint satisfaction.
- For integer solutions, cast variable values to integers.

### Step 4 - Perform Post-Solution Analysis
- Compute profit-to-resource ratios (`profit[i]/resource_consumption[i]`) to understand the solution structure.
- Identify binding constraints by checking slack/residuals.
- Output key results and diagnostics in a clear, machine-parsable format.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Data: profit, resource_consumption, max_production, total_resource
n_items = len(profit)
solver = pywraplp.Solver.CreateSolver("GLOP")  # Use "CBC" for integer
if not solver:
    raise RuntimeError("Solver creation failed")

# Variables with built-in bounds
x = [solver.NumVar(0, max_production[i], f"x_{i}") for i in range(n_items)]

# Resource constraint
resource_expr = sum(resource_consumption[i] * x[i] for i in range(n_items))
solver.Add(resource_expr <= total_resource)

# Objective
objective = solver.Objective()
for i in range(n_items):
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# Solve
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_profit = objective.Value()
    quantities = [x[i].solution_value() for i in range(n_items)]
    # Validation and output
else:
    # Handle failure
```

### Common Pitfalls
- Not using tolerance when checking if a variable is at its bound (e.g., `abs(val - bound) < 1e-6`).
- Assuming `FEASIBLE` status implies optimality; always prefer `OPTIMAL`.
- Neglecting to compute and verify derived metrics, leading to undetected constraint violations.

# Workflow 2 (Pyomo Backend)

## Modeling stage

### Strategy Overview
Structure the problem using Pyomo's abstract modeling capabilities. Define sets, parameters, variables, objectives, and constraints in a declarative style, enabling solver independence and clear separation of data and model logic.

### Step 1 - Define Sets and Parameters
- Create a Pyomo `Set` (e.g., `model.I`) to index items/products.
- Define `Param` objects for profit, resource consumption, and individual capacity limits, indexed by the set.
- Store the total resource as a scalar parameter.

### Step 2 - Create Decision Variables
- Instantiate variables: `model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)` for continuous production.
- For integer production, use `domain=pyo.NonNegativeIntegers`.
- Apply individual upper bounds via a constraint rule or variable bounds attribute.

### Step 3 - Formulate the Objective
- Define the objective as a linear expression: `model.obj = pyo.Objective(expr=sum(model.profit[i] * model.x[i] for i in model.I), sense=pyo.maximize)`.

### Step 4 - Add Constraints
- **Shared Resource Constraint**: `model.resource_con = pyo.Constraint(expr=sum(model.resource_consumption[i] * model.x[i] for i in model.I) <= model.total_resource)`.
- **Individual Upper Bounds**: `model.cap_con = pyo.Constraint(model.I, rule=lambda m, i: m.x[i] <= m.max_production[i])`.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": ["profit_i", "resource_consumption_i", "max_production_i", "total_resource"],
  "decision_variables": ["x_i"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_i * x_i for i in I)"
  },
  "constraints": [
    "sum(resource_consumption_i * x_i for i in I) <= total_resource",
    "x_i <= max_production_i for all i in I"
  ]
}
```

### Common Pitfalls
- Using reserved Python/Pyomo keywords (e.g., `items`, `sum`) as component names.
- Forgetting to initialize parameters before solving, leading to uninitialized value errors.
- Applying individual upper bounds via variable bounds (`bounds=(0, max_production[i])`) and also adding explicit constraints, causing duplication.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with various solvers (e.g., HiGHS, CBC). Configure solver options, solve the model, and implement robust checks on solver status and termination conditions.

### Step 1 - Select and Configure Solver
- For continuous LP: `solver = pyo.SolverFactory("highs")` or `"cbc"`.
- For integer MIP: `solver = pyo.SolverFactory("cbc")` or `"highs"`.
- Set practical options: `solver.options["time_limit"] = 30`, `solver.options["threads"] = 4`. For MIP, set `"ratio"` or `"mip_rel_gap"` for optimality tolerance.

### Step 2 - Solve and Verify Status
- Execute: `results = solver.solve(model, tee=False)`.
- Import and check: `from pyomo.opt import SolverStatus, TerminationCondition`.
- Ensure `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `TerminationCondition.optimal` or `.feasible`.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value: `total_profit = pyo.value(model.obj)`.
- Extract variable values: `quantities = [pyo.value(model.x[i]) for i in model.I]`.
- For integer variables, cast to `int()`.
- Compute total resource usage and compare against the limit to verify feasibility.

### Step 4 - Analyze and Output Results
- Calculate profit-to-resource ratios to validate solution intuition.
- Identify which constraints are binding.
- Output results in both human-readable and structured machine-readable formats.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Data dictionaries/lists: profit, resource_consumption, max_production, total_resource
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(n_items))

model.profit = pyo.Param(model.I, initialize=profit_dict)
model.resource_consumption = pyo.Param(model.I, initialize=resource_dict)
model.max_production = pyo.Param(model.I, initialize=capacity_dict)
model.total_resource = pyo.Param(initialize=total_resource)

model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)  # or NonNegativeIntegers

def obj_rule(m):
    return sum(m.profit[i] * m.x[i] for i in m.I)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

def resource_rule(m):
    return sum(m.resource_consumption[i] * m.x[i] for i in m.I) <= m.total_resource
model.resource_con = pyo.Constraint(rule=resource_rule)

def capacity_rule(m, i):
    return m.x[i] <= m.max_production[i]
model.cap_con = pyo.Constraint(model.I, rule=capacity_rule)

solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_profit = pyo.value(model.obj)
    quantities = [pyo.value(model.x[i]) for i in model.I]
    # Validation and output
else:
    # Handle failure
```

### Common Pitfalls
- Not importing `SolverStatus` and `TerminationCondition` for proper status checking.
- Accessing `pyo.value()` on variables before verifying the solve was successful, causing errors.
- Using `tee=True` in production without capturing or suppressing its output.
