---
name: BipartitePartialAssignment
description: |
  Model and solve bipartite partial assignment problems with one-to-one matching, exact total assignments, and cost minimization using binary decision variables.

---
# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Formulate the problem using OR-Tools' CP-SAT solver, which is designed for constraint programming and integer problems with binary variables. The model enforces at-most-one constraints per row and column, plus a global cardinality constraint for exact total assignments, minimizing a linear cost function.

### Step 1 - Define Sets and Parameters
- Identify the two disjoint sets `A` and `B` (e.g., `items_a`, `items_b`) and their sizes.
- Define a 2D cost matrix `cost[i][j]` representing the assignment cost between element `i` in set `A` and element `j` in set `B`.
- Determine the required number of total assignments `k`.

### Step 2 - Create Binary Decision Variables
- For each possible assignment `(i, j)`, create a binary variable `x[i, j]` using `model.NewBoolVar()`.
- Store variables in a dictionary keyed by tuple `(i, j)` for efficient access during constraint and objective building.

### Step 3 - Enforce One-to-One Matching Constraints
- For each element `i` in set `A`, add constraint: `sum(x[i, j] for j in B) <= 1`.
- For each element `j` in set `B`, add constraint: `sum(x[i, j] for i in A) <= 1`.
- These ensure each element is assigned at most once.

### Step 4 - Enforce Exact Total Assignments
- Add a global constraint: `sum(x[i, j] for all i, j) == k`.
- This, combined with the one-to-one constraints, defines a partial assignment problem.

### Step 5 - Define Linear Minimization Objective
- Formulate the objective as `sum(cost[i][j] * x[i, j] for all i, j)`.
- Use `model.Minimize()` with the constructed linear expression.

### Formulation Template
```json
{
  "sets": ["A", "B"],
  "parameters": ["cost[A][B]", "k"],
  "decision_variables": ["x[A][B] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in A, j in B)"
  },
  "constraints": [
    "sum(x[i][j] for j in B) <= 1, for all i in A",
    "sum(x[i][j] for i in A) <= 1, for all j in B",
    "sum(x[i][j] for all i, j) == k"
  ]
}
```

### Common Pitfalls
- Forgetting to validate that `k` is less than or equal to the minimum of `|A|` and `|B|`, which can lead to infeasibility.
- Using inefficient data structures (e.g., nested lists) for large sets, causing slow model construction.
- Misaligning indices between the cost matrix and the variable dictionary, leading to incorrect objective values.

## Solving stage

### Strategy Overview
Solve the model using the CP-SAT solver with configuration for time limits, parallelism, and exact solutions. Extract and verify assignments from the solution, handling both optimal and feasible statuses.

### Step 1 - Configure Solver and Solve
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 8`, `solver.parameters.random_seed = 42`, and `solver.parameters.relative_gap_limit = 0.0` for exact solutions.
- Call `status = solver.Solve(model)`.

### Step 2 - Check Solver Status
- Check if a solution was found: `if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):`.
- If `status` is `cp_model.INFEASIBLE` or `cp_model.MODEL_INVALID`, log an error and proceed to diagnostic steps (e.g., feasibility validation).

### Step 3 - Extract Solution and Objective
- For optimal/feasible status, retrieve the objective value: `obj_value = solver.ObjectiveValue()`.
- Iterate through all variable indices `(i, j)` and collect assignments where `solver.Value(x[i, j]) == 1`.
- Store assignments as a list of tuples `(i, j, cost[i][j])` for verification.

### Step 4 - Output Standardization
- Print a human-readable summary including status, objective value, and list of assignments.
- Output a machine-readable tag (e.g., `RESULT:{obj_value}`) for automated parsing in pipelines.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (construct model as per Modeling stage)
# solve with status / termination checks
solver = cp_model.CpSolver()
# Apply solver parameters
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Objective: {solver.ObjectiveValue()}")
    assignments = []
    for i in range(len(A)):
        for j in range(len(B)):
            if solver.Value(x[i, j]) == 1:
                assignments.append((i, j, cost[i][j]))
    print(f"Assignments: {assignments}")
    print(f"RESULT:{solver.ObjectiveValue()}")
else:
    print("No solution found.")
```

### Common Pitfalls
- Not setting `relative_gap_limit = 0.0`, which can cause the solver to return a suboptimal solution prematurely.
- Assuming `FEASIBLE` status implies optimality; always check for `OPTIMAL` if proof is required.
- Neglecting to handle solver statuses other than `OPTIMAL`/`FEASIBLE`, leading to crashes in automated workflows.

# Workflow 2 (MIP Solver via Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem using Pyomo's abstract or concrete modeling interface, targeting Mixed-Integer Programming (MIP) solvers like HiGHS, SCIP, or CBC. The model structure emphasizes set-based constraints and parameter dictionaries for clarity and flexibility.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `model.A` and `model.B`.
- Define `model.cost` as a `Param` initialized by a dictionary with keys `(i, j)`.
- Declare `model.k` as a scalar parameter for the required number of assignments.

### Step 2 - Create Binary Decision Variables
- Define `model.x` as a `Var` indexed by `model.A * model.B` (Cartesian product), with domain `Binary`.
- This creates variable `model.x[i, j]` for each potential assignment.

### Step 3 - Enforce One-to-One Matching Constraints
- For each `i` in `model.A`, add constraint: `sum(model.x[i, j] for j in model.B) <= 1`.
- For each `j` in `model.B`, add constraint: `sum(model.x[i, j] for i in model.A) <= 1`.
- Use Pyomo's `Constraint` object with rule functions or direct expressions.

### Step 4 - Enforce Exact Total Assignments
- Add a global constraint: `sum(model.x[i, j] for i in model.A for j in model.B) == model.k`.

### Step 5 - Define Linear Minimization Objective
- Formulate the objective as `sum(model.cost[i, j] * model.x[i, j] for i in model.A for j in model.B)`.
- Use `model.obj = Objective(expr=..., sense=minimize)`.

### Formulation Template
```json
{
  "sets": ["A", "B"],
  "parameters": ["cost[i,j] for i in A, j in B", "k"],
  "decision_variables": ["x[i,j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in A, j in B)"
  },
  "constraints": [
    "sum(x[i,j] for j in B) <= 1, for all i in A",
    "sum(x[i,j] for i in A) <= 1, for all j in B",
    "sum(x[i,j] for all i, j) == k"
  ]
}
```

### Common Pitfalls
- Using concrete model initialization with large datasets can be memory-intensive; consider abstract models with rule-based parameter initialization.
- Incorrectly defining the Cartesian product set for variables, leading to missing or extra variables.
- Not validating parameter `k` against set cardinalities during model instantiation, causing later infeasibility.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver backend (e.g., HiGHS via `appsi.highs`). Configure the solver for exact solutions, handle termination statuses robustly, and extract assignments by checking variable values.

### Step 1 - Select and Configure Solver
- Instantiate the solver: `solver = SolverFactory('highs')`.
- Set solver options: `solver.options['mip_rel_gap'] = -1.0` (disable early termination), `solver.options['threads'] = -1` (auto threads), `solver.options['time_limit'] = 30`.
- For other solvers (e.g., `scip`, `cbc`), use corresponding option names.

### Step 2 - Solve and Check Termination Status
- Call `results = solver.solve(model, tee=False)`.
- Check termination condition: `if results.solver.termination_condition == TerminationCondition.optimal:`.
- For `infeasible` or other non-optimal statuses, proceed to diagnostic validation (e.g., combinatorial enumeration).

### Step 3 - Extract Solution and Objective
- For optimal termination, retrieve the objective value: `obj_value = pyo.value(model.obj)`.
- Iterate through `model.x` and collect assignments where `pyo.value(model.x[i, j]) > 0.5`.
- Store assignments as a list of `(i, j, model.cost[i, j])`.

### Step 4 - Validate and Output Results
- Optionally verify constraint satisfaction by checking the extracted assignments against the model constraints.
- Output structured results (e.g., JSON) containing status, objective value, and assignment list.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.A = pyo.Set(initialize=range(len(A)))
model.B = pyo.Set(initialize=range(len(B)))
model.cost = pyo.Param(model.A, model.B, initialize=cost_dict)
model.k = pyo.Param(initialize=k, mutable=True)
model.x = pyo.Var(model.A, model.B, domain=pyo.Binary)
# ... (add constraints and objective as per Modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['mip_rel_gap'] = -1.0
solver.options['time_limit'] = 30
results = solver.solve(model)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    print(f"Objective: {pyo.value(model.obj)}")
    assignments = []
    for i in model.A:
        for j in model.B:
            if pyo.value(model.x[i, j]) > 0.5:
                assignments.append((i, j, pyo.value(model.cost[i, j])))
    print(f"Assignments: {assignments}")
else:
    print(f"Solver terminated with: {results.solver.termination_condition}")
    # Consider feasibility validation via enumeration for small instances
```

### Common Pitfalls
- Attempting to access `pyo.value(var)` on variables from an unsolved or infeasible model, which may raise errors; always check solver status first.
- Not setting `mip_rel_gap` appropriately, leading to early termination with suboptimal solutions.
- Overlooking the need to set `mutable=True` on parameter `k` if it will be changed across multiple model solves.
