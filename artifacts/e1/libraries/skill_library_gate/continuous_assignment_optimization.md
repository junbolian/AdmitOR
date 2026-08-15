---
name: Continuous Assignment Optimization
description: |
  Model and solve resource-to-task allocation problems with supply limits, demand requirements, and per-assignment caps using continuous variables to minimize total cost.
---

# Workflow 1 (OR-Tools LP)

## Modeling stage

### Strategy Overview
Formulate the allocation as a linear program using the OR-Tools CP-SAT (for LP) or GLOP backends. This workflow is suitable for direct, procedural model building with explicit variable bounds and constraint loops, ideal for integration into larger applications or when using the Google OR-Tools ecosystem.

### Step 1 - Define Data Structures
- Organize input parameters as indexed lists or dictionaries for clear access. For example, `availability[i]` for resource capacity, `requirement[j]` for task demand, `cost[i][j]` for unit costs, and `limit[i][j]` for per-assignment maximums.
- Use zero-based integer indexing for resources `i` in set `I` and tasks `j` in set `J`.

### Step 2 - Create Decision Variables
- Instantiate continuous, non-negative decision variables `x[i][j]` using `solver.NumVar(lower_bound, upper_bound, name)`.
- Set the `lower_bound` to 0.0 and the `upper_bound` directly to `limit[i][j]` to enforce per-assignment caps during variable creation.

### Step 3 - Formulate Supply and Demand Constraints
- For each resource `i`, add a supply constraint: `sum(x[i][j] for j in J) <= availability[i]`.
- For each task `j`, add a demand constraint: `sum(x[i][j] for i in I) >= requirement[j]`. Use `>=` for flexibility or `==` for exact requirement.

### Step 4 - Set Linear Objective
- Define the objective as the sum of cost-weighted assignments: `minimize sum(cost[i][j] * x[i][j] for i in I for j in J)`.
- Use `solver.Minimize()` or `objective.SetMinimization()` after setting all coefficients.

### Formulation Template
```json
{
  "sets": ["I (resources)", "J (tasks)"],
  "parameters": [
    "availability[i] ∈ ℝ⁺",
    "requirement[j] ∈ ℝ⁺",
    "cost[i][j] ∈ ℝ",
    "limit[i][j] ∈ ℝ⁺"
  ],
  "decision_variables": ["x[i][j] ∈ ℝ⁺, 0 ≤ x[i][j] ≤ limit[i][j]"],
  "objective": {
    "sense": "min",
    "expression": "∑_i ∑_j cost[i][j] * x[i][j]"
  },
  "constraints": [
    "Supply: ∑_j x[i][j] ≤ availability[i], ∀i ∈ I",
    "Demand: ∑_i x[i][j] ≥ requirement[j], ∀j ∈ J"
  ]
}
```

### Common Pitfalls
- Forgetting to set the upper bound on variables during creation, leading to a model without per-assignment limits.
- Using `==` for demand constraints when total supply is tight, which can cause unnecessary infeasibility; `>=` is often more robust.
- Not verifying that the sum of all `availability[i]` meets or exceeds the sum of all `requirement[j]` before solving, a common cause of infeasibility.

## Solving stage

### Strategy Overview
Solve the built LP model using the OR-Tools wrapper, check the solution status rigorously, extract results, and perform post-solve verification to ensure correctness and feasibility.

### Step 1 - Select and Configure Solver
- For a pure LP, use `pywraplp.Solver.CreateSolver('GLOP')`. For consistency with potential integer extensions, `pywraplp.Solver.CreateSolver('SAT')` (CP-SAT) also handles LPs.
- Set time limits or other solver-specific parameters if needed (e.g., `solver.SetTimeLimit(limit_in_milliseconds)`).

### Step 2 - Solve and Check Status
- Execute `solver.Solve()`.
- Check the result status: `status == pywraplp.Solver.OPTIMAL` or `status == pywraplp.Solver.FEASIBLE`. Handle other statuses (INFEASIBLE, UNBOUNDED) with appropriate error messages or fallback logic.

### Step 3 - Extract and Filter Solution
- Retrieve the objective value via `solver.Objective().Value()`.
- Iterate over all variables `x[i][j]` and get their values with `var.solution_value()`.
- Apply a tolerance (e.g., `1e-6`) to filter out near-zero assignments for cleaner reporting.

### Step 4 - Verify Solution Feasibility
- Programmatically recompute total allocations per resource and per task.
- Verify that supply constraints, demand constraints, and per-assignment bounds are satisfied within a small numerical tolerance (e.g., `1e-5`).
- Log or report any significant violations for debugging.

### Code Usage
```python
# Example using OR-Tools CP-SAT for LP
from ortools.sat.python import cp_model

# Build model
model = cp_model.CpModel()
x = {}
for i in I:
    for j in J:
        x[i, j] = model.NewNumVar(0.0, limit[i][j], f'x_{i}_{j}')

# Supply constraints
for i in I:
    model.Add(sum(x[i, j] for j in J) <= availability[i])

# Demand constraints
for j in J:
    model.Add(sum(x[i, j] for i in I) >= requirement[j])

# Objective
model.Minimize(sum(cost[i][j] * x[i, j] for i in I for j in J))

# Solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters if needed, e.g., solver.parameters.max_time_in_seconds = 30.0
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    obj_value = solver.ObjectiveValue()
    assignments = []
    for i in I:
        for j in J:
            val = solver.Value(x[i, j])
            if val > 1e-6:
                assignments.append((i, j, val))
    # ... verification and output
else:
    # Handle infeasible or error status
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Assuming `FEASIBLE` status guarantees optimality; it does not. Check for `OPTIMAL` if the exact optimum is required.
- Not using a tolerance when checking variable values against bounds, leading to false failures due to floating-point precision.
- Omitting post-solve verification, which can miss modeling errors that the solver might not explicitly report.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Formulate the problem using Pyomo's abstract or concrete modeling paradigm, separating data from model structure. This approach is declarative, promotes reusability, and leverages Pyomo's integration with solvers like HiGHS (for LP) or CBC (for LP/MILP).

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for resources (`model.I`) and tasks (`model.J`).
- Declare `Param` objects for `availability`, `requirement`, `cost`, and `limit`, indexed by the appropriate sets. Initialize them from external data dictionaries.

### Step 2 - Declare Decision Variables
- Create a continuous, non-negative variable `model.x` indexed over `model.I` and `model.J` using `pyo.Var(domain=pyo.NonNegativeReals)`.
- Enforce per-assignment upper bounds via explicit constraints in the next step, not variable bounds, for clarity within the Pyomo structure.

### Step 3 - Construct Constraints via Rules
- Define a rule for supply constraints: for each `i` in `model.I`, `sum(model.x[i,j] for j in model.J) <= model.availability[i]`.
- Define a rule for demand constraints: for each `j` in `model.J`, `sum(model.x[i,j] for i in model.I) >= model.requirement[j]`.
- Define a rule for per-assignment limits: for each `(i,j)` in `model.I * model.J`, `model.x[i,j] <= model.limit[i,j]`.

### Step 4 - Set the Objective
- Define the objective expression as `sum(model.cost[i,j] * model.x[i,j] for i in model.I for j in model.J)`.
- Instantiate it as a `pyo.Objective` with `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["I (resources)", "J (tasks)"],
  "parameters": [
    "availability[i] ∈ ℝ⁺",
    "requirement[j] ∈ ℝ⁺",
    "cost[i][j] ∈ ℝ",
    "limit[i][j] ∈ ℝ⁺"
  ],
  "decision_variables": ["x[i][j] ∈ ℝ⁺"],
  "objective": {
    "sense": "min",
    "expression": "∑_i ∑_j cost[i][j] * x[i][j]"
  },
  "constraints": [
    "Supply: ∑_j x[i][j] ≤ availability[i], ∀i ∈ I",
    "Demand: ∑_i x[i][j] ≥ requirement[j], ∀j ∈ J",
    "PerAssignment: x[i][j] ≤ limit[i][j], ∀i ∈ I, ∀j ∈ J"
  ]
}
```

### Common Pitfalls
- Initializing `Param` objects with incomplete data, causing KeyError during rule execution. Ensure all required indices are present.
- Using Python's `sum` inside Pyomo rules on large sets can be slow; prefer generator expressions or built-in Pyomo summation.
- Confusing abstract and concrete model paradigms; choose one consistently to avoid initialization errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver factory (e.g., HiGHS for LP, CBC for LP/MILP), perform comprehensive status checks, extract results, and verify feasibility programmatically.

### Step 1 - Instantiate Solver with Options
- Use `SolverFactory('highs')` for linear problems or `SolverFactory('cbc')` for broader compatibility.
- Configure key options: `solver.options['time_limit']` for runtime control, and for CBC, `solver.options['ratio']=0.0` to seek an optimal solution.

### Step 2 - Solve and Validate Status
- Execute `results = solver.solve(model, tee=False)` (set `tee=True` for verbose output).
- Check both the solver status (`results.solver.status == SolverStatus.ok`) and the termination condition (`results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`).

### Step 3 - Extract Solution Values
- Retrieve the objective value via `pyo.value(model.obj)`.
- Access variable values using `pyo.value(model.x[i,j])`. Store non-zero assignments (e.g., `> 1e-6`) for reporting.

### Step 4 - Post-Solution Verification and Reporting
- Loop through all constraints to compute actual left-hand side values and compare them to right-hand side bounds within tolerance.
- Generate a summary report showing resource utilization, task fulfillment, and a list of significant assignments.

### Code Usage
```python
# Example using Pyomo with HiGHS
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# Build concrete model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=resources)
model.J = pyo.Set(initialize=tasks)

model.availability = pyo.Param(model.I, initialize=availability_dict)
model.requirement = pyo.Param(model.J, initialize=requirement_dict)
model.cost = pyo.Param(model.I, model.J, initialize=cost_dict)
model.limit = pyo.Param(model.I, model.J, initialize=limit_dict)

model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

def supply_rule(m, i):
    return sum(m.x[i, j] for j in m.J) <= m.availability[i]
model.supply = pyo.Constraint(model.I, rule=supply_rule)

def demand_rule(m, j):
    return sum(m.x[i, j] for i in m.I) >= m.requirement[j]
model.demand = pyo.Constraint(model.J, rule=demand_rule)

def limit_rule(m, i, j):
    return m.x[i, j] <= m.limit[i, j]
model.per_assign = pyo.Constraint(model.I, model.J, rule=limit_rule)

model.obj = pyo.Objective(expr=sum(m.cost[i,j] * m.x[i,j] for i in m.I for j in m.J), sense=pyo.minimize)

# Solve with status / termination checks
solver = SolverFactory('highs')
results = solver.solve(model)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    obj_val = pyo.value(model.obj)
    # Extract and verify solution...
else:
    # Handle infeasible or error status
    print(f"Solver terminated: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to extraction errors from suboptimal or interrupted solves.
- Modifying the model object after solving without cloning, which can corrupt the solved state.
- Assuming the solver's feasibility report is absolute; always implement independent verification to catch numerical issues.
