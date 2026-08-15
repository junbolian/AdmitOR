---
name: Transit Network Design with Unmet Demand
description: |
  A skill for modeling and solving transit network design problems with line selection, frequency setting, transfer station designation, and unmet demand penalties using mixed-integer linear programming.
---

# Workflow 1 (Highs Solver with Pyomo)

## Modeling stage

### Strategy Overview
This workflow models the problem as a MILP using Pyomo, focusing on clear variable linking and constraint logic. It is designed for use with the open-source Highs solver, emphasizing exact solutions and robust status checking.

### Step 1 - Define Core Decision Variables
- Define binary variables for discrete infrastructure decisions (e.g., `y_l` for line selection, `t_s` for transfer station designation) using `pyo.Binary()`.
- Define continuous non-negative variables for operational decisions (e.g., `f_l` for line frequencies, `u_od` for unmet demand) using `pyo.NonNegativeReals()`.

### Step 2 - Link Binary and Continuous Variables
- Implement activation logic for frequencies: `f_l >= min_freq[l] * y_l` and `f_l <= max_freq[l] * y_l`. This ensures frequencies are zero if a line is not selected.
- Implement conditional activation for transfer stations: `sum_{l in L_s} y_l >= 2 * t_s`. This enforces that a station can only be a transfer if at least two selected lines serve it.

### Step 3 - Formulate Demand and Resource Constraints
- Formulate demand satisfaction with slack: `sum_{l in L_od} f_l + u_od >= demand_od` for each OD pair.
- Formulate resource capacity (e.g., vehicles) as a linear combination: `sum_{l} (vehicle_usage_l * f_l) <= total_vehicles`. Verify parameter units (per line vs. per frequency) to ensure feasibility.

### Step 4 - Construct the Objective Function
- Formulate the total cost as a minimization of fixed costs (line selection), operational costs (frequency-dependent), and penalty costs (unmet demand). Use `pyo.Objective(rule=obj_rule, sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "L: set of candidate lines",
    "OD: set of origin-destination pairs",
    "S: set of stations"
  ],
  "parameters": [
    "fixed_cost_l: fixed cost for selecting line l",
    "operational_cost_l: cost per unit frequency on line l",
    "penalty_od: penalty per unit of unmet demand for OD pair od",
    "demand_od: travel demand for OD pair od",
    "A_od_l: 1 if line l serves OD pair od, else 0",
    "B_s_l: 1 if line l passes through station s, else 0",
    "min_freq_l, max_freq_l: minimum and maximum frequency for line l",
    "vehicle_usage_l: vehicle units consumed per unit frequency on line l",
    "total_vehicles: total available vehicle units"
  ],
  "decision_variables": [
    "y_l: binary, 1 if line l is selected",
    "f_l: continuous, frequency of line l",
    "u_od: continuous, unmet demand for OD pair od",
    "t_s: binary, 1 if station s is designated a transfer"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{l in L} fixed_cost_l * y_l + sum_{l in L} operational_cost_l * f_l + sum_{od in OD} penalty_od * u_od"
  },
  "constraints": [
    "frequency_linking_lower: f_l >= min_freq_l * y_l, for all l in L",
    "frequency_linking_upper: f_l <= max_freq_l * y_l, for all l in L",
    "transfer_activation_s: sum_{l in L} B_s_l * y_l >= 2 * t_s, for all s in S",
    "demand_satisfaction_od: sum_{l in L} A_od_l * f_l + u_od >= demand_od, for all od in OD",
    "vehicle_capacity: sum_{l in L} vehicle_usage_l * f_l <= total_vehicles"
  ]
}
```

### Common Pitfalls
- Interpreting resource capacity parameters (e.g., `vehicle_usage_l`) incorrectly (per line vs. per frequency), leading to infeasible or degenerate solutions.
- Implementing transfer station constraints without an objective coefficient, adding unnecessary complexity without affecting the solution.
- Failing to verify that the minimum resource requirement (one line at minimum frequency) is compatible with the total capacity constraint.

## Solving stage

### Strategy Overview
This solving stage uses Pyomo's `SolverFactory` interface with the Highs solver, configured for exact MILP solutions. It emphasizes rigorous solution validation and systematic diagnosis of infeasibility.

### Step 1 - Configure and Run the Solver
- Instantiate the solver: `solver = pyo.SolverFactory('highs')`.
- Set solver options for a time limit and optimality gap: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0`.
- Solve the model: `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Solution Status
- Check the solver status and termination condition using `pyo.check_optimal_termination(results)` or explicit checks against `SolverStatus.ok` and `TerminationCondition.optimal`/`feasible`.
- Proceed to extract results only if the solve was successful.

### Step 3 - Extract and Analyze Results
- Extract variable values using `pyo.value(var)`.
- For binary variables, apply a tolerance (e.g., `> 0.5`) to determine selections.
- Compute derived metrics (e.g., total vehicle usage, total unmet demand) by summing parameter-weighted variable values.
- If the solution is degenerate (e.g., no lines selected), perform a feasibility check: calculate if `min_freq_l * vehicle_usage_l <= total_vehicles` for any line `l`.

### Step 4 - Perform Diagnostic Sensitivity Analysis
- If the model is infeasible or yields a trivial solution, systematically relax the most binding constraint (e.g., increase `total_vehicles`) to understand the problem structure.
- Avoid arbitrary parameter scaling; instead, analyze the mathematical feasibility of constraints.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (model definition code not shown for brevity)
# ...

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)

# Validate solution
if pyo.check_optimal_termination(results):
    # Extract results
    selected_lines = [l for l in model.L if pyo.value(model.y[l]) > 0.5]
    total_cost = pyo.value(model.obj)
    # ... further analysis
else:
    print("Solve failed. Status:", results.solver.status)
    # Perform infeasibility diagnosis
```

### Common Pitfalls
- Accepting degenerate optimal solutions (e.g., all demand unmet) without questioning model validity or data consistency.
- Using iterative trial-and-error with arbitrary scaling factors instead of systematic constraint analysis.
- Omitting status and termination checks, leading to errors when extracting results from failed solves.

# Workflow 2 (CBC Solver with Pyomo)

## Modeling stage

### Strategy Overview
This workflow also models the problem as a MILP using Pyomo but is tailored for the CBC solver. It emphasizes efficient constraint generation for larger instances and includes explicit handling of special cases.

### Step 1 - Structure Sets and Parameters
- Organize all problem data into dictionaries with consistent indexing (lines, OD pairs, stations).
- Use nested dictionaries for coverage matrices (e.g., `A[od][l]`, `B[s][l]`) to enable efficient constraint generation in Pyomo rules.

### Step 2 - Implement Activation and Linking Constraints
- Model line-frequency linking with big-M constraints as in Workflow 1.
- For transfer stations, implement the activation logic: `sum(B_s_l[s][l] * y[l] for l in L) >= 2 * t[s]`.
- For stations that cannot be transfer stations, add an explicit equality constraint `t[s] == 0` instead of modifying the general rule.

### Step 3 - Incorporate Unmet Demand as Slack
- For each OD pair, add a continuous unmet demand variable `u[od] >= 0`.
- Formulate the demand constraint: `sum(A[od][l] * f[l] for l in L) + u[od] >= demand[od]`.

### Step 4 - Formulate Objective with All Cost Components
- Assemble the objective function as the sum of fixed, operational, and penalty costs, ensuring all coefficients are correctly mapped to their respective variables.

### Formulation Template
```json
{
  "sets": [
    "L: set of candidate lines",
    "OD: set of origin-destination pairs",
    "S: set of stations"
  ],
  "parameters": [
    "fixed_cost_l: fixed cost for selecting line l",
    "operational_cost_l: cost per unit frequency on line l",
    "penalty_od: penalty per unit of unmet demand for OD pair od",
    "demand_od: travel demand for OD pair od",
    "A_od_l: 1 if line l serves OD pair od, else 0",
    "B_s_l: 1 if line l passes through station s, else 0",
    "min_freq_l, max_freq_l: bounds on frequency for line l",
    "resource_consumption_l: units of limited resource (e.g., vehicles) consumed per unit frequency on line l",
    "total_resource: total available resource units"
  ],
  "decision_variables": [
    "y_l: binary, selection of line l",
    "f_l: continuous, frequency on line l",
    "u_od: continuous, unmet demand for OD pair od",
    "t_s: binary, transfer designation for station s"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{l in L} fixed_cost_l * y_l + sum_{l in L} operational_cost_l * f_l + sum_{od in OD} penalty_od * u_od"
  },
  "constraints": [
    "frequency_active_l: f_l >= min_freq_l * y_l, for all l in L",
    "frequency_limit_l: f_l <= max_freq_l * y_l, for all l in L",
    "transfer_if_two_lines_s: sum_{l in L} B_s_l * y_l >= 2 * t_s, for all s in S",
    "special_station_s: t_s == 0, for specific s in S (if applicable)",
    "demand_with_slack_od: sum_{l in L} A_od_l * f_l + u_od >= demand_od, for all od in OD",
    "resource_capacity: sum_{l in L} resource_consumption_l * f_l <= total_resource"
  ]
}
```

### Common Pitfalls
- Treating all constraints as equally binding without identifying the dominant constraint that controls feasibility.
- Adding transfer station constraints that have no impact on the objective, unnecessarily increasing model size.
- Failing to verify parameter units for resource consumption, leading to infeasible models.

## Solving stage

### Strategy Overview
This solving stage uses the CBC solver via Pyomo, configured for performance on MILP problems. It includes steps for solution verification, corner-case analysis, and iterative refinement.

### Step 1 - Configure CBC Solver Options
- Instantiate the solver: `solver = pyo.SolverFactory('cbc')`.
- Set performance options: `solver.options['seconds'] = 60` for time limit, `solver.options['ratio'] = 0.01` for optimality gap, `solver.options['threads'] = 4` for parallel processing if supported.

### Step 2 - Solve and Check Termination
- Execute the solve: `results = solver.solve(model, tee=True)` (using `tee=True` for logging if needed).
- Validate success by checking `results.solver.status` and `results.solver.termination_condition`.

### Step 3 - Analyze Solution and Corner Cases
- Extract variable values and compute key performance indicators (selected lines, total cost, resource usage).
- If the solution is trivial (e.g., no lines selected), calculate the minimal resource requirement: check if `min_freq_l * resource_consumption_l <= total_resource` for any line `l` to test constraint feasibility.

### Step 4 - Iterative Refinement and Sensitivity
- If the initial model yields unrealistic results, systematically test alternative interpretations of ambiguous constraints while keeping others fixed.
- Perform sensitivity analysis by relaxing the binding constraint (e.g., increasing `total_resource`) to observe trade-offs and validate model behavior.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (model definition code not shown for brevity)
# ...

# Solve with CBC
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 60
solver.options['ratio'] = 0.01
# Avoid setting 'threads' if a global scheduler is already initialized
results = solver.solve(model, tee=False)

# Verify solution feasibility and optimality
from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    # Extract and validate solution components
    for l in model.L:
        if pyo.value(model.y[l]) > 0.5:
            print(f"Line {l} selected with frequency {pyo.value(model.f[l])}")
    # ... further analysis
else:
    print(f"Solver did not find an optimal solution. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Running multiple solver trials with arbitrary parameter scaling instead of a single, systematic parameter analysis.
- Accepting optimal solutions that are mathematically correct but practically meaningless (e.g., all demand unmet) without diagnosing the root cause.
- Omitting validation of solver status, leading to runtime errors when accessing solution values.
