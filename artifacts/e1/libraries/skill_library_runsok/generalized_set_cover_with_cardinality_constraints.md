---
name: Generalized Set Cover with Cardinality Constraints
description: |
  Model and solve binary selection problems with minimum coverage requirements per subset, minimizing total cost, using either CP-SAT or MIP solvers.

---
# Workflow 1 (CP-SAT for Exact Binary Programs)

## Modeling stage

### Strategy Overview
Formulate the problem as a pure binary integer program with linear constraints, leveraging the CP-SAT solver's native efficiency for Boolean logic and cardinality constraints. This approach is ideal for problems where all decision variables are binary and the objective and constraints are linear.

### Step 1 - Define Sets and Parameters
- Define a set of selectable `items` (e.g., teams, facilities) and a set of `requirements` (e.g., locations, tasks).
- Define a cost parameter `cost[i]` for each item `i`.
- Define a minimum coverage requirement `req[r]` for each requirement `r`.
- Define a coverage mapping `covers[r]` which is a list of item indices that can satisfy requirement `r`.

### Step 2 - Create Binary Decision Variables
- Create a binary decision variable `x[i]` for each item `i`. A value of 1 indicates the item is selected.

### Step 3 - Formulate Cardinality Constraints
- For each requirement `r`, create a linear constraint: the sum of `x[i]` for all `i` in `covers[r]` must be at least `req[r]`.

### Step 4 - Define the Objective Function
- Define the objective to minimize the total cost: the sum of `cost[i] * x[i]` for all items `i`.

### Formulation Template
```json
{
  "sets": [
    "items: list of selectable elements",
    "requirements: list of subsets needing coverage"
  ],
  "parameters": [
    "cost: dict[item_id -> numerical_cost]",
    "req: dict[requirement_id -> minimum_required_count]",
    "covers: dict[requirement_id -> list[item_id]]"
  ],
  "decision_variables": [
    "x: dict[item_id -> BinaryVar]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    "for each r in requirements: sum(x[i] for i in covers[r]) >= req[r]"
  ]
}
```

### Common Pitfalls
- Forgetting to ensure all costs and requirement counts are integers or can be scaled to integers for CP-SAT.
- Incorrectly defining the coverage mapping, leading to constraints that reference non-existent variables.
- Using floating-point coefficients directly in CP-SAT constraints, which may require scaling.

## Solving stage

### Strategy Overview
Use the OR-Tools CP-SAT solver to find an optimal or feasible solution. Configure solver parameters for performance and reliability, and implement robust solution extraction and verification.

### Step 1 - Instantiate Solver and Model
- Create a `cp_model.CpModel()` object.
- Add variables, constraints, and the objective as defined in the modeling stage.

### Step 2 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` to limit runtime.
- Set `solver.parameters.num_search_workers` for parallel solving.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to search for proven optimal solutions.

### Step 3 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the status (`cp_model.OPTIMAL`, `cp_model.FEASIBLE`, `cp_model.INFEASIBLE`) to determine the outcome.

### Step 4 - Extract and Verify Solution
- If status is OPTIMAL or FEASIBLE, extract selected items where `solver.Value(x[i]) == 1`.
- Implement a verification loop to check that all cardinality constraints are satisfied by the extracted solution.

### Step 5 - Verify Optimality (Optional)
- To confirm optimality, add a new constraint: `sum(cost[i] * x[i]) <= current_objective - 1`. Attempting to solve again should result in INFEASIBLE.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... create variables, constraints, objective
solver = cp_model.CpSolver()
# set parameters
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
# solve with status / termination checks
status = solver.Solve(model)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected_items = [i for i in items if solver.Value(x[i]) == 1]
    # ... verification and output
else:
    # handle infeasible or unknown status
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Misinterpreting `FEASIBLE` as `OPTIMAL` when reporting results.
- Overlooking the need to scale floating-point data to integers for CP-SAT, which can affect accuracy.

# Workflow 2 (MIP Solver via Modeling Framework)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Programming (MIP) model using a modeling framework (e.g., Pyomo, PuLP). This provides flexibility to use various open-source or commercial MIP solvers (e.g., HiGHS, CBC, Gurobi) and is suitable for problems that may later incorporate continuous variables or more complex constraint types.

### Step 1 - Define Abstract Sets and Parameters
- Define index sets for `items` and `requirements` as abstract sets within the modeling framework.
- Define parameters for `cost`, `req`, and the `covers` mapping as model parameters or external data structures.

### Step 2 - Declare Binary Variables
- Declare a binary variable `model.x` indexed by the set of items.

### Step 3 - Build Coverage Constraints
- Construct constraints using the modeling framework's expression syntax: for each requirement `r`, `sum(model.x[i] for i in covers[r]) >= req[r]`.

### Step 4 - Construct the Objective
- Define the objective as `sum(cost[i] * model.x[i] for i in items)` and set its sense to minimize.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "R: set of requirements"
  ],
  "parameters": [
    "c_i: param dict for item cost",
    "r_j: param dict for requirement count",
    "Covers_j: param dict mapping requirement to list of covering items"
  ],
  "decision_variables": [
    "x_i: Binary variable for each item i in I"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(c_i[i] * x_i[i] for i in I)"
  },
  "constraints": [
    "for each j in R: sum(x_i[i] for i in Covers_j[j]) >= r_j[j]"
  ]
}
```

### Common Pitfalls
- Using inefficient data structures for the `covers` mapping that slow down constraint generation for large problems.
- Not keeping the model abstract, leading to hard-coded indices that reduce reusability.
- Forgetting to deactivate the solver's presolve or heuristic options when debugging model correctness.

## Solving stage

### Strategy Overview
Instantiate the model, send it to a MIP solver via the modeling framework's interface, and manage solver options, solution extraction, and validation. This workflow emphasizes solver-agnostic code.

### Step 1 - Instantiate Solver Object
- Use the framework's `SolverFactory` to create a solver object (e.g., `SolverFactory('highs')`).

### Step 2 - Set Solver Options
- Set a time limit via `options['time_limit']`.
- Set optimality tolerance via `options['mip_rel_gap']`.
- Set the number of threads via `options['threads']` for parallel solving.
- Set a random seed if supported.

### Step 3 - Solve and Check Termination
- Call `solver.solve(model, options=options)`.
- Check the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`) separately.

### Step 4 - Extract Solution Safely
- If the termination condition is acceptable, load the solution into the model instance.
- Extract selected items by filtering variables where `value(model.x[i]) > 0.5`.

### Step 5 - Validate Solution and Handle Failures
- Programmatically verify all coverage constraints using the extracted solution.
- Implement try-except blocks to gracefully handle solver errors or infeasible instances.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.R = pyo.Set(initialize=requirements)
# ... define parameters, variables, constraints, objective
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
options = {'time_limit': 30, 'mip_rel_gap': 0.0001}
results = solver.solve(model, options=options)
if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
        selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
        # ... verification and output
```

### Common Pitfalls
- Confusing solver `status` (process success) with `termination_condition` (solution quality).
- Attempting to access variable values before checking if a solution was found, leading to errors.
- Not using `load_solutions=False` when probing for feasibility or optimality to avoid loading invalid solutions.
