---
name: Capacitated Facility Location MILP
description: |
  Model and solve capacitated facility location problems as mixed-integer linear programs with binary facility opening decisions, continuous flow variables, fixed costs, linear transportation costs, demand satisfaction, and capacity-activation linking constraints.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling syntax, which provides a high-level, algebraic interface. This approach cleanly separates model structure from data and is portable across multiple solvers.

### Step 1 - Define Sets and Parameters
- Declare sets for facilities and customers.
- Define parameters for fixed costs, capacities, demands, and unit transportation costs.

### Step 2 - Declare Decision Variables
- Create binary variables for facility opening decisions.
- Create continuous, non-negative variables for flow from each facility to each customer.

### Step 3 - Formulate Objective Function
- Construct the objective as the sum of total fixed costs and total linear transportation costs.
- Set the sense to minimization.

### Step 4 - Impose Demand and Capacity Constraints
- Add constraints ensuring total flow to each customer equals its demand.
- Add capacity-activation linking constraints: total outflow from a facility cannot exceed its capacity if open, and must be zero if closed.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": [
    "fixed_cost[facilities]",
    "capacity[facilities]",
    "demand[customers]",
    "transport_cost[facilities][customers]"
  ],
  "decision_variables": [
    {"name": "y", "type": "binary", "index": "facilities"},
    {"name": "x", "type": "continuous_nonnegative", "index": ["facilities", "customers"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i] for i in facilities) + sum(transport_cost[i][j] * x[i][j] for i in facilities for j in customers)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "sum(x[i][j] for i in facilities) == demand[j] for all j in customers"},
    {"name": "capacity_linking", "expression": "sum(x[i][j] for j in customers) <= capacity[i] * y[i] for all i in facilities"}
  ]
}
```

### Common Pitfalls
- Forgetting to multiply `y[i]` in the capacity constraint, which incorrectly allows flow from closed facilities.
- Using inequality (`>=`) for demand satisfaction, which allows over-supply and may distort costs.
- Defining transportation cost parameters with the wrong dimensions, leading to indexing errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an efficient MILP solver like HiGHS or CBC, configured for reliability. Focus on robust solution status checking and post-solution verification.

### Step 1 - Instantiate Solver and Set Options
- Create a solver instance (e.g., `SolverFactory('highs')` or `SolverFactory('cbc')`).
- Set basic options like time limit and optimality gap tolerance if needed.

### Step 2 - Solve and Check Termination Status
- Execute the solve command.
- Check the solver status and termination condition to determine if a feasible or optimal solution was found.

### Step 3 - Extract and Verify Solution
- If the solve was successful, extract the objective value and variable values.
- Programmatically verify that demand and capacity constraints are satisfied within a small numerical tolerance.

### Step 4 - Report Key Results
- Summarize which facilities are open, their utilization, and the cost breakdown (fixed vs. transportation).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (using the formulation template)
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=facilities)
model.J = pyo.Set(initialize=customers)
model.fixed_cost = pyo.Param(model.I, initialize=fixed_cost_data)
model.capacity = pyo.Param(model.I, initialize=capacity_data)
model.demand = pyo.Param(model.J, initialize=demand_data)
model.transport_cost = pyo.Param(model.I, model.J, initialize=transport_cost_data)

model.y = pyo.Var(model.I, domain=pyo.Binary)
model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

def obj_rule(m):
    return sum(m.fixed_cost[i] * m.y[i] for i in m.I) + \
           sum(m.transport_cost[i,j] * m.x[i,j] for i in m.I for j in m.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def demand_rule(m, j):
    return sum(m.x[i,j] for i in m.I) == m.demand[j]
model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

def capacity_rule(m, i):
    return sum(m.x[i,j] for j in m.J) <= m.capacity[i] * m.y[i]
model.capacity_con = pyo.Constraint(model.I, rule=capacity_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'cbc'
results = solver.solve(model, tee=False)

status = results.solver.status
termination = results.solver.termination_condition

if status == SolverStatus.ok and termination in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = pyo.value(model.obj)
    # Extract solution values for model.y and model.x
    open_facilities = [i for i in model.I if pyo.value(model.y[i]) > 0.5]
    # ... perform verification and reporting
else:
    # Handle solver failure
    print(f"Solver failed: Status={status}, Termination={termination}")
```

### Common Pitfalls
- Assuming `results.solver.status == 'ok'` guarantees an optimal solution; it only means the solver ran without error. Always check the termination condition.
- Not using a tolerance (e.g., `1e-6`) when checking variable values (e.g., `pyo.value(model.y[i]) > 0.5`).
- Forgetting to call `pyo.value()` on the objective or variables before using their results in calculations.

# Workflow 2 (OR-Tools with SCIP/CBC Backend)

## Modeling stage

### Strategy Overview
Model the problem directly using the OR-Tools linear solver wrapper (`pywraplp`). This imperative, API-driven approach builds the model step-by-step and is tightly integrated with the SCIP and CBC solvers.

### Step 1 - Initialize Solver and Define Infinity
- Create a solver instance (e.g., `SCIP` or `CBC`).
- Define an infinity constant for variable upper bounds.

### Step 2 - Create Decision Variables
- Create binary variables for facility opening.
- Create continuous variables for flows, with a lower bound of 0.

### Step 3 - Build Objective Function
- Construct the objective expression by setting coefficients for each variable.
- Set the objective sense to minimization.

### Step 4 - Add Constraints
- Add linear constraints for demand satisfaction (equality).
- Add linear constraints for capacity-activation linking (inequality).

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": [
    "fixed_cost[facilities]",
    "capacity[facilities]",
    "demand[customers]",
    "unit_cost[facilities][customers]"
  ],
  "decision_variables": [
    {"name": "y", "type": "binary", "index": "facilities"},
    {"name": "x", "type": "continuous", "bounds": "[0, INF]", "index": ["facilities", "customers"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i]) + sum(unit_cost[i][j] * x[i][j])"
  },
  "constraints": [
    {"name": "meet_demand", "expression": "sum(x[i][j] for i in facilities) == demand[j]"},
    {"name": "link_capacity", "expression": "sum(x[i][j] for j in customers) - capacity[i] * y[i] <= 0"}
  ]
}
```

### Common Pitfalls
- Manually creating large nested dictionaries for variables, which can be memory-inefficient for very large instances. Consider using list comprehensions.
- Incorrectly ordering the indices when creating flow variables, leading to mismatched dimensions in constraints.
- Using `solver.infinity()` directly in a loop condition, which is inefficient; store it in a variable first.

## Solving stage

### Strategy Overview
Solve the model using the configured OR-Tools solver backend. Leverage solver-specific parameters for performance and implement thorough solution checking.

### Step 1 - Configure Solver Parameters
- Set a time limit to prevent excessive runtime.
- Set the number of threads for parallel processing if supported.
- Optionally set an optimality gap tolerance.

### Step 2 - Execute Solve and Check Result Status
- Call the `Solve()` method.
- Check the result status (`OPTIMAL`, `FEASIBLE`, etc.) to determine success.

### Step 3 - Validate Solution Feasibility
- After a successful solve, compute aggregated flows to verify demand satisfaction and capacity limits.
- Ensure flows from closed facilities are zero.

### Step 4 - Extract and Format Output
- Retrieve the objective value.
- Extract lists of open facilities and non-zero flows for reporting.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
if not solver:
    raise RuntimeError('Solver not available.')

INF = solver.infinity()

# Create variables
y = {i: solver.BoolVar(f'y_{i}') for i in facilities}
x = {}
for i in facilities:
    for j in customers:
        x[i, j] = solver.NumVar(0, INF, f'x_{i}_{j}')

# Demand constraints
for j in customers:
    ct = solver.Constraint(demand[j], demand[j])
    for i in facilities:
        ct.SetCoefficient(x[i, j], 1)

# Capacity-linking constraints
for i in facilities:
    ct = solver.Constraint(-INF, 0)
    for j in customers:
        ct.SetCoefficient(x[i, j], 1)
    ct.SetCoefficient(y[i], -capacity[i])

# Objective
objective = solver.Objective()
for i in facilities:
    objective.SetCoefficient(y[i], fixed_cost[i])
for i in facilities:
    for j in customers:
        objective.SetCoefficient(x[i, j], unit_cost[i][j])
objective.SetMinimization()

# Solve with status / termination checks
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

result_status = solver.Solve()

if result_status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = objective.Value()
    # Extract solution
    open_facs = [i for i in facilities if y[i].solution_value() > 0.5]
    # ... perform verification and reporting
else:
    # Handle solver failure
    print(f"Solver did not find a solution. Status: {result_status}")
```

### Common Pitfalls
- Confusing `solver.Solve()` return status codes with Pyomo's status objects. OR-Tools uses integer/enum codes.
- Not using `.solution_value()` on variables after solving, which leads to accessing the variable object instead of its value.
- Setting an overly restrictive time limit for large instances, causing premature termination before a good solution is found.
