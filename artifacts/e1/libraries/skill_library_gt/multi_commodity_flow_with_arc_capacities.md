---
name: Multi-Commodity Flow with Arc Capacities
description: |
  Model and solve multi-commodity transportation problems with shared arc capacities, using systematic constraint implementation and robust solver configuration.
---

# Workflow 1 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
Model the problem as a multi-commodity flow network using Google OR-Tools' linear solver API. Define flow variables indexed by source, destination, and product. Implement supply, demand, and capacity constraints via explicit coefficient loops.

### Step 1 - Define Sets and Parameters
- Organize data as Python lists or dictionaries with zero-based indexing for sources, destinations, and products.
- Store supply, demand, capacity, and cost parameters in nested structures (e.g., `supply[source][product]`, `capacity[source][destination]`).

### Step 2 - Create Decision Variables
- Instantiate a continuous linear solver (e.g., `pywraplp.Solver.CreateSolver('GLOP')`).
- Create non-negative flow variables `x[source][destination][product]` using `solver.NumVar(0, solver.infinity(), 'x_s_d_p')`.

### Step 3 - Build Supply Constraints
- For each source and product, create a constraint with upper bound `supply[source][product]`.
- Loop over all destinations and set coefficient `1` for each variable `x[source][destination][product]`.

### Step 4 - Build Demand Constraints
- For each destination and product, create an equality constraint with right-hand side `demand[destination][product]`.
- Loop over all sources and set coefficient `1` for each variable `x[source][destination][product]`.

### Step 5 - Build Arc Capacity Constraints
- For each source-destination pair, create a constraint with upper bound `capacity[source][destination]`.
- Loop over all products and set coefficient `1` for each variable `x[source][destination][product]`.

### Step 6 - Define Linear Objective
- Create the objective expression by summing `cost[source][destination][product] * x[source][destination][product]` over all indices.
- Set the solver objective to minimize this sum.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "products"],
  "parameters": [
    "supply[sources][products]",
    "demand[destinations][products]",
    "capacity[sources][destinations]",
    "cost[sources][destinations][products]"
  ],
  "decision_variables": ["x[sources][destinations][products] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s][d][p] * x[s][d][p] for s, d, p)"
  },
  "constraints": [
    "sum(x[s][d][p] for d in destinations) <= supply[s][p] for all s, p",
    "sum(x[s][d][p] for s in sources) == demand[d][p] for all d, p",
    "sum(x[s][d][p] for p in products) <= capacity[s][d] for all s, d"
  ]
}
```

### Common Pitfalls
- Using one-based indexing when data structures are zero-based, causing index errors.
- Forgetting to aggregate flows across products in the arc capacity constraint.
- Not verifying total supply >= total demand per product before solving, which can lead to infeasibility.

## Solving stage

### Strategy Overview
Solve the linear program using OR-Tools' wrapper, configure solver parameters for reliability, and implement comprehensive solution validation with tolerance checks.

### Step 1 - Configure and Solve
- Call `solver.Solve()` to execute the optimization.
- For larger problems, set a time limit using `solver.SetTimeLimit(limit_in_milliseconds)`.

### Step 2 - Check Solver Status
- Verify the solve status: `status == pywraplp.Solver.OPTIMAL` or `FEASIBLE`.
- If status is not optimal/feasible, log the status code and investigate infeasibility.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value via `solver.Objective().Value()`.
- For each variable, get the solution value with `x_var.solution_value()`.
- Programmatically check all constraints with a tolerance (e.g., 1e-6) to confirm feasibility.

### Step 4 - Output Standardized Results
- For a successful solve, print the result in the format: `RESULT:{objective_value}`.
- For debugging, output a detailed summary of non-zero flows and constraint satisfaction.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... variable and constraint creation ...

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    # Validate solution
    for s in sources:
        for p in products:
            total_shipped = sum(x[s, d, p].solution_value() for d in destinations)
            assert total_shipped <= supply[s][p] + 1e-6, "Supply violation"
    # Output result
    print(f"RESULT:{objective_value}")
else:
    print(f"SOLVE_FAILED:{{'status': {status}}}")
```

### Common Pitfalls
- Assuming a feasible status means all constraints are satisfied within tolerance; always validate.
- Not handling solver timeouts, which return `FEASIBLE` or `OPTIMAL` but may not be optimal.
- Extracting variable values without checking if the solve was successful, leading to errors.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling framework. Define sets, variables, and constraints declaratively. Leverage Pyomo's integration with open-source solvers like HiGHS or CBC for solving.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo Sets for sources, destinations, and products.
- Declare Pyomo Parameters for supply, demand, capacity, and cost, indexed by the appropriate sets.

### Step 2 - Define Decision Variables
- Create a Pyomo Var `model.x` indexed by sources, destinations, and products, with domain `pyo.NonNegativeReals`.

### Step 3 - Construct Objective Function
- Define a Pyomo Objective that minimizes the sum of cost-weighted flow variables.

### Step 4 - Implement Constraints via Rules
- Create a Constraint for supply limits, indexed by source and product, using a rule that sums flows over destinations.
- Create a Constraint for demand satisfaction, indexed by destination and product, using an equality rule summing over sources.
- Create a Constraint for arc capacities, indexed by source and destination, summing flows over products.

### Formulation Template
```json
{
  "sets": ["model.SOURCES", "model.DESTS", "model.PRODS"],
  "parameters": [
    "model.supply[SOURCES, PRODS]",
    "model.demand[DESTS, PRODS]",
    "model.capacity[SOURCES, DESTS]",
    "model.cost[SOURCES, DESTS, PRODS]"
  ],
  "decision_variables": ["model.x[SOURCES, DESTS, PRODS] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[s,d,p] * model.x[s,d,p] for s,d,p)"
  },
  "constraints": [
    "sum(model.x[s,d,p] for d in DESTS) <= model.supply[s,p] for all s,p",
    "sum(model.x[s,d,p] for s in SOURCES) == model.demand[d,p] for all d,p",
    "sum(model.x[s,d,p] for p in PRODS) <= model.capacity[s,d] for all s,d"
  ]
}
```

### Common Pitfalls
- Using concrete model initialization with mismatched index orders between data and sets.
- Forgetting to deactivate the solver's presolve, which can sometimes mask modeling errors.
- Defining constraint rules that close over mutable global variables, causing incorrect references.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., HiGHS, CBC). Configure solver options for performance and reliability. Perform rigorous post-solution validation and extract results.

### Step 1 - Configure Solver and Solve
- Instantiate a solver via `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set solver options such as `time_limit`, `threads`, and `optimality_gap`.
- Call `solver.solve(model, tee=False)` to execute the optimization.

### Step 2 - Check Termination Condition
- Verify `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `.feasible`.
- If termination is not acceptable, analyze the solver log or termination message.

### Step 3 - Validate Solution and Extract Values
- Use `pyo.value(model.x[s,d,p])` to get variable values.
- Compute aggregate flows and compare against all constraints with a tolerance (e.g., 1e-6).
- Calculate key metrics like supply utilization and capacity usage for insight.

### Step 4 - Output Results
- Print the objective value in the standard format: `RESULT:{pyo.value(model.obj)}`.
- For failures, output a JSON with status, termination condition, and any error messages.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... set, parameter, variable, constraint, objective definitions ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, options={'time_limit': 30})
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    # Validate
    for s in model.SOURCES:
        for p in model.PRODS:
            total = sum(pyo.value(model.x[s,d,p]) for d in model.DESTS)
            assert total <= model.supply[s,p] + 1e-6
    # Output
    print(f"RESULT:{pyo.value(model.obj)}")
else:
    print(f"SOLVE_FAILED:{results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of suboptimal or incomplete solves.
- Assuming variable values are automatically loaded; ensure `model.solutions.load_from(results)` if needed.
- Overlooking the need to convert Pyomo numeric values to floats before comparison in validation checks.
