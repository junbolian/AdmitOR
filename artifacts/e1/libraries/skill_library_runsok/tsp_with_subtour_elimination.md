---
name: TSP with Subtour Elimination
description: |
  Model and solve the Traveling Salesperson Problem using compact formulations that eliminate subtours, with workflows for both CP-SAT and MIP solvers.

---

# Workflow 1 (CP-SAT with MTZ Formulation)

## Modeling stage

### Strategy Overview
This workflow uses the Miller-Tucker-Zemlin (MTZ) formulation within Google OR-Tools' CP-SAT solver. It is a compact linear formulation suitable for small to medium-sized instances, leveraging the solver's efficient handling of integer variables and logical constraints.

### Step 1 - Define Variables
- Create binary decision variables `x[i][j]` for all ordered pairs of distinct nodes `(i, j)` to indicate if an arc is part of the tour.
- Create integer decision variables `u[i]` for each node `i`, bounded between `0` and `n-1`, to represent the node's position in the tour sequence.

### Step 2 - Enforce Tour Structure
- Add constraints `sum(x[i][j] for j != i) == 1` and `sum(x[j][i] for j != i) == 1` for each node `i` to ensure exactly one incoming and one outgoing arc (degree constraints).
- Add constraint `u[0] == 0` to fix the starting node's position, anchoring the tour order.

### Step 3 - Eliminate Subtours with MTZ
- For all pairs `(i, j)` where `i != j` and `j != 0`, add the MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`. This prevents cycles that do not include the start node.
- Ensure the constraint is applied correctly to avoid over-constraining the model for arcs returning to the start.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (0..n-1)"
  ],
  "parameters": [
    "cost[i][j]: cost of traveling from node i to node j, for all i, j in N, i != j"
  ],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc from i to j is selected, for all i, j in N, i != j",
    "u[i]: integer, position of node i in the tour, for all i in N, domain {0..n-1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in N} sum_{j in N, j != i} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "degree_out: for all i in N, sum_{j in N, j != i} x[i][j] == 1",
    "degree_in: for all i in N, sum_{j in N, j != i} x[j][i] == 1",
    "start_position: u[0] == 0",
    "mtz: for all i in N, for all j in N \\ {0}, i != j, u[i] - u[j] + n * x[i][j] <= n - 1"
  ]
}
```

### Common Pitfalls
- Applying the MTZ constraint for `j = 0` (the start node), which can incorrectly forbid the tour's return arc and make the model infeasible.
- Adding extra, unnecessary constraints like `u[j] == u[i] + 1` for selected arcs, which over-constrains the model.
- Forgetting to exclude self-loop variables (`x[i][i]`) from the variable creation and objective.

## Solving stage

### Strategy Overview
Configure and execute the CP-SAT solver to find an optimal or feasible tour. The focus is on setting appropriate limits for exact or good-quality solutions and implementing robust solution extraction and verification.

### Step 1 - Configure Solver Parameters
- Set a time limit (`max_time_in_seconds`) appropriate for the instance size to bound runtime.
- Enable parallel search by setting `num_search_workers` to the number of available cores or `-1` for automatic detection.
- Set `random_seed` for reproducibility of the search process.
- For an exact solution, set `relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the returned status (`cp_model.OPTIMAL`, `cp_model.FEASIBLE`, etc.) before attempting to extract values. Handle `INFEASIBLE` or `UNKNOWN` statuses with appropriate error messages.

### Step 3 - Extract and Verify Solution
- Reconstruct the tour sequence by starting at node `0` and iteratively finding the unique `j` where `solver.Value(x[current][j]) == 1`.
- Calculate the total cost from the selected arcs and compare it to the solver's reported objective value to verify consistency.
- Optionally, validate that the tour visits all nodes exactly once and that the position variables `u[i]` are consistent with the tour order.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (create variables and constraints as per Modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract tour
    tour = [0]
    current = 0
    while len(tour) < num_nodes:
        for j in range(num_nodes):
            if j != current and solver.Value(x[current][j]) == 1:
                tour.append(j)
                current = j
                break
    # Verify and use solution
    calculated_cost = sum(cost[tour[i]][tour[i+1]] for i in range(num_nodes-1))
    calculated_cost += cost[tour[-1]][tour[0]]  # Add return to start if required
    print(f"Tour: {tour}, Solver Objective: {solver.ObjectiveValue()}, Calculated: {calculated_cost}")
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Not checking solver status before value extraction, leading to runtime errors.
- Incorrectly reconstructing the tour (e.g., infinite loops) due to not handling the return to start or misreading variable values.
- Setting an invalid `relative_gap_limit` (e.g., a negative value) or conflicting parameters.

# Workflow 2 (MIP Solver with MTZ Formulation)

## Modeling stage

### Strategy Overview
This workflow implements the MTZ formulation for a generic Mixed-Integer Programming (MIP) solver (e.g., SCIP, CBC). It uses a linearized version of the MTZ constraint and is suitable for solvers accessed via modeling interfaces like Pyomo or OR-Tools' linear solver wrapper.

### Step 1 - Define Variables
- Create binary decision variables `x[i,j]` for all ordered pairs of distinct nodes.
- Create continuous or integer decision variables `u[i]` for each node, with bounds `0 <= u[i] <= n-1`.

### Step 2 - Enforce Degree and Flow Constraints
- Add constraints ensuring each node has exactly one incoming and one outgoing arc: `sum(x[i,j] for j != i) == 1` and `sum(x[j,i] for j != i) == 1`.
- Explicitly fix the start node's position: `u[0] == 0`.

### Step 3 - Apply Linearized MTZ Constraints
- For all `i != j`, add the constraint: `u[j] >= u[i] + 1 - n * (1 - x[i,j])`. This linearizes the logical condition that if arc `(i,j)` is selected, then `u[j]` must be at least `u[i] + 1`.
- Ensure the "big-M" value (`n`, the number of nodes) is sufficiently large to not cut off valid solutions when `x[i,j] = 0`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (0..n-1)"
  ],
  "parameters": [
    "cost[i][j]: cost of traveling from node i to node j, for all i, j in N, i != j"
  ],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc from i to j is selected, for all i, j in N, i != j",
    "u[i]: continuous or integer, position of node i, for all i in N, domain [0, n-1]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in N} sum_{j in N, j != i} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "out_flow: for all i in N, sum_{j in N, j != i} x[i][j] == 1",
    "in_flow: for all i in N, sum_{j in N, j != i} x[j][i] == 1",
    "start_pos: u[0] == 0",
    "mtz_linear: for all i in N, for all j in N, i != j, u[j] >= u[i] + 1 - n * (1 - x[i,j])"
  ]
}
```

### Common Pitfalls
- Using an incorrectly small "big-M" value in the linearized MTZ constraint, which can make feasible tours infeasible.
- Defining `u[i]` as continuous without enforcing integrality, which may lead to fractional solutions that satisfy the MTZ constraints but do not represent a valid permutation (though the objective with binary `x` often forces integrality).
- Neglecting to set an upper bound on `u[i]` variables, which can lead to unbounded variable issues.

## Solving stage

### Strategy Overview
Configure and run a MIP solver via a standard interface (e.g., Pyomo `SolverFactory`, OR-Tools `pywraplp`). Focus on setting optimality tolerances, resource limits, and extracting the solution in a solver-agnostic way.

### Step 1 - Instantiate and Configure Solver
- Select an appropriate MIP solver (e.g., `"SCIP"`, `"CBC"`).
- Set a time limit (`TimeLimit`) to prevent excessive runtime.
- Set the optimality gap tolerance (`MIPGap`) to `0.0` for an exact optimal solution or a small positive value for early termination.
- Configure the number of threads (`Threads`) for parallel processing.
- Set a random seed (`Seed`) for reproducible results.

### Step 2 - Solve and Inspect Termination Condition
- Call the solver's `solve()` method.
- Check both the high-level solver status (e.g., `ok`, `warning`) and the detailed termination condition (e.g., `optimal`, `feasible`, `maxTimeLimit`). Proceed only if a feasible solution is found.

### Step 3 - Extract and Reconstruct Solution
- Retrieve the values of the `x[i,j]` variables from the solver result object.
- Reconstruct the tour by starting at the designated start node and following the selected arcs.
- Validate the solution by checking degree constraints and recalculating the objective value from the cost matrix.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.N = pyo.RangeSet(0, num_nodes-1)
# ... (create variables and constraints as per Modeling stage using Pyomo)

# solve with status / termination checks
solver = pyo.SolverFactory('scip')
solver.options['limits/time'] = 30
solver.options['limits/gap'] = 0.0
solver.options['parallel'] = 4
solver.options['randomseed'] = 42

results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:
    # Extract variable values
    x_values = {(i,j): pyo.value(model.x[i,j]) for i in model.N for j in model.N if i != j}
    # Reconstruct tour
    tour = [0]
    current = 0
    while len(tour) < num_nodes:
        for j in model.N:
            if j != current and x_values[current, j] > 0.5: # Check binary variable
                tour.append(j)
                current = j
                break
    print(f"Optimal tour found: {tour}")
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    print("Feasible solution found, but not proven optimal.")
else:
    print(f"Solver failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing solver status (`ok`) with solution quality (`optimal`). A status of `ok` only means the solver ran without error, not that an optimal solution was found.
- Incorrectly accessing variable values (e.g., using `.value` vs `.solution_value()` depending on the interface) leading to extraction errors.
- Setting `MIPGap` to `-1` or an invalid negative value, which may be interpreted differently by different solvers. Use `0.0` for exact optimality.
