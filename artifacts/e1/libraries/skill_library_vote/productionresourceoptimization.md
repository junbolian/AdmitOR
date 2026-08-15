---
name: ProductionResourceOptimization
description: |
  Model and solve production planning problems with linear profit maximization under resource and individual capacity constraints, supporting both continuous and integer variable domains.
---

# Workflow 1 (OR-Tools LP/MIP)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using the OR-Tools linear solver wrapper. Variables are defined with explicit upper bounds, and constraints are added directly to the solver object. This workflow is efficient for direct, procedural model building.

### Step 1 - Define Data Structures
- Organize problem parameters into parallel arrays or lists indexed by product/item.
- Store `profit_per_unit`, `resource_consumption_per_unit`, and `individual_capacity` for each item.
- Define a scalar `total_resource_available` for the shared constraint.

### Step 2 - Instantiate Solver and Variables
- Create a solver instance using `pywraplp.Solver.CreateSolver()`. Choose `"GLOP"` for continuous LP or `"SCIP"/"CBC"` for MIP.
- Create decision variables in a list using `solver.NumVar(lb, ub, name)` for continuous or `solver.IntVar(lb, ub, name)` for integer domains. Set `lb=0` and `ub=individual_capacity[i]`.

### Step 3 - Add Global Resource Constraint
- Add a single linear inequality constraint: `solver.Add(sum(resource_consumption[i] * x[i] for i in items) <= total_resource_available)`.
- Use a generator expression for efficient summation.

### Step 4 - Set Linear Maximization Objective
- Instantiate the objective with `solver.Objective()`.
- Iterate through variables, setting coefficients with `objective.SetCoefficient(x[i], profit_per_unit[i])`.
- Call `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["I_items"],
  "parameters": [
    {"name": "profit", "index": "I_items"},
    {"name": "resource_consumption", "index": "I_items"},
    {"name": "capacity", "index": "I_items"},
    {"name": "total_resource", "index": null}
  ],
  "decision_variables": [
    {"name": "x", "index": "I_items", "domain": "NonNegativeReals/Integers", "bounds": "[0, capacity[i]]"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I_items)"
  },
  "constraints": [
    {"name": "resource_limit", "expression": "sum(resource_consumption[i] * x[i] for i in I_items) <= total_resource"}
  ]
}
```

### Common Pitfalls
- Confusing solver backends: using `"GLOP"` for integer problems will ignore integrality.
- Forgetting to set the objective sense to maximization.
- Hard-coding parameter values inside loops instead of using data arrays, reducing reusability.
- Not verifying that individual capacity bounds are non-negative.

## Solving stage

### Strategy Overview
Solve the built model using the configured OR-Tools solver. Check the solution status rigorously and extract results for validation and analysis. This stage focuses on reliable solution retrieval.

### Step 1 - Execute Solve and Check Status
- Call `status = solver.Solve()`.
- Verify success with `status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE)`. Handle other statuses (INFEASIBLE, UNBOUNDED) with appropriate error messages.

### Step 2 - Extract and Validate Solution
- Retrieve the total profit with `objective.Value()`.
- Extract each production quantity with `x[i].solution_value()`.
- Calculate the total resource used from the solution: `sum(resource_consumption[i] * solution_value[i])`.
- Assert this calculated usage satisfies the global constraint (within a small tolerance).

### Step 3 - Analyze and Report Results
- Compute resource utilization percentage: `(total_resource_used / total_resource_available) * 100`.
- Identify items produced at their capacity bounds versus fractional/interior levels.
- Output a structured summary including status, objective value, key metrics, and non-zero production quantities.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Data (placeholders)
profit = [...]  # per unit profit
resource_cons = [...]  # resource consumption per unit
capacity = [...]  # individual production limits
total_resource = ...  # global resource availability
n_items = len(profit)

# 2. Model Building
solver = pywraplp.Solver.CreateSolver("GLOP")  # Use "SCIP" for MIP
x = [solver.NumVar(0.0, capacity[i], f'x_{i}') for i in range(n_items)]

# 3. Global Resource Constraint
solver.Add(sum(resource_cons[i] * x[i] for i in range(n_items)) <= total_resource)

# 4. Objective
objective = solver.Objective()
for i in range(n_items):
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# 5. Solve & Check
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_profit = objective.Value()
    production = [x[i].solution_value() for i in range(n_items)]
    # ... validation and analysis
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming `OPTIMAL` status for all feasible solutions; `FEASIBLE` is acceptable for early termination.
- Not using a tolerance (e.g., `1e-6`) when checking constraint satisfaction due to floating-point arithmetic.
- Omitting solver time or thread configuration for larger problems, risking long runtimes.

# Workflow 2 (Pyomo with Algebraic Modeling)

## Modeling stage

### Strategy Overview
Formulate the problem using Pyomo's abstract or concrete modeling paradigm. Define sets, parameters, variables, and constraints using declarative rules. This workflow emphasizes model clarity, scalability, and separation of data from structure.

### Step 1 - Define Abstract Model Structure
- Create a `ConcreteModel` or `AbstractModel`.
- Define a Set `model.I` to index all items/products.
- Define `Param` objects for `profit`, `resource_consumption`, `capacity` (indexed by `model.I`), and `total_resource` (a scalar).

### Step 2 - Declare Decision Variables
- Create a variable `model.x` indexed by `model.I`.
- Set the domain to `pyo.NonNegativeReals` for continuous production or `pyo.NonNegativeIntegers` for discrete units.
- Individual upper bounds are enforced later via constraints, not in the variable declaration.

### Step 3 - Formulate Objective Function
- Define the objective as `model.obj = pyo.Objective(expr=sum(model.profit[i] * model.x[i] for i in model.I), sense=pyo.maximize)`.

### Step 4 - Implement Constraints via Rules
- Add the global resource constraint: `model.resource_limit = pyo.Constraint(expr=sum(model.resource_consumption[i] * model.x[i] for i in model.I) <= model.total_resource)`.
- Add individual capacity constraints using a rule: `model.capacity_constraints = pyo.Constraint(model.I, rule=lambda m, i: m.x[i] <= m.capacity[i])`.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": [
    {"name": "profit", "index": "I"},
    {"name": "resource_consumption", "index": "I"},
    {"name": "capacity", "index": "I"},
    {"name": "total_resource", "index": null}
  ],
  "decision_variables": [
    {"name": "x", "index": "I", "domain": "NonNegativeReals/Integers"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    {"name": "resource_limit", "expression": "sum(resource_consumption[i] * x[i] for i in I) <= total_resource"},
    {"name": "capacity", "index": "I", "expression": "x[i] <= capacity[i]"}
  ]
}
```

### Common Pitfalls
- Using reserved keywords (e.g., `model.items`) for set names, causing attribute conflicts.
- Hard-coding parameter values inside constraint rules instead of referencing `Param` objects.
- Forgetting to initialize `Param` dictionaries correctly when using `ConcreteModel`.
- Creating the model without separating data, making it less reusable for different instances.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., CBC, HiGHS). Configure solver options for performance, check termination conditions rigorously, and extract solution values using `pyo.value()`. This workflow is robust for production use.

### Step 1 - Configure and Execute Solver
- Instantiate a solver with `pyo.SolverFactory("solver_name")`, e.g., `"highs"` for LP or `"cbc"` for MIP.
- Set practical options: `solver.options["seconds"] = time_limit`, `solver.options["threads"] = thread_count`. For MIP, set `solver.options["ratio"] = gap_tolerance`.
- Call `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Solver Status and Termination
- Check `results.solver.status` equals `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`. Handle other conditions appropriately.

### Step 3 - Extract, Compute, and Analyze
- Retrieve the objective value: `total_profit = pyo.value(model.obj)`.
- Extract production quantities: `production = {i: pyo.value(model.x[i]) for i in model.I}`.
- Calculate derived metrics like total resource usage from the solution to verify constraints.
- Analyze binding constraints and profit-to-resource ratios to understand the solution.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Data (placeholders)
profit_dict = {i: val for i, val in enumerate([...])}
resource_cons_dict = {i: val for i, val in enumerate([...])}
capacity_dict = {i: val for i, val in enumerate([...])}
total_resource = ...

# 2. Model Building
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=profit_dict.keys())
model.profit = pyo.Param(model.I, initialize=profit_dict)
model.resource_cons = pyo.Param(model.I, initialize=resource_cons_dict)
model.capacity = pyo.Param(model.I, initialize=capacity_dict)
model.total_resource = pyo.Param(initialize=total_resource)

model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)  # or NonNegativeIntegers

model.obj = pyo.Objective(
    expr=sum(model.profit[i] * model.x[i] for i in model.I),
    sense=pyo.maximize
)
model.resource_limit = pyo.Constraint(
    expr=sum(model.resource_cons[i] * model.x[i] for i in model.I) <= model.total_resource
)
def capacity_rule(m, i):
    return m.x[i] <= m.capacity[i]
model.capacity_constraints = pyo.Constraint(model.I, rule=capacity_rule)

# 3. Solving
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
results = solver.solve(model, tee=False)

# 4. Check and Extract
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_profit = pyo.value(model.obj)
    # ... further processing
else:
    print(f"Solve failed: {results.solver.status}: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of suboptimal or error states.
- Using `pyo.value()` on variables or expressions before verifying a solution exists, which may raise errors.
- Over-configuring solver options (e.g., time limit, threads) for trivial problems, adding unnecessary overhead.
- Creating overly verbose output that duplicates information already present in the model or results object.
