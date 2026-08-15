---
name: TSP with Position-Based Subtour Elimination
description: |
  Model and solve the Traveling Salesperson Problem using binary arc selection and integer position variables with Miller–Tucker–Zemlin subtour elimination constraints.

---

# Workflow 1 (MILP with MTZ Constraints)

## Modeling stage

### Strategy Overview
Formulate the TSP as a Mixed-Integer Linear Program using binary variables for arc selection and integer variables for node positions. Subtours are eliminated via Miller–Tucker–Zemlin (MTZ) constraints that enforce a logical ordering of visits.

### Step 1 - Define Sets and Parameters
- Define a set of nodes `N` representing all locations, including the depot.
- Define a cost parameter `c[i,j]` for the travel cost from node `i` to node `j`.
- Identify the depot node (e.g., `0`) as the fixed start and end point of the tour.

### Step 2 - Define Decision Variables
- Create binary decision variable `x[i,j]` for all `i,j` in `N`, `i != j`. `x[i,j] = 1` if arc `(i,j)` is part of the tour.
- Create integer decision variable `u[i]` for all `i` in `N`. `u[i]` represents the position of node `i` in the tour sequence.

### Step 3 - Formulate Degree Constraints
- For each node `i` in `N`, enforce exactly one outgoing arc: `sum_{j in N, j != i} x[i,j] = 1`.
- For each node `j` in `N`, enforce exactly one incoming arc: `sum_{i in N, i != j} x[i,j] = 1`.

### Step 4 - Apply MTZ Subtour Elimination Constraints
- Fix the depot's position to establish a reference: `u[depot] = 0`.
- Set bounds for position variables: `0 <= u[i] <= |N| - 1` for all `i` in `N`.
- For all `i,j` in `N` where `i != j`, `i != depot`, and `j != depot`, apply the MTZ constraint: `u[j] >= u[i] + 1 - M * (1 - x[i,j])`. The Big-M constant `M` must be larger than the maximum possible position difference (e.g., `M = |N|` or `|N| + 1`).

### Step 5 - Define Objective
- Minimize the total tour cost: `min sum_{i in N} sum_{j in N, j != i} c[i,j] * x[i,j]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes (cities/locations)."},
    {"name": "A", "description": "Set of all directed arcs (i,j) where i != j, subset of N x N."}
  ],
  "parameters": [
    {"name": "c", "index": ["i", "j"], "description": "Travel cost from node i to node j."},
    {"name": "depot", "description": "Index of the start/end depot node."},
    {"name": "M", "description": "Big-M constant for MTZ constraints, must be > |N|-1."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["i", "j"], "type": "binary", "description": "1 if arc (i,j) is selected."},
    {"name": "u", "index": ["i"], "type": "integer", "bounds": "[0, |N|-1]", "description": "Position of node i in the tour."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in N} sum_{j in N, j != i} c[i,j] * x[i,j]"
  },
  "constraints": [
    {"name": "outgoing_arc", "expression": "sum_{j in N, j != i} x[i,j] = 1", "for_all": "i in N"},
    {"name": "incoming_arc", "expression": "sum_{i in N, i != j} x[i,j] = 1", "for_all": "j in N"},
    {"name": "depot_position", "expression": "u[depot] = 0"},
    {"name": "mtz", "expression": "u[j] >= u[i] + 1 - M * (1 - x[i,j])", "for_all": "i,j in N, i != j, i != depot, j != depot"}
  ]
}
```

### Common Pitfalls
- Applying MTZ constraints to arcs involving the depot (`i=depot` or `j=depot`) when the depot's position is fixed to 0, which can create infeasible constraints.
- Using a Big-M value (`M`) that is too small (e.g., `M = |N| - 1`), which can incorrectly cut off valid tours. Use `M >= |N|`.
- Forgetting to exclude the `i=j` case from the MTZ constraint index set, which is unnecessary and can cause formulation errors.

## Solving stage

### Strategy Overview
Implement the MILP model using a modeling library (e.g., OR-Tools, PuLP) and solve it with a MIP solver. Carefully handle solver status and solution extraction to ensure robust results.

### Step 1 - Build Model from Formulation
- Instantiate a solver object (e.g., `CBC`, `SCIP`, `Gurobi`).
- Create model variables `x[i,j]` (binary) and `u[i]` (integer with bounds).
- Add constraints using the exact formulation logic, paying special attention to the index sets for MTZ constraints.

### Step 2 - Set Solver Parameters and Solve
- Set appropriate solver parameters for the problem scale (e.g., time limit, relative MIP gap).
- Invoke the solver and capture the result status.

### Step 3 - Check Solver Status and Extract Solution
- Check if the solver status indicates `OPTIMAL` or `FEASIBLE`.
- If successful, iterate over `x[i,j]` variables and collect arcs where `x[i,j].solution_value() > 0.5` to reconstruct the tour.
- Extract the objective value as the total cost.

### Step 4 - Validate Solution (Optional for Small N)
- For small instances (`|N| <= 10`), validate the solver's tour and cost via exhaustive enumeration (e.g., checking all permutations) as a sanity check.

### Code Usage
```python
# build model from formulation
import pulp

# Define sets, parameters (cost, depot, M)
N = range(num_nodes)
cost = {...}  # cost matrix
depot = 0
M = len(N)  # Big-M constant

# Create problem
prob = pulp.LpProblem('TSP_MTZ', pulp.LpMinimize)

# Decision variables
x = pulp.LpVariable.dicts('x', ((i, j) for i in N for j in N if i != j), cat='Binary')
u = pulp.LpVariable.dicts('u', N, lowBound=0, upBound=len(N)-1, cat='Integer')

# Objective
prob += pulp.lpSum(cost[i][j] * x[i, j] for i in N for j in N if i != j)

# Degree constraints
for i in N:
    prob += pulp.lpSum(x[i, j] for j in N if j != i) == 1
for j in N:
    prob += pulp.lpSum(x[i, j] for i in N if i != j) == 1

# Depot position
prob += u[depot] == 0

# MTZ constraints (exclude depot)
for i in N:
    for j in N:
        if i != j and i != depot and j != depot:
            prob += u[j] >= u[i] + 1 - M * (1 - x[i, j])

# solve with status / termination checks
solver = pulp.PULP_CBC_CMD(timeLimit=30, gapRel=0.0)
prob.solve(solver)

# Check status and extract solution
if pulp.LpStatus[prob.status] in ['Optimal', 'Feasible']:
    tour_arcs = [(i, j) for (i, j) in x if pulp.value(x[i, j]) > 0.5]
    total_cost = pulp.value(prob.objective)
    # Reconstruct tour sequence from active arcs
else:
    print(f"Solver status: {pulp.LpStatus[prob.status]}")
```

### Common Pitfalls
- Not checking solver status before accessing variable values, leading to runtime errors.
- Using a modeling interface that raises exceptions on infeasibility (e.g., new Pyomo contrib) without proper try-except handling.
- Misinterpreting a non-zero solver return code as a guarantee of infeasibility; always check the official status attribute.

# Workflow 2 (Exhaustive Enumeration for Verification)

## Modeling stage

### Strategy Overview
For small-scale TSP instances, bypass complex MILP formulation and directly evaluate all possible tours via permutation-based enumeration. This provides a guaranteed optimal solution and serves as a verification tool for MILP models.

### Step 1 - Define Problem Inputs
- Define the list of nodes `N` and the cost matrix `c[i,j]`.
- Identify the fixed depot node which must be the start and end of every tour.

### Step 2 - Define Solution Representation
- A complete tour is represented as a sequence starting and ending at the depot, visiting all other nodes exactly once in some order.
- The solution space is the set of all permutations of the non-depot nodes.

### Step 3 - Define Evaluation Function
- For a given permutation `p` of non-depot nodes, construct the full tour: `[depot] + list(p) + [depot]`.
- Compute the total cost by summing the cost of each consecutive pair in the tour.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes."},
    {"name": "N_no_depot", "description": "Set of all nodes excluding the depot."}
  ],
  "parameters": [
    {"name": "c", "index": ["i", "j"], "description": "Travel cost from node i to node j."},
    {"name": "depot", "description": "Index of the start/end depot node."}
  ],
  "decision_variables": [
    {"name": "tour", "type": "permutation", "description": "An ordered list of nodes from N_no_depot defining the visit sequence between depot start and end."}
  ],
  "objective": {
    "sense": "min",
    "expression": "c[depot, tour[0]] + sum_{k=0}^{|tour|-2} c[tour[k], tour[k+1]] + c[tour[-1], depot]"
  },
  "constraints": []
}
```

### Common Pitfalls
- Attempting enumeration for large `|N|` (e.g., >12), where the permutation count becomes computationally prohibitive.
- Incorrectly constructing the tour cost by omitting the return leg to the depot or misindexing the cost matrix.

## Solving stage

### Strategy Overview
Generate all permutations of non-depot nodes, evaluate the cost of each corresponding tour, and track the minimum. Use Python's `itertools.permutations` for generation.

### Step 1 - Generate All Permutations
- Use `itertools.permutations(N_no_depot)` to iterate over all possible orders of visiting the non-depot nodes.

### Step 2 - Evaluate Each Tour
- For each permutation, form the complete tour list (depot + permutation + depot).
- Calculate the total cost by summing costs between consecutive nodes in the complete tour.

### Step 3 - Track the Best Solution
- Maintain variables for the best tour found and its cost.
- Update these variables whenever a lower-cost tour is encountered.

### Step 4 - Return Optimal Solution
- After evaluating all permutations, the best tour and its cost are guaranteed to be optimal.

### Code Usage
```python
# build model from formulation
import itertools

# Define inputs
N = range(num_nodes)
cost = {...}  # cost matrix
depot = 0
N_no_depot = [i for i in N if i != depot]

best_tour = None
best_cost = float('inf')

# Enumerate all permutations
for perm in itertools.permutations(N_no_depot):
    # Construct full tour: start at depot, follow permutation, return to depot
    full_tour = [depot] + list(perm) + [depot]
    
    # Calculate total cost
    tour_cost = 0
    for k in range(len(full_tour) - 1):
        tour_cost += cost[full_tour[k]][full_tour[k+1]]
    
    # Update best solution
    if tour_cost < best_cost:
        best_cost = tour_cost
        best_tour = full_tour

# solve with status / termination checks
# Exhaustive search completes deterministically.
print(f"Optimal cost: {best_cost}")
print(f"Optimal tour: {best_tour}")
```

### Common Pitfalls
- Using enumeration as a primary solver for problems beyond trivial size, leading to excessive runtimes.
- Not using the enumeration result to cross-validate the output of a MILP solver for small instances, missing formulation errors.
