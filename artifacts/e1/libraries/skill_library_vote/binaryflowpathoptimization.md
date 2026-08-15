---
name: BinaryFlowPathOptimization
description: |
  Model and solve minimum-cost binary flow problems on directed networks with single source and sink, using either MIP or specialized network flow solvers.
---

# Workflow 1 (MIP-based Binary Flow)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Program (MIP) with binary arc variables, suitable for general-purpose solvers like CBC or SCIP. It directly encodes flow conservation and binary selection, providing a flexible and verifiable formulation.

### Step 1 - Define Network and Parameters
- Enumerate all nodes and directed arcs (i, j) where i ≠ j.
- Assign a unit cost parameter `c_ij` to each arc.
- Define a net supply parameter `b_i` for each node: +1 for source, -1 for sink, 0 for transshipment nodes.

### Step 2 - Create Binary Decision Variables
- Create a binary decision variable `x_ij` for each arc, where `x_ij = 1` if the arc is used in the flow path, and `0` otherwise.

### Step 3 - Formulate Flow Conservation Constraints
- For each node `i`, enforce the flow balance constraint: Σ_{(i,j) in arcs} x_ij - Σ_{(j,i) in arcs} x_ji = b_i.
- This single constraint type handles source supply, sink demand, and transshipment node balance.

### Step 4 - Set Objective Function
- Minimize the total cost: Σ_{(i,j) in arcs} c_ij * x_ij.

### Formulation Template
```json
{
  "sets": [
    "N (nodes)",
    "A (arcs, subset of N × N, i ≠ j)"
  ],
  "parameters": [
    "c_ij (unit cost for arc (i,j) in A)",
    "b_i (net supply at node i in N; Σ_i b_i = 0)"
  ],
  "decision_variables": [
    "x_ij (binary, 1 if arc (i,j) is used)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{ (i,j) in A } c_ij * x_ij"
  },
  "constraints": [
    "flow_conservation_i: sum_{ (i,j) in A } x_ij - sum_{ (j,i) in A } x_ji = b_i, for all i in N"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops (i,i) from the arc set, which can lead to degenerate solutions.
- Incorrectly signing the net supply parameter `b_i` (e.g., using +1 for sink instead of source).
- Assuming the solver will automatically handle binary variable integrality without explicit declaration.

## Solving stage

### Strategy Overview
Solve the MIP model using an open-source solver (e.g., CBC via Pyomo) with configuration for binary problems. Implement robust solution status checks and post-solution validation.

### Step 1 - Instantiate Solver and Set Parameters
- Instantiate a MIP solver (e.g., `SolverFactory('cbc')`).
- Set a time limit (e.g., `seconds=30`).
- Set an optimality gap tolerance (e.g., `ratio=0.0` for optimality).
- Configure parallel threads if available (e.g., `threads=-1`).

### Step 2 - Solve and Check Status
- Execute the solve command.
- Check both the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`). Proceed only if both indicate a valid solution.

### Step 3 - Extract and Interpret Solution
- For each binary variable `x_ij`, retrieve its value. Arcs with `value > 0.5` are considered selected.
- The selected arcs should form a single directed path from source to sink.
- Compute the objective value from the solution: sum of `c_ij` for selected arcs.

### Step 4 - Validate Solution
- Recompute flow conservation at each node using the selected arcs to verify it matches `b_i`.
- For small networks, consider brute-force enumeration to verify optimality.

### Code Usage
```python
import pyomo.environ as pyo

# build model from formulation
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=node_list)
model.A = pyo.Set(within=model.N*model.N, initialize=arcs_list, filter=lambda m, i, j: i != j)
model.c = pyo.Param(model.A, initialize=cost_dict)
model.b = pyo.Param(model.N, initialize=supply_dict)
model.x = pyo.Var(model.A, domain=pyo.Binary)

def obj_rule(m):
    return pyo.sum(m.c[i,j] * m.x[i,j] for (i,j) in m.A)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def flow_cons_rule(m, i):
    outflow = pyo.sum(m.x[i,j] for j in m.N if (i,j) in m.A)
    inflow = pyo.sum(m.x[j,i] for j in m.N if (j,i) in m.A)
    return outflow - inflow == m.b[i]
model.flow_conservation = pyo.Constraint(model.N, rule=flow_cons_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    # Extract solution
    used_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.x[i,j]) > 0.5]
    total_cost = pyo.value(model.obj)
else:
    # Handle infeasible or error state
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to misinterpretation of infeasible or unbounded results.
- Using a floating-point equality check (e.g., `value == 1.0`) for binary variables; use a tolerance (e.g., `> 0.5`).
- Omitting post-solution validation, which can miss modeling errors.

# Workflow 2 (Specialized Network Flow Solver)

## Modeling stage

### Strategy Overview
This workflow uses a specialized minimum-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) that exploits the network structure. It models arcs with unit capacity and uses node supplies to enforce flow conservation, often yielding faster solves.

### Step 1 - Map to Network Flow Structure
- Recognize the problem as a unit-capacity flow from a single source to a single sink.
- All other nodes are transshipment nodes with zero net supply.

### Step 2 - Define Arcs with Unit Capacity
- For each directed arc (i, j) where i ≠ j, define it with a capacity of 1 and a unit cost `c_ij`.
- The unit capacity enforces the binary "use or not use" behavior.

### Step 3 - Set Node Supplies
- Set the supply at the source node to the total flow amount (e.g., +1).
- Set the supply at the sink node to the negative of the total flow amount (e.g., -1).
- Set the supply at all transshipment nodes to 0.

### Formulation Template
```json
{
  "sets": [
    "N (nodes)",
    "A (arcs, subset of N × N, i ≠ j)"
  ],
  "parameters": [
    "c_ij (unit cost for arc (i,j) in A)",
    "supply_i (net flow for node i; source > 0, sink < 0, others = 0)"
  ],
  "decision_variables": [
    "flow_ij (integer flow on arc (i,j), will be 0 or 1 due to capacity)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{ (i,j) in A } c_ij * flow_ij"
  },
  "constraints": [
    "capacity: 0 <= flow_ij <= 1, for all (i,j) in A",
    "flow_conservation: sum_{ (i,j) in A } flow_ij - sum_{ (j,i) in A } flow_ji = supply_i, for all i in N"
  ]
}
```

### Common Pitfalls
- Using a solver not designed for integer flows, which may return fractional solutions.
- Incorrectly setting the sink node supply as a positive value.
- Adding self-loop arcs, which can cause solver errors or incorrect solutions.

## Solving stage

### Strategy Overview
Utilize a dedicated network flow algorithm via an API like OR-Tools. This approach is efficient for unit-capacity problems and handles integrality guarantees internally.

### Step 1 - Initialize Network Flow Solver
- Create an instance of a min-cost flow solver (e.g., `SimpleMinCostFlow()`).

### Step 2 - Add Arcs and Set Parameters
- For each arc (i, j), add it to the solver with `capacity=1` and `unit_cost=c_ij`.
- Use `set_node_supply(node_index, supply_value)` for all nodes.

### Step 3 - Solve and Check Optimality
- Call the solver's `solve()` method.
- Check the return status against the solver's `OPTIMAL` constant. Handle non-optimal statuses (e.g., `INFEASIBLE`) appropriately.

### Step 4 - Extract Integral Flow Solution
- Query the flow on each arc using the solver's `flow(arc_index)` method.
- Arcs with `flow > 0` (typically 1) are part of the selected path.
- Retrieve the total cost via `optimal_cost()`.

### Code Usage
```python
from ortools.graph.python import min_cost_flow

# build model from formulation
smcf = min_cost_flow.SimpleMinCostFlow()

# Add arcs (exclude self-loops)
arc_index = {}
for i in node_set:
    for j in node_set:
        if i != j:
            arc_id = smcf.add_arc_with_capacity_and_unit_cost(
                tail=i,
                head=j,
                capacity=1,
                unit_cost=cost_matrix[i][j]
            )
            arc_index[(i, j)] = arc_id

# Set node supplies
smcf.set_node_supply(source_node, supply_amount)
smcf.set_node_supply(sink_node, -supply_amount)
for n in transshipment_nodes:
    smcf.set_node_supply(n, -0)

# solve with status / termination checks
status = smcf.solve()
if status == smcf.OPTIMAL:
    total_cost = smcf.optimal_cost()
    used_arcs = []
    for i in range(smcf.num_arcs()):
        if smcf.flow(i) > 0:
            tail = smcf.tail(i)
            head = smcf.head(i)
            used_arcs.append((tail, head, smcf.unit_cost(i)))
else:
    # Handle infeasible or other status
    print(f"Solver returned non-optimal status: {status}")
```

### Common Pitfalls
- Assuming the solver status is an integer matching a generic code; always compare to the solver's own `OPTIMAL` attribute.
- Not verifying that the extracted flow values are integral (0 or 1), though they should be for unit capacities.
- Forgetting to set supplies for transshipment nodes (should be set to 0 explicitly).
