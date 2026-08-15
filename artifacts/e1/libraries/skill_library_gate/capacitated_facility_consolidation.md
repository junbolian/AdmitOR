---
name: Capacitated Facility Consolidation
description: |
  Model and solve binary assignment problems to minimize facility count under capacity constraints, using either CP-SAT or MIP solvers.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a binary integer program suitable for constraint programming solvers like OR-Tools CP-SAT, focusing on logical constraints and exact optimization.

### Step 1 - Define Core Variables
- Create binary facility usage variables `y[j]` for each facility `j`. `y[j] = 1` indicates the facility is open.
- Create binary assignment variables `x[i][j]` for each resource `i` and facility `j`. `x[i][j] = 1` indicates resource `i` is assigned to facility `j`.

### Step 2 - Enforce Assignment Logic
- Add an exactly-one constraint for each resource: `sum_{j} x[i][j] == 1`. This ensures every resource is assigned to exactly one facility.
- Add linking constraints: `x[i][j] <= y[j]` for all `i, j`. This prevents assignment to a closed facility.

### Step 3 - Impose Capacity Limits
- For each facility `j`, add a knapsack-style capacity constraint: `sum_{i} weight[i] * x[i][j] <= capacity[j] * y[j]`. This ensures capacity is only enforced for open facilities and links usage to assignment.

### Step 4 - Set the Objective
- Define the objective to minimize the total number of open facilities: `minimize sum_{j} y[j]`.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "facilities"
  ],
  "parameters": [
    {"name": "weight", "domain": "resources", "type": "float"},
    {"name": "capacity", "domain": "facilities", "type": "float"}
  ],
  "decision_variables": [
    {"name": "y", "domain": "facilities", "type": "binary"},
    {"name": "x", "domain": ["resources", "facilities"], "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in facilities)"
  },
  "constraints": [
    "assignment_exactly_one: sum(x[i][j] for j in facilities) == 1, for all i in resources",
    "facility_usage_linking: x[i][j] <= y[j], for all i in resources, j in facilities",
    "capacity_knapsack: sum(weight[i] * x[i][j] for i in resources) <= capacity[j] * y[j], for all j in facilities"
  ]
}
```

### Common Pitfalls
- Forgetting the linking constraint `x[i][j] <= y[j]` can allow assignments to closed facilities, violating the physical meaning of `y[j]`.
- Using a single global capacity parameter instead of a per-facility `capacity[j]` dictionary limits model flexibility.
- Not computing a theoretical lower bound (`ceil(total_weight / max_capacity)`) misses a quick sanity check for problem feasibility and solution quality.

## Solving stage

### Strategy Overview
Use the OR-Tools CP-SAT solver for its efficiency with binary variables and logical constraints. Configure for exact solution, implement verification, and extract comprehensive results.

### Step 1 - Build and Configure the Model
- Instantiate a `cp_model.CpModel()`.
- Add all variables and constraints as defined in the modeling stage.
- Set the objective using `model.Minimize()`.
- Configure solver parameters: set `solver.parameters.max_time_in_seconds` for a time limit, `num_search_workers` for parallelism, and `relative_gap_limit = 0.0` for an exact solution.

### Step 2 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`). Proceed only if a feasible solution is found.
- For an `OPTIMAL` status, the solver has proven optimality. For `FEASIBLE`, the solution is valid but not proven optimal.

### Step 3 - Verify Solution and Prove Optimality
- Extract the solution value `k` for the objective (number of open facilities).
- Systematically verify: each resource assigned exactly once, capacity constraints hold for open facilities, no assignments to closed facilities.
- To rigorously prove `k` is minimal, add a constraint `sum(y[j]) <= k-1` and re-solve. If the model becomes infeasible, `k` is optimal.

### Step 4 - Extract and Report Results
- Extract the list of open facilities where `y[j]` value is 1.
- Extract the assignment mapping: for each resource `i`, find `j` where `x[i][j]` is 1.
- Calculate the load and utilization percentage for each open facility.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (create variables y, x and add constraints as per modeling steps)
model.Minimize(sum(y[j] for j in facilities))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 4
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    obj_value = int(solver.ObjectiveValue())
    # Extract solution: solver.Value(y[j]), solver.Value(x[i][j])
    # ... verification and reporting logic
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing `ObjectiveValue()` or `Value()` can cause runtime errors.
- Setting `relative_gap_limit` to a non-zero value accepts suboptimal solutions, which conflicts with the goal of minimizing count.
- Failing to implement the optimality proof (adding `sum(y[j]) <= k-1` constraint) leaves optimality reliant solely on solver status, which may be inconclusive for hard instances.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using Pyomo's abstract modeling capabilities, enabling solver-agnostic code that can interface with commercial (e.g., Gurobi) or open-source (e.g., HiGHS) solvers.

### Step 1 - Declare Model Components
- Define Pyomo Sets for `resources` and `facilities`.
- Define Pyomo Parameters: `weight` over the resource set and `capacity` over the facility set.
- Declare binary decision variables: `model.y` for facility usage and `model.x` for resource assignment.

### Step 2 - Construct Constraints
- Add the assignment constraint as a Pyomo ConstraintList or a single rule: `sum(model.x[i, j] for j in facilities) == 1` for each `i`.
- Add linking constraints: `model.x[i, j] <= model.y[j]` for all `i, j`.
- Add capacity constraints: `sum(weight[i] * model.x[i, j] for i in resources) <= capacity[j] * model.y[j]` for each `j`.

### Step 3 - Define the Objective
- Set the objective to minimize the sum of `model.y` variables using `pyo.Objective(expr=..., sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "facilities"
  ],
  "parameters": [
    {"name": "weight", "domain": "resources", "type": "float", "pyomo_type": "Param"},
    {"name": "capacity", "domain": "facilities", "type": "float", "pyomo_type": "Param"}
  ],
  "decision_variables": [
    {"name": "y", "domain": "facilities", "type": "binary", "pyomo_type": "Var"},
    {"name": "x", "domain": ["resources", "facilities"], "type": "binary", "pyomo_type": "Var"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in facilities)",
    "pyomo_sense": "minimize"
  },
  "constraints": [
    {"name": "assign_one", "rule": "sum(x[i, j] for j in facilities) == 1, for all i"},
    {"name": "link", "rule": "x[i, j] <= y[j], for all i, j"},
    {"name": "cap", "rule": "sum(weight[i] * x[i, j] for i in resources) <= capacity[j] * y[j], for all j"}
  ]
}
```

### Common Pitfalls
- Initializing Pyomo Parameters with lists instead of dictionaries can lead to incorrect indexing. Always use a dict `{index: value}`.
- Using `pyo.Constraint` without a proper indexing rule for sets results in a single scalar constraint instead of the required set of constraints.
- Omitting the `sense` argument in `pyo.Objective` defaults to minimization, but explicit definition improves code clarity.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with a MIP solver. Configure solver-specific options for exact solutions, handle solver statuses carefully, and implement a verification loop to confirm optimality.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory("solver_name")` (e.g., "gurobi", "highs").
- Set key options: `time_limit`, `mipgap` (or `mip_rel_gap`) to `0.0` for exact solution, `threads` for parallelism, and `seed` for reproducibility.
- Validate that numerical option values (e.g., `MIPGap`) are non-negative to avoid solver errors.

### Step 2 - Solve and Inspect Termination
- Call `results = solver.solve(model, tee=False)`.
- Check both `results.solver.status` (e.g., `pyo.SolverStatus.ok`) and `results.solver.termination_condition` (e.g., `pyo.TerminationCondition.optimal`).
- If status is not `ok` or termination is not `optimal`/`feasible`, diagnose using the solver's log or termination message.

### Step 3 - Extract and Validate Solution
- If the solve was successful, load the solution into the model (`model.solutions.load_from(results)`).
- Extract the objective value `k` using `pyo.value(model.obj)`.
- Extract open facilities and assignments by filtering variables where `pyo.value(var) > 0.5`.
- Calculate facility loads for verification against capacity constraints.

### Step 4 - Prove Optimality via Feasibility Test
- To confirm `k` is minimal, add a new constraint to the model: `sum(model.y[j] for j in facilities) <= k - 1`.
- Re-solve the model as a feasibility problem (no objective needed). If the solver returns `infeasible`, `k` is proven optimal.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.R = pyo.Set(initialize=resources)
model.F = pyo.Set(initialize=facilities)
model.weight = pyo.Param(model.R, initialize=weight_dict)
model.capacity = pyo.Param(model.F, initialize=capacity_dict)
model.y = pyo.Var(model.F, domain=pyo.Binary)
model.x = pyo.Var(model.R, model.F, domain=pyo.Binary)
# ... (add constraints as per modeling steps)
model.obj = pyo.Objective(expr=sum(model.y[j] for j in model.F), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    k = pyo.value(model.obj)
    # Extract solution and verify
    # ... optimality proof logic
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not using `load_solutions=False` in the `solve` call when planning to add constraints for optimality proof can lead to loading an incompatible solution.
- Accessing `pyo.value(model.obj)` before checking solver status may raise an error if the solve failed.
- Setting solver options incorrectly (e.g., `MIPGap` for Gurobi vs. `mip_rel_gap` for HiGHS) causes the option to be ignored, potentially leading to suboptimal solutions.
