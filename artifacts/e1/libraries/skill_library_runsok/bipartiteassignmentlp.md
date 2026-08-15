---
name: BipartiteAssignmentLP
description: |
  Model and solve bipartite assignment problems with supply, demand, and per-assignment limits as a continuous linear program.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Build a structured Pyomo ConcreteModel using explicit Sets and Parameters, formulating a bipartite flow problem with three constraint types. Use variable bounds for per-assignment limits to reduce constraint count.

### Step 1 - Define Sets and Parameters
- Define two index sets: `I` for supply nodes (e.g., individuals) and `J` for demand nodes (e.g., projects).
- Organize data into Pyomo Parameters: `capacity_i[i]`, `demand_j[j]`, `cost_ij[i,j]`, and `max_hours_ij[i,j]`.

### Step 2 - Create Decision Variables
- Define continuous, non-negative decision variables `x[i,j]` representing the assignment quantity from `i` to `j`.
- Optionally, set variable upper bounds directly using `max_hours_ij[i,j]` to enforce per-assignment limits.

### Step 3 - Formulate Objective and Constraints
- Build a linear objective to minimize total cost: `sum(cost_ij[i,j] * x[i,j] for i in I for j in J)`.
- Add supply constraints: `sum(x[i,j] for j in J) <= capacity_i[i]` for each `i`.
- Add demand constraints: `sum(x[i,j] for i in I) == demand_j[j]` for each `j`.
- If not using variable bounds, add explicit per-assignment limit constraints: `x[i,j] <= max_hours_ij[i,j]`.

### Formulation Template
```json
{
  "sets": ["I (supply nodes)", "J (demand nodes)"],
  "parameters": [
    "capacity_i[i] (supply capacity per node)",
    "demand_j[j] (demand requirement per node)",
    "cost_ij[i,j] (cost per unit assigned)",
    "max_hours_ij[i,j] (maximum assignment per pair)"
  ],
  "decision_variables": ["x[i,j] (non-negative continuous assignment)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_ij[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "supply_limit: sum(x[i,j] for j in J) <= capacity_i[i], for each i in I",
    "demand_satisfaction: sum(x[i,j] for i in I) == demand_j[j], for each j in J",
    "individual_capacity_limit: x[i,j] <= max_hours_ij[i,j], for each i in I, j in J (or via variable bounds)"
  ]
}
```

### Common Pitfalls
- Forgetting to include nodes with zero capacity/demand, which can break set iteration.
- Using explicit constraints for per-assignment limits when variable bounds are more efficient.
- Mismatching indices between parameter initialization and constraint rules.

## Solving stage

### Strategy Overview
Solve the LP using a reliable open-source solver via Pyomo's SolverFactory, configure performance settings, and implement robust status checking and solution validation.

### Step 1 - Select and Configure Solver
- For pure LP, use `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set practical limits: `time_limit=30`, `threads=4` for parallel processing, and `ratio=0.0` for an exact optimality gap.

### Step 2 - Solve and Check Status
- Call `solver.solve(model, tee=True)` to execute and log progress.
- Check both `results.solver.status` (must be `SolverStatus.ok`) and `results.solver.termination_condition` (accept `TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Validate Solution
- Extract the objective value via `float(pyo.value(model.obj))`.
- Iterate through `model.x` to retrieve assignments, filtering values above a tolerance (e.g., `1e-6`).
- Post-solve, verify all constraints by recomputing sums and comparing against parameter values.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (assumes data dictionaries are populated)
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_list)
model.J = pyo.Set(initialize=J_list)
model.capacity_i = pyo.Param(model.I, initialize=capacity_data)
model.demand_j = pyo.Param(model.J, initialize=demand_data)
model.cost_ij = pyo.Param(model.I, model.J, initialize=cost_data)
model.max_hours_ij = pyo.Param(model.I, model.J, initialize=limit_data)

model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals, bounds=lambda m,i,j: (0, m.max_hours_ij[i,j]))

def obj_rule(m):
    return sum(m.cost_ij[i,j] * m.x[i,j] for i in m.I for j in m.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def supply_rule(m, i):
    return sum(m.x[i,j] for j in m.J) <= m.capacity_i[i]
model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

def demand_rule(m, j):
    return sum(m.x[i,j] for i in m.I) == m.demand_j[j]
model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

# Solve
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['time_limit'] = 30
solver.options['threads'] = 4

results = solver.solve(model, tee=True)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
    total_cost = float(pyo.value(model.obj))
    assignments = {(i,j): pyo.value(model.x[i,j]) for i in model.I for j in model.J if pyo.value(model.x[i,j]) > 1e-6}
    # Validation checks here
else:
    raise RuntimeError(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to processing of invalid solutions.
- Extracting all variable values without threshold filtering, which clutters output with near-zero values.
- Omitting post-solution validation, which can miss subtle constraint violations.

# Workflow 2 (OR-Tools with GLOP)

## Modeling stage

### Strategy Overview
Use Google's OR-Tools linear solver wrapper to build a matrix-style LP directly. This approach is efficient for problems where data is naturally represented as 2D arrays and leverages the high-performance GLOP solver.

### Step 1 - Initialize Solver and Data Structures
- Create a linear solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Store cost coefficients in a 2D list `cost[i][j]`, and capacity/demand/limit data in analogous structures.

### Step 2 - Create Variables with Bounds
- Create continuous variables `x[i][j]` using `solver.NumVar(lb, ub, name)`.
- Set lower bound to 0 and upper bound to `max_hours_ij[i][j]` directly.

### Step 3 - Add Constraints and Objective
- Add supply constraints: for each `i`, `sum(x[i][j] for j) <= capacity_i[i]`.
- Add demand constraints: for each `j`, `sum(x[i][j] for i) == demand_j[j]`.
- Build objective: `solver.Minimize(sum(cost[i][j] * x[i][j] for i,j))`.

### Formulation Template
```json
{
  "sets": ["I (supply nodes)", "J (demand nodes)"],
  "parameters": [
    "capacity_i[i] (supply capacity per node)",
    "demand_j[j] (demand requirement per node)",
    "cost_ij[i][j] (cost per unit assigned, as 2D array)",
    "max_hours_ij[i][j] (maximum assignment per pair, as 2D array)"
  ],
  "decision_variables": ["x[i][j] (continuous, bounded variable)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_ij[i][j] * x[i][j] for i in I for j in J)"
  },
  "constraints": [
    "supply_limit: sum(x[i][j] for j in J) <= capacity_i[i], for each i in I",
    "demand_satisfaction: sum(x[i][j] for i in I) == demand_j[j], for each j in J"
  ]
}
```

### Common Pitfalls
- Using Python lists without ensuring consistent dimensions, leading to index errors.
- Forgetting that OR-Tools requires explicit constraint construction via `solver.Add()`.
- Not leveraging variable bounds for per-assignment limits, which adds unnecessary constraints.

## Solving stage

### Strategy Overview
Invoke the solver, check result statuses specific to OR-Tools, extract the solution, and perform verification checks. Use multiple solvers (e.g., CBC) for cross-verification if needed.

### Step 1 - Solve and Interpret Status
- Call `solver.Solve()`.
- Check if result status is `pywraplp.Solver.OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `ABNORMAL` statuses with clear error reporting.

### Step 2 - Extract Solution Details
- Retrieve objective value via `solver.Objective().Value()`.
- Iterate through variables `x[i][j]` and collect values where `x[i][j].solution_value() > tolerance`.

### Step 3 - Verify and Report
- Compute aggregate assignments per supply and demand node to verify constraint satisfaction.
- Report a summary including total cost, individual utilization, and project demand fulfillment.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')
if not solver:
    raise RuntimeError('GLOP solver not available.')

# Assume data is provided as 2D lists or dicts
I = range(num_supply)
J = range(num_demand)
cost = [[cost_data[i][j] for j in J] for i in I]
capacity = [capacity_data[i] for i in I]
demand = [demand_data[j] for j in J]
max_hours = [[limit_data[i][j] for j in J] for i in I]

# Create variables
x = [[solver.NumVar(0.0, max_hours[i][j], f'x_{i}_{j}') for j in J] for i in I]

# Supply constraints
for i in I:
    ct = solver.Constraint(0.0, capacity[i])
    for j in J:
        ct.SetCoefficient(x[i][j], 1)

# Demand constraints
for j in J:
    ct = solver.Constraint(demand[j], demand[j])
    for i in I:
        ct.SetCoefficient(x[i][j], 1)

# Objective
objective = solver.Objective()
for i in I:
    for j in J:
        objective.SetCoefficient(x[i][j], cost[i][j])
objective.SetMinimization()

# Solve
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = objective.Value()
    assignments = []
    for i in I:
        for j in J:
            val = x[i][j].solution_value()
            if val > 1e-6:
                assignments.append((i, j, val))
    # Verification loops here
else:
    raise RuntimeError(f'Solver returned status: {status}')
```

### Common Pitfalls
- Misinterpreting OR-Tools status codes (e.g., treating `FEASIBLE` as `OPTIMAL` without noting the difference).
- Not using a tolerance when extracting variable values, outputting many negligible assignments.
- Failing to set the objective sense correctly (`SetMinimization` vs `SetMaximization`).
