---
name: Set Cover with Linear Cost
description: |
  Model and solve binary selection problems where subsets must cover all elements at minimum linear cost using MILP solvers.
---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
This workflow models the set cover problem using a direct matrix representation of coverage relationships. It is designed for integration with Google OR-Tools' linear solver wrapper, emphasizing efficient constraint building and explicit lower bounds.

### Step 1 - Define Selection Variables
- Create a binary decision variable for each selectable subset (e.g., worker, facility).
- Use a naming convention like `x[i]` where `i` is the subset index.

### Step 2 - Map Coverage Requirements
- Construct a binary capability matrix `capable[i][j]` where entry is 1 if subset `i` covers element `j`.
- This matrix is a parameter used to generate constraints.

### Step 3 - Formulate Linear Objective
- Define a linear cost parameter `cost[i]` for each subset.
- Set the objective to minimize the total cost: `min sum(cost[i] * x[i])`.

### Step 4 - Enforce Coverage Constraints
- For each element `j` that must be covered, create a constraint: `sum(capable[i][j] * x[i] for all i) >= 1`.
- This ensures at least one capable subset is selected for every element.

### Formulation Template
```json
{
  "sets": [
    "Subsets",
    "Elements"
  ],
  "parameters": [
    "cost[Subsets]",
    "capable[Subsets][Elements]"
  ],
  "decision_variables": [
    "x[Subsets] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in Subsets)"
  },
  "constraints": [
    "Coverage_j: sum(capable[i][j] * x[i] for i in Subsets) >= 1, for all j in Elements"
  ]
}
```

### Common Pitfalls
- Using dense matrices for sparse coverage relationships, which unnecessarily increases model size.
- Forgetting to validate that the `capable` matrix has no rows of zeros (uncoverable elements), which leads to infeasibility.
- Defining `cost` as a non-positive value, which can trivialize the objective.

## Solving stage

### Strategy Overview
This stage uses the OR-Tools `pywraplp` interface to a MIP solver (e.g., SCIP, CBC). It focuses on solver configuration, robust status checking, and post-solution validation of coverage.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Set a time limit (`solver.SetTimeLimit`) and number of threads (`solver.SetNumThreads`) for performance control.

### Step 2 - Build Model Efficiently
- Add variables using `solver.BoolVar()`.
- For each element, create a constraint with `solver.Add(sum(...) >= 1)`, adding coefficients only for subsets where `capable[i][j] == 1`.

### Step 3 - Solve and Check Status
- Call `solver.Solve()`.
- Check status for `pywraplp.Solver.OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error messages.

### Step 4 - Extract and Validate Solution
- Extract selected subsets where the variable solution value is > 0.5.
- Programmatically verify that every element is covered by at least one selected subset, independent of solver status.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# Variable creation
x = {}
for i in subsets:
    x[i] = solver.BoolVar(f'x_{i}')

# Objective
objective = solver.Objective()
for i in subsets:
    objective.SetCoefficient(x[i], cost[i])
objective.SetMinimization()

# Constraints
for j in elements:
    constraint = solver.Constraint(1, solver.infinity())
    for i in subsets:
        if capable[i][j]:
            constraint.SetCoefficient(x[i], 1)

# Solve with status / termination checks
result_status = solver.Solve()
if result_status == pywraplp.Solver.OPTIMAL:
    print('Optimal solution found.')
elif result_status == pywraplp.Solver.FEASIBLE:
    print('Feasible solution found.')
else:
    raise Exception('Solver did not find a feasible solution.')

# Extract solution
selected = [i for i in subsets if x[i].solution_value() > 0.5]
# Validation: Ensure coverage
for j in elements:
    if not any(capable[i][j] for i in selected):
        raise AssertionError(f'Element {j} is not covered.')
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; always check for `OPTIMAL` if an exact solution is required.
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.
- Failing to verify coverage after solving, which can miss subtle solver or model errors.

# Workflow 2 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define the set cover problem with explicit sets and rules. It is designed for clarity, maintainability, and use with open-source solvers like CBC via the `pyomo.opt` interface.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `Subsets` and `Elements`.
- Define `Param` objects for `cost` (indexed by Subsets) and a `coverage` dictionary mapping each element to a list of covering subsets.

### Step 2 - Declare Binary Variables
- Create a `Var` object indexed by the `Subsets` set with domain `pyo.Binary`.

### Step 3 - Construct Objective Rule
- Define an `Objective` rule that sums `cost[s] * m.x[s]` over all subsets, with sense `minimize`.

### Step 4 - Build Coverage Constraints via Rule
- Create a `Constraint` indexed by the `Elements` set.
- For each element, the rule returns `sum(m.x[s] for s in coverage[e]) >= 1`.

### Formulation Template
```json
{
  "sets": [
    "S (Subsets)",
    "E (Elements)"
  ],
  "parameters": [
    "cost[S]",
    "coverage[E] -> list of S"
  ],
  "decision_variables": [
    "x[S] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s] * x[s] for s in S)"
  },
  "constraints": [
    "Cover_e: sum(x[s] for s in coverage[e]) >= 1, for all e in E"
  ]
}
```

### Common Pitfalls
- Defining the `coverage` parameter as a dense matrix within Pyomo, which loses the benefits of Pyomo's sparse set-based indexing.
- Using mutable Python data structures inside Pyomo rules without proper reinitialization, leading to incorrect model behavior.
- Not verifying that the `coverage` list for each element is non-empty during data input, which causes infeasible constraints.

## Solving stage

### Strategy Overview
This stage solves the Pyomo model using a solver factory (e.g., `cbc`). It emphasizes proper handling of solver results, extraction of variable values, and programmatic verification of the solution's feasibility.

### Step 1 - Instantiate Solver and Configure Options
- Create a solver object: `solver = pyo.SolverFactory('cbc')`.
- Set options such as time limit (`seconds`), optimality gap (`ratio`), and thread count (`threads`).

### Step 2 - Solve and Inspect Termination Conditions
- Call `results = solver.solve(model, tee=False)`.
- Check both `results.solver.status` (should be `SolverStatus.ok`) and `results.solver.termination_condition` (preferably `TerminationCondition.optimal`).

### Step 3 - Extract Solution Values
- Use `pyo.value(model.x[s])` to get the value of each binary variable.
- Collect selected subsets where the value is > 0.5.

### Step 4 - Validate Coverage and Output Results
- Verify coverage by checking, for each element, if any selected subset is in its `coverage` list.
- Return results in a structured format (e.g., dictionary with objective value and selected list).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.S = pyo.Set(initialize=subsets)
model.E = pyo.Set(initialize=elements)
model.cost = pyo.Param(model.S, initialize=cost_dict)
# coverage_dict maps element -> list of subset indices
model.x = pyo.Var(model.S, domain=pyo.Binary)

def obj_rule(m):
    return sum(m.cost[s] * m.x[s] for s in m.S)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def cover_rule(m, e):
    # coverage_dict is in outer scope
    return sum(m.x[s] for s in coverage_dict[e]) >= 1
model.cover = pyo.Constraint(model.E, rule=cover_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

# Check results
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    print('Optimal solution found.')
    selected = [s for s in model.S if pyo.value(model.x[s]) > 0.5]
    obj_val = pyo.value(model.obj)
    # Validate coverage
    all_covered = all(any(s in selected for s in coverage_dict[e]) for e in model.E)
    if not all_covered:
        raise AssertionError('Solution validation failed: not all elements covered.')
else:
    raise Exception('Solver did not return an optimal solution.')
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran normally) with `TerminationCondition.optimal` (found proven optimum); both checks are necessary.
- Not setting `ratio` (optimality gap) to `0.0` when an exact optimal solution is required, which may return a suboptimal result.
- Accessing `pyo.value` on variables without first checking the solver status, which can lead to errors if the solve failed.
