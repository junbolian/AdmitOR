---
name: Binary Arc Selection with Flow Conservation
description: |
  Model and solve binary arc selection problems with flow conservation constraints using either specialized network flow solvers or general-purpose MILP frameworks.

---

# Workflow 1 (Specialized Min-Cost Flow)

## Modeling stage

### Strategy Overview
Leverage a specialized min-cost flow solver to model binary arc selection as a unit-capacity flow problem. This approach encodes the binary decision implicitly via arc capacities, eliminating the need for explicit binary variables and linking constraints.

### Step 1 - Map Problem to Network Flow
- Identify the set of nodes and all possible directed arcs between them.
- Define a cost parameter for each arc, representing the cost of using it.
- Determine the source node (supply) and sink node (demand) for the single commodity flow.

### Step 2 - Enforce Binary Selection via Unit Capacity
- Assign a capacity of 1 to every arc. This ensures each arc can carry at most one unit of flow, making its usage binary (0 or 1).
- The total flow amount from source to sink is set to 1, forcing the solver to select a single path.

### Step 3 - Formulate Flow Conservation
- Set the supply at the source node to +1 (or the total flow amount).
- Set the demand at the sink node to -1 (or the negative of the total flow amount).
- Set the supply/demand for all intermediate (transshipment) nodes to 0.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i, j) where i, j ∈ N and i ≠ j"
  ],
  "parameters": [
    "c_{ij}: cost of using arc (i, j) for all (i, j) in A",
    "source: node identifier for flow origin",
    "sink: node identifier for flow destination",
    "flow_amount: total amount of flow to route (typically 1)"
  ],
  "decision_variables": [
    "Implicit binary selection via flow variable f_{ij} (0 or flow_amount), bounded by capacity 1."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j) in A} c_{ij} * f_{ij}"
  },
  "constraints": [
    "Flow conservation: For each node n in N, ∑_{(i,n) in A} f_{i,n} - ∑_{(n,j) in A} f_{n,j} = supply_n, where supply_source = flow_amount, supply_sink = -flow_amount, and supply_n = 0 otherwise.",
    "Capacity: 0 ≤ f_{ij} ≤ 1 for all (i,j) in A."
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loop arcs (i,i) from the arc set, which can lead to trivial, invalid solutions.
- Mismatching supply/demand signs, causing infeasibility (e.g., setting source supply to -1).
- Using a flow_amount greater than 1 while keeping unit capacities, which makes the problem infeasible.

## Solving stage

### Strategy Overview
Use a dedicated min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) which is optimized for this problem class. The solving stage involves building the network, setting parameters, invoking the solver, and rigorously checking the solution status.

### Step 1 - Initialize Solver and Build Network
- Instantiate the specialized min-cost flow solver object.
- Add all arcs to the solver using the `add_arc_with_capacity_and_unit_cost` method, specifying tail node, head node, capacity (1), and cost.
- Set node supplies using `set_node_supply`.

### Step 2 - Solve and Validate Status
- Call the solver's `solve` method or equivalent.
- Check the return status is `OPTIMAL` (or a similar success code). If not, handle the error (e.g., report infeasibility).

### Step 3 - Extract and Interpret Solution
- Retrieve the total optimal cost from the solver.
- Iterate over all arcs, checking if the flow value is positive (e.g., `flow(arc_id) > 0.5`) to identify selected arcs.
- Reconstruct the selected path from source to sink using the flow values.

### Code Usage
```python
# Example using OR-Tools SimpleMinCostFlow
from ortools.graph.python import min_cost_flow

# 1. Initialize solver
solver = min_cost_flow.SimpleMinCostFlow()

# 2. Build network: Add arcs (placeholder: NODES, ARCS, COSTS are defined)
for (i, j), cost in COSTS.items():
    # Capacity 1 enforces binary selection for unit flow
    solver.add_arc_with_capacity_and_unit_cost(i, j, 1, cost)

# 3. Set node supplies
for node in NODES:
    supply = 0
    if node == SOURCE_NODE:
        supply = FLOW_AMOUNT  # e.g., 1
    elif node == SINK_NODE:
        supply = -FLOW_AMOUNT
    solver.set_node_supply(node, supply)

# 4. Solve and check status
status = solver.solve()
if status != solver.OPTIMAL:
    raise Exception(f"Solver did not find an optimal solution. Status: {status}")

# 5. Extract results
total_cost = solver.optimal_cost()
selected_arcs = []
for arc_id in range(solver.num_arcs()):
    if solver.flow(arc_id) > 0.5:  # Arc is used
        tail = solver.tail(arc_id)
        head = solver.head(arc_id)
        selected_arcs.append((tail, head))

print(f"Optimal cost: {total_cost}")
print(f"Selected arcs: {selected_arcs}")
```

### Common Pitfalls
- Not verifying the solver status before extracting results, leading to errors or incorrect interpretation.
- Assuming the flow value will be exactly 1.0 for selected arcs; use a tolerance (e.g., `> 0.5`) for robustness.
- Incorrectly mapping arc indices back to (tail, head) pairs if the solver API requires it for interpretation.

# Workflow 2 (General MILP with Explicit Binary Variables)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) with explicit binary variables for arc selection and continuous variables for flow. This provides maximum flexibility and clarity, allowing for easy extension with additional constraints.

### Step 1 - Define Sets and Parameters
- Define the set of nodes and the set of feasible directed arcs.
- Define a cost parameter for each arc, representing the fixed charge for its activation.

### Step 2 - Create Decision Variables
- Create binary variables `x[i,j]` ∈ {0,1} for arc activation.
- Create continuous non-negative variables `f[i,j]` for flow on each arc.

### Step 3 - Formulate Linking and Flow Constraints
- Link flow and activation variables: `f[i,j] <= M * x[i,j]`, where M is a sufficiently large number (e.g., the total flow amount).
- Enforce flow conservation at each node: inflow - outflow = supply/demand.
- Set supply at source and demand at sink.

### Step 4 - Define Linear Cost Objective
- Minimize the total fixed cost of activated arcs: `min sum( c[i,j] * x[i,j] )`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i, j) where i, j ∈ N and i ≠ j"
  ],
  "parameters": [
    "c_{ij}: fixed cost of activating arc (i, j) for all (i, j) in A",
    "source: node identifier for flow origin",
    "sink: node identifier for flow destination",
    "flow_amount: total amount of flow to route",
    "M: big-M constant (typically >= flow_amount)"
  ],
  "decision_variables": [
    "x_{ij} ∈ {0, 1}: binary variable for arc (i,j) activation",
    "f_{ij} ≥ 0: continuous variable for flow on arc (i,j)"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j) in A} c_{ij} * x_{ij}"
  },
  "constraints": [
    "Linking: f_{ij} ≤ M * x_{ij} for all (i,j) in A",
    "Flow conservation: For each node n in N, ∑_{(i,n) in A} f_{i,n} - ∑_{(n,j) in A} f_{n,j} = supply_n, where supply_source = flow_amount, supply_sink = -flow_amount, and supply_n = 0 otherwise.",
    "Non-negativity: f_{ij} ≥ 0 for all (i,j) in A"
  ]
}
```

### Common Pitfalls
- Choosing an unnecessarily small or excessively large value for `M` in the linking constraint, which can weaken the LP relaxation or cause numerical instability.
- Omitting the linking constraint, allowing flow on inactive arcs.
- Forgetting to enforce `i != j` when generating the arc set, which can create invalid self-loops.

## Solving stage

### Strategy Overview
Use a general-purpose MILP solver (e.g., via Pyomo with HiGHS/Gurobi/CBC) to solve the explicit binary formulation. The process involves building the model, configuring the solver, solving, and performing comprehensive status checks.

### Step 1 - Instantiate Model and Solver Factory
- Create a concrete or abstract model object using a modeling framework (e.g., Pyomo).
- Instantiate a solver factory for the chosen backend (e.g., `SolverFactory("highs")`).

### Step 2 - Configure Solver Parameters
- Set key parameters such as time limit, optimality gap tolerance (e.g., `mip_rel_gap = 0.0` for exact solution), and number of threads.
- Set a random seed for reproducibility if the solver supports it.

### Step 3 - Solve and Validate Termination
- Invoke the solver's `solve` method on the model.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`optimal` or `feasible`).

### Step 4 - Extract and Verify Solution
- Retrieve the objective value from the model.
- Extract the values of binary variables `x[i,j]` to identify selected arcs (value > 0.5).
- Optionally, verify that the flow variables `f[i,j]` form a feasible path from source to sink.

### Code Usage
```python
# Example using Pyomo with a generic MILP solver
import pyomo.environ as pyo

# 1. Create model
model = pyo.ConcreteModel()

# 2. Define sets (placeholder: NODES, ARCS are defined)
model.N = pyo.Set(initialize=NODES)
model.A = pyo.Set(initialize=ARCS, dimen=2)

# 3. Define parameters (placeholder: COSTS, SOURCE, SINK, FLOW_AMOUNT, M are defined)
model.c = pyo.Param(model.A, initialize=COSTS)
model.M = pyo.Param(initialize=M)

# 4. Define variables
model.x = pyo.Var(model.A, domain=pyo.Binary)  # Arc activation
model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)  # Flow

# 5. Define objective
def obj_rule(model):
    return sum(model.c[i, j] * model.x[i, j] for (i, j) in model.A)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# 6. Define linking constraints
def link_rule(model, i, j):
    return model.f[i, j] <= model.M * model.x[i, j]
model.link_constr = pyo.Constraint(model.A, rule=link_rule)

# 7. Define flow balance constraints
def balance_rule(model, n):
    inflow = sum(model.f[i, n] for (i, j) in model.A if j == n)
    outflow = sum(model.f[n, j] for (i, j) in model.A if i == n)
    supply = 0
    if n == SOURCE:
        supply = FLOW_AMOUNT
    elif n == SINK:
        supply = -FLOW_AMOUNT
    return inflow - outflow == supply
model.balance_constr = pyo.Constraint(model.N, rule=balance_rule)

# 8. Solve
solver = pyo.SolverFactory("highs")  # Or "gurobi", "cbc"
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = -0.0
results = solver.solve(model, tee=False)

# 9. Check status
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # 10. Extract results
    total_cost = pyo.value(model.obj)
    selected_arcs = [(i, j) for (i, j) in model.A if pyo.value(model.x[i, j]) > 0.5]
    print(f"Optimal cost: {total_cost}")
    print(f"Selected arcs: {selected_arcs}")
else:
    print("Solver did not return an optimal or feasible solution.")
```

### Common Pitfalls
- Failing to check both the solver status and termination condition, potentially accepting suboptimal or invalid results.
- Not using a tolerance (e.g., `> 0.5`) when evaluating binary variable values due to solver precision.
- Neglecting to set a time limit or optimality gap, which can lead to excessively long run times for large instances.
