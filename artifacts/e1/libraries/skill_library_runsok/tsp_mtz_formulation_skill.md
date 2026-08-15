---
name: TSP_MTZ_Formulation_Skill
description: |
  A skill for modeling and solving Traveling Salesman Problems using Miller-Tucker-Zemlin subtour elimination, with workflows for CP-SAT and MIP solvers.
---

# Workflow 1 (CP-SAT with Explicit AllDifferent)

## Modeling stage

### Strategy Overview
This workflow uses OR-Tools CP-SAT to model the TSP with binary routing and integer position variables. It explicitly enforces position distinctness with an AllDifferent constraint alongside MTZ constraints for robust subtour elimination, suitable for exact solving with parallel search.

### Step 1 - Define Variables
- Create binary decision variables `x[i][j]` for all directed arcs `(i, j)` where `i != j`, using `model.NewBoolVar()`.
- Create integer position variables `u[i]` for each city `i`, bounded between `0` and `n-1`, using `model.NewIntVar(0, n-1, ...)`.

### Step 2 - Enforce Assignment Constraints
- For each city `i`, add a constraint that the sum of outgoing arcs `sum_j x[i][j]` equals `1`.
- For each city `j`, add a constraint that the sum of incoming arcs `sum_i x[i][j]` equals `1`.
- Optionally, fix self-loop variables `x[i][i]` to `0`.

### Step 3 - Implement Subtour Elimination
- Fix the starting city's position: `u[0] == 0`.
- For all pairs `(i, j)` where `i != j` and `j != 0`, add the MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.
- Enforce position distinctness explicitly: add an `AllDifferent(u)` constraint.

### Step 4 - Formulate Objective
- Define the objective to minimize total tour cost: `sum_{i,j} cost[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    "CITIES = list of city indices"
  ],
  "parameters": [
    "cost[i][j] = travel cost from city i to city j, for i, j in CITIES"
  ],
  "decision_variables": [
    "x[i][j] ∈ {0, 1}, for i, j in CITIES, i != j",
    "u[i] ∈ {0, ..., n-1}, for i in CITIES"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in CITIES} sum_{j in CITIES, j != i} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "sum_{j in CITIES, j != i} x[i][j] == 1, for all i in CITIES",
    "sum_{i in CITIES, i != j} x[i][j] == 1, for all j in CITIES",
    "u[0] == 0",
    "u[i] - u[j] + n * x[i][j] <= n - 1, for all i, j in CITIES, i != j, j != 0",
    "AllDifferent(u)"
  ]
}
```

### Common Pitfalls
- Applying MTZ constraints to arcs entering the depot (`j == 0`) can cause infeasibility due to negative position requirements.
- Omitting the explicit `AllDifferent` constraint can lead to solutions with duplicate positions for non-adjacent cities, violating the Hamiltonian cycle.
- Not pre-processing the cost matrix to set diagonal entries (self-loops) to a prohibitively high cost or fixing the corresponding variable to zero.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with parallel search and time limits. Extract and validate the tour from the binary routing variables, and verify constraint satisfaction post-solution.

### Step 1 - Configure Solver
- Instantiate `CpSolver()`.
- Set parameters: `solver.parameters.max_time_in_seconds = time_limit`, `solver.parameters.num_search_workers = num_cores`, `solver.parameters.random_seed = seed` for reproducibility.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status: if `status` is `OPTIMAL` or `FEASIBLE`, proceed to solution extraction; else, return a failure indicator.

### Step 3 - Extract Solution
- Reconstruct the tour: start at city `0`, find `j` such that `solver.Value(x[current][j]) == 1`, append `j` to the tour, and set `current = j`. Repeat until returning to the start.
- Collect position values: `pos[i] = solver.Value(u[i])` for all cities.

### Step 4 - Validate Solution
- Verify degree constraints: each city appears exactly once in the reconstructed tour.
- Verify MTZ constraints: for each arc `(i, j)` in the tour, check `pos[i] < pos[j]`.
- Verify `AllDifferent`: all `pos[i]` values are unique.
- Calculate the objective value from the extracted tour and compare with `solver.ObjectiveValue()`.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... variable and constraint creation as per modeling stage ...
# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters
solver.parameters.max_time_in_seconds = time_limit
solver.parameters.num_search_workers = num_cores
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract tour and positions
    tour = [0]
    current = 0
    while True:
        for j in cities:
            if j != current and solver.Value(x[current][j]) == 1:
                tour.append(j)
                current = j
                break
        if current == 0:
            break
    # Validate and output
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not setting a `max_time_in_seconds` can lead to excessively long runs for large instances.
- Failing to handle `FEASIBLE` status when optimality is not guaranteed, leading to misinterpretation of solution quality.
- Incorrect tour reconstruction logic that does not handle the return to the start city correctly, causing infinite loops.

# Workflow 2 (MIP Solver with Standard MTZ)

## Modeling stage

### Strategy Overview
This workflow models the TSP using a standard MIP formulation with MTZ constraints, targeting solvers like Gurobi, SCIP, or CBC via Pyomo or direct APIs. It relies on the MTZ constraints alone for subtour elimination, omitting explicit AllDifferent, for a more compact model.

### Step 1 - Define Variables
- Create binary routing variables `x[i, j]` for `i != j`.
- Create integer position variables `u[i]` with bounds `[0, n-1]`.

### Step 2 - Enforce Flow Conservation
- Add constraints: `sum_{j, j != i} x[i, j] == 1` for all `i` (outgoing flow).
- Add constraints: `sum_{i, i != j} x[i, j] == 1` for all `j` (incoming flow).

### Step 3 - Apply MTZ Subtour Elimination
- Fix the depot position: `u[0] == 0`.
- For all `i != j` where `j != 0`, add constraint: `u[i] - u[j] + n * x[i, j] <= n - 1`.

### Step 4 - Set Objective
- Minimize `sum_{i, j, i != j} cost[i][j] * x[i, j]`.

### Formulation Template
```json
{
  "sets": [
    "CITIES = list of city indices"
  ],
  "parameters": [
    "cost[i][j] = travel cost from city i to city j, for i, j in CITIES"
  ],
  "decision_variables": [
    "x[i, j] ∈ {0, 1}, for i, j in CITIES, i != j",
    "u[i] ∈ {0, ..., n-1}, for i in CITIES"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in CITIES} sum_{j in CITIES, j != i} cost[i][j] * x[i, j]"
  },
  "constraints": [
    "sum_{j in CITIES, j != i} x[i, j] == 1, for all i in CITIES",
    "sum_{i in CITIES, i != j} x[i, j] == 1, for all j in CITIES",
    "u[0] == 0",
    "u[i] - u[j] + n * x[i, j] <= n - 1, for all i, j in CITIES, i != j, j != 0"
  ]
}
```

### Common Pitfalls
- Incorrectly applying MTZ constraints to arcs where `j == 0`, which can create infeasible constraints like `u[i] <= -1`.
- Assuming MTZ constraints alone enforce position uniqueness; for some solvers or formulations, explicit distinctness may still be needed to prevent symmetric solutions.
- Using an equality constraint (`==`) for the MTZ condition instead of inequality (`<=`), which over-constrains the model.

## Solving stage

### Strategy Overview
Solve the MIP model with an appropriate backend, setting optimality gap and time limits. Extract the tour from the binary solution matrix and perform post-solution verification.

### Step 1 - Configure Solver Parameters
- Set `TimeLimit` to control runtime.
- Set `MIPGap` (or equivalent) to `0.0` for optimality, or a small tolerance for early termination.
- Set `Threads` for parallel execution.
- Set `Seed` for reproducibility if supported.

### Step 2 - Solve and Capture Status
- Invoke the solver's `solve()` method.
- Check termination condition: `optimal`, `feasible`, `timeLimit`, or `infeasible`.

### Step 3 - Extract and Reconstruct Tour
- Retrieve variable values: `x_val[i,j] = value(x[i,j])`.
- Build the tour by starting at city `0` and following arcs where `x_val > tolerance` (e.g., `0.5`).

### Step 4 - Verify Solution Integrity
- Manually check that the extracted tour is a Hamiltonian cycle.
- For small `n`, enumerate all possible tours to verify optimality.
- Validate MTZ constraints: for each `(i,j)` with `x_val[i,j] > tolerance`, ensure `value(u[i]) < value(u[j])`.

### Code Usage
```python
# build model from formulation (example using Pyomo)
model = pyo.ConcreteModel()
model.CITIES = pyo.Set(initialize=cities)
# ... variable and constraint creation as per modeling stage ...
# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'scip', 'cbc'
solver.options['TimeLimit'] = time_limit
solver.options['MIPGap'] = gap_tolerance
results = solver.solve(model, tee=False)
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    # Extract solution
    tour = [0]
    current = 0
    while True:
        for j in model.CITIES:
            if j != current and pyo.value(model.x[current, j]) > 0.5:
                tour.append(j)
                current = j
                break
        if current == 0:
            break
    # Output tour and cost
else:
    print(f"Solver terminated with: {results.solver.termination_condition}")
```

### Common Pitfalls
- Setting `MIPGap` to an invalid negative value.
- Not checking for `feasible` termination status when time limit is reached, leading to missed suboptimal solutions.
- Using a loose tolerance (e.g., `0.1`) for extracting binary variable values, which might misidentify active arcs.
