---
name: TSP_MTZ_Formulation
description: |
  Model and solve the Traveling Salesman Problem using the Miller-Tucker-Zemlin (MTZ) formulation with position variables for subtour elimination, suitable for small to medium-sized instances.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
This workflow uses the OR-Tools CP-SAT solver, a constraint programming and SAT solver, to implement the MTZ formulation. It is effective for exact solving of TSP instances where the number of nodes is moderate.

### Step 1 - Define Variables
- Create binary decision variables `x[i][j]` for all directed arcs `(i, j)` where `i != j`. This variable indicates if the arc is part of the tour.
- Create integer position variables `u[i]` for each node `i`. The variable represents the node's order in the tour, bounded between `0` and `n-1`.

### Step 2 - Set Node Position Bounds
- Fix the starting node's position to `0` to establish a reference point for the tour ordering.
- For all other nodes, set the lower bound of the position variable to `1` and the upper bound to `n-1`.

### Step 3 - Apply Flow Conservation
- Add constraints ensuring each node has exactly one outgoing arc: `sum(x[i][j] for j in nodes if j != i) == 1` for all `i`.
- Add constraints ensuring each node has exactly one incoming arc: `sum(x[i][j] for i in nodes if i != j) == 1` for all `j`.

### Step 4 - Implement MTZ Subtour Elimination
- For all pairs `(i, j)` where `i != j` and neither is the fixed start node, add the MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`. This enforces a logical ordering to prevent subtours.

### Step 5 - Define Objective
- Formulate the objective as the minimization of the total tour cost: `sum(cost[i][j] * x[i][j] for all i, j where i != j)`.

### Formulation Template
```json
{
  "sets": [
    "nodes"
  ],
  "parameters": [
    {"name": "cost", "description": "Cost matrix where cost[i][j] is the cost to travel from node i to node j."},
    {"name": "start_node", "description": "The index of the node designated as the start of the tour."}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["i", "j"], "description": "1 if arc from node i to j is selected."},
    {"name": "u", "type": "integer", "indices": ["i"], "description": "Position of node i in the tour."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in nodes for j in nodes if i != j)"
  },
  "constraints": [
    {"name": "outgoing_flow", "expression": "sum(x[i][j] for j in nodes if j != i) == 1 for each i in nodes"},
    {"name": "incoming_flow", "expression": "sum(x[i][j] for i in nodes if i != j) == 1 for each j in nodes"},
    {"name": "start_position", "expression": "u[start_node] == 0"},
    {"name": "position_bounds", "expression": "1 <= u[i] <= n-1 for each i in nodes, i != start_node"},
    {"name": "mtz_subtour", "expression": "u[i] - u[j] + n * x[i][j] <= n - 1 for each i,j in nodes, i != j, i != start_node, j != start_node"}
  ]
}
```

### Common Pitfalls
- Forgetting to exclude the start node from the MTZ constraints, which can lead to an infeasible model.
- Using an incorrect big-M value (`n`) in the MTZ constraint, which fails to properly eliminate subtours.
- Not explicitly preventing self-loops (`x[i][i]`), though this is often handled implicitly by the flow constraints.

## Solving stage

### Strategy Overview
Solve the formulated model using the OR-Tools CP-SAT solver. Configure it for a balance of speed and optimality, then extract and validate the resulting tour.

### Step 1 - Configure Solver
- Instantiate the CP-SAT solver.
- Set a time limit (`max_time_in_seconds`) appropriate for the problem size.
- Enable multiple search workers (`num_search_workers`) to utilize parallel processing.
- Set a `random_seed` for reproducibility and a `relative_gap_limit` of `0.0` to search for the optimal solution.

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve` method.
- Check the solver's status (`OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`). Proceed only if a feasible solution is found.

### Step 3 - Extract Solution
- Reconstruct the tour by starting at the designated start node.
- Iteratively find the next node `j` where the solution value for `x[current][j]` is `1`.
- Append each node to the tour list until all nodes are visited and the cycle returns to the start.

### Step 4 - Validate Solution
- Verify that the extracted tour visits each node exactly once.
- Calculate the total cost of the extracted tour and compare it to the solver's reported objective value to ensure consistency.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build model using steps from Modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract tour
    tour = [start_node]
    current = start_node
    for _ in range(len(nodes) - 1):
        for j in nodes:
            if j != current and solver.Value(x[current, j]) == 1:
                tour.append(j)
                current = j
                break
    tour.append(start_node)  # Close the loop
    print(f"Objective: {solver.ObjectiveValue()}")
    print(f"Tour: {tour}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking the solver status before attempting to extract variable values, which causes runtime errors.
- The tour extraction logic may enter an infinite loop if the solution does not form a proper Hamiltonian cycle; always limit the loop to `n` iterations.
- Assuming optimality without verifying the solver status is `OPTIMAL`; a `FEASIBLE` status only guarantees a solution, not optimality.

# Workflow 2 (MIP Solver via Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to formulate the MTZ-based TSP as a Mixed-Integer Program (MIP). It is then solved using an external MIP solver like Gurobi or SCIP, suitable for leveraging advanced commercial or open-source solvers.

### Step 1 - Define Model and Sets
- Create a Pyomo `ConcreteModel`.
- Define a `Set` for the nodes.

### Step 2 - Create Parameters and Variables
- Define a `Param` for the two-dimensional cost matrix.
- Define binary variables `x[i, j]` for all `i != j` using `Var(within=Binary)`.
- Define integer position variables `u[i]` with bounds `(0, n-1)` using `Var(within=NonNegativeIntegers, bounds=(0, n-1))`.

### Step 3 - Set Start Position and Bounds
- Fix the start node's position to `0` using a `Constraint`.
- For other nodes, add constraints to enforce `u[i] >= 1`.

### Step 4 - Enforce Flow Conservation
- Add constraints for outgoing flow: `sum(x[i, j] for j in nodes if j != i) == 1`.
- Add constraints for incoming flow: `sum(x[i, j] for i in nodes if i != j) == 1`.

### Step 5 - Apply MTZ Constraints
- For all `i != j` where `j` is not the start node, add the constraint: `u[i] - u[j] + n * x[i, j] <= n - 1`.

### Step 6 - Define Objective
- Set the model's objective to minimize `sum(cost[i, j] * x[i, j] for i in nodes for j in nodes if i != j)`.

### Formulation Template
```json
{
  "sets": [
    "nodes"
  ],
  "parameters": [
    {"name": "cost", "description": "Cost matrix where cost[i, j] is the cost to travel from node i to node j."}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["i", "j"], "description": "1 if arc from node i to j is selected."},
    {"name": "u", "type": "integer", "indices": ["i"], "description": "Position of node i in the tour."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in nodes for j in nodes if i != j)"
  },
  "constraints": [
    {"name": "out_flow", "expression": "sum(x[i, j] for j in nodes if j != i) == 1 for each i"},
    {"name": "in_flow", "expression": "sum(x[i, j] for i in nodes if i != j) == 1 for each j"},
    {"name": "fix_start", "expression": "u[start_node] == 0"},
    {"name": "lower_bound_pos", "expression": "u[i] >= 1 for each i != start_node"},
    {"name": "mtz", "expression": "u[i] - u[j] + n * x[i, j] <= n - 1 for each i,j in nodes, i != j, j != start_node"}
  ]
}
```

### Common Pitfalls
- Applying the MTZ constraint for `j == start_node`, which can incorrectly restrict the model.
- Not defining the cost parameter with correct indexing, leading to key errors during model construction.
- Omitting the lower bound constraint (`u[i] >= 1`) for non-start nodes, which allows them to take position 0 and can create subtours.

## Solving stage

### Strategy Overview
Solve the Pyomo model by calling an external MIP solver (e.g., Gurobi, SCIP). Configure solver options for performance, check termination status, and extract the solution tour.

### Step 1 - Select and Configure Solver
- Instantiate a solver object (e.g., `SolverFactory('gurobi')`).
- Set solver options: `TimeLimit`, `Threads` for parallelism, `MIPGap` (set to `0.0` for optimality), and `Seed` for reproducibility.

### Step 2 - Solve and Inspect Results
- Execute the `solve` command on the model.
- Check the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Reconstruct Tour
- Access the variable values using `model.x[i, j].value`.
- Starting from the start node, follow arcs where `x[i, j].value > 0.5` to reconstruct the complete tour.

### Step 4 - Validate and Report
- Verify the tour length equals the number of nodes.
- Calculate the total cost from the extracted tour and compare it to the model's objective value.
- Print both the tour and the objective value.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.nodes = pyo.Set(initialize=nodes)
model.cost = pyo.Param(model.nodes, model.nodes, initialize=cost_dict)
model.x = pyo.Var(model.nodes, model.nodes, within=pyo.Binary)
model.u = pyo.Var(model.nodes, within=pyo.NonNegativeIntegers, bounds=(0, n-1))
# ... (add constraints and objective as per Modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'scip'
solver.options['TimeLimit'] = 30
solver.options['Threads'] = 4
solver.options['MIPGap'] = -1.0  # Use -1.0 for optimality (gap=0) in Gurobi
solver.options['Seed'] = 42

results = solver.solve(model)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Extract tour
    tour = [start_node]
    current = start_node
    visited = set(tour)
    while len(visited) < len(model.nodes):
        for j in model.nodes:
            if j != current and pyo.value(model.x[current, j]) > 0.5:
                tour.append(j)
                current = j
                visited.add(j)
                break
    tour.append(start_node)
    print(f"Objective: {pyo.value(model.obj)}")
    print(f"Tour: {tour}")
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not converting Pyomo variable values to scalars using `pyo.value()` before numerical comparison.
- The tour extraction loop may miss nodes if the solution contains subtours (though MTZ should prevent this); always check the length of the extracted tour.
- Misinterpreting solver status; `SolverStatus.ok` only indicates the solver ran successfully, not that a solution was found. Always check `termination_condition`.
