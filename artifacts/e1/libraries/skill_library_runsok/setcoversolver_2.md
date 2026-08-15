---
name: SetCoverSolver
description: |
  Model and solve weighted set covering problems with logical OR constraints using binary selection variables and minimize weighted sum objectives, with workflows for CP-SAT and Pyomo backends.
---

# Workflow 1 (CP-SAT Workflow)

## Modeling stage

### Strategy Overview
This workflow models the set covering problem using Google's OR-Tools CP-SAT solver, which is designed for discrete optimization with Boolean variables. It directly encodes logical OR constraints as linear inequalities and uses efficient search strategies for binary integer programming.

### Step 1 - Define Data Structures
- Map the problem elements (e.g., regions, tasks) to the covering subsets (e.g., vehicles, facilities) using a dictionary. This defines the coverage matrix.
- Store the cost for each selectable subset in a list or dictionary, indexed the same as the selection variables.

### Step 2 - Create Model and Variables
- Instantiate a `cp_model.CpModel()`.
- For each selectable subset, create a binary decision variable: `x[i] = model.NewBoolVar(f"x_{i}")`.

### Step 3 - Add Coverage Constraints
- For each element requiring coverage, add a constraint ensuring the sum of the binary variables for its covering subsets is at least 1: `model.Add(sum(x[v] for v in coverage[e]) >= 1)`.

### Step 4 - Set Weighted Sum Objective
- Define the objective to minimize the total cost: `model.Minimize(sum(cost[i] * x[i] for i in all_subsets))`.

### Formulation Template
```json
{
  "sets": [
    "E: set of elements to cover",
    "S: set of selectable subsets"
  ],
  "parameters": [
    "cost[s in S]: cost of selecting subset s",
    "coverage[e in E]: list of subsets s in S that cover element e"
  ],
  "decision_variables": [
    "x[s in S]: binary, 1 if subset s is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s] * x[s] for s in S)"
  },
  "constraints": [
    "Coverage: sum(x[s] for s in coverage[e]) >= 1, for all e in E"
  ]
}
```

### Common Pitfalls
- Incorrectly mapping the coverage relationship, leading to infeasible or overly restrictive models.
- Forgetting to index cost parameters consistently with variable indices.
- Using `model.NewIntVar` instead of `model.NewBoolVar` for binary selection, which is less efficient.

## Solving stage

### Strategy Overview
Solve the model using the CP-SAT solver with configuration for optimality proof, parallel search, and time management. The focus is on verifying solution status and ensuring the output is parseable.

### Step 1 - Configure Solver
- Instantiate `cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds = TIME_LIMIT`, `solver.parameters.num_search_workers = NUM_WORKERS`, `solver.parameters.random_seed = SEED`, and `solver.parameters.relative_gap_limit = 0.0` for exact optimization.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check `status`: `cp_model.OPTIMAL` confirms proven optimality; `cp_model.FEASIBLE` indicates a feasible solution; `cp_model.INFEASIBLE` or `cp_model.MODEL_INVALID` indicate failure.

### Step 3 - Extract and Verify Solution
- If status is OPTIMAL or FEASIBLE, extract the objective value and selected items.
- Programmatically verify that all coverage constraints are satisfied by the selected subsets to catch modeling errors.

### Step 4 - Output Standardized Results
- Print results in a consistent format, starting with `RESULT:{objective_value}` for automated parsing, followed by human-readable details.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model (follow Modeling stage steps)
model = cp_model.CpModel()
# ... define variables, constraints, objective

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

# Handle results
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    objective_value = solver.ObjectiveValue()
    selected_items = [i for i in range(NUM_SUBSETS) if solver.Value(x[i]) == 1]
    # Verification loop (optional but recommended)
    for e in ELEMENTS:
        if not any(solver.Value(x[s]) == 1 for s in COVERAGE[e]):
            print(f"ERROR: Element {e} not covered.")
    print(f"RESULT:{objective_value}")
    print(f"Selected: {selected_items}")
elif status == cp_model.INFEASIBLE:
    print("RESULT:INFEASIBLE")
else:
    print(f"RESULT:ERROR status={status}")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses before extracting solution values, causing runtime errors.
- Omitting verification steps, which can lead to accepting incorrect solutions due to subtle modeling bugs.
- Setting `relative_gap_limit` too high when an exact optimal solution is required.

# Workflow 2 (Pyomo Workflow)

## Modeling stage

### Strategy Overview
This workflow models the set covering problem using Pyomo, an algebraic modeling language, targeting MILP solvers like HiGHS, CBC, or Gurobi. It emphasizes structured set and parameter definitions for clarity and maintainability.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo Sets for elements (`model.E`) and selectable subsets (`model.S`).
- Define a Pyomo Parameter `model.cost` indexed by `model.S` to hold selection costs.
- Store the coverage matrix as a dictionary mapping each element to a list of covering subsets.

### Step 2 - Create Binary Variables
- Create a Pyomo Variable `model.x` indexed by `model.S` with `domain=pyo.Binary`.

### Step 3 - Formulate Coverage Constraints
- Define a constraint rule that, for each element `e` in `model.E`, sums the variables of its covering subsets and enforces the sum >= 1.

### Step 4 - Define Minimization Objective
- Create an Objective `model.obj` with `sense=pyo.minimize` and expression `sum(model.cost[s] * model.x[s] for s in model.S)`.

### Formulation Template
```json
{
  "sets": [
    "E: set of elements to cover",
    "S: set of selectable subsets"
  ],
  "parameters": [
    "cost[s in S]: cost of selecting subset s",
    "coverage[e in E]: list of subsets s in S that cover element e"
  ],
  "decision_variables": [
    "x[s in S]: binary, 1 if subset s is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s] * x[s] for s in S)"
  },
  "constraints": [
    "Coverage: sum(x[s] for s in coverage[e]) >= 1, for all e in E"
  ]
}
```

### Common Pitfalls
- Using concrete model initialization with large data sets, which can be slow; consider `AbstractModel` for large problems.
- Defining constraint rules incorrectly, e.g., using global variables instead of model components within the rule.
- Not using `pyo.Param` for costs, leading to less readable and less flexible models.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver via the SolverFactory interface. Configure for optimality proof, handle solver status and termination conditions rigorously, and implement solution verification.

### Step 1 - Select and Configure Solver
- Use `pyo.SolverFactory('SOLVER_NAME')` (e.g., 'highs', 'cbc', 'gurobi').
- Set solver options: `opt.options['time_limit'] = TIME_LIMIT`, `opt.options['mip_rel_gap'] = 0.0` for exact optimality, `opt.options['threads'] = NUM_THREADS`, and `opt.options['seed'] = SEED`.

### Step 2 - Solve and Inspect Results
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` and `results.solver.termination_condition`.
- Accept solutions where status is `SolverStatus.ok` and termination is `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract Solution and Verify
- Load results into the model instance.
- Extract the objective value via `pyo.value(model.obj)` and selected items where `pyo.value(model.x[s]) > 0.5`.
- Optionally, verify coverage by checking each element against the selected subsets.

### Step 4 - Output Standardized Results
- Print the objective value with the prefix `RESULT:` for parsing, followed by detailed solution information.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (follow Modeling stage steps)
model = pyo.ConcreteModel()
model.E = pyo.Set(initialize=ELEMENTS)
model.S = pyo.Set(initialize=SUBSETS)
model.cost = pyo.Param(model.S, initialize=COST_DICT)
model.x = pyo.Var(model.S, domain=pyo.Binary)
def coverage_rule(m, e):
    return sum(m.x[s] for s in COVERAGE[e]) >= 1
model.coverage = pyo.Constraint(model.E, rule=coverage_rule)
model.obj = pyo.Objective(expr=sum(model.cost[s] * model.x[s] for s in model.S), sense=pyo.minimize)

# Solve
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30.0
solver.options['mip_rel_gap'] = 0.0
solver.options['threads'] = 4
solver.options['seed'] = 42

results = solver.solve(model, tee=False)
status = results.solver.status
term = results.solver.termination_condition

# Handle results
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    objective_value = float(pyo.value(model.obj))
    selected_items = [s for s in model.S if pyo.value(model.x[s]) > 0.5]
    # Verification loop (optional)
    for e in model.E:
        if not any(pyo.value(model.x[s]) > 0.5 for s in COVERAGE[e]):
            print(f"ERROR: Element {e} not covered.")
    print(f"RESULT:{objective_value}")
    print(f"Selected: {selected_items}")
elif status == SolverStatus.warning and term == TerminationCondition.infeasible:
    print("RESULT:INFEASIBLE")
else:
    print(f"RESULT:ERROR status={status}, termination={term}")
```

### Common Pitfalls
- Accessing variable values without first checking solver status and termination condition, leading to `RuntimeError`.
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (solution is proven optimal).
- Not setting `mip_rel_gap=0.0` when an exact optimum is required, resulting in early termination with a gap.
