---
name: Bipartite Flow Transportation
description: |
  Model and solve balanced bipartite flow problems with supply/demand equality constraints and linear cost minimization using open-source solvers.

---

# Workflow 1 (Pyomo with CBC/Highs)

## Modeling stage

### Strategy Overview
Formulate the problem as a balanced transportation network using Pyomo's abstract modeling capabilities, defining sets, parameters, and constraints for a bipartite flow with arc capacities.

### Step 1 - Define Problem Structure
- Identify two disjoint sets: supply nodes (origins) and demand nodes (destinations).
- Verify the problem is balanced: total supply must equal total demand for feasibility with equality constraints.
- Organize data into indexed structures: lists for supply/demand, 2D arrays for cost and capacity.

### Step 2 - Declare Model Components
- Create a `ConcreteModel` and define `Set` objects for supply and demand indices.
- Declare `Param` objects for supply, demand, cost, and capacity parameters, initializing from data structures.
- Define the primary decision variable `flow` as `Var(domain=NonNegativeReals)` indexed over supply-demand pairs.

### Step 3 - Formulate Constraints
- Add supply constraints: for each supply node `i`, `sum(flow[i,j] for j in demand_nodes) == supply[i]`.
- Add demand constraints: for each demand node `j`, `sum(flow[i,j] for i in supply_nodes) == demand[j]`.
- Add arc capacity constraints: for each pair `(i,j)`, `flow[i,j] <= capacity[i,j]`.

### Step 4 - Set Objective
- Formulate the objective as a linear cost minimization: `minimize sum(cost[i,j] * flow[i,j] for all i,j)`.

### Formulation Template
```json
{
  "sets": ["supply_nodes", "demand_nodes"],
  "parameters": ["supply", "demand", "cost", "capacity"],
  "decision_variables": ["flow[supply_nodes, demand_nodes]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * flow[i,j])"
  },
  "constraints": [
    "supply_con[i]: sum(flow[i,j]) == supply[i]",
    "demand_con[j]: sum(flow[i,j]) == demand[j]",
    "capacity_con[i,j]: flow[i,j] <= capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Forgetting to verify total supply equals total demand, leading to infeasibility.
- Using incorrect indexing in parameter dictionaries, causing key errors.
- Omitting arc capacity constraints, resulting in unrealistic flow allocations.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source LP solver (CBC or HiGHS), configuring for performance and reliability, then rigorously verify the solution against the original constraints.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `SolverFactory("cbc")` or `SolverFactory("highs")`.
- Set practical options: `seconds=30` for time limit, `ratio=0.0` for exact optimality, `threads=4` for parallelism.
- Call `solver.solve(model, tee=False)` to execute.

### Step 2 - Validate Solution Status
- Check `results.solver.status == SolverStatus.ok`.
- Verify `results.solver.termination_condition` is `optimal` or `feasible`.
- If status is not ok or termination is not acceptable, report structured error and halt.

### Step 3 - Extract and Verify Solution
- Extract the objective value: `total_cost = float(pyo.value(model.obj))`.
- For each flow variable, retrieve value if above a tolerance (e.g., `1e-6`).
- Recompute sums for each supply and demand constraint to verify satisfaction within tolerance.
- Check each flow against its capacity limit.

### Step 4 - Report Results
- Output the total cost with a parsable prefix: `RESULT:{total_cost}`.
- Optionally, print a table of non-zero flows with origin, destination, amount, and cost contribution.
- Include a verification summary confirming constraint satisfaction.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
model.S = pyo.Set(initialize=supply_nodes)
model.D = pyo.Set(initialize=demand_nodes)
model.supply = pyo.Param(model.S, initialize=supply_data)
model.demand = pyo.Param(model.D, initialize=demand_data)
model.cost = pyo.Param(model.S, model.D, initialize=cost_data)
model.capacity = pyo.Param(model.S, model.D, initialize=capacity_data)
model.flow = pyo.Var(model.S, model.D, domain=pyo.NonNegativeReals)

def obj_rule(m):
    return sum(m.cost[i,j] * m.flow[i,j] for i in m.S for j in m.D)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def supply_rule(m, i):
    return sum(m.flow[i,j] for j in m.D) == m.supply[i]
model.supply_con = pyo.Constraint(model.S, rule=supply_rule)

def demand_rule(m, j):
    return sum(m.flow[i,j] for i in m.S) == m.demand[j]
model.demand_con = pyo.Constraint(model.D, rule=demand_rule)

def capacity_rule(m, i, j):
    return m.flow[i,j] <= m.capacity[i,j]
model.capacity_con = pyo.Constraint(model.S, model.D, rule=capacity_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    total_cost = float(pyo.value(model.obj))
    print(f"RESULT:{total_cost}")
    # Verification and detailed output can follow
else:
    print(f"ERROR: Solver failed with status {results.solver.status}, termination {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to acceptance of failed solves.
- Using `tee=True` in production without managing output volume.
- Forgetting to load the solution into the model before extracting values (Pyomo does this automatically with `solve`).

# Workflow 2 (OR-Tools LP with GLOP)

## Modeling stage

### Strategy Overview
Directly construct a linear program using the OR-Tools LP solver API, explicitly creating variables with bounds, and building constraints via coefficient setting for a bipartite flow problem.

### Step 1 - Initialize Solver and Data
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Organize input data: lists for supply and demand, 2D lists for cost and capacity matrices.
- Set a time limit on the solver: `solver.SetTimeLimit(30000)`.

### Step 2 - Create Variables with Bounds
- For each supply node `i` and demand node `j`, create a variable `x[i,j] = solver.NumVar(0, capacity[i][j], name)`.
- This embeds the non-negativity and arc capacity bounds directly into the variable declaration.

### Step 3 - Build Supply Constraints
- For each supply node `i`, create a linear constraint: `constraint = solver.Constraint(supply[i], supply[i])`.
- For each demand node `j`, set coefficient: `constraint.SetCoefficient(x[i,j], 1.0)`.

### Step 4 - Build Demand Constraints
- For each demand node `j`, create a linear constraint: `constraint = solver.Constraint(demand[j], demand[j])`.
- For each supply node `i`, set coefficient: `constraint.SetCoefficient(x[i,j], 1.0)`.

### Step 5 - Set Linear Objective
- Create the objective: `objective = solver.Objective()`.
- For each variable `x[i,j]`, set its coefficient: `objective.SetCoefficient(x[i,j], cost[i][j])`.
- Set minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations"],
  "parameters": ["supply", "demand", "cost", "capacity"],
  "decision_variables": ["x[origins, destinations]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "supply_con[i]: sum(x[i][:]) == supply[i]",
    "demand_con[j]: sum(x[:][j]) == demand[j]",
    "capacity_builtin: 0 <= x[i][j] <= capacity[i][j]"
  ]
}
```

### Common Pitfalls
- Using `solver.infinity()` for capacity when a finite large value is more stable.
- Incorrectly ordering loops when setting constraint coefficients, leading to wrong constraint shapes.
- Not balancing total supply and demand, causing infeasibility with equality constraints.

## Solving stage

### Strategy Overview
Solve the constructed LP using the GLOP solver, extract the solution values, and perform post-solve verification to ensure the result is valid and meets all problem constraints.

### Step 1 - Execute Solve
- Call `solver.Solve()` and capture the status code.

### Step 2 - Check Solve Status
- Verify status is `OPTIMAL` or `FEASIBLE`.
- If status is not acceptable, report the solver status and terminate.

### Step 3 - Extract Solution Values
- Retrieve the objective value: `total_cost = objective.Value()`.
- For each variable `x[i,j]`, get its value: `flow_value = x[i,j].solution_value()`.
- Filter flows above a small tolerance (e.g., `1e-6`) for reporting.

### Step 4 - Verify Constraints
- Recompute total outflow for each supply node and compare to supply.
- Recompute total inflow for each demand node and compare to demand.
- Check each flow value against its capacity upper bound.
- Report any violations beyond numerical tolerance.

### Step 5 - Output Results
- Print the total cost.
- Optionally, output a table of non-zero shipments.
- Include a summary of verification checks.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
solver.SetTimeLimit(30000)

# Create variables
x = {}
for i in range(len(supply)):
    for j in range(len(demand)):
        # Use a large finite value if capacity is missing
        upper_bound = capacity[i][j] if capacity[i][j] is not None else 1000.0
        x[i, j] = solver.NumVar(0, upper_bound, f'x_{i}_{j}')

# Supply constraints
for i in range(len(supply)):
    constraint = solver.Constraint(supply[i], supply[i])
    for j in range(len(demand)):
        constraint.SetCoefficient(x[i, j], 1.0)

# Demand constraints
for j in range(len(demand)):
    constraint = solver.Constraint(demand[j], demand[j])
    for i in range(len(supply)):
        constraint.SetCoefficient(x[i, j], 1.0)

# Objective
objective = solver.Objective()
for i in range(len(supply)):
    for j in range(len(demand)):
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# Solve with status / termination checks
status = solver.Solve()

if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_cost = objective.Value()
    print(f"RESULT:{total_cost}")
    # Verification and detailed output can follow
else:
    print(f"ERROR: Solver failed with status {status}")
```

### Common Pitfalls
- Assuming `solver.Solve()` returns a boolean; it returns an enum status.
- Not handling missing capacity values, leading to unbounded variables.
- Forgetting that `objective.Value()` returns a float, while `x[i,j].solution_value()` returns the flow value.
