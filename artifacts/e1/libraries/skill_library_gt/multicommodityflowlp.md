---
name: MultiCommodityFlowLP
description: |
  Model and solve multi-commodity flow problems with bundle capacity constraints using linear programming, featuring both direct solver API and algebraic modeling framework workflows.

---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
This workflow models the problem using a direct solver API (e.g., OR-Tools, PuLP) where variables and constraints are built via explicit loops and coefficient setting. It is suitable for users who prefer procedural control and direct interaction with the solver's native objects.

### Step 1 - Define Data Structures
- Organize problem data using dictionaries or arrays with clear, multi-dimensional keys (e.g., `(origin, product)` for supply).
- Use placeholders like `origins`, `destinations`, `products` for index sets.
- Store parameters: `supply[origin][product]`, `demand[destination][product]`, `cost[origin][destination][product]`, `capacity[origin][destination]`.

### Step 2 - Create Flow Variables
- Instantiate a three-dimensional, continuous, non-negative decision variable `x[origin][destination][product]`.
- Use the solver's method for creating variables (e.g., `solver.NumVar`), setting a lower bound of 0 and an upper bound of infinity.

### Step 3 - Formulate Supply Constraints
- For each `origin` and `product`, create a linear constraint: `sum_{destination} x[origin][destination][product] == supply[origin][product]`.
- Use equality to enforce that all available supply is shipped.

### Step 4 - Formulate Demand Constraints
- For each `destination` and `product`, create a linear constraint: `sum_{origin} x[origin][destination][product] == demand[destination][product]`.
- Use equality to guarantee all demand is satisfied.

### Step 5 - Formulate Bundle Capacity Constraints
- For each `origin` and `destination`, create a linear inequality constraint: `sum_{product} x[origin][destination][product] <= capacity[origin][destination]`.
- This aggregates flow across all commodities on a given arc.

### Step 6 - Define Linear Cost Objective
- Define the objective as `minimize sum_{origin, destination, product} cost[origin][destination][product] * x[origin][destination][product]`.
- Use the solver's method to set the objective sense and coefficients.

### Formulation Template
```json
{
  "sets": ["origins", "destinations", "products"],
  "parameters": [
    "supply[origin][product]",
    "demand[destination][product]",
    "cost[origin][destination][product]",
    "capacity[origin][destination]"
  ],
  "decision_variables": ["x[origin][destination][product] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j][p] * x[i][j][p] )"
  },
  "constraints": [
    "sum_j x[i][j][p] == supply[i][p] for all i, p",
    "sum_i x[i][j][p] == demand[j][p] for all j, p",
    "sum_p x[i][j][p] <= capacity[i][j] for all i, j"
  ]
}
```

### Common Pitfalls
- Using inequality (`<=`) for supply/demand when exact fulfillment is required, leading to incorrect solutions.
- Mismatching indices between variable definitions and parameter lookups, causing constraint errors.
- Forgetting to set an upper bound on variables, which is implicitly infinite but should be explicit for clarity.

## Solving stage

### Strategy Overview
This stage involves creating a solver instance, building the model via loops, solving, and rigorously checking the solution status and feasibility. It emphasizes manual verification of results.

### Step 1 - Initialize Solver
- Create a linear programming solver instance appropriate for continuous variables (e.g., `GLOP` for OR-Tools, `PULP_CBC_CMD` for PuLP).
- Verify the solver backend is available.

### Step 2 - Build Model via Loops
- Use nested loops over `origins`, `destinations`, `products` to create variables and add them to constraints.
- For each constraint type, create an empty constraint object and then populate it by iterating over the relevant variables and setting coefficients.

### Step 3 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the solution status: confirm it is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error messages.

### Step 4 - Extract and Verify Solution
- Extract the objective value.
- Retrieve variable values using `solution_value()` or equivalent method.
- Programmatically verify all constraints by recomputed sums, using a small tolerance (e.g., `1e-6`) for numerical comparisons.

### Step 5 - Report Results
- Print the objective value in a parseable format (e.g., `RESULT: <value>`).
- Optionally, list non-zero flows above a tolerance for interpretability.

### Code Usage
```python
# Example using OR-Tools (conceptual)
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... variable and constraint creation loops ...
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    # Verify constraints
    for i in origins:
        for p in products:
            total = sum(x[i, j, p].solution_value() for j in destinations)
            assert abs(total - supply[i, p]) <= 1e-6
    # Extract flows
    flows = {(i, j, p): x[i, j, p].solution_value() for i, j, p in indices if x[i, j, p].solution_value() > 1e-6}
else:
    # Handle failure
    print("Solver failed:", status)
```

### Common Pitfalls
- Not checking solver status before extracting values, leading to runtime errors.
- Using loose tolerances for feasibility checks, potentially accepting infeasible solutions.
- Building constraints inefficiently in nested loops, which is acceptable for small problems but may need optimization for large-scale instances.

---

# Workflow 2 (Algebraic Modeling Framework)

## Modeling stage

### Strategy Overview
This workflow uses an algebraic modeling framework (e.g., Pyomo, Google OR-Tools CP-SAT for linear expressions) to declaratively define sets, variables, and constraints. It is suitable for complex models, promotes maintainability, and leverages solver-independent formulation.

### Step 1 - Define Abstract Sets
- Declare index sets as `model.origins`, `model.destinations`, `model.products`.
- Initialize them with placeholder lists.

### Step 2 - Declare Parameters
- Define parameters (supply, demand, cost, capacity) as `pyo.Param` objects indexed by the appropriate sets, or use external dictionaries accessed within constraint rules.
- This separates model logic from data.

### Step 3 - Define Flow Variables
- Declare a non-negative continuous variable `model.x` indexed over `origins × destinations × products`.

### Step 4 - Formulate Constraints via Rules
- Define supply constraint rule: returns `sum(model.x[i, j, p] for j in model.destinations) == supply[i, p]`.
- Define demand constraint rule: returns `sum(model.x[i, j, p] for i in model.origins) == demand[j, p]`.
- Define bundle capacity constraint rule: returns `sum(model.x[i, j, p] for p in model.products) <= capacity[i, j]`.
- Use `pyo.Constraint` with the appropriate indexing sets and rules.

### Step 5 - Define Objective
- Define the objective as a `pyo.Objective` with `sense=pyo.minimize` and an expression summing `cost[i, j, p] * model.x[i, j, p]`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations", "products"],
  "parameters": [
    "supply (indexed by origin, product)",
    "demand (indexed by destination, product)",
    "cost (indexed by origin, destination, product)",
    "capacity (indexed by origin, destination)"
  ],
  "decision_variables": ["x[origin, destination, product] in NonNegativeReals"],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i, j, p] * x[i, j, p] )"
  },
  "constraints": [
    "SupplyCon[i, p]: sum_j x[i, j, p] == supply[i, p]",
    "DemandCon[j, p]: sum_i x[i, j, p] == demand[j, p]",
    "CapacityCon[i, j]: sum_p x[i, j, p] <= capacity[i, j]"
  ]
}
```

### Common Pitfalls
- Passing data directly inside constraint rules without proper indexing, causing scope errors.
- Using mutable global variables within Pyomo rules, which can lead to incorrect or stale data.
- Confusing Pyomo's `value()` function for parameter access vs. variable value extraction.

## Solving stage

### Strategy Overview
This stage involves instantiating a concrete model, selecting an LP solver (e.g., HiGHS, CBC), configuring solver options, solving, and performing detailed termination and solution validation.

### Step 1 - Instantiate Model and Set Data
- Create a concrete model instance.
- Populate parameter dictionaries or initialize `pyo.Param` objects with the problem data.

### Step 2 - Select and Configure Solver
- Create a solver factory object (e.g., `SolverFactory('highs')`).
- Set solver options like `time_limit`, `threads`, or `optimality_gap` as needed.

### Step 3 - Solve and Check Termination
- Call `solver.solve(model, ...)`.
- Check both `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 4 - Extract and Validate Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Retrieve variable values via `pyo.value(model.x[i, j, p])` or dictionary comprehension.
- Implement a verification function that recomputes constraint left-hand sides and compares them to limits with tolerance.

### Step 5 - Report and Analyze
- Print the objective value.
- Optionally, analyze binding constraints (e.g., capacity utilization) and non-zero flows.

### Code Usage
```python
# Example using Pyomo with HiGHS (conceptual)
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
# ... define sets, variables, constraints, objective ...
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = pyo.value(model.obj)
    # Verification loop
    for i in model.origins:
        for p in model.products:
            total = sum(pyo.value(model.x[i, j, p]) for j in model.destinations)
            assert abs(total - supply[i, p]) <= 1e-6
    # Extract flows
    flows = {(i, j, p): pyo.value(model.x[i, j, p]) for i, j, p in model.x if pyo.value(model.x[i, j, p]) > 1e-6}
else:
    # Handle failure
    print(f"Solver terminated with status: {status}, condition: {term}")
```

### Common Pitfalls
- Not checking both solver status and termination condition, missing cases where the solver finishes but without a guarantee of optimality.
- Setting conflicting solver options that cause runtime errors; consult solver documentation.
- Forgetting to call `pyo.value()` on the objective expression, leading to an expression object instead of a float.
