---
name: Multi-commodity Flow Optimization
description: |
  Model and solve multi-commodity flow problems with shared arc capacities using LP/MIP solvers, ensuring supply-demand balance and cost minimization.
---

# Workflow 1 (OR-Tools / Pywraplp)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using Google OR-Tools' `pywraplp` interface. This workflow is efficient for prototyping and solving pure linear multi-commodity flow problems with a straightforward, imperative modeling style.

### Step 1 - Define Data Structures
- Use nested lists or dictionaries to store parameters: `supply[origin][product]`, `demand[destination][product]`, `cost[origin][destination][product]`, `capacity[origin][destination]`.
- Ensure data dimensions are consistent: the number of origins, destinations, and products defines the problem size.

### Step 2 - Create Decision Variables
- Instantiate a three-dimensional array of continuous, non-negative decision variables `x[i][j][k]` representing the flow of product `k` from origin `i` to destination `j`.
- Use `solver.NumVar(0, solver.infinity(), name)` to create each variable.

### Step 3 - Add Supply and Demand Constraints
- For each origin `i` and product `k`, add a linear equality constraint: `sum_{j} x[i][j][k] == supply[i][k]`.
- For each destination `j` and product `k`, add a linear equality constraint: `sum_{i} x[i][j][k] == demand[j][k]`.

### Step 4 - Add Arc Capacity Constraints
- For each origin-destination pair `(i, j)`, add a linear inequality constraint: `sum_{k} x[i][j][k] <= capacity[i][j]`.

### Step 5 - Define Linear Cost Objective
- Formulate the objective as `sum_{i} sum_{j} sum_{k} cost[i][j][k] * x[i][j][k]`.
- Set the solver's objective to minimize this expression.

### Formulation Template
```json
{
  "sets": [
    "origins",
    "destinations",
    "products"
  ],
  "parameters": [
    "supply[origin][product]",
    "demand[destination][product]",
    "cost[origin][destination][product]",
    "capacity[origin][destination]"
  ],
  "decision_variables": [
    "x[origin][destination][product] >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{o in origins} sum_{d in destinations} sum_{p in products} cost[o][d][p] * x[o][d][p]"
  },
  "constraints": [
    "supply[o][p] == sum_{d in destinations} x[o][d][p] for all o in origins, p in products",
    "demand[d][p] == sum_{o in origins} x[o][d][p] for all d in destinations, p in products",
    "sum_{p in products} x[o][d][p] <= capacity[o][d] for all o in origins, d in destinations"
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand for each product before solving, which can lead to infeasibility.
- Using integer variable types unnecessarily, which increases solve time for problems where fractional flows are acceptable.
- Mismatching indices in nested loops when building constraints, causing incorrect model logic.

## Solving stage

### Strategy Overview
Solve the constructed model using the GLOP linear solver (for continuous LPs) or the CBC mixed-integer solver (for MIPs). Implement systematic status checking and solution validation.

### Step 1 - Select and Configure Solver
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('GLOP')` for linear problems.
- For MIPs, use `'CBC'` and optionally set time limits or tolerances via `solver.SetTimeLimit()` or `solver.SetNumThreads()`.

### Step 2 - Solve and Check Status
- Execute `status = solver.Solve()`.
- Check if `status == pywraplp.Solver.OPTIMAL`. If not, handle `FEASIBLE`, `INFEASIBLE`, or `UNBOUNDED` statuses with appropriate error messages.

### Step 3 - Extract and Validate Solution
- If optimal, retrieve the objective value: `solver.Objective().Value()`.
- Iterate over variables `x[i][j][k]` and extract their `.solution_value()`.
- Programmatically recompute sums for supply, demand, and capacity constraints to verify satisfaction within a small tolerance (e.g., 1e-6).

### Step 4 - Report Results
- Print a summary of non-zero flows (e.g., flows > 1e-6).
- Output the total cost and a confirmation of constraint satisfaction.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation code)
# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL:
    print(f'Optimal cost: {solver.Objective().Value()}')
    # Extract and validate solution
    for i in range(num_origins):
        for j in range(num_destinations):
            for k in range(num_products):
                flow_val = x[i][j][k].solution_value()
                if flow_val > 1e-6:
                    print(f'Flow {i},{j},{k}: {flow_val}')
else:
    print(f'Solver did not find optimal solution. Status: {status}')
```

### Common Pitfalls
- Assuming the solver status is `OPTIMAL` without checking, leading to errors when accessing solution values from an infeasible model.
- Not using a tolerance when checking floating-point equality in constraint verification, causing false failures.
- Omitting solver output during debugging, making it difficult to diagnose presolve reductions or iteration issues.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo's `ConcreteModel` and `Set` objects. This approach is highly readable, separates model logic from data, and integrates seamlessly with advanced solvers like HiGHS or CBC.

### Step 1 - Define Abstract Sets
- Create Pyomo `Set` objects for `model.origins`, `model.destinations`, and `model.products` to manage indices cleanly.

### Step 2 - Define Parameters
- Use `Param` objects initialized with nested dictionaries for `model.supply`, `model.demand`, `model.cost`, and `model.capacity`. This enforces a clear data structure.

### Step 3 - Define Decision Variables
- Declare a three-dimensional `Var` object `model.x`, indexed over `origins * destinations * products`, with domain `NonNegativeReals` (or `NonNegativeIntegers` for MIP).

### Step 4 - Construct Constraints via Rules
- Define a rule for the supply constraint that returns `sum(model.x[o,d,p] for d in model.destinations) == model.supply[o,p]` for each `(o,p)`.
- Define a rule for the demand constraint similarly.
- Define a rule for the capacity constraint: `sum(model.x[o,d,p] for p in model.products) <= model.capacity[o,d]` for each `(o,d)`.

### Step 5 - Define Objective Function
- Use a `Objective` rule that returns `sum(model.cost[o,d,p] * model.x[o,d,p] for o,d,p in model.origins * model.destinations * model.products)` and set `sense=minimize`.

### Formulation Template
```json
{
  "sets": [
    "origins",
    "destinations",
    "products"
  ],
  "parameters": [
    "supply[origin, product]",
    "demand[destination, product]",
    "cost[origin, destination, product]",
    "capacity[origin, destination]"
  ],
  "decision_variables": [
    "x[origin, destination, product] in NonNegativeReals"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[o,d,p] * x[o,d,p] for o,d,p in origins*destinations*products)"
  },
  "constraints": [
    "supply_constr[o,p]: sum(x[o,d,p] for d in destinations) == supply[o,p]",
    "demand_constr[d,p]: sum(x[o,d,p] for o in origins) == demand[d,p]",
    "capacity_constr[o,d]: sum(x[o,d,p] for p in products) <= capacity[o,d]"
  ]
}
```

### Common Pitfalls
- Defining constraint rules with incorrect indexing, leading to `KeyError` or missing constraints.
- Not initializing `Param` objects with complete data, causing silent failures during model instantiation.
- Using `model.x.index_set()` incorrectly when the variable is multi-dimensional.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS (LP) or CBC (MIP) solver via the `SolverFactory`. Leverage Pyomo's status checking and solution inspection capabilities for robust results.

### Step 1 - Instantiate and Configure Solver
- Create solver: `solver = SolverFactory('appsi_highs')` for HiGHS or `solver = SolverFactory('cbc')`.
- Set solver options like time limit (`solver.options['time_limit'] = 30`) or optimality tolerance if needed.

### Step 2 - Solve and Check Termination Conditions
- Execute `results = solver.solve(model, tee=False)`.
- Check both the solver status (`results.solver.status == SolverStatus.ok`) and the termination condition (`results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`).

### Step 3 - Extract and Verify Solution
- If successful, access the objective value via `pyo.value(model.obj)`.
- Iterate over `model.x` to get variable values using `pyo.value(model.x[o,d,p])`.
- Programmatically verify all constraints by recomputing sums and comparing to parameters with a tolerance.

### Step 4 - Handle Infeasibility
- If the model is infeasible, implement diagnostic checks (e.g., verify supply-demand balance per product, check if any `max(supply[o,p]) > capacity[o,d]`).
- Report a structured error message for downstream processing.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.origins = pyo.Set(initialize=origins_list)
# ... (parameter, variable, constraint, objective definition)
# solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs')
results = solver.solve(model)
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    print(f'Optimal cost: {pyo.value(model.obj)}')
    # Extract and validate solution
    for o in model.origins:
        for d in model.destinations:
            for p in model.products:
                val = pyo.value(model.x[o,d,p])
                if val > 1e-6:
                    print(f'Flow {o},{d},{p}: {val}')
else:
    print(f'Solve failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}')
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran normally) with `TerminationCondition.optimal` (found optimal solution).
- Not using `pyo.value()` to extract numeric values from Pyomo components, leading to symbolic expression objects.
- Forgetting to pass the `model` instance to `solver.solve()`.
