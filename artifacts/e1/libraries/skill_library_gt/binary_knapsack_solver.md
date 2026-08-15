---
name: Binary Knapsack Solver
description: |
  Model and solve binary selection problems with a single capacity constraint to maximize total value, using structured formulation and robust solving with verification.
---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a standard 0-1 knapsack using the OR-Tools linear solver wrapper. This approach directly maps binary decisions to integer variables and uses a high-performance MIP solver (SCIP/CBC) for optimization.

### Step 1 - Define Problem Data
- Organize item data into parallel lists or dictionaries for values and weights, indexed by a common set of item identifiers.
- Store the global capacity limit as a separate parameter.

### Step 2 - Create Binary Decision Variables
- For each item, create a binary decision variable `x[i] ∈ {0,1}` using `solver.IntVar(0, 1, name)`.
- Use a list or dictionary to store variables for easy access in constraints and the objective.

### Step 3 - Formulate Objective Function
- Construct a linear objective to maximize the total value: `maximize Σ (value[i] * x[i])`.
- Build the objective incrementally by setting coefficients for each variable.

### Step 4 - Add Capacity Constraint
- Add a single linear constraint to enforce the weight limit: `Σ (weight[i] * x[i]) ≤ capacity`.
- Use Python's `sum()` function for clarity when building the constraint expression.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": ["value[items]", "weight[items]", "capacity"],
  "decision_variables": ["x[items] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(value[i] * x[i] for i in items)"
  },
  "constraints": [
    "sum(weight[i] * x[i] for i in items) <= capacity"
  ]
}
```

### Common Pitfalls
- Hardcoding data within constraint expressions instead of using parameters, reducing reusability.
- Forgetting to set the objective sense to maximization.
- Creating variables with incorrect bounds (e.g., `IntVar(0, n)` instead of `IntVar(0, 1)`).

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools wrapper for SCIP or CBC. Configure solver limits, execute the solve, and rigorously check the status before extracting and verifying the solution.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set practical limits: a time limit (e.g., `solver.SetTimeLimit(30000)`) and number of threads (e.g., `solver.SetNumThreads(4)`).
- Call `solver.Solve()` to run the optimization.

### Step 2 - Check Solver Status
- Check if the solver returned an optimal or feasible solution: `status in (solver.OPTIMAL, solver.FEASIBLE)`.
- If the status is not acceptable, handle the failure by reporting the status and investigating infeasibility or unboundedness.

### Step 3 - Extract and Verify Solution
- Extract selected items by evaluating each variable: `x[i].solution_value() > 0.5`.
- Compute derived metrics: total value, total weight used, and remaining capacity.
- Perform a sanity check: verify the total weight does not exceed the capacity.

### Step 4 - Report Results
- Output the objective value, list of selected items, and capacity utilization metrics.
- For optimal solutions, optionally report the best bound and optimality gap.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Data
items = [...]  # list of item identifiers
value = {...}  # dict: item -> value
weight = {...} # dict: item -> weight
capacity = ... # integer capacity

# Build Model
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

x = {}
for i in items:
    x[i] = solver.IntVar(0, 1, f"x_{i}")

# Capacity Constraint
ct = solver.Sum([weight[i] * x[i] for i in items]) <= capacity
solver.Add(ct)

# Objective
objective = solver.Objective()
for i in items:
    objective.SetCoefficient(x[i], value[i])
objective.SetMaximization()

# Solve
status = solver.Solve()

# Check and Output
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [i for i in items if x[i].solution_value() > 0.5]
    total_value = sum(value[i] for i in selected)
    total_weight = sum(weight[i] for i in selected)
    print(f"Objective: {objective.Value()}")
    print(f"Selected items: {selected}")
    print(f"Total weight: {total_weight} / {capacity}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not setting a time limit, risking excessively long runs for large instances.
- Assuming a feasible solution exists without checking the solver status.
- Using a loose tolerance (e.g., `> 0`) for binary variable values instead of `> 0.5`.

# Workflow 2 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract modeling language, separating data from structure. This enables solver independence and easy integration with open-source solvers like CBC or GLPK.

### Step 1 - Define Abstract Sets and Parameters
- Define a Pyomo `Set` for the items.
- Define `Param` objects for item values, item weights, and the global capacity, initializing them from data dictionaries.

### Step 2 - Declare Binary Variables
- Declare a Pyomo `Var` indexed by the item set with `domain=pyo.Binary`.

### Step 3 - Construct Objective and Constraint
- Define the objective as a `pyo.Objective` with `expr=sum(value[i] * x[i] for i in items)` and `sense=pyo.maximize`.
- Define the capacity constraint as a `pyo.Constraint` with `expr=sum(weight[i] * x[i] for i in items) <= capacity`.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": ["value[I]", "weight[I]", "capacity"],
  "decision_variables": ["x[I] ∈ Binary"],
  "objective": {
    "sense": "max",
    "expression": "sum(value[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(weight[i] * x[i] for i in I) <= capacity"
  ]
}
```

### Common Pitfalls
- Using a `ConcreteModel` but not properly initializing parameters via `initialize` dict.
- Defining the objective expression incorrectly (e.g., missing the summation over the set).
- Not using Pyomo's `sum()` or `quicksum()` for large expressions, which can be inefficient.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., CBC). Configure solver options, handle solution loading carefully, and implement verification heuristics to cross-check results.

### Step 1 - Configure Solver and Solve
- Create a solver object: `solver = pyo.SolverFactory("cbc")`.
- Set solver options: time limit (`seconds`), optimality gap tolerance (`ratio`), and threads (`threads`).
- Solve with `load_solutions=False` to manually control solution loading.

### Step 2 - Validate Solver Termination
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `optimal` or `feasible`.
- Only load the solution into the model if these checks pass.

### Step 3 - Extract Solution and Perform Verification
- Load the solution: `model.solutions.load_from(results)`.
- Extract selected items: `[i for i in model.I if pyo.value(model.x[i]) > 0.5]`.
- Compute total weight and verify it satisfies the capacity constraint.
- Optionally, run a fast greedy heuristic or dynamic programming verification for small instances to confirm solution quality.

### Step 4 - Handle Failures and Edge Cases
- If the solver fails or times out, implement a fallback method (e.g., greedy algorithm) to produce a feasible solution.
- For very small instances (n ≤ 20), consider exact enumeration via `itertools.combinations` as a verification benchmark.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Data
items = [...]  # list of item identifiers
value_dict = {...}  # item -> value
weight_dict = {...} # item -> weight
capacity = ...

# Build Model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.value = pyo.Param(model.I, initialize=value_dict)
model.weight = pyo.Param(model.I, initialize=weight_dict)
model.capacity = pyo.Param(initialize=capacity)

model.x = pyo.Var(model.I, domain=pyo.Binary)

model.obj = pyo.Objective(
    expr=sum(model.value[i] * model.x[i] for i in model.I),
    sense=pyo.maximize
)
model.cap_con = pyo.Constraint(
    expr=sum(model.weight[i] * model.x[i] for i in model.I) <= model.capacity
)

# Solve
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False, load_solutions=False)

# Check Status and Extract
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    model.solutions.load_from(results)
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_value = sum(value_dict[i] for i in selected)
    total_weight = sum(weight_dict[i] for i in selected)
    print(f"Objective: {pyo.value(model.obj)}")
    print(f"Selected: {selected}")
    print(f"Weight: {total_weight} / {capacity}")
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
    # Implement fallback heuristic here
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) without checking termination condition, risking errors on infeasible solves.
- Not setting a `ratio` (MIP gap) tolerance, causing solvers to run indefinitely on hard instances.
- Forgetting to call `pyo.value()` on Pyomo components when extracting numeric results.
