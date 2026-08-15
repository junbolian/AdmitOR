---
name: BinaryArcRoutingWithOrdering
description: |
  Model and solve routing problems with binary arc selection and ordering variables to enforce Hamiltonian cycles, using either CP-SAT with logical implications or MIP with Big-M constraints.

---
# Workflow 1 (CP-SAT with Logical Implications)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Constraint Programming (CP) model using OR-Tools CP-SAT. It leverages native logical constraints (`OnlyEnforceIf`) to directly encode conditional relationships between arc selection and ordering, avoiding manual Big-M formulations.

### Step 1 - Define Arc Selection Variables
- Create a binary decision variable for each directed arc between distinct nodes.
- Use a dictionary keyed by `(i, j)` for efficient access.

### Step 2 - Define Ordering Variables
- Create integer or continuous variables to represent a node's position in a sequence.
- Assign appropriate lower and upper bounds based on the problem context (e.g., `0` to `n-1`).

### Step 3 - Enforce Assignment Constraints
- For each node, ensure exactly one incoming arc is selected.
- For each node, ensure exactly one outgoing arc is selected.
- Optionally, explicitly prohibit self-loops if not already excluded in variable creation.

### Step 4 - Enforce Subtour Elimination via Conditional Ordering
- For each directed arc `(i, j)`, add a constraint: `position[i] + 1 <= position[j]`.
- Apply this constraint conditionally, only if the corresponding arc variable `x[i,j]` is selected, using `model.Add(...).OnlyEnforceIf(x_var)`.

### Step 5 - Define Linear Objective
- Formulate the objective as the sum of arc costs multiplied by the corresponding binary selection variables.
- Set the solver objective to minimize this total cost.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes"
  ],
  "parameters": [
    "cost_ij: cost of traversing arc from node i to j, for all i,j in N, i != j"
  ],
  "decision_variables": [
    "x_ij: binary, 1 if arc (i,j) is selected",
    "p_i: integer or continuous, ordering variable for node i"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in N} sum_{j in N, j != i} cost_ij * x_ij"
  },
  "constraints": [
    "sum_{i in N, i != j} x_ij == 1, for all j in N",
    "sum_{j in N, j != i} x_ij == 1, for all i in N",
    "p_i + 1 <= p_j, enforced only if x_ij == 1, for all i,j in N, i != j"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops (`i != j`) when creating arc variables or constraints, which can lead to trivial, invalid solutions.
- Using an insufficient upper bound for ordering variables, which can make the model infeasible; use a bound like `n-1` or a large constant.
- Incorrectly applying the `OnlyEnforceIf` syntax, which requires the condition variable as an argument to the method, not within the constraint expression.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, which is optimized for combinatorial problems with logical constraints. Configure search parameters for performance and extract the solution, carefully handling solver statuses.

### Step 1 - Initialize Solver and Set Parameters
- Create a CP-SAT model instance.
- Set a time limit (`model.parameters.max_time_in_seconds`).
- Optionally set the number of parallel workers (`model.parameters.num_search_workers`) and a random seed for reproducibility.

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the status: accept `OPTIMAL` or `FEASIBLE` solutions; handle `INFEASIBLE` or `UNKNOWN` statuses appropriately.

### Step 3 - Extract and Validate Solution
- If a feasible solution is found, iterate over all arc variables and collect those with a value of `1`.
- Extract the values of the ordering variables.
- Reconstruct the route by starting from a designated node and following selected arcs.
- Verify that the reconstructed route visits all nodes exactly once and returns to the start (for a cycle) or forms a Hamiltonian path, as required.

### Step 4 - Report Results
- Output the objective value, the sequence of nodes, and the selected arcs.
- For debugging, optionally print the values of the ordering variables.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()

# 1. Create variables
nodes = range(num_nodes)
x = {(i, j): model.NewBoolVar(f"x_{i}_{j}") for i in nodes for j in nodes if i != j}
p = {i: model.NewIntVar(lb[i], ub[i], f"p_{i}") for i in nodes}

# 2. Add assignment constraints
for j in nodes:
    model.Add(sum(x[(i, j)] for i in nodes if i != j) == 1)
for i in nodes:
    model.Add(sum(x[(i, j)] for j in nodes if j != i) == 1)

# 3. Add conditional subtour elimination
for i in nodes:
    for j in nodes:
        if i != j:
            model.Add(p[i] + 1 <= p[j]).OnlyEnforceIf(x[(i, j)])

# 4. Set objective
model.Minimize(sum(cost[(i, j)] * x[(i, j)] for (i, j) in x))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = time_limit
solver.parameters.random_seed = random_seed
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Objective: {solver.ObjectiveValue()}")
    # Extract selected arcs
    tour_arcs = [(i, j) for (i, j), var in x.items() if solver.Value(var) == 1]
    # Extract ordering
    positions = {i: solver.Value(p[i]) for i in nodes}
    # Reconstruct and validate route...
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Accessing variable values without first checking that the solver found a feasible solution, leading to runtime errors.
- Using undefined or invalid parameter values (e.g., a non-integer seed) when configuring the solver.
- Assuming the solver's optimality guarantee without setting appropriate optimality tolerances (`model.parameters.relative_gap_limit`) for very large instances.

# Workflow 2 (MIP with Big-M Formulation)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Program (MIP) using a linear solver backend (e.g., SCIP, CBC). Subtour elimination is enforced via a linear Big-M constraint, making it suitable for solvers that do not support native logical implications.

### Step 1 - Define Arc Selection Variables
- Create binary decision variables for each directed arc between distinct nodes.

### Step 2 - Define Continuous Ordering Variables
- Create continuous variables to represent node positions.
- Bound them appropriately (e.g., `0` to `n-1`). The starting node's position may be left unbounded or fixed.

### Step 3 - Enforce Assignment Constraints
- For each node, constrain the sum of incoming arcs to equal `1`.
- For each node, constrain the sum of outgoing arcs to equal `1`.

### Step 4 - Enforce Subtour Elimination via Big-M Constraint
- For each directed arc `(i, j)` (often excluding a designated depot), add the linear constraint: `p_i - p_j + M * x_ij <= M - 1`.
- Choose `M` sufficiently large (e.g., `n` or `n+1`) to deactivate the constraint when `x_ij = 0`, but not so large as to cause numerical instability.

### Step 5 - Define Linear Objective
- Minimize the total cost as the sum of `cost_ij * x_ij`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes"
  ],
  "parameters": [
    "cost_ij: cost of traversing arc from node i to j, for all i,j in N, i != j",
    "M: a sufficiently large constant (Big-M)"
  ],
  "decision_variables": [
    "x_ij: binary, 1 if arc (i,j) is selected",
    "p_i: continuous, ordering variable for node i"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in N} sum_{j in N, j != i} cost_ij * x_ij"
  },
  "constraints": [
    "sum_{i in N, i != j} x_ij == 1, for all j in N",
    "sum_{j in N, j != i} x_ij == 1, for all i in N",
    "p_i - p_j + M * x_ij <= M - 1, for all i,j in N, i != j, (optionally i != depot)"
  ]
}
```

### Common Pitfalls
- Choosing an excessively large `M` value, which can lead to numerical issues and slow convergence; use the smallest valid value (e.g., `n`).
- Forgetting to apply bounds to all ordering variables, which can result in unbounded subproblems or undefined variable values in the solution.
- Incorrectly excluding the Big-M constraint for arcs involving a designated start node, which can inadvertently create subtours that include that node.

## Solving stage

### Strategy Overview
Solve the MIP model using a linear solver wrapper (e.g., OR-Tools MPSolver). Configure solver settings, solve, and extract the solution. Implement a route reconstruction algorithm based on the selected arcs.

### Step 1 - Initialize Solver and Set Parameters
- Instantiate a solver with a suitable backend (e.g., `'SCIP'`).
- Set a time limit (`solver.SetTimeLimit(ms)`) and optionally the number of threads.

### Step 2 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the return status against `OPTIMAL` and `FEASIBLE` constants.

### Step 3 - Extract Solution and Reconstruct Route
- For each arc variable, check if its solution value exceeds `0.5` (tolerance for binary variables).
- Store selected arcs and use a traversal algorithm (start from a node, follow the selected outgoing arc) to build the node sequence.
- Validate that the sequence is a single tour covering all nodes.

### Step 4 - Report Results
- Output the total cost and the ordered list of nodes in the tour.
- For debugging, print the values of the ordering variables.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
nodes = range(num_nodes)
inf = solver.infinity()

# 1. Create variables
x = {}
for i in nodes:
    for j in nodes:
        if i != j:
            x[i, j] = solver.IntVar(0, 1, f'x_{i}_{j}')
p = {i: solver.NumVar(lb[i], ub[i], f'p_{i}') for i in nodes}
# Optionally fix or unbound depot position
# p[depot].SetLb(-inf)

# 2. Add assignment constraints
for j in nodes:
    solver.Add(sum(x[i, j] for i in nodes if i != j) == 1)
for i in nodes:
    solver.Add(sum(x[i, j] for j in nodes if j != i) == 1)

# 3. Add Big-M subtour elimination
M = big_m_value  # e.g., len(nodes)
for i in nodes:
    for j in nodes:
        if i != j: # and i != depot: # Optional exclusion
            solver.Add(p[i] - p[j] + M * x[i, j] <= M - 1)

# 4. Set objective
solver.Minimize(sum(cost[i, j] * x[i, j] for (i, j) in x))

# Solve with status / termination checks
solver.SetTimeLimit(time_limit_ms)
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f"Objective: {solver.Objective().Value()}")
    # Extract selected arcs
    tour_arcs = [(i, j) for (i, j), var in x.items() if var.solution_value() > 0.5]
    # Reconstruct route
    current = start_node
    route = [current]
    while len(route) <= len(nodes):
        for j in nodes:
            if j != current and x[current, j].solution_value() > 0.5:
                route.append(j)
                current = j
                break
    print(f"Route: {route}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Accessing `.solution_value()` on variables before confirming the solver status is `OPTIMAL` or `FEASIBLE`, which may raise an error.
- Using an incorrect tolerance (e.g., `== 1`) when checking binary variable values; floating-point results require a tolerance like `> 0.5`.
- Failing to handle potential cycles in the reconstruction logic if the solution is invalid; add a check for repeated nodes.
