---
name: Continuous Assignment with Capacity Limits
description: |
  Model and solve linear assignment problems with continuous non-negative variables, three-layer constraints (resource capacity, demand satisfaction, per-assignment limits), and linear cost minimization using open-source solvers.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling style to define a bipartite assignment problem. It structures data as dictionaries for clarity and leverages Pyomo's integration with open-source solvers like HiGHS and CBC for solving continuous linear programs.

### Step 1 - Define Sets and Parameters
- Declare two index sets: `RESOURCES` and `TASKS`.
- Create parameters for resource availability (`availability[i]`), task requirements (`requirement[j]`), per-pair assignment costs (`cost[i,j]`), and per-pair capacity limits (`capacity[i,j]`).
- Store parameters as dictionaries or 2D arrays for efficient access during constraint building.

### Step 2 - Create Decision Variables
- Define a continuous, non-negative variable `x[i,j]` for each resource-task pair, representing the allocation amount.
- Use `pyo.Var(domain=pyo.NonNegativeReals)` to enforce non-negativity.

### Step 3 - Formulate Three-Layer Constraints
- **Resource Capacity**: `sum(x[i,j] for j in TASKS) <= availability[i]` for each resource `i`.
- **Demand Satisfaction**: `sum(x[i,j] for i in RESOURCES) == requirement[j]` for each task `j`.
- **Individual Assignment Limits**: `x[i,j] <= capacity[i,j]` for each resource-task pair.

### Step 4 - Set Linear Objective
- Define the objective to minimize total cost: `minimize sum(cost[i,j] * x[i,j] for i in RESOURCES for j in TASKS)`.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    {"name": "availability", "index": "RESOURCES"},
    {"name": "requirement", "index": "TASKS"},
    {"name": "cost", "index": ["RESOURCES", "TASKS"]},
    {"name": "capacity", "index": ["RESOURCES", "TASKS"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["RESOURCES", "TASKS"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in RESOURCES for j in TASKS)"
  },
  "constraints": [
    {"name": "ResourceCapacity", "expression": "sum(x[i,j] for j in TASKS) <= availability[i]", "index": "RESOURCES"},
    {"name": "DemandSatisfaction", "expression": "sum(x[i,j] for i in RESOURCES) == requirement[j]", "index": "TASKS"},
    {"name": "AssignmentLimit", "expression": "x[i,j] <= capacity[i,j]", "index": ["RESOURCES", "TASKS"]}
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total resource availability is at least total demand, which can lead to infeasibility.
- Using integer or binary variable domains when the problem context allows fractional allocations, unnecessarily complicating the solve.
- Not initializing all `capacity[i,j]` parameters, which may cause model construction errors if a pair is missing.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured open-source solver (HiGHS or CBC). The process involves instantiating the solver, setting performance parameters, checking termination status rigorously, and programmatically validating the solution against all constraints.

### Step 1 - Configure and Run Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set solver options such as time limit (`seconds=30`), optimality tolerance (`ratio=0.0`), and threads for parallel processing (`threads=4`).
- Execute the solve: `results = solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Verify the solver status: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `assert results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}`.
- If status or termination is not acceptable, output a structured error message with details for debugging.

### Step 3 - Extract and Validate Solution
- Retrieve variable values: `value = pyo.value(model.x[i,j])`.
- Programmatically verify all three constraint types with a tolerance (e.g., `1e-6`) to ensure the solution is feasible.
- Compute aggregates (total per resource, total per task) and compare against parameters.

### Step 4 - Report Results
- Print the objective value with a prefix like `RESULT:{objective_value}` for automated parsing.
- Generate a detailed assignment report showing non-zero allocations, their costs, and constraint satisfaction summaries.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (using concrete example)
model = pyo.ConcreteModel()
model.RESOURCES = pyo.Set(initialize=RESOURCE_INDICES)
model.TASKS = pyo.Set(initialize=TASK_INDICES)
# ... (populate parameters and create variables, constraints, objective as per steps)

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    # Extract and validate solution
    for i in model.RESOURCES:
        for j in model.TASKS:
            val = pyo.value(model.x[i,j])
            # ... validation logic
    print(f"RESULT:{pyo.value(model.objective)}")
else:
    print(f"SOLVER_FAILED: status={results.solver.status}, termination={results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `solver.termination_condition`, which can mask suboptimal or failed solves.
- Failing to set a time limit, potentially allowing the solver to run indefinitely on large or difficult instances.
- Assuming the solver's internal feasibility tolerances are sufficient; always perform post-solution validation.

# Workflow 2 (OR-Tools with GLOP/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to construct the model imperatively. It is well-suited for rapid prototyping and leverages the efficient GLOP solver for continuous LPs, with a fallback to CBC for mixed-integer requirements.

### Step 1 - Initialize Solver and Data Structures
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver("GLOP")`.
- Prepare input data as 2D lists or arrays for costs and capacities, indexed by `[resource][task]`.
- Define scalar parameters for resource availability and task requirements.

### Step 2 - Create Bounded Decision Variables
- For each resource `i` and task `j`, create a variable: `x[i][j] = solver.NumVar(0.0, capacity[i][j], f"x_{i}_{j}")`.
- The upper bound is set directly from the per-pair capacity matrix, enforcing individual assignment limits.

### Step 3 - Add Aggregate Constraints
- **Resource Capacity**: For each resource `i`, create a constraint `sum(x[i][j] for j in tasks) <= availability[i]`.
- **Demand Satisfaction**: For each task `j`, create a constraint `sum(x[i][j] for i in resources) == requirement[j]`.
- Build constraints by setting coefficients via `constraint.SetCoefficient(x[i][j], 1.0)` in nested loops.

### Step 4 - Define Linear Objective
- Create the objective expression: `objective = solver.Objective()`.
- In nested loops, set coefficients: `objective.SetCoefficient(x[i][j], cost[i][j])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["resources", "tasks"],
  "parameters": [
    {"name": "availability", "index": "resources"},
    {"name": "requirement", "index": "tasks"},
    {"name": "cost", "index": ["resources", "tasks"]},
    {"name": "capacity", "index": ["resources", "tasks"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["resources", "tasks"], "domain": "Continuous", "lower_bound": 0, "upper_bound": "capacity[i][j]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in resources for j in tasks)"
  },
  "constraints": [
    {"name": "ResourceCapacity", "expression": "sum(x[i][:]) <= availability[i]", "index": "resources"},
    {"name": "DemandSatisfaction", "expression": "sum(x[:][j]) == requirement[j]", "index": "tasks"}
  ]
}
```

### Common Pitfalls
- Manually setting variable upper bounds incorrectly if `capacity` matrix contains `None` or very large values; ensure bounds are finite.
- Adding constraints in an order that makes coefficient setting complex; follow a systematic nested loop pattern.
- Using the wrong solver string (e.g., `"CBC"` for a pure LP) which may be less efficient than `"GLOP"`.

## Solving stage

### Strategy Overview
Solve the OR-Tools model, check for optimality or feasibility, and extract the solution. The workflow includes explicit verification of constraint satisfaction and provides a template for reporting detailed assignment patterns.

### Step 1 - Execute Solve and Check Status
- Run the solver: `status = solver.Solve()`.
- Check if the solve was successful: `if status in (solver.OPTIMAL, solver.FEASIBLE):`.
- If the status is not acceptable, handle the failure by reporting the status code and any available solver information.

### Step 2 - Extract Variable Values and Verify
- Retrieve each variable's value: `x[i][j].solution_value()`.
- Compute sums per resource and per task to verify resource capacity and demand satisfaction constraints within a tolerance.
- Verify each assignment against its individual capacity limit.

### Step 3 - Report Objective and Assignment Details
- Print the objective value: `print(f"RESULT:{solver.Objective().Value()}")`.
- Iterate over variables and print non-zero assignments, showing resource, task, allocated amount, and cost contribution.

### Step 4 - Consider Integer Requirements (If Needed)
- If the problem context suggests integer allocations (e.g., whole units), re-solve using a MIP solver (`"CBC"`) and compare the integer objective with the LP relaxation to assess the integrality gap.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
# ... (create variables, constraints, objective as per modeling steps)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Extract and validate solution
    total_cost = solver.Objective().Value()
    for i in range(num_resources):
        resource_sum = 0.0
        for j in range(num_tasks):
            val = x[i][j].solution_value()
            resource_sum += val
            # ... individual validation and reporting
        # Verify resource capacity constraint
        assert resource_sum <= availability[i] + 1e-6
    print(f"RESULT:{total_cost}")
else:
    print(f"SOLVER_FAILED: status={status}")
```

### Common Pitfalls
- Confusing `solver.OPTIMAL` with `solver.FEASIBLE`; both indicate a valid solution, but only `OPTIMAL` guarantees optimality.
- Not using a tolerance when checking constraint satisfaction due to floating-point arithmetic, leading to false infeasibility errors.
- Overlooking the need for integer variables when the real-world application requires whole units, resulting in an impractical fractional solution.
