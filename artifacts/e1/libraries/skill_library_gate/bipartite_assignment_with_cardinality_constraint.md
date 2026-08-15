---
name: Bipartite Assignment with Cardinality Constraint
description: |
  Model and solve bipartite assignment problems with at-most-one matching constraints and a fixed total number of assignments, using either network flow or integer programming approaches.
---

# Workflow 1 (Network Flow via OR-Tools)

## Modeling stage

### Strategy Overview
Transform the bipartite assignment problem into a minimum cost flow problem on a constructed network. This leverages efficient polynomial-time algorithms for network flow, suitable for larger instances.

### Step 1 - Define Network Structure
- Identify two disjoint sets: `SetA` and `SetB`.
- Construct a flow network with nodes: source, all nodes in `SetA`, all nodes in `SetB`, and sink.
- Define arcs: source → `SetA` (capacity 1, cost 0), `SetA` → `SetB` (capacity 1, cost = assignment cost), `SetB` → sink (capacity 1, cost 0).

### Step 2 - Enforce Constraints via Supplies and Capacities
- Set the source node supply to `k`, the required total number of assignments.
- Set the sink node demand to `-k`.
- Set all intermediate node supplies to 0.
- Arc capacities of 1 enforce the at-most-one matching constraints per element.

### Formulation Template
```json
{
  "sets": ["SetA", "SetB"],
  "parameters": ["cost_matrix[SetA][SetB]", "k"],
  "decision_variables": ["flow[arcs]"],
  "objective": {
    "sense": "min",
    "expression": "sum( cost(arc) * flow(arc) for all arcs )"
  },
  "constraints": [
    "flow conservation at each node",
    "0 <= flow(arc) <= capacity(arc)",
    "total flow from source = k"
  ]
}
```

### Common Pitfalls
- Forgetting to scale fractional costs to integers for the integer flow solver, leading to precision errors.
- Incorrect node indexing causing misalignment between arcs and original set elements.
- Setting arc capacities >1, which violates the one-to-one matching requirement.

## Solving stage

### Strategy Overview
Use OR-Tools' `SimpleMinCostFlow` solver to find the optimal flow. Extract the solution by identifying arcs with positive flow between the two sets.

### Step 1 - Build and Solve the Flow Model
- Instantiate the `SimpleMinCostFlow` object.
- Add arcs using the defined network structure and scaled integer costs.
- Set node supplies as defined in the modeling stage.
- Call the `solve()` method and check for an `OPTIMAL` status.

### Step 2 - Extract and Map the Assignment Solution
- Iterate over all arcs in the solved model.
- Filter for arcs with `flow > 0` that connect a node in `SetA` to a node in `SetB`.
- Map the solver's internal node indices back to the original element indices in `SetA` and `SetB`.

### Code Usage
```python
from ortools.graph import pywrapgraph

# Build model from formulation
smcf = pywrapgraph.SimpleMinCostFlow()
# Define indices: source=0, SetA=1..n, SetA_offset=n, SetB=n+1..n+m, sink=n+m+1
# Add arcs: source->SetA, SetA->SetB, SetB->sink
# Scale fractional costs: scaled_cost = int(cost * SCALING_FACTOR)
# Set node supplies: smcf.SetNodeSupply(source_idx, k), smcf.SetNodeSupply(sink_idx, -k)

# Solve with status / termination checks
if smcf.Solve() == smcf.OPTIMAL:
    total_cost = smcf.OptimalCost() / SCALING_FACTOR  # Rescale cost
    assignments = []
    for arc in range(smcf.NumArcs()):
        if smcf.Flow(arc) > 0:
            tail, head = smcf.Tail(arc), smcf.Head(arc)
            # Filter for arcs from SetA to SetB based on index ranges
            if 1 <= tail <= n and n+1 <= head <= n+m:
                a_idx = tail - 1
                b_idx = head - (n + 1)
                assignments.append((a_idx, b_idx))
else:
    raise Exception("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Not handling the solver status, leading to errors when trying to extract an invalid solution.
- Forgetting to rescale the optimal cost back to its original units after solving.
- Incorrectly filtering arcs, potentially including source or sink connections in the assignment list.

# Workflow 2 (Integer Programming via Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem directly as a Mixed-Integer Program (MIP) using binary assignment variables. This approach provides explicit control over constraints and is highly portable across different solvers.

### Step 1 - Define Variables and Parameters
- Create a binary decision variable `x[i,j]` for each possible assignment between `i` in `SetA` and `j` in `SetB`.
- Define a parameter `cost[i,j]` representing the assignment cost matrix.

### Step 2 - Implement Matching and Cardinality Constraints
- Add constraints ensuring each element in `SetA` is assigned to at most one element in `SetB`: `sum(x[i,j] for j in SetB) <= 1`.
- Add symmetric constraints for `SetB`: `sum(x[i,j] for i in SetA) <= 1`.
- Enforce the exact total number of assignments: `sum(x[i,j] for i in SetA for j in SetB) == k`.

### Formulation Template
```json
{
  "sets": ["SetA", "SetB"],
  "parameters": ["cost[SetA][SetB]", "k"],
  "decision_variables": ["x[SetA][SetB] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i,j] * x[i,j] for i in SetA, j in SetB )"
  },
  "constraints": [
    "sum(x[i,j] for j in SetB) <= 1, for all i in SetA",
    "sum(x[i,j] for i in SetA) <= 1, for all j in SetB",
    "sum(x[i,j] for i in SetA, j in SetB) == k"
  ]
}
```

### Common Pitfalls
- Creating a fully dense variable matrix for very large sets, leading to model bloat; consider sparsity if applicable.
- Mis-indexing parameters and variables within constraint rules.
- Forgetting to set the objective sense to minimization.

## Solving stage

### Strategy Overview
Use a MIP solver (e.g., HiGHS, GLPK, CBC) via the Pyomo interface. Implement robust error handling to manage solver availability and termination conditions.

### Step 1 - Instantiate Solver and Solve
- Create a Pyomo `ConcreteModel` containing the formulated variables, constraints, and objective.
- Instantiate a solver object (e.g., `SolverFactory('highs')`).
- Call the solver's `solve()` method on the model within a try-except block.

### Step 2 - Validate and Extract Solution
- Check the solver status and termination condition to confirm an optimal or feasible solution was found.
- Extract the objective value.
- Iterate over the binary variables `x[i,j]` and collect those with a solution value > 0.5 as the active assignments.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# Build model from formulation
m = pyo.ConcreteModel()
m.SetA = pyo.Set(initialize=SetA_list)
m.SetB = pyo.Set(initialize=SetB_list)
m.cost = pyo.Param(m.SetA, m.SetB, initialize=cost_data)
m.x = pyo.Var(m.SetA, m.SetB, domain=pyo.Binary)
m.obj = pyo.Objective(expr=sum(m.cost[i,j] * m.x[i,j] for i in m.SetA for j in m.SetB), sense=pyo.minimize)
# Add constraints as per formulation

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')  # Can substitute 'glpk' or 'cbc'
try:
    results = solver.solve(m, tee=False)
    status = results.solver.status
    term = results.solver.termination_condition

    if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
        obj_val = float(pyo.value(m.obj))
        assignments = [(i, j) for i in m.SetA for j in m.SetB if pyo.value(m.x[i, j]) > 0.5]
        print(f"RESULT:{obj_val}")
        # Output assignments
    else:
        print(f"RESULT_JSON:{json.dumps({'status':'failed','reason':'infeasible_or_error','solver_status':str(status),'termination_condition':str(term)})}")
except Exception as e:
    print(f"RESULT_JSON:{json.dumps({'status':'error','reason':str(e)})}")
```

### Common Pitfalls
- Assuming solver availability without a fallback plan; always have an alternative solver (e.g., GLPK) specified.
- Not checking termination conditions, potentially accepting suboptimal or invalid solutions.
- Comparing floating-point solution values directly to 1.0; use a tolerance (e.g., > 0.5).
