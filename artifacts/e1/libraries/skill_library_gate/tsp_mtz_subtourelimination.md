---
name: TSP_MTZ_SubtourElimination
description: |
  Model and solve traveling salesman problems using binary routing and integer position variables with Miller-Tucker-Zemlin subtour elimination constraints.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
This workflow uses a CP-SAT solver (e.g., OR-Tools CP-SAT) to model the TSP. It leverages native Boolean and integer variables, linear constraints, and an AllDifferent constraint on positions to enforce a single tour.

### Step 1 - Define Variables
- Create a binary decision variable `x[i][j]` for each directed arc from node `i` to node `j` (where `i != j`). This variable indicates if the arc is part of the tour.
- Create an integer decision variable `u[i]` for each node `i`, representing its visit order/position in the tour. Set its domain from `0` to `n-1` (where `n` is the number of nodes).

### Step 2 - Enforce Basic Routing
- Add constraints so each node has exactly one outgoing arc: `sum(x[i][j] for all j != i) == 1` for each node `i`.
- Add constraints so each node has exactly one incoming arc: `sum(x[i][j] for all i != j) == 1` for each node `j`.
- Explicitly forbid self-loops by fixing `x[i][i] = 0` for all `i`.

### Step 3 - Eliminate Subtours with MTZ
- For all ordered pairs `(i, j)` where `i != j` and `j` is not the designated start node (e.g., node `0`), add the MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.
- To strengthen the formulation and prevent duplicate positions, add an `AllDifferent` constraint on all `u[i]` variables.
- Fix the position of the start node: `u[start_node] == 0`.

### Step 4 - Formulate Objective
- Define the objective to minimize the total tour cost: `sum(cost[i][j] * x[i][j] for all i != j)`.

### Formulation Template
```json
{
  "sets": [
    "N = set of all nodes (cities)",
    "A = set of all directed arcs (i, j) where i, j in N and i != j"
  ],
  "parameters": [
    "cost[i][j]: travel cost from node i to node j, for (i,j) in A"
  ],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc (i,j) is used in the tour, for (i,j) in A",
    "u[i]: integer, visit order/position of node i, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j] * x[i][j] for (i,j) in A )"
  },
  "constraints": [
    "outgoing_degree: sum( x[i][j] for j in N, j != i ) == 1, for each i in N",
    "incoming_degree: sum( x[i][j] for i in N, i != j ) == 1, for each j in N",
    "no_self_loop: x[i][i] == 0, for each i in N",
    "mtz: u[i] - u[j] + |N| * x[i][j] <= |N| - 1, for each (i,j) in A where j != start_node",
    "all_different: AllDifferent( [u[i] for i in N] )",
    "fix_start: u[start_node] == 0"
  ]
}
```

### Common Pitfalls
- Forgetting to add the `AllDifferent` constraint, which can lead to subtours not eliminated by the basic MTZ constraints.
- Applying the MTZ constraint when `j` is the start node, which can create infeasibility with the fixed `u[start_node] = 0`.
- Not setting a time limit or search parameters, which can cause the solver to run indefinitely on larger instances.

## Solving stage

### Strategy Overview
Solve the CP-SAT model by configuring the solver for a balance of speed and proof of optimality. Extract the solution by tracing the active arcs and verify all constraints are satisfied.

### Step 1 - Configure Solver
- Instantiate the CP-SAT solver.
- Set a time limit (`max_time_in_seconds`).
- Configure parallel search (`num_search_workers`).
- Set a random seed for reproducibility.
- Optionally, set a relative optimality gap limit to `0.0` to enforce a search for the proven optimal solution.

### Step 2 - Solve and Check Status
- Call the solver's `Solve` method.
- Check the status: it must be `OPTIMAL` or `FEASIBLE` before proceeding.
- If the status is not `FEASIBLE` or `OPTIMAL`, handle the infeasibility or unknown result appropriately (e.g., log solver response, return empty result).

### Step 3 - Extract and Reconstruct Solution
- For all arcs `(i, j)`, if the solver's value for `x[i][j]` is `1`, record it as an active arc.
- Starting from the designated start node, follow the chain of active outgoing arcs to reconstruct the complete tour sequence.
- Extract the position values `u[i]` for all nodes.

### Step 4 - Verify Solution
- Programmatically verify that degree constraints, MTZ constraints, and the `AllDifferent` constraint hold for the extracted solution.
- Recalculate the objective value from the active arcs and compare it to the solver's reported objective value.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... (build variables and constraints as per Modeling Stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set solver parameters
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    tour = []
    current_node = start_node
    while True:
        tour.append(current_node)
        # Find the next node via the active arc
        for j in nodes:
            if j != current_node and solver.Value(x[current_node][j]) == 1:
                next_node = j
                break
        current_node = next_node
        if current_node == start_node:
            break
    # ... (extract other variable values, calculate cost)
else:
    # Handle non-feasible status
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Not checking solver status before extracting variable values, which causes runtime errors.
- Incorrectly reconstructing the tour by not handling the loop back to the start node correctly.
- Assuming the solver found the optimal solution without checking for the `OPTIMAL` status.

# Workflow 2 (MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses a traditional Mixed-Integer Programming (MIP) solver (e.g., Gurobi, SCIP via Pyomo) to model the TSP. It follows the same MTZ formulation but uses a modeling framework to abstract constraint creation.

### Step 1 - Define Sets and Parameters
- Define the set of nodes `N` and the set of arcs `A`.
- Define a cost parameter `cost[i,j]` for each arc `(i,j)` in `A`.

### Step 2 - Create Decision Variables
- Create binary variables `model.x[i,j]` for each `(i,j)` in `A`.
- Create integer variables `model.u[i]` for each `i` in `N` with bounds `(0, n-1)`.

### Step 3 - Add Degree and Subtour Elimination Constraints
- Add outgoing and incoming degree constraints using summations over the defined sets.
- Add the MTZ constraints: `model.u[i] - model.u[j] + n * model.x[i,j] <= n - 1` for all `(i,j)` in `A` where `j != start_node`.
- Fix the start node's position: `model.u[start_node] == 0`.

### Step 4 - Set Objective
- Define the objective to minimize the sum of `cost[i,j] * model.x[i,j]` over all arcs.

### Formulation Template
```json
{
  "sets": [
    "N = set of all nodes",
    "A = set of directed arcs (i,j) for i,j in N, i != j"
  ],
  "parameters": [
    "cost[i,j] for (i,j) in A"
  ],
  "decision_variables": [
    "x[i,j]: binary, for (i,j) in A",
    "u[i]: integer, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i,j] * x[i,j] for (i,j) in A )"
  },
  "constraints": [
    "out_deg: sum( x[i,j] for j in N if j != i ) == 1, for i in N",
    "in_deg: sum( x[i,j] for i in N if i != j ) == 1, for j in N",
    "mtz: u[i] - u[j] + |N| * x[i,j] <= |N| - 1, for (i,j) in A where j != start_node",
    "start_pos: u[start_node] == 0"
  ]
}
```

### Common Pitfalls
- Using `MIPGap=-1.0` (seeking optimality) instead of `MIPGap=0.0` (proven optimality) in some solvers, which can lead to early termination.
- Not explicitly returning both the model and the data structures from the model-building function, causing scope issues in the solving function.
- Forgetting to set the `Threads` parameter for parallel solving, underutilizing available compute resources.

## Solving stage

### Strategy Overview
Solve the MIP model by setting appropriate solver parameters for proof of optimality within a time limit. Extract and validate the solution using the modeling framework's value extraction methods.

### Step 1 - Instantiate Solver and Set Parameters
- Select a MIP solver (e.g., `'gurobi'`, `'scip'`).
- Set a time limit (`TimeLimit`).
- Set the optimality gap tolerance to `0.0` for a proven optimal solution.
- Set the number of threads for parallel search (`Threads`).
- Set a random seed for reproducibility if supported.

### Step 2 - Solve and Check Termination Condition
- Call the solver's `solve` method on the model.
- Check the solver status (`SolverStatus`) and termination condition (`TerminationCondition`). Proceed only if the status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Extract Solution Values
- For each binary variable `model.x[i,j]`, check if its value is greater than a tolerance (e.g., `0.5`) to determine if the arc is active.
- Extract the integer values for `model.u[i]`.
- Reconstruct the tour by following active arcs from the start node.

### Step 4 - Validate and Report
- Verify that all constraints are satisfied by the extracted values.
- Calculate the total cost from active arcs and compare it to the solver's objective value.
- For small instances, optionally enumerate all possible tours to cross-verify optimality.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(initialize=arcs, dimen=2)
model.cost = pyo.Param(model.A, initialize=cost_dict)
model.x = pyo.Var(model.A, within=pyo.Binary)
model.u = pyo.Var(model.N, within=pyo.NonNegativeIntegers, bounds=(0, n-1))
# ... (add constraints and objective as per Modeling Stage)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    # Extract solution
    tour = [start_node]
    current = start_node
    while True:
        for j in model.N:
            if j != current and pyo.value(model.x[current, j]) > 0.5:
                next_node = j
                break
        if next_node == start_node:
            break
        tour.append(next_node)
        current = next_node
    # ... (extract other variable values)
else:
    # Handle non-optimal/infeasible result
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not using `pyo.value()` to extract variable values, leading to incorrect solution interpretation.
- Failing to check both `SolverStatus` and `TerminationCondition`, which can mask solver failures.
- Setting an infeasibly small time limit for the problem size, causing the solver to return no solution.
