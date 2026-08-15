---
name: Cardinality-Constrained Assignment
description: |
  Model and solve assignment problems with at-most-one constraints and a fixed total number of assignments, minimizing total cost.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a binary integer program and model it directly using the OR-Tools CP-SAT solver's native API, which is efficient for combinatorial problems with logical constraints.

### Step 1 - Define Variables
- Declare a binary decision variable for each potential assignment between an item and a resource.
- Use `model.NewBoolVar(f"x_{i}_{j}")` to create variables, storing them in a dictionary or 2D list for easy access.

### Step 2 - Formulate Objective
- Construct a linear objective to minimize total assignment cost: `sum(cost[i][j] * x[i][j])`.
- Apply it using `model.Minimize(objective_expression)`.

### Step 3 - Add Assignment Limits
- For each item `i`, add a constraint limiting its total assignments to at most one: `sum(x[i][j] for j in resources) <= 1`.
- For each resource `j`, add a constraint limiting its total assignments to at most one: `sum(x[i][j] for i in items) <= 1`.

### Step 4 - Enforce Cardinality Constraint
- Add a single global constraint to fix the exact number of total assignments `K`: `sum(x[i][j] for i in items for j in resources) == K`.

### Formulation Template
```json
{
  "sets": ["items", "resources"],
  "parameters": ["cost[items][resources]", "K"],
  "decision_variables": ["x[items][resources] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in items for j in resources)"
  },
  "constraints": [
    "sum(x[i][j] for j in resources) <= 1, for each i in items",
    "sum(x[i][j] for i in items) <= 1, for each j in resources",
    "sum(x[i][j] for i in items for j in resources) == K"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce both directional assignment limits, which can lead to infeasible or incorrect models.
- Using float coefficients in the objective or constraints with CP-SAT; scale costs to integers if necessary.
- Not using unique, descriptive names for variables, complicating post-solution analysis.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for deterministic, optimal search, extract the solution, and implement verification for small-scale instances.

### Step 1 - Configure Solver
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds` for a time limit, `solver.parameters.num_search_workers` for parallelism, and `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = -1.0` to require proven optimality.

### Step 2 - Solve and Check Status
- Execute the solver: `status = solver.Solve(model)`.
- Check if the status is `OPTIMAL` or `FEASIBLE` before proceeding. Handle `INFEASIBLE` or `MODEL_INVALID` statuses appropriately.

### Step 3 - Extract Solution
- If the status is acceptable, iterate over all variable indices `(i, j)`.
- For each variable where `solver.Value(x[i][j]) == 1`, record the assignment `(i, j)` and accumulate its cost.
- Compute and report the total objective value.

### Step 4 - Verify with Enumeration (Optional)
- For small problem instances, implement a brute-force verification using `itertools.combinations` and `itertools.permutations` to enumerate all feasible assignments.
- Confirm the solver's solution matches the enumerated optimum to build confidence in the modeling.

### Code Usage
```python
from ortools.sat.python import cp_model
import itertools

# Build model
model = cp_model.CpModel()
# ... (build variables, objective, constraints as per modeling stage)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 4
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = -1.0  # Require optimality

status = solver.Solve(model)

# Check status and extract solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    total_cost = 0
    assignments = []
    for i in items:
        for j in resources:
            if solver.Value(x[i][j]) == 1:
                assignments.append((i, j))
                total_cost += cost[i][j]
    print(f"STATUS: {status}")
    print(f"TOTAL_COST: {total_cost}")
    print(f"ASSIGNMENTS: {assignments}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing variable values, which can cause runtime errors.
- Setting an insufficient time limit for larger instances, resulting in suboptimal or no solutions.
- Omitting the random seed, leading to non-reproducible results across runs.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
Use the Pyomo modeling library to create an abstract mathematical model, enabling solver-agnostic formulation and easy integration with high-performance MIP solvers like Gurobi or CBC.

### Step 1 - Define Sets and Parameters
- Declare Pyomo `Set` objects for the items and resources.
- Define a cost parameter `cost[i,j]` using a Pyomo `Param` initialized from a dictionary, which efficiently handles sparse data.

### Step 2 - Declare Decision Variables
- Create binary variables `model.x[i,j]` over the Cartesian product of the item and resource sets using `pyo.Var(domain=pyo.Binary)`.

### Step 3 - Construct Objective
- Formulate the minimization objective as a Pyomo `Objective` expression: `sum(model.cost[i,j] * model.x[i,j] for i in model.I for j in model.J)`.

### Step 4 - Impose Constraints
- Add a `Constraint` for each item: `sum(model.x[i,j] for j in model.J) <= 1`.
- Add a `Constraint` for each resource: `sum(model.x[i,j] for i in model.I) <= 1`.
- Add a single cardinality `Constraint`: `sum(model.x[i,j] for i in model.I for j in model.J) == K`.

### Formulation Template
```json
{
  "sets": ["I (items)", "J (resources)"],
  "parameters": ["cost[I,J]"],
  "decision_variables": ["x[I,J] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I for j in J)"
  },
  "constraints": [
    "sum(x[i,j] for j in J) <= 1, ∀ i ∈ I",
    "sum(x[i,j] for i in I) <= 1, ∀ j ∈ J",
    "sum(x[i,j] for i in I for j in J) == K"
  ]
}
```

### Common Pitfalls
- Initializing the cost parameter with missing keys for non-existent assignments; ensure the dictionary is complete or use a default value.
- Using mutable objects like lists within Pyomo rule functions, which can lead to unexpected behavior.
- Not leveraging Pyomo's `initialize` argument for parameters, resulting in less efficient model construction.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MIP solver, implement robust status checking, and include a fallback mechanism for solver availability.

### Step 1 - Configure and Execute Solver
- Create a solver object: `solver = pyo.SolverFactory("solver_name")`.
- Set options: `TimeLimit`, `MIPGap=0.0` (for exact solution), `Threads`, and `Seed` for deterministic results.
- Solve with `load_solutions=False` to defer solution loading until status is verified.

### Step 2 - Check Termination Status
- Inspect `results.solver.status` (should be `ok`) and `results.solver.termination_condition`.
- Proceed only if termination is `optimal` or `feasible`. Handle other conditions (e.g., `maxTimeLimit`, `infeasible`) with appropriate error messages.

### Step 3 - Load and Extract Solution
- If status is good, load the solution: `model.solutions.load_from(results)`.
- Extract the objective value: `obj_val = float(pyo.value(model.obj))`.
- Iterate over variables `model.x[i,j]` and collect assignments where `pyo.value(model.x[i,j]) > 0.5`.

### Step 4 - Implement Solver Fallback
- Define an ordered list of preferred solvers (e.g., `["gurobi", "cbc", "highs"]`).
- Attempt to solve with each solver sequentially until one returns a successful status.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (using function from modeling stage)
model = build_assignment_model(items, resources, cost_dict, K)

# Ordered list of solver attempts
solvers_to_try = ["gurobi", "cbc", "highs"]
results = None

for solver_name in solvers_to_try:
    solver = pyo.SolverFactory(solver_name)
    if solver.available():
        solver.options["TimeLimit"] = 30
        solver.options["MIPGap"] = -1.0  # Use -1.0 for OR-Tools, 0.0 for others
        solver.options["Threads"] = 4
        solver.options["Seed"] = 42
        results = solver.solve(model, tee=False, load_solutions=False)
        if results.solver.status == SolverStatus.ok:
            break

# Check results and extract solution
if results and results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:
    model.solutions.load_from(results)
    total_cost = float(pyo.value(model.obj))
    assignments = [(i, j, cost_dict[i,j]) for i in model.I for j in model.J if pyo.value(model.x[i,j]) > 0.5]
    print(f"SOLVER_USED: {solver_name}")
    print(f"TOTAL_COST: {total_cost}")
    print(f"ASSIGNMENTS: {assignments}")
else:
    raise Exception(f"Solver failed. Last status: {getattr(results, 'solver', {}).get('termination_condition', 'unknown')}")
```

### Common Pitfalls
- Checking only the solver status without verifying the termination condition, potentially accepting suboptimal or incomplete solutions.
- Not using `load_solutions=False`, which can cause errors when trying to access variable values from a failed solve.
- Hardcoding a single solver name without fallbacks, making the code fragile in different execution environments.
