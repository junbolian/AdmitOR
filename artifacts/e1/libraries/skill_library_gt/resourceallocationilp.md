---
name: ResourceAllocationILP
description: |
  Formulate and solve integer linear programs for resource allocation with capacity-weighted demand satisfaction and linear cost minimization.
---

# Workflow 1 (OR-Tools SCIP/CBC)

## Modeling stage

### Strategy Overview
Model the problem as an integer linear program using OR-Tools' linear solver wrapper. Define integer assignment variables with explicit bounds, construct linear constraints for resource availability and weighted demand satisfaction, and set a linear minimization objective.

### Step 1 - Define Indexed Data Structures
- Organize problem data into lists or dictionaries for resources and tasks.
- Define parameters: `availability[i]`, `demand[j]`, `capacity[i][j]`, `cost[i][j]`.
- Use consistent indexing (resource `i`, task `j`) across all data structures.

### Step 2 - Create Integer Decision Variables
- Instantiate a 2D array of integer variables `x[i][j]` using `solver.IntVar(lower_bound, upper_bound, name)`.
- Set lower bound to 0 and upper bound to `availability[i]` for each variable to provide a tight bound.
- Name variables systematically (e.g., `f"x_{i}_{j}"`) for debugging.

### Step 3 - Formulate Resource Availability Constraints
- For each resource `i`, create a linear constraint: `sum(x[i][j] for j in tasks) <= availability[i]`.
- Use `solver.Constraint(-solver.infinity(), availability[i])` and `SetCoefficient` to build the sum.

### Step 4 - Formulate Demand Satisfaction Constraints
- For each task `j`, create a linear constraint: `sum(capacity[i][j] * x[i][j] for i in resources) >= demand[j]`.
- Use `solver.Constraint(demand[j], solver.infinity())` and `SetCoefficient` with coefficient `capacity[i][j]`.

### Step 5 - Set Linear Minimization Objective
- Create the objective with `solver.Objective()`.
- Add terms using `objective.SetCoefficient(x[i][j], cost[i][j])` for all variable indices.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["resources", "tasks"],
  "parameters": [
    "availability[resource]",
    "demand[task]",
    "capacity[resource][task]",
    "cost[resource][task]"
  ],
  "decision_variables": ["x[resource][task] ∈ ℤ⁺"],
  "objective": {
    "sense": "min",
    "expression": "Σ_resource Σ_task cost[resource][task] * x[resource][task]"
  },
  "constraints": [
    "Σ_task x[resource][task] ≤ availability[resource] ∀ resource",
    "Σ_resource capacity[resource][task] * x[resource][task] ≥ demand[task] ∀ task"
  ]
}
```

### Common Pitfalls
- Forgetting to set variable upper bounds, leading to weaker relaxation and slower solving.
- Incorrectly ordering indices in `capacity` or `cost` matrices, causing mismatched coefficients.
- Not checking for `solver.infinity()` availability when creating unbounded constraints.

## Solving stage

### Strategy Overview
Solve the integer linear program using the SCIP or CBC backend via OR-Tools. Configure solver performance settings, execute the solve, rigorously check the solution status, and extract and validate the integer assignment results.

### Step 1 - Initialize Solver with MIP Backend
- Create solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")` or `"CBC"`.
- Prefer SCIP for advanced features or CBC for open-source reliability.

### Step 2 - Configure Performance Parameters
- Set a time limit: `solver.SetTimeLimit(milliseconds)`.
- Set number of threads: `solver.SetNumThreads(integer)` for parallel processing.
- Avoid setting conflicting parameters; rely on defaults for optimality gap unless specific tolerance is needed.

### Step 3 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check status: `status = solver.Solve()`.
- Accept solutions with status `pywraplp.Solver.OPTIMAL` (0) or `pywraplp.Solver.FEASIBLE` (1).

### Step 4 - Extract and Validate Solution
- If status is acceptable, retrieve variable values: `val = x[i][j].solution_value()`.
- Round values to nearest integer if fractional tolerances appear.
- Compute verification metrics: total resource usage per `i` and total capacity delivered per `j`.
- Programmatically assert `usage_i <= availability[i]` and `delivered_j >= demand[j]`.

### Step 5 - Output Structured Results
- Report total objective value: `objective.Value()`.
- Output non-zero assignments with indices and values.
- Include constraint verification summary in the output.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (variable and constraint creation as per modeling stage)
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    assignments = {}
    for i in resources:
        for j in tasks:
            val = x[i][j].solution_value()
            if val > 0:
                assignments[(i, j)] = int(round(val))
    # Verification
    for i in resources:
        used = sum(x[i][j].solution_value() for j in tasks)
        assert used <= availability[i], f"Resource {i} overused"
    for j in tasks:
        delivered = sum(capacity[i][j] * x[i][j].solution_value() for i in resources)
        assert delivered >= demand[j], f"Task {j} demand not met"
    print(f"Optimal cost: {total_cost}", f"Assignments: {assignments}")
else:
    print("No feasible solution found", status)
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; it only guarantees feasibility.
- Not rounding near-integer solution values (e.g., 1.999999) before integer validation.
- Omitting verification steps, which can hide subtle constraint violations.

# Workflow 2 (Pyomo with CBC/Highs)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract syntax with `ConcreteModel`. Define sets for indexing, parameters for data, `NonNegativeIntegers` variables for assignments, and construct constraints and objective using rule functions for clarity and scalability.

### Step 1 - Define Sets and Parameters
- Create Pyomo Sets: `model.RESOURCES = pyo.Set(initialize=resource_list)` and `model.TASKS = pyo.Set(initialize=task_list)`.
- Define Parameters: `model.availability = pyo.Param(model.RESOURCES, initialize=avail_dict)`, `model.demand`, `model.capacity`, `model.cost` similarly.

### Step 2 - Declare Integer Decision Variables
- Create variable: `model.x = pyo.Var(model.RESOURCES, model.TASKS, domain=pyo.NonNegativeIntegers)`.
- The `NonNegativeIntegers` domain enforces integer and non-negativity constraints.

### Step 3 - Formulate Objective with Linear Expression
- Define objective: `model.obj = pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for i in model.RESOURCES for j in model.TASKS), sense=pyo.minimize)`.
- Use Pyomo's `sum` and parameter indexing directly in the expression.

### Step 4 - Implement Availability Constraint Rule
- Define a rule function: `def availability_rule(model, i): return sum(model.x[i,j] for j in model.TASKS) <= model.availability[i]`.
- Create constraint: `model.avail_con = pyo.Constraint(model.RESOURCES, rule=availability_rule)`.

### Step 5 - Implement Demand Constraint Rule
- Define a rule function: `def demand_rule(model, j): return sum(model.capacity[i,j] * model.x[i,j] for i in model.RESOURCES) >= model.demand[j]`.
- Create constraint: `model.demand_con = pyo.Constraint(model.TASKS, rule=demand_rule)`.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    "availability[RESOURCES]",
    "demand[TASKS]",
    "capacity[RESOURCES, TASKS]",
    "cost[RESOURCES, TASKS]"
  ],
  "decision_variables": ["x[RESOURCES, TASKS] ∈ ℤ⁺"],
  "objective": {
    "sense": "min",
    "expression": "Σ_{i∈RESOURCES} Σ_{j∈TASKS} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "Σ_{j∈TASKS} x[i,j] ≤ availability[i] ∀ i∈RESOURCES",
    "Σ_{i∈RESOURCES} capacity[i,j] * x[i,j] ≥ demand[j] ∀ j∈TASKS"
  ]
}
```

### Common Pitfalls
- Using mutable default arguments (like `list`) in rule functions; always define rules with explicit parameters.
- Confusing Pyomo `Param` initialization with live Python dictionaries; ensure data is static at model creation.
- Incorrectly indexing parameters in rules, leading to `KeyError`; verify all `(i,j)` pairs exist in parameter dictionaries.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or HiGHS solver via `SolverFactory`. Configure solver options for time and optimality gap, execute solve with proper error handling, check termination conditions, and load and verify the solution.

### Step 1 - Instantiate Solver Factory
- Create solver: `solver = pyo.SolverFactory("cbc")` or `pyo.SolverFactory("highs")`.
- HiGHS is preferred for performance; CBC is a robust fallback.

### Step 2 - Set Solver Options
- Configure time limit: `solver.options["seconds"] = 30`.
- Set optimality gap: `solver.options["ratio"] = 0.0` for exact optimal solution.
- Optionally set thread count: `solver.options["threads"] = 4`.

### Step 3 - Solve with Status Checking
- Execute: `results = solver.solve(model, tee=False)` (`tee=True` for verbose output).
- Check solver status: `status = results.solver.status`.
- Check termination condition: `term = results.solver.termination_condition`.
- Accept `SolverStatus.ok` with `TerminationCondition.optimal` or `.feasible`.

### Step 4 - Load and Extract Solution
- If status is acceptable, values are automatically loaded into the model.
- Extract objective: `total_cost = pyo.value(model.obj)`.
- Extract assignments: `{ (i,j): int(pyo.value(model.x[i,j])) for i,j in model.x if pyo.value(model.x[i,j]) > 0 }`.

### Step 5 - Verify Constraints Programmatically
- Recompute resource usage: `used_i = sum(pyo.value(model.x[i,j]) for j in model.TASKS)` and compare to `model.availability[i]`.
- Recompute delivered capacity: `delivered_j = sum(model.capacity[i,j] * pyo.value(model.x[i,j]) for i in model.RESOURCES)` and compare to `model.demand[j]`.
- Use a small tolerance (e.g., `1e-6`) for floating-point comparisons.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
model.RES = pyo.Set(initialize=resources)
model.TASK = pyo.Set(initialize=tasks)
# ... (parameter and variable creation as per modeling stage)
# ... (constraint and objective creation as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    total_cost = pyo.value(model.obj)
    assignments = {(i,j): int(pyo.value(model.x[i,j])) for i in model.RES for j in model.TASK if pyo.value(model.x[i,j]) > 0}
    # Verification
    for i in model.RES:
        used = sum(pyo.value(model.x[i,j]) for j in model.TASK)
        assert used <= pyo.value(model.availability[i]) + 1e-6, f"Resource {i} overused"
    for j in model.TASK:
        delivered = sum(pyo.value(model.capacity[i,j]) * pyo.value(model.x[i,j]) for i in model.RES)
        assert delivered >= pyo.value(model.demand[j]) - 1e-6, f"Task {j} demand not met"
    print(f"Optimal cost: {total_cost}", f"Assignments: {assignments}")
else:
    print(f"Solver failed: status={status}, termination={term}")
```

### Common Pitfalls
- Forgetting to check both `solver.status` and `termination_condition`, leading to acceptance of incomplete solutions.
- Not using `pyo.value()` to access parameter and variable values post-solve.
- Setting invalid solver options (e.g., negative time) that cause the solver to fail silently.
