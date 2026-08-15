---
name: Bipartite Assignment with Capacity Constraints
description: |
  Model and solve resource-to-task assignment problems with integer counts, per-unit capacity contributions, and linear costs using MILP solvers.

---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
Model the problem as a bipartite assignment with integer decision variables, where each assignment provides a specific capacity contribution towards a demand. The objective is to minimize total linear cost while respecting resource availability and satisfying all demand requirements.

### Step 1 - Define Problem Sets and Parameters
- Define two distinct sets: `RESOURCES` for supply nodes and `TASKS` for demand nodes.
- Collect parameters: `availability[i]` for each resource, `demand[j]` for each task, `capacity[i][j]` (per-unit contribution), and `cost[i][j]` (per-unit cost).

### Step 2 - Formulate Integer Decision Variables
- Create non-negative integer variables `x[i][j]`, representing the number of units of resource `i` assigned to task `j`.
- Define variable bounds directly using resource availability: `0 <= x[i][j] <= availability[i]`.

### Step 3 - Construct Demand Satisfaction Constraints
- For each task `j`, ensure the total capacity provided meets or exceeds its demand: `sum_over_i(capacity[i][j] * x[i][j]) >= demand[j]`.

### Step 4 - Enforce Resource Supply Limits
- For each resource `i`, ensure total assignments do not exceed its availability: `sum_over_j(x[i][j]) <= availability[i]`.

### Step 5 - Define Linear Cost Objective
- Formulate the objective to minimize total cost: `minimize sum_over_i sum_over_j(cost[i][j] * x[i][j])`.

### Formulation Template
```json
{
  "sets": ["RESOURCES", "TASKS"],
  "parameters": [
    "availability[RESOURCES]",
    "demand[TASKS]",
    "capacity[RESOURCES][TASKS]",
    "cost[RESOURCES][TASKS]"
  ],
  "decision_variables": ["x[RESOURCES][TASKS] ∈ NonNegativeIntegers"],
  "objective": {
    "sense": "min",
    "expression": "sum(i in RESOURCES, j in TASKS) cost[i][j] * x[i][j]"
  },
  "constraints": [
    "DemandSatisfaction[j in TASKS]: sum(i in RESOURCES) capacity[i][j] * x[i][j] >= demand[j]",
    "SupplyLimit[i in RESOURCES]: sum(j in TASKS) x[i][j] <= availability[i]"
  ]
}
```

### Common Pitfalls
- Forgetting that `capacity[i][j]` is a per-unit coefficient, not a limit on the variable itself.
- Defining variable bounds that are tighter than the aggregate supply limit, which can over-constrain the model.
- Using incomplete or inconsistent parameter matrices, leading to infeasibility or nonsensical results.

## Solving stage

### Strategy Overview
Implement the model using the OR-Tools linear solver wrapper, configure the SCIP or CBC solver for mixed-integer programming, solve within practical time limits, and rigorously verify the feasibility of the returned solution.

### Step 1 - Initialize Solver and Data Structures
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Initialize parameter matrices (e.g., `capacity`, `cost`) as nested lists or dictionaries, using synthetic data generation if complete data is unavailable.

### Step 2 - Create Bounded Integer Variables
- For each `(i, j)` pair, create variable: `x[i][j] = solver.IntVar(0, availability[i], f'x_{i}_{j}')`.

### Step 3 - Build Weighted Demand Constraints
- For each task `j`, create a constraint: `ct = solver.Constraint(demand[j], solver.infinity())`.
- For each resource `i`, add the weighted contribution: `ct.SetCoefficient(x[i][j], capacity[i][j])`.

### Step 4 - Build Supply Limit Constraints
- For each resource `i`, create a constraint: `ct = solver.Constraint(0, availability[i])`.
- For each task `j`, add the assignment: `ct.SetCoefficient(x[i][j], 1)`.

### Step 5 - Set Objective and Solve
- Create the objective expression by summing `cost[i][j] * x[i][j]` for all `i, j`.
- Set the objective to minimize and configure solver parameters: `solver.SetTimeLimit(60000)` and `solver.SetNumThreads(4)`.
- Call `solver.Solve()` and capture the result status.

### Step 6 - Verify Solution and Extract Results
- Check if the solver returned `OPTIMAL` or `FEASIBLE`.
- If successful, compute the total capacity delivered to each task `j` as `sum(capacity[i][j] * x[i][j].solution_value())` and verify it meets demand.
- Extract and report all non-zero assignments and the total objective value.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (create variables, constraints, objective as per steps)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    # Verify demand satisfaction
    for j in TASKS:
        delivered = sum(capacity[i][j] * x[i][j].solution_value() for i in RESOURCES)
        assert delivered >= demand[j] - 1e-6, f"Demand {j} not met."
    print(f'RESULT:{objective_value}')
else:
    print('{"status": "infeasible", "reason": "Solver could not find a feasible solution."}')
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Failing to verify that the solver's solution actually satisfies all constraints due to numerical tolerances.
- Omitting time limits or thread configuration for larger instances, leading to unpredictable runtimes.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Use Pyomo's abstract modeling capabilities to create a scalable, declarative MILP model. This approach cleanly separates sets, parameters, variables, and constraints, facilitating easy adaptation to different problem sizes and data sources.

### Step 1 - Declare Abstract Sets and Parameters
- Define `model.RESOURCES = pyo.Set()` and `model.TASKS = pyo.Set()`.
- Declare `model.availability`, `model.demand`, `model.capacity`, and `model.cost` as `pyo.Param` objects indexed over the appropriate sets.

### Step 2 - Define Integer Decision Variables
- Create variable `model.x = pyo.Var(model.RESOURCES, model.TASKS, within=pyo.NonNegativeIntegers, bounds=(0, None))`.

### Step 3 - Formulate Demand Constraints Using Rules
- Define a rule function `demand_rule(model, j)` that returns `sum(model.capacity[i, j] * model.x[i, j] for i in model.RESOURCES) >= model.demand[j]`.
- Create constraint `model.DemandSatisfaction = pyo.Constraint(model.TASKS, rule=demand_rule)`.

### Step 4 - Formulate Supply Constraints Using Rules
- Define a rule function `supply_rule(model, i)` that returns `sum(model.x[i, j] for j in model.TASKS) <= model.availability[i]`.
- Create constraint `model.SupplyLimit = pyo.Constraint(model.RESOURCES, rule=supply_rule)`.

### Step 5 - Construct Linear Objective Function
- Define the objective using a rule or expression: `model.total_cost = pyo.Objective(expr=sum(model.cost[i, j] * model.x[i, j] for i in model.RESOURCES for j in model.TASKS), sense=pyo.minimize)`.

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
  "decision_variables": ["x[RESOURCES, TASKS] ∈ NonNegativeIntegers"],
  "objective": {
    "sense": "min",
    "expression": "sum((i,j) in RESOURCES*TASKS) cost[i,j] * x[i,j]"
  },
  "constraints": [
    "DemandSatisfaction[j in TASKS]: sum(i in RESOURCES) capacity[i,j] * x[i,j] >= demand[j]",
    "SupplyLimit[i in RESOURCES]: sum(j in TASKS) x[i,j] <= availability[i]"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters or variables within rule functions, leading to `KeyError`.
- Forgetting to initialize all required parameters before creating a `ConcreteModel`, resulting in uninitialized data errors.
- Using overly complex rule functions that hinder model readability and performance.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with concrete data, select an appropriate MILP solver (HiGHS or CBC), solve with configured tolerances and time limits, and systematically handle the solver's termination status to ensure robust result extraction.

### Step 1 - Create Concrete Model and Populate Data
- Instantiate `model = pyo.ConcreteModel()`.
- Populate the sets and parameters, using systematic data generation if a full dataset is not provided.

### Step 2 - Instantiate Model Components
- The previously defined `Set`, `Param`, `Var`, `Constraint`, and `Objective` components are automatically instantiated with the concrete data.

### Step 3 - Select and Configure Solver
- Create solver object: `solver = pyo.SolverFactory('appsi_highs')` or `solver = pyo.SolverFactory('cbc')`.
- Configure solver options: `solver.options['time_limit'] = 30` and `solver.options['mip_rel_gap'] = 0.0`.

### Step 4 - Solve and Check Termination Status
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `pyo.SolverStatus.ok` and `results.solver.termination_condition` is `pyo.TerminationCondition.optimal` or `...feasible`.

### Step 5 - Extract and Validate Solution
- If the solve was successful, access `pyo.value(model.total_cost)` for the objective value.
- Iterate through `model.x` to report non-zero assignments.
- Programmatically verify that all demand and supply constraints are satisfied by the solution values.

### Step 6 - Handle Infeasibility or Errors
- If the solver status indicates an error or infeasibility, do not attempt to read variable values.
- Output a structured failure message and consider relaxing constraints or revising input data.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.RESOURCES = pyo.Set(initialize=resources_list)
model.TASKS = pyo.Set(initialize=tasks_list)
# ... (define parameters, variables, constraints, objective)

# solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs')
results = solver.solve(model)
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    objective_value = pyo.value(model.total_cost)
    # Validate constraints
    for j in model.TASKS:
        delivered = sum(pyo.value(model.capacity[i, j]) * pyo.value(model.x[i, j]) for i in model.RESOURCES)
        assert delivered >= pyo.value(model.demand[j]) - 1e-6
    print(f'RESULT:{objective_value}')
else:
    print('{"status": "failed", "termination_condition": "' + str(results.solver.termination_condition) + '"}')
```

### Common Pitfalls
- Confusing Pyomo's `SolverStatus` with `TerminationCondition`, leading to incorrect success/failure detection.
- Attempting to access `pyo.value()` on variables or expressions before checking the solve was successful.
- Not using the `appsi_highs` or `cbc` executable names correctly for the `SolverFactory`, causing solver not found errors.
