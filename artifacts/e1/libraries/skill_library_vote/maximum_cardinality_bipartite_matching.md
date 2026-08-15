---
name: Maximum Cardinality Bipartite Matching
description: |
  Model and solve one-to-one assignment problems between two disjoint sets with preference restrictions, maximizing the total number of matches.
---

# Workflow 1 (MILP Formulation)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using binary assignment variables. This approach is flexible, solver-agnostic, and easily extensible to include additional constraints like costs or fairness.

### Step 1 - Identify Problem Structure
- Recognize the presence of two disjoint sets (e.g., `SetA` and `SetB`) where elements from one set can be matched to at most one element from the other.
- Identify a binary compatibility matrix (`preference[i][j]`) that defines admissible matches between elements of `SetA` and `SetB`.

### Step 2 - Define Core Model Components
- **Sets**: Define index sets for `SetA` and `SetB`.
- **Parameters**: Define a binary parameter `preference[i][j]` (1 if match is allowed, 0 otherwise).
- **Decision Variables**: Create a binary variable `assign[i][j]` for each potential match.
- **Objective**: Maximize the sum of all assignment variables: `maximize sum(assign[i][j] for i in SetA, j in SetB)`.
- **Constraints**:
    - **One-to-One (SetA)**: `sum(assign[i][j] for j in SetB) <= 1` for each `i` in `SetA`.
    - **One-to-One (SetB)**: `sum(assign[i][j] for i in SetA) <= 1` for each `j` in `SetB`.
    - **Preference Admissibility**: `assign[i][j] <= preference[i][j]` for all `i, j`.

### Formulation Template
```json
{
  "sets": ["SetA_indices", "SetB_indices"],
  "parameters": [
    {"name": "preference", "type": "binary", "indices": ["SetA_indices", "SetB_indices"], "description": "1 if match is allowed, 0 otherwise"}
  ],
  "decision_variables": [
    {"name": "assign", "type": "binary", "indices": ["SetA_indices", "SetB_indices"], "description": "1 if element i from SetA is matched to element j from SetB"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(assign[i][j] for i in SetA_indices for j in SetB_indices)"
  },
  "constraints": [
    {"name": "one_per_element_setA", "expression": "sum(assign[i][j] for j in SetB_indices) <= 1", "for_each": "i in SetA_indices"},
    {"name": "one_per_element_setB", "expression": "sum(assign[i][j] for i in SetA_indices) <= 1", "for_each": "j in SetB_indices"},
    {"name": "respect_preferences", "expression": "assign[i][j] <= preference[i][j]", "for_each": "i in SetA_indices, j in SetB_indices"}
  ]
}
```

### Common Pitfalls
- Forgetting to enforce `assign[i][j] <= preference[i][j]`, which can lead to matches on incompatible pairs.
- Using `== 1` instead of `<= 1` in the one-to-one constraints, which forces all elements to be matched and can cause infeasibility.
- Not verifying that the `preference` parameter is binary (0/1); non-binary values can break the admissibility constraint logic.

## Solving stage

### Strategy Overview
Solve the MILP using a standard integer programming solver (e.g., HiGHS, CBC, Gurobi). Configure the solver for an exact solution, implement robust status checking, and extract the matching pairs from the solved model.

### Step 1 - Select and Configure Solver
- Choose an appropriate MILP solver available in your modeling framework (e.g., `highs` for Pyomo, `CBC` for PuLP).
- Configure key parameters: set a time limit (`time_limit`), optimality gap to zero (`mip_rel_gap = 0.0`), and enable parallel threads if desired.

### Step 2 - Solve and Check Status
- Invoke the solver on the model.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`optimal` or `feasible`). Proceed only if the solve was successful.

### Step 3 - Extract and Validate Solution
- Extract the objective value (total matches).
- Iterate over all `assign[i][j]` variables, collecting pairs where `value(assign[i][j]) > 0.5`.
- Perform a sanity check: verify that no element appears in more than one pair and that all matches are in the allowed set.

### Code Usage
```python
# Example using a generic modeling framework (conceptual)
solver = SolverFactory("solver_name")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = -1.0  # Use -1.0 or 0.0 for exact solution

results = solver.solve(model)

# Robust status checking
if results.solver.status == SolverStatus.ok and \
   results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_matches = value(model.obj)
    assignments = []
    for i in model.SetA:
        for j in model.SetB:
            if value(model.assign[i, j]) > 0.5:
                assignments.append((i, j))
    # Validate: check constraints manually if needed
else:
    # Handle solver failure (infeasible, error, etc.)
    print("Solver failed:", results.solver.termination_condition)
```

### Common Pitfalls
- Assuming a solution is optimal without checking the termination condition; a `feasible` status may indicate a suboptimal solution or a timeout.
- Using a loose `mip_rel_gap` (e.g., default 0.01) when an exact integer solution is required.
- Not handling solver failures gracefully, which can crash downstream processes.

# Workflow 2 (Network Flow Reduction)

## Modeling stage

### Strategy Overview
Reduce the bipartite matching problem to a maximum flow problem on a constructed network. This leverages specialized, polynomial-time algorithms and is often more efficient for pure cardinality matching without additional side constraints.

### Step 1 - Construct Flow Network Graph
- Create a directed graph with nodes: a `source`, all elements of `SetA`, all elements of `SetB`, and a `sink`.
- Add arcs with capacity 1:
    - From `source` to each node in `SetA`.
    - From each node in `SetA` to each node in `SetB` **only if** `preference[i][j] == 1`.
    - From each node in `SetB` to the `sink`.

### Step 2 - Map Solution to Original Problem
- The **maximum flow value** from `source` to `sink` equals the maximum number of matches.
- A **matching** is recovered by identifying arcs from `SetA` to `SetB` that carry positive flow (flow == 1).

### Formulation Template
```json
{
  "sets": ["SetA_indices", "SetB_indices"],
  "parameters": [
    {"name": "preference", "type": "binary", "indices": ["SetA_indices", "SetB_indices"], "description": "Defines which arcs exist from SetA to SetB"}
  ],
  "graph_structure": {
    "nodes": ["source", "SetA_nodes", "SetB_nodes", "sink"],
    "arcs": [
      {"from": "source", "to": "SetA_nodes", "capacity": 1},
      {"from": "SetA_nodes", "to": "SetB_nodes", "capacity": 1, "condition": "preference[i][j] == 1"},
      {"from": "SetB_nodes", "to": "sink", "capacity": 1}
    ]
  },
  "solution_mapping": "Arcs from SetA_nodes to SetB_nodes with flow == 1 correspond to matches."
}
```

### Common Pitfalls
- Incorrect node indexing leading to mismatches between original indices and graph node IDs.
- Forgetting to add arcs from `SetB` to the `sink`, which prevents any flow from reaching the sink.
- Assuming the graph library automatically handles parallel arcs; some max-flow implementations may require unique arc identifiers.

## Solving stage

### Strategy Overview
Use a dedicated maximum flow solver (e.g., OR-Tools `SimpleMaxFlow`) to find the maximum flow on the constructed network. Extract the flow solution and map it back to the original assignment pairs.

### Step 1 - Build the Flow Network in Solver
- Instantiate the max-flow solver object.
- Add all arcs using the solver's `add_arc_with_capacity(tail, head, capacity)` method, following the network structure defined in the modeling stage.
- Maintain a clear mapping between graph node indices and the original element identifiers from `SetA` and `SetB`.

### Step 2 - Solve and Verify Optimality
- Call the solver's `solve(source_node, sink_node)` method.
- Check that the solver status is `OPTIMAL` before proceeding.

### Step 3 - Extract Assignments from Flow
- Query the optimal flow value.
- Iterate through all arcs in the solved network.
- For each arc where `flow(arc) > 0`, check if its tail is in `SetA` and its head is in `SetB`. If so, decode the original indices and record the match.

### Code Usage
```python
# Example using OR-Tools SimpleMaxFlow
from ortools.graph.python import max_flow

# 1. Define node indices
#    Let nA = len(SetA), nB = len(SetB)
#    source = 0
#    SetA nodes: 1 .. nA
#    SetB nodes: nA+1 .. nA+nB
#    sink = nA + nB + 1
source = 0
sink = nA + nB + 1

# 2. Instantiate solver and build network
mf = max_flow.SimpleMaxFlow()

# Source -> SetA
for i_idx, i in enumerate(SetA, start=1):  # i_idx is graph node ID
    mf.add_arc_with_capacity(source, i_idx, 1)

# SetA -> SetB (only where preference allows)
for i_idx, i in enumerate(SetA, start=1):
    for j_idx, j in enumerate(SetB, start=nA+1):
        if preference[i][j] == 1:
            mf.add_arc_with_capacity(i_idx, j_idx, 1)

# SetB -> Sink
for j_idx, j in enumerate(SetB, start=nA+1):
    mf.add_arc_with_capacity(j_idx, sink, 1)

# 3. Solve
status = mf.solve(source, sink)

if status == mf.OPTIMAL:
    max_matches = mf.optimal_flow()
    assignments = []
    for arc in range(mf.num_arcs()):
        if mf.flow(arc) > 0:
            tail = mf.tail(arc)
            head = mf.head(arc)
            # Check if arc goes from SetA to SetB
            if 1 <= tail <= nA and nA+1 <= head <= nA+nB:
                orig_i = SetA[tail - 1]  # Map back to original ID
                orig_j = SetB[head - (nA + 1)]
                assignments.append((orig_i, orig_j))
else:
    # Handle non-optimal status
    print("Max flow solver did not find optimal solution.")
```

### Common Pitfalls
- Not checking the solver status (`OPTIMAL`) and assuming a valid flow was found.
- Incorrectly mapping graph node IDs back to original element identifiers, leading to wrong assignment pairs.
- Using a max-flow solver that does not guarantee integer flows with unit capacities; `SimpleMaxFlow` is safe for this.
