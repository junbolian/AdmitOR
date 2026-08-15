---
name: TSP with Subtour Elimination
description: |
  Model and solve routing problems with binary route selection, node position variables for subtour elimination, and a cost minimization objective using either MIP or CP-SAT solvers.
---

# Workflow 1 (MIP with MTZ Formulation)

## Modeling stage

### Strategy Overview
Formulate the routing problem as a Mixed-Integer Program (MIP) using binary flow variables and integer position variables. The Miller-Tucker-Zemlin (MTZ) constraints eliminate subtours, while flow conservation ensures a single tour.

### Step 1 - Define Core Sets and Parameters
- Define a set of nodes (e.g., `NODES`).
- Define a cost parameter `cost[i][j]` for traveling from node i to node j.
- Identify a fixed start node (e.g., `start_node`).

### Step 2 - Create Decision Variables
- Create binary variables `x[i][j]` for all i≠j, where 1 indicates the route from i to j is selected.
- Create integer variables `u[i]` representing the position of node i in the tour.

### Step 3 - Formulate Flow Conservation
- For each node i, add a constraint: sum of all outgoing `x[i][j]` equals 1.
- For each node i, add a constraint: sum of all incoming `x[j][i]` equals 1.
- Add constraints `x[i][i] = 0` to prevent self-loops.

### Step 4 - Implement Subtour Elimination via MTZ
- Fix the start node's position: `u[start_node] = 0`.
- For all other nodes i, set bounds: `1 <= u[i] <= |NODES| - 1`.
- For all i, j (i ≠ j, and neither is the start node), add the MTZ constraint: `u[i] - u[j] + |NODES| * x[i][j] <= |NODES| - 1`.

### Step 5 - Define the Objective
- Minimize the total cost: `sum( cost[i][j] * x[i][j] for all i≠j )`.

### Formulation Template
```json
{
  "sets": ["NODES"],
  "parameters": [
    {"name": "cost", "index": ["NODES", "NODES"], "type": "float"},
    {"name": "start_node", "type": "int"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["NODES", "NODES"], "type": "binary"},
    {"name": "u", "index": ["NODES"], "type": "integer", "bounds": {"min": 0, "max": "len(NODES)-1"}}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j] * x[i][j] for i in NODES for j in NODES if i != j )"
  },
  "constraints": [
    {"name": "outgoing_flow", "expression": "sum( x[i][j] for j in NODES if j != i ) == 1 for i in NODES"},
    {"name": "incoming_flow", "expression": "sum( x[j][i] for j in NODES if j != i ) == 1 for i in NODES"},
    {"name": "no_self_loop", "expression": "x[i][i] == 0 for i in NODES"},
    {"name": "fix_start_position", "expression": "u[start_node] == 0"},
    {"name": "mtz_subtour", "expression": "u[i] - u[j] + len(NODES) * x[i][j] <= len(NODES) - 1 for i in NODES for j in NODES if i != j and i != start_node and j != start_node"}
  ]
}
```

### Common Pitfalls
- Using an overly large "Big-M" value in MTZ constraints, which weakens the formulation. Use the number of nodes (`n`) as the coefficient.
- Forgetting to exclude the start node from the MTZ constraints, which can cause infeasibility.
- Not setting proper bounds on the position variables `u[i]` for non-start nodes.

## Solving stage

### Strategy Overview
Solve the MIP model using a traditional branch-and-cut solver (e.g., SCIP, CBC, Gurobi) via a modeling library interface. Focus on configuring solver parameters for performance and reliably extracting the solution.

### Step 1 - Instantiate Solver and Model
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("SCIP")` or `SolverFactory("gurobi")`).
- Use the modeling library (e.g., OR-Tools linear solver wrapper, Pyomo) to build the model from the formulation.

### Step 2 - Configure Solver Parameters
- Set a time limit (`solver.SetTimeLimit(ms)` or `opt.options['TimeLimit'] = t`).
- Set the number of threads for parallel processing.
- Set a MIP gap tolerance for early termination if applicable.
- Set a random seed for reproducibility.

### Step 3 - Solve and Check Status
- Execute the solve command.
- Check the solver status. A successful status is `OPTIMAL` or `FEASIBLE`.
- If the status is not successful, diagnose by solving a relaxed model or checking constraint logic.

### Step 4 - Extract and Reconstruct Solution
- Retrieve the objective function value.
- Extract the values of binary variables `x[i][j]` where `solution_value() > 0.5`.
- Reconstruct the tour by starting at the fixed start node and following the selected edges.

### Code Usage
```python
# Example using OR-Tools MIP solver (conceptual)
from ortools.linear_solver import pywraplp

# 1. Instantiate Solver
solver = pywraplp.Solver.CreateSolver('SCIP')
# 2. Define data (placeholders)
NODES = range(num_nodes)
cost = {...}  # cost matrix
start_node = 0
n = len(NODES)
# 3. Build Model (variables, constraints, objective) per formulation
x = {}
for i in NODES:
    for j in NODES:
        if i != j:
            x[i, j] = solver.IntVar(0, 1, f'x_{i}_{j}')
u = {i: solver.IntVar(0, n-1, f'u_{i}') for i in NODES}
# ... Add all constraints ...
objective = solver.Objective()
for (i, j), var in x.items():
    objective.SetCoefficient(var, cost[i][j])
objective.SetMinimization()
# 4. Configure Solver
solver.SetTimeLimit(30000)  # 30 seconds
# 5. Solve and Check Status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # Extract tour
    tour = [start_node]
    current = start_node
    while len(tour) < len(NODES):
        for j in NODES:
            if j != current and x[current, j].solution_value() > 0.5:
                tour.append(j)
                current = j
                break
    print(f'Cost: {total_cost}, Tour: {tour}')
else:
    print('No solution found.')
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses before extracting solution values.
- Incorrect tour reconstruction logic that gets stuck in a loop; ensure each node is visited exactly once.
- Setting an invalid MIP gap (e.g., negative value); use a small non-negative value like 1e-4.

# Workflow 2 (CP-SAT with Circuit Constraint)

## Modeling stage

### Strategy Overview
Formulate the routing problem for a Constraint Programming (CP) solver using binary literal variables and a global `AddCircuit` constraint to inherently eliminate subtours. This often yields stronger propagation and better performance for mid-sized instances.

### Step 1 - Define Core Sets and Parameters
- Define a set of nodes (e.g., `NODES`).
- Define a cost parameter `cost[i][j]` for traveling from node i to node j.
- Identify a fixed start node (e.g., `start_node`).

### Step 2 - Create Decision Variables
- Create Boolean (or binary) variables `x[i][j]` for all i≠j, where `True` indicates the route from i to j is selected.

### Step 3 - Formulate Flow Conservation
- For each node i, add a constraint: sum of all outgoing `x[i][j]` equals 1.
- For each node i, add a constraint: sum of all incoming `x[j][i]` equals 1.
- The `AddCircuit` constraint will handle the subtour elimination, making MTZ constraints unnecessary.

### Step 4 - Apply the Circuit Constraint
- Prepare a list of arcs where each arc is a tuple `(tail, head, literal)` and `literal` is the corresponding Boolean variable `x[tail][head]`.
- Add the circuit constraint to the model: `model.AddCircuit(arcs)`.

### Step 5 - Define the Objective
- Minimize the total cost: `sum( cost[i][j] * x[i][j] for all i≠j )`.

### Formulation Template
```json
{
  "sets": ["NODES"],
  "parameters": [
    {"name": "cost", "index": ["NODES", "NODES"], "type": "integer"},
    {"name": "start_node", "type": "int"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["NODES", "NODES"], "type": "boolean"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j] * x[i][j] for i in NODES for j in NODES if i != j )"
  },
  "constraints": [
    {"name": "outgoing_flow", "expression": "sum( x[i][j] for j in NODES if j != i ) == 1 for i in NODES"},
    {"name": "incoming_flow", "expression": "sum( x[j][i] for j in NODES if j != i ) == 1 for i in NODES"},
    {"name": "circuit", "expression": "AddCircuit( arcs )", "arcs": "(i, j, x[i][j]) for i in NODES for j in NODES if i != j"}
  ]
}
```

### Common Pitfalls
- Using non-integer costs with CP-SAT, which requires integer objective coefficients. Scale float costs to integers if necessary.
- Including self-loop variables (`x[i][i]`) in the arcs list for the circuit constraint; they should be excluded.
- Expecting position variables; the circuit constraint makes them redundant for subtour elimination.

## Solving stage

### Strategy Overview
Solve the model using a CP-SAT solver (e.g., OR-Tools CP-SAT). Leverage its efficient handling of circuit constraints and Boolean logic. Configure search parameters to balance speed and solution quality.

### Step 1 - Instantiate CP-SAT Model
- Create a CP-SAT model instance (e.g., `cp_model.CpModel()`).

### Step 2 - Configure Solver Parameters
- Set a time limit (`model.Proto().search_parameters.max_time_in_seconds = t`).
- Set the number of parallel workers (`num_search_workers`).
- Set a relative gap limit for early termination if suboptimal solutions are acceptable.
- Set a random seed for reproducibility.

### Step 3 - Solve and Check Status
- Execute the solve command using a CP-SAT solver.
- Check the solver status. A successful status is `OPTIMAL` or `FEASIBLE`.
- If the status is `INFEASIBLE`, debug by relaxing constraints or checking the arc list.

### Step 4 - Extract and Reconstruct Solution
- Retrieve the objective function value.
- Extract the values of Boolean variables `x[i][j]` where `solver.Value(literal) == True`.
- Reconstruct the tour by starting at the fixed start node and following the selected edges.

### Code Usage
```python
# Example using OR-Tools CP-SAT (conceptual)
from ortools.sat.python import cp_model

# 1. Instantiate Model
model = cp_model.CpModel()
# 2. Define data (placeholders)
NODES = range(num_nodes)
cost = {...}  # integer cost matrix
start_node = -1  # Not strictly required for circuit, but useful for extraction
# 3. Build Model
x = {}
for i in NODES:
    for j in NODES:
        if i != j:
            x[i, j] = model.NewBoolVar(f'x_{i}_{j}')
# Flow conservation
for i in NODES:
    model.Add(sum(x[i, j] for j in NODES if j != i) == 1)
    model.Add(sum(x[j, i] for j in NODES if j != i) == 1)
# Circuit constraint
arcs = []
for i in NODES:
    for j in NODES:
        if i != j:
            arcs.append((i, j, x[i, j]))
model.AddCircuit(arcs)
# Objective
objective_terms = []
for (i, j), var in x.items():
    objective_terms.append(cost[i][j] * var)
model.Minimize(sum(objective_terms))
# 4. Configure Solver
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = -1  # all cores
# 5. Solve and Check Status
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    total_cost = solver.ObjectiveValue()
    # Extract tour
    tour = [0]  # assuming start_node = 0
    current = 0
    while len(tour) < len(NODES):
        for j in NODES:
            if j != current and solver.Value(x[current, j]) == 1:
                tour.append(j)
                current = j
                break
    print(f'Cost: {total_cost}, Tour: {tour}')
else:
    print('No solution found.')
```

### Common Pitfalls
- Forgetting to convert float costs to integers for CP-SAT, causing a model building error.
- Incorrectly constructing the arcs list (e.g., including `(i,i,var)`), which violates the circuit definition.
- Not using `solver.Value()` to extract Boolean variable values, assuming they are Python booleans.
