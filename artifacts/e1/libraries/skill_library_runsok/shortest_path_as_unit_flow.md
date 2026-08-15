---
name: Shortest Path as Unit Flow
description: |
  Model and solve shortest path problems as binary arc selection with unit flow from source to sink, using either min-cost flow with unit capacities or binary integer programming.
---

# Workflow 1 (Min-Cost Flow with Unit Capacities)

## Modeling stage

### Strategy Overview
Formulate the shortest path problem as a min-cost flow problem with unit capacities and a total flow of one. This leverages the integrality property of min-cost flow with unit capacities, guaranteeing integer (0/1) flows without explicit binary variables.

### Step 1 - Define Network Structure
- Define the set of nodes `N` and the set of all possible directed arcs `A`.
- Identify the source node `s` and sink node `t`.

### Step 2 - Parameterize Arc Costs
- Create a cost parameter `c[i][j]` for each arc `(i,j)` in `A`.
- For arcs with unknown or prohibited costs, assign a sufficiently large penalty value (e.g., `M`) to discourage their use while maintaining feasibility.

### Step 3 - Set Node Supplies
- Set the supply at the source node `s` to `1`.
- Set the supply at the sink node `t` to `-1`.
- Set the supply for all other intermediate nodes to `0`.

### Step 4 - Set Arc Capacities
- Assign a capacity of `1` to every arc `(i,j)` in `A`. This, combined with a total flow of 1, ensures flows are binary.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i,j in N"
  ],
  "parameters": [
    "s: source node in N",
    "t: sink node in N",
    "c[i][j]: cost of traversing arc (i,j) in A",
    "M: large penalty cost for missing/undesired arcs"
  ],
  "decision_variables": [
    "f[i][j]: flow on arc (i,j) in A (continuous, but will be integer 0/1)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{(i,j) in A} c[i][j] * f[i][j]"
  },
  "constraints": [
    "Flow conservation (intermediate nodes): sum_{(i,k) in A} f[i][k] = sum_{(k,j) in A} f[k][j] for all k in N \\ {s, t}",
    "Source supply: sum_{(s,j) in A} f[s][j] = 1",
    "Sink demand: sum_{(i,t) in A} f[i][t] = 1",
    "Capacity limits: 0 <= f[i][j] <= 1 for all (i,j) in A"
  ]
}
```

### Common Pitfalls
- Using a penalty cost `M` that is too small, allowing the solver to use a high-cost, infeasible (in reality) arc as part of the optimal path.
- Forgetting to set the sink node supply to `-1`, which leads to an infeasible model.
- Assuming the solver will return integer flows without setting unit capacities and a total flow of one.

## Solving stage

### Strategy Overview
Use a specialized min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) that exploits the network structure for efficiency. The solver directly handles the flow conservation and capacity constraints.

### Step 1 - Initialize Solver and Add Nodes
- Instantiate the min-cost flow solver.
- Add all nodes to the solver.
- Set the supply/demand for each node according to the model.

### Step 2 - Add Arcs with Costs and Capacities
- For each arc `(i,j)` in `A`, add it to the solver with its cost `c[i][j]` and a capacity of `1`.

### Step 3 - Solve and Check Status
- Invoke the solver's `solve()` method.
- Check the solver status (e.g., `OPTIMAL`, `INFEASIBLE`) to confirm a solution was found.

### Step 4 - Extract and Reconstruct the Path
- Retrieve the flow value for each arc. Arcs with a flow > 0.5 are part of the solution path.
- Starting from the source node `s`, follow the outgoing arc with positive flow to reconstruct the complete path to the sink `t`.

### Step 5 - Validate Solution
- Verify the total cost of the reconstructed path matches the optimal objective value returned by the solver.
- Confirm flow conservation at intermediate nodes by checking inflows and outflows.

### Code Usage
```python
# Example using OR-Tools SimpleMinCostFlow
from ortools.graph import pywrapgraph

# Instantiate solver
min_cost_flow = pywrapgraph.SimpleMinCostFlow()

# Add nodes and set supplies (node_index, supply)
for node in N:
    supply = 1 if node == s else (-1 if node == t else 0)
    min_cost_flow.SetNodeSupply(node, supply)

# Add arcs (tail, head, capacity, cost)
for (i, j) in A:
    min_cost_flow.AddArcWithCapacityAndUnitCost(i, j, 1, c[i][j])

# Solve
status = min_cost_flow.Solve()

if status == min_cost_flow.OPTIMAL:
    # Extract optimal flow and cost
    optimal_cost = min_cost_flow.OptimalCost()
    
    # Reconstruct path
    path = []
    current_node = s
    while current_node != t:
        for arc_index in range(min_cost_flow.NumArcs()):
            if min_cost_flow.Tail(arc_index) == current_node and min_cost_flow.Flow(arc_index) > 0:
                next_node = min_cost_flow.Head(arc_index)
                path.append((current_node, next_node))
                current_node = next_node
                break
    print(f"Optimal path: {path}")
    print(f"Total cost: {optimal_cost}")
else:
    print("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Misinterpreting solver status codes, leading to incorrect handling of infeasible or unbounded problems.
- Not checking for numerical precision when comparing flow to zero; use a tolerance (e.g., `flow > 1e-7`).
- Attempting to reconstruct the path by checking all arcs without a systematic traversal from the source, which can fail if the solution contains cycles (which it shouldn't in this formulation).

# Workflow 2 (Binary Integer Programming)

## Modeling stage

### Strategy Overview
Formulate the shortest path problem explicitly as a Binary Integer Program (BIP) with binary arc selection variables. This approach provides maximum flexibility for adding side constraints and is solved with general-purpose MIP solvers.

### Step 1 - Define Binary Decision Variables
- For each arc `(i,j)` in `A`, define a binary decision variable `x[i][j]` that equals `1` if the arc is used in the path, and `0` otherwise.

### Step 2 - Enforce Source and Sink Constraints
- Add a constraint ensuring exactly one arc leaves the source node: `sum_{(s,j) in A} x[s][j] = 1`.
- Add a constraint ensuring exactly one arc enters the sink node: `sum_{(i,t) in A} x[i][t] = 1`.

### Step 3 - Enforce Flow Conservation at Intermediate Nodes
- For each intermediate node `k` (not source or sink), add a constraint: `sum_{(i,k) in A} x[i][k] = sum_{(k,j) in A} x[k][j]`. This ensures the path passes through the node if it enters it.

### Step 4 - (Optional) Prevent Flow into Source
- Add a constraint `sum_{(i,s) in A} x[i][s] = 0` to explicitly prevent the path from cycling back to the source.

### Step 5 - Define Objective Function
- Minimize the total cost: `sum_{(i,j) in A} c[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i,j in N"
  ],
  "parameters": [
    "s: source node in N",
    "t: sink node in N",
    "c[i][j]: cost of traversing arc (i,j) in A"
  ],
  "decision_variables": [
    "x[i][j]: binary variable indicating if arc (i,j) is used"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{(i,j) in A} c[i][j] * x[i][j]"
  },
  "constraints": [
    "Source outflow: sum_{(s,j) in A} x[s][j] = 1",
    "Sink inflow: sum_{(i,t) in A} x[i][t] = 1",
    "Flow conservation: sum_{(i,k) in A} x[i][k] = sum_{(k,j) in A} x[k][j] for all k in N \\ {s, t}",
    "No return to source: sum_{(i,s) in A} x[i][s] = 0 (optional)"
  ]
}
```

### Common Pitfalls
- Forgetting the flow conservation constraints for intermediate nodes, which can result in disconnected or invalid paths.
- Using an incomplete set of arcs `A`, making the model infeasible if no path exists.
- Not defining the binary nature of variables explicitly in the solver, leading to continuous relaxations.

## Solving stage

### Strategy Overview
Use a general-purpose Mixed-Integer Programming (MIP) solver (e.g., CBC, SCIP, HiGHS via Pyomo or PuLP). This approach is versatile and allows for easy integration of additional logical constraints.

### Step 1 - Instantiate Model and Define Variables
- Create a model object.
- Add binary variables `x[i][j]` for each arc `(i,j)`.

### Step 2 - Add Constraints to Model
- Add the source, sink, and flow conservation constraints as defined in the model.

### Step 3 - Set Objective Function
- Set the model objective to minimize the sum of costs over selected arcs.

### Step 4 - Configure and Execute Solver
- Select an appropriate MIP solver backend.
- Set solver parameters such as time limit, optimality gap, and number of threads.
- Call the `solve()` method.

### Step 5 - Process Solution and Extract Path
- Check the solver termination condition (e.g., `OPTIMAL`, `FEASIBLE`).
- Retrieve the values of the binary variables. Arcs with `x[i][j] > 0.5` are selected.
- Reconstruct the path by starting at the source and following selected arcs to the sink.

### Step 6 - Validate and Report
- Calculate the total cost from the selected arcs and verify it matches the solver's reported objective value.
- Optionally, verify that all constraints are satisfied by the solution.

### Code Usage
```python
# Example using PuLP with CBC
import pulp

# Create model
model = pulp.LpProblem("ShortestPath", pulp.LpMinimize)

# Define binary variables
x = {}
for (i, j) in A:
    x[i, j] = pulp.LpVariable(f"x_{i}_{j}", cat='Binary')

# Set objective
model += pulp.lpSum(c[i][j] * x[i, j] for (i, j) in A)

# Source constraint
model += pulp.lpSum(x[s, j] for j in N if (s, j) in A) == 1, "SourceOutflow"

# Sink constraint
model += pulp.lpSum(x[i, t] for i in N if (i, t) in A) == 1, "SinkInflow"

# Flow conservation for intermediate nodes
for k in N:
    if k not in (s, t):
        inflow = pulp.lpSum(x[i, k] for i in N if (i, k) in A)
        outflow = pulp.lpSum(x[k, j] for j in N if (k, j) in A)
        model += inflow == outflow, f"FlowConservation_{k}"

# Solve
solver = pulp.PULP_CBC_CMD(timeLimit=30, threads=4)
model.solve(solver)

# Check status and extract solution
if pulp.LpStatus[model.status] == 'Optimal':
    selected_arcs = [(i, j) for (i, j) in A if pulp.value(x[i, j]) > 0.5]
    
    # Reconstruct path (simple traversal, assumes a single path)
    path = []
    current = s
    while current != t:
        for (i, j) in selected_arcs:
            if i == current:
                path.append((i, j))
                current = j
                break
    print(f"Optimal path: {path}")
    print(f"Total cost: {pulp.value(model.objective)}")
else:
    print("No optimal solution found.")
```

### Common Pitfalls
- Not setting a time limit or optimality gap for large instances, potentially causing excessively long runtimes.
- Incorrectly handling the solver's status/termination condition, leading to errors when trying to access a non-existent solution.
- Using a naive path reconstruction that fails if the selected arcs do not form a simple path (e.g., due to solver numerical errors or an incorrect model).
