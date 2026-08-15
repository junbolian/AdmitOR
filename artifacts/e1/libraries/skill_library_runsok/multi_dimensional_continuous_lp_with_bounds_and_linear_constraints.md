---
name: Multi-Dimensional Continuous LP with Bounds and Linear Constraints
description: |
  Model and solve linear optimization problems with continuous multi-dimensional variables, box bounds, linear inequality constraints, and a linear objective using structured workflows for different solver backends.
---

# Workflow 1 (Direct Solver API: OR-Tools GLOP)

## Modeling stage

### Strategy Overview
This workflow uses a direct, imperative API to construct a linear program. It is suitable for prototyping and scenarios where fine-grained control over the solving process is desired, leveraging the open-source GLOP solver.

### Step 1 - Define Data Structures
- Organize all problem parameters in parallel, indexable data structures (e.g., lists, dictionaries) for clarity and maintainability.
- Store per-item coefficients for profit, resource consumption, and lower/upper bounds, all indexed by the same set of item identifiers.

### Step 2 - Instantiate Solver and Variables
- Create a linear solver instance using the `GLOP` backend.
- In a single loop over all items, create continuous decision variables, directly applying their individual lower and upper bounds during construction.

### Step 3 - Formulate Constraints and Objective
- Create a linear constraint for the global resource limit, setting its upper bound to the total capacity.
- Iterate through variables to add their coefficients to this constraint using their respective consumption rates.
- Define the objective function as maximization, iterating through variables to set their profit coefficients.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit_i[I]",
    "consumption_i[I]",
    "lb_i[I]",
    "ub_i[I]",
    "capacity"
  ],
  "decision_variables": ["x_i[I] (continuous)"],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in I} profit_i[i] * x_i[i]"
  },
  "constraints": [
    "box_bounds: lb_i[i] <= x_i[i] <= ub_i[i], forall i in I",
    "resource_limit: sum_{i in I} consumption_i[i] * x_i[i] <= capacity"
  ]
}
```

### Common Pitfalls
- Accidentally reversing inequality signs or misplacing bounds when creating variables.
- Using mismatched indices between parameter arrays, leading to incorrect coefficient assignment.
- Forgetting to set the objective sense (`Maximize` or `Minimize`) before solving.

## Solving stage

### Strategy Overview
The solving stage focuses on executing the model, rigorously checking the solution status, and performing validation and post-optimality analysis to ensure correctness and derive insights.

### Step 1 - Execute Solve and Check Status
- Call the solver's `Solve()` method.
- Immediately check the result status (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`) to determine if a valid solution is available.

### Step 2 - Extract and Validate Solution
- If optimal or feasible, extract variable values and objective value.
- Programmatically recalculate the total resource consumption and verify it does not exceed the capacity.
- Check that each variable value respects its declared lower and upper bounds.

### Step 3 - Perform Post-Optimality Analysis
- Calculate efficiency ratios (e.g., profit per unit resource) for each item to interpret the solution.
- Identify binding constraints (e.g., items at their bounds, resource constraint at capacity).
- Use the continuous solution as a benchmark upper bound if integrality is later considered.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... [Variable, constraint, and objective construction code]

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    # Extract variable values and validate
    total_used = 0.0
    for i in items:
        val = x[i].solution_value()
        total_used += consumption[i] * val
        assert lb[i] - 1e-6 <= val <= ub[i] + 1e-6
    assert total_used <= capacity + 1e-6
    # Perform analysis
    ratios = [profit[i]/consumption[i] for i in items]
else:
    print("Solve failed. Status:", status)
```

### Common Pitfalls
- Proceeding to extract solution values without checking the solver status, leading to errors.
- Using loose tolerances for validation; always use a small epsilon (e.g., 1e-6) for floating-point comparisons.
- Neglecting to analyze the solution, missing insights into why certain variables are at their bounds.

# Workflow 2 (Modeling Framework: Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo modeling abstraction to declaratively define the optimization problem. It separates model specification from solver execution, facilitating maintainability and easy switching between solvers like HiGHS or CBC.

### Step 1 - Declare Model and Sets
- Create a `ConcreteModel` for deterministic problems with known data.
- Define a Pyomo `Set` to represent the index for items (e.g., products, activities).

### Step 2 - Define Parameters and Variables
- Use Python data structures (lists, dicts) to hold parameter values, which are referenced during model construction.
- Declare a continuous `Var` indexed by the set, specifying its `domain` (e.g., `NonNegativeReals`) and applying individual bounds via a `bounds` rule or `setlb`/`setub`.

### Step 3 - Construct Objective and Constraints
- Define the objective using Pyomo's `Objective` component with an expression summing profit coefficients.
- Formulate the resource constraint as a `Constraint` with a linear inequality expression.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit_i[I]",
    "consumption_i[I]",
    "lb_i[I]",
    "ub_i[I]",
    "capacity"
  ],
  "decision_variables": ["model.x[i] (continuous, i in I)"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_i[i] * model.x[i] for i in I)"
  },
  "constraints": [
    "bounds: model.x[i].setlb(lb_i[i]); model.x[i].setub(ub_i[i])",
    "resource: sum(consumption_i[i] * model.x[i] for i in I) <= capacity"
  ]
}
```

### Common Pitfalls
- Confusing `AbstractModel` with `ConcreteModel`; use `ConcreteModel` when all data is available at build time.
- Incorrectly defining bounds inside a rule that doesn't properly index the model instance.
- Writing constraint expressions that inadvertently create multiple constraint objects instead of a single indexed constraint.

## Solving stage

### Strategy Overview
The solving stage configures the chosen solver, executes the model, and implements robust result handling. It emphasizes checking solver status and termination condition before extracting results.

### Step 1 - Configure and Execute Solver
- Instantiate a solver via `SolverFactory` (e.g., `'highs'`, `'cbc'`).
- Set appropriate options such as time limit (`seconds`), optimality tolerance (`ratio`), and number of threads.

### Step 2 - Validate Solution Status
- After solving, check `results.solver.status` equals `SolverStatus.ok`.
- Verify `results.solver.termination_condition` is `optimal` or `feasible`. Handle other conditions (infeasible, unbounded) explicitly.

### Step 3 - Extract Results and Verify
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate through variables to get their values and recalculate derived quantities (e.g., total resource used) for validation.
- Optionally, solve both continuous and integer versions of the model to quantify the integrality gap.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
for i in model.I:
    model.x[i].setlb(lb[i])
    model.x[i].setub(ub[i])
model.obj = pyo.Objective(expr=sum(profit[i] * model.x[i] for i in model.I), sense=pyo.maximize)
model.resource = pyo.Constraint(expr=sum(consumption[i] * model.x[i] for i in model.I) <= capacity)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'cbc'
results = solver.solve(model, tee=False)
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
    total_profit = pyo.value(model.obj)
    total_used = sum(consumption[i] * pyo.value(model.x[i]) for i in items)
    # Validation and further analysis
else:
    # Handle failure, e.g., print results.solver.termination_condition
```

### Common Pitfalls
- Assuming a solved model is optimal without checking `termination_condition`.
- Not using `pyo.value()` to extract numeric values from Pyomo components.
- Setting solver options incorrectly (e.g., wrong parameter names for the specific solver).
