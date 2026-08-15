---
name: Weighted Set Covering with Multi-Coverage
description: |
  Model and solve weighted set covering problems with binary selection variables, multi-coverage requirements, and cost minimization objectives using integer programming solvers.

---
# Workflow 1 (CP-SAT for Exact Binary Optimization)

## Modeling stage

### Strategy Overview
Formulate the problem as a binary integer program suitable for constraint programming and SAT solvers, focusing on efficient linear constraint representation and mandatory variable fixing to reduce search space.

### Step 1 - Define Core Data Structures
- Represent the set of selectable items (e.g., teams, resources) and the set of elements requiring coverage (e.g., areas, tasks).
- Store coverage relationships as a mapping from each element to a list of items that can cover it.
- Define parameters: cost per item, and minimum required coverage count per element.

### Step 2 - Create Binary Decision Variables
- Declare a binary variable `x[i]` for each item `i`, where `x[i] = 1` indicates selection.
- Optionally, pre-fix variables to `1` for items that are mandatory due to coverage requirements (e.g., if an element's requirement equals the number of covering items).

### Step 3 - Formulate Coverage Constraints
- For each element `e`, create a linear constraint: the sum of `x[i]` for all items `i` that cover `e` must be at least the required coverage count `R[e]`.
- Validate problem feasibility by checking that no requirement exceeds the total number of covering items for any element.

### Step 4 - Define Linear Objective
- Formulate the objective to minimize total selection cost: sum of `cost[i] * x[i]` over all items.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "E: set of elements requiring coverage"
  ],
  "parameters": [
    "cost[i ∈ I]: cost of selecting item i",
    "R[e ∈ E]: required coverage count for element e",
    "cover[e ∈ E]: list of items i ∈ I that cover element e"
  ],
  "decision_variables": [
    "x[i ∈ I]: binary, 1 if item i is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "coverage[e ∈ E]: sum(x[i] for i in cover[e]) >= R[e]"
  ]
}
```

### Common Pitfalls
- Attempting to solve an infeasible model because a coverage requirement exceeds available items. Always pre-validate.
- Using floating-point costs or coefficients, which can cause precision issues; use integers where possible.
- Neglecting to fix mandatory variables, which wastes solver time on trivial decisions.

## Solving stage

### Strategy Overview
Solve the binary model using OR-Tools CP-SAT, configuring for exact optimization with parallelism and time limits, followed by solution verification and optimality confirmation.

### Step 1 - Configure Solver Parameters
- Set `max_time_in_seconds` to enforce a runtime limit.
- Enable parallelism with `num_search_workers`.
- Set `random_seed` for reproducibility.
- Enforce exact optimality by setting `relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Invoke the solver and capture the status code.
- Interpret status: `OPTIMAL` indicates proven optimum, `FEASIBLE` indicates a feasible solution found within limits, `INFEASIBLE` indicates no solution exists.

### Step 3 - Extract and Verify Solution
- If status is `OPTIMAL` or `FEASIBLE`, extract the values of all binary variables.
- Post-solve, compute the actual coverage for each element to verify all constraints are satisfied, guarding against solver tolerances.

### Step 4 - Confirm Optimality (Optional)
- For `OPTIMAL` status, optimality is proven by the solver. To double-check, add a constraint forcing total cost below the incumbent and attempt to solve; infeasibility confirms optimality.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in items}

# Objective
model.Minimize(sum(cost[i] * x[i] for i in items))

# Coverage constraints
for e in elements:
    covering_items = coverage[e]
    model.Add(sum(x[i] for i in covering_items) >= requirements[e])

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = solver_timeout
solver.parameters.num_search_workers = num_workers
solver.parameters.random_seed = random_seed
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

# Interpret result
if status == cp_model.OPTIMAL:
    print("Optimal solution found.")
elif status == cp_model.FEASIBLE:
    print("Feasible solution found (time/limit reached).")
elif status == cp_model.INFEASIBLE:
    print("Problem is infeasible.")
else:
    print("Solver returned unknown status.")

# Extract solution if feasible
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    selected_items = [i for i in items if solver.Value(x[i]) == 1]
    # Verification
    for e in elements:
        actual_coverage = sum(solver.Value(x[i]) for i in coverage[e])
        assert actual_coverage >= requirements[e], f"Coverage failed for {e}"
```

### Common Pitfalls
- Misinterpreting `FEASIBLE` as `OPTIMAL`; always check the status code.
- Not verifying constraints post-solve, which can miss violations due to numerical tolerances.
- Using default parameters for large problems, leading to excessive runtime; always set appropriate time limits and parallelism.

# Workflow 2 (MILP Solver via High-Level Modeling Library)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program using a high-level modeling library (e.g., PuLP, Pyomo), separating model abstraction from solver execution for flexibility and clarity.

### Step 1 - Organize Problem Data
- Define clear dictionaries or indexed sets for costs, coverage requirements, and coverage lists.
- Structure data to enable constraint building via list comprehensions or rule functions.

### Step 2 - Build Abstract Model
- Instantiate a problem object with a sense (minimize).
- Create binary decision variables indexed by the set of items.
- Add the linear objective function summing cost * variable.

### Step 3 - Add Indexed Constraints
- For each element, add a constraint that sums the decision variables over its covering item list, enforcing the minimum requirement.
- Leverage the modeling library's constraint abstraction to keep model definition clean.

### Step 4 - Perform Pre-Solve Analysis
- Identify and fix mandatory variables (e.g., where requirement equals list length) to reduce model size.
- Check for trivial infeasibility (requirement > number of covering items).

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "E: set of elements"
  ],
  "parameters": [
    "cost[i ∈ I]: selection cost",
    "R[e ∈ E]: required coverage",
    "cover[e ∈ E]: subset of I covering e"
  ],
  "decision_variables": [
    "x[i ∈ I]: binary selection variable"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(x[i] for i in cover[e]) >= R[e], for each e in E"
  ]
}
```

### Common Pitfalls
- Building dense constraint matrices unnecessarily; use sparse representation via coverage lists.
- Mixing solver-specific code within the model definition, reducing portability.
- Forgetting to convert solver results to binary values (e.g., checking `> 0.5`) due to floating-point outputs.

## Solving stage

### Strategy Overview
Solve the abstract model using a backend MILP solver (e.g., CBC via PuLP), handle solver statuses gracefully, and implement robust solution extraction and validation.

### Step 1 - Select and Configure Solver
- Choose an appropriate solver command (e.g., `PULP_CBC_CMD` for PuLP, `'cbc'` for Pyomo).
- Set solver options: time limit (`timeLimit`), optimality gap (`gapRel`), and thread count.

### Step 2 - Invoke Solver and Interpret Status
- Call the solver and capture the problem status.
- Map solver status to categories: `Optimal`, `Feasible` (non-optimal), `Infeasible`, `Unbounded`, or `Not Solved`.

### Step 3 - Extract and Validate Solution
- If status indicates a feasible solution, extract variable values, applying a tolerance (e.g., `> 0.5`) to determine selection.
- Compute actual coverage for all elements to validate constraint satisfaction independently.

### Step 4 - Handle Suboptimal or Failed Solves
- For `Feasible` status, report the solution but note optimality is not proven.
- For `Not Solved` or other errors, consider fallback actions like switching solvers or relaxing parameters.

### Code Usage
```python
import pulp  # or pyomo import

# Build model from formulation
prob = pulp.LpProblem("WeightedSetCover", pulp.LpMinimize)
x = pulp.LpVariable.dicts("x", items, cat='Binary')

# Objective
prob += pulp.lpSum(cost[i] * x[i] for i in items)

# Constraints
for e in elements:
    prob += pulp.lpSum(x[i] for i in coverage[e]) >= requirements[e]

# Solve with status / termination checks
solver = pulp.PULP_CBC_CMD(timeLimit=solver_timeout, gapRel=0.0, threads=num_threads, msg=False)
prob.solve(solver)

# Interpret status
status = pulp.LpStatus[prob.status]
if status == 'Optimal':
    print("Optimal solution found.")
elif status == 'Feasible':
    print("Feasible solution found (non-optimal).")
elif status == 'Infeasible':
    print("Problem is infeasible.")
else:
    print(f"Solver status: {status}")

# Extract and verify solution if feasible
if status in ['Optimal', 'Feasible']:
    selected_items = [i for i in items if pulp.value(x[i]) > 0.5]
    # Post-solve validation
    for e in elements:
        actual = sum(pulp.value(x[i]) for i in coverage[e] if pulp.value(x[i]) > 0.5)
        assert actual >= requirements[e], f"Coverage violation for element {e}"
```

### Common Pitfalls
- Relying solely on solver-reported status without independent solution verification.
- Not handling the case where the solver returns a non-`Optimal` feasible solution, leading to misinterpretation of results.
- Using default solver settings for large-scale instances, resulting in poor performance; always set time limits and optimality gaps.
