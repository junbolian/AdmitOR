---
name: Assignment Problem with Capacity and Per-Allocation Limits
description: |
  Model and solve linear assignment problems with resource capacities, task requirements, per-assignment bounds, and linear cost minimization using structured data and open-source solvers.

---

# Workflow 1 (Pyomo with HiGHS/CBC Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define a linear program with clear separation of sets, parameters, variables, and constraints. It is designed for flexibility and integration with high-performance open-source solvers like HiGHS and CBC.

### Step 1 - Define Index Sets and Parameters
- Define two index sets: `RESOURCES` (e.g., persons, machines) and `TASKS` (e.g., projects, jobs).
- Organize all input data into parameter dictionaries: `available_time[i]` for resource capacity, `project_requirement[j]` for task demand, `cost[i][j]` for unit cost, and `assignment_limit[i][j]` for per-allocation upper bounds.
- Use nested dictionaries or 2D lists for cost and limit parameters, indexed by `(i, j)`.

### Step 2 - Create Decision Variables
- Create a continuous, non-negative decision variable `assignment_amount[i, j]` for each resource-task pair.
- Directly incorporate the per-assignment limit as an upper bound during variable creation (`ub=assignment_limit[i][j]`) to reduce the number of explicit constraints.

### Step 3 - Formulate Objective and Constraints
- Formulate the objective to minimize total cost: `sum(cost[i][j] * assignment_amount[i, j] for all i, j)`.
- Add resource capacity constraints: `sum(assignment_amount[i, j] for j in TASKS) <= available_time[i]` for each resource `i`.
- Add task requirement constraints: `sum(assignment_amount[i, j] for i in RESOURCES) == project_requirement[j]` for each task `j`.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    {"name": "available_time", "index": "i in RESOURCES"},
    {"name": "project_requirement", "index": "j in TASKS"},
    {"name": "cost", "index": "(i in RESOURCES, j in TASKS)"},
    {"name": "assignment_limit", "index": "(i in RESOURCES, j in TASKS)"}
  ],
  "decision_variables": [
    {"name": "assignment_amount", "index": "(i in RESOURCES, j in TASKS)", "domain": "NonNegativeReals", "bounds": "ub=assignment_limit[i][j]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * assignment_amount[i,j] for i in RESOURCES for j in TASKS)"
  },
  "constraints": [
    {"name": "resource_capacity", "index": "i in RESOURCES", "expression": "sum(assignment_amount[i,j] for j in TASKS) <= available_time[i]"},
    {"name": "task_requirement", "index": "j in TASKS", "expression": "sum(assignment_amount[i,j] for i in RESOURCES) == project_requirement[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to define the `assignment_limit` parameter, leading to unbounded variables and unrealistic solutions.
- Using equality (`==`) for resource capacity constraints, which can make the model infeasible if total capacity exceeds total requirement.
- Not using a tolerance (e.g., `1e-6`) when checking equality constraints in the solution verification step.

## Solving stage

### Strategy Overview
The solving stage focuses on instantiating the Pyomo model, configuring a solver (HiGHS for LP, CBC for MIP), executing the solve, and rigorously checking the solution status before extracting and verifying results.

### Step 1 - Instantiate Model and Solve
- Create a `ConcreteModel` and use the defined sets, parameters, and formulation to build it.
- Instantiate the solver via `SolverFactory` (e.g., `'highs'` or `'cbc'`).
- Set key solver options such as `time_limit` and `threads` for performance control.
- Execute the solve and capture the results object.

### Step 2 - Check Solver Status and Termination
- Before accessing the solution, check the solver status (`results.solver.status`) is `SolverStatus.ok`.
- Check the termination condition (`results.solver.termination_condition`) is `optimal` or `feasible`. Handle other conditions (e.g., `infeasible`, `unbounded`) with appropriate error messages.

### Step 3 - Extract and Verify Solution
- Extract the objective value using `pyo.value(model.objective)`.
- Iterate over decision variables to retrieve non-zero assignments, using a tolerance (e.g., `> 1e-6`) to filter near-zero values.
- Implement verification logic: recalculate sums for capacity and requirement constraints to ensure they are satisfied within a small tolerance.

### Code Usage
```python
import pyomo.environ as pyo

# 1. Build model (assuming data is in dictionaries: available_time, project_requirement, cost, assignment_limit)
model = pyo.ConcreteModel()
model.R = pyo.Set(initialize=RESOURCES)
model.T = pyo.Set(initialize=TASKS)
model.assignment_amount = pyo.Var(model.R, model.T, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, assignment_limit[i][j]))
def obj_rule(m):
    return sum(cost[i][j] * m.assignment_amount[i, j] for i in m.R for j in m.T)
model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
# ... Add constraint rules using `pyo.Constraint`

# 2. Solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['threads'] = 4
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimal solution found.")
        # 3. Extract and verify solution
        total_cost = pyo.value(model.objective)
        assignments = {}
        for i in model.R:
            for j in model.T:
                val = pyo.value(model.assignment_amount[i, j])
                if val > 1e-6:
                    assignments[(i, j)] = val
        # ... Add verification checks here
    else:
        print(f"Solver terminated with condition: {results.solver.termination_condition}")
else:
    print("Solver failed.")
```

### Common Pitfalls
- Proceeding to extract variable values without checking `termination_condition`, potentially using suboptimal or infeasible results.
- Not setting a `time_limit`, allowing the solver to run indefinitely on large or difficult instances.
- Using loose tolerances for verification, which might mask constraint violations.

# Workflow 2 (OR-Tools Linear Solver Backend)

## Modeling stage

### Strategy Overview
This workflow uses the Google OR-Tools linear solver wrapper (supporting GLOP, CBC, SCIP) for a more direct, matrix-oriented API. It is suitable for rapid prototyping and problems where variable and constraint creation is done via explicit loops.

### Step 1 - Initialize Solver and Define Data Structures
- Choose a solver backend appropriate for the problem type: `GLOP` for LP, `CBC` or `SCIP` for MIP.
- Store input parameters in lists or dictionaries indexed by resource and task IDs.

### Step 2 - Create Variables with Bounds
- Use nested loops over resources and tasks to create solver variables (`solver.NumVar` or `solver.IntVar`).
- Set the variable's lower bound to 0 and upper bound directly to the `assignment_limit[i][j]` value.

### Step 3 - Build Constraints and Objective Incrementally
- Create capacity constraints by summing variables for each resource and setting the sum `<= available_time[i]`.
- Create requirement constraints by summing variables for each task and setting the sum `== project_requirement[j]`.
- Build the objective function by adding terms `cost[i][j] * variable[i][j]` for all variables.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    {"name": "available_time", "index": "i in RESOURCES"},
    {"name": "project_requirement", "index": "j in TASKS"},
    {"name": "cost", "index": "(i in RESOURCES, j in TASKS)"},
    {"name": "assignment_limit", "index": "(i in RESOURCES, j in TASKS)"}
  ],
  "decision_variables": [
    {"name": "assignment_amount", "index": "(i in RESOURCES, j in TASKS)", "domain": "Continuous (or Integer)", "bounds": "[0, assignment_limit[i][j]]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * assignment_amount[i][j])"
  },
  "constraints": [
    {"name": "resource_capacity", "index": "i in RESOURCES", "expression": "sum_j assignment_amount[i][j] <= available_time[i]"},
    {"name": "task_requirement", "index": "j in TASKS", "expression": "sum_i assignment_amount[i][j] == project_requirement[j]"}
  ]
}
```

### Common Pitfalls
- Mixing up indices when creating constraints, leading to incorrect sums (e.g., using task index in a resource capacity sum).
- Not using integer variables when the real-world problem requires discrete allocations, resulting in fractional solutions that are impractical.
- Failing to name constraints and variables, making debugging more difficult.

## Solving stage

### Strategy Overview
The solving stage involves invoking the solver, checking the result code, extracting the solution if optimal/feasible, and performing post-solve validation of constraints and objective value.

### Step 1 - Solve and Check Result Status
- Call `solver.Solve()`.
- Check the returned status against solver-specific constants (e.g., `pywraplp.Solver.OPTIMAL`, `FEASIBLE`). Handle non-optimal statuses appropriately.

### Step 2 - Extract Variable Values and Objective
- If the status is optimal or feasible, retrieve the objective value via `solver.Objective().Value()`.
- Loop through all variables and extract their solution values using `variable.solution_value()`.
- Store non-zero assignments (above a tolerance) for reporting.

### Step 3 - Validate Solution and Output Results
- Recompute the left-hand side of all constraints using the extracted variable values.
- Compare against the right-hand side (capacity, requirement) within a small tolerance (e.g., `1e-6`).
- Output a structured summary including total cost, solver status, and a list of assignments.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Build model from formulation
solver = pywraplp.Solver.CreateSolver('CBC')
if not solver:
    raise Exception('Solver not available.')

# Create variables with bounds
x = {}
for i in RESOURCES:
    for j in TASKS:
        x[i, j] = solver.NumVar(0, assignment_limit[i][j], f'x_{i}_{j}')

# Add constraints
for i in RESOURCES:
    constraint = solver.Constraint(0, available_time[i])
    for j in TASKS:
        constraint.SetCoefficient(x[i, j], 1)

for j in TASKS:
    constraint = solver.Constraint(project_requirement[j], project_requirement[j])
    for i in RESOURCES:
        constraint.SetCoefficient(x[i, j], 1)

# Set objective
objective = solver.Objective()
for i in RESOURCES:
    for j in TASKS:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# 2. Solve with status / termination checks
status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL:
    print('Optimal solution found.')
    total_cost = objective.Value()
    assignments = {}
    for i in RESOURCES:
        for j in TASKS:
            val = x[i, j].solution_value()
            if val > 1e-6:
                assignments[(i, j)] = val
    # 3. Add verification checks here
elif status == pywraplp.Solver.FEASIBLE:
    print('Feasible, but not necessarily optimal, solution found.')
else:
    print('The problem does not have an optimal solution.')
```

### Common Pitfalls
- Assuming `solver.Solve()` always returns an optimal solution without checking the status code.
- Not using a tolerance when checking if a variable value is zero, leading to excessive output from near-zero assignments.
- Omitting solution verification, which can miss subtle constraint violations due to numerical rounding.
