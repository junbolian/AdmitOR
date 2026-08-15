---
name: Bounded Linear Knapsack Optimization
description: |
  Model and solve integer knapsack problems with individual item capacity bounds and a shared resource constraint using linear programming solvers.
---

# Workflow 1 (Google OR-Tools / pywraplp)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' `pywraplp` interface to formulate a Mixed-Integer Programming (MIP) model. It leverages the solver's native variable bounds for individual capacity constraints and constructs the model using efficient Python data structures.

### Step 1 - Define Data Structures
- Organize problem parameters as parallel lists or dictionaries indexed by item identifiers for clarity and maintainability.
- Store `profit_per_unit`, `resource_consumption_per_unit`, and `individual_capacity_limit` for each item.
- Define a `total_resource_limit` parameter for the shared knapsack constraint.

### Step 2 - Instantiate Solver and Variables
- Create a solver instance using `pywraplp.Solver.CreateSolver("SCIP")` or `"CBC"`.
- For each item, define a non-negative integer decision variable using `solver.IntVar(lower_bound, upper_bound, name)`, directly encoding its individual capacity limit as the variable's upper bound.

### Step 3 - Formulate Objective and Constraints
- Create the objective expression: `solver.Maximize(sum(profit[i] * x[i] for i in items))`.
- Add the shared resource constraint: `solver.Add(sum(resource_consumption[i] * x[i] for i in items) <= total_resource_limit)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of items"
  ],
  "parameters": [
    "p_i: profit per unit of item i ∈ I",
    "w_i: resource consumption per unit of item i ∈ I",
    "c_i: individual capacity limit for item i ∈ I",
    "W: total resource limit (knapsack capacity)"
  ],
  "decision_variables": [
    "x_i: non-negative integer quantity of item i ∈ I to produce/select"
  ],
  "objective": {
    "sense": "max",
    "expression": "∑_{i ∈ I} p_i * x_i"
  },
  "constraints": [
    "∑_{i ∈ I} w_i * x_i ≤ W (shared resource)",
    "x_i ≤ c_i, ∀ i ∈ I (individual bounds, often encoded as variable bounds)"
  ]
}
```

### Common Pitfalls
- Forgetting to set a time limit or thread count for larger instances, leading to uncontrolled runtime.
- Using `solver.IntVar(0, solver.infinity(), name)` and adding separate `x_i <= c_i` constraints, which is less efficient than setting the upper bound directly.
- Not verifying the solver was successfully created (`if solver is None`) before proceeding.

## Solving stage

### Strategy Overview
Solve the MIP model with performance tuning, robust status checking, and solution validation. Extract and analyze results to verify optimality and constraint satisfaction.

### Step 1 - Configure and Execute Solver
- Set solver parameters: `solver.SetTimeLimit(time_limit_ms)` and `solver.SetNumThreads(num_threads)`.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Check Solution Status and Extract Values
- Verify the solution status is `OPTIMAL` or `FEASIBLE` using `status in (solver.OPTIMAL, solver.FEASIBLE)`.
- If successful, extract variable values using `x[i].solution_value()`.
- Compute derived metrics (e.g., total profit, total resource used) for validation.

### Step 3 - Validate and Analyze Solution
- Assert that the extracted solution satisfies all constraints (individual bounds and shared resource).
- Calculate profit-per-resource ratios to understand the solver's selection logic.
- Optionally, add a constraint `objective >= current_best + 1` and re-solve to prove optimality (infeasibility confirms no better solution).

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
if solver is None:
    raise RuntimeError("Solver backend not available.")
x = {}
for i in I:
    x[i] = solver.IntVar(0, individual_capacity_limit[i], f"x_{i}")
objective = solver.Objective()
for i in I:
    objective.SetCoefficient(x[i], profit_per_unit[i])
objective.SetMaximization()
solver.Add(sum(resource_consumption[i] * x[i] for i in I) <= total_resource_limit)

# solve with status / termination checks
solver.SetTimeLimit(30000)  # 30 seconds
solver.SetNumThreads(4)
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    solution = {i: x[i].solution_value() for i in I}
    total_profit = sum(profit_per_unit[i] * solution[i] for i in I)
    total_used = sum(resource_consumption[i] * solution[i] for i in I)
    # Validation and analysis...
else:
    print("No optimal or feasible solution found.")
```

### Common Pitfalls
- Confusing `solver.OPTIMAL` with `solver.FEASIBLE`; both indicate a valid solution, but only the former guarantees optimality.
- Not handling the case where the solver hits the time limit and returns a `FEASIBLE` status.
- Assuming variable values exist without checking the solution status first.

# Workflow 2 (Pyomo with CBC/GLPK)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo modeling library to create an abstract or concrete model, separating problem specification from solver interaction. It emphasizes clarity and solver-agnostic formulation, with individual bounds applied via constraints or variable attributes.

### Step 1 - Define Abstract Sets and Parameters
- Declare an abstract `Set` for items (`model.I`).
- Define `Param` components for `profit`, `resource_consumption`, `individual_capacity`, and `total_resource_limit`, indexed by the item set.

### Step 2 - Declare Variables and Bounds
- Create non-negative integer variables: `model.x = pyo.Var(model.I, domain=pyo.NonNegativeIntegers)`.
- Apply individual capacity limits either by setting variable upper bounds (`model.x[i].setub(capacity[i])`) or by adding explicit constraints (`model.x[i] <= capacity[i]`).

### Step 3 - Construct Objective and Constraints
- Define the objective: `model.obj = pyo.Objective(expr=sum(profit[i] * model.x[i] for i in model.I), sense=pyo.maximize)`.
- Add the shared resource constraint: `model.resource_constraint = pyo.Constraint(expr=sum(resource_consumption[i] * model.x[i] for i in model.I) <= total_resource_limit)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of items"
  ],
  "parameters": [
    "p_i: profit per unit of item i ∈ I",
    "w_i: resource consumption per unit of item i ∈ I",
    "u_i: individual upper bound for item i ∈ I",
    "W: total resource limit"
  ],
  "decision_variables": [
    "x_i: non-negative integer quantity of item i ∈ I"
  ],
  "objective": {
    "sense": "max",
    "expression": "∑_{i ∈ I} p_i * x_i"
  },
  "constraints": [
    "∑_{i ∈ I} w_i * x_i ≤ W",
    "x_i ≤ u_i, ∀ i ∈ I"
  ]
}
```

### Common Pitfalls
- Using `bounds=(0, None)` in `pyo.Var` and forgetting to apply individual upper bounds via separate constraints or `setub`.
- Creating the model with data hard-coded inside expressions, reducing reusability.
- Not verifying the mathematical formulation matches the problem statement before implementation.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver like CBC or GLPK, with explicit configuration for optimality gap and time limits. Implement robust solution loading and validation.

### Step 1 - Select and Configure Solver
- Instantiate a solver: `solver = pyo.SolverFactory("cbc")`.
- Configure solver options: `solver.options["seconds"] = time_limit`, `solver.options["ratio"] = 0.0` for zero optimality gap.

### Step 2 - Solve with Defensive Result Handling
- Solve with `load_solutions=False` to prevent automatic loading of potentially invalid results.
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- Only load the solution if the status checks pass.

### Step 3 - Extract, Validate, and Report
- Extract variable values: `model.x[i].value`.
- Compute and validate derived metrics (total profit, resource usage).
- Output results in a structured format (e.g., JSON) for downstream use.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=item_indices)
model.p = pyo.Param(model.I, initialize=profit_data)
model.w = pyo.Param(model.I, initialize=resource_consumption_data)
model.u = pyo.Param(model.I, initialize=individual_capacity_data)
model.W = pyo.Param(initialize=total_resource_limit)

model.x = pyo.Var(model.I, domain=pyo.NonNegativeIntegers)
# Apply individual bounds via variable upper bounds
for i in model.I:
    model.x[i].setub(model.u[i])

model.obj = pyo.Objective(expr=sum(model.p[i] * model.x[i] for i in model.I), sense=pyo.maximize)
model.resource_con = pyo.Constraint(expr=sum(model.w[i] * model.x[i] for i in model.I) <= model.W)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = -1.0  # Use default for exact solution; 0.0 may not be valid for all solvers
results = solver.solve(model, load_solutions=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    model.solutions.load_from(results)
    solution = {i: pyo.value(model.x[i]) for i in model.I}
    # Validation and analysis...
else:
    print("Solver failed to find an optimal or feasible solution.")
```

### Common Pitfalls
- Using `load_solutions=True` and then checking status, which may load an invalid solution before the check.
- Assuming `ratio=0.0` is a valid option for all solvers; some require `-1.0` for default or a specific keyword.
- Not having a fallback solver strategy (e.g., trying GLPK if CBC fails) when the primary solver is unavailable.
