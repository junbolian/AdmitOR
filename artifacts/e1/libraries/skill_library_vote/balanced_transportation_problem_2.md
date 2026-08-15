---
name: Balanced Transportation Problem
description: |
  Model and solve balanced bipartite flow problems with supply and demand equality constraints to minimize total transportation cost.
---

# Workflow 1 (OR-Tools LP Solver)

## Modeling stage

### Strategy Overview
Model the problem as a linear program using the OR-Tools wrapper, defining flow variables and equality constraints directly within the solver's native API.

### Step 1 - Define Data Structures
- Define sets for origins and destinations as lists of indices or identifiers.
- Define parameters: supply per origin, demand per destination, and unit cost per origin-destination pair as arrays or dictionaries.

### Step 2 - Create Flow Variables
- Create a continuous, non-negative decision variable for each origin-destination pair, representing the flow quantity.

### Step 3 - Formulate Supply Constraints
- For each origin, add a linear constraint stating the sum of all outgoing flows equals its supply.

### Step 4 - Formulate Demand Constraints
- For each destination, add a linear constraint stating the sum of all incoming flows equals its demand.

### Step 5 - Set Linear Objective
- Define the objective to minimize the sum of flow variables multiplied by their respective unit costs.

### Formulation Template
```json
{
  "sets": [
    {"name": "origins", "description": "List of supply node indices"},
    {"name": "destinations", "description": "List of demand node indices"}
  ],
  "parameters": [
    {"name": "supply", "set": "origins", "description": "Available units at each origin"},
    {"name": "demand", "set": "destinations", "description": "Required units at each destination"},
    {"name": "cost", "sets": ["origins", "destinations"], "description": "Unit transportation cost"}
  ],
  "decision_variables": [
    {"name": "flow", "sets": ["origins", "destinations"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * flow[i][j] for i in origins for j in destinations)"
  },
  "constraints": [
    {"name": "supply_constraint", "set": "origins", "expression": "sum(flow[i][j] for j in destinations) == supply[i]"},
    {"name": "demand_constraint", "set": "destinations", "expression": "sum(flow[i][j] for i in origins) == demand[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to verify total supply equals total demand before solving, which leads to infeasibility with equality constraints.
- Using solver-specific variable creation loops that obscure the model's structure, making debugging difficult.
- Not defining variable upper bounds, which can be left as infinity for standard transportation problems.

## Solving stage

### Strategy Overview
Solve the linear program using OR-Tools' GLOP or CBC solver, with explicit status checking and post-solution validation.

### Step 1 - Instantiate Solver and Build Model
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("GLOP")`).
- Build the model by translating the formulation into solver calls for variables, constraints, and objective.

### Step 2 - Solve and Check Status
- Execute `solver.Solve()`.
- Check the returned status against `OPTIMAL` or `FEASIBLE` to confirm a solution was found.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value.
- Extract the flow variable values and verify they satisfy supply and demand constraints within a numerical tolerance.

### Step 4 - Report Results
- Output the total cost and a summary of flows.
- For failures, output solver status and diagnostic information.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Instantiate solver
solver = pywraplp.Solver.CreateSolver("GLOP")
# Build model from data (supply_list, demand_list, cost_matrix)
flow = {}
for i in range(num_origins):
    for j in range(num_destinations):
        flow[i, j] = solver.NumVar(0, solver.infinity(), f'flow_{i}_{j}')

# Supply constraints
for i in range(num_origins):
    ct = solver.Constraint(supply_list[i], supply_list[i])
    for j in range(num_destinations):
        ct.SetCoefficient(flow[i, j], 1)

# Demand constraints
for j in range(num_destinations):
    ct = solver.Constraint(demand_list[j], demand_list[j])
    for i in range(num_origins):
        ct.SetCoefficient(flow[i, j], 1)

# Objective
objective = solver.Objective()
for i in range(num_origins):
    for j in range(num_destinations):
        objective.SetCoefficient(flow[i, j], cost_matrix[i][j])
objective.SetMinimization()

# Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # Extract flows and validate
    for i in range(num_origins):
        for j in range(num_destinations):
            val = flow[i, j].solution_value()
            # Use val for reporting/validation
    print(f"RESULT:{total_cost}")
else:
    print(f"RESULT_JSON:{{'status': {status}}}")
```

### Common Pitfalls
- Assuming `solver.Solve()` always returns an optimal solution without checking the status.
- Not validating the solution against the original constraints, which can mask numerical issues.
- Using a solver that does not support linear programming (e.g., a MIP-only solver) for this continuous problem.

# Workflow 2 (Pyomo with High-Level Solver)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo's abstract or concrete modeling components, separating data from structure for flexibility and reuse.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo Sets for origins and destinations.
- Declare Pyomo Parameters for supply, demand, and cost, indexed by the appropriate sets.

### Step 2 - Declare Decision Variables
- Define a Pyomo Var indexed over origin-destination pairs, with a non-negative real domain.

### Step 3 - Construct Constraints via Rules
- Define a rule function for the supply constraint that sums flows for each origin.
- Define a rule function for the demand constraint that sums flows for each destination.

### Step 4 - Define Objective Expression
- Create a Pyomo Objective object with the sense set to minimize and the expression summing cost * flow.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of origins"},
    {"name": "J", "description": "Set of destinations"}
  ],
  "parameters": [
    {"name": "S", "set": "I", "description": "Supply amount at origin i"},
    {"name": "D", "set": "J", "description": "Demand amount at destination j"},
    {"name": "C", "sets": ["I", "J"], "description": "Unit cost from i to j"}
  ],
  "decision_variables": [
    {"name": "x", "sets": ["I", "J"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(C[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    {"name": "SupplyBalance", "set": "I", "expression": "sum(x[i,j] for j in J) == S[i]"},
    {"name": "DemandBalance", "set": "J", "expression": "sum(x[i,j] for i in I) == D[j]"}
  ]
}
```

### Common Pitfalls
- Mixing concrete and abstract model styles inconsistently, leading to confusion in data initialization.
- Defining constraint rules that incorrectly reference model components due to Pyomo's deferred initialization.
- Not pre-checking data balance (total supply vs. total demand) before model instantiation, causing avoidable infeasibility errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external LP solver (e.g., HiGHS, CBC) via SolverFactory, with robust termination and status checks.

### Step 1 - Instantiate Model and Load Data
- Create a ConcreteModel or instantiate an AbstractModel with data.
- Populate the model's Sets and Parameters with the problem data.

### Step 2 - Configure and Execute Solver
- Create a solver object using `SolverFactory("solver_name")`.
- Set solver options (e.g., time limit, threads).
- Call `solver.solve(model)`.

### Step 3 - Inspect Termination and Solution Status
- Check `model.solutions.solver.status` is `SolverStatus.ok`.
- Check `model.solutions.solver.termination_condition` is `optimal` or `feasible`.

### Step 4 - Validate and Report Solution
- Extract the objective value from `model.objective()`.
- Iterate over flow variables to validate constraint satisfaction.
- Output results in a structured format.

### Code Usage
```python
import pyomo.environ as pyo

# Create a concrete model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=origin_indices)
model.J = pyo.Set(initialize=destination_indices)
model.S = pyo.Param(model.I, initialize=supply_dict)
model.D = pyo.Param(model.J, initialize=demand_dict)
model.C = pyo.Param(model.I, model.J, initialize=cost_dict)

model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

def supply_rule(model, i):
    return sum(model.x[i, j] for j in model.J) == model.S[i]
model.SupplyBalance = pyo.Constraint(model.I, rule=supply_rule)

def demand_rule(model, j):
    return sum(model.x[i, j] for i in model.I) == model.D[j]
model.DemandBalance = pyo.Constraint(model.J, rule=demand_rule)

def obj_rule(model):
    return sum(model.C[i, j] * model.x[i, j] for i in model.I for j in model.J)
model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Solve
solver = pyo.SolverFactory('highs')
results = solver.solve(model, options={'time_limit': 30})

# Check status and termination
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    total_cost = pyo.value(model.objective)
    # Validate flows
    for i in model.I:
        total_out = sum(pyo.value(model.x[i, j]) for j in model.J)
        # Compare total_out with model.S[i] within tolerance
    print(f"RESULT:{total_cost}")
else:
    print(f"RESULT_JSON:{results.solver}")
```

### Common Pitfalls
- Confusing solver status (`SolverStatus`) with termination condition, leading to incorrect feasibility assessments.
- Accessing variable values before verifying the solver terminated successfully, which may raise exceptions.
- Not using `pyo.value()` to extract numeric values from Pyomo expressions, causing type errors.
