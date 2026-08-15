---
name: AllocationWithExactDemandLP
description: |
  Model and solve linear allocation problems with exact demand satisfaction, using continuous non-negative variables and equality constraints, maximizing total linear profit.
---

# Workflow 1 (Pyomo with Highs/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define sets, parameters, variables, and constraints in a structured, solver-agnostic manner. It is well-suited for problems where the exact demand constraints fix all variables, turning optimization into a verification step, and facilitates easy extension to more complex variants.

### Step 1 - Define Core Index Sets
- Identify and list all source and destination dimensions for the allocation (e.g., `sources`, `destinations`).
- Initialize Pyomo `Set` objects with these lists to serve as the foundation for indexed components.

### Step 2 - Structure Indexed Parameters
- Store profit coefficients and demand requirements as Python dictionaries, keyed by `(source, destination)` tuples.
- Ensure parameter indexing aligns perfectly with the defined sets for consistent referencing in constraints and the objective.

### Step 3 - Create Allocation Variables
- Define a Pyomo `Var` indexed over the source and destination sets.
- Set the domain to `pyo.NonNegativeReals` to enforce non-negativity for the continuous allocation quantities.

### Step 4 - Formulate Exact Demand Constraints
- Add a `ConstraintList` to the model.
- For each `(source, destination)` pair, append an equality constraint fixing the allocation variable to the corresponding demand value.

### Step 5 - Build Linear Maximization Objective
- Construct the objective expression as the sum of `profit[source, destination] * variable[source, destination]` over all index pairs.
- Set the sense to `pyo.maximize`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "profit", "indexed_by": ["source", "destination"], "type": "float"},
    {"name": "demand", "indexed_by": ["source", "destination"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": ["source", "destination"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i,j] * x[i,j] for i in sources for j in destinations)"
  },
  "constraints": [
    {"name": "exact_demand", "expression": "x[i,j] == demand[i,j]", "indexed_by": ["source", "destination"]}
  ]
}
```

### Common Pitfalls
- Using mismatched indices between parameters and variables, leading to `KeyError` or incorrect constraint definitions.
- Forgetting to set the variable domain to non-negative, which may allow invalid negative allocations.
- Overcomplicating the model when all variables are fixed by equality constraints; the primary value is verification and framework consistency.

## Solving stage

### Strategy Overview
This stage configures a linear solver (Highs or CBC) via Pyomo's `SolverFactory`, solves the model, and rigorously checks solver status and termination conditions before extracting and validating results.

### Step 1 - Configure Solver with Options
- Instantiate the solver using `pyo.SolverFactory("highs")` or `pyo.SolverFactory("cbc")`.
- Set appropriate options, such as a time limit (`seconds`) or tolerance (`ratio`), to control solver behavior.

### Step 2 - Solve and Capture Results
- Call `solver.solve(model, tee=False)` to execute the optimization without verbose solver output.
- Store the returned `results` object for status inspection.

### Step 3 - Check Solver Status and Termination
- Verify `results.solver.status` equals `SolverStatus.ok`.
- Check `results.solver.termination_condition` is either `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 4 - Extract and Validate Solution
- If checks pass, retrieve the objective value using `pyo.value(model.obj)`.
- Optionally, iterate over variables to extract allocation values with `pyo.value(model.x[i,j])`.
- Cross-validate by manually recomputing the objective from extracted values and demand parameters.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Assume 'model' is built according to the Modeling stage steps
# 1. Configure solver
solver = pyo.SolverFactory("highs")  # Alternative: "cbc"
solver.options["seconds"] = 30

# 2. Solve
results = solver.solve(model, tee=False)

# 3. Check status
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_profit = float(pyo.value(model.obj))
    # Optional: Extract variable values
    # for i in model.sources:
    #     for j in model.destinations:
    #         alloc = pyo.value(model.x[i, j])
    #         print(f"x[{i},{j}] = {alloc}")
else:
    raise RuntimeError(f"Solver failed: status={status}, termination={term}")
```

### Common Pitfalls
- Proceeding to extract values without checking termination condition, potentially using results from an infeasible or non-optimal solve.
- Misinterpreting the trivial case where the objective is predetermined; the solver's role is verification.
- Omitting error handling for solver failures, which can cause silent incorrect outputs.

# Workflow 2 (OR-Tools with GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools linear solver wrapper, constructing the model through direct coefficient setting in a more imperative style. It is efficient for straightforward LP problems and provides clear, low-level control over variable and constraint creation.

### Step 1 - Map Problem Dimensions
- Define lists for source and destination indices (e.g., `products`, `schools`).
- These lists will be used to iterate and create variables and constraints.

### Step 2 - Create Decision Variable Dictionary
- Instantiate an empty dictionary to hold decision variables.
- For each `(source, destination)` pair, create a continuous, non-negative variable using `solver.NumVar(0, solver.infinity(), name)`.
- Use a tuple `(source, destination)` as the dictionary key for clarity and easy access.

### Step 3 - Build Linear Objective
- Initialize the objective with `solver.Objective()`.
- Iterate over all variable keys, setting each variable's coefficient in the objective to its corresponding profit value using `objective.SetCoefficient(var, coeff)`.
- Set the objective sense to maximization.

### Step 4 - Add Exact Demand Constraints
- For each `(source, destination)` pair, create a linear constraint using `solver.Constraint(demand_value, demand_value)`.
- Add the corresponding allocation variable to this constraint with a coefficient of 1.0 using `constraint.SetCoefficient(var, 1.0)`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "profit", "indexed_by": ["source", "destination"], "type": "float"},
    {"name": "demand", "indexed_by": ["source", "destination"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": ["source", "destination"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i,j] * x[i,j])"
  },
  "constraints": [
    {"name": "exact_demand", "expression": "x[i,j] == demand[i,j]", "indexed_by": ["source", "destination"]}
  ]
}
```

### Common Pitfalls
- Using inconsistent naming or indexing between variables and parameters, causing coefficient mismatch.
- Neglecting to set the upper bound of `NumVar` to `solver.infinity()` for truly unbounded non-negative variables.
- Adding constraints in a different order than variable creation, which is harmless but can reduce code clarity.

## Solving stage

### Strategy Overview
This stage involves invoking the GLOP linear solver, checking for an optimal solution status, and then extracting the objective value and variable solutions. The focus is on the solver's native status codes and direct value retrieval.

### Step 1 - Initialize Solver and Build Model
- Create a solver instance with `pywraplp.Solver.CreateSolver('GLOP')`.
- Construct the model by following the steps from the modeling stage (defining variables, objective, constraints).

### Step 2 - Execute Solve
- Call `solver.Solve()` to run the optimization.
- The method returns a status code (e.g., `pywraplp.Solver.OPTIMAL`).

### Step 3 - Verify Solver Status
- Check if the returned status equals `pywraplp.Solver.OPTIMAL`.
- For this problem with only equality constraints, `OPTIMAL` or `FEASIBLE` are both acceptable outcomes.

### Step 4 - Retrieve and Validate Results
- If the status is acceptable, obtain the objective value via `solver.Objective().Value()`.
- Iterate over the variable dictionary to get each variable's solution value using `var.solution_value()`.
- Optionally, print variable values alongside their demand and profit to verify constraint satisfaction.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Assume `sources`, `destinations`, `profit`, `demand` are defined
# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')

# 2. Create variables (Modeling Step 2)
x = {}
for i in sources:
    for j in destinations:
        x[(i, j)] = solver.NumVar(0, solver.infinity(), f'x_{i}_{j}')

# 3. Build objective (Modeling Step 3)
objective = solver.Objective()
for i in sources:
    for j in destinations:
        objective.SetCoefficient(x[(i, j)], profit[(i, j)])
objective.SetMaximization()

# 4. Add constraints (Modeling Step 4)
for i in sources:
    for j in destinations:
        constraint = solver.Constraint(demand[(i, j)], demand[(i, j)])
        constraint.SetCoefficient(x[(i, j)], 1.0)

# 5. Solve and check
status = solver.Solve()
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_profit = objective.Value()
    # Optional: Verify variable values
    # for i in sources:
    #     for j in destinations:
    #         print(f"{x[(i, j)].name()} = {x[(i, j)].solution_value()}")
else:
    raise RuntimeError(f"Solver did not find an optimal/feasible solution. Status: {status}")
```

### Common Pitfalls
- Confusing solver status codes; `OPTIMAL` is typical even for fixed-variable problems.
- Forgetting that `solver.Solve()` must be called before attempting to access `solution_value()` or `Objective().Value()`.
- Lack of validation that the extracted solution indeed satisfies the equality constraints, especially when debugging.
