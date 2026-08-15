---
name: Budgeted Weighted Coverage
description: |
  Model and solve budget-constrained weighted coverage problems using binary selection and coverage variables with implication constraints, implemented in either CP-SAT or Pyomo with MILP solvers.
---

# Workflow 1 (CP-SAT for Constraint Programming)

## Modeling stage

### Strategy Overview
Formulate the problem using Google's OR-Tools CP-SAT solver, which is designed for integer programming with Boolean logic. The model uses binary variables for both selection and coverage, with linear constraints to link them via coverage implications and a knapsack constraint for the budget.

### Step 1 - Define Variables and Data
- Define two sets of binary decision variables: `x[i]` for selecting item `i` and `y[j]` for covering outcome `j`.
- Prepare input data: item costs, outcome weights, total budget, and a coverage map `coverage_map[j]` listing which items can cover outcome `j`.

### Step 2 - Build Coverage Implication Constraints
- For each outcome `j`, add a linear constraint: `y[j] <= sum(x[i] for i in coverage_map[j])`. This ensures coverage is only possible if at least one covering item is selected.
- This formulation does not force coverage if an item is selected, which is correct for a maximization objective.

### Step 3 - Apply Budget Constraint
- Add a knapsack constraint: `sum(cost[i] * x[i] for i in items) <= budget`. Use integer coefficients for the costs.

### Step 4 - Set Objective
- Define the objective to maximize the total weighted coverage: `Maximize(sum(weight[j] * y[j] for j in outcomes))`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "outcomes"
  ],
  "parameters": [
    "cost[items]",
    "weight[outcomes]",
    "budget",
    "coverage_map[outcomes] -> list of items"
  ],
  "decision_variables": [
    "x[items] ∈ {0,1}",
    "y[outcomes] ∈ {0,1}"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[j] * y[j] for j in outcomes)"
  },
  "constraints": [
    "y[j] <= sum(x[i] for i in coverage_map[j]) for each j",
    "sum(cost[i] * x[i] for i in items) <= budget"
  ]
}
```

### Common Pitfalls
- Forgetting to define the coverage map as a list-of-lists, leading to incorrect constraint generation.
- Using a strict equality (`y[j] == ...`) for coverage, which incorrectly forces coverage when an item is selected and can make the problem infeasible.
- Not scaling cost or weight parameters to integers, which CP-SAT requires for exact arithmetic.

## Solving stage

### Strategy Overview
Solve the model using the CP-SAT solver with configured parameters for time limit, parallelism, and optimality gap. Extract and validate the solution, providing clear outputs and error handling.

### Step 1 - Initialize Solver and Set Parameters
- Create a `CpModel` and add the formulated constraints and objective.
- Instantiate the `CpSolver` and configure key parameters: `max_time_in_seconds`, `num_search_workers`, and `random_seed` for reproducibility. Set `relative_gap_limit` to `0.0` for an optimality guarantee.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)` and capture the status.
- Before extracting values, verify the status is `OPTIMAL` or `FEASIBLE`. If not, output a structured error message.

### Step 3 - Extract and Validate Solution
- Retrieve selected items: `[i for i in items if solver.Value(x[i]) == 1]`.
- Retrieve covered outcomes: `[j for j in outcomes if solver.Value(y[j]) == 1]`.
- Validate feasibility by recomputing the total cost and checking it against the budget, and verifying each covered outcome has at least one selected covering item.

### Step 4 - Report Results
- Output the selected items, covered outcomes, total value, and total cost.
- Print the final objective value in a parseable format like `RESULT:{value}`.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... define variables, constraints, objective as per modeling stage

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected_items = [i for i in range(num_items) if solver.Value(x[i]) == 1]
    covered_outcomes = [j for j in range(num_outcomes) if solver.Value(y[j]) == 1]
    total_cost = sum(cost[i] for i in selected_items)
    total_value = sum(weight[j] for j in covered_outcomes)
    # ... validation and output
    print(f"RESULT:{solver.ObjectiveValue()}")
else:
    # Output structured error
    error_info = {"status": status, "message": "Solver did not find a solution."}
    print(error_info)
```

### Common Pitfalls
- Not checking solver status before calling `Value()` on variables, which can cause runtime errors.
- Misinterpreting `FEASIBLE` as optimal; for reporting, distinguish between optimal and feasible solutions.
- Omitting post-solution validation, which can miss subtle constraint violations due to solver tolerances.

# Workflow 2 (Pyomo for MILP with Commercial/Open-Source Solvers)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using Pyomo, an algebraic modeling language. This approach decouples the model definition from the solver backend, allowing use of solvers like Gurobi, CBC, or CPLEX.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for items and outcomes.
- Declare `Param` objects for costs, weights, budget, and store the coverage map as an external data structure.

### Step 2 - Create Binary Variables
- Define two `Var` containers with `domain=pyo.Binary`: `x` for item selection and `y` for outcome coverage.

### Step 3 - Implement Coverage Implication Rule
- For each outcome `j`, add a constraint: `y[j] <= sum(x[i] for i in coverage_map[j])`. Implement this via a Pyomo `Constraint` rule that iterates over outcomes.

### Step 4 - Enforce Budget and Objective
- Add a single budget constraint: `sum(cost[i] * x[i] for i in items) <= budget`.
- Set the objective to maximize `sum(weight[j] * y[j] for j in outcomes)`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "outcomes"
  ],
  "parameters": [
    "cost[items]",
    "weight[outcomes]",
    "budget",
    "coverage_map[outcomes] -> list of items"
  ],
  "decision_variables": [
    "x[items] ∈ {0,1}",
    "y[outcomes] ∈ {0,1}"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[j] * y[j] for j in outcomes)"
  },
  "constraints": [
    "y[j] <= sum(x[i] for i in coverage_map[j]) for each j",
    "sum(cost[i] * x[i] for i in items) <= budget"
  ]
}
```

### Common Pitfalls
- Defining the coverage map as a Pyomo `Param` with complex indexing; it's often simpler to keep it as a Python dictionary and access it within constraint rules.
- Using `==` instead of `<=` in coverage constraints, which over-constrains the model.
- Not initializing parameters correctly when building a `ConcreteModel`, leading to missing data errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver via the `SolverFactory`. Configure solver-specific options for time limit, optimality gap, and parallelism. Robustly check termination conditions and extract the solution.

### Step 1 - Instantiate Solver and Set Options
- Use `SolverFactory('solver_name')` (e.g., `'gurobi'`, `'cbc'`).
- Set options such as `TimeLimit`, `MIPGap` (or `ratio`), `Threads`, and `Seed` for reproducibility and performance.

### Step 2 - Solve and Verify Termination
- Call `solver.solve(model, tee=True)` and capture the results object.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`optimal` or `feasible`). Proceed only if both indicate a valid solution.

### Step 3 - Extract and Validate Solution Values
- Retrieve variable values using `pyo.value(var)` or `model.var[index].value`.
- Collect selected items where `value(x[i]) > 0.5` and covered outcomes similarly.
- Perform post-solution validation: compute actual cost and verify coverage implications.

### Step 4 - Report Comprehensive Results
- Output lists of selected items and covered outcomes, along with total cost, total value, and objective value.
- Structure outputs for easy parsing and downstream use.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# build model from formulation (example using ConcreteModel)
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=range(num_items))
model.outcomes = pyo.Set(initialize=range(num_outcomes))
# ... define parameters, variables, constraints, objective as per modeling stage

# solve with status / termination checks
solver = SolverFactory('gurobi')  # or 'cbc'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 8
solver.options['Seed'] = 42

results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    selected_items = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
    covered_outcomes = [j for j in model.outcomes if pyo.value(model.y[j]) > 0.5]
    total_cost = sum(cost[i] for i in selected_items)
    total_value = sum(weight[j] for j in covered_outcomes)
    # ... validation and output
    print(f"RESULT:{pyo.value(model.obj)}")
else:
    # Output structured error
    error_info = {
        "solver_status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
    print(error_info)
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran without error) with `TerminationCondition.optimal` (solution is optimal); both checks are necessary.
- Using `model.var[index]` without checking if the variable exists, leading to `KeyError`.
- Forgetting to call `pyo.value()` on objective expressions, which returns the expression object, not the numerical value.
