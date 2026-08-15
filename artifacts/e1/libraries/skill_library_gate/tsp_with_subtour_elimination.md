---
name: TSP with Subtour Elimination
description: |
  Model and solve Traveling Salesman Problems using binary arc selection and node position variables, with explicit subtour elimination constraints and robust solver handling.

---

# Workflow 1 (MIP with MTZ Subtour Elimination)

## Modeling stage

### Strategy Overview
Formulate the TSP as a Mixed-Integer Program (MIP) using the Miller-Tucker-Zemlin (MTZ) constraints for subtour elimination. This approach uses binary arc variables and integer position variables, suitable for solvers like SCIP, Gurobi, or CPLEX.

### Step 1 - Define Core Variables
- Create binary decision variable `x[i,j]` for each ordered pair of distinct nodes `(i, j)` to indicate if arc `(i, j)` is part of the tour.
- Create integer decision variable `u[i]` for each node `i` to represent its position in the tour sequence.

### Step 2 - Implement Flow Conservation
- For each node `i`, add a constraint `sum(x[i,j] for j in N if j != i) == 1` to ensure a single departure.
- For each node `j`, add a constraint `sum(x[i,j] for i in N if i != j) == 1` to ensure a single arrival.
- Explicitly set `x[i,i] = 0` for all `i` to prohibit self-loops.

### Step 3 - Apply MTZ Subtour Elimination
- For all `i, j` where `i != j` and `j != depot_node`, add the constraint `u[j] >= u[i] + 1 - M * (1 - x[i,j])`.
- Set the big-M parameter `M` to `num_nodes - 1` to ensure constraint activity only when the arc is selected.
- Fix the position of the starting depot: `u[depot_node] = 0`.
- Bound other position variables: `1 <= u[i] <= num_nodes - 1` for `i != depot_node`.

### Step 4 - Formulate the Objective
- Define the objective as minimizing the total travel cost: `min sum(cost[i,j] * x[i,j] for i,j in N if i != j)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (cities/locations)"
  ],
  "parameters": [
    "cost[i,j]: travel cost from node i to node j, for i,j in N, i != j",
    "depot_node: index of the starting/root node",
    "num_nodes: total number of nodes, |N|"
  ],
  "decision_variables": [
    "x[i,j]: binary, 1 if arc (i,j) is selected, for i,j in N, i != j",
    "u[i]: integer, position of node i in the tour, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i,j in N if i != j)"
  },
  "constraints": [
    "single_departure[i in N]: sum(x[i,j] for j in N if j != i) == 1",
    "single_arrival[j in N]: sum(x[i,j] for i in N if i != j) == 1",
    "no_self_loop[i in N]: x[i,i] == 0",
    "mtz[i in N, j in N if i != j and j != depot_node]: u[j] >= u[i] + 1 - (num_nodes - 1) * (1 - x[i,j])",
    "fix_depot_position: u[depot_node] == 0",
    "position_bounds[i in N if i != depot_node]: 1 <= u[i] <= num_nodes - 1"
  ]
}
```

### Common Pitfalls
- Setting the big-M value too small, which can cut off valid tours, or too large, which weakens the LP relaxation.
- Forgetting to exclude constraints for `j == depot_node` in MTZ, which can incorrectly prevent the return arc to the depot.
- Not fixing the depot position or applying symmetry-breaking constraints, leading to a slower solve time.

## Solving stage

### Strategy Overview
Solve the MIP model using a traditional branch-and-cut solver. Configure for optimality, manage runtime limits, and implement robust checks for solution status before extracting and validating the tour.

### Step 1 - Configure Solver and Solve
- Instantiate a MIP solver (e.g., `SCIP`, `CBC`, `GUROBI`).
- Set a time limit (`SetTimeLimit`), optimality gap tolerance (`SetRelativeGapTolerance`), and number of threads (`SetNumThreads`).
- Call the solver's `Solve()` method and capture the result status.

### Step 2 - Check Solution Status
- Check if the solver status is `OPTIMAL` or `FEASIBLE`. If `INFEASIBLE` or `UNKNOWN`, handle the error and analyze the model.
- Only proceed to extract variable values if a feasible solution is confirmed.

### Step 3 - Extract and Reconstruct the Tour
- Extract all arcs where `x[i,j].solution_value() > 0.5`.
- Starting from the `depot_node`, iteratively follow the selected outgoing arcs to reconstruct the Hamiltonian cycle.
- Optionally, extract the `u[i]` values to verify the position ordering.

### Step 4 - Validate Solution
- Verify the reconstructed tour visits each node exactly once.
- Recalculate the total cost from the extracted arcs and compare it to the solver's reported objective value.
- For small instances, cross-check optimality via enumeration or an alternative formulation.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=N)  # N is the list of nodes
model.x = pyo.Var(model.N, model.N, within=pyo.Binary)
model.u = pyo.Var(model.N, within=pyo.NonNegativeIntegers)

# Add constraints as per Formulation Template...
# ...

# solve with status / termination checks
solver = pyo.SolverFactory('scip')
solver.options['limits/time'] = time_limit
solver.options['limits/gap'] = optimality_gap
results = solver.solve(model, tee=False)

# Check status
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    print("Optimal solution found.")
    # Extract solution
    tour = reconstruct_tour(model)  # Custom function
elif results.solver.termination_condition == TerminationCondition.feasible:
    print("Feasible solution found, but not proven optimal.")
else:
    print("No feasible solution found or solver error.")
```

### Common Pitfalls
- Accessing variable values without checking solver status first, leading to errors.
- Using a loose optimality gap (`MIPGap`) which may stop the solver before proving optimality.
- Not setting a random seed, causing non-deterministic results across runs.

# Workflow 2 (CP-SAT with Position-Based Elimination)

## Modeling stage

### Strategy Overview
Formulate the TSP using Google's OR-Tools CP-SAT solver. Leverage its native support for integer variables and logical constraints to implement a compact MTZ formulation, focusing on efficient search and symmetry breaking.

### Step 1 - Define CP-SAT Variables
- Create Boolean decision variable `x[i,j]` for each ordered pair `(i, j)`, `i != j`.
- Create integer decision variable `u[i]` with domain `[0, num_nodes-1]`.

### Step 2 - Enforce Hamiltonian Cycle Constraints
- For each node `i`, add `sum(x[i,j] for j in N if j != i) == 1` and `sum(x[j,i] for j in N if j != i) == 1`.
- Use the model's `Add` method to post these linear constraints.

### Step 3 - Implement MTZ using CP-SAT Primitives
- For all `i != j`, add the implication: `x[i,j] == 1` -> `u[j] >= u[i] + 1`.
- This is enforced as `model.Add(u[j] >= u[i] + 1).OnlyEnforceIf(x[i,j])`.
- To handle the depot return, exclude the constraint when `j == depot_node`.

### Step 4 - Add Symmetry-Breaking and Objective
- Fix the starting arc, e.g., `model.Add(x[depot_node, first_city] == 1)` to reduce permutations.
- Define the objective: `model.Minimize(sum(cost[i,j] * x[i,j] for i,j in N if i != j))`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes"
  ],
  "parameters": [
    "cost[i,j]: travel cost matrix",
    "depot_node: index of starting node",
    "num_nodes: |N|"
  ],
  "decision_variables": [
    "x[i,j]: CP-SAT Boolean variable, for i,j in N, i != j",
    "u[i]: CP-SAT integer variable with domain [0, num_nodes-1]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i,j in N if i != j)"
  },
  "constraints": [
    "departure[i in N]: sum(x[i,j] for j in N if j != i) == 1",
    "arrival[j in N]: sum(x[i,j] for i in N if i != j) == 1",
    "mtz_implication[i in N, j in N if i != j and j != depot_node]: x[i,j] == 1 -> u[j] >= u[i] + 1",
    "symmetry_break: x[depot_node, first_city] == 1",
    "depot_position: u[depot_node] == 0"
  ]
}
```

### Common Pitfalls
- Incorrectly translating the MTZ inequality into a CP-SAT implication, which must use `OnlyEnforceIf`.
- Adding redundant constraints for the depot return arc, which can make the model infeasible.
- Not setting appropriate domains for integer variables, causing solver errors.

## Solving stage

### Strategy Overview
Solve using OR-Tools CP-SAT, configuring its search parameters for a balance of speed and proof of optimality. Extract the solution by evaluating variable values and reconstructing the tour.

### Step 1 - Configure and Execute Solver
- Create a `CpModel`.
- Add variables and constraints as per the modeling stage.
- Set objective.
- Configure solver parameters: `solver.parameters.max_time_in_seconds`, `solver.parameters.num_search_workers`, `solver.parameters.random_seed`.
- Call `CpSolver().Solve(model, solution_callback)`.

### Step 2 - Interpret Solver Result
- Check the returned status: `cp_model.OPTIMAL`, `cp_model.FEASIBLE`, or `cp_model.INFEASIBLE`.
- If status is not `OPTIMAL` or `FEASIBLE`, report the outcome and terminate.

### Step 3 - Extract Variable Assignments
- For each Boolean variable `x[i,j]`, check `solver.Value(x[i,j]) == 1` to identify selected arcs.
- For each integer variable `u[i]`, retrieve `solver.Value(u[i])` to get node positions.

### Step 4 - Build and Verify the Tour
- Reconstruct the tour by following arcs from the `depot_node`.
- Validate that all nodes are visited exactly once and the positions `u[i]` are consistent with the arc sequence.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# Create variables
x = {}
for i in N:
    for j in N:
        if i != j:
            x[i, j] = model.NewBoolVar(f'arc_{i}_{j}')
u = {i: model.NewIntVar(0, num_nodes - 1, f'pos_{i}') for i in N}

# Add constraints (example: flow conservation)
for i in N:
    model.Add(sum(x[i, j] for j in N if j != i) == 1)
    model.Add(sum(x[j, i] for j in N if j != i) == 1)

# Add MTZ implications
for i in N:
    for j in N:
        if i != j and j != depot_node:
            model.Add(u[j] >= u[i] + 1).OnlyEnforceIf(x[i, j])

# Fix depot position and add symmetry breaking
model.Add(u[depot_node] == 0)
model.Add(x[depot_node, first_city] == 1)  # first_city is a chosen node

# Set objective
model.Minimize(sum(cost[i, j] * x[i, j] for i, j in x.keys()))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = time_limit
solver.parameters.num_search_workers = num_threads
solver.parameters.random_seed = random_seed

status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    print("Optimal solution found.")
elif status == cp_model.FEASIBLE:
    print("Feasible solution found.")
else:
    print("No solution found.")

# Extract solution if feasible
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected_arcs = [(i, j) for (i, j), var in x.items() if solver.Value(var) == 1]
    tour = reconstruct_tour_from_arcs(selected_arcs, depot_node)
```

### Common Pitfalls
- Using `model.Add(u[j] >= u[i] + 1)` without `.OnlyEnforceIf(...)`, which incorrectly applies the constraint globally.
- Not setting `num_search_workers` for parallel search, missing potential speed-ups.
- Forgetting to handle the `depot_node` exclusion in MTZ implications, causing infeasibility.
