---
name: Set Cover Optimization
description: |
  Model and solve weighted set cover problems using binary selection variables, coverage constraints, and a minimize weighted sum objective.

---

# Workflow 1 (MIP Solver with OR-Tools)

## Modeling stage

### Strategy Overview
Model the problem as a standard binary integer program (BIP) using a direct matrix-free representation of the coverage relationship, suitable for solvers like SCIP or CBC.

### Step 1 - Define Problem Data
- Identify the set of selectable items (e.g., `items`) and the set of requirements to be covered (e.g., `requirements`).
- Define a cost parameter `cost[i]` for each item `i`.
- Define a coverage mapping `coverage[r]` which returns a list of items that satisfy requirement `r`.

### Step 2 - Formulate Binary Variables
- Create a binary decision variable `x[i]` for each item `i`, where `x[i] = 1` indicates the item is selected.

### Step 3 - Formulate Coverage Constraints
- For each requirement `r`, create a constraint that the sum of selected covering items is at least one: `sum(x[i] for i in coverage[r]) >= 1`.

### Step 4 - Define Weighted Objective
- Formulate the objective to minimize the total weighted sum: `min sum(cost[i] * x[i] for i in items)`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "requirements"
  ],
  "parameters": [
    "cost[items]",
    "coverage[requirements] -> list of items"
  ],
  "decision_variables": [
    "x[items] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    "for each r in requirements: sum(x[i] for i in coverage[r]) >= 1"
  ]
}
```

### Common Pitfalls
- Forgetting to ensure the coverage mapping is defined for every requirement, leading to missing constraints.
- Using dense matrix representations for sparse coverage, which wastes memory and slows model building.

## Solving stage

### Strategy Overview
Solve the BIP using the OR-Tools wrapper for SCIP or CBC, focusing on efficient model construction, robust status checking, and solution validation.

### Step 1 - Initialize Solver and Variables
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Create binary variables using `solver.IntVar(0, 1, name)` in a loop over all items.

### Step 2 - Build Objective and Constraints
- Build the objective by setting coefficients for each variable.
- Create coverage constraints by iterating over the `coverage` mapping and adding coefficients for each covering item.

### Step 3 - Solve and Check Status
- Call `solver.Solve()` and capture the status.
- Check for `OPTIMAL` or `FEASIBLE` status before proceeding to extract the solution.

### Step 4 - Extract and Validate Solution
- Extract selected items by thresholding variable solution values (e.g., `> 0.5`).
- Compute the total cost from the objective value.
- Optionally, verify that all coverage constraints are satisfied by the selected items.

### Code Usage
```python
# build model from formulation
import ortools.linear_solver.pywraplp as ort

# Define data
items = [...]  # list of item identifiers
costs = {...}  # dict: item -> cost
coverage = {...}  # dict: requirement -> list of covering items

# Create solver
solver = ort.Solver.CreateSolver("SCIP")
x = {}
for i in items:
    x[i] = solver.IntVar(0, 1, f"x_{i}")

# Set objective
objective = solver.Objective()
for i in items:
    objective.SetCoefficient(x[i], costs[i])
objective.SetMinimization()

# Add coverage constraints
for req, covering_items in coverage.items():
    constraint = solver.Constraint(1, solver.infinity(), f"cover_{req}")
    for i in covering_items:
        constraint.SetCoefficient(x[i], 1)

# solve with status / termination checks
status = solver.Solve()
if status in (ort.Solver.OPTIMAL, ort.Solver.FEASIBLE):
    selected = [i for i in items if x[i].solution_value() > 0.5]
    total_cost = objective.Value()
    # Verification (optional)
    for req, covering_items in coverage.items():
        if sum(x[i].solution_value() for i in covering_items) < 0.5:
            print(f"Warning: Requirement {req} not covered.")
else:
    print("No optimal or feasible solution found.")
```

### Common Pitfalls
- Not checking solver status, leading to errors when trying to access solution values from an infeasible or unbounded model.
- Using a loose tolerance (e.g., `> 0`) instead of `> 0.5` to interpret binary variables, which can misclassify fractional values from some solvers.

# Workflow 2 (Pyomo with High-Level Solver)

## Modeling stage

### Strategy Overview
Model the problem using the Pyomo modeling language, leveraging its abstract set and parameter definitions for clarity, and target solvers like HiGHS or CBC via SolverFactory.

### Step 1 - Define Abstract Sets and Parameters
- Use `pyo.Set()` to define sets for `items` and `requirements`.
- Use `pyo.Param()` to define `cost` indexed by `items` and a sparse `coverage` parameter (or rule) indicating which items cover each requirement.

### Step 2 - Declare Binary Variables
- Declare a `pyo.Var` indexed by `items` with domain `pyo.Binary`.

### Step 3 - Construct Coverage Constraints via Rules
- Define a constraint rule that, for each requirement, sums the variables of covering items and enforces a lower bound of 1.

### Step 4 - Define Objective Expression
- Define the objective as a `pyo.Objective` with sense `minimize` and expression as the sum of cost-weighted variables.

### Formulation Template
```json
{
  "sets": [
    "model.items",
    "model.requirements"
  ],
  "parameters": [
    "model.cost[model.items]",
    "model.covers[model.requirements, model.items] (binary)"
  ],
  "decision_variables": [
    "model.x[model.items] ∈ Binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[i] * model.x[i] for i in model.items)"
  },
  "constraints": [
    "def cover_rule(model, r): return sum(model.covers[r,i] * model.x[i] for i in model.items) >= 1"
  ]
}
```

### Common Pitfalls
- Defining the coverage parameter as a dense matrix when the relationship is sparse, causing unnecessary memory overhead.
- Incorrectly indexing parameters within constraint rules, leading to `KeyError` or incorrect constraint generation.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., HiGHS), configure solver options for performance, handle solver termination gracefully, and validate the solution.

### Step 1 - Instantiate Model and Solver
- Create a `pyo.ConcreteModel()` and populate it with sets, parameters, variables, constraints, and objective.
- Create a solver object using `pyo.SolverFactory("highs")`.

### Step 2 - Configure Solver and Solve
- Set solver options such as time limit and MIP gap (e.g., `solver.options["time_limit"] = 30`).
- Call `solver.solve(model, tee=False)` and capture the results object.

### Step 3 - Check Termination and Load Solution
- Check the solver status and termination condition from the results object.
- If the solution is acceptable, load it into the model using `model.solutions.load_from(results)`.

### Step 4 - Extract, Validate, and Report
- Extract selected items by evaluating `pyo.value(model.x[i]) > 0.5`.
- Compute the objective value and verify coverage constraints.
- Output results in a structured format for easy parsing.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items_list)
model.requirements = pyo.Set(initialize=reqs_list)

# Parameters
model.cost = pyo.Param(model.items, initialize=cost_dict)
# Assume coverage_dict is {(r,i): 1 if i covers r}
model.covers = pyo.Param(model.requirements, model.items, initialize=coverage_dict, default=0)

# Variables
model.x = pyo.Var(model.items, domain=pyo.Binary)

# Constraints
def cover_rule(model, r):
    return sum(model.covers[r, i] * model.x[i] for i in model.items) >= 1
model.cover = pyo.Constraint(model.requirements, rule=cover_rule)

# Objective
model.obj = pyo.Objective(
    expr=sum(model.cost[i] * model.x[i] for i in model.items),
    sense=pyo.minimize
)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
results = solver.solve(model, tee=False)

# Check status
if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    # Load solution
    model.solutions.load_from(results)
    selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
    total_cost = pyo.value(model.obj)
    # Verification
    for r in model.requirements:
        cover_sum = sum(pyo.value(model.covers[r, i]) * pyo.value(model.x[i]) for i in model.items)
        if cover_sum < 0.5:
            print(f"Warning: Requirement {r} not covered.")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Forgetting to load the solution into the model after solving, leading to access of stale variable values.
- Not handling the case where the solver returns a feasible but non-optimal solution, which may require different post-processing.
