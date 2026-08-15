---
name: BipartiteFlowAssignment
description: |
  Model and solve balanced bipartite assignment problems with supply exhaustion, demand satisfaction, and per-assignment capacity limits to minimize linear cost.

---

# Workflow 1 (LP Solver with Explicit Variable Bounds)

## Modeling stage

### Strategy Overview
This workflow models the problem as a linear program (LP) using a solver backend that supports variable bounds (e.g., OR-Tools GLOP). It leverages explicit upper bounds on decision variables to enforce per-assignment capacity, simplifying constraint management.

### Step 1 - Define Sets and Parameters
- Define the set of supply nodes `I` (e.g., individuals) and demand nodes `J` (e.g., projects).
- Define parameters: `capacity[i]` for total supply, `demand[j]` for total demand, `cost[i,j]` for unit cost, and `max_assign[i,j]` for per-assignment upper limit.

### Step 2 - Create Decision Variables
- Create continuous, non-negative decision variables `x[i,j]` representing the flow from `i` to `j`.
- Set variable bounds directly: `0 <= x[i,j] <= max_assign[i,j]`. This encodes the per-assignment capacity constraint.

### Step 3 - Formulate Supply and Demand Constraints
- Add a **supply exhaustion constraint** for each `i` in `I`: `sum_{j in J} x[i,j] = capacity[i]`.
- Add a **demand satisfaction constraint** for each `j` in `J`: `sum_{i in I} x[i,j] = demand[j]`.

### Step 4 - Define Linear Objective
- Formulate the objective to minimize total linear cost: `min sum_{i in I} sum_{j in J} cost[i,j] * x[i,j]`.

### Formulation Template
```json
{
  "sets": ["I (supply nodes)", "J (demand nodes)"],
  "parameters": [
    "capacity[i] ∈ ℝ⁺ for i in I",
    "demand[j] ∈ ℝ⁺ for j in J",
    "cost[i,j] ∈ ℝ for i in I, j in J",
    "max_assign[i,j] ∈ ℝ⁺ for i in I, j in J"
  ],
  "decision_variables": ["x[i,j] ∈ ℝ⁺, 0 ≤ x[i,j] ≤ max_assign[i,j]"],
  "objective": {
    "sense": "min",
    "expression": "∑_{i∈I} ∑_{j∈J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "supply_exhaustion_i: ∑_{j∈J} x[i,j] = capacity[i], ∀i∈I",
    "demand_satisfaction_j: ∑_{i∈I} x[i,j] = demand[j], ∀j∈J"
  ]
}
```

### Common Pitfalls
- Forgetting to verify total supply equals total demand (`sum(capacity) == sum(demand)`); an imbalance makes the equality constraints infeasible.
- Setting `max_assign[i,j]` to zero for unavailable assignments, which is correct, but failing to initialize the corresponding `cost[i,j]`, potentially causing solver errors.
- Using loose tolerances when checking constraint satisfaction post-solve; use a strict tolerance (e.g., 1e-6) to validate feasibility.

## Solving stage

### Strategy Overview
Solve the LP using a dedicated linear programming solver (e.g., OR-Tools GLOP) configured for deterministic results. Focus on efficient model building, robust solution status checking, and post-solve validation of all constraints.

### Step 1 - Initialize Solver and Build Model
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Instantiate variables with their lower and upper bounds as defined in the model.
- Add supply and demand constraints by iterating over sets `I` and `J`.
- Set the objective function coefficients.

### Step 2 - Solve and Check Status
- Invoke `solver.Solve()`.
- Check the solver status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.). Proceed only if status indicates success.

### Step 3 - Extract and Validate Solution
- Extract variable values for `x[i,j]` greater than a small tolerance.
- Compute actual supply used per `i` and demand met per `j` to verify constraints are satisfied within tolerance.
- Calculate the total cost from the extracted solution and compare it to the solver's reported objective value.

### Step 4 - Output Results
- Print the optimal objective value with a consistent prefix (e.g., `RESULT: {total_cost}`) for automated parsing.
- Optionally, report a summary of non-zero assignments.

### Code Usage
```python
# Example using OR-Tools' GLOP backend
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')
# 2. Define data placeholders: capacities, demands, costs, max_assign
#    I, J = range(num_supply), range(num_demand)
# 3. Create variables with bounds
x = {}
for i in I:
    for j in J:
        x[i, j] = solver.NumVar(0, max_assign[i][j], f'x_{i}_{j}')
# 4. Add supply constraints
for i in I:
    ct = solver.Constraint(capacity[i], capacity[i])
    for j in J:
        ct.SetCoefficient(x[i, j], 1)
# 5. Add demand constraints
for j in J:
    ct = solver.Constraint(demand[j], demand[j])
    for i in I:
        ct.SetCoefficient(x[i, j], 1)
# 6. Set objective
objective = solver.Objective()
for i in I:
    for j in J:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()
# 7. Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # 8. Validation loop (optional)
    for i in I:
        used = sum(x[i, j].solution_value() for j in J)
        assert abs(used - capacity[i]) < 1e-6
    print(f'RESULT: {total_cost}')
else:
    print('Solver failed', status)
```

### Common Pitfalls
- Not setting solver parameters (like time limits) for reproducibility; always set a random seed if the solver uses one.
- Assuming the solver's `FEASIBLE` status guarantees optimality; for LP, `OPTIMAL` is preferred, but `FEASIBLE` may be acceptable with a note.
- Extracting variable values without checking if the solve was successful first, leading to attribute errors.

# Workflow 2 (Algebraic Modeling with MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses an algebraic modeling language (e.g., Pyomo) to declaratively define the model, separating formulation from solver specifics. It targets mixed-integer programming (MIP) solvers (e.g., CBC) which can also handle LPs, providing flexibility for future integer extensions.

### Step 1 - Declare Abstract Sets and Parameters
- Declare abstract sets `model.I` and `model.J` for supply and demand nodes.
- Declare parameters `model.capacity`, `model.demand`, `model.cost`, and `model.max_limit` using `pyo.Param`.

### Step 2 - Define Variables with Rule-Based Bounds
- Define continuous variables `model.x[i,j]` in the domain `pyo.NonNegativeReals`.
- Implement a bounds rule (or a constraint) to enforce `model.x[i,j] <= model.max_limit[i,j]`.

### Step 3 - Write Constraint Rules
- Define a **supply exhaustion constraint** rule: for each `i`, `sum(model.x[i,j] for j in model.J) == model.capacity[i]`.
- Define a **demand satisfaction constraint** rule: for each `j`, `sum(model.x[i,j] for i in model.I) == model.demand[j]`.

### Step 4 - Define Objective Expression
- Define the objective as a `pyo.Objective` with sense `minimize` and expression `sum(model.cost[i,j] * model.x[i,j] for i in model.I for j in model.J)`.

### Formulation Template
```json
{
  "sets": ["I (supply nodes)", "J (demand nodes)"],
  "parameters": [
    "capacity[i] ∈ ℝ⁺ for i in I",
    "demand[j] ∈ ℝ⁺ for j in J",
    "cost[i,j] ∈ ℝ for i in I, j in J",
    "max_limit[i,j] ∈ ℝ⁺ for i in I, j in J"
  ],
  "decision_variables": ["x[i,j] ∈ ℝ⁺"],
  "objective": {
    "sense": "min",
    "expression": "∑_{i∈I} ∑_{j∈J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "supply_exhaustion_i: ∑_{j∈J} x[i,j] = capacity[i], ∀i∈I",
    "demand_satisfaction_j: ∑_{i∈I} x[i,j] = demand[j], ∀j∈J",
    "per_assignment_capacity_ij: x[i,j] ≤ max_limit[i,j], ∀i∈I, ∀j∈J"
  ]
}
```

### Common Pitfalls
- Using `model.x[i,j] <= model.max_limit[i,j]` as a separate constraint instead of a variable bound can increase problem size unnecessarily; use bounds where the solver supports them.
- Forgetting to initialize all indices of parameters `cost` and `max_limit`; missing data causes key errors during model instantiation.
- Declaring the objective expression inside a loop, which is inefficient; use a single summation over the sets.

## Solving stage

### Strategy Overview
Instantiate the concrete model with provided data, configure a MIP/LP solver (e.g., CBC via Pyomo's SolverFactory), solve with controlled options, and perform detailed post-solution verification and reporting.

### Step 1 - Instantiate Model and Configure Solver
- Populate the abstract model with concrete data (dictionaries or arrays).
- Create a solver object via `SolverFactory("cbc")`.
- Set solver options: `time_limit`, `threads`, and `ratio` (optimality gap) for deterministic performance.

### Step 2 - Solve and Inspect Termination
- Call `solver.solve(model)`.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Validate and Extract Solution
- If solve was successful, extract the objective value via `pyo.value(model.obj)`.
- Implement a verification function that iterates over all `i` and `j` to check supply, demand, and capacity constraints within tolerance.
- Optionally, generate a detailed report of non-zero assignments and their costs.

### Step 4 - Output Structured Results
- Print the optimal cost in a parseable format.
- Optionally, print validation tables showing demand/capacity versus assigned amounts.

### Code Usage
```python
# Example using Pyomo with CBC solver
import pyomo.environ as pyo
import random

# 1. Build Concrete Model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_supply))
model.J = pyo.Set(initialize=range(num_demand))
# 2. Parameters (using placeholder data generation for reproducibility)
random.seed(42)
model.capacity = pyo.Param(model.I, initialize=lambda m, i: capacities[i])
model.demand = pyo.Param(model.J, initialize=lambda m, j: demands[j])
model.cost = pyo.Param(model.I, model.J, initialize=lambda m, i, j: costs[i][j])
model.max_limit = pyo.Param(model.I, model.J, initialize=lambda m, i, j: max_limits[i][j])
# 3. Variables with bounds via rule
def x_bounds(m, i, j):
    return (0, m.max_limit[i, j])
model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals, bounds=x_bounds)
# 4. Constraints
def supply_rule(m, i):
    return sum(m.x[i, j] for j in m.J) == m.capacity[i]
model.supply_con = pyo.Constraint(model.I, rule=supply_rule)
def demand_rule(m, j):
    return sum(m.x[i, j] for i in m.I) == m.demand[j]
model.demand_con = pyo.Constraint(model.J, rule=demand_rule)
# 5. Objective
model.obj = pyo.Objective(expr=sum(m.cost[i,j] * m.x[i,j] for i in m.I for j in m.J), sense=pyo.minimize)
# 6. Solve
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['threads'] = 4
results = solver.solve(model)
# 7. Check status and termination
from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = pyo.value(model.obj)
    # 8. Validation
    tol = 1e-6
    for i in model.I:
        assigned = sum(pyo.value(model.x[i, j]) for j in model.J)
        assert abs(assigned - pyo.value(model.capacity[i])) < tol
    print(f'RESULT: {total_cost}')
else:
    print(f'Solve failed: Status={status}, Termination={term}')
```

### Common Pitfalls
- Not importing `SolverStatus` and `TerminationCondition` for proper status checking, leading to incorrect success detection.
- Using `pyo.value()` on parameters or variables before solving, which returns `None`; only call after a successful solve.
- Omitting solver options like `seconds` can lead to unpredictable runtimes; always set reasonable limits.
