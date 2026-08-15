---
name: MultiDimensionalAllocationLP
description: |
  Model and solve multi-dimensional allocation problems with demand satisfaction and profit maximization using structured set-based formulations and robust solver integration.
---

# Workflow 1 (OR-Tools/GLOP for Linear Programming)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) with the GLOP backend, ideal for pure linear programming problems with continuous variables. It emphasizes explicit variable and constraint construction via coefficient setting.

### Step 1 - Define Data Structures
- Organize input data as multi-dimensional arrays or dictionaries, ensuring alignment between indices (e.g., `profit[source][destination][item]` and `demand[destination][item]`).
- Use descriptive key names (e.g., `companies`, `markets`, `products`) for clarity and to prevent index confusion during model building.

### Step 2 - Create Decision Variables
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Create non-negative continuous variables using nested loops over all dimensions: `x[i, j, k] = solver.NumVar(0, solver.infinity(), f'x_{i}_{j}_{k}')`. The lower bound of 0 enforces non-negativity implicitly.

### Step 3 - Formulate Demand Satisfaction Constraints
- For each (destination, item) pair, create an equality constraint with both lower and upper bounds set to the demand value: `constraint = solver.Constraint(demand_val, demand_val)`.
- Add a coefficient of 1 for the variable from each source to this constraint: `constraint.SetCoefficient(x[i, j, k], 1)`.

### Step 4 - Build the Objective Function
- Create the objective: `objective = solver.Objective()`.
- Iterate over all variable indices and set their coefficients to the corresponding profit value: `objective.SetCoefficient(x[i, j, k], profit[i][j][k])`.
- Set the sense to maximization: `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": [
    {"name": "sources", "description": "Set of supplying entities (e.g., companies, factories)."},
    {"name": "destinations", "description": "Set of receiving entities (e.g., markets, warehouses)."},
    {"name": "items", "description": "Set of products or resources being allocated."}
  ],
  "parameters": [
    {"name": "profit", "index": ["source", "destination", "item"], "description": "Unit profit for allocating one unit of item from source to destination."},
    {"name": "demand", "index": ["destination", "item"], "description": "Exact demand quantity required at each destination for each item."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["source", "destination", "item"], "description": "Quantity allocated from source to destination of item.", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[source, destination, item] * x[source, destination, item] over all indices)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["destination", "item"], "expression": "sum(x[source, destination, item] for all sources) == demand[destination, item]"}
  ]
}
```

### Common Pitfalls
- Misaligning indices between profit table and variable creation loops, leading to incorrect objective coefficients.
- Forgetting to set the objective sense (`SetMaximization` or `SetMinimization`), resulting in a default minimization problem.
- Using `solver.infinity()` for an upper bound when a finite capacity constraint should exist, potentially missing model errors.

## Solving stage

### Strategy Overview
This stage focuses on executing the model with the GLOP solver, rigorously checking solution status, and extracting/verifying results. It includes patterns for error handling and solution analysis.

### Step 1 - Execute the Solver
- Call `solver.Solve()` to initiate the optimization.
- No additional solver options are typically required for GLOP, as it is a pure LP solver.

### Step 2 - Check Solution Status
- Verify the solver status: `if status == pywraplp.Solver.OPTIMAL:`. Also handle `FEASIBLE` status for non-optimal but acceptable solutions.
- If status is not `OPTIMAL` or `FEASIBLE`, implement a failure branch that reports the status (e.g., `INFEASIBLE`, `UNBOUNDED`) for diagnostics.

### Step 3 - Extract and Validate Solution
- Extract the objective value: `total_profit = objective.Value()`.
- Iterate over all decision variables and collect those with a positive value (`if x[i, j, k].solution_value() > tolerance`).
- For validation, recompute the total allocated quantity per (destination, item) pair and assert it equals the demand within a small tolerance (e.g., `1e-6`).

### Step 4 - Report Results
- Print a structured summary including the total objective value.
- Output details of positive allocations, showing source, destination, item, quantity, and its contribution to profit.
- Optionally, format key results with prefixes like `RESULT:` for automated parsing in downstream workflows.

### Code Usage
```python
# Solve the model
status = solver.Solve()

# Check status and process results
if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    print(f"Optimal total profit: {objective.Value():.2f}")
    # Extract positive allocations
    for i in sources:
        for j in destinations:
            for k in items:
                val = x[i, j, k].solution_value()
                if val > 1e-6:
                    print(f"  {i} -> {j} ({k}): {val:.2f} units")
    # Verify demand satisfaction
    for j in destinations:
        for k in items:
            total_allocated = sum(x[i, j, k].solution_value() for i in sources)
            if abs(total_allocated - demand[j][k]) > 1e-6:
                print(f"WARNING: Demand mismatch for {j}, {k}")
else:
    print(f"Solver did not find an optimal solution. Status: {status}")
```

### Common Pitfalls
- Assuming optimality without checking the solver status, leading to errors when accessing solution values from failed solves.
- Using a zero tolerance (`> 0`) for filtering positive allocations, which may miss very small non-zero values due to numerical precision; use a small epsilon instead.
- Neglecting to verify constraint satisfaction, which can hide modeling errors even if the solver returns an `OPTIMAL` status.

# Workflow 2 (Pyomo with HiGHS/CBC Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define sets, parameters, and variables declaratively. It is solved using the HiGHS (LP) or CBC (MIP) solvers via `SolverFactory`, offering a flexible and expressive approach suitable for complex or extended models.

### Step 1 - Define Abstract Sets and Parameters
- Create Pyomo sets for each dimension using `pyo.Set(initialize=...)` (e.g., `model.SOURCES`, `model.DESTINATIONS`, `model.ITEMS`).
- Define parameters using `pyo.Param` with multi-dimensional indexing. Initialize `model.profit` and `model.demand` from dictionaries with tuple keys `(source, dest, item)` and `(dest, item)` respectively.

### Step 2 - Declare Decision Variables
- Create a continuous decision variable indexed over all sets: `model.x = pyo.Var(model.SOURCES, model.DESTINATIONS, model.ITEMS, domain=pyo.NonNegativeReals)`. The domain enforces non-negativity.

### Step 3 - Formulate Constraints via Rules
- Define a Pyomo `Constraint` using a rule function. For demand satisfaction, create a rule that returns `sum(model.x[c, m, p] for c in model.SOURCES) == model.demand[m, p]` for each `(m, p)` index pair.
- Apply the constraint using `model.demand_constraint = pyo.Constraint(model.DESTINATIONS, model.ITEMS, rule=demand_rule)`.

### Step 4 - Construct the Objective
- Define the objective as a `pyo.Objective` using a rule or expression: `model.obj = pyo.Objective(expr=sum(model.profit[c, m, p] * model.x[c, m, p] for c, m, p in model.SOURCES * model.DESTINATIONS * model.ITEMS), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "SOURCES", "description": "Pyomo Set of origin points."},
    {"name": "DESTINATIONS", "description": "Pyomo Set of destination points."},
    {"name": "ITEMS", "description": "Pyomo Set of item types."}
  ],
  "parameters": [
    {"name": "profit", "index": ["SOURCES", "DESTINATIONS", "ITEMS"], "pyomo_type": "Param", "description": "Unit profit parameter."},
    {"name": "demand", "index": ["DESTINATIONS", "ITEMS"], "pyomo_type": "Param", "description": "Demand parameter."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["SOURCES", "DESTINATIONS", "ITEMS"], "pyomo_type": "Var", "domain": "NonNegativeReals", "description": "Allocation variable."}
  ],
  "objective": {
    "sense": "max",
    "pyomo_expression": "sum(profit[s, d, i] * x[s, d, i] for s in SOURCES for d in DESTINATIONS for i in ITEMS)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["DESTINATIONS", "ITEMS"], "pyomo_rule": "sum(x[s, d, i] for s in SOURCES) == demand[d, i]"}
  ]
}
```

### Common Pitfalls
- Incorrectly ordering indices in parameter dictionaries relative to set definitions, causing `KeyError` during model instantiation.
- Using Python's built-in `sum` inside Pyomo expressions on large sets, which can be slow; prefer Pyomo's `summation` or generator expressions.
- Forgetting to deactivate the solver's `load_solutions` option when implementing robust error handling, leading to crashes on infeasible models.

## Solving stage

### Strategy Overview
This stage configures the chosen solver (HiGHS for LP, CBC for MIP), executes the model with error handling, and implements rigorous solution checking and extraction patterns specific to Pyomo's results object.

### Step 1 - Configure and Execute Solver
- Create solver object: `solver = pyo.SolverFactory('highs')` (or `'cbc'`).
- Set practical options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`. For CBC, also set `solver.options['ratio'] = 0.0` for zero optimality gap.
- Solve with `load_solutions=False` for robust error handling: `results = solver.solve(model, tee=False, load_solutions=False)`.

### Step 2 - Check Solver Status and Termination
- Import `pyo.SolverStatus` and `pyo.TerminationCondition`.
- Verify: `if results.solver.status == SolverStatus.ok and results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:`.
- If conditions are not met, handle the failure by reporting the termination condition and status in a structured format (e.g., JSON).

### Step 3 - Load and Extract Solution
- Only if the status checks pass, load the solution: `model.solutions.load_from(results)`.
- Extract the objective value: `objective_value = pyo.value(model.obj)`.
- Iterate over variables to get values: `val = pyo.value(model.x[s, d, i])`. Filter for positive allocations using a tolerance.

### Step 4 - Verify and Report
- Recompute total allocation per demand constraint and compare against the original `demand` parameter within tolerance.
- Print a summary including the objective value and a table of non-zero allocations.
- For automation, output key results with a parsable prefix (e.g., `RESULT_JSON:{...}`).

### Code Usage
```python
# Solve with error handling
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False, load_solutions=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term == TerminationCondition.optimal:
    model.solutions.load_from(results)
    objective_value = float(pyo.value(model.obj))
    print(f"Optimal objective: {objective_value:.2f}")

    # Extract and display positive allocations
    for s in model.SOURCES:
        for d in model.DESTINATIONS:
            for i in model.ITEMS:
                val = pyo.value(model.x[s, d, i])
                if val > 1e-6:
                    print(f"  {s} -> {d} ({i}): {val:.2f}")
    # Optional verification
    for d in model.DESTINATIONS:
        for i in model.ITEMS:
            total = sum(pyo.value(model.x[s, d, i]) for s in model.SOURCES)
            if abs(total - pyo.value(model.demand[d, i])) > 1e-6:
                print(f"Verification failed for {d}, {i}")
else:
    # Handle failure
    print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'termination_condition': str(term)})}")
```

### Common Pitfalls
- Accessing `pyo.value(model.obj)` before loading the solution, resulting in `None` or an uninitialized value.
- Using `results.solver.termination_condition == 'optimal'` (string) instead of the `TerminationCondition.optimal` enum, which may fail depending on Pyomo/solver version.
- Not setting a `time_limit`, allowing the solver to run indefinitely on large or difficult instances.
