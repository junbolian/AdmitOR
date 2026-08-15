---
name: BudgetedCoverageSelection
description: |
  A skill for modeling and solving budget-constrained coverage problems with binary selection and coverage variables, using implication constraints to link them, across multiple solver backends.

---
# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the problem using Google OR-Tools' CP-SAT solver, which is designed for discrete optimization with Boolean logic. The formulation uses binary variables for both selection and coverage, with linear constraints to enforce budget and coverage implications.

### Step 1 - Define Variables and Data Structures
- Create two lists of binary decision variables: `x[i]` for selecting item `i` and `y[j]` for covering unit `j`.
- Store coverage relationships in a list-of-lists `coverage_map`, where `coverage_map[j]` contains indices of items that can cover unit `j`.
- Define parameters as Python lists or arrays: `costs[i]`, `weights[j]`, and a scalar `budget`.

### Step 2 - Build Implication and Budget Constraints
- For each coverage unit `j`, add a linear constraint: `y[j] <= sum(x[i] for i in coverage_map[j])`. This ensures coverage is only possible if at least one covering item is selected.
- Add a knapsack-style budget constraint: `sum(costs[i] * x[i] for i in items) <= budget`.

### Step 3 - Set the Objective
- Define the objective to maximize the weighted sum of coverage: `Maximize(sum(weights[j] * y[j] for j in coverage_units))`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items (e.g., towers, facilities).",
    "J: Set of coverage units (e.g., regions, customers)."
  ],
  "parameters": [
    "cost_i: Cost of selecting item i ∈ I.",
    "weight_j: Weight/benefit of covering unit j ∈ J.",
    "budget: Total available budget.",
    "coverage_map_j: List of item indices i ∈ I that can cover unit j ∈ J."
  ],
  "decision_variables": [
    "x_i: Binary, 1 if item i ∈ I is selected.",
    "y_j: Binary, 1 if unit j ∈ J is covered."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight_j * y_j for j in J)"
  },
  "constraints": [
    "Budget: sum(cost_i * x_i for i in I) <= budget",
    "Coverage Implication: y_j <= sum(x_i for i in coverage_map_j) for all j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce `y_j` as binary; it must be a `BoolVar` to correctly represent coverage.
- Using `y_j == sum(...)` instead of `y_j <= sum(...)`, which incorrectly forces coverage if an item is selected.
- Not pre-computing `coverage_map` efficiently, leading to slow constraint generation for large problems.

## Solving stage

### Strategy Overview
Solving involves configuring the CP-SAT solver for performance and reproducibility, executing the model, and rigorously checking the solution status before extracting and verifying results.

### Step 1 - Configure Solver Parameters
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 8`, `solver.parameters.random_seed = 42`.
- For optimality, set `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Execute the solver: `status = solver.Solve(model)`.
- Check for an acceptable status: `if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):`. Handle each case appropriately (e.g., log if only feasible).

### Step 3 - Extract and Verify Solution
- Extract selected items: `selected_items = [i for i in I if solver.Value(x[i]) == 1]`.
- Extract covered units: `covered_units = [j for j in J if solver.Value(y[j]) == 1]`.
- Retrieve the objective value: `obj_val = solver.ObjectiveValue()`.
- Perform verification: Calculate total cost from `selected_items` and confirm it's within budget; verify that for each `covered_units[j]`, at least one item in `coverage_map[j]` is selected.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
x = [model.NewBoolVar(f'x_{i}') for i in range(n_items)]
y = [model.NewBoolVar(f'y_{j}') for j in range(n_units)]

# Budget constraint
model.Add(sum(costs[i] * x[i] for i in range(n_items)) <= budget)

# Coverage implication constraints
for j in range(n_units):
    model.Add(y[j] <= sum(x[i] for i in coverage_map[j]))

# Objective
model.Maximize(sum(weights[j] * y[j] for j in range(n_units)))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in range(n_items) if solver.Value(x[i]) == 1]
    covered = [j for j in range(n_units) if solver.Value(y[j]) == 1]
    print(f'RESULT:{solver.ObjectiveValue()}')
    # ... verification and output
else:
    print('No solution found.')
```

### Common Pitfalls
- Not setting `num_search_workers` for parallel speedup on multi-core machines.
- Misinterpreting `FEASIBLE` as sub-optimal; it may be the best solution found within time limits.
- Forgetting to use `solver.Value()` on variables to get the solution assignment.

# Workflow 2 (MILP with Pyomo and CBC/Gurobi)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model formulation, which can be solved by various MILP solvers (e.g., CBC, Gurobi). It emphasizes clear set and parameter definitions, making the model easily adaptable to different data scales and solver backends.

### Step 1 - Define Abstract Sets and Parameters
- Create Pyomo `Set` objects for items `model.I` and coverage units `model.J`.
- Define `Param` objects for `model.cost`, `model.weight`, and scalar `model.budget`.
- Store coverage relationships in a parameter or rule, e.g., a dictionary `coverage_map` mapping unit `j` to a list of items.

### Step 2 - Declare Binary Variables and Constraints
- Declare binary variables: `model.x = Var(model.I, domain=Binary)` for selection and `model.y = Var(model.J, domain=Binary)` for coverage.
- Implement the budget constraint as a single `Constraint` rule summing `cost[i] * x[i]`.
- Implement coverage implication constraints via a `Constraint` rule over `model.J`: `model.y[j] <= sum(model.x[i] for i in coverage_map[j])`.

### Step 3 - Define the Maximization Objective
- Create an `Objective` rule: `sum(weight[j] * model.y[j] for j in model.J)` with `sense=maximize`.

### Formulation Template
```json
{
  "sets": [
    "I: Pyomo Set of selectable items.",
    "J: Pyomo Set of coverage units."
  ],
  "parameters": [
    "cost: Pyomo Param indexed by I, for item costs.",
    "weight: Pyomo Param indexed by J, for coverage weights.",
    "budget: Scalar numeric budget.",
    "coverage_map: Python dictionary mapping unit j ∈ J to list of items i ∈ I."
  ],
  "decision_variables": [
    "x: Pyomo Var indexed by I, domain=Binary.",
    "y: Pyomo Var indexed by J, domain=Binary."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[j] * y[j] for j in J)"
  },
  "constraints": [
    "budget_constraint: sum(cost[i] * x[i] for i in I) <= budget",
    "coverage_constraint_j: y[j] <= sum(x[i] for i in coverage_map[j]) for all j in J"
  ]
}
```

### Common Pitfalls
- Initializing `Param` objects without a proper `initialize` function, leading to missing data errors.
- Using Python's `sum` inside Pyomo rules without `pyo.summation` or generator expressions; Pyomo's `sum()` is required.
- Defining `coverage_map` inefficiently within the model rule, causing repeated calculations; pre-compute it externally.

## Solving stage

### Strategy Overview
Solving involves selecting a MILP solver (CBC for open-source, Gurobi for commercial), configuring it for deterministic performance, and handling solver status and termination conditions robustly before parsing the solution.

### Step 1 - Select and Configure Solver
- Choose a solver: `solver = pyo.SolverFactory('cbc')` or `'gurobi'`.
- Set solver options: For CBC: `solver.options = {'ratio': 0.0, 'seconds': 30, 'threads': 4}`. For Gurobi: `solver.options = {'MIPGap': 0.0, 'TimeLimit': 30, 'Threads': 4, 'Seed': 42}`.

### Step 2 - Solve and Inspect Termination
- Execute: `results = solver.solve(model, tee=False)`.
- Check both high-level status and termination condition: `if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):`.

### Step 3 - Extract Solution and Output Metrics
- Extract selected items: `selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]`.
- Extract covered units: `covered_units = [j for j in model.J if pyo.value(model.y[j]) > 0.5]`.
- Compute total cost and verify against budget.
- Output a structured result, e.g., a dictionary with status, objective value, and solution lists.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=units)
model.cost = pyo.Param(model.I, initialize=cost_dict)
model.weight = pyo.Param(model.J, initialize=weight_dict)
model.budget = budget

model.x = pyo.Var(model.I, domain=pyo.Binary)
model.y = pyo.Var(model.J, domain=pyo.Binary)

def budget_rule(m):
    return sum(m.cost[i] * m.x[i] for i in m.I) <= m.budget
model.budget_con = pyo.Constraint(rule=budget_rule)

def coverage_rule(m, j):
    return m.y[j] <= sum(m.x[i] for i in coverage_map[j])
model.coverage_con = pyo.Constraint(model.J, rule=coverage_rule)

model.obj = pyo.Objective(expr=sum(m.weight[j] * m.y[j] for j in m.J), sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options = {'ratio': 0.0, 'seconds': —, 'threads': —}
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    covered = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
    print(f'RESULT:{pyo.value(model.obj)}')
    # ... verification and output
else:
    print({'status': 'failure', 'reason': results.solver.termination_condition})
```

### Common Pitfalls
- For CBC, setting `ratio=-1` is invalid; use `0.0` for optimality.
- Not checking both `solver.status` and `termination_condition`, which can mask infeasible or error states.
- Using `pyo.value(var)` without the `> 0.5` tolerance for binary variables, risking floating-point precision issues.
