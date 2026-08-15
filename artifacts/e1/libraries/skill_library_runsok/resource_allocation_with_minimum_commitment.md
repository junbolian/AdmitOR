---
name: Resource Allocation with Minimum Commitment
description: |
  Model and solve allocation problems with minimum delivery thresholds and contributor requirements using mixed-integer linear programming.
---

# Workflow 1 (OR-Tools / SCIP)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Linear Program (MILP) using the OR-Tools Python library. It employs a direct, low-level API for creating variables and constraints, suitable for performance-critical applications and integration into larger systems.

### Step 1 - Define Data Structures
- Organize problem data into indexed lists or dictionaries for sources (`i`), destinations (`j`), capacities, demands, minimum delivery thresholds, and cost matrices.
- Use tuple keys `(i, j)` for efficient access to cost and variable data.

### Step 2 - Create Decision Variables
- Create continuous allocation variables `x[i, j]` with lower bound 0 and no upper bound (or a large number).
- Create binary activation variables `y[i, j]` to indicate if source `i` supplies destination `j`.
- Use `solver.NumVar` and `solver.BoolVar` for variable creation.

### Step 3 - Implement Core Constraints
- **Capacity Limits**: For each source `i`, `sum(x[i, j] for j) <= capacity[i]`.
- **Demand Satisfaction**: For each destination `j`, `sum(x[i, j] for i) >= demand[j]`.
- **Minimum Contributors**: For each destination `j`, `sum(y[i, j] for i) >= K`, where `K` is the required minimum number of sources.
- **Minimum Delivery & Activation Link**: For each `(i, j)` pair, add two constraints: `x[i, j] >= min_delivery[i] * y[i, j]` and `x[i, j] <= capacity[i] * y[i, j]`.

### Step 4 - Formulate Objective
- Define a linear cost minimization objective: `minimize sum(cost[i][j] * x[i, j] for all i, j)`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    "capacity[sources]",
    "demand[destinations]",
    "min_delivery[sources]",
    "cost[sources, destinations]",
    "min_contributors"
  ],
  "decision_variables": [
    "x[sources, destinations] (continuous, >=0)",
    "y[sources, destinations] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in sources, j in destinations)"
  },
  "constraints": [
    "capacity_limit[i]: sum(x[i][j] for j in destinations) <= capacity[i]",
    "demand_satisfaction[j]: sum(x[i][j] for i in sources) >= demand[j]",
    "min_contributors[j]: sum(y[i][j] for i in sources) >= min_contributors",
    "min_delivery_lower[i,j]: x[i][j] >= min_delivery[i] * y[i][j]",
    "activation_upper[i,j]: x[i][j] <= capacity[i] * y[i][j]"
  ]
}
```

### Common Pitfalls
- Using Python's built-in `sum()` inside constraint construction, which is inefficient for large models; use `solver.Sum()` instead.
- Forgetting to link the binary variable `y` to the continuous variable `x` with both upper and lower bounds, leading to incorrect activation logic.
- Setting an overly tight optimality gap or time limit that prevents finding a feasible solution for tightly constrained instances.

## Solving stage

### Strategy Overview
This stage focuses on solving the MILP using the SCIP solver via OR-Tools, with emphasis on configuration, solution verification, and robust result extraction.

### Step 1 - Configure Solver and Parameters
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set performance parameters: `solver.SetTimeLimit(time_limit_ms)`, `solver.SetNumThreads(num_threads)`.
- Set optimality tolerance: Access solver parameters to set a relative MIP gap (e.g., `1e-4`).

### Step 2 - Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `if status == pywraplp.Solver.OPTIMAL:` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses appropriately.

### Step 3 - Extract and Verify Solution
- Extract variable values using `.solution_value()`.
- Implement a post-solve verification function that checks all constraints (capacity, demand, minimum contributors, minimum delivery) against the solution values with a numerical tolerance.
- Calculate and report key metrics: total cost, source utilization, destination contributor counts.

### Step 4 - Report Results
- Generate a structured output summarizing allocations, activations, constraint satisfaction, and solver statistics.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (variable and constraint creation)
solver.Minimize(objective_expr)

# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL or status == solver.FEASIBLE:
    # Extract solution
    for i in sources:
        for j in destinations:
            x_val = x[i, j].solution_value()
            y_val = y[i, j].solution_value()
    # Call verification function
    verify_solution(x_vals, y_vals, data, tolerance=1e-6)
    print(f"Total cost: {solver.Objective().Value()}")
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Not verifying the solution post-solve, leading to acceptance of numerically infeasible results.
- Misinterpreting the solver status (e.g., treating `FEASIBLE` as `OPTIMAL` without noting the difference in solution quality).
- Failing to handle solver errors or timeouts gracefully, causing the application to crash.

# Workflow 2 (Pyomo / HiGHS or Gurobi)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to formulate the MILP. It emphasizes readability, maintainability, and solver-agnostic code, allowing easy switching between solvers like HiGHS (open-source) and Gurobi (commercial).

### Step 1 - Define Abstract Sets and Parameters
- Use `pyo.Set()` to define sets for sources and destinations.
- Use `pyo.Param()` to define all input data (capacity, demand, min_delivery, cost, min_contributors), potentially indexed over the defined sets.

### Step 2 - Declare Decision Variables
- Declare a continuous variable `model.x` indexed over source-destination pairs with a lower bound of 0.
- Declare a binary variable `model.y` indexed over the same pairs.

### Step 3 - Construct Constraints as Rules
- Define constraint rules using Pyomo's `pyo.Constraint` and `rule` argument. This promotes modularity.
- Create rules for capacity limits, demand satisfaction, minimum contributors, and the minimum delivery/activation linking constraints.

### Step 4 - Define the Objective Function
- Define the objective using `pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for ...), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["model.sources", "model.destinations"],
  "parameters": [
    "model.capacity[model.sources]",
    "model.demand[model.destinations]",
    "model.min_delivery[model.sources]",
    "model.cost[model.sources, model.destinations]",
    "model.min_contributors"
  ],
  "decision_variables": [
    "model.x[model.sources, model.destinations] (continuous, >=0)",
    "model.y[model.sources, model.destinations] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[i,j] * model.x[i,j] for i in model.sources, j in model.destinations)"
  },
  "constraints": [
    "model.capacity_con[i]: sum(model.x[i,j] for j in model.destinations) <= model.capacity[i]",
    "model.demand_con[j]: sum(model.x[i,j] for i in model.sources) >= model.demand[j]",
    "model.contributors_con[j]: sum(model.y[i,j] for i in model.sources) >= model.min_contributors",
    "model.min_delivery_con[i,j]: model.x[i,j] >= model.min_delivery[i] * model.y[i,j]",
    "model.activation_con[i,j]: model.x[i,j] <= model.capacity[i] * model.y[i,j]"
  ]
}
```

### Common Pitfalls
- Creating a `ConcreteModel` and trying to use `rule` functions that reference external data without proper scoping; ensure all data is attached to the model as `Param` objects.
- Using overly complex Python logic inside constraint rules, which can slow down model construction. Keep rules simple and vectorized where possible.
- Not initializing parameters before solving, leading to errors when the solver attempts to evaluate expressions.

## Solving stage

### Strategy Overview
This stage involves solving the Pyomo model using a chosen solver backend (e.g., HiGHS or Gurobi), with a focus on solver configuration, robust status checking, and solution validation.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory("highs")` or `SolverFactory("gurobi")`.
- Set solver-specific options: `solver.options["time_limit"] = time_limit`, `solver.options["mip_rel_gap"] = tolerance`. For Gurobi, options like `Threads`, `Seed`, and `MIPGap` are common.

### Step 2 - Solve and Inspect Results
- Call `results = solver.solve(model, tee=True)` to solve and optionally print solver log.
- Check the high-level status: `if results.solver.status == pyo.SolverStatus.ok:`.
- Check the termination condition: `if results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:`.

### Step 3 - Extract and Validate Solution
- Extract variable values using `pyo.value(model.x[i, j])` and `pyo.value(model.y[i, j])`.
- Filter allocations below a small tolerance (e.g., `1e-6`) to account for numerical noise.
- Programmatically verify all constraints against the extracted solution to ensure feasibility.

### Step 4 - Generate Structured Output
- Summarize the solution, including total cost (`pyo.value(model.obj)`), detailed allocations, active contributors per destination, and source utilization rates.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, params, variables, constraints, objective)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")  # or "gurobi"
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 1e-4

results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    # Extract and process solution
    allocations = {(i,j): pyo.value(model.x[i,j]) for i in model.sources for j in model.destinations}
    # Call verification function
    verify_solution(allocations, model, tolerance=1e-6)
else:
    print(f"Solver failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (the solver ran) with `TerminationCondition.optimal` (it found an optimal solution); both must be checked.
- Not using `pyo.value()` to extract variable values, leading to references to the variable object instead of its numerical solution.
- Setting incompatible solver options (e.g., a HiGHS-specific option for Gurobi), which causes the solver to fail or be ignored.
