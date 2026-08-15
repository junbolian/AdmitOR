---
name: Linear Allocation with Exact Demand Satisfaction
description: |
  Model and solve linear allocation problems where continuous, non-negative quantities must exactly meet known demands to maximize total linear profit.

---

# Workflow 1 (Pyomo with Highs/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define sets, parameters, and variables, creating a structured and solver-agnostic model. It is well-suited for problems with clear index sets and tabular data.

### Step 1 - Define Index Sets
- Declare `Set` objects for the distinct categories of items being allocated (e.g., `products`) and their destinations (e.g., `destinations`).
- Initialize these sets with lists of unique identifiers to establish the model's dimensions.

### Step 2 - Parameterize Profit and Demand
- Use `Param` components, indexed by the Cartesian product of the defined sets, to store profit coefficients and demand values.
- Store data in a dictionary with tuple keys `(item, destination)` for direct mapping to decision variables.

### Step 3 - Declare Decision Variables
- Create a `Var` component indexed over the same product of sets.
- Specify the domain as `NonNegativeReals` to represent continuous, non-negative allocation quantities.

### Step 4 - Formulate Objective and Constraints
- Define the objective as a `sum` of `profit[i,j] * x[i,j]` across all indices, with `sense=maximize`.
- Add a `Constraint` for each `(item, destination)` pair enforcing `x[i,j] == demand[i,j]` to satisfy exact demand.

### Formulation Template
```json
{
  "sets": ["items", "destinations"],
  "parameters": [
    {"name": "profit", "indexed_by": ["items", "destinations"]},
    {"name": "demand", "indexed_by": ["items", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": ["items", "destinations"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i,j] * x[i,j] for i in items for j in destinations)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "x[i,j] == demand[i,j]", "for_all": ["i in items", "j in destinations"]}
  ]
}
```

### Common Pitfalls
- Forgetting to initialize `Set` objects before using them to index parameters or variables, causing runtime errors.
- Using mismatched index orders between parameter dictionaries and variable declarations, leading to incorrect coefficient mapping.
- Overlooking that equality constraints make the solution deterministic; the solver's role is to confirm feasibility, not to optimize.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an efficient LP solver (Highs or CBC) via the `SolverFactory`. The focus is on robust solving, status checking, and solution validation.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object using `SolverFactory("highs")` or `SolverFactory("cbc")`.
- Configure options such as a time limit (`"seconds"`) to prevent indefinite runs, especially for larger instances.

### Step 2 - Execute Solve and Check Status
- Call `solver.solve(model, tee=False)` to execute the optimization quietly.
- Systematically check both `SolverStatus.ok` and `TerminationCondition` (optimal or feasible) before extracting results.

### Step 3 - Extract and Validate Solution
- Compute the total objective value using `pyo.value(model.obj)`.
- Iterate through all variable indices using the model's sets to extract allocation values.
- Perform a manual verification by recalculating the objective from extracted variable values and comparing it to the solver's reported value.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (function implementing steps from Modeling stage)
model = build_allocation_model(item_list, destination_list, profit_dict, demand_dict)

# Configure and run solver
solver = pyo.SolverFactory("highs")  # or "cbc"
solver.options["seconds"] = 30
results = solver.solve(model, tee=False)

# Check termination status
status = results.solver.status
termination = results.solver.termination_condition

if (status == SolverStatus.ok and
    termination in {TerminationCondition.optimal, TerminationCondition.feasible}):
    total_profit = float(pyo.value(model.obj))
    # Extract solution
    solution = {}
    for i in model.items:
        for j in model.destinations:
            val = pyo.value(model.x[i, j])
            solution[(i, j)] = val
    # Optional: Direct verification for equality-constrained problems
    calculated_profit = sum(profit_dict[i, j] * demand_dict[i, j] for i in model.items for j in model.destinations)
    # ... compare calculated_profit with total_profit
else:
    print(f"Solver failed. Status: {status}, Termination: {termination}")
```

### Common Pitfalls
- Proceeding to extract variable values without confirming the solver status is `ok` and termination is `optimal` or `feasible`.
- Omitting the manual verification step, which can catch errors in objective formulation or parameter mapping.
- Setting `tee=True` without need, cluttering the output for straightforward LPs.

# Workflow 2 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools linear solver API for direct, imperative model construction. It is ideal for rapid prototyping and problems where the model structure is simple and does not require the abstraction of a modeling language.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver('GLOP')`) for linear programming.
- Organize profit and demand data as nested dictionaries or 2D lists keyed by `(item, destination)` for clarity.

### Step 2 - Create Decision Variables
- Use a loop over all `(item, destination)` pairs to create continuous, non-negative variables via `solver.NumVar(lb, ub, name)`.
- Store variables in a dictionary with tuple keys matching the parameter data structure.

### Step 3 - Build Linear Objective
- Initialize the objective expression with `solver.Objective()`.
- Iterate through all variable indices, using `objective.SetCoefficient(var, coefficient)` to add the corresponding profit term.

### Step 4 - Add Exact Demand Constraints
- For each `(item, destination)` pair, create a linear equality constraint: `solver.Constraint(demand_value, demand_value)`.
- Add the single decision variable to this constraint with a coefficient of 1.

### Formulation Template
```json
{
  "sets": ["items", "destinations"],
  "parameters": [
    {"name": "profit", "indexed_by": ["items", "destinations"]},
    {"name": "demand", "indexed_by": ["items", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": ["items", "destinations"], "domain": "Continuous >= 0"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i,j] * x[i,j] for i in items for j in destinations)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "x[i,j] == demand[i,j]", "for_all": ["i in items", "j in destinations"]}
  ]
}
```

### Common Pitfalls
- Creating variables or constraints inside misaligned loops, leading to incorrect indexing.
- Forgetting to set the objective sense (`Maximize` or `Minimize`) after building the expression.
- Not recognizing that with only equality constraints, the solution is fixed; the solve step merely validates feasibility.

## Solving stage

### Strategy Overview
Solve the constructed model using the OR-Tools solver backend. The process involves executing the solve, checking the result status, and then extracting and verifying the solution values.

### Step 1 - Execute Solve and Check Result
- Call `solver.Solve()` to run the optimization.
- Check the return status (e.g., `pywraplp.Solver.OPTIMAL` or `FEASIBLE`) before proceeding.

### Step 2 - Extract Solution and Compute Objective
- If the solve was successful, iterate through the dictionary of variables and retrieve their values using `.solution_value()`.
- Calculate the total objective value by summing `profit[i,j] * variable_value` across all indices.

### Step 3 - Validate Against Deterministic Outcome
- For problems with only equality constraints, independently compute the expected profit as the sum of `profit[i,j] * demand[i,j]`.
- Compare this computed value with the solver's objective value as a sanity check.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')
solver.set_time_limit_seconds(30)

# Assume profit_dict and demand_dict are predefined with tuple keys (i, j)
items = list_of_items
destinations = list_of_destinations

# Create variables
x = {}
for i in items:
    for j in destinations:
        x[(i, j)] = solver.NumVar(0, solver.infinity(), f'x_{i}_{j}')

# Build objective
objective = solver.Objective()
for (i, j), var in x.items():
    objective.SetCoefficient(var, profit_dict[(i, j)])
objective.SetMaximization()

# Add equality constraints
for (i, j), var in x.items():
    constraint = solver.Constraint(demand_dict[(i, j)], demand_dict[(i, j)])
    constraint.SetCoefficient(var, 1)

# Solve
result_status = solver.Solve()

# Check status and extract solution
if result_status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_profit = objective.Value()
    solution = {}
    for (i, j), var in x.items():
        val = var.solution_value()
        solution[(i, j)] = val
    # Validation for deterministic case
    calculated_profit = sum(profit_dict[(i, j)] * demand_dict[(i, j)] for i in items for j in destinations)
    # ... compare calculated_profit with total_profit
else:
    print(f"Solver did not find an optimal or feasible solution. Status: {result_status}")
```

### Common Pitfalls
- Misinterpreting the solver status; `OPTIMAL` is returned even for feasible equality-constrained problems, but the solution is predetermined.
- Not using consistent loops for variable creation, objective building, and constraint addition, risking index mismatches.
- Omitting the validation step, which is crucial for confirming the model correctly encodes the fixed-demand scenario.
