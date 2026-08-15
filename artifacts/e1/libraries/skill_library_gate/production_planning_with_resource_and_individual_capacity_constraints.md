---
name: Production Planning with Resource and Individual Capacity Constraints
description: |
  A skill for modeling and solving linear production optimization problems with continuous variables, individual capacity bounds, and a shared resource constraint.
---

# Workflow 1 (OR-Tools LP with Bounded Variables)

## Modeling stage

### Strategy Overview
Model the problem as a continuous linear program using the OR-Tools wrapper. Define variables with explicit lower and upper bounds to embed non-negativity and individual capacity constraints efficiently. Formulate a single linear resource constraint and a linear profit maximization objective.

### Step 1 - Define Data Structures
- Organize problem parameters into parallel lists or dictionaries for easy iteration.
- Store `profit`, `resource_consumption`, and `individual_capacity` values indexed by item.

### Step 2 - Create Variables with Bounds
- Use `solver.NumVar(lower_bound, upper_bound, name)` to create each `production_quantity` variable.
- Set lower bound to 0 for non-negativity and upper bound to the item's `individual_capacity`.

### Step 3 - Formulate Resource Constraint
- Build a linear expression summing `resource_consumption[i] * variable[i]` across all items.
- Add a single constraint: `solver.Add(sum_expr <= total_resource_capacity)`.

### Step 4 - Set Linear Objective
- Create an objective object: `objective = solver.Objective()`.
- For each item, set its coefficient: `objective.SetCoefficient(variable[i], profit[i])`.
- Set the objective sense to maximization: `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["I_items"],
  "parameters": ["profit[I]", "resource_consumption[I]", "individual_capacity[I]", "total_resource_capacity"],
  "decision_variables": ["x[I] (continuous, 0 <= x[i] <= individual_capacity[i])"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I_items)"
  },
  "constraints": [
    "resource_constraint: sum(resource_consumption[i] * x[i] for i in I_items) <= total_resource_capacity"
  ]
}
```

### Common Pitfalls
- Assuming continuous variables when integer production is more realistic; always check the problem context.
- Fabricating missing data instead of requesting clarification or handling incomplete data explicitly.
- Adding separate `x[i] >= 0` constraints when non-negativity is already enforced via variable bounds.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools linear programming backend (GLOP). Check solver status rigorously, extract and verify the solution, and perform post-optimal analysis such as calculating resource utilization.

### Step 1 - Select and Configure Solver
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- For mixed-integer problems, use `'CBC'` or `'SCIP'` instead.

### Step 2 - Solve and Check Status
- Execute the solve: `status = solver.Solve()`.
- Verify success: check if `status` is `solver.OPTIMAL` or `solver.FEASIBLE`. Do not proceed if status indicates infeasibility or error.

### Step 3 - Extract and Validate Solution
- Extract the objective value: `total_profit = objective.Value()`.
- Extract variable values: `production[i] = variable[i].solution_value()`.
- Calculate derived metrics (e.g., total resource used) to confirm constraint satisfaction.

### Step 4 - Perform Post-Solution Analysis
- Compute profit-to-resource ratios to verify economic intuition.
- Identify binding constraints by checking slack or dual values.
- Report key metrics: total profit, resource utilization percentage, and items at capacity.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
x = [solver.NumVar(0.0, individual_capacity[i], f'x_{i}') for i in range(num_items)]
resource_expr = sum(resource_consumption[i] * x[i] for i in range(num_items))
solver.Add(resource_expr <= total_resource_capacity)
objective = solver.Objective()
for i in range(num_items):
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_profit = objective.Value()
    solution = [x[i].solution_value() for i in range(num_items)]
    # Validate and report
else:
    # Handle infeasible/unbounded status
```

### Common Pitfalls
- Trusting non-optimal solver statuses (e.g., `UNKNOWN`, `INFEASIBLE`) and outputting pseudo-answers.
- Running multiple redundant solver calls without changing model parameters.
- Implementing manual feasibility checks that duplicate solver functionality.

# Workflow 2 (Pyomo LP with Indexed Constraints)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract modeling capabilities. Define indexed sets, parameters, and variables. Use Pyomo's `Constraint` and `Objective` components for a clean separation of model structure and data, facilitating scalability and maintainability.

### Step 1 - Define Index Sets and Parameters
- Create an index set: `model.I = pyo.Set(initialize=range(num_items))`.
- Define Pyomo `Param` objects for `profit`, `resource_consumption`, and `individual_capacity`, initialized from data dictionaries.

### Step 2 - Define Variables with Domain
- Create continuous, non-negative variables: `model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)`.
- Apply individual upper bounds via a constraint rule or by setting variable bounds directly.

### Step 3 - Formulate Objective and Constraints
- Define the objective: `model.obj = pyo.Objective(expr=sum(model.profit[i] * model.x[i] for i in model.I), sense=pyo.maximize)`.
- Add the global resource constraint as a single `pyo.Constraint`.
- Add individual capacity constraints as an indexed `pyo.Constraint` using a rule.

### Step 4 - Separate Model from Data
- Use lambda functions or external data files to initialize parameters, keeping the model template generic.

### Formulation Template
```json
{
  "sets": ["I_items"],
  "parameters": ["profit[I]", "consumption[I]", "upper_limit[I]", "total_capacity"],
  "decision_variables": ["x[I] (NonNegativeReals)"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I_items)"
  },
  "constraints": [
    "resource_limit: sum(consumption[i] * x[i] for i in I_items) <= total_capacity",
    "capacity[i]: x[i] <= upper_limit[i] for each i in I_items"
  ]
}
```

### Common Pitfalls
- Using Pyomo reserved words (e.g., `items`) as set names.
- Omitting critical constraints like individual capacity bounds.
- Introducing unsupported nonlinear terms for a linear workflow.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an appropriate open-source LP solver (e.g., HiGHS, CBC). Configure solver options for performance, check termination conditions rigorously, and extract results with validation.

### Step 1 - Select and Configure Solver
- Instantiate the solver: `solver = pyo.SolverFactory('highs')` (or `'cbc'`).
- Set practical options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`.

### Step 2 - Solve and Verify Termination
- Execute the solve: `results = solver.solve(model, tee=False)`.
- Check both `results.solver.status` (`SolverStatus.ok`) and `results.solver.termination_condition` (`optimal` or `feasible`).

### Step 3 - Extract and Analyze Solution
- Extract the objective value: `total_profit = pyo.value(model.obj)`.
- Extract variable values: `production[i] = pyo.value(model.x[i])`.
- Calculate total resource usage to verify constraint satisfaction and identify binding constraints.

### Step 4 - Output and Validate
- Report solution in a structured format (e.g., JSON) including status, objective value, and production quantities.
- Perform ratio analysis (profit/consumption) as a sanity check on the solution's logic.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_items))
model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals, bounds=lambda m, i: (0, upper_limit[i]))
model.obj = pyo.Objective(expr=sum(profit[i] * model.x[i] for i in model.I), sense=pyo.maximize)
model.resource_con = pyo.Constraint(expr=sum(consumption[i] * model.x[i] for i in model.I) <= total_capacity)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    total_profit = pyo.value(model.obj)
    solution = [pyo.value(model.x[i]) for i in model.I]
    # Validate and report
else:
    # Handle solver failure
```

### Common Pitfalls
- Not checking both solver status and termination condition before extracting results.
- Setting unnecessary or redundant solver parameters.
- Hardcoding solution values for verification instead of extracting them from the solved model object.
