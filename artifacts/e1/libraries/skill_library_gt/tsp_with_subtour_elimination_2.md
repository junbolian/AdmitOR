---
name: TSP with Subtour Elimination
description: |
  Model and solve the Traveling Salesperson Problem using binary routing variables and subtour elimination constraints, with workflows for CP-SAT and MIP solvers.
---

# Workflow 1 (CP-SAT with MTZ Formulation)

## Modeling stage

### Strategy Overview
This workflow models the TSP using the Miller-Tucker-Zemlin (MTZ) subtour elimination constraints within the Google OR-Tools CP-SAT solver. It uses binary arc selection variables and integer position variables to enforce a Hamiltonian cycle.

### Step 1 - Define Sets and Parameters
- Define a set of cities, typically indexed from `0` to `n-1`.
- Define a distance matrix `dist[i][j]` for all ordered pairs of distinct cities.

### Step 2 - Create Decision Variables
- Create a binary variable `x[i][j]` for each directed arc `(i, j)` where `i != j`, representing whether the tour includes that arc.
- Create an integer variable `u[i]` for each city `i`, representing its position in the tour, with domain `[1, n]`.

### Step 3 - Apply Standard TSP Constraints
- For each city `i`, add a constraint that the sum of outgoing arcs `sum_{j != i} x[i][j]` equals `1`.
- For each city `i`, add a constraint that the sum of incoming arcs `sum_{j != i} x[j][i]` equals `1`.

### Step 4 - Implement MTZ Subtour Elimination
- Fix the position of the starting city: `u[0] = 1`.
- For all cities `i, j` where `i != j`, `i >= 1`, and `j >= 1`, add the MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.
- For arcs leaving the starting city (`i=0, j>=1`), add an indicator constraint: `u[j] >= 2` only if `x[0][j] == 1`.

### Step 5 - Define the Objective
- Set the objective to minimize the total tour distance: `sum_{i, j, i != j} dist[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "cities", "description": "List of all cities to visit", "index": "i, j"}
  ],
  "parameters": [
    {"name": "dist", "description": "Distance matrix, dist[i][j] is cost from i to j", "type": "float[][]"},
    {"name": "n", "description": "Number of cities", "type": "int"}
  ],
  "decision_variables": [
    {"name": "x", "description": "Binary, 1 if arc (i,j) is in the tour", "type": "binary", "indices": ["i", "j"], "condition": "i != j"},
    {"name": "u", "description": "Integer position of city i in the tour", "type": "integer", "indices": ["i"], "domain": [1, "n"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i, j, i != j} dist[i][j] * x[i][j]"
  },
  "constraints": [
    {"name": "outgoing_flow", "expression": "sum_{j, j != i} x[i][j] == 1", "for_all": "i"},
    {"name": "incoming_flow", "expression": "sum_{j, j != i} x[j][i] == 1", "for_all": "i"},
    {"name": "start_position", "expression": "u[0] == 1"},
    {"name": "mtz", "expression": "u[i] - u[j] + n * x[i][j] <= n - 1", "for_all": ["i", "j"], "condition": "i != j, i>=1, j>=1"},
    {"name": "start_arc_position", "expression": "u[j] >= 2", "enforced_if": "x[0][j] == 1", "for_all": "j, j>=1"}
  ]
}
```

### Common Pitfalls
- Applying the standard MTZ constraint for arcs involving the starting city (`i=0` or `j=0`), which conflicts with the fixed start position.
- Using an arbitrary large constant (`big-M`) instead of the number of cities `n` in the MTZ constraint, causing numerical issues.
- Forgetting to enforce position constraints for arcs leaving the start via indicator (`OnlyEnforceIf`).
- Assuming position variables `u[i]` will have unique values; MTZ only prevents cycles, not duplicate positions.

## Solving stage

### Strategy Overview
Solve the formulated CP-SAT model, extract the optimal tour by following selected arcs, and verify solution integrity against the distance matrix.

### Step 1 - Configure and Run the Solver
- Instantiate the CP-SAT solver.
- Set a time limit (`max_time_in_seconds`).
- Set the number of parallel workers (`num_search_workers`).
- Set the relative optimality gap to `0.0` for an exact solution.
- Call the solver's `Solve` method.

### Step 2 - Check Solver Status and Extract Solution
- Check if the solver status is `OPTIMAL` or `FEASIBLE`.
- If optimal/feasible, retrieve the value of each `x[i][j]` variable.
- Reconstruct the tour by starting at city `0` and repeatedly finding the next city `j` where `x[current][j]` equals `1`.

### Step 3 - Validate and Report the Solution
- Calculate the total distance of the reconstructed tour using the `dist` matrix.
- Compare this calculated distance with the solver's reported objective value to ensure consistency.
- Output the ordered list of cities in the tour and the total distance.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 8
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract tour from x[i][j] variables
    tour = [0]
    current = 0
    while len(tour) < n:
        for j in range(n):
            if j != current and solver.Value(x[current][j]) == 1:
                tour.append(j)
                current = j
                break
    # Validate objective
    calculated_dist = sum(dist[tour[i]][tour[(i+1)%n]] for i in range(n))
    print(f"Tour: {tour}, Distance: {calculated_dist}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not verifying the reconstructed tour forms a single cycle covering all cities.
- Misinterpreting solver status codes (e.g., `UNKNOWN`).
- Failing to handle the indicator constraint for start arcs correctly in the solution extraction logic.
- Not setting a time limit, causing the solver to run indefinitely on large instances.

# Workflow 2 (MIP Solver with MTZ Formulation)

## Modeling stage

### Strategy Overview
This workflow models the TSP using the same MTZ formulation but targets a traditional Mixed-Integer Programming (MIP) solver (e.g., SCIP, CBC). It uses linear constraints without CP-SAT's indicator features, adapting the start arc constraint accordingly.

### Step 1 - Define Sets and Parameters
- Define the set of cities and the distance matrix, identical to Workflow 1.

### Step 2 - Create Decision Variables
- Create binary variables `x[i][j]` for all `i != j`.
- Create integer variables `u[i]` with bounds `[0, n-1]` (or `[1, n]`).

### Step 3 - Apply Standard TSP Constraints
- Add outgoing flow constraints: `sum_{j != i} x[i][j] == 1` for all `i`.
- Add incoming flow constraints: `sum_{j != i} x[j][i] == 1` for all `i`.

### Step 4 - Implement MTZ Subtour Elimination for MIP
- Fix the starting city position: `u[0] = 0`.
- For all `i, j` where `i != j` and `i >= 1, j >= 1`, add the constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.
- For arcs from the start (`i=0, j>=1`), add a linear constraint: `u[j] >= 1 - n * (1 - x[0][j])`. This linearizes the indicator condition.

### Step 5 - Define the Objective
- Minimize the total distance: `min sum_{i, j, i != j} dist[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "cities", "description": "List of all cities to visit", "index": "i, j"}
  ],
  "parameters": [
    {"name": "dist", "description": "Distance matrix", "type": "float[][]"},
    {"name": "n", "description": "Number of cities", "type": "int"}
  ],
  "decision_variables": [
    {"name": "x", "description": "Binary arc selection variable", "type": "binary", "indices": ["i", "j"], "condition": "i != j"},
    {"name": "u", "description": "Integer visit order position", "type": "integer", "indices": ["i"], "domain": [0, "n-1"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i, j, i != j} dist[i][j] * x[i][j]"
  },
  "constraints": [
    {"name": "outgoing_flow", "expression": "sum_{j, j != i} x[i][j] == 1", "for_all": "i"},
    {"name": "incoming_flow", "expression": "sum_{j, j != i} x[j][i] == 1", "for_all": "i"},
    {"name": "start_position", "expression": "u[0] == 0"},
    {"name": "mtz", "expression": "u[i] - u[j] + n * x[i][j] <= n - 1", "for_all": ["i", "j"], "condition": "i != j, i>=1, j>=1"},
    {"name": "start_arc_linear", "expression": "u[j] >= 1 - n * (1 - x[0][j])", "for_all": "j, j>=1"}
  ]
}
```

### Common Pitfalls
- Using the wrong coefficient (`big-M`) in the linearized start arc constraint, leading to a weak or incorrect formulation.
- Setting the position variable domain inconsistently (e.g., `[1,n]` for `u` but using `u[0]=0`).
- Applying the standard MTZ constraint to arcs involving the start city, creating infeasibility.
- Forgetting to exclude the start city (`i=0, j=0`) from the standard MTZ constraints.

## Solving stage

### Strategy Overview
Solve the MIP model using a solver like SCIP or CBC, extract the tour from the binary variables, and validate the solution.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `Solver.CreateSolver('SCIP')`).
- Set a time limit in milliseconds.
- Set the number of threads for parallel solving.
- Set the MIP relative gap tolerance (e.g., `0.0` for optimality).

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the result status for `OPTIMAL` or `FEASIBLE`.

### Step 3 - Extract and Reconstruct the Tour
- If solved successfully, iterate over the `x[i][j]` variables and collect arcs where the solution value is greater than `0.5`.
- Starting from city `0`, follow the selected arcs to build the tour sequence.

### Step 4 - Validate and Output Results
- Calculate the total distance of the extracted tour.
- Verify it matches the solver's objective value within tolerance.
- Output the tour and its cost.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)
# Set other parameters as needed

status = solver.Solve()

if status in [solver.OPTIMAL, solver.FEASIBLE]:
    # Extract tour
    tour = [0]
    current = 0
    visited = set([0])
    while len(tour) < n:
        for j in range(n):
            if j != current and x[current][j].solution_value() > 0.5:
                tour.append(j)
                current = j
                break
    # Validate
    calculated_dist = sum(dist[tour[i]][tour[(i+1)%n]] for i in range(n))
    print(f"Tour: {tour}, Objective: {solver.Objective().Value()}, Calculated: {calculated_dist}")
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not checking the solver status before accessing solution values, leading to errors.
- Using a loose tolerance when comparing arc selection values (e.g., `== 1.0`), risking missed arcs due to numerical precision.
- Omitting the validation step, potentially reporting an incorrect tour if the model or extraction has an error.
- Setting inappropriate MIP gap or time limit parameters for the problem size.
