---
name: Binary Facility Coverage Optimization
description: |
  Model and solve budget-constrained maximum coverage problems with two-layer binary variables using either CP-SAT or Pyomo/Highs.
---

# Workflow 1 (CP-SAT for Logical Coverage)

## Modeling stage

### Strategy Overview
Formulate coverage problems using OR-Tools CP-SAT, leveraging its native Boolean variables and logical constraints to directly encode activation relationships between facility selection and service coverage.

### Step 1 - Define Data Structures
- Map coverage relationships: create a dictionary mapping each area to a list of covering facility indices.
- Define cost and weight arrays for facilities and areas, respectively.
- Set a scalar budget limit.

### Step 2 - Create Binary Variables
- Create a Boolean variable `x[j]` for each facility `j` using `model.NewBoolVar()`.
- Create a Boolean variable `y[i]` for each area `i` using `model.NewBoolVar()`.

### Step 3 - Add Coverage Activation Constraints
- For each area `i`, add a linear inequality: `y[i] <= sum(x[j] for j in coverage[i])`. This ensures coverage is only possible if at least one covering facility is selected.

### Step 4 - Add Budget Constraint
- Add a linear constraint: `sum(cost[j] * x[j] for j in facilities) <= budget`.

### Step 5 - Set Weighted Objective
- Maximize the sum: `sum(weight[i] * y[i] for i in areas)`.

### Formulation Template
```json
{
  "sets": ["facilities", "areas"],
  "parameters": ["cost[facilities]", "weight[areas]", "budget", "coverage[areas] -> list(facilities)"],
  "decision_variables": ["x[facilities] ∈ {0,1}", "y[areas] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i] * y[i] for i in areas)"
  },
  "constraints": [
    "y[i] <= sum(x[j] for j in coverage[i]) for each i in areas",
    "sum(cost[j] * x[j] for j in facilities) <= budget"
  ]
}
```

### Common Pitfalls
- Forgetting to define the coverage mapping, leading to incorrect or missing constraints.
- Using `y[i] == sum(...)` instead of `y[i] <= sum(...)`, which incorrectly forces coverage if any facility is selected.
- Not scaling weights or costs appropriately, which can cause numerical issues for the solver.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured parameters for performance and reproducibility, then extract and validate the solution using status-aware logic.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.parameters.max_time_in_seconds = time_limit`.
- Enable parallel search: `solver.parameters.num_search_workers = num_workers`.
- Set a random seed for reproducibility: `solver.parameters.random_seed = seed`.
- Enforce optimality search: `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check if `status` is `OPTIMAL` or `FEASIBLE` before proceeding.

### Step 3 - Extract Solution Values
- For each variable `v`, check if `solver.Value(v) > 0.5` to determine if it is selected/covered.
- Store selected facility indices and covered area indices.

### Step 4 - Validate Solution Feasibility
- Programmatically verify that every covered area has at least one selected facility from its coverage list.
- Ensure the total cost of selected facilities does not exceed the budget.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... create variables and constraints as per modeling stage

# solve with status / termination checks
solver = cp_model.CpSolver()
# Apply parameter configuration from Step 1
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected_facilities = [j for j in facilities if solver.Value(x[j]) > 0.5]
    covered_areas = [i for i in areas if solver.Value(y[i]) > 0.5]
    # Perform validation from Step 4
else:
    # Handle infeasible or error status
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking solver status before reading variable values, causing runtime errors.
- Misinterpreting `FEASIBLE` as `OPTIMAL` in reporting.
- Omitting solution validation, which can mask modeling errors in the coverage mapping.

# Workflow 2 (Pyomo/Highs for MILP Coverage)

## Modeling stage

### Strategy Overview
Formulate the coverage problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract or concrete modeling, separating sets, parameters, and variables for clarity and maintainability.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo Sets for `facilities` and `areas`.
- Declare Pyomo Parameters for `cost`, `weight`, and `budget`.
- Store coverage as a parameter or external mapping.

### Step 2 - Declare Binary Variables
- Define `model.x` as a `pyo.Var` indexed by facilities with `domain=pyo.Binary`.
- Define `model.y` as a `pyo.Var` indexed by areas with `domain=pyo.Binary`.

### Step 3 - Implement Coverage Activation Rule
- Define a Pyomo Constraint rule for each area `a`: `model.y[a] <= sum(model.x[t] for t in coverage[a])`.

### Step 4 - Implement Budget Constraint Rule
- Define a Pyomo Constraint: `sum(model.cost[t] * model.x[t] for t in facilities) <= model.budget`.

### Step 5 - Define Weighted Maximization Objective
- Define `model.obj` as a `pyo.Objective` with `sense=pyo.maximize` and expression `sum(model.weight[a] * model.y[a] for a in areas)`.

### Formulation Template
```json
{
  "sets": ["facilities", "areas"],
  "parameters": ["cost[facilities]", "weight[areas]", "budget", "coverage[areas] -> list(facilities)"],
  "decision_variables": ["x[facilities] ∈ {0,1}", "y[areas] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[a] * y[a] for a in areas)"
  },
  "constraints": [
    "y[a] <= sum(x[t] for t in coverage[a]) for each a in areas",
    "sum(cost[t] * x[t] for t in facilities) <= budget"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters or variables within Pyomo rules, leading to runtime errors.
- Using a dense coverage matrix instead of a sparse mapping, which increases model build time unnecessarily.
- Forgetting to initialize the `budget` parameter before solving.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the Highs solver via the `highs` interface, configure it for performance, and robustly extract the solution after checking termination conditions.

### Step 1 - Instantiate Solver and Set Options
- Create solver instance: `solver = pyo.SolverFactory('highs')`.
- Set options: `solver.options['time_limit'] = time_limit`, `solver.options['mip_rel_gap'] = 0.0`, `solver.options['threads'] = num_threads`.

### Step 2 - Solve and Check Termination Status
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Extract Solution via Value Retrieval
- For each variable `v`, check if `pyo.value(v) > 0.5` to determine selection/coverage.
- Store results in lists or dictionaries for reporting.

### Step 4 - Perform Post-Solution Validation
- Verify coverage logic: for each area with `y[a] == 1`, confirm at least one `x[t] == 1` for `t` in its coverage list.
- Calculate total cost and confirm it is within budget.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, and objective as per modeling stage

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = time_limit
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    selected_facilities = [t for t in model.facilities if pyo.value(model.x[t]) > 0.5]
    covered_areas = [a for a in model.areas if pyo.value(model.y[a]) > 0.5]
    # Perform validation from Step 4
else:
    # Handle solver failure
    print("Solver did not return a feasible solution.")
```

### Common Pitfalls
- Confusing `SolverStatus` with `TerminationCondition`, leading to incorrect solution acceptance logic.
- Not using `pyo.value()` to access variable values in a Pyomo model after solving.
- Setting invalid solver options (e.g., negative gap) that cause the solver to fail silently.
