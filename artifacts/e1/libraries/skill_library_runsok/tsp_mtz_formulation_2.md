---
name: TSP_MTZ_Formulation
description: |
  Model the Traveling Salesperson Problem using binary arc selection and integer node position variables with Miller-Tucker-Zemlin subtour elimination, then solve via a Mixed-Integer Programming or CP-SAT solver.
---

# Workflow 1 (MIP Solver with MTZ)

## Modeling stage

### Strategy Overview
This workflow models the TSP as a Mixed-Integer Program using the Miller-Tucker-Zemlin (MTZ) formulation. It is suitable for solvers like SCIP, CBC, or Gurobi that handle linear constraints with binary and integer variables directly.

### Step 1 - Define Variables
- Create binary decision variables `x[i][j]` for all ordered pairs of distinct nodes `(i, j)` where `i != j`. A value of 1 indicates the arc from node i to node j is selected in the tour.
- Create integer position variables `u[i]` for each node i, bounded between 1 and the number of nodes `n`. These represent the sequence order of the node in the tour.

### Step 2 - Enforce Flow Conservation
- For each node i, add a constraint that the sum of outgoing arcs equals 1: `sum(x[i][j] for j in nodes if j != i) == 1`.
- For each node j, add a constraint that the sum of incoming arcs equals 1: `sum(x[i][j] for i in nodes if i != j) == 1`.

### Step 3 - Eliminate Subtours with MTZ
- For all ordered pairs `(i, j)` where `i != j` and neither i nor j is the designated start node, add the MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.
- This constraint forces a logical ordering, preventing cycles that do not include all nodes.

### Step 4 - Fix Start and Define Objective
- Fix the position of the start node to 1 to break symmetry: `u[start_node] == 1`.
- Define the objective to minimize total travel distance: `minimize sum( distance[i][j] * x[i][j] for all i != j )`.

### Formulation Template
```json
{
  "sets": [
    "nodes: list of node indices"
  ],
  "parameters": [
    "distance[i][j]: cost matrix for traveling from node i to node j",
    "start_node: index of the fixed starting node"
  ],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc i->j is in tour",
    "u[i]: integer, position of node i in tour (1..n)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in nodes} sum_{j in nodes, j != i} distance[i][j] * x[i][j]"
  },
  "constraints": [
    "single_exit: for all i in nodes, sum_{j in nodes, j != i} x[i][j] == 1",
    "single_entry: for all j in nodes, sum_{i in nodes, i != j} x[i][j] == 1",
    "mtz: for all i,j in nodes, i != j, i != start_node, j != start_node: u[i] - u[j] + n * x[i][j] <= n - 1",
    "fix_start: u[start_node] == 1"
  ]
}
```

### Common Pitfalls
- Applying the MTZ constraint to arcs involving the start node, which can make the model infeasible. Exclude `i = start_node` and `j = start_node`.
- Forgetting to enforce `i != j` in the MTZ constraint loops, which is unnecessary and can cause errors.
- Using an incorrect coefficient (e.g., `(n-1) * x[i][j]`) in the MTZ constraint; the standard form uses `n * x[i][j]`.

## Solving stage

### Strategy Overview
Solve the MIP model using a traditional linear programming solver interface (e.g., OR-Tools `pywraplp`, Pyomo). Configure for optimality or time-limited feasible solutions, then extract the tour by following active arcs.

### Step 1 - Configure and Solve
- Instantiate a MIP solver (e.g., `SCIP`, `CBC`, `GUROBI`).
- Set solver parameters: time limit, optimality gap tolerance (`MIPGap`), number of threads, and a random seed for reproducibility.
- Invoke the solver and capture the status/termination condition.

### Step 2 - Extract and Validate Solution
- Check if the solver status is `OPTIMAL` or `FEASIBLE` before proceeding.
- Reconstruct the tour sequence: start at `start_node`, then iteratively find the next node `j` where `x[current_node][j].solution_value() > 0.5`.
- Verify solution integrity by calculating the total distance from the reconstructed tour and comparing it to the solver's reported objective value.

### Step 3 - Handle Results and Errors
- Output results in a structured format (e.g., JSON) containing status, objective value, tour sequence, and position variables.
- For infeasible or error statuses, provide diagnostic information and suggest checking the MTZ constraint formulation and distance matrix.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... create variables, constraints, and objective as per modeling stage

# solve with status / termination checks
solver.SetTimeLimit(time_limit_milliseconds)
solver.SetNumThreads(num_threads)
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Extract tour
    tour = [start_node]
    current = start_node
    while len(tour) < n:
        for j in range(n):
            if j != current and x[current][j].solution_value() > 0.5:
                tour.append(j)
                current = j
                break
    # Output results
    result = {
        "status": "OPTIMAL" if status == solver.OPTIMAL else "FEASIBLE",
        "objective": solver.Objective().Value(),
        "tour": tour
    }
else:
    result = {"status": "INFEASIBLE_OR_UNBOUNDED", "message": "Solver failed to find a solution."}
```

### Common Pitfalls
- Not checking solver status before accessing `solution_value()`, which can cause runtime errors.
- Incorrect tour reconstruction logic that gets stuck in a loop; ensure each iteration finds a unique next node.
- Setting an invalid optimality gap (e.g., negative value); use `0.0` for absolute optimality.

# Workflow 2 (CP-SAT Solver with MTZ)

## Modeling stage

### Strategy Overview
This workflow models the TSP using OR-Tools CP-SAT solver, which is optimized for combinatorial problems with integer and boolean variables. The MTZ formulation is adapted using CP-SAT's linear constraint API.

### Step 1 - Define CP-SAT Variables
- Create Boolean decision variables `x[i][j]` for all `i != j` using `model.NewBoolVar()`.
- Create integer position variables `u[i]` using `model.NewIntVar(1, n, '')`.

### Step 2 - Enforce Single Visit Constraints
- For each node i, add an exactly-one constraint over its outgoing Boolean variables: `model.Add(sum(x[i][j] for j in nodes if j != i) == 1)`.
- For each node j, add an exactly-one constraint over its incoming Boolean variables: `model.Add(sum(x[i][j] for i in nodes if i != j) == 1)`.

### Step 3 - Apply MTZ Subtour Elimination
- For all `i, j` where `i != j` and neither is the start node, add the linear constraint: `model.Add(u[i] - u[j] + n * x[i][j] <= n - 1)`.
- Optionally, add an `AllDifferent` constraint on the position variables to strengthen the formulation: `model.AddAllDifferent(u)`.

### Step 4 - Anchor Start and Set Objective
- Fix the start node's position: `model.Add(u[start_node] == 1)`.
- Define the minimization objective: `model.Minimize( sum( distance[i][j] * x[i][j] for all i != j ) )`.

### Formulation Template
```json
{
  "sets": [
    "nodes: list of node indices"
  ],
  "parameters": [
    "distance[i][j]: cost matrix for traveling from node i to node j",
    "start_node: index of the fixed starting node"
  ],
  "decision_variables": [
    "x[i][j]: Boolean, True if arc i->j is in tour",
    "u[i]: integer, position of node i in tour (1..n)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in nodes} sum_{j in nodes, j != i} distance[i][j] * x[i][j]"
  },
  "constraints": [
    "single_exit: for all i in nodes, sum_{j in nodes, j != i} x[i][j] == 1",
    "single_entry: for all j in nodes, sum_{i in nodes, i != j} x[i][j] == 1",
    "mtz: for all i,j in nodes, i != j, i != start_node, j != start_node: u[i] - u[j] + n * x[i][j] <= n - 1",
    "fix_start: u[start_node] == 1",
    "all_diff: AllDifferent(u)  # optional strengthening"
  ]
}
```

### Common Pitfalls
- Using `model.Add(u[i] - u[j] + n * x[i][j] <= n - 1)` for arcs where `i` or `j` is the start node, which is unnecessary and restrictive.
- Creating Boolean variables for self-loops (`i == j`), which wastes memory and complicates constraints.
- Neglecting to set a time limit or search parameters, which can lead to excessively long runtimes for larger instances.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured search parameters. Leverage its parallel search capabilities and use status codes to handle optimal and feasible solutions, then reconstruct the tour from Boolean variable values.

### Step 1 - Configure Solver and Solve
- Set solver parameters: `max_time_in_seconds`, `num_search_workers`, and `random_seed` for deterministic behavior.
- Call `solver.Solve(model)` and capture the resulting status.

### Step 2 - Reconstruct Tour and Verify
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- Reconstruct the tour: start at `start_node`, then repeatedly find the next node `j` where `solver.Value(x[current][j]) == 1`.
- Validate by computing the total distance of the extracted tour and comparing it to the solver's objective value.

### Step 3 - Output and Error Handling
- Return results in a parseable format (e.g., JSON) including status, objective, tour, and optionally position values.
- For non-successful statuses (e.g., `MODEL_INVALID`, `INFEASIBLE`), log diagnostic details and suggest reviewing constraint logic, especially MTZ exclusions.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... create Boolean and integer variables, add constraints and objective as per modeling stage

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = time_limit
solver.parameters.num_search_workers = num_workers
solver.parameters.random_seed = random_seed
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract tour
    tour = [start_node]
    current = start_node
    while len(tour) < n:
        for j in range(n):
            if j != current and solver.Value(x[current][j]) == 1:
                tour.append(j)
                current = j
                break
    # Output results
    result = {
        "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
        "objective": solver.ObjectiveValue(),
        "tour": tour
    }
else:
    result = {"status": solver.StatusName(status), "message": "Solver did not find a solution."}
```

### Common Pitfalls
- Confusing CP-SAT's `OPTIMAL`/`FEASIBLE` statuses with MIP solver's status codes; use the correct constants from `cp_model`.
- Forgetting that `solver.Value()` returns an integer (0/1) for Boolean variables; direct comparison to `True` is incorrect.
- Not using `solver.parameters.random_seed` when reproducibility across runs is required.
