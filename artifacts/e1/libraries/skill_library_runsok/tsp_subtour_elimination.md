---
name: TSP_Subtour_Elimination
description: |
  Model and solve Traveling Salesperson Problems with explicit subtour elimination constraints, using either MTZ or DFJ formulations, and extract valid tours from solver results.
---

# Workflow 1 (CP-SAT with MTZ Formulation)

## Modeling stage

### Strategy Overview
Model the TSP as a mixed-integer program using the Miller-Tucker-Zemlin (MTZ) formulation for subtour elimination. This approach uses auxiliary position variables and linear constraints, suitable for solvers like CP-SAT that handle logical implications and integer domains efficiently.

### Step 1 - Define Core Variables
- Create a binary decision variable `x[i][j]` for each directed arc between distinct cities `i` and `j` to represent route selection.
- Create an integer decision variable `u[i]` for each city `i` to represent its sequence position in the tour, with a domain from `1` to `N` (number of cities).

### Step 2 - Implement Flow Conservation Constraints
- Add a constraint for each city `i` that the sum of outgoing binary variables equals 1: `sum(x[i][j] for j in cities if j != i) == 1`.
- Add a constraint for each city `j` that the sum of incoming binary variables equals 1: `sum(x[i][j] for i in cities if i != j) == 1`.

### Step 3 - Apply MTZ Subtour Elimination
- For all pairs of cities `i`, `j` where `i != j` and neither is the designated start city (index 0), add the MTZ constraint: `u[i] - u[j] + N * x[i][j] <= N - 1`.
- Fix the position of the start city: `u[0] == 1`.
- For arcs leaving the start city, enforce a lower bound on the destination's position using a logical constraint: `u[j] >= 2` only if `x[0][j] == 1`.

### Step 4 - Formulate the Objective
- Define the objective to minimize total tour distance: `Minimize sum( distance[i][j] * x[i][j] for all i, j where i != j )`.

### Formulation Template
```json
{
  "sets": ["cities: list of city indices"],
  "parameters": ["distance[i][j]: matrix of travel costs between cities"],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc from i to j is used",
    "u[i]: integer, position of city i in tour"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( distance[i][j] * x[i][j] for i in cities for j in cities if i != j )"
  },
  "constraints": [
    "single_outgoing(i): sum( x[i][j] for j in cities if j != i ) == 1 for all i",
    "single_incoming(j): sum( x[i][j] for i in cities if i != j ) == 1 for all j",
    "mtz(i,j): u[i] - u[j] + N * x[i][j] <= N - 1 for all i,j where i!=j, i>0, j>0",
    "start_position: u[0] == 1",
    "logical_start_arc(j): (x[0][j] == 1) => (u[j] >= 2) for all j>0"
  ]
}
```

### Common Pitfalls
- Applying MTZ constraints to arcs involving the start city (`i=0` or `j=0`) can over-constrain the model; exclude them from the standard MTZ rule.
- Forgetting to enforce a lower bound on positions for cities visited after the start can allow invalid tours starting at position 1.
- Using a big-M value (`N`) that is too small (less than the number of cities) can make the MTZ constraint ineffective.

## Solving stage

### Strategy Overview
Solve the MIP model using the CP-SAT solver, configuring it for performance and reproducibility. After solving, programmatically reconstruct the tour from binary variable values and validate the solution's integrity.

### Step 1 - Configure and Execute Solver
- Instantiate the CP-SAT solver and set parameters: `max_time_in_seconds`, `num_search_workers`, and `random_seed` for deterministic behavior.
- Invoke the solver with the model and capture the status result (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.).

### Step 2 - Extract and Validate Solution
- If the status is `OPTIMAL` or `FEASIBLE`, iterate through the binary `x[i][j]` variables to reconstruct the Hamiltonian cycle, starting from city `0`.
- Calculate the total distance of the extracted tour independently to verify it matches the solver's reported objective value.
- If the status is `INFEASIBLE`, review constraint logic and variable bounds; do not attempt to extract variable values.

### Step 3 - Implement Iterative Refinement
- If the initial model is infeasible, debug by temporarily relaxing or removing the MTZ constraints to verify the core assignment constraints are correct.
- Systematically re-add subtour elimination constraints, checking for feasibility at each step.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (create variables and add constraints as per Modeling Stage)
model.Minimize(objective_expr)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Reconstruct tour
    tour = [0]
    current = 0
    for _ in range(N-1):
        for j in range(N):
            if current != j and solver.Value(x[current][j]) == 1:
                tour.append(j)
                current = j
                break
    # Validate
    calculated_dist = sum(dist[tour[i]][tour[i+1]] for i in range(N-1))
    calculated_dist += dist[tour[-1]][tour[0]]  # return to start
    print(f"Solver objective: {solver.ObjectiveValue()}, Calculated: {calculated_dist}")
else:
    print("Model is infeasible or not solved to feasibility.")
```

### Common Pitfalls
- Attempting to access `.Value()` on variables when the solver status is not `OPTIMAL` or `FEASIBLE` will cause an error.
- Manually reconstructing the tour incorrectly (e.g., not handling the return to start) leads to validation mismatches.
- Setting an unrealistic `relative_gap_limit` or `max_time_in_seconds` may cause premature termination without a feasible solution.

# Workflow 2 (MIP Solver with DFJ Formulation)

## Modeling stage

### Strategy Overview
Model the TSP using a pure binary programming formulation with Dantzig-Fulkerson-Johnson (DFJ) subtour elimination constraints. This method adds constraints dynamically or a priori to forbid every possible subtour, and is solved with a general-purpose MIP solver like SCIP or Gurobi.

### Step 1 - Define Routing Variables
- Create a binary decision variable `x[i][j]` for each directed arc between distinct cities `i` and `j`.

### Step 2 - Implement Degree Constraints
- Add constraints ensuring each city has exactly one outgoing arc and one incoming arc, as in Workflow 1.

### Step 3 - Formulate DFJ Subtour Elimination
- For every non-empty proper subset `S` of cities (excluding the full set and the empty set), add a constraint: `sum( x[i][j] for i in S for j in S if i != j ) <= |S| - 1`.
- In practice, these constraints can be added lazily via callbacks (lazy constraints) during the branch-and-cut process to avoid an exponential number upfront.

### Step 4 - Set the Objective
- Define the objective to minimize total distance, identical to the MTZ formulation.

### Formulation Template
```json
{
  "sets": ["cities: list of city indices"],
  "parameters": ["distance[i][j]: matrix of travel costs between cities"],
  "decision_variables": ["x[i][j]: binary, 1 if arc from i to j is used"],
  "objective": {
    "sense": "min",
    "expression": "sum( distance[i][j] * x[i][j] for i in cities for j in cities if i != j )"
  },
  "constraints": [
    "out_degree(i): sum( x[i][j] for j in cities if j != i ) == 1 for all i",
    "in_degree(j): sum( x[i][j] for i in cities if i != j ) == 1 for all j",
    "subtour_elimination(S): sum( x[i][j] for i in S for j in S if i != j ) <= |S| - 1 for all S subset of cities, 1 < |S| < |cities|"
  ]
}
```

### Common Pitfalls
- Adding all DFJ constraints explicitly for large `N` is computationally prohibitive; use solver callbacks for lazy constraint addition.
- Forgetting to exclude the case where `S` is the full set of cities invalidates the formulation.
- In asymmetric TSP, the DFJ constraint must consider directed arcs within the subset.

## Solving stage

### Strategy Overview
Solve the model using a traditional MIP solver capable of handling lazy constraints. Configure solver tolerances and limits appropriately. After solving, extract the tour and validate it, similar to the CP-SAT workflow.

### Step 1 - Configure Solver and Solve
- Instantiate the solver (e.g., via Pyomo or direct API) and set parameters: `TimeLimit`, `MIPGap`, `Threads`, and `Seed`.
- If using lazy constraints, implement a callback that identifies violated subtour constraints using the current solution and adds them to the model.
- Invoke the solver and capture the termination condition.

### Step 2 - Process Solution and Verify
- Check if the termination condition is `optimal` or `feasible`.
- Extract the values of binary variables and reconstruct the tour starting from the designated start city.
- Independently calculate the tour distance and compare it to the solver's objective value for validation.

### Step 3 - Implement Subtour Separation Callback
- In the callback, get the current solution values for `x[i][j]`.
- Construct a directed graph from arcs where `x[i][j] > 0.5`.
- Identify connected components (subtours) that do not include all cities.
- For each violating subtour `S`, add the corresponding DFJ constraint to the model.

### Code Usage
```python
# build model from formulation (using Pyomo example)
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.cities = pyo.Set(initialize=range(N))
model.x = pyo.Var(model.cities, model.cities, domain=pyo.Binary)
# ... (add degree constraints and objective)

# solve with status / termination checks
solver = pyo.SolverFactory('scip')
solver.options['limits/time'] = 300
solver.options['parallel/minnthreads'] = 4
solver.options['randomization/randomseedshift'] = 42
results = solver.solve(model, tee=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    # Extract solution
    tour = [0]
    current = 0
    for _ in range(N-1):
        for j in model.cities:
            if current != j and pyo.value(model.x[current, j]) > 0.5:
                tour.append(j)
                current = j
                break
    # Validate
    calculated_dist = sum(dist[tour[i]][tour[i+1]] for i in range(N-1))
    calculated_dist += dist[tour[-1]][tour[0]]
    print(f"Solver objective: {pyo.value(model.obj)}, Calculated: {calculated_dist}")
else:
    print(f"Solver terminated with: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not enabling lazy constraint support in the solver can lead to incorrect results if not all DFJ constraints are added a priori.
- Incorrectly identifying subtours in the callback (e.g., missing directed cycles) leads to missing violated constraints.
- Setting `MIPGap` to an invalid value (like -1) may cause solver errors; use 0.0 for optimality or a small positive tolerance.
