---
name: Maximum Bipartite Matching
description: |
  Model and solve one-to-one assignment problems between two disjoint sets with preference restrictions, maximizing the number of matches.
---

# Workflow 1 (CP-SAT for Binary Assignment)

## Modeling stage

### Strategy Overview
Formulate the problem as a binary integer program using explicit decision variables for each potential assignment, with constraints enforcing one-to-one matching and preference compatibility. This approach is flexible and allows for easy integration of additional side constraints.

### Step 1 - Define Sets and Parameters
- Identify the two disjoint sets, typically labeled as `left_set` and `right_set`.
- Define a binary `preference_matrix` or a list of allowed pairs `allowed_edges` to encode compatibility.
- Use integer indices for elements to simplify variable creation and constraint indexing.

### Step 2 - Create Binary Decision Variables
- Create a binary variable `x[i][j]` for each element `i` in `left_set` and `j` in `right_set`.
- Use `model.NewBoolVar(f"x_{i}_{j}")` to create variables, storing them in a dictionary or 2D list for easy access.

### Step 3 - Enforce One-to-One Matching Constraints
- For each element `i` in `left_set`, add constraint `sum(x[i][j] for j in right_set) <= 1`.
- For each element `j` in `right_set`, add constraint `sum(x[i][j] for i in left_set) <= 1`.
- These constraints ensure each element is matched at most once.

### Step 4 - Incorporate Preference Restrictions
- For each pair `(i, j)` not in the allowed set, add constraint `x[i][j] == 0`.
- Alternatively, if using a binary `preference_matrix`, add constraint `x[i][j] <= preference_matrix[i][j]`.
- This step restricts assignments to compatible pairs only.

### Step 5 - Set Maximization Objective
- Define the objective as `maximize sum(x[i][j] for i in left_set for j in right_set)`.
- This directly maximizes the total number of successful matches.

### Formulation Template
```json
{
  "sets": ["left_set", "right_set"],
  "parameters": ["preference_matrix (binary)"],
  "decision_variables": ["x[i][j] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum(x[i][j] for i in left_set for j in right_set)"
  },
  "constraints": [
    "sum(x[i][j] for j in right_set) <= 1, ∀ i ∈ left_set",
    "sum(x[i][j] for i in left_set) <= 1, ∀ j ∈ right_set",
    "x[i][j] == 0, ∀ (i,j) ∉ allowed_edges"
  ]
}
```

### Common Pitfalls
- Creating variables for all possible pairs, including incompatible ones, which increases model size unnecessarily. Use sparse variable creation based on allowed edges.
- Adding redundant constraints (e.g., both `x[i][j] == 0` and `sum(x[i][:]) == 0` for the same element) which can confuse the solver.
- Assuming `MODEL_INVALID` status indicates real-world infeasibility rather than a modeling error. Debug by simplifying constraints incrementally.

## Solving stage

### Strategy Overview
Use the OR-Tools CP-SAT solver to find an optimal or feasible assignment. Configure solver parameters for performance and reliability, and implement robust solution extraction and verification.

### Step 1 - Initialize Solver and Configure Parameters
- Create a `CpSolver()` instance.
- Set `solver.parameters.max_time_in_seconds` for a runtime limit.
- Set `solver.parameters.num_search_workers` to utilize parallel processing.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to demand an exact optimal solution.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if `status` is `cp_model.OPTIMAL` (proven optimal) or `cp_model.FEASIBLE` (valid solution found).
- Handle `cp_model.MODEL_INVALID` by debugging constraint contradictions, not assuming infeasibility.

### Step 3 - Extract and Verify Solution
- Iterate through all decision variables `x[i][j]`.
- Collect pairs where `solver.Value(x[i][j]) == 1` as the assignment.
- Verify the solution: count matches equals objective value, each element appears at most once, and all assignments respect preferences.

### Step 4 - Output Results
- Print the objective value (number of matches).
- Output the list of matched pairs in a structured format (e.g., JSON) for downstream use.
- Optionally, list unassigned elements from each set.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
x = {}
for i in left_set:
    for j in right_set:
        if (i, j) in allowed_edges:  # Sparse creation
            x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")
# Add constraints
for i in left_set:
    model.Add(sum(x.get((i, j), 0) for j in right_set) <= 1)
for j in right_set:
    model.Add(sum(x.get((i, j), 0) for i in left_set) <= 1)
# Objective
model.Maximize(sum(x.values()))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = [(i, j) for (i, j), var in x.items() if solver.Value(var) == 1]
    print(f"Optimal matches: {solver.ObjectiveValue()}")
    print(f"Assignments: {assignments}")
else:
    print("No solution found.")
```

### Common Pitfalls
- Not checking solver status before reading variable values, leading to runtime errors.
- Setting `max_time_in_seconds` to a negative value, which causes `MODEL_INVALID`.
- Interpreting `MODEL_INVALID` as mere infeasibility; it indicates structural model issues requiring debugging.

# Workflow 2 (Max-Flow via Graph Backend)

## Modeling stage

### Strategy Overview
Reduce the bipartite matching problem to a maximum flow problem on a constructed network. This approach leverages specialized graph algorithms, often leading to faster solving for pure cardinality maximization without additional constraints.

### Step 1 - Construct Flow Network Representation
- Define a source node and a sink node.
- Create a node for each element in `left_set` and `right_set`.
- Assign unique integer IDs to all nodes (e.g., left nodes: `0..n-1`, right nodes: `n..n+m-1`, source: `n+m`, sink: `n+m+1`).

### Step 2 - Add Arcs with Unit Capacity
- Add an arc from source to each left node with capacity 1.
- Add an arc from each right node to sink with capacity 1.
- For each allowed pair `(i, j)`, add an arc from left node `i` to right node `j` with capacity 1.
- Do not add arcs for incompatible pairs.

### Step 3 - Map Objective to Flow Maximization
- The objective to maximize matches is equivalent to maximizing the flow from source to sink.
- The maximum flow value will equal the maximum number of feasible matches.

### Formulation Template
```json
{
  "sets": ["left_set", "right_set", "allowed_edges"],
  "parameters": [],
  "decision_variables": ["flow on each arc"],
  "objective": {
    "sense": "max",
    "expression": "total flow from source to sink"
  },
  "constraints": [
    "flow conservation at each node",
    "flow on each arc ≤ capacity (1)",
    "flow is integer"
  ]
}
```

### Common Pitfalls
- Incorrect node indexing leading to arcs connecting wrong nodes. Use offset variables consistently.
- Adding arcs for all possible pairs instead of only allowed edges, which unnecessarily enlarges the network.
- Using a min-cost flow solver for unweighted matching, which may fail due to infeasibility; use a max-flow solver instead.

## Solving stage

### Strategy Overview
Use a maximum flow solver (e.g., OR-Tools `SimpleMaxFlow`) to compute the optimal flow. Extract assignments from the flow on arcs connecting the two sets, and verify the solution against the original constraints.

### Step 1 - Initialize Max-Flow Solver
- Create a `SimpleMaxFlow()` instance.
- Use `add_arc_with_capacity(tail, head, capacity)` to build the network as modeled.

### Step 2 - Solve and Check Optimality
- Call `status = smf.solve(source, sink)`.
- Verify `status == smf.OPTIMAL` before extracting results.
- The optimal flow value is obtained via `smf.optimal_flow()`.

### Step 3 - Extract Assignments from Flow
- Iterate through all arcs using `smf.num_arcs()`.
- For each arc index, check if `smf.flow(arc_idx) > 0`.
- Filter arcs where the tail is a left node and the head is a right node (using the predefined offsets).
- The pair `(tail, head - right_offset)` represents a match.

### Step 4 - Validate and Output
- Ensure the number of matches equals the optimal flow value.
- Verify that each left and right element appears in at most one match.
- Output the matches and the total cardinality.

### Code Usage
```python
from ortools.graph.python import max_flow

# Build model from formulation
smf = max_flow.SimpleMaxFlow()
# Define offsets
left_count = len(left_set)
right_count = len(right_set)
source = left_count + right_count
sink = source + 1
right_offset = left_count

# Add arcs
for i in range(left_count):
    smf.add_arc_with_capacity(source, i, 1)
for j in range(right_count):
    smf.add_arc_with_capacity(right_offset + j, sink, 1)
for (i, j) in allowed_edges:
    smf.add_arc_with_capacity(i, right_offset + j, 1)

# Solve with status / termination checks
status = smf.solve(source, sink)
if status == smf.OPTIMAL:
    assignments = []
    for arc_idx in range(smf.num_arcs()):
        if smf.flow(arc_idx) > 0:
            tail, head = smf.tail(arc_idx), smf.head(arc_idx)
            # Check if arc connects left to right set
            if 0 <= tail < left_count and right_offset <= head < right_offset + right_count:
                assignments.append((tail, head - right_offset))
    print(f"Optimal matches: {smf.optimal_flow()}")
    print(f"Assignments: {assignments}")
else:
    print("Max-flow solver did not find an optimal solution.")
```

### Common Pitfalls
- Misinterpreting solver status; `OPTIMAL` is required for a proven maximum flow.
- Forgetting to filter arcs when extracting assignments, including source-left or right-sink arcs in the match list.
- Using `SimpleMinCostFlow` for unweighted matching, which may fail with infeasibility status; prefer `SimpleMaxFlow`.
