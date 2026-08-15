---
name: IntegerLinearProgram_NutrientOptimization
description: |
  Model and solve integer linear programs for diet/nutrient optimization with non-negative integer servings, linear nutrient bounds, volume capacity, and linear cost minimization.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling style, separating data parameters from model structure. Define sets for indexing, integer decision variables, and linear constraints for nutrient bounds and capacity.

### Step 1 - Define Sets and Parameters
- Define a set `FOODS` for all available food items and a set `NUTRIENTS` for all relevant nutrients.
- Create parameters for cost per serving (`cost`), volume per serving (`volume`), nutrient content matrix (`nutrient_content`), nutrient minimums (`nutrient_min`), nutrient maximums (`nutrient_max`), and a total volume capacity (`max_volume`).

### Step 2 - Create Decision Variables
- Define a non-negative integer decision variable `servings[f]` for each food `f` in `FOODS`, representing the number of servings to consume.

### Step 3 - Formulate Objective and Constraints
- Set the objective to minimize the total linear cost: `sum(cost[f] * servings[f] for f in FOODS)`.
- For each nutrient `n` in `NUTRIENTS`, add two linear constraints: a lower bound (`>= nutrient_min[n]`) and an upper bound (`<= nutrient_max[n]`) on the total nutrient intake.
- Add a single linear volume capacity constraint: `sum(volume[f] * servings[f] for f in FOODS) <= max_volume`.

### Formulation Template
```json
{
  "sets": ["FOODS", "NUTRIENTS"],
  "parameters": {
    "cost": {"index": ["FOODS"], "type": "float"},
    "volume": {"index": ["FOODS"], "type": "float"},
    "nutrient_content": {"index": ["FOODS", "NUTRIENTS"], "type": "float"},
    "nutrient_min": {"index": ["NUTRIENTS"], "type": "float"},
    "nutrient_max": {"index": ["NUTRIENTS"], "type": "float"},
    "max_volume": {"type": "float"}
  },
  "decision_variables": [
    {"name": "servings", "index": ["FOODS"], "type": "NonNegativeIntegers"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[f] * servings[f] for f in FOODS)"
  },
  "constraints": [
    {"name": "nutrient_min_constraint", "index": ["NUTRIENTS"], "expression": "sum(nutrient_content[f, n] * servings[f] for f in FOODS) >= nutrient_min[n]"},
    {"name": "nutrient_max_constraint", "index": ["NUTRIENTS"], "expression": "sum(nutrient_content[f, n] * servings[f] for f in FOODS) <= nutrient_max[n]"},
    {"name": "volume_capacity", "expression": "sum(volume[f] * servings[f] for f in FOODS) <= max_volume"}
  ]
}
```

### Common Pitfalls
- Hard-coding parameter values directly into constraint expressions, which reduces model adaptability.
- Forgetting to define both minimum and maximum bounds for each nutrient, leading to an incomplete nutritional model.
- Using continuous variables when integer servings are required, resulting in unrealistic fractional solutions.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver via the `SolverFactory`. Configure solver options for optimality and time limits, then verify solver status and termination condition before extracting and validating the solution.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object using `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set solver options such as `time_limit` and `mip_rel_gap` (e.g., `0.0` for optimality) to control solution quality and runtime.

### Step 2 - Solve and Check Status
- Call `solver.solve(model)` and capture the results object.
- Check that `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`. If not, handle the infeasible or error state appropriately.

### Step 3 - Extract and Validate Solution
- Extract the values of `model.servings` for all foods, focusing on non-zero servings.
- Calculate derived totals (total cost, total volume, nutrient sums) from the solution.
- Programmatically verify that all nutrient bounds and the volume capacity constraint are satisfied within a small tolerance.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import numpy as np

# --- Assume model 'model' is built according to the formulation ---
# Example data generation if parameters are not provided
np.random.seed(42)  # For reproducibility
# ... populate model parameters ...

# Solve
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model)

# Status and termination checks
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    # Extract solution
    servings_sol = {f: pyo.value(model.servings[f]) for f in model.FOODS}
    # Validation logic here
    print(f"Objective: {pyo.value(model.objective)}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Accessing solution values without checking solver status, leading to errors when the problem is infeasible.
- Not setting a random seed when generating placeholder data, causing non-reproducible results.
- Omitting solution validation, which can miss subtle constraint violations due to numerical tolerances.

# Workflow 2 (OR-Tools with CBC)

## Modeling stage

### Strategy Overview
Model the problem directly using the OR-Tools CP-SAT or MPSolver interface, constructing the model procedurally. Define integer variables, then add linear constraints and objective term by term.

### Step 1 - Initialize Solver and Create Variables
- Create a MIP solver instance using `ortools.linear_solver.pywraplp.Solver.CreateSolver('CBC')`.
- For each food item, create an integer variable with a lower bound of 0 and an upper bound set to a large number (or `solver.infinity()`) to represent servings.

### Step 2 - Add Nutrient and Capacity Constraints
- For each nutrient, create two linear constraints: one for the minimum (`sum(coeff * variable) >= min_req`) and one for the maximum (`sum(coeff * variable) <= max_req`), using the solver's `Add` method.
- Add a single linear constraint for the total volume capacity.

### Step 3 - Define the Linear Objective
- Set the objective to minimize by calling `solver.Minimize()`.
- Add the linear cost terms using `objective.SetCoefficient(variable, cost)` for each food variable.

### Formulation Template
```json
{
  "sets": ["FOODS", "NUTRIENTS"],
  "parameters": {
    "cost": {"index": ["FOODS"], "type": "float"},
    "volume": {"index": ["FOODS"], "type": "float"},
    "nutrient_content": {"index": ["FOODS", "NUTRIENTS"], "type": "float"},
    "nutrient_min": {"index": ["NUTRIENTS"], "type": "float"},
    "nutrient_max": {"index": ["NUTRIENTS"], "type": "float"},
    "max_volume": {"type": "float"}
  },
  "decision_variables": [
    {"name": "servings", "index": ["FOODS"], "type": "integer", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[f] * servings[f] for f in FOODS)"
  },
  "constraints": [
    {"name": "nutrient_min", "index": ["NUTRIENTS"], "expression": "sum(nutrient_content[f, n] * servings[f] for f in FOODS) >= nutrient_min[n]"},
    {"name": "nutrient_max", "index": ["NUTRIENTS"], "expression": "sum(nutrient_content[f, n] * servings[f] for f in FOODS) <= nutrient_max[n]"},
    {"name": "volume_cap", "expression": "sum(volume[f] * servings[f] for f in FOODS) <= max_volume"}
  ]
}
```

### Common Pitfalls
- Manually writing out each constraint for large sets instead of using loops over indices, making code verbose and error-prone.
- Setting unreasonably tight upper bounds on integer variables, which can artificially restrict the feasible region.
- Neglecting to define both sense and coefficients for the objective, resulting in an unset or incorrect objective function.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools wrapper for the CBC solver. After solving, check the result status, extract the integer solution, and perform post-solution validation of constraints.

### Step 1 - Solve and Interpret Result Status
- Call `solver.Solve()`.
- Check the result status: `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE` indicates a valid solution. Handle `INFEASIBLE` or other statuses with appropriate error messages.

### Step 2 - Extract Solution Values
- If the status is optimal or feasible, iterate through the decision variables and retrieve their solution values using `variable.solution_value()`.
- Store non-zero values and compute aggregate metrics (total cost, volume, nutrient sums).

### Step 3 - Validate Against Constraints
- Recompute the left-hand side of each constraint using the extracted solution values.
- Compare against the constraint bounds (minimums, maximums, capacity) to ensure they are satisfied within a small numerical tolerance.

### Code Usage
```python
from ortools.linear_solver import pywraplp
import random

# For reproducible data generation
random.seed(123)

# Initialize solver
solver = pywraplp.Solver.CreateSolver('CBC')
# ... create variables 'x' indexed by FOODS ...
# ... add constraints using loops over NUTRIENTS and FOODS ...
# ... set objective ...

# Solve
status = solver.Solve()

# Status check and solution extraction
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = 0
    for f in FOODS:
        val = x[f].solution_value()
        if val > 0:
            total_cost += cost[f] * val
    print(f"Optimal cost: {total_cost}")
    # Add validation logic here
elif status == solver.INFEASIBLE:
    print("Model is infeasible.")
else:
    print(f"Solver returned status: {status}")
```

### Common Pitfalls
- Treating a `FEASIBLE` status the same as `OPTIMAL` without noting the potential optimality gap, which may misrepresent solution quality.
- Failing to handle the case where the solver hits a time limit and returns `FEASIBLE`, leading to potentially suboptimal results being accepted as optimal.
- Not using a random seed when generating synthetic data for testing, making debugging difficult due to non-deterministic behavior.
