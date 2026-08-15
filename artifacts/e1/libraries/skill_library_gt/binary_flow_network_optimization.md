---
name: Binary Flow Network Optimization
description: |
  Model and solve unit flow routing problems as binary arc selection on directed graphs with linear costs, using either MIP solvers via algebraic modeling or specialized network flow algorithms.

---

# Workflow 1 (MIP Solver via Algebraic Modeling)

## Modeling stage

### Strategy Overview
Formulate the unit flow routing problem as a Mixed-Integer Program (MIP) using binary arc selection variables. This approach provides a flexible, explicit representation of flow conservation and source/sink constraints, suitable for a wide range of solvers.

### Step 1 - Define Sets and Parameters
- Define a set of nodes `N` representing all locations in the network.
- Define a set of arcs `A` as a subset of `N × N`, typically all ordered pairs `(i,j)` where `i ≠ j`.
- Create a cost parameter `c_{i,j}` for each arc `(i,j) ∈ A`, representing the linear cost of using that arc.

### Step 2 - Create Binary Decision Variables
- Create a binary decision variable `x_{i,j} ∈ {0,1}` for each arc `(i,j) ∈ A`. A value of 1 indicates the arc is selected for flow.

### Step 3 - Formulate Flow Conservation Constraints
- For the source node `s`, enforce net outflow: `∑_{j:(s,j)∈A} x_{s,j} - ∑_{i:(i,s)∈A} x_{i,s} = supply` (typically `supply = 1`).
- For the sink node `t`, enforce net inflow: `∑_{i:(i,t)∈A} x_{i,t} - ∑_{j:(t,j)∈A} x_{t,j} = demand` (typically `demand = 1`).
- For all intermediate nodes `k ∈ N \ {s, t}`, enforce flow balance: `∑_{i:(i,k)∈A} x_{i,k} = ∑_{j:(k,j)∈A} x_{k,j}`.

### Step 4 - Set Linear Cost Objective
- Formulate the objective to minimize total cost: `minimize ∑_{(i,j)∈A} c_{i,j} * x_{i,j}`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes"},
    {"name": "A", "description": "Set of directed arcs, subset of N × N, i ≠ j"}
  ],
  "parameters": [
    {"name": "c", "indexed_by": "A", "description": "Cost per unit flow on arc (i,j)"},
    {"name": "source", "description": "Source node identifier"},
    {"name": "sink", "description": "Sink node identifier"},
    {"name": "supply", "description": "Net flow out of source (typically 1)"},
    {"name": "demand", "description": "Net flow into sink (typically 1)"}
  ],
  "decision_variables": [
    {"name": "x", "indexed_by": "A", "domain": "binary", "description": "1 if arc (i,j) is used"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( c[i,j] * x[i,j] for (i,j) in A )"
  },
  "constraints": [
    {"name": "source_flow", "expression": "sum(x[source,j] for j if (source,j) in A) - sum(x[i,source] for i if (i,source) in A) == supply"},
    {"name": "sink_flow", "expression": "sum(x[i,sink] for i if (i,sink) in A) - sum(x[sink,j] for j if (sink,j) in A) == demand"},
    {"name": "flow_conservation", "indexed_by": "k in N, k != source, k != sink", "expression": "sum(x[i,k] for i if (i,k) in A) == sum(x[k,j] for j if (k,j) in A)"}
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops (`i=j`) from the arc set, which can lead to degenerate solutions.
- Incorrectly signing the source/sink constraints (outflow-inflow vs. inflow-outflow).
- Defining an incomplete arc set that unintentionally prohibits valid paths.

## Solving stage

### Strategy Overview
Solve the formulated MIP using a general-purpose solver (e.g., CBC, SCIP, Gurobi) via an algebraic modeling library (e.g., Pyomo). This involves configuring the solver, executing the optimization, and rigorously checking the solution status before extracting results.

### Step 1 - Instantiate Solver and Configure Parameters
- Create a solver instance via the modeling library's factory (e.g., `SolverFactory("solver_name")`).
- Set key parameters: time limit (`TimeLimit`), optimality gap tolerance (`MIPGap` or `ratio`), number of threads (`Threads`), and random seed (`Seed`) for reproducibility.

### Step 2 - Solve and Check Termination Status
- Execute the solve command on the model.
- Check the high-level solver status (e.g., `SolverStatus.ok`).
- Check the detailed termination condition (e.g., `TerminationCondition.optimal`, `.feasible`, `.infeasible`).

### Step 3 - Extract and Validate Solution
- If the status is optimal or feasible, extract the objective value via the model's objective object.
- Identify selected arcs by iterating over the binary variables `x[i,j]` and checking if their solution value exceeds a threshold (e.g., `> 0.5`).
- Perform a sanity check: verify that the selected arcs form a simple path from source to sink and satisfy flow conservation at intermediate nodes.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (following the formulation template)
model = build_binary_flow_model(N, A, costs, source, sink)

# Solve with configured solver
solver = pyo.SolverFactory('cbc')  # or 'scip', 'gurobi'
solver.options['seconds'] = 30      # Time limit
solver.options['ratio'] = 0.0       # MIP gap tolerance (0 for optimal)
solver.options['threads'] = 4
results = solver.solve(model, tee=False)  # Set tee=True for solver log

# Check status and termination
status = results.solver.status
termination = results.solver.termination_condition

if status == SolverStatus.ok and termination in (TerminationCondition.optimal, TerminationCondition.feasible):
    objective_value = float(pyo.value(model.obj))
    used_arcs = [(i, j) for (i, j) in model.A if pyo.value(model.x[i, j]) > 0.5]
    # Output results
else:
    # Handle infeasible/unfinished solves
    error_payload = {"status": str(status), "termination": str(termination)}
```

### Common Pitfalls
- Attempting to access solution values without first confirming the solver status is `ok` and termination is `optimal` or `feasible`.
- Setting a negative optimality gap tolerance, which is invalid for most solvers (use `0.0`).
- Not verifying that the extracted path is connected and respects all constraints.

# Workflow 2 (Specialized Network Flow Solver)

## Modeling stage

### Strategy Overview
Model the problem as a min-cost flow problem with unit capacities, leveraging the inherent network structure. This formulation allows the use of specialized, efficient algorithms (e.g., network simplex) available in dedicated libraries, bypassing the need for explicit constraint equations.

### Step 1 - Map to Min-Cost Flow Components
- Represent each node with a supply value: `supply[s] = 1` for source, `supply[t] = -1` for sink, `supply[k] = 0` for all intermediate nodes `k`.
- Represent each possible route as a directed arc with a unit capacity and a unit cost equal to the transportation cost.

### Step 2 - Define Graph Structure
- Create a list of all directed arcs as tuples `(start_node, end_node, cost)`.
- Ensure the graph includes all arcs necessary for feasible paths.

### Step 3 - Implicit Constraint Formulation
- Rely on the network flow solver's internal algorithms to enforce flow conservation at all nodes based on the supplied node balances.
- No need to manually write flow balance constraints.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes"},
    {"name": "A", "description": "List of arcs as (start, end, cost) tuples"}
  ],
  "parameters": [
    {"name": "source", "description": "Source node identifier"},
    {"name": "sink", "description": "Sink node identifier"}
  ],
  "decision_variables": [
    {"name": "flow", "indexed_by": "A", "domain": "integer", "description": "Flow on arc (i,j), will be binary due to unit capacities"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost * flow[i,j] for (i,j,cost) in A )"
  },
  "constraints": [
    {"name": "implicit_conservation", "description": "Enforced by solver: sum(flow[*,k]) - sum(flow[k,*]) = supply[k] for all k"}
  ]
}
```

### Common Pitfalls
- Incorrectly setting node supplies (e.g., using `1` for both source and sink instead of `+1` and `-1`).
- Defining arcs with capacities greater than 1, which may allow fractional flows and change the problem nature.
- Assuming the solver will automatically prevent cycles; additional constraints may be needed if subtours are possible.

## Solving stage

### Strategy Overview
Solve using a dedicated network flow solver (e.g., OR-Tools `SimpleMinCostFlow`). This involves loading the network structure, setting node supplies, and invoking the specialized algorithm, which is often faster than a general MIP solver for this problem class.

### Step 1 - Initialize Network Flow Solver
- Create an instance of the specialized solver (e.g., `min_cost_flow.SimpleMinCostFlow()`).
- Add each arc to the solver, specifying its tail, head, capacity (set to 1 for unit flow), and unit cost.

### Step 2 - Set Node Supplies and Solve
- For each node, set its supply value using the solver's API.
- Call the solver's `solve()` method.

### Step 3 - Process Results and Verify Optimality
- Check the solver's return status (e.g., `OPTIMAL`).
- If optimal, retrieve the total cost via the solver's optimal cost method.
- Iterate over all arcs to identify those with positive flow (`> 0`).
- Optionally, validate the solution by reconstructing the path from source to sink.

### Code Usage
```python
from ortools.graph import pywrapgraph

# Initialize solver
min_cost_flow = pywrapgraph.SimpleMinCostFlow()

# Add arcs (tail, head, capacity, unit cost)
arc_index = {}
for idx, (start, end, cost) in enumerate(arcs):
    arc_index[idx] = min_cost_flow.AddArcWithCapacityAndUnitCost(start, end, 1, cost)

# Set node supplies
node_supplies = [0] * num_nodes
node_supplies[source] = 1
node_supplies[sink] = -1
for node, supply in enumerate(node_supplies):
    min_cost_flow.SetNodeSupply(node, supply)

# Solve
solve_status = min_cost_flow.Solve()

if solve_status == min_cost_flow.OPTIMAL:
    total_cost = min_cost_flow.OptimalCost()
    used_arcs = []
    for i in range(min_cost_flow.NumArcs()):
        if min_cost_flow.Flow(i) > 0:
            tail = min_cost_flow.Tail(i)
            head = min_cost_flow.Head(i)
            used_arcs.append((tail, head))
    # Output results
else:
    # Handle non-optimal status
    print(f"Solver returned status: {solve_status}")
```

### Common Pitfalls
- Not checking the solver status (`OPTIMAL`) before accessing solution values, leading to runtime errors.
- Misinterpreting the solver's supply convention (some use `demand = -supply`).
- Forgetting that arcs are indexed internally by the solver, requiring a mapping to recover original arc information.
