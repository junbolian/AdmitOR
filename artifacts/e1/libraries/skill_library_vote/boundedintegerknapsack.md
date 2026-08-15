---
name: BoundedIntegerKnapsack
description: |
  Model and solve a single-resource constrained integer knapsack problem with individual item capacity limits, maximizing linear profit.
---

# Workflow 1 (OR-Tools / SCIP)

## Modeling stage

### Strategy Overview
Model the problem using Google OR-Tools' linear solver wrapper (pywraplp), defining bounded integer variables directly and constructing the model via a procedural API. This approach is efficient for straightforward MILP formulations and provides direct control over the solver backend.

### Step 1 - Define Variables and Parameters
- Organize problem data in parallel lists or dictionaries indexed by item: `profit`, `resource_consumption`, `individual_capacity`.
- Create a solver instance (e.g., `SCIP`). Use `solver.IntVar(lower_bound, upper_bound, name)` to define non-negative integer decision variables, where `upper_bound` is the individual capacity limit for each item.

### Step 2 - Formulate Constraints
- For the shared resource constraint (`knapsack_capacity`), build a linear expression `sum(resource_consumption[i] * x[i] for i in items)` and add it with `solver.Add(expr <= total_limit)`.
- Individual upper bounds are enforced by the variable definitions themselves and do not require separate constraints.

### Step 3 - Set Objective
- Create the objective with `solver.Objective()`.
- Set coefficients for each variable using `objective.SetCoefficient(x[i], profit[i])`.
- Specify maximization with `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": {
    "profit": {"index": "items", "type": "float"},
    "resource_consumption": {"index": "items", "type": "float"},
    "individual_capacity": {"index": "items", "type": "integer"},
    "total_resource_limit": {"type": "float"}
  },
  "decision_variables": {
    "x": {"index": "items", "domain": "nonnegative_integers", "upper_bound": "individual_capacity"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in items)"
  },
  "constraints": [
    {
      "name": "resource_limit",
      "expression": "sum(resource_consumption[i] * x[i] for i in items) <= total_resource_limit"
    }
  ]
}
```

### Common Pitfalls
- Forgetting to check if the solver backend is available (`if solver is None:`), leading to runtime errors.
- Using `solver.NumVar` instead of `solver.IntVar`, which results in continuous variables and changes the problem type.
- Not setting a time limit for large instances, potentially causing the solve to run indefinitely.

## Solving stage

### Strategy Overview
Solve the model using the configured SCIP backend, extract the solution, and perform verification. Implement robust status checking and error handling to manage infeasible or unbounded cases.

### Step 1 - Configure and Execute Solver
- Set solver parameters for performance: `solver.SetTimeLimit(ms)` and `solver.SetNumThreads(n)`.
- Call `solver.Solve()` to execute the optimization.

### Step 2 - Extract and Verify Solution
- Check the solver status: `status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE)`.
- If optimal or feasible, extract the objective value with `objective.Value()` and variable values with `x[i].solution_value()`.
- Recompute total resource usage and verify it does not exceed the limit. Check that each variable respects its individual upper bound.

### Step 3 - Output and Integration
- Provide a human-readable summary listing production quantities, total profit, and resource usage.
- Output a machine-readable result (e.g., `RESULT:{value}`) for easy integration into automated systems.
- For non-optimal statuses, output structured error information including the solver status code.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
if solver is None:
    raise Exception('SCIP solver not available.')
# ... (variable creation, constraint addition, objective setting)

# solve with status / termination checks
solver.SetTimeLimit(time_limit_ms)
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    solution = {i: x[i].solution_value() for i in items}
    # Verification and output
else:
    # Handle infeasible, unbounded, or other statuses
    print(f"Solver terminated with status: {status}")
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; always check for `OPTIMAL` if an exact solution is required.
- Not verifying solution feasibility against the original constraints, which can catch solver numerical errors.
- Omitting error handling for cases where the model is infeasible, leading to crashes when accessing solution values.

# Workflow 2 (Pyomo / CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract modeling syntax, defining sets, parameters, and variables declaratively. This approach enhances model readability, maintainability, and facilitates integration with a wide range of solvers via the Pyomo ecosystem.

### Step 1 - Declare Model Components
- Define a Pyomo `ConcreteModel` or `AbstractModel`.
- Create a Set `model.I` initialized with the list of item indices.
- Define a `Var` `model.x` indexed by `model.I` with domain `pyo.NonNegativeIntegers`.

### Step 2 - Implement Bounds and Constraints
- Set individual upper bounds by either using `model.x[i].setub(individual_capacity[i])` in a loop or by adding constraints via a `ConstraintList`.
- Add the shared resource constraint as a single `Constraint` object: `sum(resource_consumption[i] * model.x[i] for i in model.I) <= total_limit`.

### Step 3 - Define Objective
- Create an `Objective` object with the expression `sum(profit[i] * model.x[i] for i in model.I)` and `sense=pyo.maximize`.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": {
    "profit": {"index": "I", "type": "float"},
    "resource_consumption": {"index": "I", "type": "float"},
    "individual_capacity": {"index": "I", "type": "integer"},
    "total_resource_limit": {"type": "float"}
  },
  "decision_variables": {
    "x": {"index": "I", "domain": "NonNegativeIntegers"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    {
      "name": "resource_limit",
      "expression": "sum(resource_consumption[i] * x[i] for i in I) <= total_resource_limit"
    },
    {
      "name": "individual_bounds",
      "index": "I",
      "expression": "x[i] <= individual_capacity[i]"
    }
  ]
}
```

### Common Pitfalls
- Using an `AbstractModel` without properly defining `Param` rules for data initialization, causing runtime errors.
- Forgetting to set the `upper_bound` for variables, leaving them unbounded and potentially causing unrealistic solutions.
- Inefficiently adding individual bound constraints one by line instead of using a loop or `ConstraintList`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via a standard solver manager (e.g., `SolverFactory`). Implement a solver fallback strategy, carefully manage solution loading, and verify results.

### Step 1 - Select and Configure Solver
- Instantiate a solver object: `solver = pyo.SolverFactory('cbc')`.
- Configure solver options: set time limit (`seconds`), optimality gap (`ratio`), and number of threads (`threads`). For exact solutions, set `ratio=0.0`.

### Step 2 - Execute with Robust Handling
- Solve with `results = solver.solve(model, tee=False)`.
- Check the solver termination condition: `results.solver.termination_condition == TerminationCondition.optimal`.
- Use `load_solutions=False` initially to check status before loading results, then load manually with `model.solutions.load_from(results)`.

### Step 3 - Analyze and Output Solution
- Extract variable values: `value(model.x[i])`.
- Recompute objective and constraint values to verify feasibility.
- Output a structured JSON result containing the objective value, solution vector, and solver statistics for integration and logging.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.x = pyo.Var(model.I, domain=pyo.NonNegativeIntegers)
# ... (set bounds, add constraints, define objective)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = time_limit
solver.options['ratio'] = optimality_gap

results = solver.solve(model, load_solutions=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    solution = {i: pyo.value(model.x[i]) for i in model.I}
    # Verification and output
else:
    # Handle non-optimal termination
    print(f"Solver terminated with condition: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not implementing a solver fallback (e.g., trying GLPK if CBC is unavailable), which can halt execution in constrained environments.
- Assuming the solution is loaded automatically; always check `load_solutions` usage and the `results` object structure.
- Ignoring the optimality gap setting, which may lead to accepting suboptimal solutions for problems requiring exact answers.
