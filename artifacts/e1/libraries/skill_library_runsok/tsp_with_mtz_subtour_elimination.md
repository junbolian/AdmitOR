---
name: TSP with MTZ Subtour Elimination
description: |
  Model routing problems with binary assignment and auxiliary position variables, then solve using either CP-SAT or MIP solvers with explicit subtour elimination.

---
# Workflow 1 (CP-SAT for Exact Combinatorial Routing)

## Modeling stage

### Strategy Overview
This workflow uses OR-Tools CP-SAT to model the problem as a pure integer program with logical constraints. It is well-suited for problems where the solver's native support for integer variables and efficient propagation of the Miller-Tucker-Zemlin (MTZ) constraints is beneficial.

### Step 1 - Define Core Sets and Parameters
- Define a set of nodes (e.g., `NODES`).
- Define a cost matrix `cost[i][j]` representing the travel cost from node `i` to node `j`.
- Identify any specific nodes with required position bounds (e.g., `node_k` must be visited between positions `L` and `U`).

### Step 2 - Create Binary Assignment Variables
- For each ordered pair `(i, j)` where `i != j`, create a binary variable `x[i][j]`.
- This variable equals 1 if the tour travels directly from node `i` to node `j`.

### Step 3 - Create Position Auxiliary Variables
- For each node `i`, create an integer variable `u[i]`.
- This variable represents the position (or visit order) of node `i` in the tour.

### Step 4 - Enforce Assignment Constraints
- Add constraints ensuring each node has exactly one outgoing arc: `sum(x[i][j] for j in NODES if j != i) == 1` for all `i`.
- Add constraints ensuring each node has exactly one incoming arc: `sum(x[i][j] for i in NODES if i != j) == 1` for all `j`.

### Step 5 - Apply MTZ Subtour Elimination Constraints
- For all `i, j` in `NODES` where `i != j` and `j != start_node`, add the constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.
- The condition `j != start_node` prevents redundant constraints for the fixed starting node.

### Step 6 - Set Position Bounds and Reference
- Fix the position of the starting node: `u[start_node] == 0`.
- For any node `k` with specified position bounds, add: `lower_bound <= u[k] <= upper_bound`.

### Step 7 - Define the Objective
- Minimize the total cost: `sum(cost[i][j] * x[i][j] for all i, j where i != j)`.

### Formulation Template
```json
{
  "sets": ["NODES"],
  "parameters": ["cost[i][j]"],
  "decision_variables": [
    {"name": "x[i][j]", "type": "binary", "domain": "{i, j in NODES, i != j}"},
    {"name": "u[i]", "type": "integer", "domain": "{i in NODES}"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i, j in NODES if i != j)"
  },
  "constraints": [
    {"name": "outgoing_arc", "expression": "sum(x[i][j] for j in NODES if j != i) == 1", "for_all": "i in NODES"},
    {"name": "incoming_arc", "expression": "sum(x[i][j] for i in NODES if i != j) == 1", "for_all": "j in NODES"},
    {"name": "mtz", "expression": "u[i] - u[j] + n * x[i][j] <= n - 1", "for_all": "i, j in NODES, i != j, j != start_node"},
    {"name": "fix_start", "expression": "u[start_node] == 0"},
    {"name": "position_bounds", "expression": "lower_bound <= u[k] <= upper_bound", "for_some": "k in NODES"}
  ]
}
```

### Common Pitfalls
- Forgetting the `j != start_node` condition in MTZ constraints, which creates redundant and potentially conflicting constraints.
- Not setting `u[start_node] = 0`, which leaves the position variables unbounded and can lead to subtours.
- Using an incorrect coefficient (`n`) in the MTZ constraint, which must be at least the number of nodes.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, which is designed for combinatorial problems with integer and logical constraints. Configure for exact solution and extract the tour sequence.

### Step 1 - Instantiate Solver and Build Model
- Create a CP-SAT model instance.
- Add variables and constraints as defined in the modeling stage using the solver's API (e.g., `model.NewBoolVar`, `model.NewIntVar`).

### Step 2 - Configure Solver Parameters
- Set a time limit (`max_time_in_seconds`) for runtime control.
- Enable parallel search (`num_search_workers`) if supported.
- Set `relative_gap_limit = 0.0` to seek an exact optimal solution.
- Optionally set a `random_seed` for reproducibility.

### Step 3 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the status: `OPTIMAL` or `FEASIBLE` indicates a solution was found.

### Step 4 - Extract and Reconstruct the Tour
- For all `i, j`, if `solver.Value(x[i][j])` equals 1, record that arc as part of the solution.
- Starting from the designated `start_node`, follow the arcs where `x[current][next] == 1` to reconstruct the full tour sequence.
- Collect the position values `u[i]` for validation.

### Step 5 - Validate and Output Results
- Verify the extracted tour visits each node exactly once and forms a Hamiltonian cycle.
- Output the objective value, the tour sequence, and the solver status.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... create variables x and u, add constraints, set objective
# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters: solver.parameters.max_time_in_seconds = time_limit
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract tour from x variables
    tour = [start_node]
    current = start_node
    while len(tour) < n_nodes:
        for j in nodes:
            if j != current and solver.Value(x[current][j]) > 0.5:
                tour.append(j)
                current = j
                break
    print(f"Objective: {solver.ObjectiveValue()}")
    print(f"Tour: {tour}")
else:
    print("No solution found.")
```

### Common Pitfalls
- Assuming the solver status is `OPTIMAL` without checking; always handle `FEASIBLE` and `INFEASIBLE` cases.
- Incorrectly reconstructing the tour by not checking the binary variable value against a tolerance (e.g., `> 0.5`).
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to create an abstract model that can be solved by various MIP solvers (e.g., Gurobi, CBC). It separates problem specification from solver choice, offering flexibility and clear constraint expression via rule functions.

### Step 1 - Define Abstract Sets and Parameters
- Define an abstract set `NODES`.
- Define a parameter `cost` indexed over `(i, j)` for `i != j`.
- Define parameters for position bounds (e.g., `pos_lb[k]`, `pos_ub[k]`) for specific nodes.

### Step 2 - Declare Decision Variables
- Declare binary variables `model.x[i, j]` for `i != j`.
- Declare integer variables `model.u[i]` with appropriate bounds (e.g., `0` to `n-1`).

### Step 3 - Enforce Assignment Constraints via Rules
- Define a rule for the outgoing arc constraint: `sum(model.x[i, j] for j in model.NODES if j != i) == 1`.
- Define a rule for the incoming arc constraint: `sum(model.x[i, j] for i in model.NODES if i != j) == 1`.

### Step 4 - Implement MTZ Constraints with Index Rules
- Define a rule that generates the MTZ constraint `model.u[i] - model.u[j] + n * model.x[i, j] <= n - 1` for all `i != j`, `j != start_node`.

### Step 5 - Set Position Bounds and Fix Starting Position
- Add a constraint fixing the start node's position: `model.u[start_node] == 0`.
- For nodes with bounds, add constraints: `pos_lb[k] <= model.u[k] <= pos_ub[k]`.

### Step 6 - Define the Objective Function
- Minimize `sum(cost[i, j] * model.x[i, j] for (i, j) in model.x.index_set())`.

### Formulation Template
```json
{
  "sets": ["NODES"],
  "parameters": ["cost[i, j]", "pos_lb[k]", "pos_ub[k]"],
  "decision_variables": [
    {"name": "x[i, j]", "type": "binary", "domain": "(i, j) in NODES × NODES, i != j"},
    {"name": "u[i]", "type": "integer", "domain": "i in NODES", "bounds": "[0, n-1]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for (i, j) in x.index_set())"
  },
  "constraints": [
    {"name": "outgoing", "rule": "sum(x[i, j] for j in NODES if j != i) == 1"},
    {"name": "incoming", "rule": "sum(x[i, j] for i in NODES if i != j) == 1"},
    {"name": "mtz", "rule": "u[i] - u[j] + n * x[i, j] <= n - 1", "condition": "i != j, j != start_node"},
    {"name": "fix_start", "rule": "u[start_node] == 0"},
    {"name": "node_position_bounds", "rule": "pos_lb[k] <= u[k] <= pos_ub[k]", "for_some": "k"}
  ]
}
```

### Common Pitfalls
- Defining MTZ constraints for `j == start_node`, which creates a constraint `u[i] - 0 + n*x[i,start] <= n-1` that can be overly restrictive.
- Not providing proper bounds for the `u[i]` variables, which can lead to solver performance issues or unbounded variable warnings.
- Incorrectly indexing the cost parameter in the objective, leading to missing terms or key errors.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with concrete data, then use a solver factory to interface with a MIP solver. Configure solver-specific parameters for performance and extract the solution for validation.

### Step 1 - Create Concrete Model and Instantiate Data
- Create a `ConcreteModel()`.
- Populate the sets (`model.NODES`) and parameters (`model.cost`, `model.pos_lb`, etc.) with actual data.

### Step 2 - Select and Configure Solver
- Use `SolverFactory('solver_name')` (e.g., `'gurobi'`, `'cbc'`).
- Set solver parameters: `TimeLimit`, `MIPGap=0.0` for exact optimality, `Threads` for parallelism, `Seed` for reproducibility.

### Step 3 - Solve and Check Termination Conditions
- Call `solver.solve(model, tee=False)`.
- Check `solver.status` (should be `ok`) and `model.solutions[0].termination_condition` (`optimal` or `feasible`).

### Step 4 - Extract Solution Values
- Access variable values: `pyo.value(model.x[i, j])` and `pyo.value(model.u[i])`.
- Reconstruct the tour by starting at `start_node` and following arcs where `x[i, j]` is approximately 1.

### Step 5 - Validate and Report
- Verify the tour is a Hamiltonian cycle.
- Report the objective value (`pyo.value(model.obj)`), the tour sequence, and the solver status.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.NODES = pyo.Set(initialize=nodes)
# ... define parameters, variables, constraints, objective
# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = time_limit
solver.options['MIPGap'] = 0.0
results = solver.solve(model, tee=False)
if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    # Extract tour
    tour = [start_node]
    current = start_node
    while len(tour) < len(model.NODES):
        for j in model.NODES:
            if j != current and pyo.value(model.x[current, j]) > 0.5:
                tour.append(j)
                current = j
                break
    print(f"Objective: {pyo.value(model.obj)}")
    print(f"Tour: {tour}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`; a status of `ok` with `termination_condition` of `infeasible` indicates no solution.
- Comparing floating-point values of binary variables directly to 1; use a tolerance (e.g., `> 0.5`).
- Forgetting to pass the model instance to `pyo.value()` when accessing variable values.
