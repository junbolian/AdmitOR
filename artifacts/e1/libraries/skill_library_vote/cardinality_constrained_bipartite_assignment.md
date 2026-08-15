---
name: Cardinality-Constrained Bipartite Assignment
description: |
  Model and solve bipartite assignment problems with a fixed number of matches, minimizing total cost, using either a specialized min-cost flow or a general MIP approach.

---

# Workflow 1 (Min-Cost Flow Specialization)

## Modeling stage

### Strategy Overview
Formulate the cardinality-constrained assignment as a minimum-cost flow problem on a bipartite network. This leverages the inherent network structure for efficient solving.

### Step 1 - Map to Network Flow
- Recognize the problem as a bipartite matching with a fixed number `k` of matches.
- Construct a flow network: source connects to left nodes, left nodes connect to right nodes, right nodes connect to sink.
- Define arc capacities: all arcs have capacity 1 to enforce at-most-one matching.
- Define node supplies: source supply = `k`, sink demand = `-k`, all other nodes = 0.

### Step 2 - Define Costs and Variables
- Associate each potential assignment `(i, j)` with a cost `c_ij`.
- The decision variable is the flow on the arc from left node `i` to right node `j`, which will be integral (0 or 1) due to the network structure and integral supplies.

### Formulation Template
```json
{
  "sets": [
    "A = {a1, a2, ..., am} // Left set",
    "B = {b1, b2, ..., bn} // Right set"
  ],
  "parameters": [
    "c[i][j] // Cost of assigning left element i to right element j",
    "k // Required number of total assignments (cardinality)"
  ],
  "decision_variables": [
    "flow_i_j // Integer flow from left node i to right node j, implicitly binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in A, j in B} c[i][j] * flow_i_j"
  },
  "constraints": [
    "Flow conservation at each node.",
    "Source supply = k, Sink demand = -k.",
    "Arc capacities: source→A = 1, A→B = 1, B→sink = 1."
  ]
}
```

### Common Pitfalls
- Forgetting to scale fractional costs to integers for solvers requiring integral costs, which can lead to precision errors.
- Incorrect node indexing leading to mismatched arcs between left and right sets.
- Setting arc capacities greater than 1, which violates the "at-most-one" matching condition.

## Solving stage

### Strategy Overview
Use a specialized min-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) to efficiently find the optimal integral flow, which corresponds to the optimal assignment.

### Step 1 - Build Flow Network
- Instantiate the min-cost flow solver.
- Add arcs: source→left (capacity 1, cost 0), left→right (capacity 1, scaled cost `c_ij`), right→sink (capacity 1, cost 0).
- Set node supplies: source = `k`, sink = `-k`, all others = 0.

### Step 2 - Solve and Extract Assignments
- Invoke the solver's `solve()` method.
- Check the status is `OPTIMAL`.
- Iterate over arcs with positive flow; arcs between left and right nodes with flow > 0 indicate an assignment.

### Code Usage
```python
import math
from ortools.graph.python import min_cost_flow

# Initialize solver
smcf = min_cost_flow.SimpleMinCostFlow()
SCALE_FACTOR = 1000000  # For scaling fractional costs to integers

# Parameters: m, n, k, cost_matrix
# Add arcs: source (0) -> left nodes (1..m)
for i in range(m):
    smcf.add_arc_with_capacity_and_unit_cost(0, 1 + i, 1, 0)
# Add arcs: left nodes -> right nodes (m+1..m+n)
for i in range(m):
    for j in range(n):
        scaled_cost = int(cost_matrix[i][j] * SCALE_FACTOR)
        smcf.add_arc_with_capacity_and_unit_cost(1 + i, 1 + m + j, 1, scaled_cost)
# Add arcs: right nodes -> sink (m+n+1)
for j in range(n):
    smcf.add_arc_with_capacity_and_unit_cost(1 + m + j, 1 + m + n, 1, -0)

# Set supplies
smcf.set_node_supply(0, k)
smcf.set_node_supply(1 + m + n, -k)
# All other nodes have supply 0

# Solve
status = smcf.solve()
assignments = []
total_cost = 0.0
if status == smcf.OPTIMAL:
    for arc in range(smcf.num_arcs()):
        if smcf.flow(arc) > 0:
            tail, head = smcf.tail(arc), smcf.head(arc)
            # Check if arc connects left to right
            if 1 <= tail <= m and m + 1 <= head <= m + n:
                i = tail - 1
                j = head - (m + 1)
                assignments.append((i, j))
                total_cost += smcf.unit_cost(arc) / SCALE_FACTOR
else:
    # Handle solver failure (infeasible, etc.)
    pass
```

### Common Pitfalls
- Not checking solver status before extracting results, leading to runtime errors.
- Misinterpreting arc indices; ensure you filter for arcs between the correct node ranges.
- For large `k`, ensure the problem is feasible (k <= min(m, n)).

# Workflow 2 (General MIP Formulation)

## Modeling stage

### Strategy Overview
Formulate the problem directly as a Mixed-Integer Program (MIP) with binary assignment variables. This approach is solver-agnostic and explicitly encodes all constraints.

### Step 1 - Define Binary Variables
- For each pair `(i, j)` from left set `A` and right set `B`, create a binary variable `x[i][j]`.
- `x[i][j] = 1` indicates an assignment is made.

### Step 2 - Impose Matching and Cardinality Constraints
- Add constraints: sum over `j` for each `i` <= 1 (each left element assigned at most once).
- Add constraints: sum over `i` for each `j` <= 1 (each right element assigned at most once).
- Add global cardinality constraint: sum over all `i, j` of `x[i][j] == k`.

### Step 3 - Define Linear Objective
- Formulate the objective as the sum of assignment costs weighted by the decision variables: Minimize Σ_i Σ_j `c[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    "A = {a1, a2, ..., am} // Left set",
    "B = {b1, b2, ..., bn} // Right set"
  ],
  "parameters": [
    "c[i][j] // Cost of assigning left element i to right element j",
    "k // Required number of total assignments (cardinality)"
  ],
  "decision_variables": [
    "x[i][j] ∈ {0, 1} // Binary assignment variable"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in A} sum_{j in B} c[i][j] * x[i][j]"
  },
  "constraints": [
    "sum_{j in B} x[i][j] <= 1, for all i in A",
    "sum_{i in A} x[i][j] <= 1, for all j in B",
    "sum_{i in A} sum_{j in B} x[i][j] == k"
  ]
}
```

### Common Pitfalls
- Using `== 1` instead of `<= 1` for the per-element constraints, which would force every element to be assigned, often making the problem infeasible.
- Incorrectly indexing cost parameters when building the objective, leading to wrong cost calculations.
- Not verifying that `k` is within the feasible range [0, min(m, n)].

## Solving stage

### Strategy Overview
Use a general-purpose MIP solver (e.g., CBC, SCIP, HiGHS via OR-Tools or Pyomo) to find an optimal solution. This involves building the model, setting the objective and constraints, and solving.

### Step 1 - Instantiate Solver and Variables
- Create a solver instance (e.g., `Solver.CreateSolver("SCIP")` in OR-Tools).
- Create a dictionary or 2D array of binary variables `x[i][j]`.

### Step 2 - Add Constraints and Objective
- Add the three constraint families using loops and `solver.Sum()`.
- Build the objective expression and call `solver.Minimize()`.

### Step 3 - Solve and Validate
- Execute `solver.Solve()`.
- Check the status (`OPTIMAL` or `FEASIBLE`).
- Extract assignments by checking `x[i][j].solution_value() > 0.5`.
- For small instances, validate against brute-force enumeration to ensure model correctness.

### Code Usage
```python
from ortools.linear_solver import pywraplp

def solve_assignment_mip(m, n, k, cost_matrix):
    # Solver selection
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        raise RuntimeError("Solver not available.")

    # Variables: x[i][j] binary
    x = {}
    for i in range(m):
        for j in range(n):
            x[i, j] = solver.BoolVar(f"x_{i}_{j}")

    # Constraints: each left element at most one assignment
    for i in range(m):
        solver.Add(solver.Sum([x[i, j] for j in range(n)]) <= 1)
    # Constraints: each right element at most one assignment
    for j in range(n):
        solver.Add(solver.Sum([x[i, j] for i in range(m)]) <= 1)
    # Constraint: total assignments = k
    solver.Add(solver.Sum([x[i, j] for i in range(m) for j in range(n)]) == k)

    # Objective: minimize total cost
    objective = solver.Sum([cost_matrix[i][j] * x[i, j] for i in range(m) for j in range(n)])
    solver.Minimize(objective)

    # Solve
    status = solver.Solve()
    assignments = []
    total_cost = 0.0
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        for i in range(m):
            for j in range(n):
                if x[i, j].solution_value() > 0.5:
                    assignments.append((i, j))
                    total_cost += cost_matrix[i][j]
        # Optional: brute-force validation for small m, n
        # validate_with_bruteforce(m, n, k, cost_matrix, assignments, total_cost)
    else:
        # Handle solver failure (infeasible, etc.)
        pass
    return assignments, total_cost
```

### Common Pitfalls
- Assuming the solver always finds an optimal solution; always check the status code.
- Using a loose tolerance (e.g., `> 0`) instead of `> 0.5` to determine binary variable activity, which can be error-prone due to solver tolerances.
- Not catching exceptions when a specific solver backend is not installed.
