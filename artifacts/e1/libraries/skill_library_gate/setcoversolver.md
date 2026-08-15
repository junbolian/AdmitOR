---
name: SetCoverSolver
description: |
  Model and solve weighted set cover problems using binary selection variables, coverage constraints, and cost minimization across multiple solver backends.
---

# Workflow 1 (OR-Tools MIP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' MIP solver interface for a direct, imperative model build. It is well-suited for rapid prototyping and deployment where a lightweight, self-contained Python library is preferred.

### Step 1 - Define Data Structures
- Map each selectable item (e.g., team, facility) to its cost.
- Map each element requiring coverage (e.g., location, task) to a list of items that can cover it.
- Use Python dictionaries for clarity and efficient constraint generation.

### Step 2 - Create Binary Variables
- For each item in the cost dictionary, create a binary decision variable `x[item]`.
- Use `solver.IntVar(0, 1, name)` to define variables with bounds 0 and 1.

### Step 3 - Formulate Coverage Constraints
- For each element in the coverage dictionary, add a linear constraint.
- The constraint ensures the sum of variables for covering items is at least 1: `sum(x[item] for item in coverage[element]) >= 1`.

### Step 4 - Set Minimization Objective
- Define the objective as the sum of cost[item] * x[item] over all items.
- Use `objective.SetCoefficient()` for each variable and call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "J: set of elements requiring coverage"
  ],
  "parameters": [
    "c_i: cost of selecting item i ∈ I",
    "S_j: set of items i ∈ I that can cover element j ∈ J"
  ],
  "decision_variables": [
    "x_i ∈ {0,1}: 1 if item i is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} c_i * x_i"
  },
  "constraints": [
    "Coverage: ∑_{i ∈ S_j} x_i ≥ 1, ∀ j ∈ J"
  ]
}
```

### Common Pitfalls
- Forgetting to check solver status before extracting solution values, leading to runtime errors.
- Using a dense coverage matrix when a sparse dictionary mapping is more efficient and readable.
- Neglecting to set solver time or iteration limits, potentially causing indefinite hangs on large instances.

## Solving stage

### Strategy Overview
Solve the MIP model using the SCIP or CBC backend via OR-Tools' wrapper. Configure solver limits, check termination status rigorously, and extract and validate the solution.

### Step 1 - Initialize Solver and Set Limits
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set practical limits: `solver.SetTimeLimit(30000)` for a 30-second timeout and `solver.SetNumThreads(4)` for parallel processing.

### Step 2 - Solve and Check Status
- Execute `status = solver.Solve()`.
- Verify the status is `OPTIMAL` or `FEASIBLE` before proceeding. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error messages.

### Step 3 - Extract and Validate Solution
- Retrieve selected items where `x[item].solution_value() > 0.5`.
- Compute the total cost from `objective.Value()`.
- Programmatically verify that every element is covered by at least one selected item to guard against solver anomalies.

### Code Usage
```python
# build model from formulation
import ortools.linear_solver.pywraplp as ort
solver = ort.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)

# Data placeholders
cost = {"item1": 5, "item2": 3}  # map item -> cost
coverage = {"element1": ["item1"], "element2": ["item1", "item2"]}  # map element -> list[item]

# Create variables
x = {}
for item in cost:
    x[item] = solver.IntVar(0, 1, f"x_{item}")

# Add coverage constraints
for element, covering_items in coverage.items():
    solver.Add(solver.Sum(x[item] for item in covering_items) >= 1)

# Set objective
objective = solver.Objective()
for item, c in cost.items():
    objective.SetCoefficient(x[item], c)
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [item for item in cost if x[item].solution_value() > 0.5]
    total_cost = objective.Value()
    # Validation loop (optional but recommended)
    for element, covering_items in coverage.items():
        if not any(x[item].solution_value() > 0.5 for item in covering_items):
            print(f"Warning: element {element} is not covered.")
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Assuming `solution_value()` returns exactly 0 or 1; use a tolerance (e.g., > 0.5) due to floating-point precision.
- Omitting the validation step, which can miss subtle infeasibilities in the solver's returned solution.
- Not setting a time limit, which can cause the process to stall on difficult problem instances.

# Workflow 2 (Pyomo with CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a declarative model definition, separating model construction from solver calls. It is ideal for integration into larger optimization systems and for users familiar with algebraic modeling languages.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo Sets for items (`model.I`) and elements (`model.J`).
- Use `pyo.Param` for costs, initialized from a data dictionary.
- Represent coverage relationships via a direct Python dictionary accessed within constraint rules, avoiding complex Pyomo indexed parameters.

### Step 2 - Create Binary Variables
- Define `model.x` as a `pyo.Var` indexed over `model.I`, with domain `pyo.Binary`.

### Step 3 - Formulate Coverage Constraints via Rule
- Define a constraint rule `def cover_rule(model, j):`.
- Inside the rule, sum `model.x[i]` for all `i` in the external coverage dictionary for element `j`.
- Add the constraint to the model indexed over `model.J`.

### Step 4 - Define Objective Function
- Define the objective as `sum(model.cost[i] * model.x[i] for i in model.I)`.
- Use `pyo.Objective(expr=..., sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "J: set of elements requiring coverage"
  ],
  "parameters": [
    "c_i: cost of selecting item i ∈ I"
  ],
  "decision_variables": [
    "x_i ∈ {0,1}: 1 if item i is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} c_i * x_i"
  },
  "constraints": [
    "Coverage: ∑_{i ∈ S_j} x_i ≥ 1, ∀ j ∈ J, where S_j is defined externally"
  ]
}
```

### Common Pitfalls
- Overcomplicating the model by using Pyomo `Param` objects for sparse coverage data; a plain dictionary is often simpler.
- Defining constraint rules that incorrectly capture closure over mutable data, leading to incorrect constraints.
- Not verifying that all necessary sets and parameters are initialized before creating the objective or constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via the `SolverFactory`. Configure solver options, check termination conditions, and extract results using Pyomo's value functions.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory("cbc")`.
- Set options: `solver.options['seconds'] = 30` for time limit, `solver.options['threads'] = 4`.

### Step 2 - Solve and Inspect Results
- Execute `results = solver.solve(model, tee=False)`.
- Check the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`). Accept `optimal` or `feasible` conditions.

### Step 3 - Extract and Verify Solution
- Extract selected items where `pyo.value(model.x[i]) > 0.5`.
- Obtain the objective value via `pyo.value(model.obj)`.
- Perform a post-solve verification loop using the external coverage dictionary to ensure all elements are covered.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()

# Data placeholders
cost_data = {"item1": 5, "item2": 3}
coverage_data = {"element1": ["item1"], "element2": ["item1", "item2"]}

# Sets
model.I = pyo.Set(initialize=cost_data.keys())  # Items
model.J = pyo.Set(initialize=coverage_data.keys())  # Elements

# Parameters
model.cost = pyo.Param(model.I, initialize=cost_data)

# Variables
model.x = pyo.Var(model.I, domain=pyo.Binary)

# Objective
model.obj = pyo.Objective(
    expr=sum(model.cost[i] * model.x[i] for i in model.I),
    sense=pyo.minimize
)

# Constraints
def cover_rule(model, j):
    # Access external coverage_data dictionary
    return sum(model.x[i] for i in coverage_data[j]) >= 1
model.cover = pyo.Constraint(model.J, rule=cover_rule)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options['seconds'] = 30
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = pyo.value(model.obj)
    # Validation
    for j in model.J:
        if not any(pyo.value(model.x[i]) > 0.5 for i in coverage_data[j]):
            print(f"Warning: element {j} is not covered.")
else:
    print(f"Solver failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (found optimal solution); both must be checked.
- Using `model.x[i]` directly in logical checks without calling `pyo.value()`, which returns a Pyomo expression object, not a number.
- Forgetting that the coverage dictionary used in the rule must be in scope and unchanged after model creation.
