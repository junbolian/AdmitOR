---
name: TSP_MTZ_Formulation_Skill
description: |
  Model and solve traveling salesman problems using binary assignment and Miller-Tucker-Zemlin subtour elimination, with workflows for both integer programming and specialized routing solvers.
---

# Workflow 1 (Integer Programming with MTZ)

## Modeling stage

### Strategy Overview
This workflow models the TSP as a Mixed-Integer Program (MIP) using binary arc selection variables and integer position variables for subtour elimination via the Miller-Tucker-Zemlin (MTZ) constraints. It is a direct, portable formulation suitable for general-purpose MIP/CP-SAT solvers.

### Step 1 - Define Sets and Parameters
- Define a set of nodes to be visited, typically indexed from 0 to N-1.
- Define a cost matrix parameter, `cost[i][j]`, representing the travel cost from node i to node j. Ensure the matrix is square and self-loop costs are set to a large value or zero as appropriate.

### Step 2 - Create Decision Variables
- Create binary decision variables `x[i][j]` for each ordered pair of distinct nodes. `x[i][j] = 1` indicates the tour includes the arc from i to j.
- Create integer position variables `u[i]` for each node, representing its order in the tour. Bound them appropriately (e.g., 0 to N-1).

### Step 3 - Formulate Degree Constraints
- For each node i, add a constraint ensuring exactly one outgoing arc: `sum_{j != i} x[i][j] == 1`.
- For each node j, add a constraint ensuring exactly one incoming arc: `sum_{i != j} x[i][j] == 1`.

### Step 4 - Implement MTZ Subtour Elimination
- For all pairs of nodes i, j (where i and j are not the designated start node), add the MTZ constraint: `u[i] - u[j] + N * x[i][j] <= N - 1`.
- Fix the position of the start node to break symmetry: `u[start_node] = 0`.

### Step 5 - Define the Objective Function
- Formulate the objective to minimize total travel cost: `minimize sum_{i,j} cost[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    "nodes: list of node indices (e.g., [0, 1, ..., N-1])"
  ],
  "parameters": [
    "cost: a |nodes| x |nodes| matrix of travel costs"
  ],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc i->j is used",
    "u[i]: integer, position of node i in the tour"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in nodes} sum_{j in nodes} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "single_departure(i): sum_{j in nodes, j != i} x[i][j] == 1, for all i",
    "single_arrival(j): sum_{i in nodes, i != j} x[i][j] == 1, for all j",
    "mtz(i,j): u[i] - u[j] + |nodes| * x[i][j] <= |nodes| - 1, for all i,j where i != start_node, j != start_node, i != j",
    "start_position: u[start_node] == 0",
    "no_self_loop: x[i][i] == 0, for all i"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude the start node from the MTZ constraints, which can lead to incorrect or overly restrictive formulations.
- Using an invalid MIP gap parameter (e.g., a negative value); set it to 0.0 for exact optimality or a small positive tolerance.
- Not providing an upper bound for the position variables `u[i]`, which can lead to unbounded variable errors in some solvers.

## Solving stage

### Strategy Overview
Solve the MIP model using a general-purpose integer programming solver (e.g., CP-SAT, Gurobi, CBC). The focus is on correct solver configuration, robust solution status checking, and reliable tour reconstruction from binary variable values.

### Step 1 - Configure Solver and Parameters
- Instantiate the solver (e.g., `cp_model.CpSolver()` for OR-Tools CP-SAT).
- Set key parameters: `max_time_in_seconds` for time limit, `num_search_workers` for parallelism, and `random_seed` for reproducibility. For optimality, set `relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Invoke the solver's solve method on the model.
- Check the solver's status code (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`). Proceed only if status indicates a feasible solution was found.

### Step 3 - Extract Solution and Reconstruct Tour
- Collect all arcs where the binary variable `x[i][j]` has a value greater than a tolerance (e.g., 0.5).
- Starting from the designated start node, iteratively find the unique outgoing arc to reconstruct the full tour sequence.
- Optionally, compute the total cost from the extracted tour to validate against the solver's reported objective value.

### Step 4 - Output and Verification
- Return a standardized result containing the objective value, the tour sequence, and solver status.
- For small instances, consider a brute-force verification to confirm optimality and validate the model's correctness.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (create variables, add constraints, set objective)
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

# solve with status / termination checks
status = solver.Solve(model)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract active arcs
    tour_arcs = [(i, j) for i in nodes for j in nodes if solver.Value(x[i][j]) > 0.5]
    # Reconstruct tour starting from start_node
    tour = [start_node]
    current = start_node
    while len(tour) < len(nodes):
        next_node = [j for (i, j) in tour_arcs if i == current][0]
        tour.append(next_node)
        current = next_node
    objective_value = solver.ObjectiveValue()
    result = {"status": status, "objective": objective_value, "tour": tour}
else:
    result = {"status": status, "error": "No feasible solution found"}
```

### Common Pitfalls
- Assuming a solver status of `OPTIMAL` without checking termination conditions; always handle `FEASIBLE` and other statuses appropriately.
- Incorrectly reconstructing the tour due to not handling the return to start if a closed tour is required; ensure the reconstruction logic accounts for the final arc.
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.

# Workflow 2 (Specialized Routing Solver)

## Modeling stage

### Strategy Overview
This workflow leverages a solver's native routing library (e.g., OR-Tools Routing Library) which is specifically optimized for TSP and VRP problems. It uses the solver's internal graph representation and callbacks for distance/cost, abstracting away explicit MTZ constraints.

### Step 1 - Define the Routing Model and Manager
- Create a routing model object, specifying the number of nodes (including the depot).
- Create a routing index manager to handle the mapping between solver indices and your node indices.

### Step 2 - Register a Transit Cost Callback
- Define a callback function that, given two solver indices, returns the travel cost between the corresponding original nodes.
- Register this callback with the routing model as the transit cost evaluator.

### Step 3 - Set Routing Parameters and Search Strategy
- Set the first solution heuristic (e.g., `PATH_CHEAPEST_ARC`) to find an initial feasible tour quickly.
- Configure the local search metaheuristic (e.g., `GUIDED_LOCAL_SEARCH`) and set its intensity parameters for solution improvement.
- Define a time limit or iteration limit for the search process.

### Step 4 - Add Core TSP Constraints
- Use the solver's built-in methods to enforce that each node is visited exactly once. This typically involves setting the same start and end location for the route and using the model's internal constraints.

### Formulation Template
```json
{
  "sets": [
    "nodes: list of node indices, with node 0 typically as the depot"
  ],
  "parameters": [
    "distance_callback: function(i, j) returning cost from node i to j"
  ],
  "decision_variables": [
    "next_var[i]: solver's internal variable representing the next node after i"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum over arcs of distance_callback(i, j) * indicator(next_var[i] == j)"
  },
  "constraints": [
    "single_visit: each node (except depot) must be visited exactly once, enforced by solver's AddDisjunction or by setting start/end points"
  ]
}
```

### Common Pitfalls
- Incorrectly mapping between solver indices and original node indices in the distance callback, leading to wrong cost calculations.
- Not setting a time limit, allowing the solver to run longer than intended on large problems.
- Assuming the solver always returns the global optimum; for large instances, it often returns a high-quality heuristic solution.

## Solving stage

### Strategy Overview
Solve the problem using the routing solver's `SolveWithParameters` method. The solver handles the search logic internally. The primary tasks are configuring the search, extracting the solution route, and validating the result.

### Step 1 - Configure and Execute the Solver
- Assemble the search parameters from the configured first solution strategy, local search metaheuristic, and time limit.
- Call the solver's main solve method (e.g., `routing.SolveWithParameters`).

### Step 2 - Extract and Interpret the Solution
- Check if a solution was found by verifying the solver's returned solution object is not `None`.
- Use the solution object and the index manager to extract the sequence of visited nodes. Start from the depot and follow the `NextVar` values.

### Step 3 - Compute and Verify Total Cost
- Use the extracted node sequence and the original cost matrix to compute the total tour cost independently.
- Compare this computed cost with the objective value reported by the solver to ensure consistency and catch potential callback errors.

### Step 4 - Return Standardized Results
- Package the tour sequence, total cost, and solver status (e.g., `ROUTING_SUCCESS`, `ROUTING_FAIL_TIMEOUT`) into a structured output.

### Code Usage
```python
# build model from formulation
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def distance_callback(from_index, to_index):
    # Convert solver indices to user node indices
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return cost_matrix[from_node][to_node]

# Create routing model and manager
manager = pywrapcp.RoutingIndexManager(len(nodes), 1, 0) # 1 vehicle, depot at index 0
routing = pywrapcp.RoutingModel(manager)
transit_callback_index = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# Set search parameters
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
search_parameters.time_limit.seconds = 30

# solve with status / termination checks
solution = routing.SolveWithParameters(search_parameters)
if solution:
    # Extract tour
    index = routing.Start(0)
    tour = [manager.IndexToNode(index)]
    while not routing.IsEnd(index):
        index = solution.Value(routing.NextVar(index))
        tour.append(manager.IndexToNode(index))
    # Compute cost for verification
    total_cost = sum(cost_matrix[tour[i]][tour[i+1]] for i in range(len(tour)-1))
    result = {"status": "ROUTING_SUCCESS", "objective": total_cost, "tour": tour}
else:
    result = {"status": "ROUTING_FAIL", "error": "No solution found"}
```

### Common Pitfalls
- Forgetting to convert solver indices back to original node indices when extracting the tour, resulting in an incorrect sequence.
- Not verifying the solution cost independently, which can miss errors in the distance callback implementation.
- Misconfiguring the number of vehicles in the `RoutingIndexManager`; for a standard TSP, use 1 vehicle.
