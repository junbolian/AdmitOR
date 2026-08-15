---
name: Capacitated Facility Location Modeling and Solving
description: |
  A structured approach for modeling and solving capacitated facility location problems with fixed costs and linear shipping costs, using binary selection and continuous flow variables, with implementation guidance for both Pyomo and OR-Tools backends.
---

# Workflow 1 (Pyomo-based Modeling and Solving)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to separate problem formulation from data, creating a clean, maintainable model structure suitable for integration with various solvers.

### Step 1 - Define Sets and Parameters
- Define two distinct sets: one for facilities and one for customers.
- Create parameter dictionaries for fixed costs, capacities, customer demands, and per-unit shipping costs, ensuring they are indexed by the appropriate sets.

### Step 2 - Declare Decision Variables
- Declare binary variables for facility selection, indexed by the facility set.
- Declare continuous, non-negative variables for flow allocation, indexed by the Cartesian product of facility and customer sets.

### Step 3 - Formulate Objective and Constraints
- Formulate the objective as the sum of fixed costs (linear on binary variables) and variable shipping costs (linear on flow variables).
- Add equality constraints to ensure total flow to each customer meets its exact demand.
- Add inequality constraints to link total flow from a facility to its capacity and binary selection variable.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": [
    "fixed_cost[facility]",
    "capacity[facility]",
    "demand[customer]",
    "shipping_cost[facility, customer]"
  ],
  "decision_variables": [
    "y[facility] ∈ {0, 1}",
    "x[facility, customer] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i] for i in facilities) + sum(shipping_cost[i, j] * x[i, j] for i in facilities for j in customers)"
  },
  "constraints": [
    "demand_satisfaction[j]: sum(x[i, j] for i in facilities) == demand[j] for each customer j",
    "capacity_linking[i]: sum(x[i, j] for j in customers) <= capacity[i] * y[i] for each facility i"
  ]
}
```

### Common Pitfalls
- Forgetting to check solver status and termination condition before loading and extracting solution values, leading to runtime errors.
- Using inconsistent indexing between parameter dictionaries and variable declarations, causing key errors.
- Adding redundant per-flow linking constraints (`x[i,j] <= capacity[i] * y[i]`) when the aggregate capacity constraint already enforces the same logic, unnecessarily increasing model size.

## Solving stage

### Strategy Overview
This solving stage focuses on using Pyomo's `SolverFactory` interface, typically with the HiGHS or CBC solvers, emphasizing robust solution checking and error handling.

### Step 1 - Configure and Instantiate the Solver
- Instantiate the solver via `SolverFactory('solver_name')` (e.g., 'highs' or 'cbc').
- Set key options such as time limit, optimality gap tolerance (`mip_rel_gap`), and number of threads.

### Step 2 - Solve and Check Status
- Execute the solve command with `load_solutions=False` to prevent automatic loading before status verification.
- Check that `results.solver.status` equals `SolverStatus.ok` and `results.solver.termination_condition` indicates optimality or feasibility.

### Step 3 - Extract and Validate Solution
- If the solve was successful, load the solution into the model instance.
- Extract objective value and variable values, using a tolerance (e.g., `1e-6`) for floating-point comparisons.
- Programmatically verify that demand and capacity constraints are satisfied by the extracted flows.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
# ... (model construction as per Modeling Stage)
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1  # Use solver default
# solver.options['mip_rel_gap'] = 0.0  # For exact optimality
results = solver.solve(model, load_solutions=False, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    model.solutions.load_from(results)
    total_cost = pyo.value(model.obj)
    # ... extract and validate solution
else:
    # Handle infeasible or error status
    print(f"Solve failed: Status={results.solver.status}, Termination={results.solver.termination_condition}")
```

### Common Pitfalls
- Setting `mip_rel_gap` to an invalid value (like `-1` for HiGHS when expecting `0.0` for exact optimality); always check solver-specific option syntax.
- Assuming a solve was successful without checking `termination_condition`, potentially loading an incomplete or invalid solution.
- Not using `load_solutions=False` during the solve call, which can cause errors if the solver fails.

# Workflow 2 (OR-Tools-based Modeling and Solving)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools (pywraplp) for direct, imperative model construction, offering fine-grained control over variable and constraint creation, ideal for embedding within larger applications.

### Step 1 - Initialize Solver and Create Variables
- Create a solver instance (e.g., `SCIP` or `CBC` backend).
- Create binary variables for each facility using `solver.IntVar(0, 1, ...)`.
- Create continuous flow variables for each facility-customer pair using `solver.NumVar(0, infinity, ...)`.

### Step 2 - Build Objective Function
- Initialize the objective with `solver.Objective()`.
- Add the linear coefficient for each binary variable (fixed cost) and each flow variable (shipping cost).
- Set the objective sense to minimization.

### Step 3 - Add Constraints
- For each customer, create an equality constraint with lower and upper bound equal to the demand.
- For each facility, create an inequality constraint representing `sum(flows) - capacity * y <= 0` by setting an upper bound of 0 and adding coefficients appropriately.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": [
    "fixed_cost[facility]",
    "capacity[facility]",
    "demand[customer]",
    "shipping_cost[facility, customer]"
  ],
  "decision_variables": [
    "y[facility] ∈ {0, 1} (IntVar)",
    "x[facility, customer] ≥ 0 (NumVar)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i]) + sum(shipping_cost[i, j] * x[i, j])"
  },
  "constraints": [
    "demand_constr[j]: sum(x[i, j] for i) == demand[j]",
    "capacity_constr[i]: sum(x[i, j] for j) - capacity[i] * y[i] <= 0"
  ]
}
```

### Common Pitfalls
- Incorrectly creating a constraint with `solver.Constraint(0, 0)`, which forces an expression to equal 0, instead of `solver.Constraint(-infinity, 0)` for an inequality (`expr <= 0`).
- Adding both aggregate capacity linking and redundant per-flow linking constraints, which can make the problem infeasible if `M` values are inconsistent.
- Not verifying the fundamental feasibility of total demand versus total available capacity before attempting to solve.

## Solving stage

### Strategy Overview
This solving stage leverages OR-Tools' direct solver interface, focusing on performance tuning, solution extraction, and post-solution validation of constraints.

### Step 1 - Set Solver Parameters
- Set a time limit using `solver.SetTimeLimit()`.
- Configure the number of threads with `solver.SetNumThreads()`.
- Optionally set other solver-specific parameters via `solver.SetSolverSpecificParametersAsString()`.

### Step 2 - Solve and Interpret Status
- Call `solver.Solve()`.
- Check the returned status against constants like `pywraplp.Solver.OPTIMAL` or `FEASIBLE`.
- Do not proceed with solution extraction if the status indicates infeasibility or an error.

### Step 3 - Extract and Verify Solution
- Extract variable values using `.solution_value()`.
- Compute total costs and validate all constraints programmatically with a tolerance.
- Report key outputs: opened facilities, flow allocation, and cost breakdown.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (variable and constraint creation as per Modeling Stage)
# solve with status / termination checks
solver.SetTimeLimit(30000)  # Time limit in milliseconds
solver.SetNumThreads(4)
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    # Extract facility decisions: y[i].solution_value() > 0.5
    # Extract flows: x[(i, j)].solution_value()
    # ... validate constraints
else:
    # Handle infeasible or error status
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Trusting a non-`OPTIMAL`/`FEASIBLE` status and attempting to extract solution values, which may be undefined.
- Misinterpreting the constraint bounds in OR-Tools, leading to incorrect constraint logic (e.g., using `constraint = solver.Constraint(demand, demand)` correctly for equality, but `constraint = solver.Constraint(-infinity, 0)` for `expr <= 0`).
- Outputting pseudo-numeric answers or incomplete results when the solver fails; instead, output a structured error message.
