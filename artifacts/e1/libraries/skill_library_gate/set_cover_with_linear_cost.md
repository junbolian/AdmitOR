---
name: Set Cover with Linear Cost
description: |
  Model and solve binary selection problems where elements must be covered by selected subsets at minimum linear cost, using systematic constraint generation and robust solver handling.

---
# Workflow 1 (Matrix-Based Modeling with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a binary coverage matrix to systematically define the relationship between selectable items and elements requiring coverage. It is well-suited for problems where coverage relationships are dense or can be efficiently represented as a 0-1 matrix, and leverages the OR-Tools CP-SAT or MIP backends for solving.

### Step 1 - Define Core Sets and Parameters
- Identify the set of selectable items (e.g., workers, facilities) and the set of elements requiring coverage (e.g., tasks, locations).
- Define a linear cost parameter for selecting each item.
- Construct a binary coverage matrix `capable[i][j]` where entry `(i, j)` is 1 if item `i` can cover element `j`.

### Step 2 - Declare Binary Decision Variables
- Create a binary decision variable `x[i]` for each selectable item `i`, where `x[i] = 1` indicates the item is selected.

### Step 3 - Formulate Coverage Constraints
- For each element `j`, create a linear constraint: `sum_{i} capable[i][j] * x[i] >= 1`. This ensures at least one capable item is selected to cover the element.

### Step 4 - Specify Linear Objective
- Define the objective to minimize total linear cost: `minimize sum_{i} cost[i] * x[i]`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items (indices i).",
    "J: Set of elements requiring coverage (indices j)."
  ],
  "parameters": [
    "cost[i]: Linear cost of selecting item i ∈ I.",
    "capable[i][j]: Binary parameter (0/1) indicating if item i ∈ I covers element j ∈ J."
  ],
  "decision_variables": [
    "x[i] ∈ {0, 1}: Binary variable indicating selection of item i ∈ I."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} cost[i] * x[i]"
  },
  "constraints": [
    "Coverage: For each j in J: sum_{i in I} capable[i][j] * x[i] >= 1"
  ]
}
```

### Common Pitfalls
- Forgetting to ensure the coverage matrix is binary (0/1), which can lead to incorrect constraint coefficients.
- Creating constraints for elements that have no covering items (empty column in the matrix), which makes the problem inherently infeasible.
- Using floating-point numbers for costs when exact integer costs are available, which can introduce unnecessary numerical issues.

## Solving stage

### Strategy Overview
This solving stage uses the OR-Tools library with a MIP solver backend (e.g., SCIP, CBC). It focuses on systematic model building from the matrix representation, explicit solver configuration, and rigorous solution verification.

### Step 1 - Initialize Solver and Variables
- Instantiate the OR-Tools MIP solver (e.g., `pywraplp.Solver.CreateSolver('SCIP')`).
- Create the binary decision variables `x[i]` using the solver's `BoolVar` method.

### Step 2 - Build Constraints from Coverage Matrix
- Iterate over each element `j`. For each, create a constraint with a lower bound of 1.
- For each item `i`, if `capable[i][j] == 1`, set the coefficient of `x[i]` in the constraint to 1.

### Step 3 - Set Objective and Solver Parameters
- Set the linear objective using the solver's `Objective()` method and the cost coefficients.
- Configure practical solver parameters such as a time limit (`SetTimeLimit`), optimality gap tolerance (`SetRelativeGap`), and number of threads (`SetNumThreads`).

### Step 4 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the result status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`) to determine the next steps.

### Step 5 - Extract and Verify Solution
- If a feasible solution exists, extract the values of `x[i]` and compute the objective value.
- Perform a post-solve verification by checking, for each element `j`, that the sum `sum_{i} capable[i][j] * x[i]` is at least 1.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
# Define sets I and J, parameters cost and capable
x = {}
for i in I:
    x[i] = solver.BoolVar(f'x[{i}]')

# Coverage constraints
for j in J:
    constraint = solver.Constraint(1, solver.infinity(), f'cover_{j}')
    for i in I:
        if capable[i][j] == 1:
            constraint.SetCoefficient(x[i], 1)

# Objective
objective = solver.Objective()
for i in I:
    objective.SetCoefficient(x[i], cost[i])
objective.SetMinimization()

# Set solver parameters
solver.SetTimeLimit(time_limit_milliseconds)
solver.SetNumThreads(num_threads)

# solve with status / termination checks
status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    objective_value = objective.Value()
    selected_items = [i for i in I if x[i].solution_value() > 0.5]
    # Post-solve verification
    for j in J:
        coverage_sum = sum(capable[i][j] * x[i].solution_value() for i in I)
        assert coverage_sum >= 1, f"Element {j} not covered."
else:
    # Handle infeasible or other status
    selected_items = []
    objective_value = None
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good feasible solutions when optimality isn't proven.
- Omitting post-solve verification, which can miss subtle errors in constraint formulation or data.
- Setting solver parameters (like time limit) in the wrong units (seconds vs. milliseconds).

# Workflow 2 (Set-Based Modeling with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities with set-based indexing. It is ideal for problems where coverage relationships are naturally expressed as mappings from elements to lists of covering items (e.g., dictionaries). It leverages open-source MILP solvers like CBC or HiGHS through Pyomo's `SolverFactory`.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for the selectable items and the elements requiring coverage.
- Define a `Param` for the linear cost of each item, indexed by the item set.
- Define a coverage mapping, typically as a dictionary `coverage[t]` that lists all items capable of covering element `t`.

### Step 2 - Declare Binary Decision Variables
- Create a Pyomo `Var` indexed by the item set, with domain `pyo.Binary`.

### Step 3 - Formulate Coverage Constraints via Rule
- Define a constraint rule function that, for a given element `t`, sums the decision variables for all items in `coverage[t]` and enforces the sum >= 1.
- Apply this rule to create a `Constraint` indexed by the element set.

### Step 4 - Specify Linear Objective
- Define an `Objective` with sense `minimize` and expression `sum(cost[i] * x[i] for i in item_set)`.

### Formulation Template
```json
{
  "sets": [
    "I: Pyomo Set of selectable items.",
    "J: Pyomo Set of elements requiring coverage."
  ],
  "parameters": [
    "cost[i]: Pyomo Param for cost of item i ∈ I.",
    "coverage_map[j]: Python dictionary mapping each element j ∈ J to a list of items i ∈ I that cover it."
  ],
  "decision_variables": [
    "x[i] ∈ {0, 1}: Pyomo Var, binary selection variable for item i ∈ I."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} cost[i] * x[i]"
  },
  "constraints": [
    "Coverage: For each j in J: sum_{i in coverage_map[j]} x[i] >= 1"
  ]
}
```

### Common Pitfalls
- Defining the coverage mapping incorrectly (e.g., mapping items to elements instead of elements to items), leading to inverted constraints.
- Using Python lists directly inside Pyomo constraint rules without ensuring the indices are valid Pyomo set members.
- Not initializing all required Pyomo `Param` objects before model instantiation, causing runtime errors.

## Solving stage

### Strategy Overview
This solving stage uses Pyomo's `SolverFactory` to interface with MILP solvers (e.g., `'cbc'`, `'highs'`). It emphasizes robust handling of solver status and termination conditions, and includes explicit solution verification.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object using `pyo.SolverFactory(solver_name)`.
- Set solver options such as time limit (`seconds`), optimality gap tolerance (`ratio` or `mip_rel_gap`), and number of threads (`threads`).

### Step 2 - Solve and Capture Results
- Call `solver.solve(model, tee=False)` to execute the solve.
- Capture the returned `results` object.

### Step 3 - Check Solver Status and Termination
- Inspect `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 4 - Extract Solution and Compute Objective
- Extract variable values using `pyo.value(model.x[i])`.
- Compute the objective value using `pyo.value(model.obj)`.
- Build a list of selected items where the variable value is > 0.5.

### Step 5 - Verify Coverage and Output
- For each element, verify that at least one item in its coverage list is selected.
- Output results in a structured format (e.g., dictionary or JSON) including status, objective value, selected items, and verification flag.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=elements)

model.cost = pyo.Param(model.I, initialize=cost_dict)
model.x = pyo.Var(model.I, domain=pyo.Binary)

def obj_rule(m):
    return sum(m.cost[i] * m.x[i] for i in m.I)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def coverage_rule(m, j):
    # coverage_map is a dict: j -> list of i
    return sum(m.x[i] for i in coverage_map[j]) >= 1
model.coverage_con = pyo.Constraint(model.J, rule=coverage_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = time_limit
solver.options['ratio'] = optimality_gap
solver.options['threads'] = num_threads

results = solver.solve(model, tee=False)
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    # Verification
    all_covered = all(any(pyo.value(model.x[i]) > 0.5 for i in coverage_map[j]) for j in model.J)
    output = {
        'status': 'success',
        'objective': objective_value,
        'selected': selected_items,
        'verified': all_covered
    }
else:
    output = {
        'status': 'failed',
        'solver_status': str(status),
        'termination': str(term)
    }
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (found optimal solution); both checks are necessary.
- Not converting `pyo.value()` results to native Python types (e.g., `float`, `int`) before using them in verification logic.
- Setting solver options incorrectly for the chosen solver backend (e.g., using Gurobi-specific options with CBC).
