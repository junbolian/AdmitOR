---
name: Multi-Commodity Assignment with Capacity-Weighted Demand
description: |
  Model and solve integer assignment problems where heterogeneous resources with limited availability must meet demand via capacity-weighted contributions, minimizing total cost.
---

# Workflow 1 (OR-Tools MIP Backend)

## Modeling stage

### Strategy Overview
Formulate the problem as an Integer Linear Program (ILP) using the OR-Tools linear solver wrapper. This approach leverages a direct, imperative API for building constraints and is well-suited for rapid prototyping and integration into larger systems.

### Step 1 - Define Data Structures
- Organize input data into Python dictionaries or lists for efficient access. Use `resources` and `demands` as index sets.
- Store parameters `availability[resource]`, `demand[demand]`, `capacity[resource][demand]`, and `cost[resource][demand]`.

### Step 2 - Instantiate Solver and Variables
- Create a MIP solver instance (e.g., SCIP, CBC) using `pywraplp.Solver.CreateSolver()`.
- Define integer decision variables `x[resource, demand]` with `solver.IntVar(lb, ub, name)` to represent assignment counts.

### Step 3 - Formulate Capacity-Weighted Demand Constraints
- For each demand point `j`, add a constraint ensuring the sum of capacity-weighted assignments meets demand: `solver.Add(sum(capacity[i][j] * x[i,j] for i in resources) >= demand[j])`.

### Step 4 - Formulate Resource Availability Constraints
- For each resource type `i`, add a constraint limiting total assignments: `solver.Add(sum(x[i,j] for j in demands) <= availability[i])`.

### Step 5 - Set Cost Minimization Objective
- Define the objective function as the sum of assignment costs: `solver.Minimize(sum(cost[i][j] * x[i,j] for i in resources for j in demands))`.

### Formulation Template
```json
{
  "sets": ["resources", "demands"],
  "parameters": {
    "availability": {"type": "dict", "keys": "resources"},
    "demand": {"type": "dict", "keys": "demands"},
    "capacity": {"type": "dict", "keys": ["resources", "demands"]},
    "cost": {"type": "dict", "keys": ["resources", "demands"]}
  },
  "decision_variables": [
    {"name": "x", "indices": ["resources", "demands"], "type": "integer", "domain": "non_negative"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i,j] for i in resources for j in demands)"
  },
  "constraints": [
    {"name": "demand_coverage", "for_each": "j in demands", "expression": "sum(capacity[i][j] * x[i,j] for i in resources) >= demand[j]"},
    {"name": "resource_limit", "for_each": "i in resources", "expression": "sum(x[i,j] for j in demands) <= availability[i]"}
  ]
}
```

### Common Pitfalls
- Forgetting to set variable bounds, leading to unbounded variables; always specify `lb=0`.
- Using floating-point equality in constraints; use `>=` or `<=` for demand and capacity.
- Not verifying that the sum of maximum possible capacity (`availability[i] * capacity[i,j]`) can meet demand, which can lead to infeasibility.

## Solving stage

### Strategy Overview
Solve the model using the configured OR-Tools MIP backend, focusing on performance tuning, robust solution status checking, and systematic result extraction.

### Step 1 - Configure Solver Parameters
- Set a time limit with `solver.SetTimeLimit(ms)` to prevent excessive runtime.
- Enable parallel processing with `solver.SetNumThreads(n)` for larger instances.
- Optionally set relative MIP gap with `solver.SetRelativeGap(tolerance)` if a non-zero gap is acceptable.

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve()` and capture the result status.
- Check for optimal or feasible status using `status in (solver.OPTIMAL, solver.FEASIBLE)`. Handle `solver.INFEASIBLE` or `solver.UNBOUNDED` with appropriate error messages.

### Step 3 - Extract and Validate Solution
- If feasible, retrieve the objective value via `solver.Objective().Value()`.
- Iterate through decision variables, collecting those with `x.solution_value() > tolerance` to identify active assignments.
- Post-solve, recompute total resource usage and demand coverage from the solution to validate constraint satisfaction.

### Step 4 - Report Standardized Output
- Print or return a structured result containing the objective value, assignment list, resource utilization rates, and demand coverage percentages.
- Format key results (e.g., `RESULT:{objective_value}`) for automated parsing.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (variable and constraint creation as per modeling stage)
solver.Minimize(objective_expr)

# solve with status / termination checks
solver.SetTimeLimit(30000)  # 30 seconds
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    assignments = []
    for i in resources:
        for j in demands:
            val = x[i,j].solution_value()
            if val > 1e-6:
                assignments.append(((i,j), val))
    # ... validation and reporting
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking for `FEASIBLE` status, missing valid but non-optimal solutions.
- Extracting variable values without checking the solver status first, leading to errors.
- Omitting post-solution validation, which can miss subtle constraint violations due to numerical tolerances.

# Workflow 2 (Pyomo with High-Level Solver Interface)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo, defining abstract sets and parameters. This approach separates model logic from data, enhancing reusability and clarity, and interfaces seamlessly with numerous solvers via the `SolverFactory`.

### Step 1 - Define Abstract Sets and Parameters
- Use `pyo.Set()` to create index sets for `resources` and `demands`.
- Declare parameters (`availability`, `demand`, `capacity`, `cost`) using `pyo.Param(set, initialize=dict)` for scalar and matrix data.

### Step 2 - Declare Integer Decision Variables
- Define the assignment variable `model.x` as `pyo.Var(model.resources, model.demands, within=pyo.NonNegativeIntegers)`.

### Step 3 - Build Constraints Using Rule Functions
- Implement a rule function for demand coverage: for each `j` in `model.demands`, return `sum(model.capacity[i,j] * model.x[i,j] for i in model.resources) >= model.demand[j]`.
- Implement a rule for resource limits: for each `i` in `model.resources`, return `sum(model.x[i,j] for j in model.demands) <= model.availability[i]`.
- Add constraints to the model using `pyo.Constraint(model.demands, rule=demand_rule)`.

### Step 4 - Define the Objective Function
- Create the objective to minimize total cost: `model.obj = pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for i in model.resources for j in model.demands), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["model.resources", "model.demands"],
  "parameters": [
    {"name": "availability", "index": "model.resources"},
    {"name": "demand", "index": "model.demands"},
    {"name": "capacity", "index": ["model.resources", "model.demands"]},
    {"name": "cost", "index": ["model.resources", "model.demands"]}
  ],
  "decision_variables": [
    {"name": "x", "indices": ["model.resources", "model.demands"], "type": "pyo.NonNegativeIntegers"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[i,j] * model.x[i,j] for i in model.resources for j in model.demands)"
  },
  "constraints": [
    {"name": "demand_coverage", "rule": "for j in model.demands: sum(model.capacity[i,j] * model.x[i,j] for i in model.resources) >= model.demand[j]"},
    {"name": "resource_limit", "rule": "for i in model.resources: sum(model.x[i,j] for j in model.demands) <= model.availability[i]"}
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters within rule functions; ensure indices match the constraint's indexing set.
- Forgetting to initialize all parameters, which leads to runtime errors when the model is instantiated.
- Using mutable objects (like lists) for set initialization; prefer tuples or explicit `initialize` calls.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., CBC, HiGHS), configure it for performance, and implement robust checks for solution status and termination condition before extracting results.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object with `pyo.SolverFactory("cbc")`.
- Configure key options: `time_limit`, `ratio` (for MIP gap), `threads`, and `presolve`.

### Step 2 - Execute Solve with Error Handling
- Call `solver.solve(model, options=...)` within a try-except block to catch common exceptions.
- Store the result object for status inspection.

### Step 3 - Verify Solution Status and Termination
- Check `model.solutions[0].status == pyo.SolverStatus.ok` and `model.solutions[0].termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}`.
- If status is not ok or termination is not acceptable, return a structured failure report.

### Step 4 - Extract, Validate, and Report Results
- If successful, compute the objective value via `pyo.value(model.obj)`.
- Iterate through `model.x` to extract non-zero assignments (`if pyo.value(model.x[i,j]) > tolerance`).
- Compute derived metrics (resource utilization, demand coverage) for validation.
- Output results in a consistent format, such as a dictionary with keys `objective`, `assignments`, `utilization`.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.resources = pyo.Set(initialize=resources_list)
# ... (parameter and variable definition as per modeling stage)
model.obj = pyo.Objective(expr=objective_expr, sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
results = solver.solve(model, options={"seconds": 30, "ratio": 0.0})

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    obj_val = pyo.value(model.obj)
    # ... extraction and reporting
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus` with `TerminationCondition`; both must be checked for a complete status assessment.
- Accessing variable values directly without first ensuring the model instance contains the solution (`model.solutions`).
- Not setting a time limit or MIP gap, potentially causing the solver to run indefinitely on difficult instances.
