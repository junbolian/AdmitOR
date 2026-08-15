---
name: TSP_MTZ_Formulation
description: |
  Model and solve the Traveling Salesperson Problem using Miller-Tucker-Zemlin subtour elimination, with robust handling of depot position and solver status checks.

---

# Workflow 1 (MIP Solver with Explicit Big-M)

## Modeling stage

### Strategy Overview
This workflow models the TSP as a Mixed-Integer Program (MIP) using binary arc selection and integer position variables. It employs a classic Big-M formulation for subtour elimination, explicitly defining a large constant `M` to deactivate ordering constraints for unselected arcs. The model is built for compatibility with general-purpose MIP solvers like SCIP or CBC.

### Step 1 - Define Variables and Parameters
- Define a set of nodes `N` representing cities, with a designated depot node (e.g., `0`).
- Create a binary decision variable `x[i,j]` for each directed arc `(i,j)`, where `i != j`.
- Create an integer decision variable `u[i]` for each node to represent its position in the tour.
- Define parameter `cost[i,j]` as the travel cost for arc `(i,j)`.

### Step 2 - Implement Assignment Constraints
- Add a `single_exit_per_node` constraint: `sum(x[i,j] for j in N if j != i) == 1` for each node `i`.
- Add a `single_visit_per_node` constraint: `sum(x[i,j] for i in N if i != j) == 1` for each node `j`.
- Add a `no_self_loop` constraint: `x[i,i] == 0` for each node `i`.

### Step 3 - Implement Subtour Elimination via Position Ordering
- Fix the depot's position: `u[depot] == 0`.
- Set bounds for position variables: `0 <= u[i] <= len(N) - 1` for all nodes `i`.
- For all arcs `(i,j)` where `i != depot` and `j != depot`, add the Miller-Tucker-Zemlin constraint: `u[j] >= u[i] + 1 - M * (1 - x[i,j])`. Use a sufficiently large `M` (e.g., `len(N)`) to ensure the constraint is inactive when `x[i,j] == 0`.

### Step 4 - Define the Objective
- Minimize the total tour cost: `min sum(cost[i,j] * x[i,j] for i in N for j in N if i != j)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (cities)"
  ],
  "parameters": [
    "cost[i,j]: travel cost from node i to node j, for i,j in N, i != j"
  ],
  "decision_variables": [
    "x[i,j]: binary, 1 if arc (i,j) is in the tour, for i,j in N, i != j",
    "u[i]: integer, position of node i in the tour, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i,j in N if i != j)"
  },
  "constraints": [
    "single_exit_per_node: sum(x[i,j] for j in N if j != i) == 1, for each i in N",
    "single_visit_per_node: sum(x[i,j] for i in N if i != j) == 1, for each j in N",
    "no_self_loop: x[i,i] == 0, for each i in N",
    "depot_position: u[depot] == 0",
    "position_bounds: 0 <= u[i] <= |N| - 1, for each i in N",
    "subtour_elimination: u[j] >= u[i] + 1 - M * (1 - x[i,j]), for each i,j in N where i != depot and j != depot and i != j"
  ]
}
```

### Common Pitfalls
- Applying the `subtour_elimination` constraint to arcs involving the depot (`i == depot` or `j == depot`). This creates a logical conflict with the fixed `u[depot] = 0`. Always exclude the depot node from these constraints.
- Using a Big-M value that is too small (e.g., exactly `|N|`). If `u[i]` can be `|N|-1`, the constraint `u[j] >= u[i] + 1 - M` when `x[i,j]=0` could become `u[j] >= (|N|-1) + 1 - |N| = 0`, which is not restrictive enough. Use `M = |N| + 1` or larger to ensure it is inactive.
- Forgetting to exclude self-loops (`i == j`) from the assignment constraints, which can lead to trivial, invalid solutions.

## Solving stage

### Strategy Overview
This solving stage uses a standard MIP solver interface (e.g., OR-Tools, PuLP) to find an optimal tour. It emphasizes proper solver configuration, rigorous status checking, and solution validation against enumeration for small instances.

### Step 1 - Configure Solver and Build Model
- Instantiate a MIP solver (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set solver parameters: `SetTimeLimit`, `SetNumThreads`, and `SetSolverSpecificParameters` as needed.
- Programmatically build the model using the formulation template, iterating over sets and parameters.

### Step 2 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the result status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNBOUNDED`).
- If status is not `OPTIMAL` or `FEASIBLE`, raise an error or log diagnostics; do not proceed to extract a solution.

### Step 3 - Extract and Validate Solution
- If feasible, iterate over `x[i,j]` variables and collect arcs where `solution_value() > 0.5`.
- Extract `u[i]` values to verify the tour ordering.
- For small instances (`|N| <= threshold`), validate optimality by comparing the solver's objective value with the cost from an exhaustive enumeration of all possible tours.

### Step 4 - Output Results
- Print the objective value with a parsable prefix (e.g., `RESULT:{value}`).
- Output the selected arcs or the sequence of nodes in tour order.

### Code Usage
```python
# build model from formulation
import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (Create variables x, u based on set N)
# ... (Add constraints using loops)
# ... (Set objective)

# solve with status / termination checks
solver.SetTimeLimit(60000)  # milliseconds
result_status = solver.Solve()

if result_status in [solver.OPTIMAL, solver.FEASIBLE]:
    print(f'RESULT:{solver.Objective().Value()}')
    # Extract solution
    tour_arcs = []
    for i in N:
        for j in N:
            if i != j and x[i,j].solution_value() > 0.5:
                tour_arcs.append((i,j))
    # ... (process and output tour)
else:
    print('ERROR: Model infeasible or no solution found.')
```

### Common Pitfalls
- Assuming a `FEASIBLE` status guarantees optimality. Always check for `OPTIMAL` if an exact solution is required.
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.
- Extracting variable values without checking the solution status first, leading to errors.

# Workflow 2 (MTZ with Compact Inequality)

## Modeling stage

### Strategy Overview
This workflow uses the alternative, compact Miller-Tucker-Zemlin inequality formulation. It avoids an explicit Big-M constant by leveraging the known upper bound on position variables. This formulation is often more numerically stable and is directly supported by some modeling frameworks.

### Step 1 - Define Variables and Parameters
- Define set `N` and designate a depot node.
- Create binary arc variables `x[i,j]` for `i != j`.
- Create integer position variables `u[i]` for all nodes.
- Define cost parameter `cost[i,j]`.

### Step 2 - Implement Assignment and Domain Constraints
- Add `single_exit_per_node` and `single_visit_per_node` constraints identical to Workflow 1.
- Add `no_self_loop` constraints.
- Fix the depot position: `u[depot] == -1` or `0` (depending on convention).
- Set bounds: `0 <= u[i] <= |N| - 1` for all `i`.

### Step 3 - Apply Compact MTZ Subtour Elimination
- For all `i != depot` and `j != depot` with `i != j`, add the constraint: `u[i] - u[j] + |N| * x[i,j] <= |N| - 1`.
- This constraint prevents subtours without an explicit Big-M. When `x[i,j] = 1`, it enforces `u[i] - u[j] <= -1`, meaning `u[j] >= u[i] + 1`. When `x[i,j] = 0`, it becomes `u[i] - u[j] <= |N| - 1`, which is always satisfied given the variable bounds.

### Step 4 - Define the Objective
- Minimize total cost: `min sum(cost[i,j] * x[i,j] for i,j in N if i != j)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (cities)"
  ],
  "parameters": [
    "cost[i,j]: travel cost from node i to node j, for i,j in N, i != j"
  ],
  "decision_variables": [
    "x[i,j]: binary, 1 if arc (i,j) is in the tour, for i,j in N, i != j",
    "u[i]: integer, position of node i in the tour, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i,j in N if i != j)"
  },
  "constraints": [
    "single_exit_per_node: sum(x[i,j] for j in N if j != i) == 1, for each i in N",
    "single_visit_per_node: sum(x[i,j] for i in N if i != j) == 1, for each j in N",
    "no_self_loop: x[i,i] == 0, for each i in N",
    "depot_position: u[depot] == 0",
    "position_bounds: 0 <= u[i] <= |N| - 1, for each i in N",
    "subtour_elimination: u[i] - u[j] + |N| * x[i,j] <= |N| - 1, for each i,j in N where i != depot and j != depot and i != j"
  ]
}
```

### Common Pitfalls
- Applying the compact MTZ constraint to arcs where `i == depot` or `j == depot`. This can force impossible conditions (e.g., `u[depot] - u[j] <= -1`). Always exclude the depot.
- Incorrectly setting the depot position `u[depot]`. Using `0` is standard, but ensure the bounds `0 <= u[i]` allow it and that non-depot nodes start from position `1`.
- Using `|N|` as the coefficient for `x[i,j]` in the constraint. This is correct, but ensure it matches the upper bound on `u[i]` (`|N|-1`).

## Solving stage

### Strategy Overview
This stage leverages a modeling language (e.g., Pyomo) that supports concise constraint declaration, allowing the compact MTZ formulation to be written cleanly. It focuses on solver-agnostic model building and includes a fallback to a brute-force validator.

### Step 1 - Build Model with Modeling Framework
- Use a modeling framework like Pyomo to define abstract sets and parameters.
- Declare variables and constraints using the framework's syntax, which closely mirrors the mathematical formulation.
- Connect to a solver backend (e.g., GLPK, CPLEX, Gurobi).

### Step 2 - Solve and Interpret Termination Condition
- Invoke the solver through the framework's interface.
- Check both the solver status (`SolverStatus`) and termination condition (`TerminationCondition`). A status of `ok` with a condition of `optimal` or `feasible` indicates a valid solution.

### Step 3 - Extract and Cross-Validate Solution
- Load the solution into the model instance.
- Retrieve variable values and reconstruct the tour.
- For instances below a verifiable size threshold, perform an exhaustive permutation search to confirm the solution's optimality and feasibility.

### Step 4 - Handle Infeasibility and Output
- If the model is infeasible, use the modeling framework's capabilities to diagnose conflicting constraints (e.g., by reviewing the IIS for some solvers).
- Output the objective value and tour in a structured format.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=N_set)  # N_set is the list of nodes
model.x = pyo.Var(model.N, model.N, within=pyo.Binary)
model.u = pyo.Var(model.N, within=pyo.Integers, bounds=(0, len(N_set)-1))
# ... (Define cost parameter, add constraints using rule functions)
# ... (Set objective)

# solve with status / termination checks
solver = pyo.SolverFactory('glpk')
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    print(f'RESULT:{pyo.value(model.obj)}')
    # Extract solution from model.x and model.u
else:
    print('ERROR: Solver failed to find a feasible solution.')
```

### Common Pitfalls
- Relying solely on the solver status being `ok` without checking the termination condition, which could be `infeasible` or `unbounded`.
- Not using the modeling framework's methods to load solution data before accessing variable values, resulting in `None`.
- Omitting the brute-force validation for small instances, which is a crucial step for verifying the correctness of the MTZ formulation implementation.
