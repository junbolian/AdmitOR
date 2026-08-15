---
name: Allocation with Participation Requirements
description: |
  Model and solve allocation problems with minimum delivery thresholds and minimum contributor requirements using MILP formulations with continuous allocation and binary participation variables.

---

# Workflow 1 (Pyomo-HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for model definition and the HiGHS solver for optimization, providing a flexible, open-source environment suitable for complex MILP problems with clear constraint grouping.

### Step 1 - Define Sets and Parameters
- Define sets for `PRODUCERS` and `CONTRACTS` as lists or index sets.
- Create parameter dictionaries: `capacity[p]`, `demand[c]`, `min_delivery[p]`, `cost[p,c]`, and `min_contributors` (a scalar or per-contract value).

### Step 2 - Create Decision Variables
- Define continuous variable `x[p,c]` for allocation quantity from producer `p` to contract `c`.
- Define binary variable `y[p,c]` to indicate participation (1 if `p` supplies `c`, else 0).

### Step 3 - Formulate Constraints
- **Supply Capacity**: `sum(x[p,c] for c in CONTRACTS) <= capacity[p]` for each `p`.
- **Demand Requirement**: `sum(x[p,c] for p in PRODUCERS) >= demand[c]` for each `c`.
- **Minimum Contributors**: `sum(y[p,c] for p in PRODUCERS) >= min_contributors` for each `c`.
- **Minimum Delivery Threshold**: `x[p,c] >= min_delivery[p] * y[p,c]` for each `(p,c)` pair.
- **Participation Logic**: `x[p,c] <= capacity[p] * y[p,c]` for each `(p,c)` pair (Big-M linking).

### Step 4 - Define Objective
- Set objective to minimize total cost: `minimize sum(cost[p,c] * x[p,c] for p in PRODUCERS for c in CONTRACTS)`.

### Formulation Template
```json
{
  "sets": ["PRODUCERS", "CONTRACTS"],
  "parameters": [
    "capacity[PRODUCERS]",
    "demand[CONTRACTS]",
    "min_delivery[PRODUCERS]",
    "cost[PRODUCERS, CONTRACTS]",
    "min_contributors"
  ],
  "decision_variables": [
    "x[PRODUCERS, CONTRACTS] (continuous, non-negative)",
    "y[PRODUCERS, CONTRACTS] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[p,c] * x[p,c] for p in PRODUCERS for c in CONTRACTS)"
  },
  "constraints": [
    "supply_capacity: sum(x[p,c] for c in CONTRACTS) <= capacity[p] for each p",
    "demand_requirement: sum(x[p,c] for p in PRODUCERS) >= demand[c] for each c",
    "minimum_contributors: sum(y[p,c] for p in PRODUCERS) >= min_contributors for each c",
    "minimum_delivery_threshold: x[p,c] >= min_delivery[p] * y[p,c] for each (p,c)",
    "participation_logic: x[p,c] <= capacity[p] * y[p,c] for each (p,c)"
  ]
}
```

### Common Pitfalls
- Using an invalid Big-M value (e.g., too small) in the participation logic constraint; `capacity[p]` is a natural, tight bound.
- Forgetting to enforce non-negativity on the continuous allocation variable `x`.
- Setting `min_contributors` as a per-producer parameter instead of a per-contract requirement.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver with configured time limits and optimality gap, followed by rigorous solution status checking and feasibility verification.

### Step 1 - Configure Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")`.
- Set key options: `time_limit`, `mip_rel_gap` (e.g., 0.0 for optimality), and `threads` for parallel processing.

### Step 2 - Solve and Check Status
- Execute `results = solver.solve(model, tee=True)`.
- Check both `results.solver.status` (`SolverStatus.ok`) and `results.solver.termination_condition` (`optimal` or `feasible`).

### Step 3 - Extract and Validate Solution
- If status is good, extract variable values using `pyo.value(x[p,c])` and `pyo.value(y[p,c])`.
- Compute derived metrics: total cost, producer utilization, per-contract allocation sums.
- Programmatically verify all constraints with a small tolerance (e.g., 1e-6) to ensure numerical feasibility.

### Step 4 - Handle Failures
- If status is not optimal/feasible, output a structured JSON result indicating infeasibility or error, including the termination condition for diagnostics.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model building code as per Modeling stage)

# Configure solver
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4

# Solve
results = solver.solve(model, tee=False)

# Check status
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    # Extract solution values and verify constraints
    for p in model.PRODUCERS:
        for c in model.CONTRACTS:
            x_val = pyo.value(model.x[p, c])
            y_val = pyo.value(model.y[p, c])
            # ... process values
    print(f"Total cost: {objective_value}")
else:
    # Handle failure
    print(f"RESULT_JSON: {{\"status\": \"{status}\", \"termination\": \"{term}\"}}")
```

### Common Pitfalls
- Setting `mip_rel_gap` to a negative value; use `0.0` to seek optimality.
- Not checking both solver status and termination condition, leading to misinterpretation of suboptimal solutions.
- Extracting variable values without confirming the solution is feasible, which may raise errors.

---

# Workflow 2 (OR-Tools / SCIP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools with the SCIP solver backend, offering a direct API for MILP construction with explicit variable and constraint creation, ideal for prototyping and deployment in production environments.

### Step 1 - Initialize Solver and Data Structures
- Create solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Define data as dictionaries: `capacity`, `demand`, `min_delivery`, `cost_matrix`, and scalar `min_contributors`.

### Step 2 - Create Variables with Naming
- Create continuous variable `x[i,j] = solver.NumVar(0, capacity[i], f"x_{i}_{j}")`.
- Create binary variable `y[i,j] = solver.BoolVar(f"y_{i}_{j}")`.

### Step 3 - Add Constraints Directly
- **Supply Capacity**: `solver.Add(sum(x[i,j] for j in contracts) <= capacity[i])`.
- **Demand Requirement**: `solver.Add(sum(x[i,j] for i in producers) >= demand[j])`.
- **Minimum Contributors**: `solver.Add(sum(y[i,j] for i in producers) >= min_contributors)`.
- **Minimum Delivery Threshold**: `solver.Add(x[i,j] >= min_delivery[i] * y[i,j])`.
- **Participation Logic**: `solver.Add(x[i,j] <= capacity[i] * y[i,j])`.

### Step 4 - Set Linear Objective
- Build objective expression: `sum(cost_matrix[i][j] * x[i,j] for i in producers for j in contracts)`.
- Set minimization: `solver.Minimize(obj_expr)`.

### Formulation Template
```json
{
  "sets": ["producers", "contracts"],
  "parameters": [
    "capacity[producers]",
    "demand[contracts]",
    "min_delivery[producers]",
    "cost_matrix[producers][contracts]",
    "min_contributors"
  ],
  "decision_variables": [
    "x[producers, contracts] (continuous, [0, capacity[i]])",
    "y[producers, contracts] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_matrix[i][j] * x[i,j] for i in producers for j in contracts)"
  },
  "constraints": [
    "supply_capacity: sum(x[i,j] for j in contracts) <= capacity[i] for each i",
    "demand_requirement: sum(x[i,j] for i in producers) >= demand[j] for each j",
    "minimum_contributors: sum(y[i,j] for i in producers) >= min_contributors for each j",
    "minimum_delivery_threshold: x[i,j] >= min_delivery[i] * y[i,j] for each (i,j)",
    "participation_logic: x[i,j] <= capacity[i] * y[i,j] for each (i,j)"
  ]
}
```

### Common Pitfalls
- Using an arbitrary large number for Big-M in participation logic; `capacity[i]` is the correct, tight bound.
- Forgetting to set upper bounds on continuous variables, which can lead to unbounded problem errors.
- Mismatching indices when building nested loops for constraints, causing incorrect constraint definitions.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' wrapper for SCIP (or CBC), with configured time limits and parallel threads, followed by explicit status checking and detailed solution reporting.

### Step 1 - Configure Solver Parameters
- Set time limit: `solver.SetTimeLimit(30000)` for 30 seconds.
- Enable parallel processing: `solver.SetNumThreads(4)`.
- (Optional) Set other parameters like relative gap tolerance if using CBC.

### Step 2 - Invoke Solver and Interpret Status
- Execute `status = solver.Solve()`.
- Check status explicitly: compare against `pywraplp.Solver.OPTIMAL`, `FEASIBLE`, etc.

### Step 3 - Extract and Report Solution
- If optimal or feasible, iterate over variables to get `.solution_value()`.
- Print allocation matrix, participation matrix, and total cost.
- Compute and display producer utilization percentages and per-contract allocation sums.

### Step 4 - Verify Solution Feasibility
- Programmatically re-check all constraints using the extracted solution values and a small tolerance (e.g., 1e-6).
- Output verification results to confirm the solution satisfies all problem requirements.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# ... (model building code as per Modeling stage)

# Configure solver
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# Solve
status = solver.Solve()

# Check status and extract solution
if status == pywraplp.Solver.OPTIMAL:
    print("Status: OPTIMAL")
elif status == pywraplp.Solver.FEASIBLE:
    print("Status: FEASIBLE (but not proven optimal)")
else:
    print(f"Solver did not find a feasible solution. Status: {status}")
    # Handle failure, potentially returning JSON output
    exit()

# Extract and report
total_cost = solver.Objective().Value()
print(f"Total cost: {total_cost}")
for i in producers:
    for j in contracts:
        x_val = x[i, j].solution_value()
        y_val = y[i, j].solution_value()
        if x_val > 1e-6:  # Only print significant allocations
            print(f"Producer {i} -> Contract {j}: {x_val} (participating: {y_val})")

# Optional: Verify constraints
tolerance = 1e-6
# ... verification code loops through constraints
```

### Common Pitfalls
- Assuming `FEASIBLE` status means optimal; always check for `OPTIMAL` if proof of optimality is required.
- Not handling the case where `solver.Solve()` returns `INFEASIBLE` or `UNBOUNDED`, leading to crashes when accessing solution values.
- Using loose tolerances for verification that might mask constraint violations.
