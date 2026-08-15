---
name: TSP_MTZ_Formulation
description: |
  Model and solve traveling salesman problems using Miller-Tucker-Zemlin subtour elimination with binary routing and positional ordering variables.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
This workflow models the TSP using the MTZ formulation and solves it with Google OR-Tools' CP-SAT solver, suitable for exact solutions on moderate-sized instances.

### Step 1 - Define Variables
- Create binary decision variables `x[i][j]` for each directed arc between distinct nodes `i` and `j`.
- Create integer variables `u[i]` representing the position of node `i` in the tour, bounded between `0` and `n-1`.

### Step 2 - Impose Flow Conservation
- For each node `i`, add a constraint that the sum of outgoing arcs `x[i][j]` equals `1`.
- For each node `j`, add a constraint that the sum of incoming arcs `x[i][j]` equals `1`.

### Step 3 - Apply MTZ Subtour Elimination
- For all pairs `(i, j)` where neither is the designated start node, add the constraint `u[i] - u[j] + n * x[i][j] <= n - 1`.
- Fix the position of the start node, e.g., `u[start] = 0`.

### Step 4 - Formulate Objective
- Define the objective as minimizing the sum of `cost[i][j] * x[i][j]` over all arcs.

### Formulation Template
```json
{
  "sets": [
    "NODES"
  ],
  "parameters": [
    {"name": "cost", "dimensions": ["NODES", "NODES"], "description": "Travel cost matrix"},
    {"name": "start_node", "type": "int", "description": "Index of the fixed start node"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "dimensions": ["NODES", "NODES"], "description": "1 if arc (i,j) is used"},
    {"name": "u", "type": "int", "dimensions": ["NODES"], "bounds": "[0, n-1]", "description": "Position of node in tour"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in NODES for j in NODES if i != j)"
  },
  "constraints": [
    {"name": "outgoing_flow", "expression": "sum(x[i][j] for j in NODES if j != i) == 1 for each i in NODES"},
    {"name": "incoming_flow", "expression": "sum(x[i][j] for i in NODES if i != j) == 1 for each j in NODES"},
    {"name": "mtz", "expression": "u[i] - u[j] + n * x[i][j] <= n - 1 for each i,j in NODES where i != j and i != start_node and j != start_node"},
    {"name": "fix_start", "expression": "u[start_node] == 0"}
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops (`i != j`) in the variable creation and objective summation.
- Applying the MTZ constraint to pairs involving the start node, which is unnecessary and weakens the formulation.
- Not providing an upper bound for the positional variables `u[i]`, which can lead to solver errors.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver with time limits and parallel search, solve the model, and extract the tour by following active arcs from the start node.

### Step 1 - Configure Solver
- Instantiate `CpSolver()` and set parameters like `max_time_in_seconds`, `num_search_workers`, and `random_seed`.
- Set `relative_gap_limit` to `0.0` to enforce a search for the optimal solution.

### Step 2 - Solve and Check Status
- Call the solver's `Solve` method on the model.
- Check the returned status for `OPTIMAL` or `FEASIBLE` before proceeding to solution extraction.

### Step 3 - Extract Solution
- Reconstruct the tour: start at `start_node`, find `j` where `solver.Value(x[current][j]) == 1`, and iterate until all nodes are visited.
- Collect the objective value using `solver.ObjectiveValue()`.

### Step 4 - Validate and Output
- Optionally, verify the solution by recalculating the tour cost from the extracted route.
- Output the tour sequence, total cost, and solver status in a structured format.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract tour
    tour = [start_node]
    current = start_node
    for _ in range(len(NODES) - 1):
        for j in NODES:
            if j != current and solver.Value(x[current][j]) == 1:
                tour.append(j)
                current = j
                break
    total_cost = solver.ObjectiveValue()
    # Output results
else:
    # Handle failure: output status and error information
```

### Common Pitfalls
- Not checking solver status before attempting to extract variable values, which causes runtime errors.
- Assuming the solver found an optimal solution without verifying the status is `OPTIMAL`.
- Using an infinite loop for tour reconstruction without a break condition for when the next node is not found.

# Workflow 2 (MIP Solver via Pyomo)

## Modeling stage

### Strategy Overview
This workflow models the TSP using the MTZ formulation within the Pyomo modeling framework and solves it with an external MIP solver like Gurobi or CBC, offering flexibility and advanced solver features.

### Step 1 - Declare Model Components
- Instantiate a Pyomo `ConcreteModel`.
- Define the set of nodes and the cost parameter as a `Param` indexed by node pairs.
- Declare binary `Var` for `x` and integer `Var` for `u` with appropriate bounds.

### Step 2 - Enforce Degree Constraints
- Add constraints using `ConstraintList` or rule functions to ensure exactly one incoming and one outgoing arc per node.

### Step 3 - Implement MTZ Constraints
- Add the MTZ constraints `u[i] - u[j] + n * x[i,j] <= n - 1` for relevant `i, j` pairs, efficiently skipping cases where `i` or `j` is the start node using `pyo.Constraint.Skip`.

### Step 4 - Define Objective
- Create an objective expression summing `cost[i,j] * x[i,j]` and set the model's objective to minimize it.

### Formulation Template
```json
{
  "sets": [
    "NODES"
  ],
  "parameters": [
    {"name": "cost", "dimensions": ["NODES", "NODES"], "description": "Travel cost matrix"},
    {"name": "start_node", "type": "int", "description": "Index of the fixed start node"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "dimensions": ["NODES", "NODES"], "description": "1 if arc (i,j) is used"},
    {"name": "u", "type": "int", "dimensions": ["NODES"], "bounds": "[0, n-1]", "description": "Position of node in tour"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in NODES for j in NODES if i != j)"
  },
  "constraints": [
    {"name": "out_degree", "expression": "sum(x[i,j] for j in NODES if j != i) == 1 for each i in NODES"},
    {"name": "in_degree", "expression": "sum(x[i,j] for i in NODES if i != j) == 1 for each j in NODES"},
    {"name": "mtz", "expression": "u[i] - u[j] + n * x[i,j] <= n - 1 for each i,j in NODES where i != j and i != start_node and j != start_node"},
    {"name": "start_pos", "expression": "u[start_node] == 0"}
  ]
}
```

### Common Pitfalls
- Incorrectly setting the MIP gap to `-1.0` (which means 'default') when intending to seek optimality (`0.0`).
- Creating dense MTZ constraints for all `i,j` pairs, including those with the start node, which adds unnecessary constraints.
- Not defining proper bounds for integer variables `u[i]`, leading to unbounded model errors.

## Solving stage

### Strategy Overview
Use Pyomo's solver interface to call an external MIP solver, configure it for optimality and performance, and robustly handle solution extraction and validation.

### Step 1 - Configure and Execute Solver
- Instantiate a solver object (e.g., `SolverFactory('gurobi')`).
- Set solver options: `MIPGap=0.0`, `TimeLimit`, `Threads`, and `Seed` for reproducibility.
- Call `solve(model)` and capture the results object.

### Step 2 - Check Solution Status
- Check both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`).
- Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value via `pyo.value(model.obj)`.
- Extract the tour by iterating over arcs where `pyo.value(model.x[i,j]) > 0.5`.
- For small instances, optionally validate optimality by enumerating all possible tours.

### Step 4 - Output Results
- Output the tour sequence, total cost, and positional variables.
- If the solver failed, output a structured JSON with status, reason, and termination details for debugging.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.NODES = pyo.Set(initialize=NODES)
model.cost = pyo.Param(model.NODES, model.NODES, initialize=cost_dict)
# ... (build variables and constraints as per modeling stage)
model.obj = pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for i in model.NODES for j in model.NODES if i != j), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 30
solver.options['Threads'] = 4
solver.options['Seed'] = 42
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    # Extract solution
    tour = [start_node]
    current = start_node
    for _ in range(len(model.NODES) - 1):
        for j in model.NODES:
            if j != current and pyo.value(model.x[current, j]) > 0.5:
                tour.append(j)
                current = j
                break
    total_cost = pyo.value(model.obj)
    # Output results
else:
    # Handle failure: output structured error information
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`); both must be checked.
- Using a tolerance like `0.5` for checking binary variable values without considering solver integrality tolerances.
- Not handling the case where the solver returns a feasible but not optimal solution, potentially misleading the user about solution quality.
