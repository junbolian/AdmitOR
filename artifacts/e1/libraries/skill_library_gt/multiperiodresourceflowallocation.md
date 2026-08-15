---
name: MultiPeriodResourceFlowAllocation
description: |
  Model and solve time-indexed resource allocation problems with integer flow and inventory variables, using linear costs and capacity/demand constraints, with robust solver handling for MIP.
---

# Workflow 1 (Pyomo with CBC/SCIP)

## Modeling stage

### Strategy Overview
Formulate a multi-period network flow problem using Pyomo's abstract or concrete modeling syntax. This approach is well-suited for structured problems with clear sets and parameters, leveraging Pyomo's expressive constraint rules and compatibility with open-source solvers like CBC and SCIP.

### Step 1 - Define Sets and Parameters
- Define sets for resource types, locations, time periods, and allowed origin-destination pairs.
- Define parameters for resource capacity, per-unit operational cost, demand per time and route, route capacity limits, and initial resource inventory.

### Step 2 - Create Integer Decision Variables
- Create `flow[resource_type, time_period, origin, destination]` as a `pyo.Var` with domain `pyo.NonNegativeIntegers`.
- Create `inventory[resource_type, time_period, location]` as a `pyo.Var` with domain `pyo.NonNegativeIntegers`.

### Step 3 - Enforce Flow Conservation Over Time
- For `t > 0`, add a constraint: `inventory[p,t,l] == inventory[p,t-1,l] - sum(flow[p,t-1,l,j] for j in destinations) + sum(flow[p,t-1,i,l] for i in origins)`.
- For `t == 0`, set initial conditions: `inventory[p,0,l] == initial_inventory[p,l]`.

### Step 4 - Apply Resource and Demand Constraints
- Add a resource availability constraint: `sum(inventory[p,t,l] for l in locations) + sum(flow[p,t,i,j] for i,j in pairs) <= max_resources[p]` for each `p` and `t`.
- Add a demand satisfaction constraint: `sum(resource_capacity[p] * flow[p,t,o,d] for p in resource_types) >= demand[t,o,d]` for each `t, o, d`.
- Add route capacity limits: `flow[p,t,o,d] <= route_capacity_limit[p,o,d]`.

### Step 5 - Formulate Linear Cost Objective
- Define the objective to minimize total operational cost: `minimize sum(operational_cost[p,o,d] * flow[p,t,o,d] for p,t,o,d)`.

### Formulation Template
```json
{
  "sets": [
    "resource_types",
    "locations",
    "time_periods",
    "origin_destination_pairs"
  ],
  "parameters": [
    "max_resources[resource_types]",
    "resource_capacity[resource_types]",
    "operational_cost[resource_types, origin_destination_pairs]",
    "demand[time_periods, origin_destination_pairs]",
    "route_capacity_limit[resource_types, origin_destination_pairs]",
    "initial_inventory[resource_types, locations]"
  ],
  "decision_variables": [
    "flow[resource_types, time_periods, origin_destination_pairs] ∈ NonNegativeIntegers",
    "inventory[resource_types, time_periods, locations] ∈ NonNegativeIntegers"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(operational_cost[p,o,d] * flow[p,t,o,d])"
  },
  "constraints": [
    "flow_conservation: inventory[p,t,l] == inventory[p,t-1,l] - sum(flow[p,t-1,l,j]) + sum(flow[p,t-1,i,l]) for t>0",
    "initial_condition: inventory[p,0,l] == initial_inventory[p,l]",
    "resource_availability: sum(inventory[p,t,l]) + sum(flow[p,t,i,j]) <= max_resources[p]",
    "demand_satisfaction: sum(resource_capacity[p] * flow[p,t,o,d]) >= demand[t,o,d]",
    "route_capacity: flow[p,t,o,d] <= route_capacity_limit[p,o,d]"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops (`flow[p,t,l,l]`) in flow conservation, which can incorrectly count idle inventory as flow.
- Defining overly large variable domains without upper bounds, slowing down the solver's presolve.
- Incorrectly indexing the demand constraint over all origin-destination pairs, including those with zero demand.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or SCIP solver via the `SolverFactory` interface. Focus on setting appropriate MIP parameters, checking solver status, and implementing verification of the solution.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver instance: `solver = pyo.SolverFactory('cbc')`.
- Set a time limit: `solver.options['seconds'] = time_limit`.
- Set MIP gap tolerance: `solver.options['ratio'] = mip_gap`.
- Enable parallel processing if supported: `solver.options['threads'] = num_threads`.

### Step 2 - Solve and Check Status
- Execute the solve: `results = solver.solve(model, tee=False)`.
- Check the solver status: `if results.solver.status == pyo.SolverStatus.ok:`.
- Check the termination condition: `if results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:`.

### Step 3 - Extract and Verify Solution
- Extract the objective value: `obj_val = pyo.value(model.objective)`.
- Iterate over key flow and inventory variables, storing values where `var.value is not None`.
- Perform post-solve verification: compute total provided capacity and compare to demand; verify resource availability constraints hold.

### Step 4 - Handle Failures Gracefully
- If the status is not `ok` or termination is not optimal/feasible, print a clear error message with the termination condition.
- For infeasibility, consider returning a structured error payload (e.g., JSON) and suggest checking initial conditions or relaxing constraints.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (using concrete or abstract model)
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective as per modeling stage ...

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 300
solver.options['ratio'] = 0.01
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok:
    term = results.solver.termination_condition
    if term in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
        obj_val = pyo.value(model.objective)
        print(f"RESULT:{obj_val}")
        # Extract and log key variable values
        for var in model.component_objects(pyo.Var, active=True):
            # ... process variable values ...
            pass
    else:
        print(f"ERROR:Solver terminated with condition: {term}")
else:
    print("ERROR:Solver failed to complete.")
```

### Common Pitfalls
- Accessing `var.value` before checking solver status, which may raise an error.
- Not setting a time limit, allowing the solver to run indefinitely on large instances.
- Using default MIP gap settings that are too tight for practical performance.

# Workflow 2 (PuLP with CBC)

## Modeling stage

### Strategy Overview
Formulate the problem using PuLP's straightforward, linear programming syntax. This workflow is ideal for rapid prototyping and problems where a lightweight, procedural modeling style is preferred. It directly interfaces with the CBC solver via PuLP's built-in wrapper.

### Step 1 - Define Problem and Variables
- Instantiate the problem: `prob = pulp.LpProblem("ResourceFlow", pulp.LpMinimize)`.
- Create integer flow variables: `flow[p][t][o][d] = pulp.LpVariable(f"flow_{p}_{t}_{o}_{d}", lowBound=0, cat='Integer')`.
- Create integer inventory variables: `inventory[p][t][l] = pulp.LpVariable(f"inv_{p}_{t}_{l}", lowBound=0, cat='Integer')`.

### Step 2 - Add Flow Conservation Constraints
- For each `p, t>0, l`, add: `inventory[p][t][l] == inventory[p][t-1][l] - sum(flow[p][t-1][l][j]) + sum(flow[p][t-1][i][l])`.
- For `t=0`, add: `inventory[p][0][l] == initial_inventory[p][l]`.

### Step 3 - Add Capacity and Demand Constraints
- Add resource availability: `sum(inventory[p][t][l] for l) + sum(flow[p][t][i][j] for i,j) <= max_resources[p]`.
- Add demand satisfaction: `sum(resource_capacity[p] * flow[p][t][o][d] for p) >= demand[t][o][d]`.
- Add route capacity limits: `flow[p][t][o][d] <= route_capacity_limit[p][o][d]`.

### Step 4 - Set Linear Cost Objective
- Define objective: `prob += sum(operational_cost[p][o][d] * flow[p][t][o][d] for p,t,o,d)`.

### Formulation Template
```json
{
  "sets": [
    "resource_types",
    "locations",
    "time_periods",
    "origin_destination_pairs"
  ],
  "parameters": [
    "max_resources[resource_types]",
    "resource_capacity[resource_types]",
    "operational_cost[resource_types, origin_destination_pairs]",
    "demand[time_periods, origin_destination_pairs]",
    "route_capacity_limit[resource_types, origin_destination_pairs]",
    "initial_inventory[resource_types, locations]"
  ],
  "decision_variables": [
    "flow[resource_types, time_periods, origin_destination_pairs] ∈ NonNegativeIntegers",
    "inventory[resource_types, time_periods, locations] ∈ NonNegativeIntegers"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(operational_cost[p,o,d] * flow[p,t,o,d])"
  },
  "constraints": [
    "flow_conservation: inventory[p,t,l] == inventory[p,t-1,l] - sum(flow[p,t-1,l,j]) + sum(flow[p,t-1,i,l]) for t>0",
    "initial_condition: inventory[p,0,l] == initial_inventory[p,l]",
    "resource_availability: sum(inventory[p,t,l]) + sum(flow[p,t,i,j]) <= max_resources[p]",
    "demand_satisfaction: sum(resource_capacity[p] * flow[p,t,o,d]) >= demand[t,o,d]",
    "route_capacity: flow[p,t,o,d] <= route_capacity_limit[p,o,d]"
  ]
}
```

### Common Pitfalls
- Using string names for variables that include special characters, causing solver interface errors.
- Adding constraints inside loops without proper condition checks, leading to redundant or invalid constraints.
- Forgetting to set upper bounds on variables, which can lead to weaker LP relaxations.

## Solving stage

### Strategy Overview
Solve the PuLP model using the default CBC solver. Leverage PuLP's simple solve call and status attributes. Focus on solution extraction and basic infeasibility handling.

### Step 1 - Solve and Check Status
- Execute the solve: `status = prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit, threads=num_threads))`.
- Check the solution status: `if pulp.LpStatus[status] == 'Optimal':` or `if pulp.LpStatus[status] == 'Feasible':`.

### Step 2 - Extract Solution Values
- Extract the objective value: `obj_val = pulp.value(prob.objective)`.
- Iterate over variables and collect those with a positive value: `if var.varValue > 0: record(var.name, var.varValue)`.

### Step 3 - Perform Solution Verification
- Recalculate total capacity provided by the solution flows and compare to demand.
- Verify that flow conservation and resource availability constraints hold numerically within a small tolerance.

### Step 4 - Handle Infeasibility or Errors
- If status is `'Infeasible'`, print an error and suggest reviewing initial inventory and demand parameters.
- If status is `'Not Solved'` or `'Undefined'`, check for modeling errors or solver configuration issues.

### Code Usage
```python
import pulp

# Build model from formulation
prob = pulp.LpProblem("ResourceFlow", pulp.LpMinimize)
# ... define variables and constraints as per modeling stage ...

# Solve with status / termination checks
solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=300, threads=4)
status = prob.solve(solver)

if pulp.LpStatus[status] in ['Optimal', 'Feasible']:
    obj_val = pulp.value(prob.objective)
    print(f"RESULT:{obj_val}")
    # Extract and log non-zero variable values
    for var in prob.variables():
        if var.varValue is not None and var.varValue > 1e-6:
            print(f"{var.name}: {var.varValue}")
else:
    print(f"ERROR:Solve failed with status: {pulp.LpStatus[status]}")
```

### Common Pitfalls
- Not using `pulp.value(prob.objective)` and instead trying to access the objective directly.
- Assuming `'Feasible'` status means optimal; it may indicate a suboptimal solution if a time limit was hit.
- Neglecting to set `msg=False` in the solver command, leading to verbose console output.
