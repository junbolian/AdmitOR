---
name: Capacitated Facility Location Solver
description: |
  Model and solve capacitated facility location problems with binary facility selection and continuous allocation using MILP, with workflows for OR-Tools and Pyomo backends.
---

# Workflow 1 (OR-Tools MILP)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using the OR-Tools (pywraplp) modeling API. This approach directly maps binary activation and continuous flow variables to the solver's native constructs, enabling efficient solving with SCIP or CBC.

### Step 1 - Define Data Structures
- Store problem parameters in indexed lists or arrays for facilities `i` and clients `j`.
- Define `fixed_costs[i]`, `shipping_costs[i][j]`, `demands[j]`, and `capacities[i]`.

### Step 2 - Create Decision Variables
- Create binary variables `y[i]` for facility activation (`0`/`1`).
- Create continuous, non-negative variables `x[i][j]` for allocation from facility `i` to client `j`.

### Step 3 - Formulate Objective Function
- Build a linear objective: minimize total fixed cost plus total transportation cost.
- Expression: `sum_i fixed_costs[i] * y[i] + sum_i sum_j shipping_costs[i][j] * x[i][j]`.

### Step 4 - Add Demand Satisfaction Constraints
- For each client `j`, add a constraint ensuring total incoming allocation meets demand.
- Constraint: `sum_i x[i][j] == demands[j]`.

### Step 5 - Add Capacity-Activation Linking Constraints
- For each facility `i`, add a constraint linking total outflow to its capacity and activation status.
- Constraint: `sum_j x[i][j] <= capacities[i] * y[i]`. This enforces zero flow if facility is closed.

### Formulation Template
```json
{
  "sets": [
    "facilities",
    "clients"
  ],
  "parameters": [
    "fixed_costs[facilities]",
    "shipping_costs[facilities][clients]",
    "demands[clients]",
    "capacities[facilities]"
  ],
  "decision_variables": [
    "y[facilities] ∈ {0,1}",
    "x[facilities][clients] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_i fixed_costs[i] * y[i] + sum_i sum_j shipping_costs[i][j] * x[i][j]"
  },
  "constraints": [
    "demand_satisfaction[j]: sum_i x[i][j] = demands[j] for all j",
    "capacity_link[i]: sum_j x[i][j] <= capacities[i] * y[i] for all i"
  ]
}
```

### Common Pitfalls
- Forgetting to set variable bounds (e.g., `x[i][j]` should be `>= 0`).
- Incorrectly indexing cost matrices or parameter lists, leading to shape mismatches.
- Using a strict equality for demand when partial fulfillment is allowed; use `<=` instead if appropriate.

## Solving stage

### Strategy Overview
Solve the MILP model using the OR-Tools wrapper for SCIP or CBC. Configure solver parameters for performance, solve, and rigorously check the status before extracting and validating the solution.

### Step 1 - Initialize Solver and Set Parameters
- Instantiate the solver (e.g., `solver = pywraplp.Solver.CreateSolver('SCIP')`).
- Set a time limit (e.g., `solver.SetTimeLimit(60000)` for 60 seconds) and number of threads (e.g., `solver.SetNumThreads(4)`).
- Set a relative optimality gap if an approximate solution is acceptable (e.g., `solver.SetRelativeGapTolerance(1e-4)`).

### Step 2 - Build Model and Solve
- Use loops to create variables, add constraints, and set the objective coefficient as defined in the modeling stage.
- Call `solver.Solve()` and capture the result status.

### Step 3 - Check Solver Status
- Check if the status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error messages or diagnostics.
- If status is not `OPTIMAL` or `FEASIBLE`, investigate model formulation or solver parameters.

### Step 4 - Extract and Validate Solution
- If feasible, extract total cost via `objective.Value()`.
- Extract opened facilities where `y[i].solution_value() > 0.5`.
- Extract allocation values `x[i][j].solution_value()` and verify demand satisfaction and capacity constraints numerically.

### Step 5 - Report and Analyze Results
- Print a cost breakdown (fixed vs. transportation).
- List opened facilities and their total utilization.
- Optionally, re-solve with a different solver backend to verify optimality.

### Code Usage
```python
# Example using OR-Tools (pywraplp)
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('SCIP')
if not solver:
    raise RuntimeError('Solver not available.')
solver.SetTimeLimit(60000)  # milliseconds
solver.SetNumThreads(4)

# 2. Build model (variables, constraints, objective) as per formulation
# ... (implementation of modeling steps)

# 3. Solve and check status
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_cost = objective.Value()
    # Extract solution...
else:
    print('Solver did not find a feasible solution.')
    # Handle infeasibility or unboundedness
```

### Common Pitfalls
- Not checking solver status before accessing solution values, causing runtime errors.
- Setting an overly restrictive time limit or optimality gap for large instances, leading to premature termination.
- Misinterpreting `FEASIBLE` as `OPTIMAL`; report the optimality gap if available.

# Workflow 2 (Pyomo with CBC/HiGHS)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model syntax, separating data from structure. This approach provides flexibility and clarity, and the model can be solved with various backends like CBC or HiGHS.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `facilities` and `clients`.
- Declare `Param` objects for `fixed_cost`, `shipping_cost`, `demand`, and `capacity`, indexed appropriately.

### Step 2 - Define Decision Variables
- Define `Var` objects: binary `y[facilities]` and non-negative continuous `x[facilities, clients]`.

### Step 3 - Formulate Objective Rule
- Define an objective rule that sums fixed and transportation costs.
- Use Pyomo's `summation` or explicit loops within the rule.

### Step 4 - Define Constraint Rules
- Create a demand satisfaction constraint rule: for each `j` in `clients`, `sum(x[i,j] for i in facilities) == demand[j]`.
- Create a capacity-linking constraint rule: for each `i` in `facilities`, `sum(x[i,j] for j in clients) <= capacity[i] * y[i]`.

### Formulation Template
```json
{
  "sets": [
    "model.facilities",
    "model.clients"
  ],
  "parameters": [
    "model.fixed_cost[model.facilities]",
    "model.shipping_cost[model.facilities, model.clients]",
    "model.demand[model.clients]",
    "model.capacity[model.facilities]"
  ],
  "decision_variables": [
    "model.y[model.facilities] ∈ Binary",
    "model.x[model.facilities, model.clients] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.fixed_cost[i] * model.y[i] for i in model.facilities) + sum(model.shipping_cost[i,j] * model.x[i,j] for i in model.facilities for j in model.clients)"
  },
  "constraints": [
    "def demand_rule(model, j): return sum(model.x[i,j] for i in model.facilities) == model.demand[j]",
    "def capacity_rule(model, i): return sum(model.x[i,j] for j in model.clients) <= model.capacity[i] * model.y[i]"
  ]
}
```

### Common Pitfalls
- Using concrete models with hard-coded data, reducing reusability; prefer abstract models with parameter initialization.
- Incorrectly scoping index variables within rule functions.
- Forgetting to deactivate constraints or objectives when modifying the model for scenario analysis.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or HiGHS solver via `SolverFactory`. Configure solver options, solve, and implement robust solution loading and validation to ensure results are reliable.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = SolverFactory('cbc')` or `SolverFactory('highs')`.
- Set options: time limit (`seconds`), relative gap (`ratio`), and thread count if supported (e.g., `threads` for CBC).

### Step 2 - Solve with Status Checking
- Call `results = solver.solve(model, tee=False, load_solutions=False)`.
- Check `results.solver.status` and `results.solver.termination_condition`. Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Load Solution Safely
- If status checks pass, load the solution: `model.solutions.load_from(results)`.
- Implement a try-except block to handle `ValueError` or `RuntimeError` if the solution is invalid.

### Step 4 - Validate Solution Feasibility
- Programmatically verify constraints: check if `sum(model.x[i,j]() for i in model.facilities)` equals `model.demand[j]` for each client `j` (within a small tolerance).
- Verify capacity constraints similarly.

### Step 5 - Extract and Report Metrics
- Compute total fixed cost: `sum(model.fixed_cost[i]() * model.y[i]() for i in model.facilities)`.
- Compute total transportation cost similarly.
- List opened facilities where `model.y[i]() > 0.5`.

### Step 6 - Implement Solver Fallback
- If the primary solver fails, try a fallback (e.g., `glpk` after `cbc`). Log the attempt and result.

### Code Usage
```python
# Example using Pyomo with CBC
from pyomo.environ import SolverFactory

# 1. Instantiate solver and set options
solver = SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0  # for exact solution
# solver.options['threads'] = 4  # if supported

# 2. Solve with careful status checking
results = solver.solve(model, tee=False, load_solutions=False)

if results.solver.status == SolverStatus.ok and results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]:
    # 3. Load solution
    model.solutions.load_from(results)
    # 4. Validate and extract...
else:
    print('Solver failed or did not find a feasible solution.')
    # Implement fallback or diagnostics
```

### Common Pitfalls
- Loading solutions without checking termination condition, leading to `ValueError` for infeasible problems.
- Not using `load_solutions=False`, which can cause conflicts when post-processing failed solves.
- Assuming solver availability; always implement fallback logic or environment checks.
