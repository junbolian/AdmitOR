---
name: Multi-Resource Knapsack with Demand Bounds
description: |
  Model and solve integer linear programs for selecting items under multiple resource capacity constraints and individual demand limits, maximizing total revenue.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a procedural, solver-specific API (Google OR-Tools) for direct model construction. It is efficient for rapid prototyping and deployment where fine-grained control over the solving process is needed.

### Step 1 - Define Variables with Integrated Bounds
- Declare integer decision variables for each item, directly setting their upper bound to the demand limit.
- Use `solver.IntVar(lb, ub, name)` to create non-negative integer variables bounded above by demand.
- Example: `x[i] = solver.IntVar(0, demand[i], f"x_{i}")`.

### Step 2 - Construct Sparse Resource Usage Matrix
- Initialize a 2D list (resources x items) with zeros to represent resource consumption.
- For each resource, iterate through a pre-defined list of items that consume it, setting the corresponding matrix entry to 1.
- This creates a sparse coefficient matrix for constraint construction.

### Step 3 - Add Knapsack-Style Capacity Constraints
- For each resource, create a linear inequality constraint summing the usage of selected items.
- Use the precomputed resource usage matrix as coefficients: `sum(usage[r][i] * x[i] for i in items) <= capacity[r]`.
- Add the constraint to the solver using `solver.Add(...)`.

### Step 4 - Set Linear Maximization Objective
- Define the objective as the sum of item revenue multiplied by the decision variable.
- Use `solver.Maximize(sum(revenue[i] * x[i] for i in items))`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of items/packages"},
    {"name": "R", "description": "Set of resources"}
  ],
  "parameters": [
    {"name": "revenue_i", "for": "i in I", "description": "Unit revenue for item i"},
    {"name": "demand_i", "for": "i in I", "description": "Maximum allowable quantity for item i"},
    {"name": "capacity_r", "for": "r in R", "description": "Available capacity of resource r"},
    {"name": "usage_ri", "for": "r in R, i in I", "description": "Binary indicator (1 if item i uses resource r)"}
  ],
  "decision_variables": [
    {"name": "x_i", "for": "i in I", "description": "Non-negative integer quantity of item i to select", "domain": "integer >= 0"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue_i * x_i for i in I)"
  },
  "constraints": [
    {"name": "DemandBound", "for": "i in I", "expression": "x_i <= demand_i"},
    {"name": "ResourceCapacity", "for": "r in R", "expression": "sum(usage_ri * x_i for i in I) <= capacity_r"}
  ]
}
```

### Common Pitfalls
- Adding separate constraints for variable upper bounds instead of using the built-in variable bounds, which increases model size unnecessarily.
- Manually populating the dense resource usage matrix with nested loops, leading to error-prone code; prefer sparse initialization from lists.
- Forgetting to check if the solver object was created successfully (`None` return), causing runtime errors.

## Solving stage

### Strategy Overview
This stage focuses on configuring the MIP solver (SCIP or CBC), executing the solve, rigorously checking the solution status, and extracting results for validation and reporting.

### Step 1 - Configure Solver with Performance Settings
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Set a time limit appropriate for the problem scale: `solver.SetTimeLimit(30000)` for 30 seconds.
- Configure parallel processing if available: `solver.SetNumThreads(4)`.

### Step 2 - Execute Solve and Check Status
- Invoke the solver: `status = solver.Solve()`.
- Check for optimality: `if status == pywraplp.Solver.OPTIMAL:`.
- Also accept feasible solutions: `elif status == pywraplp.Solver.FEASIBLE:`.

### Step 3 - Validate Solution Against Constraints
- After solving, compute the actual usage of each resource: `used_capacity = sum(usage[r][i] * x[i].solution_value() for i in items)`.
- Verify `used_capacity <= capacity[r]` for all resources to catch any potential solver numerical issues.
- Similarly, check that `x[i].solution_value() <= demand[i]`.

### Step 4 - Extract and Report Non-Zero Decisions
- Iterate through all decision variables.
- Filter and report only those with a solution value greater than zero, along with their contribution to the objective.
- Print a summary of total revenue and resource utilization.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
if solver is None:
    raise RuntimeError("Solver backend not available.")
# ... (construct model as per Modeling stage)

# solve with status / termination checks
solver.SetTimeLimit(30000)
status = solver.Solve()

if status == solver.OPTIMAL or status == solver.FEASIBLE:
    print(f"Objective value = {solver.Objective().Value()}")
    # Validate and extract solution
    for r in resources:
        usage = sum(usage_matrix[r][i] * x[i].solution_value() for i in items)
        assert usage <= capacity[r], f"Resource {r} capacity violated."
    for i in items:
        val = x[i].solution_value()
        if val > 0:
            print(f"  x[{i}] = {val}")
else:
    print("No optimal or feasible solution found.")
```

### Common Pitfalls
- Assuming the solver status `FEASIBLE` guarantees optimality; it only indicates a feasible integer solution was found.
- Not validating the solution post-solve, which can miss subtle constraint violations due to solver tolerances.
- Setting conflicting solver parameters (e.g., both `SetTimeLimit` and `SetTimeLimit` in milliseconds vs. seconds) from different documentation sources.

# Workflow 2 (Modeling Language - Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to create a declarative model. It separates problem formulation from solver choice, enhancing readability, maintainability, and ease of modification for different problem instances.

### Step 1 - Define Abstract Sets and Parameters
- Create Pyomo `Set` objects for items and resources to structure the model indices.
- Define `Param` objects (dictionaries) for revenue, demand, capacity, and binary resource usage, initializing them with data.
- Example: `model.revenue = pyo.Param(model.I, initialize=revenue_data)`.

### Step 2 - Declare Variables with Implicit Bounds
- Declare decision variables using `pyo.Var`, specifying `domain=pyo.NonNegativeIntegers`.
- Enforce demand upper bounds via explicit constraints (`model.x[i] <= model.demand[i]`) rather than variable bounds, keeping the model logic clear and constraints explicit.

### Step 3 - Construct Constraints via Rules
- Define a function (rule) for each constraint type that returns the expression for a given index.
- For resource capacity: `def resource_rule(model, r): return sum(model.usage[r, i] * model.x[i] for i in model.I) <= model.capacity[r]`.
- Use `pyo.Constraint(model.R, rule=resource_rule)` to create all constraints efficiently.

### Step 4 - Define Objective Function
- Create a `pyo.Objective` with `sense=pyo.maximize`.
- The expression is `sum(model.revenue[i] * model.x[i] for i in model.I)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of items/packages"},
    {"name": "R", "description": "Set of resources"}
  ],
  "parameters": [
    {"name": "revenue", "index": "I", "description": "Unit revenue for each item"},
    {"name": "demand", "index": "I", "description": "Maximum allowable quantity for each item"},
    {"name": "capacity", "index": "R", "description": "Available capacity for each resource"},
    {"name": "usage", "index": ["R", "I"], "description": "Binary indicator (1 if item i uses resource r)"}
  ],
  "decision_variables": [
    {"name": "x", "index": "I", "description": "Non-negative integer quantity of item i to select", "domain": "NonNegativeIntegers"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in I)"
  },
  "constraints": [
    {"name": "DemandBound", "index": "I", "expression": "x[i] <= demand[i]"},
    {"name": "ResourceCapacity", "index": "R", "expression": "sum(usage[r,i] * x[i] for i in I) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Using variable bounds (`bounds=(0, demand[i])`) for demand limits, which can make the model less transparent and harder to debug compared to explicit constraints.
- Defining constraint rules that have side effects or rely on global variables, leading to non-reproducible models.
- Not initializing `Param` dictionaries completely for all indices, which causes runtime errors when the model is instantiated.

## Solving stage

### Strategy Overview
This stage involves selecting a solver backend (e.g., CBC), configuring it through Pyomo's solver manager, solving the model, and carefully handling the solution loading and validation process.

### Step 1 - Instantiate Model and Configure Solver
- Create a concrete model instance: `instance = model.create_instance(data)`.
- Select a solver: `solver = pyo.SolverFactory('cbc')`.
- Set solver options for optimality and time: `solver.options['seconds'] = 30`.

### Step 2 - Solve and Check Termination Conditions
- Execute the solve: `results = solver.solve(instance, tee=False)`.
- Check the solver status: `if results.solver.status == pyo.SolverStatus.ok:`.
- Check the termination condition: `if results.solver.termination_condition == pyo.TerminationCondition.optimal:` or `== pyo.TerminationCondition.feasible`.

### Step 3 - Safely Load and Validate Solution
- Use `instance.solutions.load_from(results)` to load the solution into the model instance.
- Manually compute resource usage: `used = sum(pyo.value(instance.usage[r,i]) * pyo.value(instance.x[i]) for i in instance.I)`.
- Verify `used <= pyo.value(instance.capacity[r])` for all resources.

### Step 4 - Report Solution Details
- Iterate through the decision variables `instance.x`.
- Print items with non-zero values, their quantity, and contribution to revenue.
- Summarize total objective value and resource utilization percentages.

### Code Usage
```python
# build model from formulation
model = pyo.AbstractModel()
# ... (define sets, params, variables, constraints, objective as per Modeling stage)
data = { ... } # Your parameter data
instance = model.create_instance(data)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(instance, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    instance.solutions.load_from(results)
    # Validate and report
    for r in instance.R:
        usage = sum(pyo.value(instance.usage[r,i]) * pyo.value(instance.x[i]) for i in instance.I)
        assert usage <= pyo.value(instance.capacity[r]), f"Resource {r} overused."
    for i in instance.I:
        val = pyo.value(instance.x[i])
        if val > 0:
            print(f"x[{i}] = {val}")
    print(f"Total Revenue: {pyo.value(instance.objective)}")
else:
    print("Solver failed to find a feasible solution.")
```

### Common Pitfalls
- Attempting to access `instance.x[i]` values before calling `load_from(results)`, resulting in `None` or default values.
- Setting conflicting solver options (e.g., `threads` with a parallel scheduler) that cause the solver to fail silently.
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or limit-stopped solutions as failures.
