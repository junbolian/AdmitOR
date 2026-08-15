---
name: Continuous Resource Allocation with Linear Coverage Constraints
description: |
  Model and solve linear programs with continuous decision variables, linear cost minimization, and double-sided linear coverage constraints using structured data and solver-aware patterns.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling style, leveraging its expressive constraint rules and indexed sets for scalability. This approach cleanly separates data from model structure, enabling easy modification and reuse.

### Step 1 - Define Indexed Sets and Parameters
- Define sets for selectable items (e.g., `items`) and coverage requirements (e.g., `requirements`).
- Declare parameters: cost per item, contribution matrix (item × requirement), and lower/upper bounds for each requirement.
- Use Pyomo `Param` objects to store data, enabling model updates without structural changes.

### Step 2 - Declare Continuous Decision Variables
- Create a continuous, non-negative decision variable for each item (e.g., `Buy[i]`).
- Apply individual variable bounds (e.g., `(0, max_amount)`) directly during variable declaration to reduce constraint count.

### Step 3 - Formulate Double-Sided Coverage Constraints
- For each requirement, create a single linear constraint with both lower and upper bounds using Pyomo's `Constraint(expr=(lower <= expression <= upper))` syntax.
- The constraint expression is the sum of contributions from all items: `sum(contribution[i, j] * Buy[i] for i in items)`.

### Step 4 - Define Linear Cost Objective
- Formulate the objective as the minimization of total linear cost: `sum(cost[i] * Buy[i] for i in items)`.
- Set the objective sense to `minimize`.

### Formulation Template
```json
{
  "sets": ["items", "requirements"],
  "parameters": [
    "cost[items]",
    "min_req[requirements]",
    "max_req[requirements]",
    "contribution[items, requirements]"
  ],
  "decision_variables": ["Buy[items] (continuous, bounded)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * Buy[i] for i in items)"
  },
  "constraints": [
    "coverage[requirements]: min_req[j] <= sum(contribution[i, j] * Buy[i] for i in items) <= max_req[j]"
  ]
}
```

### Common Pitfalls
- Hardcoding parameter values inside constraint rules, which prevents model reuse.
- Creating separate `>=` and `<=` constraints instead of a single double-sided inequality, increasing model size unnecessarily.
- Forgetting to set variable bounds, leading to unbounded variables if not constrained by coverage requirements.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC LP solver, configured for reliability and numerical stability. The workflow includes explicit solution verification to ensure constraints are satisfied within tolerance.

### Step 1 - Instantiate Solver and Configure Options
- Create a solver object using `SolverFactory("highs")` or `SolverFactory("cbc")`.
- Set essential options: time limit (`"time_limit"`), presolve (`"presolve": "on"`), and optionally threads (avoiding conflicts).

### Step 2 - Solve and Check Termination Status
- Call `solver.solve(model, tee=False)` to execute the solver.
- Inspect `results.solver.status` and `results.solver.termination_condition` to confirm optimal or feasible termination.

### Step 3 - Extract and Verify Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Retrieve variable values via `pyo.value(model.Buy[i])`.
- Programmatically verify all coverage constraints are satisfied within a small tolerance (e.g., 1e-6) by recomputing totals.

### Step 4 - Handle Solver Failures
- If status is not `ok` or termination is not `optimal`/`feasible`, raise an informative exception or trigger a feasibility diagnostic routine.
- For infeasibility, consider solving a relaxed model to identify conflicting constraints.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (using formulation template)
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=range(num_items))
model.requirements = pyo.Set(initialize=range(num_reqs))
# ... populate parameters, variables, objective, constraints as per steps

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    # Verification loop
    for j in model.requirements:
        total = sum(pyo.value(model.contribution[i, j]) * pyo.value(model.Buy[i]) for i in model.items)
        assert (pyo.value(model.min_req[j]) - 1e-6 <= total <= pyo.value(model.max_req[j]) + 1e-6)
    opt_cost = float(pyo.value(model.obj))
else:
    raise Exception(f"Solver failed: {status}, {term}")
```

### Common Pitfalls
- Misinterpreting solver status; `ok` only indicates normal completion, not optimality.
- Not verifying constraints post-solve, potentially accepting numerically infeasible solutions.
- Setting conflicting solver options (e.g., thread count) that cause initialization errors.

# Workflow 2 (Google OR-Tools LP Solver)

## Modeling stage

### Strategy Overview
Model the problem directly using the OR-Tools linear solver API (GLOP, CBC). This imperative style builds the model step-by-step, offering fine-grained control and immediate access to solver-specific features.

### Step 1 - Initialize Solver and Define Infinity
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("GLOP")`.
- Define a large numeric value (e.g., `solver.infinity()`) to represent unbounded bounds where applicable.

### Step 2 - Create Continuous Variables with Bounds
- For each item, create a continuous variable: `var[i] = solver.NumVar(lower_bound, upper_bound, name)`.
- Store variables in a list or dictionary for easy reference in constraints.

### Step 3 - Add Double-Sided Coverage Constraints
- For each requirement, create two linear constraints: a lower bound (`>=`) and an upper bound (`<=`).
- Build each constraint by summing the product of contribution coefficients and variables: `solver.Add(sum(contribution[i][j] * var[i]) >= min_req[j])`.

### Step 4 - Set Linear Minimization Objective
- Create the objective: `objective = solver.Objective()`.
- For each variable, set its coefficient using `objective.SetCoefficient(var[i], cost[i])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["items", "requirements"],
  "parameters": [
    "cost[items]",
    "min_req[requirements]",
    "max_req[requirements]",
    "contribution[items][requirements]"
  ],
  "decision_variables": ["amount[items] (continuous, bounded)"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * amount[i] for i in items)"
  },
  "constraints": [
    "lower[requirements]: sum(contribution[i][j] * amount[i] for i in items) >= min_req[j]",
    "upper[requirements]: sum(contribution[i][j] * amount[i] for i in items) <= max_req[j]"
  ]
}
```

### Common Pitfalls
- Using the same constraint object for both lower and upper bounds; they must be separate constraints in OR-Tools.
- Forgetting to call `SetMinimization()` on the objective, defaulting to maximization.
- Not defining variable bounds, leaving them unbounded and potentially causing solver errors.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools solver, leveraging its efficient LP algorithms. The workflow includes solution extraction, optimality verification, and optional cross-validation with different solver backends.

### Step 1 - Execute Solver and Check Result Status
- Call `result_status = solver.Solve()`.
- Check if result is `pywraplp.Solver.OPTIMAL` or `FEASIBLE`. Handle other statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) appropriately.

### Step 2 - Extract Objective and Variable Values
- Get optimal cost: `opt_cost = objective.Value()`.
- Retrieve each variable's solution: `sol_val = var[i].solution_value()`.

### Step 3 - Verify Solution Against Constraints
- Recompute the left-hand side of each coverage constraint using the solution values.
- Assert results are within bounds, accounting for a small numerical tolerance.

### Step 4 - (Optional) Confirm Optimality via Infeasibility Test
- Add a new constraint forcing the objective value to be strictly less than the found optimum (e.g., `opt_cost - epsilon`).
- Re-solve; infeasibility confirms optimality.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
inf = solver.infinity()

# Create variables
vars = [solver.NumVar(lower_bound[i], upper_bound[i], f"x{i}") for i in range(num_items)]

# Add constraints
for j in range(num_reqs):
    # Lower bound constraint
    ct_lower = solver.Constraint(min_req[j], inf)
    # Upper bound constraint
    ct_upper = solver.Constraint(-inf, max_req[j])
    for i in range(num_items):
        coeff = contribution[i][j]
        ct_lower.SetCoefficient(vars[i], coeff)
        ct_upper.SetCoefficient(vars[i], coeff)

# Set objective
objective = solver.Objective()
for i in range(num_items):
    objective.SetCoefficient(vars[i], cost[i])
objective.SetMinimization()

# solve with status / termination checks
result_status = solver.Solve()
if result_status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    opt_cost = objective.Value()
    # Verification
    for j in range(num_reqs):
        total = sum(contribution[i][j] * vars[i].solution_value() for i in range(num_items))
        assert min_req[j] - 1e-6 <= total <= max_req[j] + 1e-6
else:
    raise Exception(f"Solver returned status: {result_status}")
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; it may indicate a suboptimal solution if the solver hit a time limit.
- Not using `solver.infinity()` for unbounded sides, causing incorrect constraint bounds.
- Misindexing the contribution matrix when building constraints, leading to incorrect model formulation.
