---
name: Multi-Resource Integer Allocation
description: |
  Model and solve integer linear programs for allocating products across shared resources to maximize linear profit, using incidence matrices for constraint formulation and verifying solution feasibility.

---

# Workflow 1 (OR-Tools / SCIP-CBC)

## Modeling stage

### Strategy Overview
Formulate the problem as an Integer Linear Program (ILP) using the OR-Tools wrapper. Define integer decision variables with built-in bounds, use a binary incidence matrix to map product-resource consumption, and construct linear constraints and objective directly via the solver's API.

### Step 1 - Define Data Structures
- Create sets for products and resources (e.g., `products`, `resources`).
- Store parameters: revenue per product, demand limit per product, capacity per resource.
- Construct a binary incidence matrix `usage[resource][product]` where 1 indicates the product consumes the resource.

### Step 2 - Initialize Solver and Variables
- Instantiate the solver (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Create integer decision variables using `solver.IntVar(lower_bound, upper_bound, name)`. Set the upper bound directly to the product's demand limit to enforce demand constraints without separate equations.

### Step 3 - Formulate Capacity Constraints
- For each resource, create a linear constraint using `solver.Constraint(lower_bound, upper_bound)`.
- Iterate over all products; for each product, if `usage[resource][product] == 1`, add the variable to the constraint with a coefficient of 1 using `SetCoefficient`. This represents a knapsack constraint per resource.

### Step 4 - Define the Objective Function
- Create the objective object using `solver.Objective()`.
- For each product, set its coefficient to its revenue value using `SetCoefficient`.
- Set the objective sense to maximization.

### Formulation Template
```json
{
  "sets": ["products", "resources"],
  "parameters": [
    {"name": "revenue", "index": "products", "type": "float"},
    {"name": "demand_limit", "index": "products", "type": "int"},
    {"name": "capacity", "index": "resources", "type": "int"},
    {"name": "usage", "index": ["resources", "products"], "type": "binary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "products", "type": "integer", "bounds": "[0, demand_limit[p]]"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[p] * x[p] for p in products)"
  },
  "constraints": [
    {"name": "capacity_constraint", "index": "resources", "expression": "sum(usage[r][p] * x[p] for p in products) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Forgetting to populate the incidence matrix correctly, leading to incorrect or missing constraints.
- Setting variable bounds incorrectly (e.g., using float for demand limit instead of integer).
- Not using `SetCoefficient` for all variables in a constraint, which defaults their coefficient to zero.

## Solving stage

### Strategy Overview
Configure the solver with performance parameters, execute the solve, and rigorously verify the solution's feasibility and optimality by checking solver status and calculating actual resource usage.

### Step 1 - Configure Solver
- Set a time limit (e.g., `solver.SetTimeLimit(30000)` in milliseconds).
- Set the number of threads for parallel processing (e.g., `solver.SetNumThreads(4)`).
- Optionally, set other parameters like relative gap if using a MIP solver.

### Step 2 - Solve and Check Status
- Execute `solver.Solve()`.
- Check if the returned status is `OPTIMAL` or `FEASIBLE`. If not, handle the failure (e.g., log error, return empty result).

### Step 3 - Extract and Validate Solution
- Extract variable values using `.solution_value()`.
- Perform post-solution validation: recalculate total consumption for each resource using the incidence matrix and compare against capacities to ensure constraints are satisfied.
- Compute slack for each capacity constraint to identify binding constraints.

### Step 4 - Output and Analysis
- Output the objective value and the solution vector.
- If the solution sells all products at their demand limit, verify that no capacity constraint is violated to confirm trivial optimality.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

x = [solver.IntVar(0, demand[p], f"x_{p}") for p in products]

for r in resources:
    constraint = solver.Constraint(0, capacity[r])
    for p in products:
        if usage[r][p] == 1:
            constraint.SetCoefficient(x[p], 1)

objective = solver.Objective()
for p in products:
    objective.SetCoefficient(x[p], revenue[p])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    solution = [x[p].solution_value() for p in products]
    # Validation loop
    for r in resources:
        used = sum(usage[r][p] * solution[p] for p in products)
        print(f"Resource {r}: Used {used} / Capacity {capacity[r]}")
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Assuming a `FEASIBLE` status implies optimality; it only guarantees feasibility.
- Not verifying the solution against original constraints, especially when the solver might have numerical tolerances.
- Extracting variable values without checking the solver status first, which can lead to errors.

# Workflow 2 (Pyomo / Highs-CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model paradigm. Define sets and parameters clearly, use `pyo.Var` with `domain=pyo.NonNegativeIntegers` for decision variables, and formulate constraints using rule functions or direct expressions for clarity and maintainability.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for indexing (e.g., `model.P`, `model.R`).
- Declare `Param` objects for all input data (revenue, demand_limit, capacity, usage matrix). This separates data from model logic.

### Step 2 - Define Decision Variables
- Create a variable indexed by products using `model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers, bounds=(0, model.demand_limit))`. This enforces non-negativity and demand limits.

### Step 3 - Formulate Constraints via Rules
- Create a demand constraint rule (if not embedded in variable bounds) to enforce `model.x[p] <= model.demand_limit[p]`.
- Create a capacity constraint rule for each resource: `sum(model.usage[r,p] * model.x[p] for p in model.P) <= model.capacity[r]`. Use the binary `usage` parameter.

### Step 4 - Define the Objective
- Define the objective expression as `sum(model.revenue[p] * model.x[p] for p in model.P)`.
- Set the sense to maximize using `sense=pyo.maximize`.

### Formulation Template
```json
{
  "sets": ["P", "R"],
  "parameters": [
    {"name": "revenue", "index": "P", "type": "float"},
    {"name": "demand_limit", "index": "P", "type": "int"},
    {"name": "capacity", "index": "R", "type": "int"},
    {"name": "usage", "index": ["R", "P"], "type": "binary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "P", "type": "integer", "domain": "NonNegativeIntegers", "bounds": "(0, demand_limit)"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[p] * x[p] for p in P)"
  },
  "constraints": [
    {"name": "DemandBound", "index": "P", "expression": "x[p] <= demand_limit[p]"},
    {"name": "Capacity", "index": "R", "expression": "sum(usage[r,p] * x[p] for p in P) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's `ConcreteModel` and `AbstractModel` paradigms during instantiation.
- Incorrectly indexing parameters or variables within constraint rules, leading to `KeyError`.
- Not initializing all parameters before creating the model instance, causing build errors.

## Solving stage

### Strategy Overview
Instantiate a solver via `SolverFactory`, configure it with time limits and optimality gaps, solve the model, and perform a two-tier check on both the solver status and termination condition before extracting and validating results.

### Step 1 - Instantiate and Configure Solver
- Create a solver object (e.g., `solver = pyo.SolverFactory('highs')`).
- Set solver options: `time_limit=30`, `mip_rel_gap=0.0` (for optimality), `threads=4`.

### Step 2 - Solve and Check Termination
- Execute `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `.feasible`.

### Step 3 - Extract Solution and Verify
- Load solution into the model using `model.solutions.load_from(results)`.
- Extract variable values via `pyo.value(model.x[p])`.
- Perform post-solution validation by recalculating resource usage and comparing to capacities.

### Step 4 - Output Structured Results
- Print the objective value and key solution metrics.
- Output a structured summary (e.g., JSON) including variable values, constraint slacks, and solver statistics.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=products)
model.R = pyo.Set(initialize=resources)

model.revenue = pyo.Param(model.P, initialize=revenue_data)
model.demand_limit = pyo.Param(model.P, initialize=demand_data)
model.capacity = pyo.Param(model.R, initialize=capacity_data)
model.usage = pyo.Param(model.R, model.P, initialize=usage_data)

model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers, bounds=lambda m, p: (0, m.demand_limit[p]))

def capacity_rule(m, r):
    return sum(m.usage[r, p] * m.x[p] for p in m.P) <= m.capacity[r]
model.Capacity = pyo.Constraint(model.R, rule=capacity_rule)

model.obj = pyo.Objective(expr=sum(model.revenue[p] * model.x[p] for p in model.P), sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1.0  # Disable early termination
solver.options['threads'] = 4

results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    # Extract and validate
    solution = {p: pyo.value(model.x[p]) for p in model.P}
    for r in model.R:
        used = sum(model.usage[r, p] * solution[p] for p in model.P)
        print(f"Resource {r}: Used {used} / Capacity {pyo.value(model.capacity[r])}")
else:
    print("Solver failed.", results.solver)
```

### Common Pitfalls
- Checking only `termination_condition` without verifying `solver.status` is `ok`.
- Not using `pyo.value()` to extract parameter values during validation, leading to type errors.
- Forgetting to set `tee=True` during debugging, missing valuable solver output.
