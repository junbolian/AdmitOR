---
name: MultiDimensionalAllocationLP
description: |
  Model and solve linear allocation problems with multiple sources, destinations, and product types using continuous decision variables, demand satisfaction constraints, and profit maximization objectives.
---

# Workflow 1 (OR-Tools / GLOP)

## Modeling stage

### Strategy Overview
Model the allocation problem as a multi-dimensional linear program using OR-Tools' `pywraplp` interface. Define variables as continuous quantities, enforce demand satisfaction via equality constraints, and maximize total profit. This workflow is suited for pure LP problems without integer requirements.

### Step 1 - Define Indices and Data Structures
- Define clear index sets for sources, destinations, and product types (e.g., `sources`, `destinations`, `products`).
- Organize input data as multi-dimensional lists or dictionaries: `profit[source][destination][product]` and `demand[destination][product]`.

### Step 2 - Create Decision Variables
- Create a three-dimensional dictionary of continuous decision variables `x[i][j][k]` using `solver.NumVar(0, solver.infinity(), name)`.
- Enforce non-negativity directly via the variable's lower bound.

### Step 3 - Formulate Demand Satisfaction Constraints
- For each destination-product pair, create an equality constraint: `solver.Constraint(demand_val, demand_val)`.
- Add contributions from all sources by setting the coefficient of each `x[i][j][k]` to 1 within the corresponding constraint.

### Step 4 - Construct Linear Objective
- Initialize the objective with `solver.Objective()`.
- Use nested loops to sum profit contributions: `objective.SetCoefficient(x[i][j][k], profit[i][j][k])`.
- Set the objective sense to maximization.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "products"],
  "parameters": [
    {"name": "profit", "dimensions": ["source", "destination", "product"], "type": "float"},
    {"name": "demand", "dimensions": ["destination", "product"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "dimensions": ["source", "destination", "product"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i][j][k] * x[i][j][k] for i in sources for j in destinations for k in products)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "sum(x[i][j][k] for i in sources) == demand[j][k]", "forall": ["j in destinations", "k in products"]}
  ]
}
```

### Common Pitfalls
- Mismatching indices between profit/demand arrays and variable loops, leading to incorrect coefficients.
- Forgetting to set the objective sense to maximization, defaulting to minimization.
- Using `solver.infinity()` without importing the correct module (`from ortools.linear_solver import pywraplp`).

## Solving stage

### Strategy Overview
Solve the constructed model using the GLOP linear solver. Implement robust status checking, extract and verify the solution, and format outputs for clarity and debugging.

### Step 1 - Initialize Solver and Solve
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver("GLOP")`.
- Call `status = solver.Solve()` to execute the optimization.

### Step 2 - Check Solver Status
- Verify the solution status is `OPTIMAL` or `FEASIBLE`: `if status in (solver.OPTIMAL, solver.FEASIBLE):`.
- If status is not acceptable, output a structured error message with the solver status code.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value: `total_profit = objective.Value()`.
- Iterate through all variables to extract non-zero allocations (`var.solution_value() > tolerance`).
- Optionally, verify demand constraints by recalculating totals from the extracted solution.

### Step 4 - Format and Output Results
- Print the total objective value in a parseable format (e.g., `RESULT:{total_profit}`).
- Output a summary of positive allocations, grouped by destination and product for readability.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
# Define indices: sources, destinations, products
# Define parameters: profit, demand
x = {}
for i in sources:
    for j in destinations:
        for k in products:
            x[i,j,k] = solver.NumVar(0, solver.infinity(), f"x_{i}_{j}_{k}")
# Demand constraints
for j in destinations:
    for k in products:
        constraint = solver.Constraint(demand[j][k], demand[j][k])
        for i in sources:
            constraint.SetCoefficient(x[i,j,k], 1)
# Objective
objective = solver.Objective()
for i in sources:
    for j in destinations:
        for k in products:
            objective.SetCoefficient(x[i,j,k], profit[i][j][k])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_profit = objective.Value()
    # Extract and print non-zero allocations
    allocations = []
    for i in sources:
        for j in destinations:
            for k in products:
                val = x[i,j,k].solution_value()
                if val > 1e-6:
                    allocations.append(((i,j,k), val))
    print(f"RESULT:{total_profit}")
    # Print allocation details...
else:
    print(f"SOLVER_FAILED:Status={status}")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing valid solutions.
- Extracting variable values without a tolerance check, printing near-zero values as significant allocations.
- Assuming the solver object persists after the solve call in certain environments; extract values immediately.

# Workflow 2 (Pyomo / HiGHS)

## Modeling stage

### Strategy Overview
Model the allocation problem using Pyomo's abstract modeling capabilities. Define sets, parameters, variables, and constraints in a structured, declarative style. This workflow emphasizes separation of model construction and solving, facilitating reuse and maintenance.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `sources`, `destinations`, `products`.
- Define `Param` objects for `profit` (indexed by source, destination, product) and `demand` (indexed by destination, product), initializing them with dictionaries.

### Step 2 - Declare Decision Variables
- Create a Pyomo `Var` object `model.x` indexed by the Cartesian product of the three sets.
- Set the domain to `pyo.NonNegativeReals` to enforce non-negativity.

### Step 3 - Implement Demand Constraints via Rules
- Define a constraint rule function that, for each destination and product, sums the allocation variables from all sources.
- Use `pyo.Constraint(model.destinations, model.products, rule=demand_rule)` to create the constraint block.

### Step 4 - Construct the Objective Expression
- Build the objective using a Pyomo `Expression` or directly within `model.obj = pyo.Objective(...)`.
- Use a sum comprehension over all indices: `sum(model.profit[c,m,p] * model.x[c,m,p] for c in model.sources for m in model.destinations for p in model.products)`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "products"],
  "parameters": [
    {"name": "profit", "dimensions": ["source", "destination", "product"], "type": "Param"},
    {"name": "demand", "dimensions": ["destination", "product"], "type": "Param"}
  ],
  "decision_variables": [
    {"name": "x", "dimensions": ["source", "destination", "product"], "type": "Var", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[c,m,p] * x[c,m,p] for c in sources for m in destinations for p in products)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "sum(x[c,m,p] for c in sources) == demand[m,p]", "forall": ["m in destinations", "p in products"], "rule_based": true}
  ]
}
```

### Common Pitfalls
- Confusing Pyomo `AbstractModel` with `ConcreteModel`; use `ConcreteModel` for immediate data initialization.
- Incorrectly nesting index tuples in parameter dictionaries; use `(c,m,p)` as keys, not `[c][m][p]`.
- Forgetting to deactivate the solver output (`tee=False`) in production, leading to verbose logs.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS LP solver via the `SolverFactory`. Configure solver options for performance, implement comprehensive status checking, and load solutions safely.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")`.
- Set practical options: `solver.options["time_limit"] = 30`, `solver.options["threads"] = 4`.
- Solve with `load_solutions=False`: `results = solver.solve(model, tee=False, load_solutions=False)`.

### Step 2 - Validate Termination Status
- Check the solver status: `if results.solver.status == pyo.SolverStatus.ok:`.
- Check the termination condition: `if results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:`.
- If checks fail, output a structured JSON error with solver details.

### Step 3 - Load and Extract Solution
- Load the solution into the model: `model.solutions.load_from(results)`.
- Extract the objective value: `total_profit = pyo.value(model.obj)`.
- Iterate through `model.x` to collect non-zero variable values (`pyo.value(model.x[c,m,p]) > tolerance`).

### Step 4 - Verify and Report Results
- Recalculate total allocation per demand point and verify against the demand parameter within a numerical tolerance.
- Print the objective value in a standard format (e.g., `RESULT:{total_profit}`).
- Output a clean summary of allocations, optionally as a dictionary or table.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=sources_list)
model.destinations = pyo.Set(initialize=destinations_list)
model.products = pyo.Set(initialize=products_list)
model.profit = pyo.Param(model.sources, model.destinations, model.products, initialize=profit_dict)
model.demand = pyo.Param(model.destinations, model.products, initialize=demand_dict)
model.x = pyo.Var(model.sources, model.destinations, model.products, domain=pyo.NonNegativeReals)
def demand_rule(m, d, p):
    return sum(m.x[s, d, p] for s in m.sources) == m.demand[d, p]
model.demand_constr = pyo.Constraint(model.destinations, model.products, rule=demand_rule)
model.obj = pyo.Objective(
    expr=sum(model.profit[s,d,p] * model.x[s,d,p] for s in model.sources for d in model.destinations for p in model.products),
    sense=pyo.maximize
)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["threads"] = 4
results = solver.solve(model, tee=False, load_solutions=False)
if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    model.solutions.load_from(results)
    total_profit = pyo.value(model.obj)
    # Extract non-zero allocations
    allocations = []
    for idx in model.x.index_set():
        val = pyo.value(model.x[idx])
        if val > 1e-6:
            allocations.append((idx, val))
    print(f"RESULT:{total_profit}")
    # Print allocation details...
else:
    import json
    error_info = {
        "status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
    print(f"SOLVER_FAILED:{json.dumps(error_info)}")
```

### Common Pitfalls
- Accessing `pyo.value(model.obj)` before loading the solution, resulting in `None` or an error.
- Using `model.x.index_set()` incorrectly if variables are defined with multiple `Set` objects; ensure correct indexing.
- Not setting a time limit, allowing the solver to run indefinitely on large instances.
