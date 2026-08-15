---
name: AssignmentOptimization
description: |
  Solve linear assignment problems with supply, demand, and per-arc capacity constraints using structured modeling and robust solver execution.

---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
Model the problem as a linear program using a direct solver API (e.g., OR-Tools, PuLP) with explicit variable bounds and constraint construction. This approach is procedural and closely maps the mathematical formulation to code.

### Step 1 - Define Data Structures
- Organize input data into indexed lists and matrices for clear parameter access (e.g., `availability[i]`, `cost[i][j]`).
- Pre-calculate total supply and demand to perform a basic feasibility check before building the model.

### Step 2 - Create Decision Variables
- Instantiate continuous, non-negative decision variables for each assignment arc (e.g., `x[i][j]`).
- Embed individual capacity limits directly as variable upper bounds during creation to reduce constraint count.

### Step 3 - Formulate Constraints
- Add supply constraints: For each supply node, sum of outgoing assignments must not exceed its availability.
- Add demand constraints: For each demand node, sum of incoming assignments must equal its exact requirement.
- (Optional) Add explicit per-arc capacity constraints if not already enforced by variable bounds.

### Step 4 - Set Linear Objective
- Define a minimization objective as the sum of assignment amounts multiplied by their respective costs.
- Set coefficients using nested loops over all variable indices.

### Formulation Template
```json
{
  "sets": [
    "I: set of supply nodes (e.g., employees)",
    "J: set of demand nodes (e.g., projects)"
  ],
  "parameters": [
    "availability[i]: capacity of supply node i",
    "requirement[j]: demand of node j",
    "cost[i][j]: unit cost of assigning i to j",
    "limit[i][j]: maximum allowable assignment from i to j"
  ],
  "decision_variables": [
    "x[i][j]: continuous, non-negative amount assigned from i to j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "supply_limit[i]: sum_{j in J} x[i][j] <= availability[i], for all i in I",
    "demand_satisfaction[j]: sum_{i in I} x[i][j] == requirement[j], for all j in J",
    "individual_capacity[i][j]: x[i][j] <= limit[i][j], for all i in I, j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to check for floating-point equality tolerance when verifying demand satisfaction constraints post-solution.
- Defining variables without upper bounds and then adding redundant individual capacity constraints, which increases model size unnecessarily.
- Using inconsistent indexing between parameter matrices and variable creation loops, leading to incorrect model construction.

## Solving stage

### Strategy Overview
Solve the LP using a dedicated solver (e.g., CBC, GLOP) with explicit status checks, solution validation, and fallback mechanisms. Focus on obtaining a verified, optimal solution.

### Step 1 - Select and Configure Solver
- Choose an appropriate LP solver (e.g., `GLOP` for pure LP, `CBC` for robustness).
- Set solver parameters such as time limits and optimality tolerances based on problem scale and precision requirements.

### Step 2 - Execute Solve and Check Status
- Invoke the solver and capture the termination status.
- Check for optimal or feasible termination condition before attempting to extract solution values; handle infeasible/unbounded statuses gracefully.

### Step 3 - Extract and Validate Solution
- Retrieve variable values, filtering for non-zero assignments using a small numerical tolerance.
- Programmatically verify all constraint types (supply, demand, individual limits) against the solved values to confirm feasibility.

### Step 4 - Report Results and Handle Failures
- Output a structured summary including objective value, key assignments, and utilization statistics.
- If the solver fails, provide diagnostic information (e.g., total capacity vs. demand) to aid debugging.

### Code Usage
```python
# build model from formulation
import pulp

# Define data placeholders
# I = [...], J = [...]
# availability = {...}, requirement = {...}, cost = {...}, limit = {...}

prob = pulp.LpProblem("Assignment", pulp.LpMinimize)
# Create variables with upper bounds
x = {}
for i in I:
    for j in J:
        x[i, j] = pulp.LpVariable(f"x_{i}_{j}", lowBound=0, upBound=limit[i][j])

# Objective
prob += pulp.lpSum(cost[i][j] * x[i, j] for i in I for j in J)

# Constraints
for i in I:
    prob += pulp.lpSum(x[i, j] for j in J) <= availability[i]
for j in J:
    prob += pulp.lpSum(x[i, j] for i in I) == requirement[j]

# solve with status / termination checks
prob.solve(pulp.PULP_CBC_CMD(msg=False))
if pulp.LpStatus[prob.status] == 'Optimal':
    # Extract and validate solution
    solution = { (i,j): pulp.value(x[i,j]) for i in I for j in J if pulp.value(x[i,j]) > 1e-6 }
    # ... validation logic ...
else:
    print(f"Solver status: {pulp.LpStatus[prob.status]}")
    # Handle failure
```

### Common Pitfalls
- Assuming the solver status string is directly comparable without using the library's status mapping (e.g., using `prob.status == 1` instead of `pulp.LpStatus[prob.status] == 'Optimal'`).
- Not using a tolerance when checking for non-zero values, potentially missing very small assignments due to numerical precision.
- Omitting solver time limits for large-scale problems, risking long, unresponsive execution.

# Workflow 2 (Abstract Modeling Library)

## Modeling stage

### Strategy Overview
Model the problem using an abstract modeling library (e.g., Pyomo) that separates the formulation from the solver. This approach uses declarative constraint rules and encapsulated parameters for maintainability and solver independence.

### Step 1 - Encapsulate Model Data
- Define Pyomo `Set` objects for supply and demand node indices.
- Define Pyomo `Param` objects (or similar) to store availability, requirements, costs, and limits, attaching them directly to the model.

### Step 2 - Declare Decision Variables
- Create a continuous, non-negative variable indexed over the supply-demand pairs.
- Use the `NonNegativeReals` domain to enforce non-negativity; upper bounds can be enforced via constraints or later checks.

### Step 3 - Define Constraint Rules
- Create a rule-based constraint for supply limits, summing variables over the demand set for each supply node.
- Create a rule-based constraint for demand satisfaction, summing variables over the supply set for each demand node.
- Create a rule-based constraint for individual capacity limits, comparing each variable to its corresponding parameter.

### Step 4 - Declare Objective Rule
- Define the objective function as a summation rule over all indices, referencing the cost parameter and decision variables.

### Formulation Template
```json
{
  "sets": [
    "I: set of supply nodes",
    "J: set of demand nodes"
  ],
  "parameters": [
    "availability: indexed over I",
    "requirement: indexed over J",
    "cost: indexed over IxJ",
    "limit: indexed over IxJ"
  ],
  "decision_variables": [
    "x: indexed over IxJ, domain=NonNegativeReals"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i,j] * x[i,j] for i in I, j in J )"
  },
  "constraints": [
    "supply_rule(i): sum( x[i,j] for j in J ) <= availability[i]",
    "demand_rule(j): sum( x[i,j] for i in I ) == requirement[j]",
    "capacity_rule(i,j): x[i,j] <= limit[i,j]"
  ]
}
```

### Common Pitfalls
- Referencing external data dictionaries directly inside constraint rules instead of using model `Param` objects, which breaks solver independence.
- Forgetting to deactivate the `tee` flag for solver output in production, leading to cluttered logs.
- Not pre-validating that total supply capacity meets total demand, which can lead to avoidable infeasibility errors from the solver.

## Solving stage

### Strategy Overview
Solve the abstract model using a compatible solver interface, with careful attention to solver status, solution loading, and post-solution validation. Leverage the library's ability to switch solvers seamlessly.

### Step 1 - Select Solver and Set Options
- Instantiate a solver object (e.g., `pyo.SolverFactory('cbc')`).
- Configure solver-specific options such as time limit (`seconds`) and optimality tolerance (`ratio`).

### Step 2 - Solve and Inspect Termination Condition
- Execute the solve command with `load_solutions=False` to first obtain results without loading values.
- Check the solver termination condition (`optimal`, `feasible`, `infeasible`, etc.) and status before proceeding.

### Step 3 - Load and Validate Solution
- If termination is acceptable, load the solution into the model instance.
- Iterate through constraints and variables to compute actual values, comparing them against parameters to validate feasibility.

### Step 4 - Export Results and Manage Failures
- Extract non-zero variable values and compile key performance indicators (total cost, utilization).
- In case of solver failure, output a structured error message with solver diagnostics and a summary of the infeasibility analysis.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_list)  # I_list placeholder
model.J = pyo.Set(initialize=J_list)  # J_list placeholder

model.availability = pyo.Param(model.I, initialize=availability_dict)
model.requirement = pyo.Param(model.J, initialize=requirement_dict)
model.cost = pyo.Param(model.I, model.J, initialize=cost_dict)
model.limit = pyo.Param(model.I, model.J, initialize=limit_dict)

model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

def obj_rule(m):
    return pyo.sum(m.cost[i,j] * m.x[i,j] for i in m.I for j in m.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def supply_rule(m, i):
    return pyo.sum(m.x[i,j] for j in m.J) <= m.availability[i]
model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

def demand_rule(m, j):
    return pyo.sum(m.x[i,j] for i in m.I) == m.requirement[j]
model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, tee=False, load_solutions=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    model.solutions.load_from(results)
    # Extract and validate solution
    solution = { (i,j): pyo.value(model.x[i,j]) for i in model.I for j in model.J if pyo.value(model.x[i,j]) > 1e-6 }
    # ... validation logic ...
else:
    print(f"Solver terminated with condition: {results.solver.termination_condition}")
    # Handle failure
```

### Common Pitfalls
- Loading solutions automatically without checking termination condition first, which can raise exceptions for infeasible models.
- Using a solver factory string that is not available in the current environment, causing a runtime error.
- Neglecting to set a time limit for the solver, potentially allowing it to run indefinitely on large or difficult instances.
