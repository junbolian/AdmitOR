---
name: Budgeted Maximum Coverage Modeling and Solving
description: |
  Model and solve budget-constrained weighted coverage problems using binary selection and coverage indicator variables, with workflows for CP-SAT and MILP solvers.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
This workflow models the problem using Google OR-Tools' CP-SAT solver, which is designed for constraint programming with integer variables. It leverages native Boolean logic and efficient search for binary optimization problems with linear constraints.

### Step 1 - Define Core Variables
- Create a list of binary selection variables (`x_i`) for each candidate item (e.g., facility, tower) using `model.NewBoolVar()`.
- Create a list of binary coverage indicator variables (`y_j`) for each requirement (e.g., region, customer) using `model.NewBoolVar()`.

### Step 2 - Enforce Budget Constraint
- Add a linear knapsack constraint: `sum(cost[i] * x_i for all i) <= budget_limit`. Use `model.Add()` with the summed expression.

### Step 3 - Link Coverage to Selection
- For each coverage requirement `j`, add an activation constraint: `y_j <= sum(x_i for i in coverage_set[j])`. This ensures a requirement can only be considered covered if at least one relevant item is selected.

### Step 4 - Formulate Objective
- Maximize the weighted sum of coverage indicators: `model.Maximize(sum(weight[j] * y_j for all j))`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "J: set of coverage requirements"
  ],
  "parameters": [
    "cost_i: cost of selecting item i ∈ I",
    "weight_j: weight/benefit of covering requirement j ∈ J",
    "budget: total available budget",
    "coverage_map_j: list of items i ∈ I that cover requirement j"
  ],
  "decision_variables": [
    "x_i ∈ {0,1} ∀ i ∈ I (1 if item selected)",
    "y_j ∈ {0,1} ∀ j ∈ J (1 if requirement covered)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight_j * y_j for j in J)"
  },
  "constraints": [
    "sum(cost_i * x_i for i in I) <= budget",
    "y_j <= sum(x_i for i in coverage_map_j) ∀ j ∈ J"
  ]
}
```

### Common Pitfalls
- Forgetting to define coverage indicator variables, leading to a model that only selects items without tracking coverage outcomes.
- Using equality (`y_j == sum(...)`) in the coverage constraint, which incorrectly forces coverage if any covering item is selected.
- Hard-coding data values within the model construction, reducing reusability for different problem instances.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured runtime and parallelism parameters. Extract and validate the solution, ensuring it meets the problem constraints and provides the expected objective value.

### Step 1 - Configure Solver Parameters
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds` for a runtime cap, `solver.parameters.num_search_workers` for parallel search, and `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` if a proven optimal solution is required.

### Step 2 - Solve and Check Status
- Execute the solver: `status = solver.Solve(model)`.
- Check if a feasible solution was found: `status in (cp_model.OPTIMAL, cp_model.FEASIBLE)`. Proceed only if true.

### Step 3 - Extract and Verify Solution
- Retrieve selected items: `selected_items = [i for i in I if solver.Value(x_i) == 1]`.
- Retrieve covered requirements: `covered_requirements = [j for j in J if solver.Value(y_j) == 1]`.
- Compute the total cost from the solution and verify it does not exceed the budget.
- Access the objective value via `solver.ObjectiveValue()`.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# Define variables
x = [model.NewBoolVar(f"x_{i}") for i in range(n_items)]
y = [model.NewBoolVar(f"y_{j}") for j in range(n_requirements)]
# Add constraints
model.Add(sum(cost[i] * x[i] for i in range(n_items)) <= budget)
for j in range(n_requirements):
    covering_items = coverage_map[j]
    model.Add(y[j] <= sum(x[i] for i in covering_items))
# Set objective
model.Maximize(sum(weight[j] * y[j] for j in range(n_requirements)))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in range(n_items) if solver.Value(x[i]) == 1]
    covered = [j for j in range(n_requirements) if solver.Value(y[j]) == 1]
    total_cost = sum(cost[i] for i in selected)
    print(f"RESULT:{solver.ObjectiveValue()}")
    # Additional verification and output
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking solver status before accessing variable values, which can cause runtime errors.
- Using an exact equality check (`== 1`) for binary variables; while safe for CP-SAT, be mindful of floating-point tolerances in other solvers.
- Omitting key solver parameters (like time limit) for large instances, risking excessive runtime.

# Workflow 2 (MILP Solver via Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to formulate the problem as a Mixed-Integer Linear Program (MILP), suitable for commercial or open-source solvers like Gurobi, CBC, or HiGHS. It emphasizes a declarative modeling style with sets and parameters.

### Step 1 - Define Model Structure
- Create a Pyomo `ConcreteModel`.
- Define `Set` objects for items (`I`) and requirements (`J`).
- Define `Param` objects for costs, weights, budget, and a coverage mapping dictionary.

### Step 2 - Create Decision Variables
- Define binary selection variables: `model.x = pyo.Var(model.I, domain=pyo.Binary)`.
- Define binary coverage indicator variables: `model.y = pyo.Var(model.J, domain=pyo.Binary)`.

### Step 3 - Add Budget Constraint
- Add a constraint: `sum(model.cost[i] * model.x[i] for i in model.I) <= model.budget`.

### Step 4 - Add Coverage Activation Constraints
- For each requirement `j` in `model.J`, add a constraint: `model.y[j] <= sum(model.x[i] for i in model.coverage_map[j])`.

### Step 5 - Define Objective
- Set the objective: `model.obj = pyo.Objective(expr=sum(model.weight[j] * model.y[j] for j in model.J), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "J: set of coverage requirements"
  ],
  "parameters": [
    "cost_i: cost of selecting item i ∈ I",
    "weight_j: weight/benefit of covering requirement j ∈ J",
    "budget: total available budget",
    "coverage_map_j: list of items i ∈ I that cover requirement j"
  ],
  "decision_variables": [
    "x_i ∈ {0,1} ∀ i ∈ I (1 if item selected)",
    "y_j ∈ {0,1} ∀ j ∈ J (1 if requirement covered)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight_j * y_j for j in J)"
  },
  "constraints": [
    "sum(cost_i * x_i for i in I) <= budget",
    "y_j <= sum(x_i for i in coverage_map_j) ∀ j ∈ J"
  ]
}
```

### Common Pitfalls
- Defining the coverage mapping as a dense matrix instead of a sparse dictionary, leading to inefficient model building.
- Incorrectly indexing parameters or variables within constraint rules, causing runtime errors.
- Using a `BuildAction` or callback unnecessarily for simple linear constraints; prefer direct `Constraint` rules.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver. Check termination status rigorously and extract solution values with a tolerance threshold to account for numerical precision.

### Step 1 - Select and Configure Solver
- Create a solver instance: `solver = pyo.SolverFactory('solver_name')` (e.g., 'gurobi', 'cbc', 'highs').
- Set solver options: `options = {'time_limit': 30, 'mip_rel_gap': 0.0, 'threads': 4}`. Pass options via `solver.solve(model, options=options)` or `solver.options = options`.

### Step 2 - Solve and Validate Status
- Execute the solver: `results = solver.solve(model)`.
- Check the solver status: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `assert results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)`.

### Step 3 - Extract and Verify Solution
- Retrieve selected items using a tolerance: `selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]`.
- Retrieve covered requirements: `covered_requirements = [j for j in model.J if pyo.value(model.y[j]) > 0.5]`.
- Compute total cost and verify against the budget.
- Access the objective value via `pyo.value(model.obj)`.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(n_items))
model.J = pyo.Set(initialize=range(n_requirements))
# Define parameters (example using dictionaries)
model.cost = pyo.Param(model.I, initialize=cost_dict)
model.weight = pyo.Param(model.J, initialize=weight_dict)
model.budget = pyo.Param(initialize=budget)
model.coverage_map = pyo.Param(model.J, initialize=coverage_dict, mutable=True)

model.x = pyo.Var(model.I, domain=pyo.Binary)
model.y = pyo.Var(model.J, domain=pyo.Binary)

def budget_rule(model):
    return sum(model.cost[i] * model.x[i] for i in model.I) <= model.budget
model.budget_con = pyo.Constraint(rule=budget_rule)

def coverage_rule(model, j):
    return model.y[j] <= sum(model.x[i] for i in model.coverage_map[j])
model.coverage_con = pyo.Constraint(model.J, rule=coverage_rule)

model.obj = pyo.Objective(expr=sum(model.weight[j] * model.y[j] for j in model.J), sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, options={'seconds': 30})

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                              pyo.TerminationCondition.feasible)):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    covered = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
    total_cost = sum(pyo.value(model.cost[i]) for i in selected)
    print(f"RESULT:{pyo.value(model.obj)}")
else:
    print("Solver failed or no feasible solution found.")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of failed or incomplete solutions.
- Using exact equality (`== 1`) to test binary variable values from MILP solvers; use a tolerance (`> 0.5`) instead.
- Setting conflicting solver parameters (e.g., both `time_limit` and `max_time`), causing undefined behavior.
