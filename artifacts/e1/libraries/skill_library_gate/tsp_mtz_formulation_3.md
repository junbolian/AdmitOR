---
name: TSP_MTZ_Formulation
description: |
  Model and solve the Traveling Salesperson Problem (TSP) using the Miller-Tucker-Zemlin (MTZ) subtour elimination formulation, applicable to both symmetric and asymmetric instances, with implementation guidance for CP-SAT and MIP solvers.
---

# Workflow 1 (CP-SAT with MTZ)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, which is designed for constraint programming and integer problems. The MTZ formulation is implemented with integer position variables and binary arc selection variables, leveraging CP-SAT's native support for logical constraints and AllDifferent.

### Step 1 - Define Core Variables
- Create a binary decision variable `x[i][j]` for each directed arc between distinct nodes `i` and `j`. This variable indicates if the arc is part of the tour.
- Create an integer variable `u[i]` for each node `i`, representing its position in the tour sequence, bounded between `1` and `n` (or `0` and `n-1`).

### Step 2 - Enforce Routing Constraints
- For each node `i`, add a constraint that the sum of outgoing arcs equals `1`: `sum(x[i][j] for j != i) == 1`.
- For each node `i`, add a constraint that the sum of incoming arcs equals `1`: `sum(x[j][i] for j != i) == 1`.
- Optionally, explicitly fix self-loop variables to zero: `x[i][i] == 0`.

### Step 3 - Implement MTZ Subtour Elimination
- Fix the position of the start node (e.g., `u[start_node] == 1`).
- For all pairs of non-start nodes `i` and `j` where `i != j`, add the MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.
- To strengthen the formulation, consider adding an `AllDifferent` constraint on the position variables `u`.

### Step 4 - Formulate the Objective
- Define the objective to minimize the total travel distance: `minimize sum( distance[i][j] * x[i][j] for all i != j )`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (cities)"
  ],
  "parameters": [
    "distance[i][j]: travel cost from node i to j, for i,j in N, i != j"
  ],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc (i,j) is traversed, for i,j in N, i != j",
    "u[i]: integer, position of node i in the tour, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( distance[i][j] * x[i][j] for i,j in N, i != j )"
  },
  "constraints": [
    "single_exit: sum( x[i][j] for j in N, j != i ) == 1, for all i in N",
    "single_entry: sum( x[j][i] for j in N, j != i ) == 1, for all i in N",
    "start_position: u[start_node] == 1",
    "mtz: u[i] - u[j] + |N| * x[i][j] <= |N| - 1, for all i,j in N \\ {start_node}, i != j"
  ]
}
```

### Common Pitfalls
- Applying MTZ constraints to the start node, which can cause infeasibility. Exclude the start node from the `i,j` pairs in the MTZ constraint.
- Forgetting to exclude self-loops (`i != j`) when creating arc variables or in the objective sum.
- Using an incorrect big-M value in the MTZ constraint; it should be the number of nodes `|N|`.

## Solving stage

### Strategy Overview
Solve the formulated model using the OR-Tools CP-SAT solver. Configure search parameters for a balance of speed and proof of optimality, then extract and validate the tour from the binary arc variables.

### Step 1 - Configure and Execute Solver
- Instantiate a `CpModel` and build the formulation as described.
- Create a `CpSolver` and set parameters: `max_time_in_seconds` for a time limit, `num_search_workers` for parallelism, and `random_seed` for reproducibility.
- Set `relative_gap_limit` to `0.0` to search for a proven optimal solution.
- Call the solver's `Solve` method with the model.

### Step 2 - Check Status and Extract Solution
- Check the solver's return status. Proceed only if the status is `OPTIMAL` or `FEASIBLE`.
- If feasible, extract the tour by starting at the designated start node and iteratively finding the next node `j` where the solution value for `x[current][j]` is `1`.
- Store the sequence of nodes in a list representing the tour.

### Step 3 - Validate and Report Results
- Compute the total distance of the extracted tour independently using the `distance` matrix to validate against the solver's objective value.
- Report the tour, total distance, solver status, and solve time.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (build variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract tour from arc variables x
    tour = [start_node]
    current = start_node
    for _ in range(len(N) - 1):
        for j in N:
            if j != current and solver.Value(x[current][j]) == 1:
                tour.append(j)
                current = j
                break
    # Validate and report
    calculated_distance = sum(distance[tour[k]][tour[k+1]] for k in range(len(tour)-1))
    print(f"Tour: {tour}, Distance: {calculated_distance}, Status: {status}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver status before attempting to extract variable values, which will cause an error.
- Incorrectly reconstructing the tour by not ensuring each step finds a unique next node; the single-exit constraint guarantees this.
- Misinterpreting `relative_gap_limit`; use `0.0` for exact optimality, not a negative value.

# Workflow 2 (MIP Solver with MTZ)

## Modeling stage

### Strategy Overview
This workflow uses a traditional Mixed-Integer Programming (MIP) solver (e.g., Gurobi, SCIP, CBC) via a modeling interface like `pyomo` or `ortools.linear_solver`. The MTZ formulation is implemented with linear constraints, suitable for solvers expecting a standard MIP.

### Step 1 - Define Variables and Bounds
- Create binary variables `x[i][j]` for `i != j` using `solver.IntVar(0, 1, ...)` or equivalent.
- Create integer or continuous variables `u[i]` with bounds `[0, n-1]` or `[1, n]`.

### Step 2 - Add Assignment and MTZ Constraints
- Add linear constraints for single exit and single entry per node using `solver.Add(sum(...) == 1)`.
- Fix the start node's position: `u[start_node] == 0` (or `1`).
- Add the linear MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1` for all non-start `i != j`.

### Step 3 - Set Linear Objective
- Define the objective as a linear expression: `solver.Minimize(sum(distance[i][j] * x[i][j] for i != j))`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes"
  ],
  "parameters": [
    "distance[i][j]: cost matrix, for i,j in N, i != j"
  ],
  "decision_variables": [
    "x[i][j]: binary, arc selection",
    "u[i]: continuous or integer, position variable"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( distance[i][j] * x[i][j] for i,j in N, i != j )"
  },
  "constraints": [
    "flow_conservation_out: sum( x[i][j] for j in N, j != i ) == 1, for i in N",
    "flow_conservation_in: sum( x[j][i] for j in N, j != i ) == 1, for i in N",
    "position_anchor: u[start_node] == 0",
    "subtour_elimination: u[i] - u[j] + |N| * x[i][j] <= |N| - 1, for i,j in N \\ {start_node}, i != j"
  ]
}
```

### Common Pitfalls
- Using an incorrect sense for the MTZ inequality; it must be `<=`.
- Not setting appropriate solver parameters (like `MIPGap`) for proving optimality.
- Creating variables for self-loops (`i == j`) unnecessarily, which wastes memory and can cause formulation errors.

## Solving stage

### Strategy Overview
Solve the MIP model using a chosen backend solver. Configure optimality tolerances and time limits, then extract the solution by following the active arcs. Verify the solution's correctness and optimality status.

### Step 1 - Configure Solver Parameters
- Set a time limit (`TimeLimit`) to prevent excessive runtime.
- Set the optimality gap (`MIPGap`) to `0.0` or a very small tolerance (e.g., `1e-4`) for a near-optimal solution.
- Set the number of threads (`Threads`) for parallel processing, or set to `1` for deterministic results.
- Optionally, set a random seed (`Seed`) for reproducibility.

### Step 2 - Solve and Inspect Status
- Call the solver's `Solve()` method.
- Check the termination condition (`OPTIMAL`, `FEASIBLE`, `TIME_LIMIT`, etc.) and the solver status flag.
- Proceed only if a feasible solution is available.

### Step 3 - Extract and Verify Tour
- Extract the solution values for the binary arc variables `x[i][j]`.
- Reconstruct the tour by starting at the start node and following arcs where `x[i][j].solution_value() > 0.5`.
- Calculate the total distance of the extracted tour and compare it to the solver's reported objective value.

### Code Usage
```python
# build model from formulation
solver = pyomo.SolverFactory('gurobi') # or 'scip', 'cbc'
instance = model.create_instance(data)
# ... (set objective and constraints as per modeling stage)

# solve with status / termination checks
results = solver.solve(instance, tee=True, options={'TimeLimit': 30, 'MIPGap': 0.0})

if results.solver.termination_condition == pyomo.TerminationCondition.optimal:
    # Extract variable values
    for i,j in instance.N:
        if i != j:
            x_val = instance.x[i,j].value
            # store value...
    # Reconstruct tour
    tour = [start_node]
    current = start_node
    visited = set(tour)
    while len(visited) < len(instance.N):
        for j in instance.N:
            if j != current and instance.x[current,j].value > 0.5:
                tour.append(j)
                current = j
                visited.add(j)
                break
    # Verify
    calculated_dist = sum(instance.distance[tour[k]][tour[k+1]] for k in range(len(tour)-1))
    print(f"Optimal tour found: {tour}, distance: {calculated_dist}")
elif results.solver.termination_condition == pyomo.TerminationCondition.feasible:
    print("Feasible solution found, but optimality not guaranteed.")
else:
    print(f"Solver terminated with condition: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`); both should be checked.
- Using a negative value for `MIPGap`, which is invalid; use `0.0` for optimality.
- Not using a tolerance (e.g., `> 0.5`) when checking the value of binary variables due to numerical precision.
