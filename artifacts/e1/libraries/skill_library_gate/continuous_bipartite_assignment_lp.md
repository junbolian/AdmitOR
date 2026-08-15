---
name: Continuous Bipartite Assignment LP
description: |
  Model and solve continuous linear assignment problems with bipartite resource-task structure, supply/demand constraints, and per-assignment upper bounds, using either direct solver APIs or algebraic modeling frameworks.

---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., OR-Tools, PuLP) to construct the model imperatively. It is suitable for users who prefer fine-grained control over variable and constraint creation, and for integrating into procedural codebases.

### Step 1 - Define Data Structures
- Organize problem data into indexed lists or dictionaries for resources, tasks, capacities, demands, costs, and per-assignment limits.
- Ensure indices are consistent across all data structures (e.g., `resource_index`, `task_index`).

### Step 2 - Create Decision Variables
- Instantiate a continuous, non-negative decision variable for each resource-task pair (e.g., `x[i][j]`).
- Set the variable's upper bound directly during creation to encode per-assignment limits efficiently.

### Step 3 - Formulate Demand Satisfaction Constraints
- For each task, create a linear equality constraint.
- Set the right-hand side to the task's exact demand requirement.
- For the left-hand side, sum the assignment variables from all resources to that task, each with a coefficient of 1.

### Step 4 - Formulate Supply Capacity Constraints
- For each resource, create a linear inequality (≤) constraint.
- Set the right-hand side to the resource's total capacity.
- For the left-hand side, sum the assignment variables from that resource to all tasks, each with a coefficient of 1.

### Step 5 - Define Linear Cost Objective
- Formulate the objective as the sum of each assignment variable multiplied by its per-unit cost.
- Set the solver's objective sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "tasks"
  ],
  "parameters": [
    {"name": "capacity", "index": "resources"},
    {"name": "demand", "index": "tasks"},
    {"name": "cost", "index": ["resources", "tasks"]},
    {"name": "max_assignment", "index": ["resources", "tasks"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["resources", "tasks"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in resources, j in tasks} cost[i,j] * x[i,j]"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": "tasks", "expression": "sum_{i in resources} x[i,j] == demand[j]"},
    {"name": "supply_capacity", "index": "resources", "expression": "sum_{j in tasks} x[i,j] <= capacity[i]"},
    {"name": "assignment_limit", "index": ["resources", "tasks"], "expression": "x[i,j] <= max_assignment[i,j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to set variable upper bounds, leading to unbounded solutions if `max_assignment` is not enforced elsewhere.
- Creating constraints with incorrect indices, causing mismatched sums (e.g., summing over resources in a task constraint but using a resource index).
- Not handling zero-capacity resources explicitly; while constraints will enforce zero flow, explicitly fixing their variables to zero can improve solver performance.

## Solving stage

### Strategy Overview
This stage involves invoking a linear programming solver (e.g., GLOP, CBC) through the direct API, checking solution status rigorously, extracting results, and validating them against the original constraints.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver instance for linear programming (e.g., `solver = pywraplp.Solver.CreateSolver('GLOP')`).
- Configure solver parameters such as time limits, tolerances, or verbosity as needed.

### Step 2 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the returned status against both `OPTIMAL` and `FEASIBLE` codes. Proceed only if status indicates a successful solve.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value.
- For each decision variable, extract its solution value if it exceeds a small tolerance (e.g., `1e-6`).
- Programmatically verify that the extracted solution satisfies all demand and capacity constraints within a numerical tolerance.

### Step 4 - Report Results
- Print a summary of the objective value and overall resource utilization.
- Output a detailed table of non-zero assignments, including associated costs.
- Structure critical outputs (like the objective value) for easy parsing by downstream systems.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
if solver is None:
    raise Exception('Solver not available.')
# ... (variable and constraint creation based on formulation template)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    # Extract variable values and validate
    for i in resources:
        for j in tasks:
            val = x[i,j].solution_value()
            if val > 1e-6:
                # Record assignment
    # Validate constraints
    for j in tasks:
        total_assigned = sum(x[i,j].solution_value() for i in resources)
        assert abs(total_assigned - demand[j]) < 1e-4, f"Demand {j} not met."
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Assuming a `FEASIBLE` status guarantees optimality; always check for `OPTIMAL` if an exact optimum is required.
- Not using a tolerance when checking variable values or constraint satisfaction, leading to false failures due to floating-point arithmetic.
- Omitting error handling for solver instantiation failure, causing crashes in environments where the solver is not installed.

# Workflow 2 (Algebraic Modeling Framework)

## Modeling stage

### Strategy Overview
This workflow uses an algebraic modeling framework (e.g., Pyomo, PuLP with LpVariables) to declare the model using sets, parameters, and declarative constraints. It promotes readability, maintainability, and easier model modification.

### Step 1 - Declare Abstract Sets and Parameters
- Define the index sets for resources and tasks as `Set` objects.
- Declare `Param` objects for capacities, demands, costs, and per-assignment limits, indexed by the appropriate sets.

### Step 2 - Declare Decision Variables
- Declare a continuous, non-negative `Var` for each resource-task pair.
- Optionally, set the variable's upper bound using the corresponding `max_assignment` parameter within its domain definition.

### Step 3 - Define Objective Rule
- Create a rule function that returns the sum of `cost[i,j] * x[i,j]` over all indices.
- Use this rule to construct an `Objective` object with sense `minimize`.

### Step 4 - Define Constraint Rules
- Create a rule function for demand satisfaction: for a given task `j`, return the sum of `x[i,j]` over all resources, equated to `demand[j]`.
- Create a rule function for supply capacity: for a given resource `i`, return the sum of `x[i,j]` over all tasks, constrained to be ≤ `capacity[i]`.
- Use these rules to construct `Constraint` objects indexed by the respective sets.

### Step 5 - Instantiate Concrete Model
- Create a concrete model instance by passing the data dictionaries to the `create_instance` method (Pyomo) or by directly assigning parameter values.
- Ensure all parameters are populated before solving.

### Formulation Template
```json
{
  "sets": [
    "I = set of resources",
    "J = set of tasks"
  ],
  "parameters": [
    {"name": "C", "description": "Capacity of resource i", "index": "I"},
    {"name": "D", "description": "Demand of task j", "index": "J"},
    {"name": "c", "description": "Cost per unit assigned from i to j", "index": ["I", "J"]},
    {"name": "U", "description": "Maximum allowed assignment from i to j", "index": ["I", "J"]}
  ],
  "decision_variables": [
    {"name": "x", "description": "Amount assigned from i to j", "index": ["I", "J"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum(c[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    {"name": "Demand", "index": "J", "expression": "sum(x[i,j] for i in I) == D[j]"},
    {"name": "Supply", "index": "I", "expression": "sum(x[i,j] for j in J) <= C[i]"},
    {"name": "Limit", "index": ["I", "J"], "expression": "x[i,j] <= U[i,j]"}
  ]
}
```

### Common Pitfalls
- Defining constraint rules with incorrect indexing, leading to `Rule` functions that are not passed the expected index.
- Forgetting to create a concrete instance before solving, resulting in errors about uninitialized parameters.
- Using mutable data structures (like lists) inside Pyomo `Rule` functions, which can cause performance issues or unexpected behavior; prefer accessing model parameters.

## Solving stage

### Strategy Overview
This stage involves selecting a suitable LP solver (e.g., HiGHS, CBC), passing the concrete model to it, configuring options, and processing the results with robust status checks and solution validation.

### Step 1 - Select Solver and Configure Options
- Choose an LP solver available through the modeling framework's interface (e.g., `'highs'`, `'cbc'`).
- Set solver options such as time limit (`time_limit`), optimality tolerance (`mipgap` for MIP, `ratio` for LP), and number of threads.

### Step 2 - Solve and Inspect Termination Conditions
- Invoke the solver via the framework's `solve` method on the model instance.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`). Both must indicate success to proceed.

### Step 3 - Extract and Validate Solution Values
- Access the objective value from the model object.
- Iterate over the decision variables, extracting their `value` attribute.
- Programmatically compute totals per task and per resource to verify constraint satisfaction within a numerical tolerance.

### Step 4 - Report Structured Output
- Print a summary including the objective value, solver status, and a high-level utilization report.
- Output a detailed list of assignments where the variable value exceeds a small tolerance.
- Format key results (e.g., objective value, solve time) in a machine-parsable way (e.g., JSON) for integration with automated systems.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=resource_indices)
model.J = pyo.Set(initialize=task_indices)
# ... (parameter and variable declaration based on formulation template)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, options={'time_limit': 30})

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    objective_value = pyo.value(model.obj)
    # Extract and validate variable values
    for i in model.I:
        for j in model.J:
            val = pyo.value(model.x[i,j])
            if val > 1e-6:
                # Record assignment
    # Validate constraints
    for j in model.J:
        total_assigned = sum(pyo.value(model.x[i,j]) for i in model.I)
        assert abs(total_assigned - model.D[j]) < 1e-4
else:
    print(f"Solver failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran without error) with `TerminationCondition.optimal` (a proven optimal solution was found); both checks are necessary.
- Accessing variable values before checking solver status, which may raise errors if the solve was unsuccessful.
- Not setting a time limit for large instances, potentially causing the process to hang indefinitely.
