---
name: Transportation Problem Solver
description: |
  Model and solve capacitated transportation problems with supply-demand balance and arc capacity constraints using linear programming.
---

# Workflow 1 (Google OR-Tools LP)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using the OR-Tools API, leveraging its efficient variable creation with built-in bounds and constraint builders for a clean, matrix-like representation.

### Step 1 - Define Data Structures
- Organize supply, demand, cost, and capacity data as indexed lists or dictionaries for clarity.
- Use zero-based integer indexing for supply centers (`i`) and demand locations (`j`).

### Step 2 - Create Decision Variables
- Instantiate a non-negative flow variable for each arc `(i, j)`.
- Set the variable's upper bound directly to the arc capacity during creation for efficiency, avoiding separate inequality constraints.

### Step 3 - Formulate Constraints
- Add a linear equality constraint for each supply center: sum of outgoing flows equals its supply.
- Add a linear equality constraint for each demand location: sum of incoming flows equals its demand.

### Step 4 - Define Objective
- Build a linear expression summing the product of each flow variable and its corresponding unit cost.
- Set the model objective to minimize this total cost.

### Formulation Template
```json
{
  "sets": [
    "supply_centers",
    "demand_locations"
  ],
  "parameters": [
    "supply[supply_centers]",
    "demand[demand_locations]",
    "cost[supply_centers][demand_locations]",
    "capacity[supply_centers][demand_locations]"
  ],
  "decision_variables": [
    "flow[supply_centers][demand_locations] >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * flow[i][j] for i in supply_centers for j in demand_locations)"
  },
  "constraints": [
    "supply_constraint[i]: sum(flow[i][j] for j in demand_locations) == supply[i]",
    "demand_constraint[j]: sum(flow[i][j] for i in supply_centers) == demand[j]",
    "capacity_constraint[i][j]: flow[i][j] <= capacity[i][j] (enforced as variable bound)"
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand, which is required for feasibility with equality constraints.
- Adding redundant capacity constraints as separate inequalities instead of using the more efficient variable upper bounds.
- Using inconsistent indexing between data arrays and variable creation loops, leading to mismatched parameters.

## Solving stage

### Strategy Overview
Solve the LP model using the GLOP solver, implement robust status checking, and validate the solution against the original constraints to ensure numerical correctness.

### Step 1 - Instantiate and Configure Solver
- Create a GLOP solver instance with error handling for backend availability.
- Optionally set solver parameters like time limits or tolerances if needed.

### Step 2 - Solve and Check Status
- Invoke the solver and capture the result status.
- Accept both `OPTIMAL` and `FEASIBLE` statuses as successful solves.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value and all flow variable values.
- Programmatically verify that supply, demand, and capacity constraints are satisfied within a small numerical tolerance (e.g., 1e-6).
- Report any constraint violations for debugging.

### Step 4 - Output Structured Results
- Print the optimal cost and a summary of non-zero flows.
- Provide verification details to confirm solution correctness.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
if solver is None:
    raise Exception('Solver backend not available.')
# ... (variable and constraint creation)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    # Extract and validate flows
    for i in range(num_supply):
        total_flow = sum(flow[i][j].solution_value() for j in range(num_demand))
        # Verify against supply[i] within tolerance
    # ... (similar validation for demand and capacity)
else:
    print('No solution found.')
```

### Common Pitfalls
- Failing to check solver status before accessing solution values, which can cause runtime errors.
- Using absolute equality (`==`) for floating-point comparisons of constraint satisfaction; always use a tolerance.
- Not handling the case where the solver returns `FEASIBLE` (but not proven optimal) differently from `OPTIMAL`, if required.

# Workflow 2 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo's abstract or concrete model constructs, separating data from model structure for flexibility and using an open-source solver like CBC or GLPK.

### Step 1 - Define Model and Sets
- Create a Pyomo `ConcreteModel` or `AbstractModel`.
- Define `Set` components for supply centers and demand locations.

### Step 2 - Declare Parameters
- Declare `Param` components for supply, demand, cost, and capacity, indexed by the appropriate sets.
- Load data into these parameters, either inline or from an external source.

### Step 3 - Define Variables
- Create a `Var` component for flows, indexed over the supply and demand sets.
- Specify the domain as `NonNegativeReals`.

### Step 4 - Build Constraints and Objective
- Use `Constraint` and `Objective` components with rule functions or direct expressions.
- Implement supply and demand as equality constraints and capacity as an inequality constraint (or as a variable bound).

### Formulation Template
```json
{
  "sets": [
    "I (supply centers)",
    "J (demand locations)"
  ],
  "parameters": [
    "S[i in I]",
    "D[j in J]",
    "C[i in I][j in J]",
    "U[i in I][j in J]"
  ],
  "decision_variables": [
    "x[i in I][j in J] >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(C[i][j] * x[i][j] for i in I for j in J)"
  },
  "constraints": [
    "supply[i in I]: sum(x[i][j] for j in J) == S[i]",
    "demand[j in J]: sum(x[i][j] for i in I) == D[j]",
    "capacity[i in I][j in J]: x[i][j] <= U[i][j]"
  ]
}
```

### Common Pitfalls
- Using an `AbstractModel` without properly separating data initialization, leading to errors when solving.
- Defining constraint rules with incorrect indexing or scope, causing Pyomo to create unexpected constraints.
- Not verifying parameter data (e.g., non-negative capacities) before model construction, which can cause solver failures.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., for CBC), implement a robust solution loading pattern, and perform post-solution validation to ensure reliability.

### Step 1 - Select and Configure Solver
- Use `SolverFactory` to instantiate the desired solver (e.g., `'cbc'`).
- Set solver options such as time limit, optimality gap, and verbosity level.

### Step 2 - Solve with Status Checking
- Call `solve(model, ...)` with `load_solutions=False` to separate solving from solution loading.
- Check the solver status (`SolverStatus.ok`) and termination condition (`optimal` or `feasible`).

### Step 3 - Load and Validate Solution
- If the solve was successful, manually load the solution into the model.
- Iterate through constraints and variables to verify satisfaction within a numerical tolerance.
- Compute and report any significant violations.

### Step 4 - Report Results
- Extract the objective value and key variable values.
- Output results in a structured format suitable for downstream processing.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=supply_indices)
model.J = pyo.Set(initialize=demand_indices)
# ... (parameter, variable, constraint, objective definition)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model, load_solutions=False)
if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    model.solutions.load_from(results)
    # Validate constraints
    for i in model.I:
        total = sum(model.x[i,j].value for j in model.J)
        # Check against model.S[i] with tolerance
else:
    print('Solve failed:', results.solver.termination_condition)
```

### Common Pitfalls
- Forgetting to set `load_solutions=False` and then accessing `.value` attributes before checking solve status, which may contain stale values.
- Not using a tolerance when checking constraint satisfaction, leading to false failures due to floating-point arithmetic.
- Assuming the solver always returns `optimal`; always handle `feasible` and other termination conditions appropriately.
