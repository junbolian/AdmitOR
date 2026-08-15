---
name: MILP Design with Conditional Activation and Slack Variables
description: |
  Model and solve mixed-integer linear programs with conditional activation of continuous variables, logical constraints, and demand slack with penalties using systematic constraint testing and solver configuration.

---

# Workflow 1 (Hierarchical Constraint Testing with PuLP/CBC)

## Modeling stage

### Strategy Overview
Build the model incrementally, starting with core demand and resource constraints, then adding conditional logic. This isolates infeasibility sources and validates constraint interpretations before finalizing the full formulation.

### Step 1 - Define Core Variables and Demand Slack
- Declare binary line selection variables and continuous frequency variables.
- Introduce continuous unmet demand variables for each demand pair with a high penalty coefficient in the objective.
- Link demand satisfaction: sum of frequencies on serving lines plus unmet demand must meet each demand requirement.

### Step 2 - Implement Conditional Activation with Bounds
- For each line, enforce that frequency is zero if the line is not selected using big-M style constraints: `freq_min * y_l <= f_l <= freq_max * y_l`.
- Ensure the lower bound forces activation if frequency is positive.

### Step 3 - Add Resource Capacity Constraint
- Formulate a linear resource constraint: sum over lines of (resource usage rate per frequency unit * frequency variable) <= total resource limit.
- Validate coefficient scaling by pre-calculating minimum resource consumption across all lines.

### Step 4 - Incorporate Logical Conditions
- For transfer station activation, require at least N selected lines through the station: `sum(y_l for l in station_lines) >= N * t_s`, where `t_s` is binary.
- For prohibited stations, explicitly fix the activation variable to zero.

### Formulation Template
```json
{
  "sets": [
    "L: set of lines",
    "OD: set of origin-destination pairs",
    "S: set of stations"
  ],
  "parameters": [
    "demand_od: demand for OD pair od",
    "freq_min_l, freq_max_l: min/max frequency for line l",
    "usage_l: resource units per frequency unit for line l",
    "total_resource: total available resource units",
    "penalty_od: cost per unit of unmet demand for od",
    "fixed_cost_l: fixed cost for selecting line l",
    "op_cost_l: operational cost per frequency unit for line l",
    "station_lines[s]: list of lines passing through station s",
    "N_min: minimum lines required to activate a transfer station"
  ],
  "decision_variables": [
    "y_l ∈ {0,1}: 1 if line l is selected",
    "f_l ≥ 0: frequency of line l",
    "u_od ≥ 0: unmet demand for OD pair od",
    "t_s ∈ {0,1}: 1 if transfer station s is activated"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost_l * y_l) + sum(op_cost_l * f_l) + sum(penalty_od * u_od)"
  },
  "constraints": [
    "demand_satisfaction_od: sum(f_l for l in lines_serving_od[od]) + u_od >= demand_od, for all od",
    "frequency_lower_l: f_l >= freq_min_l * y_l, for all l",
    "frequency_upper_l: f_l <= freq_max_l * y_l, for all l",
    "resource_capacity: sum(usage_l * f_l) <= total_resource",
    "transfer_activation_s: sum(y_l for l in station_lines[s]) >= N_min * t_s, for all s",
    "prohibited_station_s: t_s == 0, for s in prohibited_stations"
  ]
}
```

### Common Pitfalls
- Using fractional constraints (e.g., `t_s <= sum(y_l)/2.0`) which can produce incorrect integer-feasible solutions.
- Misinterpreting resource usage coefficients (e.g., vehicle units per frequency vs per selected line), leading to infeasibility.
- Not pre-calculating minimum resource needs, which can mask fundamental infeasibility.

## Solving stage

### Strategy Overview
Solve using PuLP with CBC backend, configuring for optimality and runtime. Implement robust solution loading and systematic validation of results against all constraints.

### Step 1 - Configure Solver and Solve
- Instantiate the model with `pulp.LpProblem` and set the solver to `pulp.PULP_CBC_CMD`.
- Set solver parameters: `timeLimit=30`, `gapRel=0.0` (for optimality), and `threads=4`.
- Call `problem.solve()` and capture the status.

### Step 2 - Validate Solution and Load Values
- Check termination condition: `pulp.LpStatus[problem.status]` should be `'Optimal'`.
- Use `load_solutions=False` option if available, then explicitly load variable values.
- For infeasible results, test a simple feasible baseline (e.g., single line at min frequency).

### Step 3 - Analyze and Report Key Metrics
- Compute total served demand, total unmet demand penalty, resource utilization, and fixed/operational costs.
- Print selected lines, their frequencies, and activated transfer stations.
- Verify all constraints explicitly with the loaded solution.

### Code Usage
```python
import pulp

# Build model from formulation
problem = pulp.LpProblem('Network_Design', pulp.LpMinimize)
# ... (add variables and constraints based on template)

# Solve with status / termination checks
solver = pulp.PULP_CBC_CMD(timeLimit=30, gapRel=0.0, threads=4)
problem.solve(solver)

# Check status and load solution
status = pulp.LpStatus[problem.status]
if status == 'Optimal':
    # Extract variable values
    selected_lines = [l for l in L if pulp.value(y[l]) > 0.5]
    # ... further analysis
else:
    print(f"Solver status: {status}")
    # Implement fallback analysis
```

### Common Pitfalls
- Setting `gapRel=-1.0` (default) instead of `0.0` for optimality, leading to premature termination.
- Not checking solver status before accessing variable values, causing runtime errors.
- Overlooking that an "all unmet demand" solution may be optimal under extreme resource constraints.

# Workflow 2 (Direct MIP with OR-Tools/SCIP)

## Modeling stage

### Strategy Overview
Formulate the complete MILP directly using a solver-native API (OR-Tools). Emphasize efficient data structures for mapping relationships and precise constraint scaling.

### Step 1 - Map Relationships and Declare Variables
- Precompute dictionaries: `lines_serving_od[od]` and `station_lines[s]`.
- Create solver, then define binary and continuous variables with appropriate bounds.

### Step 2 - Formulate Objective with Penalties
- Build objective expression as sum of: fixed costs * y_l, operational costs * f_l, and penalty costs * u_od.
- Set the minimization sense on the solver.

### Step 3 - Add All Constraints in One Pass
- Add demand satisfaction constraints using the precomputed mappings.
- Add conditional frequency bounds linking f_l and y_l.
- Add linear resource capacity constraint.
- Add transfer station activation logic with the `>= N * t_s` formulation.

### Formulation Template
```json
{
  "sets": [
    "L: set of lines",
    "OD: set of origin-destination pairs",
    "S: set of stations"
  ],
  "parameters": [
    "demand_od: demand for OD pair od",
    "freq_min_l, freq_max_l: min/max frequency for line l",
    "usage_l: resource units per frequency unit for line l",
    "total_resource: total available resource units",
    "penalty_od: cost per unit of unmet demand for od",
    "fixed_cost_l: fixed cost for selecting line l",
    "op_cost_l: operational cost per frequency unit for line l",
    "station_lines[s]: list of lines passing through station s",
    "N_min: minimum lines required to activate a transfer station"
  ],
  "decision_variables": [
    "y_l ∈ {0,1}: 1 if line l is selected",
    "f_l ∈ [freq_min_l * y_l, freq_max_l * y_l]: frequency of line l",
    "u_od ≥ 0: unmet demand for OD pair od",
    "t_s ∈ {0,1}: 1 if transfer station s is activated"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost_l * y_l) + sum(op_cost_l * f_l) + sum(penalty_od * u_od)"
  },
  "constraints": [
    "demand_satisfaction_od: sum(f_l for l in lines_serving_od[od]) + u_od >= demand_od, for all od",
    "frequency_activation_l: f_l >= freq_min_l * y_l and f_l <= freq_max_l * y_l, for all l",
    "resource_capacity: sum(usage_l * f_l) <= total_resource",
    "transfer_activation_s: sum(y_l for l in station_lines[s]) >= N_min * t_s, for all s",
    "prohibited_station_s: t_s == 0, for s in prohibited_stations"
  ]
}
```

### Common Pitfalls
- Incorrectly scaling the resource usage coefficient (e.g., using per-line fixed usage instead of per-frequency), causing infeasibility.
- Using `t_s <= sum(y_l)/2` which allows fractional satisfaction and violates integer logic.
- Not verifying that `lines_serving_od` mapping correctly reflects service relationships.

## Solving stage

### Strategy Overview
Utilize OR-Tools' MIP solver with SCIP backend for direct control. Set performance parameters, solve, and perform post-solution validation to ensure feasibility and interpret results.

### Step 1 - Initialize Solver and Set Parameters
- Create solver: `pywraplp.Solver.CreateSolver('SCIP')`.
- Set time limit: `solver.SetTimeLimit(30000)` (in milliseconds).
- Set number of threads: `solver.SetNumThreads(4)`.

### Step 2 - Solve and Check Status
- Call `solver.Solve()` and capture the result status.
- Check if status is `OPTIMAL` or `FEASIBLE`. For `INFEASIBLE`, analyze constraint tightness.

### Step 3 - Extract and Validate Solution
- Extract variable values using `.solution_value()`.
- Recompute key metrics: served demand, resource usage, and objective components.
- Perform sensitivity analysis by relaxing the most binding constraint to confirm optimality.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (create variables and constraints based on template)

# Solve with status / termination checks
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)
status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL:
    # Extract solution
    selected_lines = [l for l in L if y[l].solution_value() > 0.5]
    # ... further analysis
else:
    print(f"Solver status: {status}")
    # Analyze infeasibility by checking minimum resource requirements
```

### Common Pitfalls
- Not setting a time limit, leading to excessively long runs on large instances.
- Misinterpreting solver status codes (e.g., `FEASIBLE` vs `OPTIMAL`).
- Failing to scale large coefficients, which can cause numerical instability.
