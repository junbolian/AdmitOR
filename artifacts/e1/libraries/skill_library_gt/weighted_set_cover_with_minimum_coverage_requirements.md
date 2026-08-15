---
name: Weighted Set Cover with Minimum Coverage Requirements
description: |
  Model and solve binary selection problems where each requirement needs a minimum number of covering items, minimizing total selection cost.
---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using OR-Tools' linear solver wrapper. This approach is suitable for rapid prototyping and leverages efficient, open-source solvers like SCIP or CBC.

### Step 1 - Define Problem Data
- Define the set of selectable items (e.g., teams, facilities) and the set of coverage requirements.
- Create a dictionary mapping each requirement to the subset of items that can satisfy it.
- Define a cost parameter for each selectable item and a minimum coverage parameter for each requirement.

### Step 2 - Create Binary Decision Variables
- For each selectable item `i`, create a binary decision variable `x[i] ∈ {0,1}`.
- A value of 1 indicates the item is selected.

### Step 3 - Formulate Coverage Constraints
- For each requirement `r`, create a linear constraint: `∑_{i ∈ covering_set(r)} x[i] ≥ min_coverage[r]`.
- This ensures the requirement is covered by at least the specified minimum number of selected items.

### Step 4 - Define Linear Objective
- Define the objective to minimize the total weighted cost: `min ∑ cost[i] * x[i]`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items (e.g., teams).",
    "R: Set of coverage requirements (e.g., tasks)."
  ],
  "parameters": [
    "cost[i ∈ I]: Cost/weight of selecting item i.",
    "min_coverage[r ∈ R]: Minimum number of items required to cover requirement r.",
    "covering_set[r ∈ R]: Subset of items I that can cover requirement r."
  ],
  "decision_variables": [
    "x[i ∈ I] ∈ {0, 1}: 1 if item i is selected."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "coverage[r ∈ R]: sum(x[i] for i in covering_set[r]) >= min_coverage[r]"
  ]
}
```

### Common Pitfalls
- Using inefficient data structures (e.g., nested dictionaries) for large coverage matrices, leading to memory bloat.
- Hardcoding constraint logic with O(|I|*|R|) complexity instead of using precomputed covering sets.
- Mixing data types (lists vs. dictionaries) inconsistently, causing confusion and errors.

## Solving stage

### Strategy Overview
Solve the MIP model using OR-Tools' `pywraplp` interface, configure solver settings for performance, and implement robust solution verification and optimality checks.

### Step 1 - Initialize Solver and Configure Settings
- Create a solver instance (e.g., `SCIP` or `CBC`).
- Set a reasonable time limit (`solver.SetTimeLimit(ms)`).
- Optionally, set the number of threads for parallel processing.

### Step 2 - Build and Solve the Model
- Instantiate variables, constraints, and the objective as defined in the modeling stage.
- Call `solver.Solve()` and capture the status.

### Step 3 - Extract and Verify Solution
- If the status is `OPTIMAL` or `FEASIBLE`, extract selected items where `x[i].solution_value() > 0.5`.
- Calculate the total cost from the objective value or by summing costs of selected items.
- Verify all coverage constraints are satisfied by the extracted solution.

### Step 4 - Confirm Optimality (Optional)
- To mathematically confirm optimality, add a new constraint: `∑ cost[i] * x[i] ≤ (current_best_cost - ε)`.
- Re-solve; infeasibility proves the original solution was optimal.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

# 1. Define data (example placeholders)
items = [...]  # List of item identifiers
requirements = [...]  # List of requirement identifiers
cost = {i: cost_value for i in items}
min_coverage = {r: min_value for r in requirements}
covering_set = {r: [list_of_items] for r in requirements}

# 2. Initialize solver
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(30000)  # 30 seconds

# 3. Create variables
x = {i: solver.IntVar(0, 1, f'x_{i}') for i in items}

# 4. Add constraints
for r in requirements:
    constraint = solver.Constraint(min_coverage[r], solver.infinity(), f'cov_{r}')
    for i in covering_set[r]:
        constraint.SetCoefficient(x[i], 1)

# 5. Set objective
objective = solver.Objective()
for i in items:
    objective.SetCoefficient(x[i], cost[i])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [i for i in items if x[i].solution_value() > 0.5]
    total_cost = objective.Value()
    # Verification loop
    for r in requirements:
        actual = sum(1 for i in covering_set[r] if i in selected)
        assert actual >= min_coverage[r], f"Requirement {r} not met."
    print(f"Solution found. Cost: {total_cost}, Selected: {selected}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Setting overly aggressive time limits for small problems, wasting resources.
- Enabling verbose solver output (`tee=True`) in production without proper logging controls.
- Implementing redundant verification logic that duplicates the solver's feasibility guarantee without adding value.

# Workflow 2 (Pyomo with CBC/Highs)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model syntax, which provides a structured, maintainable approach and easy integration with various solvers like CBC or HiGHS.

### Step 1 - Define Model Components
- Create a Pyomo `ConcreteModel`.
- Define `Set` components for items and requirements.
- Define `Param` components for costs, minimum coverage, and the coverage mapping.

### Step 2 - Declare Decision Variables
- Declare binary variables `model.x[i]` using `pyo.Var(model.I, within=pyo.Binary)`.

### Step 3 - Define Constraints via Rules
- Define a constraint rule for each requirement `r` that returns the expression `sum(model.x[i] for i in model.covering_set[r]) >= model.min_coverage[r]`.

### Step 4 - Define the Objective
- Define the objective as `pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "I: pyo.Set() of selectable items.",
    "R: pyo.Set() of coverage requirements."
  ],
  "parameters": [
    "cost: pyo.Param(I) defining selection costs.",
    "min_coverage: pyo.Param(R) defining minimum required coverage.",
    "covering_set: pyo.Param(R, within=pyo.Any) or a rule mapping R to subsets of I."
  ],
  "decision_variables": [
    "x: pyo.Var(I, within=pyo.Binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "coverage_rule(r ∈ R): sum(x[i] for i in covering_set[r]) >= min_coverage[r]"
  ]
}
```

### Common Pitfalls
- Using sparse dictionary representations for large coverage matrices without considering memory efficiency.
- Defining constraint rules that inefficiently iterate over all items for each requirement.
- Inconsistent use of Pyomo components (mixing `AbstractModel` and `ConcreteModel` patterns).

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., `cbc` or `highs`), handle solver status and termination conditions carefully, and implement post-solution verification.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory('cbc')`.
- Set solver options: time limit (`seconds`), optimality gap (`ratio`), and threads.

### Step 2 - Solve and Check Termination
- Call `results = solver.solve(model, tee=False)`.
- Check both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`).

### Step 3 - Load Solution and Extract Results
- If a solution exists, load it into the model (`model.solutions.load_from(results)`).
- Extract selected items where `pyo.value(model.x[i]) > 0.5`.
- Calculate total cost and verify all constraints.

### Step 4 - Handle Edge Cases
- If the solver fails or returns no feasible solution, catch exceptions and provide informative error messages.
- For optimality verification, add a cost-bound constraint and re-solve.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

# 1. Create model and define data
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)  # items list
model.R = pyo.Set(initialize=requirements)  # requirements list
model.cost = pyo.Param(model.I, initialize=cost_dict)
model.min_coverage = pyo.Param(model.R, initialize=min_cov_dict)
# Assume covering_set_dict maps r -> list of items
def covering_set_rule(m, r):
    return covering_set_dict[r]
model.covering_set = pyo.Param(model.R, initialize=covering_set_rule)

# 2. Decision variables
model.x = pyo.Var(model.I, within=pyo.Binary)

# 3. Coverage constraints
def coverage_constraint_rule(m, r):
    return sum(m.x[i] for i in m.covering_set[r]) >= m.min_coverage[r]
model.coverage = pyo.Constraint(model.R, rule=coverage_constraint_rule)

# 4. Objective
model.obj = pyo.Objective(
    expr=sum(model.cost[i] * model.x[i] for i in model.I),
    sense=pyo.minimize
)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0  # for optimality

try:
    results = solver.solve(model, tee=False)
    status = results.solver.status
    term = results.solver.termination_condition

    if status == pyo.SolverStatus.ok and term in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
        # Load solution explicitly if needed
        # model.solutions.load_from(results)
        selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
        total_cost = pyo.value(model.obj)
        # Verification
        for r in model.R:
            actual = sum(1 for i in model.covering_set[r] if pyo.value(model.x[i]) > 0.5)
            assert actual >= pyo.value(model.min_coverage[r])
        print(f"Solution found. Cost: {total_cost}, Selected: {selected}")
    else:
        print(f"Solver failed. Status: {status}, Termination: {term}")
except Exception as e:
    print(f"Solver error: {e}")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to misinterpretation of results.
- Using `load_solutions=True` without handling cases where no solution exists, causing loading errors.
- Setting solver options (like `ratio`, `threads`) without understanding their impact on performance or solution quality.
