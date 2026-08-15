---
name: MaximumCoverageUnderBudget
description: |
  Model and solve maximum weighted coverage problems with budget constraints using binary selection and coverage implication variables, with workflows for CP-SAT and Pyomo-based MIP solvers.
---

# Workflow 1 (CP-SAT for Binary Optimization)

## Modeling stage

### Strategy Overview
This workflow models the problem as a pure binary linear program suitable for constraint programming (CP-SAT) solvers. It uses a two-layer variable structure to decouple selection decisions from coverage outcomes, enabling clear logical constraints and a linear objective.

### Step 1 - Define Core Sets and Parameters
- Define the set of selectable items (e.g., facilities, projects) and the set of elements to be covered (e.g., areas, tasks).
- Map parameters: cost per selectable item, weight (e.g., population, value) per coverable element, and a coverage mapping indicating which items cover which elements.
- Define the total budget limit as a scalar parameter.

### Step 2 - Create Binary Decision Variables
- Create a binary variable `x[i]` for each selectable item `i` to represent the selection decision (1 if selected, 0 otherwise).
- Create a binary variable `y[e]` for each coverable element `e` to indicate its coverage status (1 if covered, 0 otherwise).

### Step 3 - Formulate Coverage Implication Logic
- For each element `e`, add a constraint linking coverage to selection: `y[e] <= sum(x[i] for i in coverage_map[e])`. This ensures an element can only be considered covered if at least one covering item is selected.
- (Optional) For logical equivalence, add a forward implication: `y[e] >= x[i]` for each covering item `i`. This is often redundant if the objective maximizes `y[e]` but can be included for model clarity.

### Step 4 - Apply the Budget Constraint
- Add a linear constraint: `sum(cost[i] * x[i] for i in items) <= budget`.

### Step 5 - Set the Weighted Maximization Objective
- Define the objective to maximize the total weighted coverage: `maximize sum(weight[e] * y[e] for e in elements)`.

### Formulation Template
```json
{
  "sets": [
    "items: set of selectable items",
    "elements: set of elements to cover"
  ],
  "parameters": [
    "cost[items]: cost of selecting each item",
    "weight[elements]: weight (value) of covering each element",
    "coverage_map[elements]: list of items covering each element",
    "budget: total available budget"
  ],
  "decision_variables": [
    "x[items]: binary, 1 if item is selected",
    "y[elements]: binary, 1 if element is covered"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[e] * y[e] for e in elements)"
  },
  "constraints": [
    "budget_limit: sum(cost[i] * x[i] for i in items) <= budget",
    "coverage_implication[elements]: y[e] <= sum(x[i] for i in coverage_map[e])"
  ]
}
```

### Common Pitfalls
- Forgetting to define the coverage mapping, leading to incorrect or empty constraints.
- Using a single variable to represent both selection and coverage, which complicates constraint logic.
- Omitting the budget constraint or mis-specifying the cost parameter indexing.

## Solving stage

### Strategy Overview
This stage uses the OR-Tools CP-SAT solver, designed for combinatorial problems with Boolean variables and linear constraints. It involves building the model, configuring solver parameters for performance and reproducibility, solving, and robustly extracting results.

### Step 1 - Instantiate Model and Create Variables
- Create a `cp_model.CpModel()` instance.
- Use `model.NewBoolVar(name)` to create Boolean variables for `x` and `y`. Use descriptive names like `f"x_{i}"` and `f"y_{e}"`.

### Step 2 - Add Constraints to the Model
- Add the budget constraint using `model.Add(sum(cost[i] * x[i] for i in items) <= budget)`.
- For each element `e`, add the coverage implication constraint: `model.Add(y[e] <= sum(x[i] for i in coverage_map[e]))`.

### Step 3 - Set Objective and Solver Parameters
- Set the maximization objective with `model.Maximize(sum(weight[e] * y[e] for e in elements))`.
- Create a `cp_model.CpSolver()` instance and configure key parameters:
  - `solver.parameters.max_time_in_seconds = time_limit` for predictable termination.
  - `solver.parameters.num_search_workers = num_workers` for parallel search.
  - `solver.parameters.random_seed = seed` for reproducibility.
  - `solver.parameters.relative_gap_limit = 0.0` if proven optimality is required.

### Step 4 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check the solution status: `cp_model.OPTIMAL` indicates a proven optimal solution; `cp_model.FEASIBLE` indicates a feasible but not necessarily optimal solution. Handle `cp_model.INFEASIBLE` or `cp_model.UNKNOWN` appropriately.

### Step 5 - Extract and Validate Solution
- If the status is `OPTIMAL` or `FEASIBLE`, extract the objective value via `solver.ObjectiveValue()`.
- Extract selected items by checking `solver.Value(x[i]) == 1`.
- Extract covered elements by checking `solver.Value(y[e]) == 1`.
- Optionally, compute derived metrics (total cost, coverage percentage) to validate against constraints.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in items}
y = {e: model.NewBoolVar(f"y_{e}") for e in elements}

# Budget constraint
model.Add(sum(cost[i] * x[i] for i in items) <= budget)

# Coverage constraints
for e in elements:
    model.Add(y[e] <= sum(x[i] for i in coverage_map[e]))

# Objective
model.Maximize(sum(weight[e] * y[e] for e in elements))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = III
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"RESULT:{solver.ObjectiveValue()}")
    selected = [i for i in items if solver.Value(x[i]) == III]
    covered = [e for e in elements if solver.Value(y[e]) == III]
    # ... output and validation
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not setting a time limit, causing the solver to run indefinitely on large instances.
- Forgetting to check solver status before extracting variable values, leading to runtime errors.
- Using `==` for float comparisons when checking variable values; use integer comparisons for Boolean variables.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to formulate the problem as a Mixed-Integer Program (MIP), which can be solved by external solvers like Gurobi, HiGHS, or CBC. It emphasizes structured model definition with Sets, Params, and Vars.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `items` and `elements`.
- Declare Pyomo `Param` objects for `cost` (indexed by `items`), `weight` (indexed by `elements`), and a scalar `budget`.
- Define the coverage relationship, typically as a dictionary mapping each element to a list of covering items.

### Step 2 - Declare Binary Variables
- Declare a Pyomo `Var` `build` indexed by `items` with `domain=pyo.Binary`.
- Declare a Pyomo `Var` `covered` indexed by `elements` with `domain=pyo.Binary`.

### Step 3 - Construct the Objective Function
- Define an `Objective` rule to maximize `sum(weight[e] * covered[e] for e in model.elements)`.

### Step 4 - Implement Constraints via Rules
- Define a `Constraint` rule for the budget: `sum(cost[i] * build[i] for i in model.items) <= budget`.
- Define a `Constraint` rule for each element `e` to enforce coverage logic: `covered[e] <= sum(build[i] for i in coverage_map[e])`.

### Step 5 - Instantiate the Concrete Model
- Populate the abstract model with concrete data (initialize Sets and Params) to create a `ConcreteModel` ready for solving.

### Formulation Template
```json
{
  "sets": [
    "items: set of selectable items",
    "elements: set of elements to cover"
  ],
  "parameters": [
    "cost[items]: cost of selecting each item",
    "weight[elements]: weight (value) of covering each element",
    "budget: total available budget"
  ],
  "decision_variables": [
    "build[items]: binary, 1 if item is selected",
    "covered[elements]: binary, 1 if element is covered"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[e] * covered[e] for e in elements)"
  },
  "constraints": [
    "budget_limit: sum(cost[i] * build[i] for i in items) <= budget",
    "coverage_rule[elements]: covered[e] <= sum(build[i] for i in coverage_map[e])"
  ]
}
```

### Common Pitfalls
- Confusing abstract and concrete model stages; parameters must be initialized before solving.
- Incorrectly indexing parameters or variables within constraint rules, causing KeyErrors.
- Defining the coverage mapping outside the model without properly linking it to constraint rules.

## Solving stage

### Strategy Overview
This stage involves sending the Pyomo model to a MIP solver (e.g., HiGHS, Gurobi) via a solver factory. It focuses on robust solver configuration, status checking, and solution extraction using Pyomo's result objects.

### Step 1 - Configure and Execute the Solver
- Create a solver instance using `SolverFactory(solver_name)`.
- Set solver options such as `time_limit`, `mip_rel_gap` (e.g., 0.0 for optimality), and `threads` for parallel processing.
- Call `results = solver.solve(model, options=options, load_solutions=False)` to avoid automatic loading.

### Step 2 - Check Solver Status and Termination Condition
- Inspect `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `SolverStatus.ok` and termination is `optimal` or `feasible`. Handle `infeasible` or `other` conditions appropriately.

### Step 3 - Load Solution into Model
- If the solve was successful, load the solution into the model using `model.solutions.load_from(results)`.

### Step 4 - Extract and Analyze Results
- Extract the objective value via `pyo.value(model.obj)`.
- Extract selected items by checking `pyo.value(model.build[i]) > 0.5`.
- Extract covered elements by checking `pyo.value(model.covered[e]) > 0.5`.
- Compute total cost and coverage percentage for validation.

### Step 5 - Output Standardized Results
- Print the objective value with a prefix like `RESULT:{value}`.
- Output lists of selected items and covered elements, along with derived statistics.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items)
model.elements = pyo.Set(initialize=elements)
model.cost = pyo.Param(model.items, initialize=cost_dict)
model.weight = pyo.Param(model.elements, initialize=weight_dict)
model.budget = budget

model.build = pyo.Var(model.items, domain=pyo.Binary)
model.covered = pyo.Var(model.elements, domain=pyo.Binary)

def obj_rule(m):
    return sum(m.weight[e] * m.covered[e] for e in m.elements)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

def budget_rule(m):
    return sum(m.cost[i] * m.build[i] for i in m.items) <= m.budget
model.budget_con = pyo.Constraint(rule=budget_rule)

def coverage_rule(m, e):
    return m.covered[e] <= sum(m.build[i] for i in coverage_map[e])
model.coverage_con = pyo.Constraint(model.elements, rule=coverage_rule)

# Solve with status / termination checks
solver = SolverFactory('highs')
options = {'time_limit': 30.0, 'mip_rel_gap': 0.0}
results = solver.solve(model, options=options, load_solutions=False)

status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    model.solutions.load_from(results)
    print(f"RESULT:{pyo.value(model.obj)}")
    selected = [i for i in model.items if pyo.value(model.build[i]) > 0.5]
    covered = [e for e in model.elements if pyo.value(model.covered[e]) > 0.5]
    # ... output and validation
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Using `load_solutions=True` and encountering errors when the solver returns no feasible solution.
- Not checking both solver status and termination condition, leading to misinterpretation of results.
- Comparing floating-point variable values directly to 1.0; use a tolerance (e.g., `> 0.5`) for binary decisions.
