---
name: TSP_MTZ_Formulation_Skill
description: |
  Model and solve traveling salesman problems using binary arc variables and Miller-Tucker-Zemlin subtour elimination, with implementation options for both exact MIP and heuristic routing solvers.
---

# Workflow 1 (Exact MIP with MTZ Constraints)

## Modeling stage

### Strategy Overview
This workflow formulates the TSP as a Mixed-Integer Program (MIP) using binary arc selection variables and integer position variables to eliminate subtours via the Miller-Tucker-Zemlin (MTZ) method. It is suitable for small-to-medium instances where an exact, provably optimal solution is required.

### Step 1 - Define Sets and Parameters
- Define a set `N` representing all nodes (e.g., cities, locations).
- Define a parameter `cost[i][j]` representing the travel cost from node `i` to node `j`. Ensure `cost[i][i]` is set to a large value or zero to prevent self-loops.

### Step 2 - Create Decision Variables
- Create binary decision variables `x[i][j]` for all `i, j` in `N`, where `x[i][j] = 1` indicates travel from node `i` to node `j`.
- Create integer decision variables `u[i]` for all `i` in `N`, representing the position of node `i` in the tour.

### Step 3 - Formulate Degree Constraints
- For each node `i` in `N`, add a constraint `sum(x[i][j] for j in N) == 1` to ensure exactly one departure.
- For each node `j` in `N`, add a constraint `sum(x[i][j] for i in N) == 1` to ensure exactly one arrival.

### Step 4 - Apply Subtour Elimination (MTZ)
- For all `i, j` in `N` where `i != j` and `i != 0` and `j != 0`, add the MTZ constraint: `u[i] - u[j] + |N| * x[i][j] <= |N| - 1`.
- Set the position of the start/depot node: `u[0] = -1`.
- Set bounds for other position variables: `0 <= u[i] <= |N| - 1` for `i` in `N \ {0}`.

### Step 5 - Define Objective Function
- Formulate the objective to minimize total travel cost: `sum(cost[i][j] * x[i][j] for i in N for j in N)`.

### Formulation Template
```json
{
  "sets": ["N: set of nodes"],
  "parameters": ["cost[i][j]: travel cost from i to j"],
  "decision_variables": [
    "x[i][j]: binary, arc selection",
    "u[i]: integer, node position in tour"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in N for j in N)"
  },
  "constraints": [
    "sum(x[i][j] for j in N) == 1 for all i in N",
    "sum(x[i][j] for i in N) == 1 for all j in N",
    "u[i] - u[j] + |N| * x[i][j] <= |N| - 1 for all i,j in N, i!=j, i!=0, j!=0",
    "u[0] == -1",
    "0 <= u[i] <= |N| - 1 for all i in N \\ {0}"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude the start node (`i!=0, j!=0`) in the MTZ constraints, which can make the model infeasible.
- Setting `u[0] = 0` instead of `-1` or `0`, which can create symmetric solutions and slow solving; using `-1` is a common trick to tighten the formulation.
- Not setting `cost[i][i]` to a large value, which can allow trivial, zero-cost self-loops.

## Solving stage

### Strategy Overview
Solve the MIP model using an exact solver (e.g., CP-SAT, CBC, Gurobi) configured for optimality. The focus is on obtaining a provably optimal solution, with runtime control and verification steps.

### Step 1 - Select and Configure Solver
- Choose a MIP-capable solver backend (e.g., OR-Tools CP-SAT, `pulp` with CBC).
- Set a time limit (`max_time_in_seconds`) to prevent excessive runtime.
- Set optimality tolerance (`relative_gap_limit = 0.0`) to search for the exact optimum.
- Configure parallel threads (`num_search_workers`) for speed and set a random seed for reproducibility.

### Step 2 - Solve and Check Status
- Invoke the solver on the built model.
- Check the solver status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNBOUNDED`) immediately after the solve call.
- If status is not `OPTIMAL` or `FEASIBLE`, handle the error and return a structured failure message.

### Step 3 - Extract and Reconstruct Solution
- Extract the values of the `x[i][j]` variables.
- Reconstruct the tour sequence by starting at the designated depot node (e.g., node 0) and iteratively finding the next node `j` where `x[current][j] == 1`.
- Compute the total cost by summing `cost[i][j]` for each arc in the reconstructed tour, as a verification step against the solver's reported objective.

### Step 4 - Output and Verify
- Return a structured result containing the objective value, the tour sequence, and the solver status.
- For small instances (e.g., `|N| <= 10`), optionally perform a brute-force verification to confirm optimality and solution correctness.

### Code Usage
```python
# build model from formulation
model = build_mip_model(node_set, cost_matrix)
# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.relative_gap_limit = 0.0
solver.parameters.num_search_workers = 4
solver.parameters.random_seed = 42

status = solver.Solve(model)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract arc variable values
    arc_values = extract_arc_values(solver, model, node_set)
    # Reconstruct tour
    tour = reconstruct_tour_from_arcs(arc_values, depot=0)
    # Calculate verified cost
    total_cost = calculate_tour_cost(tour, cost_matrix)
    result = {"status": "SUCCESS", "cost": total_cost, "tour": tour}
else:
    result = {"status": "FAILURE", "reason": solver.StatusName(status)}
```

### Common Pitfalls
- Relying solely on the solver's reported objective value without recalculating from the extracted tour, which can lead to precision errors.
- Not checking solver status, leading to attempts to extract solutions from failed or infeasible models.
- Setting an overly restrictive time limit for larger instances, causing premature termination before a good solution is found.

# Workflow 2 (Specialized Routing Solver)

## Modeling stage

### Strategy Overview
This workflow leverages a specialized routing solver (e.g., OR-Tools Routing Library) which abstracts the TSP formulation. It uses a high-level API where the model is defined implicitly via a distance matrix and callback functions, and the solver employs powerful heuristics and metaheuristics. This is suitable for larger instances where near-optimal solutions are acceptable.

### Step 1 - Define Problem Data
- Define the `distance_matrix`, a 2D list where `distance_matrix[i][j]` is the travel cost from node `i` to node `j`.
- Specify the `depot` index (start and end node).
- Set the `num_vehicles` to 1 for the classic TSP.

### Step 2 - Create Routing Model Manager
- Instantiate a `RoutingIndexManager` with the number of nodes, number of vehicles, and depot index. This manager handles internal node index mappings.

### Step 3 - Create Routing Model and Register Transit Callback
- Create a `RoutingModel` instance from the manager.
- Define a `distance_callback` function that, given internal solver indices, returns the corresponding cost from the `distance_matrix`.
- Register this callback with the routing model to define the arc costs.

### Step 4 - Set Solution Strategy Parameters
- Configure first solution heuristics (e.g., `PATH_CHEAPEST_ARC`, `CHRISTOFIDES`).
- Configure local search metaheuristics (e.g., `GUIDED_LOCAL_SEARCH`, `SIMULATED_ANNEALING`).
- Set a runtime limit (`time_limit.seconds`).

### Formulation Template
```json
{
  "sets": ["N: set of nodes"],
  "parameters": ["distance_matrix[i][j]: travel cost from i to j", "depot: index of start/end node"],
  "decision_variables": ["Implicitly managed by the routing solver"],
  "objective": {
    "sense": "min",
    "expression": "Sum of distances along the route"
  },
  "constraints": ["Single-vehicle route starting and ending at depot, visiting all nodes exactly once"]
}
```

### Common Pitfalls
- Passing an incorrect or non-square `distance_matrix`, causing index errors.
- Not setting a `time_limit`, which may cause the solver to run indefinitely on difficult instances.
- Using the default solver parameters without tuning for problem size, potentially yielding poor-quality solutions quickly.

## Solving stage

### Strategy Overview
Solve the problem using the specialized routing solver's `SolveWithParameters` method. The focus is on obtaining a high-quality feasible solution efficiently, with extraction and verification of the resulting route.

### Step 1 - Instantiate and Configure Solver
- Create the routing model and manager as defined in the modeling stage.
- Set the arc cost evaluator to the registered transit callback.
- Create a `RoutingSearchParameters` object and populate it with the chosen heuristics, metaheuristics, and time limit.

### Step 2 - Solve and Check for Solution
- Call `routing.SolveWithParameters(search_parameters)`.
- Check if a solution object is returned (`solution` is not `None`).

### Step 3 - Extract Route and Compute Cost
- Extract the route sequence by starting from the vehicle's start node and iterating through `solution.Value(routing.NextVar(...))`.
- Convert the solver's internal indices back to the original node indices using the `IndexToNode` method of the manager.
- Manually compute the total tour cost by summing the distances between consecutive nodes in the extracted route, using the original `distance_matrix`.

### Step 4 - Output Structured Result
- Return a dictionary containing the total cost, the route as a list of node indices, and the solver's wall time.
- Include the name of the solution strategy used for traceability.

### Code Usage
```python
# build model from formulation
def solve_with_routing_solver(distance_matrix, depot=0):
    from ortools.constraint_solver import routing_enums_pb2, pywrapcp

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, depot)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 30

    # solve with status / termination checks
    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))  # Add depot at end
        total_cost = sum(distance_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
        return {"cost": total_cost, "route": route, "solver": "OR-Tools Routing"}
    else:
        return {"status": "NO_SOLUTION_FOUND"}
```

### Common Pitfalls
- Forgetting to append the final depot node to the route, resulting in an incomplete tour.
- Assuming the solver's internal objective value is perfectly accurate; always recalculate cost from the extracted route.
- Not experimenting with different `first_solution_strategy` and `local_search_metaheuristic` combinations, which can significantly impact solution quality for a given runtime.
