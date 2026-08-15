---
name: Generalized Set Covering with Binary Assignment
description: |
  Model and solve weighted set covering problems with binary selection variables, coverage requirements, and a linear cost objective using MILP solvers.

---

# Workflow 1 (OR-Tools Solver API)

## Modeling stage

### Strategy Overview
This workflow uses the OR-Tools linear solver wrapper (`pywraplp`) to directly construct a MILP model. It is suitable for rapid prototyping and deployment where a concise, imperative API is preferred.

### Step 1 - Define Data Structures
- Map problem data into Python dictionaries for costs, coverage requirements, and eligibility.
- Use `costs[item_id]` for the cost of selecting each item.
- Use `requirements[req_id]` for the minimum number of items required to cover each requirement.
- Use `eligibility[req_id]` to store the list of items eligible to satisfy each requirement.

### Step 2 - Create Binary Decision Variables
- Instantiate a solver object (e.g., `SCIP` or `CBC`).
- Create a binary decision variable `x[item_id]` for each item, representing its selection status (1 if selected, 0 otherwise).

### Step 3 - Formulate Coverage Constraints
- For each requirement `req_id`, create a linear constraint: the sum of `x[i]` for all `i` in `eligibility[req_id]` must be greater than or equal to `requirements[req_id]`.
- Name constraints descriptively (e.g., `f"cover_{req_id}"`) to aid in debugging.

### Step 4 - Define Linear Objective
- Construct the objective function as the sum of `costs[i] * x[i]` over all items.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "I: Set of items available for selection.",
    "J: Set of requirements to be covered."
  ],
  "parameters": [
    "c_i: Cost of selecting item i ∈ I.",
    "r_j: Minimum number of items required to cover requirement j ∈ J.",
    "E_j: Set of items i ∈ I eligible to cover requirement j ∈ J."
  ],
  "decision_variables": [
    "x_i ∈ {0, 1}: 1 if item i is selected, 0 otherwise."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} c_i * x_i"
  },
  "constraints": [
    "Coverage: ∑_{i ∈ E_j} x_i ≥ r_j, ∀ j ∈ J."
  ]
}
```

### Common Pitfalls
- Forgetting to convert solver variable objects to numerical values when building constraints (e.g., using `solver.Sum()` or Python's built-in `sum()` correctly).
- Not handling the case where a requirement has no eligible items, which makes the problem infeasible from the start.
- Using floating-point equality (`==`) for checking binary variable values post-solution; always use a tolerance (e.g., `> 0.5`).

## Solving stage

### Strategy Overview
Solve the constructed MILP model using the OR-Tools solver interface, focusing on status checking, solution extraction, and post-solution verification.

### Step 1 - Configure and Execute Solver
- Set solver parameters such as time limit (`solver.SetTimeLimit`) and number of threads if supported.
- Call `solver.Solve()` to initiate the optimization.

### Step 2 - Check Solver Status and Extract Solution
- Check if the status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses appropriately.
- If feasible, extract selected items by filtering for `x[i].solution_value() > 0.5`.
- Retrieve the objective value via `solver.Objective().Value()`.

### Step 3 - Verify Solution Feasibility
- Perform an independent verification by recalculating coverage for each requirement using the extracted solution.
- Compare against the original requirements to ensure all constraints are satisfied, guarding against potential solver tolerances.

### Step 4 - (Optional) Prove Optimality
- To mathematically confirm optimality, add a new constraint: `∑ c_i * x_i ≤ best_objective - ε`, where `ε` is a small positive constant.
- Re-solve; if the problem becomes infeasible, the original solution is optimal.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... [Variable and constraint creation as per Modeling Stage]

# Solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected_items = [i for i in all_items if x[i].solution_value() > 0.5]
    objective_value = solver.Objective().Value()
    # ... [Verification steps]
else:
    # Handle infeasible or other statuses
    selected_items, objective_value = None, None
```

### Common Pitfalls
- Assuming `OPTIMAL` status guarantees the solution meets all constraints exactly; always perform independent verification.
- Not setting a time limit for large instances, which can cause the process to hang.
- Misinterpreting the `FEASIBLE` status as optimal; it indicates a valid solution was found, but not necessarily the best possible.

# Workflow 2 (Pyomo with Highs/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to declaratively define the optimization model. It separates model specification from solver choice, offering flexibility and clarity, especially for complex constraints.

### Step 1 - Define Abstract Sets and Parameters
- Use Pyomo's `Set` and `Param` components to define the sets of items (`I`) and requirements (`J`).
- Declare parameters for costs (`c`), coverage requirements (`r`), and eligibility mapping (`E`).

### Step 2 - Declare Binary Variables and Objective
- Instantiate a `ConcreteModel`.
- Define binary variables `model.x` indexed over the set of items.
- Define the objective `model.obj` as the sum of costs multiplied by the corresponding variables.

### Step 3 - Define Coverage Constraints via Rules
- Create a constraint `model.cover` indexed over the set of requirements.
- For each requirement `j`, the constraint rule should return the expression `sum(model.x[i] for i in model.E[j]) >= model.r[j]`.
- This rule-based approach cleanly separates the model logic from data.

### Formulation Template
```json
{
  "sets": [
    "I: Set of items (index i).",
    "J: Set of requirements (index j)."
  ],
  "parameters": [
    "c[i]: Cost parameter for item i ∈ I.",
    "r[j]: Coverage requirement parameter for j ∈ J.",
    "E[j]: Set parameter containing eligible items i ∈ I for requirement j ∈ J."
  ],
  "decision_variables": [
    "x[i] ∈ {0, 1}: Binary selection variable for item i."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} c[i] * x[i]"
  },
  "constraints": [
    "cover[j]: ∑_{i ∈ E[j]} x[i] ≥ r[j], ∀ j ∈ J."
  ]
}
```

### Common Pitfalls
- Attempting to use Python data structures (lists/dicts) directly inside Pyomo constraint rules without first declaring them as Pyomo `Param` or `Set` objects.
- Defining constraints with mutable data; ensure parameters are initialized before model instantiation.
- Creating constraints for requirements with empty eligibility sets, which Pyomo may handle inconsistently; validate data first.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external MILP solver (e.g., Highs or CBC). Focus on the pattern of instantiating a solver, setting options, checking termination conditions, and safely loading solutions.

### Step 1 - Instantiate Solver and Set Options
- Use `SolverFactory` to create a solver instance (e.g., `"highs"` or `"cbc"`).
- Set options such as `time_limit`, `mip_rel_gap` (to `0.0` for exact solution), and `threads`.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model, ...)` with `load_solutions=False` to separate solving from solution loading.
- Check the solver status (`model.solver.status`) is `SolverStatus.ok` and the termination condition (`model.solver.termination_condition`) is `optimal` or `feasible`.

### Step 3 - Load Solution and Extract Results
- If status checks pass, call `model.solutions.load_from(...)` to populate variable values.
- Extract selected items by iterating over `model.x` and checking `value(model.x[i]) > 0.5`.
- Obtain the objective value via `value(model.obj)`.

### Step 4 - Verify and Validate
- Recompute coverage sums using the extracted solution and the original eligibility data.
- Assert that all requirements are met, providing a critical check against solver numerical errors.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
# ... [Set, Parameter, Variable, Objective, and Constraint definition as per Modeling Stage]

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")
results = solver.solve(model, load_solutions=False, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    model.solutions.load_from(results)
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    objective_value = pyo.value(model.obj)
    # ... [Verification steps]
else:
    # Handle solver failure or infeasibility
    selected_items, objective_value = None, None
```

### Common Pitfalls
- Forgetting `load_solutions=False` and then trying to check variable values before the solution is loaded, leading to `None` values.
- Confusing `SolverStatus.ok` (the solver ran without error) with `TerminationCondition.optimal` (it found a proven optimal solution).
- Not using `pyo.value()` to extract numeric values from Pyomo components post-solution.
