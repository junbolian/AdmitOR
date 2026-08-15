---
name: BalancedAssignmentLP
description: |
  Model and solve balanced assignment/transportation problems with supply-demand equality constraints, per-assignment capacity limits, and linear cost minimization using continuous variables.
---

# Workflow 1 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Model the problem as a balanced transportation Linear Program (LP) using Pyomo's `ConcreteModel`. This approach is well-suited for problems where fractional assignments are acceptable and leverages the efficiency of open-source solvers like HiGHS.

### Step 1 - Define Sets and Parameters
- Declare sets for supply nodes (e.g., `model.I`) and demand nodes (e.g., `model.J`).
- Define parameters for supply capacities (`supply[i]`), demand requirements (`demand[j]`), per-unit costs (`cost[i,j]`), and individual assignment upper bounds (`capacity[i,j]`). Use dictionaries for efficient indexing.

### Step 2 - Create Decision Variables
- Create a single indexed variable `model.x[i,j]` representing the continuous assignment quantity from supply `i` to demand `j`.
- Set the variable domain to `pyo.NonNegativeReals` and optionally apply the `capacity[i,j]` as an upper bound during variable creation.

### Step 3 - Formulate Supply and Demand Constraints
- Add a constraint for each supply node `i`: `sum(model.x[i,j] for j in model.J) == supply[i]`.
- Add a constraint for each demand node `j`: `sum(model.x[i,j] for i in model.I) == demand[j]`.
- Ensure total supply equals total demand before model instantiation for a balanced problem.

### Step 4 - Define Linear Objective
- Define the objective to minimize total cost: `model.obj = pyo.Objective(expr=sum(cost[i,j] * model.x[i,j] for i in model.I for j in model.J), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["I (supply nodes)", "J (demand nodes)"],
  "parameters": [
    "supply[i] for i in I",
    "demand[j] for j in J",
    "cost[i,j] for i in I, j in J",
    "capacity[i,j] for i in I, j in J"
  ],
  "decision_variables": ["x[i,j] (continuous assignment from i to j)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "supply_balance[i]: sum(x[i,j] for j in J) == supply[i] for each i in I",
    "demand_balance[j]: sum(x[i,j] for i in I) == demand[j] for each j in J",
    "capacity_limit[i,j]: x[i,j] <= capacity[i,j] for each i in I, j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand, which is required for the standard balanced transportation formulation.
- Using inefficient nested loops for constraint and objective construction on large datasets; prefer list comprehensions or efficient `sum` operations.
- Not applying individual capacity limits, leading to unrealistic assignments that exceed practical per-pair limits.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via `SolverFactory`. Configure solver options for performance and reliability, implement robust solution status checks, and extract results with validation.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory('highs')`.
- Set solver options for a time limit and optimality gap: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0` (for LP, this ensures optimality).
- Execute the solve: `results = solver.solve(model, tee=False)`.

### Step 2 - Check Solution Status and Termination
- Verify the solver status: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `assert results.solver.termination_condition == pyo.TerminationCondition.optimal`. Accept `pyo.TerminationCondition.feasible` if optimality is not guaranteed.

### Step 3 - Extract and Validate Results
- Extract the objective value: `obj_val = pyo.value(model.obj)`.
- Iterate over `model.x` to retrieve assignment values, filtering near-zero values (e.g., `if pyo.value(model.x[i,j]) > 1e-6`).
- Programmatically verify constraints by recalculating sums from solution values and comparing them to original supply/demand parameters.

### Code Usage
```python
import pyomo.environ as pyo

# Assume model is built as per Modeling stage
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

# Status checks
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    print(f"Objective: {pyo.value(model.obj):.2f}")
    # Extract and print assignments
    for i in model.I:
        for j in model.J:
            val = pyo.value(model.x[i,j])
            if val > 1e-6:
                print(f"  x[{i},{j}] = {val:.2f}")
    # Add constraint verification logic here
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Failing to check both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or infeasible results.
- Not using an epsilon threshold when filtering near-zero assignment values, resulting in cluttered output from floating-point imprecision.
- Omitting post-solve constraint verification, which is crucial for validating the solution against the original problem data.

# Workflow 2 (OR-Tools with GLOP/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Google's OR-Tools, creating variables and constraints via its direct coefficient-setting API. This workflow provides fine-grained control and is efficient for large-scale LPs (using GLOP) or Mixed-Integer Programs (using CBC).

### Step 1 - Initialize Solver and Data Structures
- Choose solver backend: `solver = pywraplp.Solver.CreateSolver('GLOP')` for continuous LP; use `'CBC'` if integer variables are required.
- Organize problem data (supply, demand, cost, capacity) in lists or dictionaries with consistent indexing.

### Step 2 - Create Assignment Variables Systematically
- Loop over all supply-demand pairs `(i, j)`.
- For each pair, create a variable: `x[i][j] = solver.NumVar(0, capacity[i][j], f'x_{i}_{j}')` for continuous assignments. Use `solver.IntVar` for integer requirements.

### Step 3 - Add Supply and Demand Constraints via Coefficients
- For each supply node `i`, create a constraint: `constraint = solver.Constraint(supply[i], supply[i])`. Then, for all `j`, set coefficient: `constraint.SetCoefficient(x[i][j], 1)`.
- For each demand node `j`, create a constraint: `constraint = solver.Constraint(demand[j], demand[j])`. Then, for all `i`, set coefficient: `constraint.SetCoefficient(x[i][j], 1)`.

### Step 4 - Set Linear Objective
- Initialize the objective: `objective = solver.Objective()`.
- Loop over all variables `x[i][j]` and set their coefficients: `objective.SetCoefficient(x[i][j], cost[i][j])`.
- Set the objective sense to minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["I (supply nodes)", "J (demand nodes)"],
  "parameters": [
    "supply[i] for i in I",
    "demand[j] for j in J",
    "cost[i,j] for i in I, j in J",
    "capacity[i,j] for i in I, j in J"
  ],
  "decision_variables": ["x[i,j] (continuous or integer assignment from i to j)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "supply_balance[i]: sum(x[i,j] for j in J) == supply[i] for each i in I",
    "demand_balance[j]: sum(x[i,j] for i in I) == demand[j] for each j in J",
    "capacity_limit[i,j]: x[i,j] <= capacity[i,j] for each i in I, j in J"
  ]
}
```

### Common Pitfalls
- Incorrectly ordering the loops when setting constraint coefficients, leading to mismatched indices and incorrect model formulation.
- Not pre-validating that total supply equals total demand, which can cause infeasibility in the standard balanced formulation.
- Using `NumVar` when the problem context (e.g., whole units) implicitly requires integer variables, resulting in impractical fractional solutions.

## Solving stage

### Strategy Overview
Solve the OR-Tools model, check for optimality or feasibility, extract the solution values, and perform verification. This workflow emphasizes the solver's native status codes and efficient solution extraction.

### Step 1 - Execute Solve and Check Status
- Run the solver: `status = solver.Solve()`.
- Check the result status: `if status == pywraplp.Solver.OPTIMAL:` for optimal solution; also accept `FEASIBLE` if optimality is not required.

### Step 2 - Extract Objective and Variable Values
- Retrieve the objective value: `obj_val = solver.Objective().Value()`.
- Iterate over all variable indices `(i, j)` and get the solution value: `val = x[i][j].solution_value()`.
- Filter assignments using an epsilon threshold (e.g., `if val > 1e-6`) to ignore near-zero flows.

### Step 3 - Verify Constraint Satisfaction
- Recompute total assigned quantities per supply and demand node from the extracted solution values.
- Compare these computed totals against the original `supply[i]` and `demand[j]` parameters, allowing for a small tolerance due to floating-point arithmetic.
- Print discrepancies to validate the solution or debug model formulation errors.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Assume solver, x, supply, demand are defined as per Modeling stage
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    print(f"Objective value = {solver.Objective().Value():.2f}")
    # Extract assignments
    for i in range(num_supply):
        for j in range(num_demand):
            val = x[i][j].solution_value()
            if val > 1e-6:
                print(f"  x[{i},{j}] = {val:.2f}")
    # Add verification: recalculate sums and compare to supply/demand
else:
    print("The problem does not have an optimal solution.")
```

### Common Pitfalls
- Relying solely on the `OPTIMAL` status; for some solvers/configurations, a `FEASIBLE` status may be returned even when optimality is reached—check both.
- Not using an epsilon tolerance when comparing recalculated constraint sums to original values, leading to false validation failures due to floating-point errors.
- Forgetting to implement verification logic, which is critical for ensuring the solution correctly implements all supply, demand, and capacity constraints.
