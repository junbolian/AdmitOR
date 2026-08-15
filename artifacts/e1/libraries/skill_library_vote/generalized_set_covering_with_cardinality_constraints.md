---
name: Generalized Set Covering with Cardinality Constraints
description: |
  Model and solve binary selection problems with set covering constraints requiring minimum coverage per requirement, minimizing total cost.
---

# Workflow 1 (CP-SAT via OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as a binary linear program suitable for constraint programming solvers, focusing on efficient Boolean variable and linear constraint representation.

### Step 1 - Define Selection Variables
- Create a binary decision variable `x[i]` for each selectable item `i` in the set `I`.
- The variable equals 1 if item `i` is selected, 0 otherwise.

### Step 2 - Map Coverage Relationships
- Define a set of requirements `J`.
- For each requirement `j` in `J`, define a parameter `r_j` for the minimum required coverage.
- Create a mapping `S_j` (a list or set) containing all items `i` in `I` that can satisfy requirement `j`.

### Step 3 - Formulate Cardinality Covering Constraints
- For each requirement `j` in `J`, add a linear constraint: `sum_{i in S_j} x[i] >= r_j`.
- This ensures the selected items provide sufficient coverage for each requirement.

### Step 4 - Define Cost Minimization Objective
- Define a cost parameter `c_i` for each item `i` in `I`.
- Set the objective to minimize the total selection cost: `min sum_{i in I} c_i * x[i]`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items.",
    "J: Set of coverage requirements."
  ],
  "parameters": [
    "c_i: Cost of selecting item i ∈ I.",
    "r_j: Minimum required coverage for requirement j ∈ J.",
    "S_j: List of items i ∈ I that cover requirement j ∈ J."
  ],
  "decision_variables": [
    "x_i ∈ {0, 1} for i ∈ I"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} c_i * x_i"
  },
  "constraints": [
    "Coverage: sum_{i in S_j} x_i >= r_j for all j ∈ J"
  ]
}
```

### Common Pitfalls
- Using integer variables instead of pure binary variables, which reduces solver efficiency.
- Incorrectly defining the coverage mapping `S_j`, leading to infeasible or incorrect solutions.
- Forgetting to validate that all `r_j` values are non-negative integers.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' CP-SAT solver, configuring it for exact optimization with runtime control and parallel search.

### Step 1 - Instantiate Model and Variables
- Create a `cp_model.CpModel()` object.
- Create Boolean variables using `model.NewBoolVar()` for each item `i`.

### Step 2 - Add Constraints and Objective
- For each requirement `j`, create a linear constraint using `model.Add(sum(x[i] for i in S_j) >= r_j)`.
- Define the objective expression using `model.Minimize()`.

### Step 3 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` to control runtime.
- Set `solver.parameters.num_search_workers` to enable parallel search.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` for exact optimization.

### Step 4 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status: `cp_model.OPTIMAL` or `cp_model.FEASIBLE` indicates a solution was found.

### Step 5 - Verify Solution and Prove Optimality
- Extract the solution and verify all coverage constraints are satisfied programmatically.
- To prove optimality, add a new constraint forcing the objective value to be less than the found cost and attempt to solve; infeasibility confirms optimality.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in items}

# Coverage constraints
for j in requirements:
    model.Add(sum(x[i] for i in coverage_sets[j]) >= requirement[j])

# Objective
model.Minimize(sum(cost[i] * x[i] for i in items))

# Solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters (e.g., solver.parameters.max_time_in_seconds = 30)
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected = [i for i in items if solver.Value(x[i])]
    total_cost = solver.ObjectiveValue()
    # Verification loop
    for j in requirements:
        actual = sum(solver.Value(x[i]) for i in coverage_sets[j])
        assert actual >= requirement[j], f"Requirement {j} not met."
else:
    # Handle no solution found
    selected = []
    total_cost = None
```

### Common Pitfalls
- Not setting `relative_gap_limit` for exact optimization, leading to suboptimal solutions.
- Failing to verify the solver's status before extracting variable values.
- Omitting solution verification, which can miss subtle constraint violations.

# Workflow 2 (MIP via Pyomo with Commercial/Open Solver)

## Modeling stage

### Strategy Overview
Construct a Mixed-Integer Programming (MIP) model using Pyomo's abstract modeling capabilities, designed for compatibility with both commercial (e.g., Gurobi) and open-source (e.g., HiGHS) solvers.

### Step 1 - Define Pyomo Sets and Parameters
- Use `pyo.Set()` to define sets for items `I` and requirements `J`.
- Use `pyo.Param()` to define cost `c_i`, coverage requirement `r_j`, and the coverage mapping `S_j` (often implemented as a parameterized rule).

### Step 2 - Create Binary Variables
- Declare a Pyomo variable `model.x` indexed over `I` with `domain=pyo.Binary`.

### Step 3 - Implement Coverage Constraint Rule
- Define a function `coverage_rule(model, j)` that returns the inequality `sum(model.x[i] for i in S_j) >= r_j`.
- Create a constraint `model.coverage` indexed over `J` using this rule.

### Step 4 - Set Linear Objective
- Define the objective as `model.obj = pyo.Objective(expr=sum(c_i * model.x[i] for i in I), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "I: pyo.Set(initialize=items)",
    "J: pyo.Set(initialize=requirements)"
  ],
  "parameters": [
    "c: pyo.Param(I, initialize=cost_dict)",
    "r: pyo.Param(J, initialize=requirement_dict)",
    "S: Mapping J -> list of I (implemented via rule or external data)"
  ],
  "decision_variables": [
    "x: pyo.Var(I, domain=pyo.Binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(c[i] * x[i] for i in I)"
  },
  "constraints": [
    "coverage: sum(x[i] for i in S[j]) >= r[j] for all j in J"
  ]
}
```

### Common Pitfalls
- Using concrete data structures inside Pyomo rules, which can cause performance issues with large sets.
- Confusing Pyomo's `Set` initialization with immediate data iteration.
- Not decoupling the coverage mapping `S` from the model building logic, reducing reusability.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured external solver, implementing robust status checks, solution verification, and optimality confirmation.

### Step 1 - Select and Configure Solver
- Instantiate a solver via `pyo.SolverFactory("solver_name")` (e.g., "gurobi", "highs").
- Set key parameters: `TimeLimit`, `MIPGap` (use a small positive value like 1e-4 for optimality tolerance), `Threads`, and `Seed`.

### Step 2 - Solve and Capture Results
- Call `solver.solve(model, tee=True)` to solve and optionally print logs.
- Store the results object for status inspection.

### Step 3 - Check Solver Status and Termination
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `.feasible`.

### Step 4 - Extract and Verify Solution
- If status is good, extract variable values using `pyo.value(model.x[i]) > 0.5`.
- Programmatically verify each coverage constraint is satisfied.

### Step 5 - Prove Optimality (Optional)
- Add a new constraint: `sum(c_i * model.x[i] for i in I) <= best_cost - epsilon`.
- Re-solve; if infeasible, the original solution is optimal.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=requirements)

model.x = pyo.Var(model.I, domain=pyo.Binary)
model.cost = pyo.Param(model.I, initialize=cost_dict)
model.req = pyo.Param(model.J, initialize=requirement_dict)

def coverage_rule(m, j):
    # coverage_sets is an external mapping j -> list of i
    return sum(m.x[i] for i in coverage_sets[j]) >= m.req[j]
model.coverage = pyo.Constraint(model.J, rule=coverage_rule)

model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")  # or "gurobi"
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = -1

results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = pyo.value(model.obj)
    # Verification loop
    for j in model.J:
        actual = sum(pyo.value(model.x[i]) for i in coverage_sets[j] if pyo.value(model.x[i]) > 0.5)
        assert actual >= pyo.value(model.req[j]), f"Requirement {j} not met."
else:
    # Handle failed solve
    selected = []
    total_cost = None
```

### Common Pitfalls
- Setting a negative `MIPGap` value, which causes a solver error.
- Not checking both `solver.status` and `termination_condition`, leading to extraction from failed solves.
- Forgetting to use `pyo.value()` when accessing variable and parameter values post-solution.
