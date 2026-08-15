---
name: Minimum-Delivery Allocation with Participation Requirements
description: |
  Model and solve allocation problems with conditional minimum delivery thresholds, minimum contributor requirements, and capacity limits using mixed-integer linear programming.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a clean, declarative MILP. It separates data from model logic, enabling easy parameter updates and constraint verification.

### Step 1 - Define Sets and Parameters
- Declare abstract sets for `producers` and `contracts` to index the problem dimensions.
- Define parameter dictionaries for `cost`, `capacity`, `demand`, and `min_delivery` using `(producer, contract)` tuple keys for clarity.
- Use `pyo.Param` within the model to store these values, making them accessible during constraint rule evaluation.

### Step 2 - Create Dual Decision Variables
- Create a continuous variable `x[producer, contract]` (NonNegativeReals) for allocation quantities.
- Create a binary variable `y[producer, contract]` (Binary) to indicate participation (1 if a producer supplies a contract).
- This dual-variable structure is essential for modeling conditional constraints.

### Step 3 - Implement Linking and Conditional Constraints
- **Linking Constraint**: Enforce `x[i,j] <= capacity[i] * y[i,j]` to ensure allocation is zero if participation is zero, using capacity as the big-M value.
- **Minimum Delivery Constraint**: Enforce `x[i,j] >= min_delivery[i] * y[i,j]` to require a minimum quantity if participation is active (`y[i,j]=1`).
- These two constraints together correctly model the "if participating, deliver at least X" logic.

### Step 4 - Add Supply, Demand, and Contributor Constraints
- **Supply Capacity**: For each producer `i`, sum allocations across all contracts must not exceed `capacity[i]`.
- **Demand Requirement**: For each contract `j`, sum allocations from all producers must meet or exceed `demand[j]`.
- **Minimum Contributors**: For each contract `j`, the sum of binary participation variables must be at least `K_j` (the required minimum number of suppliers).

### Formulation Template
```json
{
  "sets": ["producers", "contracts"],
  "parameters": [
    "cost[producer, contract]",
    "capacity[producer]",
    "demand[contract]",
    "min_delivery[producer]",
    "min_contributors[contract]"
  ],
  "decision_variables": [
    "x[producer, contract] (continuous, >=0)",
    "y[producer, contract] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i,j] * x[i,j] for i in producers, j in contracts )"
  },
  "constraints": [
    "supply_capacity[i]: sum( x[i,j] for j in contracts ) <= capacity[i]",
    "demand_requirement[j]: sum( x[i,j] for i in producers ) >= demand[j]",
    "minimum_contributors[j]: sum( y[i,j] for i in producers ) >= min_contributors[j]",
    "participation_linking[i,j]: x[i,j] <= capacity[i] * y[i,j]",
    "minimum_delivery_threshold[i,j]: x[i,j] >= min_delivery[i] * y[i,j]"
  ]
}
```

### Common Pitfalls
- Using an insufficiently large big-M value in the linking constraint (e.g., using `demand` instead of `capacity`), which can incorrectly cut off feasible solutions.
- Forgetting to index the `min_delivery` parameter by producer in the minimum delivery constraint, leading to incorrect threshold application.
- Defining the objective function before all variables are declared, which can cause Pyomo construction errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver via the `pyomo.solvers` interface. Focus on robust solver configuration, explicit status checking, and systematic solution extraction and verification.

### Step 1 - Configure and Execute Solver
- Instantiate the solver factory: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set key options: `time_limit`, `mip_rel_gap` (must be >= 0), and optionally `threads` (avoid if scheduler conflicts occur).
- Execute with `tee=True` to monitor progress: `results = solver.solve(model, tee=True)`.

### Step 2 - Check Solver Status and Termination Condition
- Extract `status = results.solver.status` and `termination = results.solver.termination_condition`.
- Accept solutions where `status` is `SolverStatus.ok` and `termination` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- For any other status, produce a structured error payload and exit gracefully.

### Step 3 - Extract and Verify Solution
- If solve is successful, retrieve the objective value: `obj_val = float(pyo.value(model.obj))`.
- Iterate over the variable indices to extract non-zero allocations (`x[i,j].value`) and active participations (`y[i,j].value`).
- Optionally, implement a verification function that re-evaluates all constraints using the extracted values to ensure feasibility.

### Code Usage
```python
import pyomo.environ as pyo
import json
from pyomo.opt import SolverStatus, TerminationCondition

# Assume `model` is built according to the modeling stage steps.
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = -1.0  # Use default gap

results = solver.solve(model, tee=True)

status = results.solver.status
termination = results.solver.termination_condition

if status == SolverStatus.ok and termination in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    print(f"RESULT:{objective_value}")
    # Extract allocation details
    allocation = {}
    for i in model.producers:
        for j in model.contracts:
            if model.x[i,j].value > 1e-6:  # Tolerance for zero
                allocation[(i,j)] = model.x[i,j].value
    print(f"ALLOCATIONS:{json.dumps(allocation)}")
else:
    payload = {
        "status": "failed",
        "reason": "infeasible_or_error",
        "solver_status": str(status),
        "termination_condition": str(termination)
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of invalid solutions (e.g., from iteration limits).
- Setting `mip_rel_gap` to a negative value, which some solvers may reject; use `0.0` for optimality or a small positive tolerance.
- Attempting to access `.value` on variables before checking solve status, which can raise exceptions.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT solver, which is effective for MILPs with Boolean logic. It employs a more imperative, builder-style API where variables and constraints are added sequentially to a model object.

### Step 1 - Initialize Model and Create Variables
- Instantiate the CP-SAT model: `model = cp_model.CpModel()`.
- Create continuous allocation variables as `IntVar` (or `NumVar`) with bounds `[0, capacity[i]]` to implicitly enforce the upper linking bound.
- Create Boolean participation variables as `BoolVar` for each producer-contract pair.

### Step 2 - Enforce Conditional Logic with Linear Constraints
- **Linking Constraint**: Add `model.Add(x[i][j] <= capacity[i] * y[i][j])`. This uses the solver's linear constraint API.
- **Minimum Delivery Constraint**: Add `model.Add(x[i][j] >= min_delivery[i] * y[i][j])`. This is a linear constraint that becomes `x[i][j] >= 0` when `y[i][j]=0`.
- These constraints must be added inside nested loops over producers and contracts.

### Step 3 - Add Aggregate Constraints
- **Supply Capacity**: For each producer `i`, sum allocations across contracts must be <= `capacity[i]`. Use `model.Add(sum(x[i][j] for j in contracts) <= capacity[i])`.
- **Demand Requirement**: For each contract `j`, sum allocations from all producers must be >= `demand[j]`.
- **Minimum Contributors**: For each contract `j`, sum of Boolean participation variables must be >= `min_contributors[j]`. Use `model.Add(sum(y[i][j] for i in producers) >= K_j)`.

### Step 4 - Define the Objective
- Create a linear expression for total cost: `sum( cost[i][j] * x[i][j] for i,j in all_pairs )`.
- Set the objective to minimize this expression: `model.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": ["producers", "contracts"],
  "parameters": [
    "cost[producer, contract]",
    "capacity[producer]",
    "demand[contract]",
    "min_delivery[producer]",
    "min_contributors[contract]"
  ],
  "decision_variables": [
    "x[producer, contract] (integer or continuous, domain [0, capacity[producer]])",
    "y[producer, contract] (boolean)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i,j] * x[i,j] for i in producers, j in contracts )"
  },
  "constraints": [
    "supply_capacity[i]: sum( x[i,j] for j in contracts ) <= capacity[i]",
    "demand_requirement[j]: sum( x[i,j] for i in producers ) >= demand[j]",
    "minimum_contributors[j]: sum( y[i,j] for i in producers ) >= min_contributors[j]",
    "participation_linking[i,j]: x[i,j] <= capacity[i] * y[i,j]",
    "minimum_delivery_threshold[i,j]: x[i,j] >= min_delivery[i] * y[i,j]"
  ]
}
```

### Common Pitfalls
- Using `IntVar` for allocation when fractional quantities are allowed; use `NumVar` for continuous domains.
- Forgetting to set upper bounds on allocation variables when creating them, missing an opportunity to help the solver.
- Adding constraints in an order that causes variable references before they are defined.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured time and optional solution limits. Extract the solution status and values, providing clear feedback for both optimal/feasible and failed cases.

### Step 1 - Configure and Run Solver
- Create a solver instance: `solver = cp_model.CpSolver()`.
- Set parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 4`.
- Execute the solver on the model: `status = solver.Solve(model)`.

### Step 2 - Interpret Solver Status
- Check the returned `status` against `cp_model.OPTIMAL`, `cp_model.FEASIBLE`, and `cp_model.INFEASIBLE`.
- For `OPTIMAL` or `FEASIBLE`, proceed to solution extraction. For `INFEASIBLE` or `MODEL_INVALID`, output a structured error.

### Step 3 - Extract Solution Values and Verify
- If the status is acceptable, compute the objective value: `obj_val = solver.ObjectiveValue()`.
- Iterate over all variable indices. For allocation variables, use `solver.Value(x_var)`; for Boolean variables, use `solver.BooleanValue(y_var)`.
- Optionally, compute and print key metrics like total allocated quantity per contract and per producer utilization.

### Code Usage
```python
from ortools.sat.python import cp_model
import json

# Assume `model` is built according to the modeling stage steps.
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 4

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    objective_value = solver.ObjectiveValue()
    print(f"RESULT:{objective_value}")
    # Extract allocation details
    allocation = {}
    for i in producers:
        for j in contracts:
            x_val = solver.Value(x[i][j])
            if x_val > 1e-6:  # Tolerance for zero
                allocation[(i,j)] = x_val
    print(f"ALLOCATIONS:{json.dumps(allocation)}")
else:
    status_map = {cp_model.UNKNOWN: "UNKNOWN", cp_model.MODEL_INVALID: "MODEL_INVALID", cp_model.INFEASIBLE: "INFEASIBLE"}
    payload = {
        "status": "failed",
        "reason": status_map.get(status, "UNKNOWN"),
        "solver_status": status
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Confusing `cp_model.OPTIMAL` (proven optimal) with `cp_model.FEASIBLE` (satisfactory but not proven); both can be acceptable for this problem type.
- Not setting `num_search_workers` when parallel solving is desired, leaving potential performance gains unused.
- Accessing `solver.Value()` on a variable before checking the solve status, which may return undefined values.
