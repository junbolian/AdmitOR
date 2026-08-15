---
name: BipartiteAssignmentWithParticipationRequirements
description: |
  Model and solve bipartite assignment problems with minimum participation counts and conditional minimum flows using mixed-integer linear programming.
---

# Workflow 1 (Pyomo-based MILP)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling to separate problem specification from data, creating a clean, reusable model structure. It leverages the `pyomo.environ` API for constraint rule-based definition, suitable for integration with various solvers like HiGHS or CBC.

### Step 1 - Define Sets and Parameters
- Declare two primary sets: `PRODUCERS` and `CONTRACTS`.
- Define scalar parameters: `capacity[PRODUCERS]`, `demand[CONTRACTS]`, `min_producers[CONTRACTS]`, `min_delivery[PRODUCERS]`.
- Define a cost matrix parameter: `cost[PRODUCERS, CONTRACTS]`.

### Step 2 - Create Decision Variables
- Create a continuous variable `x[i, j]` for the assigned quantity from producer `i` to contract `j`.
- Create a binary variable `y[i, j]` indicating if producer `i` participates in contract `j`.

### Step 3 - Formulate Core Constraints
- **Capacity Limit**: Sum of assignments from each producer must not exceed its capacity.
- **Demand Satisfaction**: Sum of assignments to each contract must meet or exceed its demand.
- **Minimum Participation Count**: For each contract, the count of participating producers must meet a minimum.
- **Minimum Assignment if Selected**: If `y[i,j]=1`, then `x[i,j]` must be at least `min_delivery[i]`.
- **Logical Upper Bound**: `x[i,j]` must be zero if `y[i,j]=0`, bounded by `capacity[i] * y[i,j]`.

### Step 4 - Define Objective
- Formulate a linear objective to minimize total cost: sum of `cost[i,j] * x[i,j]` over all pairs.

### Formulation Template
```json
{
  "sets": ["PRODUCERS", "CONTRACTS"],
  "parameters": [
    "capacity[PRODUCERS]",
    "demand[CONTRACTS]",
    "min_producers[CONTRACTS]",
    "min_delivery[PRODUCERS]",
    "cost[PRODUCERS, CONTRACTS]"
  ],
  "decision_variables": [
    "x[PRODUCERS, CONTRACTS] (continuous, >=0)",
    "y[PRODUCERS, CONTRACTS] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in PRODUCERS for j in CONTRACTS)"
  },
  "constraints": [
    "capacity_limit[i]: sum(x[i,j] for j in CONTRACTS) <= capacity[i]",
    "demand_satisfaction[j]: sum(x[i,j] for i in PRODUCERS) >= demand[j]",
    "min_participation[j]: sum(y[i,j] for i in PRODUCERS) >= min_producers[j]",
    "min_assignment_if_selected[i,j]: x[i,j] >= min_delivery[i] * y[i,j]",
    "producer_contract_assignment[i,j]: x[i,j] <= capacity[i] * y[i,j]"
  ]
}
```

### Common Pitfalls
- Using an overly large big-M value in the logical upper bound constraint; use the natural bound `capacity[i]`.
- Forgetting to index `min_delivery` by producer, which can be producer-specific.
- Defining the cost parameter with incorrect dimensions, leading to indexing errors in the objective.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver (e.g., HiGHS, CBC). Focus on setting appropriate optimality gaps and time limits, followed by systematic solution validation to ensure all business rules are satisfied.

### Step 1 - Configure and Execute Solver
- Instantiate the solver factory (e.g., `SolverFactory('highs')`).
- Set key options: `time_limit=30`, `mip_rel_gap=0.0` (or a small positive tolerance).
- Solve the model and capture the results object.

### Step 2 - Check Solver Status and Termination
- Inspect `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `SolverStatus.ok` and termination is `optimal` or `feasible`.
- For other statuses, provide a clear error message and exit gracefully.

### Step 3 - Validate Solution Against Constraints
- Programmatically verify each constraint family using the solved variable values.
- Use a small tolerance (e.g., `1e-6`) for numerical comparisons.
- Check: producer capacity utilization, contract demand satisfaction, minimum participant counts, and minimum delivery for active assignments.

### Step 4 - Extract and Report Results
- Iterate over `x[i,j]` and `y[i,j]` to extract non-zero assignments.
- Summarize results by contract (total delivered, list of contributors) and by producer (total allocated).
- Report the objective value with appropriate rounding.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (abstract)
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective ...

# Solve
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)  # Set tee=True for debug output

# Check status
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Validation and extraction logic here
    print(f"RESULT:{pyo.value(model.objective)}")
else:
    print(f"RESULT_JSON:{{\"status\": \"failed\", \"reason\": \"{results.solver.termination_condition}\"}}")
```

### Common Pitfalls
- Setting `mip_rel_gap` to a negative value, which can cause solver errors; use `0.0`.
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal solutions.
- Failing to validate the solution numerically, which can miss subtle constraint violations due to solver tolerances.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, which is designed for integer and mixed-integer problems. It employs a more imperative, programmatic API for building the model, suitable for scenarios requiring fine-grained control over variable and constraint creation.

### Step 1 - Initialize Model and Data Structures
- Create a `CpModel()` object.
- Load data into dictionaries or lists: `capacity`, `demand`, `min_producers`, `min_delivery`, `cost`.

### Step 2 - Create Variables
- Create a continuous variable `x[i][j]` using `model.NewIntVar` or `model.NewNumVar` (bounded between 0 and `capacity[i]`).
- Create a binary variable `y[i][j]` using `model.NewBoolVar`.

### Step 3 - Add Constraints via Linear Expressions
- **Capacity Limit**: For each producer `i`, create a linear constraint summing `x[i][j]` over `j` ≤ `capacity[i]`.
- **Demand Satisfaction**: For each contract `j`, create a linear constraint summing `x[i][j]` over `i` ≥ `demand[j]`.
- **Minimum Participation Count**: For each contract `j`, sum `y[i][j]` over `i` ≥ `min_producers[j]`.
- **Conditional Minimum Flow**: For each pair `(i,j)`, add `x[i][j] >= min_delivery[i] * y[i][j]`.
- **Logical Linking**: For each pair `(i,j)`, add `x[i][j] <= capacity[i] * y[i][j]`.

### Step 4 - Define Objective
- Create a linear expression summing `cost[i][j] * x[i][j]` over all pairs.
- Set the model objective to minimize this expression.

### Formulation Template
```json
{
  "sets": ["PRODUCERS", "CONTRACTS"],
  "parameters": [
    "capacity[PRODUCERS]",
    "demand[CONTRACTS]",
    "min_producers[CONTRACTS]",
    "min_delivery[PRODUCERS]",
    "cost[PRODUCERS, CONTRACTS]"
  ],
  "decision_variables": [
    "x[PRODUCERS, CONTRACTS] (integer or continuous, domain [0, capacity[i]])",
    "y[PRODUCERS, CONTRACTS] (boolean)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in PRODUCERS for j in CONTRACTS)"
  },
  "constraints": [
    "sum(x[i][j] for j in CONTRACTS) <= capacity[i]",
    "sum(x[i][j] for i in PRODUCERS) >= demand[j]",
    "sum(y[i][j] for i in PRODUCERS) >= min_producers[j]",
    "x[i][j] >= min_delivery[i] * y[i][j]",
    "x[i][j] <= capacity[i] * y[i][j]"
  ]
}
```

### Common Pitfalls
- Using `model.NewIntVar` for `x` when fractional flows are allowed; use `model.NewNumVar` for continuous quantities.
- Incorrectly constructing the sum expressions using Python lists; use `model.AddLinearExpression` or build `LinearExpr.Sum`.
- Not naming variables and constraints, which makes debugging larger models difficult.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured time and optional solution callback. Emphasize status checking and post-solution verification to ensure the assignment meets all business logic, especially the conditional minimum flows.

### Step 1 - Configure Solver and Solve
- Create a `CpSolver()` instance.
- Set solver parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 4`.
- Optionally, set a deterministic seed: `solver.parameters.random_seed = 42`.

### Step 2 - Execute and Check Status
- Call `solver.Solve(model)` and capture the status.
- Check if status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNKNOWN` with appropriate error output.

### Step 3 - Validate and Extract Solution
- If solve is successful, iterate over all variable indices.
- For each `x[i][j]`, get its value via `solver.Value(x_var)`.
- Verify all constraints programmatically using these values and a tolerance.
- Collect active assignments where `x[i][j] > tolerance` and `y[i][j] == 1`.

### Step 4 - Report Structured Output
- Format results into a contract-centric summary and a producer-centric summary.
- Output the objective value and a clear status indicator (e.g., `RESULT:{cost}`).

### Code Usage
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... build model with variables and constraints ...

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
# solver.parameters.random_seed = 42  # For reproducibility

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Validation logic
    total_cost = 0
    assignments = []
    for i in PRODUCERS:
        for j in CONTRACTS:
            x_val = solver.Value(x[i][j])
            y_val = solver.Value(y[i][j])
            if x_val > 1e-6:
                assignments.append((i, j, x_val, y_val))
                total_cost += x_val * cost[i][j]
    # Perform constraint checks here
    print(f"RESULT:{total_cost}")
else:
    print(f"RESULT_JSON:{{\"status\": \"failed\", \"reason\": \"{status}\"}}")
```

### Common Pitfalls
- Not using a tolerance when checking `x_val > 0`, leading to missed assignments due to numerical precision.
- Forgetting to check both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid but non-optimal solutions.
- Setting `num_search_workers` higher than available CPU cores, which can degrade performance.
