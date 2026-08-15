---
name: TSP with Subtour Elimination via Position Variables
description: |
  Model and solve routing problems requiring a single tour (Hamiltonian cycle) using binary arc selection and position variables to eliminate subtours, with implementation for both CP-SAT and MIP solvers.

---

# Workflow 1 (CP-SAT with Implication Constraints)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT to model the problem with logical implication constraints (`OnlyEnforceIf`) to enforce ordering relationships conditionally on arc selection, providing a direct encoding of subtour elimination.

### Step 1 - Define Core Variables
- Create binary decision variables `x[i][j]` for each directed arc between distinct nodes `i` and `j` to represent arc inclusion in the tour.
- Create integer position variables `p[i]` for each node `i` to establish a topological order, with appropriate bounds (e.g., `0` to `n-1`).

### Step 2 - Enforce Assignment Constraints
- For each node `i`, add a constraint that the sum of incoming arcs `x[j][i]` (for all `j != i`) equals 1.
- For each node `i`, add a constraint that the sum of outgoing arcs `x[i][j]` (for all `j != i`) equals 1.
- Optionally, fix `x[i][i] = 0` for all `i` to prohibit self-loops.

### Step 3 - Enforce Subtour Elimination via Implications
- For each directed arc `(i, j)` where `i != j`, add an implication constraint: if `x[i][j] == 1`, then enforce `p[i] + 1 <= p[j]`. This prevents cycles by forcing a strict order.

### Step 4 - Formulate Objective
- Define the objective as the minimization of the total cost: `sum(cost[i][j] * x[i][j] for all arcs (i,j))`.

### Formulation Template
```json
{
  "sets": ["NODES"],
  "parameters": ["cost[NODES][NODES]"],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["i in NODES", "j in NODES", "i != j"]},
    {"name": "p", "type": "integer", "indices": ["i in NODES"], "bounds": "[0, len(NODES)-1]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in NODES for j in NODES if i != j)"
  },
  "constraints": [
    "sum(x[j][i] for j in NODES if j != i) == 1 for all i in NODES",
    "sum(x[i][j] for j in NODES if j != i) == 1 for all i in NODES",
    "x[i][i] == 0 for all i in NODES",
    "p[i] + 1 <= p[j] enforced if x[i][j] == 1 for all i,j in NODES, i != j"
  ]
}
```

### Common Pitfalls
- Applying subtour elimination constraints to all arcs, including those involving a designated depot, which can be unnecessary and add model complexity.
- Forgetting to set appropriate bounds on position variables, which can lead to solver performance issues or unintended solutions.
- Assuming all position variables will be assigned a value in the solution; the starting/reference node's position may be left unrestricted.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver with parameters for performance and reliability, then extract and validate the solution, handling potential solver statuses gracefully.

### Step 1 - Configure Solver Parameters
- Set a time limit (`max_time_in_seconds`).
- Enable parallel search (`num_search_workers`).
- Set a `random_seed` for reproducibility.
- Set `relative_gap_limit = 0.0` to search for proven optimal solutions.

### Step 2 - Solve and Check Status
- Execute the solver and capture the status (`cp_model.OPTIMAL`, `cp_model.FEASIBLE`, etc.).
- If status is not `OPTIMAL` or `FEASIBLE`, log the status and proceed to error handling without attempting solution extraction.

### Step 3 - Extract and Reconstruct Solution
- Retrieve the objective value using `solver.ObjectiveValue()`.
- For each binary arc variable `x[i][j]`, check if `solver.Value(var) == 1` to identify selected arcs.
- Reconstruct the tour by starting at a designated node and following selected arcs until the cycle closes.

### Step 4 - Validate Solution
- Programmatically verify that assignment constraints hold in the extracted solution.
- Recalculate the total cost from selected arcs and compare it to the reported objective value.
- For small instances, optionally enumerate all feasible tours to confirm optimality.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()

# Define variables
x = {}
for i in NODES:
    for j in NODES:
        if i != j:
            x[i,j] = model.NewBoolVar(f"x_{i}_{j}")
p = {}
for i in NODES:
    p[i] = model.NewIntVar(0, len(NODES)-1, f"p_{i}")

# Add constraints (assignment, implications for subtour elimination)
# ... (implementation of steps 2 & 3)

# Set objective
model.Minimize(sum(cost[i][j] * x[i,j] for i in NODES for j in NODES if i != j))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = TIME_LIMIT
solver.parameters.num_search_workers = NUM_WORKERS
solver.parameters.random_seed = RANDOM_SEED
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    objective_value = solver.ObjectiveValue()
    selected_arcs = [(i,j) for (i,j), var in x.items() if solver.Value(var) == 1]
    # Reconstruct tour...
else:
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Accessing `.Value()` on variables before confirming the solver found a feasible solution, leading to runtime errors.
- Using invalid solver parameter values (e.g., negative time limits) causing immediate failure.
- Not providing fallback logic for solution extraction when the solver status is not as expected.

---

# Workflow 2 (MIP with Big-M Subtour Elimination)

## Modeling stage

### Strategy Overview
This workflow formulates the problem as a Mixed-Integer Program (MIP) using a Big-M method to encode conditional ordering constraints, suitable for solvers like SCIP, Gurobi, or CBC via linear programming interfaces.

### Step 1 - Define Core Variables
- Create binary decision variables `x[i][j]` for each directed arc between distinct nodes.
- Create continuous (or integer) position variables `p[i]` for each node. The start/reference node may be left unbounded.

### Step 2 - Enforce Assignment Constraints
- For each node `i`, enforce exactly one incoming arc: `sum(x[j][i] for j != i) == 1`.
- For each node `i`, enforce exactly one outgoing arc: `sum(x[i][j] for j != i) == 1`.
- Add explicit constraints `x[i][i] == 0` to prevent self-loops.

### Step 3 - Enforce Subtour Elimination via Big-M
- Select a sufficiently large constant `M` (e.g., number of nodes).
- For each directed arc `(i, j)` where subtour elimination is needed (e.g., `i != j` and neither is the depot), add the linear constraint: `p[i] - p[j] + M * x[i][j] <= M - 1`. This enforces `p[i] < p[j]` only if `x[i][j] = 1`.

### Step 4 - Formulate Objective
- Define the objective as the minimization of total travel cost: `sum(cost[i][j] * x[i][j] for all arcs)`.

### Formulation Template
```json
{
  "sets": ["NODES"],
  "parameters": ["cost[NODES][NODES]", "M (big-M constant)"],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["i in NODES", "j in NODES", "i != j"]},
    {"name": "p", "type": "continuous", "indices": ["i in NODES"], "bounds": "context-dependent"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in NODES for j in NODES if i != j)"
  },
  "constraints": [
    "sum(x[j][i] for j in NODES if j != i) == 1 for all i in NODES",
    "sum(x[i][j] for j in NODES if j != i) == 1 for all i in NODES",
    "x[i][i] == 0 for all i in NODES",
    "p[i] - p[j] + M * x[i][j] <= M - 1 for all i,j in NODES where condition holds"
  ]
}
```

### Common Pitfalls
- Choosing an `M` value that is too small, making the constraint ineffective, or too large, causing numerical instability.
- Applying Big-M constraints to all arcs indiscriminately, which can make the model larger and harder to solve.
- Leaving position variables for non-reference nodes unbounded, which can lead to unbounded or numerically problematic solutions.

## Solving stage

### Strategy Overview
Instantiate a MIP solver, set runtime and optimality gap parameters, solve the model, and extract the solution by following the selected arcs, with robust handling of solver outcomes.

### Step 1 - Configure Solver and Solve
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set a time limit (`SetTimeLimit`).
- Set the number of threads (`SetNumThreads`).
- Set an optimality gap (`SetMIPGap`) to `0.0` for exact solution.
- Execute the solver and capture the status.

### Step 2 - Check Solver Status
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- If the status indicates infeasibility, unboundedness, or an error, log diagnostic information and halt solution extraction.

### Step 3 - Extract Solution and Reconstruct Tour
- Retrieve the objective value.
- For each binary arc variable, check if its `solution_value()` exceeds a tolerance (e.g., `0.5`).
- Starting from a designated node, iteratively follow selected arcs to reconstruct the full Hamiltonian cycle.

### Step 4 - Independent Validation
- Verify that every node has exactly one selected incoming and outgoing arc.
- Sum the costs of selected arcs and confirm it matches the reported objective value.
- Check that the reconstructed tour visits all nodes exactly once before returning to the start.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(TIME_LIMIT_MS)
solver.SetNumThreads(NUM_THREADS)
solver.SetMIPGap(0.0)

# Define variables
x = {}
for i in NODES:
    for j in NODES:
        if i != j:
            x[i,j] = solver.IntVar(0, 1, f"x_{i}_{j}")
p = {}
for i in NODES:
    if i == START_NODE:
        p[i] = solver.NumVar(-solver.infinity(), solver.infinity(), f"p_{i}")
    else:
        p[i] = solver.NumVar(LOWER_BOUND, UPPER_BOUND, f"p_{i}")

# Add constraints (assignment, Big-M for subtour elimination)
# ... (implementation of steps 2 & 3)

# Set objective
objective = solver.Objective()
for (i,j), var in x.items():
    objective.SetCoefficient(var, cost[i][j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    # Extract solution
    objective_value = objective.Value()
    selected_arcs = [(i,j) for (i,j), var in x.items() if var.solution_value() > 0.5]
    # Reconstruct tour...
else:
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Assuming `solution_value()` is available for all variables regardless of solver status, leading to attribute errors.
- Using an invalid or unsupported solver string, causing instantiation failure.
- Not handling the case where the starting node's position variable is unbounded and may not have a meaningful `.solution_value()`.
