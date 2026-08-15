---
name: Minimum Cost Network Flow
description: |
  Model and solve capacitated network flow problems with supply/demand balance and linear costs using either a general LP framework or a specialized network flow algorithm.
---

# Workflow 1 (General LP Formulation)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using a generic modeling library (e.g., Pyomo, OR-Tools LP). This approach provides flexibility for adding complex constraints later and is portable across many solvers.

### Step 1 - Define Network Structure
- Represent the system as a directed graph. Define a set of nodes (e.g., locations) and a set of directed arcs representing possible transportation routes.
- Store parameters in dictionaries: `supply_demand[node]` (positive for supply, negative for demand), `cost[(i,j)]` (unit cost), and `capacity[(i,j)]` (maximum flow).

### Step 2 - Create Flow Variables
- Create a continuous, non-negative decision variable `x[(i,j)]` for each directed arc `(i,j)`.
- Set the variable's lower bound to 0 and its upper bound to `capacity[(i,j)]`. If an arc has no capacity, use a sufficiently large upper bound.

### Step 3 - Enforce Flow Conservation
- For each node `i`, enforce the constraint: `sum(x[(i,j)] for all j) - sum(x[(j,i)] for all j) == supply_demand[i]`.
- This ensures the net outflow (outgoing minus incoming) equals the node's specified net supply or demand.

### Step 4 - Formulate the Objective
- Define the objective to minimize total transportation cost: `sum(cost[(i,j)] * x[(i,j)] for all arcs (i,j))`.

### Formulation Template
```json
{
  "sets": {
    "nodes": ["list of node identifiers"],
    "arcs": ["list of (from_node, to_node) tuples"]
  },
  "parameters": {
    "supply_demand": {"node_id": numeric_value},
    "cost": {"(from_node, to_node)": unit_cost},
    "capacity": {"(from_node, to_node)": max_flow}
  },
  "decision_variables": {
    "x": {"(from_node, to_node)": {"type": "continuous", "lb": 0, "ub": "capacity"}}
  },
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for all (i,j) in arcs)"
  },
  "constraints": {
    "flow_conservation": "for each node i: sum(x[i,j] for j) - sum(x[j,i] for j) == supply_demand[i]",
    "capacity": "for each arc (i,j): x[i,j] <= capacity[i,j]"
  }
}
```

### Common Pitfalls
- Incorrect sign in flow conservation: Using `inflow - outflow` instead of `outflow - inflow` for the supply convention.
- Forgetting to exclude self-loop arcs (`i==j`) from summations, which can lead to nonsensical solutions.
- Not verifying that total supply equals total demand (absolute values) before solving, which can cause infeasibility.

## Solving stage

### Strategy Overview
Build the LP model using a modeling library and solve it with a general-purpose linear programming solver (e.g., HiGHS, CBC, GLOP). Implement robust solution extraction and verification.

### Step 1 - Instantiate Solver
- Create a solver object (e.g., `SolverFactory('highs')` in Pyomo, `pywraplp.Solver.CreateSolver('GLOP')` in OR-Tools).
- Configure solver options such as time limit, optimality gap tolerance, and number of threads.

### Step 2 - Solve and Check Status
- Invoke the solver's `solve()` method.
- Check both the solver status (e.g., `SolverStatus.ok`) and the termination condition (e.g., `TerminationCondition.optimal`). Proceed only if the solution is optimal or feasible.

### Step 3 - Extract and Verify Solution
- Extract the objective value and the flow values for all arcs.
- Filter flows using a small tolerance (e.g., `> 1e-6`) to identify non-zero shipments.
- Programmatically verify flow conservation at each node and ensure no flow exceeds its capacity.

### Step 4 - Output Structured Results
- Print the total cost, a list of active flows (source, destination, amount), and the result of the verification checks.
- If the solver did not find an optimal/feasible solution, output a clear error message with the solver status.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# Define sets, parameters, variables, constraints, and objective as per modeling steps.
# ... (model construction code) ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, options={'time_limit': 30})

# Check solution status
if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        total_cost = pyo.value(model.obj)
        # Extract and print non-zero flows
        for (i,j), var in model.x.items():
            flow_val = pyo.value(var)
            if flow_val > 1e-6:
                print(f"Flow from {i} to {j}: {flow_val}")
        print(f"Total Cost: {total_cost}")
    else:
        print(f"Solver terminated with condition: {results.solver.termination_condition}")
else:
    print("Solver failed.")
```

### Common Pitfalls
- Assuming a `solve()` call without errors means an optimal solution was found. Always check the termination condition.
- Not using a tolerance when checking flow conservation or identifying non-zero flows, leading to false failures due to floating-point arithmetic.
- Forgetting to convert Pyomo variable values to floats using `pyo.value()` before using them in calculations.

# Workflow 2 (Specialized Network Flow Solver)

## Modeling stage

### Strategy Overview
Use a dedicated algorithm and API specifically designed for minimum cost flow problems (e.g., OR-Tools `SimpleMinCostFlow`). This method is often more efficient and requires less manual model construction.

### Step 1 - Define Network Data
- Define the same core elements: nodes with net supply/demand, and arcs with unit cost and capacity.
- Ensure the data is structured for the solver's API, typically as lists or arrays indexed by node and arc numbers.

### Step 2 - Map to Solver Primitives
- Map your graph nodes to consecutive integer indices starting from 0, as required by most network flow solvers.
- Prepare lists for arc definitions: `tail` (source node index), `head` (sink node index), `capacity`, and `unit_cost`.

### Step 3 - Adhere to Solver Convention
- Use the solver's specific convention for supply/demand: positive values indicate supply (net outflow), negative values indicate demand (net inflow).
- The solver internally enforces flow conservation and capacity constraints based on the provided data.

### Step 4 - Formulate the Objective
- The objective to minimize total cost is implicit in the solver's algorithm; you provide the unit costs for each arc.

### Formulation Template
```json
{
  "sets": {
    "nodes": ["list of node identifiers"],
    "arcs": ["list of (from_node, to_node) tuples"]
  },
  "parameters": {
    "supply_demand": {"node_id": numeric_value},
    "cost": {"(from_node, to_node)": unit_cost},
    "capacity": {"(from_node, to_node)": max_flow}
  },
  "decision_variables": {
    "implicit_flow": "Handled internally by the solver."
  },
  "objective": {
    "sense": "min",
    "expression": "Implicitly minimized by the solver based on arc costs."
  },
  "constraints": {
    "flow_conservation": "Enforced internally by the solver.",
    "capacity": "Enforced internally based on provided arc capacities."
  }
}
```

### Common Pitfalls
- Providing supply/demand values with the wrong sign convention for the specific solver library.
- Not ensuring that the sum of all node supplies is zero (feasibility condition), which may cause the solver to fail.
- Assuming the solver's internal arc indexing matches your original data order when retrieving flows.

## Solving stage

### Strategy Overview
Utilize the specialized solver's API to add arcs, set node supplies, and solve. Trust the solver's optimality guarantee for this convex problem class, but still verify the solution's basic feasibility.

### Step 1 - Initialize Solver Object
- Create an instance of the specialized solver (e.g., `SimpleMinCostFlow()`).
- Use the solver's methods to add arcs (`add_arc_with_capacity_and_unit_cost`) and set node supplies (`set_node_supply`).

### Step 2 - Solve and Interpret Status
- Call the solver's `solve()` method.
- Check the returned status against the solver's defined constants (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`). Only extract results for optimal or feasible statuses.

### Step 3 - Extract Flows and Cost
- Retrieve the optimal total cost directly via a solver method (e.g., `optimal_cost()`).
- Iterate through all arcs (using the solver's internal arc count) and retrieve the flow value for each. Filter for non-zero flows for reporting.

### Step 4 - Perform Basic Validation
- Even though the solver guarantees feasibility, perform a quick sanity check: ensure retrieved flows are non-negative and do not exceed provided capacities.
- Optionally, recompute the total cost from extracted flows and unit costs to cross-validate.

### Code Usage
```python
# build model from formulation
from ortools.graph import pywrapgraph
# Initialize solver
min_cost_flow = pywrapgraph.SimpleMinCostFlow()

# Add arcs (tail, head, capacity, unit cost)
for arc_id, (tail, head, cap, cost) in enumerate(arc_data_list):
    min_cost_flow.AddArcWithCapacityAndUnitCost(tail, head, cap, cost)

# Set node supplies (positive = supply, negative = demand)
for node_idx, supply_val in enumerate(supply_list):
    min_cost_flow.SetNodeSupply(node_idx, supply_val)

# solve with status / termination checks
status = min_cost_flow.Solve()
if status == min_cost_flow.OPTIMAL:
    total_cost = min_cost_flow.OptimalCost()
    print(f"Total Cost: {total_cost}")
    # Extract and print non-zero flows
    for i in range(min_cost_flow.NumArcs()):
        flow = min_cost_flow.Flow(i)
        if flow > 0:
            tail = min_cost_flow.Tail(i)
            head = min_cost_flow.Head(i)
            print(f"Flow from node {tail} to node {head}: {flow}")
elif status == min_cost_flow.FEASIBLE:
    print("A feasible solution found, but may not be optimal.")
else:
    print("Solver could not find a feasible solution.")
```

### Common Pitfalls
- Misinterpreting the solver status codes. `FEASIBLE` may not mean `OPTIMAL`; treat them differently.
- Assuming the order of arcs returned by the solver (`Tail(i)`, `Head(i)`) matches the order in which they were added. Use the returned indices (`tail`, `head`) for identification.
- Not handling the case where the sum of supplies is non-zero, which leads to an infeasible problem for a pure flow conservation model.
