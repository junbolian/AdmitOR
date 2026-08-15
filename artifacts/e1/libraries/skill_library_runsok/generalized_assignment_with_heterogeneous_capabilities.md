---
name: Generalized Assignment with Heterogeneous Capabilities
description: |
  Model and solve resource allocation problems where integer quantities of heterogeneous resources are assigned to meet demands, minimizing linear cost, subject to resource capacity and demand coverage constraints.
---

# Workflow 1 (OR-Tools / SCIP Backend)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools (pywraplp) to formulate the integer linear program, leveraging the SCIP solver backend for efficient mixed-integer solving. It is well-suited for rapid prototyping and deployment in environments where OR-Tools is available.

### Step 1 - Define Data Structures
- Organize input data into clear dictionaries or lists for resources and demands.
- Define parameters: `availability[resource]`, `demand[demand_point]`, `capability[resource][demand_point]`, `cost[resource][demand_point]`.
- Use descriptive index names (e.g., `i` for resources, `j` for demand points).

### Step 2 - Create Integer Variables
- Instantiate a solver object: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Create non-negative integer variables `x[i][j]` representing assignment quantities.
- Set lower bound to 0 and upper bound to `solver.infinity()`.

### Step 3 - Add Resource Capacity Constraints
- For each resource `i`, add a constraint: `sum(x[i][j] for j in demand_points) <= availability[i]`.
- Use `solver.Add()` to build the linear constraint.

### Step 4 - Add Demand Coverage Constraints
- For each demand point `j`, add a constraint: `sum(capability[i][j] * x[i][j] for i in resources) >= demand[j]`.
- Ensure coefficients (`capability[i][j]`) are numeric.

### Step 5 - Set Linear Objective
- Create the objective: `solver.Minimize(sum(cost[i][j] * x[i][j] for i in resources for j in demand_points))`.
- Convert cost values to float when setting coefficients to avoid type errors.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "demand_points"
  ],
  "parameters": [
    {"name": "availability", "index": "resources", "type": "int"},
    {"name": "demand", "index": "demand_points", "type": "int"},
    {"name": "capability", "index": ["resources", "demand_points"], "type": "float"},
    {"name": "cost", "index": ["resources", "demand_points"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["resources", "demand_points"], "type": "int", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in resources for j in demand_points)"
  },
  "constraints": [
    {"name": "resource_capacity", "index": "resources", "expression": "sum(x[i][j] for j in demand_points) <= availability[i]"},
    {"name": "demand_coverage", "index": "demand_points", "expression": "sum(capability[i][j] * x[i][j] for i in resources) >= demand[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to convert integer cost values to float in the objective, causing solver errors.
- Using inconsistent indexing between parameter dictionaries and constraint loops.
- Not setting an upper bound on integer variables, which is implicitly infinite but should be considered for very large availability.

## Solving stage

### Strategy Overview
Solve the model using the configured SCIP solver via OR-Tools. Focus on robust solution status checking, result extraction, and validation of constraint satisfaction.

### Step 1 - Configure Solver
- Set a time limit: `solver.SetTimeLimit(time_limit_ms)`.
- Optionally set the number of threads: `solver.SetNumThreads(num_threads)`.

### Step 2 - Invoke Solver and Check Status
- Call `solver.Solve()`.
- Check the result status: `if status in [solver.OPTIMAL, solver.FEASIBLE]:`.
- If status is not optimal or feasible, handle as a failure and output an error payload.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value: `total_cost = solver.Objective().Value()`.
- Iterate over variables `x[i][j]` and collect values where `x[i][j].solution_value() > 0.5`.
- Recalculate total resource usage and demand coverage to verify constraints.

### Step 4 - Format Output
- Print the total cost in the required format: `print(f"RESULT:{total_cost}")`.
- Optionally, print a summary of assignments for verification.

### Code Usage
```python
import ortools.linear_solver.pywraplp as pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (create variables, add constraints, set objective as per Modeling stage)

# Solve with status / termination checks
solver.SetTimeLimit(30000)  # 30 seconds
status = solver.Solve()

if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    # Extract variable values and validate
    for i in resources:
        for j in demand_points:
            val = x[i][j].solution_value()
            if val > 0.5:
                print(f"Assign {val} of resource {i} to demand {j}")
    print(f"RESULT:{total_cost}")
else:
    print(f'RESULT_JSON:{{"status": "{status}", "error": "Solver did not find optimal/feasible solution."}}')
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good feasible solutions.
- Comparing floating-point solution values directly to 0; use a tolerance (e.g., `> 0.5` for integer variables).
- Omitting time limits for large instances, risking long runtimes.

# Workflow 2 (Pyomo / HiGHS Backend)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model formulation, separating data from model structure, and employs the HiGHS solver via the `highs` interface. It is ideal for maintainable, scalable models and integration into larger Python-based systems.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo sets: `model.resources = pyo.Set()`, `model.demand_points = pyo.Set()`.
- Declare parameters using `pyo.Param` within these sets for `availability`, `demand`, `capability`, and `cost`.

### Step 2 - Create Integer Decision Variables
- Define a Pyomo variable: `model.x = pyo.Var(model.resources, model.demand_points, domain=pyo.NonNegativeIntegers)`.
- This automatically enforces non-negativity and integrality.

### Step 3 - Define Objective Rule
- Create a rule function that returns `sum(model.cost[i, j] * model.x[i, j] for i in model.resources for j in model.demand_points)`.
- Assign it to `model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)`.

### Step 4 - Define Constraint Rules
- Create a rule for resource capacity: `sum(model.x[i, j] for j in model.demand_points) <= model.availability[i]`.
- Create a rule for demand coverage: `sum(model.capability[i, j] * model.x[i, j] for i in model.resources) >= model.demand[j]`.
- Instantiate constraints indexed by their respective sets.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "demand_points"
  ],
  "parameters": [
    {"name": "availability", "index": "resources", "type": "int"},
    {"name": "demand", "index": "demand_points", "type": "int"},
    {"name": "capability", "index": ["resources", "demand_points"], "type": "float"},
    {"name": "cost", "index": ["resources", "demand_points"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["resources", "demand_points"], "type": "int", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in resources for j in demand_points)"
  },
  "constraints": [
    {"name": "resource_capacity", "index": "resources", "expression": "sum(x[i, j] for j in demand_points) <= availability[i]"},
    {"name": "demand_coverage", "index": "demand_points", "expression": "sum(capability[i, j] * x[i, j] for i in resources) >= demand[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to initialize Pyomo parameters with data before creating the instance, leading to missing value errors.
- Using Python's built-in `sum` inside rule functions instead of Pyomo's expression builders (though `sum` works, explicit `pyo.quicksum` can be more efficient for large models).
- Mismatch between index order in parameter declarations and their usage in constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via `SolverFactory`. Leverage Pyomo's status reporting for robust solution handling and result extraction.

### Step 1 - Instantiate Model with Data
- Create a `ConcreteModel` and populate its sets and parameters with the actual data dictionaries.
- Ensure all indices in the data match the declared sets.

### Step 2 - Configure and Run Solver
- Create solver object: `solver = pyo.SolverFactory('highs')`.
- Set solver options: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0`, `solver.options['threads'] = -1`.
- Call `results = solver.solve(model, tee=False)`.

### Step 3 - Check Solution Status
- Verify `results.solver.status == pyo.SolverStatus.ok`.
- Verify `results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]`.
- If not met, handle as a failure.

### Step 4 - Extract and Validate Results
- Retrieve objective value: `total_cost = pyo.value(model.obj)`.
- Iterate over `model.x` to get variable values: `pyo.value(model.x[i, j])`.
- Recalculate totals to validate constraint satisfaction.

### Step 5 - Format Output
- Print the total cost: `print(f"RESULT:{total_cost}")`.
- Optionally, output a structured assignment summary.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
model.resources = pyo.Set(initialize=resources_list)
model.demand_points = pyo.Set(initialize=demand_points_list)
# ... (define parameters, variables, objective, constraints as per Modeling stage)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    total_cost = pyo.value(model.obj)
    # Extract variable values and validate
    for i in model.resources:
        for j in model.demand_points:
            val = pyo.value(model.x[i, j])
            if val > 0.5:
                print(f"Assign {val} of resource {i} to demand {j}")
    print(f"RESULT:{total_cost}")
else:
    print(f'RESULT_JSON:{{"status": "{results.solver.status}", "termination": "{results.solver.termination_condition}"}}')
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, which can lead to interpreting suboptimal or limit-stopped solutions as optimal.
- Accessing variable values without checking if the variable is active in the model instance.
- Forgetting to convert the objective value via `pyo.value()` before printing.
