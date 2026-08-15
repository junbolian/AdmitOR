---
name: Capacitated Facility Location with Fixed Costs
description: |
  Model and solve mixed-integer linear programs for selecting facilities and allocating flows to meet demand at minimum total cost (fixed + variable), using either algebraic modeling with Pyomo or direct solver API with OR-Tools.

---

# Workflow 1 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Use Pyomo's algebraic modeling to declaratively define sets, parameters, variables, and constraints. This approach separates problem specification from solver execution, enabling solver-agnostic formulation and clear constraint expression via rules.

### Step 1 - Define Sets and Parameters
- Define `facilities` and `customers` as Pyomo `Set` objects.
- Load parameters as Pyomo `Param` objects: `fixed_cost`, `capacity`, `demand`, and `shipping_cost` (indexed by facility and customer).
- Use dictionaries for parameter initialization to ensure data integrity and easy access.

### Step 2 - Create Decision Variables
- Create binary variables `y[i]` for facility selection (`pyo.Binary`).
- Create continuous non-negative variables `x[i,j]` for flow allocation (`pyo.NonNegativeReals`).
- Use descriptive variable names (`y`, `x`) aligned with standard notation.

### Step 3 - Formulate Objective Function
- Construct a linear objective: minimize total cost = sum of fixed costs (`fixed_cost[i] * y[i]`) plus variable costs (`shipping_cost[i,j] * x[i,j]`).
- Use `pyo.Objective` with `sense=pyo.minimize` and an expression built from sums over the defined sets.

### Step 4 - Implement Core Constraints
- **Demand Satisfaction**: For each customer `j`, add an equality constraint: `sum(x[i,j] for i in facilities) == demand[j]`.
- **Capacity and Activation Linking**: For each facility `i`, add an inequality constraint: `sum(x[i,j] for j in customers) <= capacity[i] * y[i]`. This enforces both the capacity limit and the logical link that flow is zero if the facility is closed.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["fixed_cost[facilities]", "capacity[facilities]", "demand[customers]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i] for i in facilities) + sum(shipping_cost[i,j] * x[i,j] for i in facilities for j in customers)"
  },
  "constraints": [
    "sum(x[i,j] for i in facilities) == demand[j] for each j in customers",
    "sum(x[i,j] for j in customers) <= capacity[i] * y[i] for each i in facilities"
  ]
}
```

### Common Pitfalls
- Forgetting to link flow to facility selection, resulting in solutions where closed facilities ship product.
- Using incorrect constraint bounds in Pyomo rules (e.g., using `<=` where `==` is required for demand).
- Defining parameters outside the model scope, causing errors during rule evaluation.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source MILP solver (e.g., CBC, HiGHS) via `SolverFactory`. Configure solver options for performance, check termination status rigorously, and extract/verify the solution programmatically.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = SolverFactory('cbc')` or `SolverFactory('highs')`.
- Set key options: `time_limit` for runtime control, `ratio` or `mip_rel_gap=0.0` for exact optimality, and `threads` for parallelism.
- Solve the model: `results = solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Import `SolverStatus` and `TerminationCondition` from `pyomo.opt`.
- Verify: `if results.solver.status == SolverStatus.ok and results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:`.
- If status is not ok or termination is not acceptable, output a structured error message.

### Step 3 - Extract and Validate Solution
- Extract objective value: `total_cost = pyo.value(model.obj)`.
- Identify open facilities: `[i for i in model.F if pyo.value(model.y[i]) > 0.5]`.
- Compute derived metrics: total flow per facility and per customer to verify constraints.
- Recalculate the objective from variable values to confirm numerical consistency.

### Step 4 - Report Results
- Print total cost and its breakdown (fixed vs. variable).
- List open facilities with their utilized capacity.
- Output shipment allocation for non-zero flows.
- Optionally, return results in a standardized JSON format for integration.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (following Modeling stage steps)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, objective, constraints

# Solve
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
solver.options['threads'] = 4
results = solver.solve(model)

# Check status and termination
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = float(pyo.value(model.obj))
    open_facs = [i for i in model.F if pyo.value(model.y[i]) > 0.5]
    # ... extract and report solution
else:
    print(f'RESULT_JSON:{{"status":"failed","reason":"solver_error","solver_status":"{status}","termination":"{term}"}}')
```

### Common Pitfalls
- Not checking both solver status and termination condition before extracting values.
- Setting invalid solver options (e.g., negative `mip_rel_gap`).
- Assuming solution values exist when the solver failed, leading to attribute errors.

# Workflow 2 (OR-Tools Direct Solver API)

## Modeling stage

### Strategy Overview
Use Google OR-Tools' direct solver API (`pywraplp`) to imperatively build the MILP. This approach offers fine-grained control over variable and constraint creation, suitable for performance-critical or embedded applications.

### Step 1 - Initialize Solver and Data Structures
- Create solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")` or `"CBC"`.
- Set solver controls: `solver.SetTimeLimit(milliseconds)` and `solver.SetNumThreads(n)`.
- Store problem data in dictionaries or lists for efficient access.

### Step 2 - Create Variables
- Create binary variables for facility selection: `y[i] = solver.IntVar(0, 1, f"y_{i}")`.
- Create continuous variables for flow: `x[i,j] = solver.NumVar(0, solver.infinity(), f"x_{i}_{j}")`.
- Use descriptive naming patterns to aid debugging.

### Step 3 - Build Objective Function
- Create objective: `objective = solver.Objective()`.
- Add fixed cost terms: `objective.SetCoefficient(y[i], fixed_cost[i])`.
- Add variable cost terms: `objective.SetCoefficient(x[i,j], shipping_cost[i][j])`.
- Set minimization: `objective.SetMinimization()`.

### Step 4 - Add Constraints via Coefficient Assignment
- **Demand Satisfaction**: For each customer `j`, create an equality constraint: `ct = solver.Constraint(demand[j], demand[j])`; then `ct.SetCoefficient(x[i,j], 1)` for all `i`.
- **Capacity and Activation Linking**: For each facility `i`, create an inequality constraint: `ct = solver.Constraint(-solver.infinity(), 0)`; then `ct.SetCoefficient(x[i,j], 1)` for all `j` and `ct.SetCoefficient(y[i], -capacity[i])`. This implements `sum_j x[i,j] - capacity[i]*y[i] <= 0`.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["fixed_cost[facilities]", "capacity[facilities]", "demand[customers]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i]) + sum(shipping_cost[i,j] * x[i,j])"
  },
  "constraints": [
    "sum(x[i,j] over i) == demand[j] for each j",
    "sum(x[i,j] over j) - capacity[i] * y[i] <= 0 for each i"
  ]
}
```

### Common Pitfalls
- Incorrectly setting constraint bounds (e.g., using `solver.Constraint(0, 0)` for a `<= 0` constraint).
- Adding redundant linking constraints (both aggregate and per-arc) that can cause infeasibility.
- Misplacing the negative sign in the linking constraint coefficient for the binary variable.

## Solving stage

### Strategy Overview
Call the solver, check the result status, extract variable values, and perform post-solution verification. The direct API provides immediate access to solution values and solver statistics.

### Step 1 - Solve and Interpret Status
- Execute: `status = solver.Solve()`.
- Map status codes: `pywraplp.Solver.OPTIMAL` (0), `FEASIBLE` (1), `INFEASIBLE` (2), etc.
- Proceed only if `status in (solver.OPTIMAL, solver.FEASIBLE)`.

### Step 2 - Extract Solution Values
- Get objective value: `total_cost = objective.Value()` or recompute from variable values.
- Retrieve binary decisions: `y[i].solution_value() > 0.5`.
- Retrieve flow amounts: `x[i,j].solution_value()`.
- Store results in structured dictionaries or lists.

### Step 3 - Verify Solution Feasibility
- For each customer, compute total received flow and compare to demand within a small tolerance.
- For each facility, compute total outflow and verify it does not exceed capacity and is zero if the facility is closed.
- Recalculate total cost from extracted values to confirm objective value accuracy.

### Step 4 - Output Structured Results
- Print total cost in a parseable format (e.g., `RESULT:{total_cost}`).
- Output open facilities and their shipments.
- For failures, output a JSON with status code and reason.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model (following Modeling stage steps)
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)
# ... create variables, objective, constraints

# Solve
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    # Alternative recomputation:
    # total_cost = sum(fixed_cost[i] * y[i].solution_value() for i in facilities) + \
    #               sum(shipping_cost[i][j] * x[i,j].solution_value() for i in facilities for j in customers)
    open_facs = [i for i in facilities if y[i].solution_value() > 0.5]
    print(f"RESULT:{total_cost}")
    # ... further reporting
else:
    print(f'RESULT_JSON:{{"status":"failed","reason":"infeasible_or_error","solver_status":{int(status)}}}')
```

### Common Pitfalls
- Not handling solver status codes correctly, leading to extraction errors on infeasible problems.
- Misinterpreting variable solution values (binary variables as continuous).
- Skipping feasibility checks, missing constraint violations due to numerical tolerances.
