---
name: MultiPeriodResourceFlowOptimization
description: |
  Model and solve multi-period resource allocation problems with flow conservation, capacity constraints, and linear costs using integer programming, supporting both comprehensive and simplified formulations.
---

# Workflow 1 (Comprehensive Multi-Period Flow)

## Modeling stage

### Strategy Overview
This workflow models the full multi-period dynamics of resource movement and inventory tracking. It is suitable for problems where resource repositioning across time periods is critical to the operational plan.

### Step 1 - Define Multi-Dimensional Integer Variables
- Create integer flow variables for resources moving between locations in each time period (e.g., `x[resource_type, time_period, origin, destination]`).
- Create integer inventory variables for idle resources at each location in each time period (e.g., `idle[resource_type, time_period, location]`).
- Use explicit upper bounds based on route capacities and total resource availability to improve solver performance.

### Step 2 - Implement Flow Conservation Constraints
- For each resource type, location, and time period after the initial one, enforce a balance equation: `idle[t,l] = idle[t-1,l] - departing_flow[t-1] + arriving_flow[t-1]`.
- This constraint tracks the movement of resources across the network over time.

### Step 3 - Apply Capacity and Demand Constraints
- Enforce route capacity limits per resource type and time period: `x[p,t,i,j] <= route_capacity[p,i,j]`.
- Ensure total active and idle resources do not exceed availability: `sum(idle[p,t,l]) + sum(x[p,t,i,j]) <= max_resources[p]` for each `p,t`.
- Scale flow variables by resource capacity to satisfy demand: `sum(capacity[p] * x[p,t,origin,destination]) >= demand[t]`.

### Step 4 - Handle Initial Conditions and Objective
- Define initial period constraints to allocate all resources, either as fixed values or decision variables with bounds.
- Formulate a linear cost objective to minimize operational expenses, typically assigning zero cost to idle resources.

### Formulation Template
```json
{
  "sets": [
    "resource_types",
    "time_periods",
    "locations",
    "origin_destination_pairs"
  ],
  "parameters": [
    "max_resources[resource_type]",
    "route_capacity[resource_type, origin, destination]",
    "resource_capacity[resource_type]",
    "demand[time_period]",
    "operational_cost[resource_type, origin, destination]"
  ],
  "decision_variables": [
    "x[resource_type, time_period, origin, destination] (integer, non-negative)",
    "idle[resource_type, time_period, location] (integer, non-negative)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(operational_cost[p,i,j] * x[p,t,i,j] for p,i,j,t)"
  },
  "constraints": [
    "flow_conservation: idle[p,t,l] == idle[p,t-1,l] - sum(x[p,t-1,l,j]) + sum(x[p,t-1,i,l]) for t>0",
    "resource_availability: sum(idle[p,t,l]) + sum(x[p,t,i,j]) <= max_resources[p] for all p,t",
    "route_capacity: x[p,t,i,j] <= route_capacity[p,i,j] for all p,t,i,j",
    "demand_satisfaction: sum(resource_capacity[p] * x[p,t,origin,destination]) >= demand[t] for all t",
    "initial_allocation: sum(idle[p,0,l]) + sum(x[p,0,i,j]) == max_resources[p] for all p"
  ]
}
```

### Common Pitfalls
- Forgetting to index flow conservation constraints for `t > 0` only, leading to an undefined `t-1` for the first period.
- Using the same variable for both flow and inventory without proper linking, breaking resource accounting.
- Neglecting to scale flow variables by resource capacity in demand constraints, resulting in unmet demand.

## Solving stage

### Strategy Overview
Solve the comprehensive model using a robust MIP solver like CBC via Pyomo, with careful attention to solver status checks and solution validation.

### Step 1 - Build and Solve Model
- Instantiate a concrete Pyomo model and populate it with the formulation components.
- Use `SolverFactory('cbc')` and set key parameters: `seconds` for time limit, `ratio` for MIP gap, `threads` for parallelism.
- Call `solver.solve(model)` and capture the result object.

### Step 2 - Check Solver Status and Termination
- Verify `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` for `optimal` or `feasible` before extracting solutions.
- If status is not ok or termination is not acceptable, output a structured error message.

### Step 3 - Extract and Validate Solution
- Iterate through model variables and collect non-zero values for analysis.
- Programmatically verify key constraints (e.g., flow conservation, demand satisfaction) using the extracted values to ensure solution integrity.
- Compute derived metrics like total cost and resource utilization.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
# ... populate model with sets, parameters, variables, constraints, objective ...

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = time_limit
solver.options['ratio'] = mip_gap
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
        # Extract solution
        solution = {v.name: pyo.value(v) for v in model.component_objects(pyo.Var, active=True)}
        # Validate constraints
        # ... validation logic ...
    else:
        output = {'status': 'failed', 'reason': 'solver did not find optimal/feasible solution', 'termination_condition': str(results.solver.termination_condition)}
else:
    output = {'status': 'failed', 'reason': 'solver error', 'solver_status': str(results.solver.status)}
```

### Common Pitfalls
- Calling `.value()` on constraint expressions instead of variable objects after solving.
- Not checking for both `optimal` and `feasible` termination conditions, potentially discarding valid solutions.
- Assuming solver output is always present; always guard against `None` values when extracting results.

# Workflow 2 (Simplified Single-Period Core)

## Modeling stage

### Strategy Overview
This workflow collapses the time dimension to a single period, focusing on the core allocation and demand satisfaction decisions. It is ideal when only the first period has demand or when multi-period dynamics are secondary.

### Step 1 - Define Single-Period Decision Variables
- Create integer variables for operated resources on each route (e.g., `operated[resource_type, route]`).
- Create integer variables for idle resources at each location (e.g., `idle[resource_type, location]`).
- Omit time indices to reduce model size and complexity.

### Step 2 - Enforce Resource Conservation
- For each resource type, ensure the sum of operated and idle resources equals the total available: `operated[p] + sum(idle[p,l]) == max_resources[p]`.
- This replaces multi-period flow conservation with a single accounting equation.

### Step 3 - Apply Demand and Capacity Constraints
- Satisfy demand using capacity-scaled operated variables: `sum(resource_capacity[p] * operated[p, demand_route]) >= demand`.
- Enforce route capacity limits: `operated[p,r] <= route_capacity[p,r]`.
- Optionally add directional flow restrictions by fixing certain variables to zero.

### Step 4 - Formulate Linear Cost Objective
- Define operational costs only for operated resources, as idle resources typically incur no variable cost.
- Minimize total cost: `sum(operational_cost[p,r] * operated[p,r])`.

### Formulation Template
```json
{
  "sets": [
    "resource_types",
    "locations",
    "routes"
  ],
  "parameters": [
    "max_resources[resource_type]",
    "route_capacity[resource_type, route]",
    "resource_capacity[resource_type]",
    "demand",
    "operational_cost[resource_type, route]"
  ],
  "decision_variables": [
    "operated[resource_type, route] (integer, non-negative)",
    "idle[resource_type, location] (integer, non-negative)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(operational_cost[p,r] * operated[p,r] for p,r)"
  },
  "constraints": [
    "resource_conservation: operated[p] + sum(idle[p,l]) == max_resources[p] for all p",
    "demand_satisfaction: sum(resource_capacity[p] * operated[p, demand_route]) >= demand",
    "route_capacity: operated[p,r] <= route_capacity[p,r] for all p,r"
  ]
}
```

### Common Pitfalls
- Incorrectly scaling the `operated` variable by resource capacity in the demand constraint, or forgetting to scale it at all.
- Over-constraining the model by applying multi-period logic to a single-period formulation.
- Not providing an upper bound for `operated` variables, which can slow down the solver.

## Solving stage

### Strategy Overview
Solve the simplified model using a lightweight interface like PuLP with CBC, enabling quick prototyping and validation of core problem feasibility.

### Step 1 - Build Model with PuLP
- Define a PuLP `LpProblem` with a sense (`LpMinimize`).
- Create `LpVariable` dictionaries for `operated` and `idle` with `lowBound=0` and `cat='Integer'`.
- Add constraints using `+=` operator and set the objective.

### Step 2 - Solve and Check Status
- Call `problem.solve(PULP_CBC_CMD(timeLimit=time_limit, gapRel=mip_gap))`.
- Check the solution status: `LpStatus[problem.status]` should be `'Optimal'` or `'Feasible'`.

### Step 3 - Extract and Analyze Solution
- Iterate through variables and collect values where `var.varValue > 0`.
- Perform a sanity check by manually verifying demand satisfaction and resource conservation.
- Use the solution to inform potential refinements for a more complex model if needed.

### Code Usage
```python
import pulp

# build model from formulation
prob = pulp.LpProblem('ResourceAllocation', pulp.LpMinimize)

# Define variables
operated = pulp.LpVariable.dicts('operated', (resource_types, routes), lowBound=0, cat='Integer')
idle = pulp.LpVariable.dicts('idle', (resource_types, locations), lowBound=0, cat='Integer')

# Add constraints
for p in resource_types:
    prob += operated[p] + pulp.lpSum(idle[p][l] for l in locations) == max_resources[p]
# ... add other constraints ...

# Set objective
prob += pulp.lpSum(operational_cost[p][r] * operated[p][r] for p in resource_types for r in routes)

# solve with status / termination checks
solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, gapRel=mip_gap)
prob.solve(solver)

status = pulp.LpStatus[prob.status]
if status in ['Optimal', 'Feasible']:
    solution = {v.name: v.varValue for v in prob.variables() if v.varValue > 0}
else:
    output = {'status': 'failed', 'reason': f'solver returned {status}'}
```

### Common Pitfalls
- Misinterpreting PuLP's status codes; `'Optimal'` guarantees optimality, `'Feasible'` does not.
- Not using `gapRel` parameter for PuLP's CBC, leading to default tolerance which may be too loose or tight.
- Forgetting to check variable values for `None` before using them in post-solution calculations.
