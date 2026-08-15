---
name: Continuous Resource Assignment with Capacity Limits
description: |
  Model and solve linear assignment problems with continuous non-negative variables, supply/demand constraints, and per-assignment limits using open-source solvers.

---

# Workflow 1 (OR-Tools LP Solver)

## Modeling stage

### Strategy Overview
Formulate a linear programming model for resource assignment using OR-Tools' direct API. This workflow is efficient for prototyping and deployment where a lightweight, integrated solver interface is preferred.

### Step 1 - Define Data Structures
- Organize supply (source) and demand (destination) indices as lists or ranges.
- Store supply capacities, demand requirements, per-assignment cost coefficients, and individual assignment limits in nested data structures (e.g., lists of lists, dictionaries) for clear indexing.
- Example: `supply_cap[i]`, `demand_req[j]`, `cost[i][j]`, `limit[i][j]`.

### Step 2 - Create Decision Variables
- Instantiate continuous non-negative variables `x[i][j]` representing the assignment amount from source `i` to destination `j`.
- Set variable bounds directly during creation: lower bound = 0, upper bound = `limit[i][j]` (or a large value if no limit).
- Use `solver.NumVar(lb, ub, name)`.

### Step 3 - Formulate Supply and Demand Constraints
- For each source `i`, add a constraint: `sum(x[i][j] for all j) <= supply_cap[i]`.
- For each destination `j`, add a constraint: `sum(x[i][j] for all i) == demand_req[j]`.
- Use `solver.Add()` or `solver.Constraint()` with appropriate lower/upper bounds.

### Step 4 - Define Linear Cost Objective
- Construct the objective as the sum of `cost[i][j] * x[i][j]` over all `i`, `j`.
- Set the objective sense to minimization using `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["I (sources)", "J (destinations)"],
  "parameters": [
    "supply_cap[i] (capacity per source)",
    "demand_req[j] (requirement per destination)",
    "cost[i][j] (unit cost per assignment)",
    "limit[i][j] (maximum per assignment)"
  ],
  "decision_variables": ["x[i][j] (continuous, non-negative assignment amount)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i][j] for j in J) <= supply_cap[i], for each i in I",
    "sum(x[i][j] for i in I) == demand_req[j], for each j in J",
    "x[i][j] <= limit[i][j], for each i in I, j in J (often handled via variable bounds)"
  ]
}
```

### Common Pitfalls
- Forgetting to set an upper bound on variables, leading to unbounded models.
- Using inequality (`>=`) for demand constraints when exact fulfillment (`==`) is required.
- Mismatched indices between data arrays and constraint loops causing silent errors.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' GLOP (for LP) or CBC (for MIP) backend, with explicit solution verification and robust status handling.

### Step 1 - Initialize Solver and Solve
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Invoke `solver.Solve()` and capture the status code.

### Step 2 - Validate Solution Status
- Check if status is `solver.OPTIMAL` or `solver.FEASIBLE`.
- If not, output a structured error message and terminate or attempt a fallback.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value: `objective.Value()`.
- For each variable `x[i][j]`, get its solution value and store if above a tolerance (e.g., `1e-6`).
- Programmatically verify all constraints: recalculate sums for each supply and demand constraint and compare against original parameters within tolerance.

### Step 4 - Report Results
- Print a summary of non-zero assignments, including source, destination, amount, and cost contribution.
- Output the total cost in a parseable format (e.g., `RESULT:<value>`).

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver('GLOP')
x = {}
for i in I:
    for j in J:
        x[i, j] = solver.NumVar(0, limit[i][j], f'x_{i}_{j}')
# Add constraints
for i in I:
    ct = solver.Constraint(0, supply_cap[i])
    for j in J:
        ct.SetCoefficient(x[i, j], 1)
for j in J:
    ct = solver.Constraint(demand_req[j], demand_req[j])
    for i in I:
        ct.SetCoefficient(x[i, j], 1)
# Set objective
objective = solver.Objective()
for i in I:
    for j in J:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # Verification loop (optional but recommended)
    for i in I:
        total_assigned = sum(x[i, j].solution_value() for j in J)
        assert total_assigned <= supply_cap[i] + 1e-6
    print(f'RESULT:{total_cost}')
else:
    print(f'ERROR:Solver failed with status {status}')
```

### Common Pitfalls
- Not checking solver status before accessing solution values, risking runtime errors.
- Using loose tolerances for equality constraints leading to incorrect feasibility checks.
- Overlooking that per-assignment limits are enforced by variable bounds, not explicit constraints.

# Workflow 2 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Build a declarative model using Pyomo, separating problem definition from solver specifics. This workflow offers flexibility and portability across multiple solvers (e.g., HiGHS, CBC).

### Step 1 - Declare Sets and Parameters
- Define Pyomo `Set` objects for sources (`I`) and destinations (`J`).
- Declare `Param` objects or use standard Python dictionaries for `supply_cap`, `demand_req`, `cost`, and `limit` data, indexed by the appropriate sets.

### Step 2 - Define Variables with Domain
- Create a Pyomo `Var` indexed over `I` and `J` with `domain=pyo.NonNegativeReals`.
- Optionally set variable upper bounds via a rule or later using `.setub()`.

### Step 3 - Construct Constraints via Rules
- Define a rule for supply constraints: for each `i` in `I`, `sum(model.x[i, j] for j in J) <= supply_cap[i]`.
- Define a rule for demand constraints: for each `j` in `J`, `sum(model.x[i, j] for i in I) == demand_req[j]`.
- Define a rule for per-assignment limits: for each `(i, j)`, `model.x[i, j] <= limit[i, j]`.

### Step 4 - Formulate Objective Expression
- Create an `Objective` with expression `sum(cost[i, j] * model.x[i, j] for i in I for j in J)` and `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["I (sources)", "J (destinations)"],
  "parameters": [
    "supply_cap[i] (capacity per source)",
    "demand_req[j] (requirement per destination)",
    "cost[i][j] (unit cost per assignment)",
    "limit[i][j] (maximum per assignment)"
  ],
  "decision_variables": ["x[i][j] (continuous, non-negative assignment amount)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i][j] for j in J) <= supply_cap[i], for each i in I",
    "sum(x[i][j] for i in I) == demand_req[j], for each j in J",
    "x[i][j] <= limit[i][j], for each i in I, j in J"
  ]
}
```

### Common Pitfalls
- Using mutable default arguments in constraint rules.
- Incorrectly indexing parameters within rules, leading to `KeyError`.
- Forgetting to deactivate the `load_solutions` flag when solver does not automatically load results.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured open-source solver (e.g., HiGHS, CBC), with careful handling of solver status and manual solution loading if needed.

### Step 1 - Configure and Execute Solver
- Instantiate a solver factory: `solver = pyo.SolverFactory('highs')` or `'cbc'`.
- Set solver options: `solver.options['time_limit'] = 30`, `solver.options['ratio'] = 0.0`.
- Solve with `load_solutions=False`: `results = solver.solve(model, load_solutions=False)`.

### Step 2 - Check Termination Status
- Verify `results.solver.status == pyo.SolverStatus.ok`.
- Verify `results.solver.termination_condition` is `pyo.TerminationCondition.optimal` or `.feasible`.
- If checks fail, output a structured error (e.g., JSON) and abort.

### Step 3 - Load and Extract Solution
- If status is good, load the solution: `model.solutions.load_from(results)`.
- Retrieve the objective value: `float(pyo.value(model.obj))`.
- Iterate over variables `model.x[i, j]` and collect values above a tolerance.

### Step 4 - Post-Solution Validation
- Recalculate totals for each supply and demand constraint to verify satisfaction within tolerance.
- Check each assignment against its individual limit.
- Print a detailed assignment report and the total cost.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I)
model.J = pyo.Set(initialize=J)
model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
def supply_rule(m, i):
    return sum(m.x[i, j] for j in m.J) <= supply_cap[i]
model.supply_con = pyo.Constraint(model.I, rule=supply_rule)
def demand_rule(m, j):
    return sum(m.x[i, j] for i in m.I) == demand_req[j]
model.demand_con = pyo.Constraint(model.J, rule=demand_rule)
def limit_rule(m, i, j):
    return m.x[i, j] <= limit[i, j]
model.limit_con = pyo.Constraint(model.I, model.J, rule=limit_rule)
model.obj = pyo.Objective(expr=sum(cost[i, j] * model.x[i, j] for i in model.I for j in model.J), sense=pyo.minimize)

# Solve
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, load_solutions=False)
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    model.solutions.load_from(results)
    total_cost = float(pyo.value(model.obj))
    # Verification loop
    for i in model.I:
        total_assigned = sum(pyo.value(model.x[i, j]) for j in model.J)
        assert total_assigned <= supply_cap[i] + 1e-6
    print(f'RESULT:{total_cost}')
else:
    print(f'ERROR:{{"status": "{status}", "termination": "{term}"}}')
```

### Common Pitfalls
- Assuming the solver automatically loads the solution; always use `load_solutions=False` and check status first.
- Not setting `ratio=0.0` for LP problems, potentially accepting suboptimal solutions.
- Using too many threads (`threads` option) with some solvers, causing initialization failures.
