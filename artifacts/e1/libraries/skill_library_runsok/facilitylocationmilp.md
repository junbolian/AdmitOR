---
name: FacilityLocationMILP
description: |
  Model and solve capacitated facility location problems with fixed opening costs and linear shipping costs using MILP, with systematic handling of incomplete data and solver diagnostics.
---

# Workflow 1 (Pyomo-Based Modeling)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a declarative, algebraic modeling approach, separating problem specification from solver choice. It emphasizes data validation, clear set/parameter definitions, and robust constraint rules.

### Step 1 - Define Model Structure
- Define a `ConcreteModel` and create `Set` objects for facilities and customers.
- Use `Param` objects to store all input data (capacities, demands, fixed costs, shipping costs) for clarity and maintainability.
- Declare decision variables: `Binary` for facility opening (`y[f]`) and `NonNegativeReals` for shipments (`x[f,c]`).

### Step 2 - Formulate Objective and Constraints
- Formulate the objective to minimize total cost: fixed costs plus linear shipping costs.
- Add demand satisfaction constraints ensuring each customer's total shipment equals its demand.
- Add capacity-linking constraints using `sum(x[f,c] for c) <= capacity[f] * y[f]` to enforce zero shipments from closed facilities and respect capacity.
- Optionally, add logical constraints to explicitly link shipments to open facilities if needed for clarity.

### Step 3 - Handle Incomplete or Patterned Data
- For incomplete shipping cost matrices, implement a data-filling rule (e.g., use average known cost per facility, min, max, or a default value).
- For cyclic/repeating cost patterns, implement a lookup using modulo indexing: `cost[f][c] = base_pattern[f][c % pattern_length]`.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["capacity[facilities]", "demand[customers]", "fixed_cost[facilities]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[f] * y[f] for f in facilities) + sum(shipping_cost[f,c] * x[f,c] for f in facilities, c in customers)"
  },
  "constraints": [
    "demand_satisfaction[c in customers]: sum(x[f,c] for f in facilities) == demand[c]",
    "capacity_limit[f in facilities]: sum(x[f,c] for c in customers) <= capacity[f] * y[f]"
  ]
}
```

### Common Pitfalls
- Forgetting to check total capacity vs. total demand for basic feasibility before solving.
- Incorrectly implementing the capacity-linking constraint as `sum(x[f,c]) <= capacity[f]` without multiplying by `y[f]`, which fails to prevent shipments from closed facilities.
- Using equality bounds `(0, 0)` for inequality constraints instead of the correct `(-inf, 0)`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source MILP solver (e.g., HiGHS, CBC) with appropriate performance settings. Focus on robust solution extraction, validation, and cost breakdown.

### Step 1 - Configure and Execute Solver
- Instantiate a solver factory (e.g., `SolverFactory('highs')`).
- Set solver options: `time_limit=30`, `mip_rel_gap=0.0` for optimality, and `threads=4` if supported.
- Solve the model and capture the results object.

### Step 2 - Validate Solution and Status
- Check the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`). Proceed only if status is `ok` and termination is `optimal` or `feasible`.
- If infeasible, first verify data integrity and constraint logic before adjusting solver parameters.

### Step 3 - Extract and Analyze Results
- Extract the objective value using `pyo.value(model.obj)`.
- Determine open facilities where `pyo.value(model.y[f]) > 0.5`.
- Extract positive shipments where `pyo.value(model.x[f,c]) > tolerance`.
- Compute and report cost breakdowns: total fixed cost and total shipping cost separately for validation.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (example structure)
model = pyo.ConcreteModel()
model.F = pyo.Set(initialize=facilities_list)
model.C = pyo.Set(initialize=customers_list)
# ... define Params, Vars, Objective, Constraints

# Solve
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model)

# Status / termination checks
if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    obj_val = pyo.value(model.obj)
    open_facs = [f for f in model.F if pyo.value(model.y[f]) > 0.5]
    # ... extract shipments and compute cost breakdowns
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking solver termination condition, leading to extraction of invalid results.
- Using a loose tolerance (e.g., 0.5) for binary variable interpretation instead of a small epsilon (e.g., 1e-6).
- Setting the `threads` option on a solver that does not support it, causing an error.

# Workflow 2 (OR-Tools / Google CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver for MILP, employing an imperative, coefficient-by-coefficient modeling style. It is suited for direct API control and scenarios requiring advanced solver features or custom callbacks.

### Step 1 - Initialize Solver and Variables
- Create a `CpModel` object.
- Create Boolean (binary) variables for facility opening using `model.NewBoolVar()`.
- Create continuous variables for shipments using `model.NewNumVar(lb=0, ub=capacity[f], name)` or as linear expressions.

### Step 2 - Build Linear Constraints
- For each customer, create a linear constraint `sum(x[f,c] for f) == demand[c]`.
- For each facility, create the capacity-linking constraint: `sum(x[f,c] for c) <= capacity[f] * y[f]`. This must be added as a linear constraint where `y[f]` is a Boolean variable.
- Use `model.AddLinearConstraint(expr, lb, ub)` or `Add(sum(...) == ...)`.

### Step 3 - Define Objective Function
- Construct the objective expression as the sum of fixed cost terms (`fixed_cost[f] * y[f]`) and shipping cost terms (`shipping_cost[f,c] * x[f,c]`).
- Use `model.Minimize(objective_expr)` to set the minimization goal.

### Step 4 - Manage Incomplete Cost Data
- Before building the model, pre-process the shipping cost matrix to fill missing values using a chosen heuristic (average, min, max, pattern repetition).
- Store the processed costs in a structure accessible during objective construction.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["capacity[facilities]", "demand[customers]", "fixed_cost[facilities]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[f] * y[f] for f in facilities) + sum(shipping_cost[f,c] * x[f,c] for f in facilities, c in customers)"
  },
  "constraints": [
    "demand_satisfaction[c in customers]: sum(x[f,c] for f in facilities) == demand[c]",
    "capacity_limit[f in facilities]: sum(x[f,c] for c in customers) - capacity[f] * y[f] <= 0"
  ]
}
```

### Common Pitfalls
- Incorrectly linearizing the capacity constraint: the term `-capacity[f] * y[f]` must have a negative coefficient when moved to the LHS in `expr <= 0`.
- Setting infinite upper bounds on shipment variables, which can weaken solver performance; use `capacity[f]` as a natural upper bound.
- Not pre-processing incomplete cost data, leading to undefined coefficients in the objective.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with performance tuning, extract the solution, and perform rigorous validation of constraints and variable linkages.

### Step 1 - Configure Solver and Solve
- Create a `CpSolver` instance.
- Set solver parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 4`.
- Optionally, set a relative MIP gap: `solver.parameters.relative_gap_limit = 0.0`.
- Execute `solver.Solve(model)`.

### Step 2 - Diagnose Solution Status
- Check the status code: `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`.
- If status is `INFEASIBLE`, debug by simplifying the model (e.g., set all shipping costs to 1) to isolate formulation errors.

### Step 3 - Extract and Verify Solution
- For each binary variable `y[f]`, get its value using `solver.Value(y_var)`.
- For each continuous variable `x[f,c]`, get its value using `solver.Value(x_var)`.
- Programmatically verify all constraints: demand satisfaction, capacity limits, and the linkage that `x[f,c] > 0` implies `y[f] == 1`.
- Compute and report separate fixed and shipping cost totals from the solution values.

### Code Usage
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# Create variables
y = {f: model.NewBoolVar(f"y_{f}") for f in facilities}
x = {(f,c): model.NewNumVar(0, capacity[f], f"x_{f}_{c}") for f in facilities for c in customers}
# Add constraints
for c in customers:
    model.Add(sum(x[f,c] for f in facilities) == demand[c])
for f in facilities:
    model.Add(sum(x[f,c] for c in customers) <= capacity[f] * y[f])
# Set objective
obj_expr = sum(fixed_cost[f] * y[f] for f in facilities) + \
           sum(shipping_cost[f,c] * x[f,c] for f in facilities for c in customers)
model.Minimize(obj_expr)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 4
status = solver.Solve(model)

# Status / termination checks
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    obj_val = solver.ObjectiveValue()
    open_facs = [f for f in facilities if solver.Value(y[f]) == 1]
    # ... extract shipments and verify constraints
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming `solver.Value()` can be called on linear expressions; it must be called on variable objects.
- Not verifying that the capacity-linking constraint is active (i.e., shipments are zero for closed facilities) in the solution.
- Overlooking the need to scale large cost coefficients, which can cause numerical issues for the CP-SAT solver.
