---
name: Binary Selection with Pairwise Benefit Maximization
description: |
  Model and solve combinatorial selection problems with pairwise interaction benefits using either linearized CP-SAT or direct quadratic MIP formulations.
---

# Workflow 1 (CP-SAT with Linearization)

## Modeling stage

### Strategy Overview
This workflow uses a Constraint Programming (CP-SAT) solver, requiring a linear model. The quadratic pairwise objective is linearized by introducing auxiliary binary variables for each pair, enabling exact solving of the binary quadratic problem.

### Step 1 - Define Core Selection Variables
- Create a binary decision variable for each candidate element to represent its selection status.
- Use a naming convention like `x_i` for variable `i` in a set of size `N`.

### Step 2 - Enforce Cardinality Constraint
- Add a single linear constraint to enforce the exact number of selected elements.
- The constraint is `sum(x_i for i in N) == k`, where `k` is the required selection count.

### Step 3 - Linearize Pairwise Objective
- For each unordered pair `(i, j)` where `i < j`, create an auxiliary binary variable `y_{i,j}`.
- Add three linear constraints to enforce the logical equivalence `y_{i,j} = x_i * x_j`:
  1. `y_{i,j} <= x_i`
  2. `y_{i,j} <= x_j`
  3. `y_{i,j} >= x_i + x_j - 1`
- The objective is to maximize `sum(benefit_{i,j} * y_{i,j} for all pairs)`.

### Formulation Template
```json
{
  "sets": [
    "N: Set of candidate elements (size N)",
    "Pairs: Set of unordered pairs (i,j) where i<j"
  ],
  "parameters": [
    "k: Integer, exact number of elements to select",
    "benefit_{i,j}: Numeric, benefit for selecting both element i and j"
  ],
  "decision_variables": [
    "x_i: Binary, 1 if element i is selected",
    "y_{i,j}: Binary, 1 if both i and j are selected"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{ (i,j) in Pairs } benefit_{i,j} * y_{i,j}"
  },
  "constraints": [
    "sum_{ i in N } x_i == k",
    "y_{i,j} <= x_i, for all (i,j) in Pairs",
    "y_{i,j} <= x_j, for all (i,j) in Pairs",
    "y_{i,j} >= x_i + x_j - 1, for all (i,j) in Pairs"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce `i < j` when creating pair variables, leading to duplicate terms and an incorrect objective.
- Using inequality (`<=` or `>=`) for the cardinality constraint when exact equality (`==`) is required.
- Not scaling large benefit parameters, which can cause numerical issues in the solver.

## Solving stage

### Strategy Overview
Solve the linearized CP-SAT model using a dedicated CP-SAT solver (e.g., OR-Tools). Configure for exact solution, handle solver status, extract the solution, and verify its correctness.

### Step 1 - Configure Solver Parameters
- Set a time limit to prevent indefinite runtime (e.g., `max_time_in_seconds`).
- Enable parallel search (`num_search_workers`) for performance.
- Set a random seed (`random_seed`) for reproducibility.
- Set the relative gap to zero (`relative_gap_limit = 0.0`) to search for the optimal solution.

### Step 2 - Solve and Check Status
- Invoke the solver and capture the status code.
- Check for `OPTIMAL` or `FEASIBLE` status before attempting to read solution values.
- If status is not `OPTIMAL` or `FEASIBLE`, handle as an incomplete or infeasible solve.

### Step 3 - Extract and Verify Solution
- Extract selected elements by evaluating the core binary variables (e.g., `[i for i in N if solver.Value(x_i) == 1]`).
- Recompute the objective value directly from the selected elements and the original benefit matrix to verify consistency with the solver's reported objective.
- For small problem instances, validate against a brute-force enumeration for absolute confidence.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in range(N) if solver.Value(x[i]) == 1]
    # ... verification and output
else:
    # Handle infeasible or unknown status
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Accessing solution values without checking solver status first, leading to runtime errors.
- Setting a negative `MIPGap` or `relative_gap_limit`, which is invalid for most solvers.
- Not verifying the solver's objective value, which can mask modeling errors.

# Workflow 2 (MIP Solver with Quadratic Objective)

## Modeling stage

### Strategy Overview
This workflow uses a Mixed-Integer Programming (MIP) solver capable of handling quadratic objectives directly (e.g., Gurobi, CPLEX). The model uses the original quadratic formulation without linearization, relying on the solver's internal handling of non-convex terms.

### Step 1 - Define Binary Selection Variables
- Create binary decision variables `x_i` for each element `i` in the candidate set `N`.

### Step 2 - Apply Cardinality Constraint
- Add a linear constraint enforcing the exact selection count: `sum(x_i for i in N) == k`.

### Step 3 - Formulate Quadratic Objective
- Define the objective directly as the sum of pairwise benefits multiplied by the product of the corresponding selection variables.
- The expression is `maximize sum_{i, j in N, i != j} benefit_{i,j} * x_i * x_j`.

### Formulation Template
```json
{
  "sets": [
    "N: Set of candidate elements"
  ],
  "parameters": [
    "k: Integer, exact number of elements to select",
    "benefit_{i,j}: Numeric, benefit for selecting both element i and j (can be asymmetric)"
  ],
  "decision_variables": [
    "x_i: Binary, 1 if element i is selected"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{ i in N } sum_{ j in N, j != i } benefit_{i,j} * x_i * x_j"
  },
  "constraints": [
    "sum_{ i in N } x_i == k"
  ]
}
```

### Common Pitfalls
- Assuming the benefit matrix is symmetric; use ordered pairs `(i,j)` to correctly model asymmetric benefits.
- Forgetting to set the solver parameter to handle non-convex quadratics, leading to errors or incorrect solutions.
- Creating an overly dense benefit matrix when many pairwise benefits are zero, wasting memory.

## Solving stage

### Strategy Overview
Solve the quadratic MIP model using a compatible solver. Key steps include configuring the solver for non-convex problems, setting optimality tolerances, and implementing robust solution extraction and verification.

### Step 1 - Configure Solver for Quadratic Problems
- Set the non-convex strategy parameter (e.g., `NonConvex=2` for Gurobi).
- Set optimality gap (`MIPGap`) to zero for exact solutions, if computationally feasible.
- Configure parallel threads (`Threads`) and a random seed (`Seed`) for performance and reproducibility.
- Apply a time limit.

### Step 2 - Solve and Validate Termination Status
- Execute the solve and capture the termination condition.
- Check for `OPTIMAL` or `FEASIBLE` status before proceeding.
- If the status is not acceptable, return a structured error without attempting to read variables.

### Step 3 - Process and Verify Solution
- Extract selected elements by thresholding the variable values (e.g., `[i for i in N if x[i].X > 0.5]`).
- Independently compute the objective value by evaluating the quadratic sum over the selected elements.
- For small `N`, perform brute-force enumeration to validate the solver's result.

### Code Usage
```python
# build model from formulation
import gurobipy as gp
m = gp.Model()
x = m.addVars(N, vtype=gp.GRB.BINARY, name="x")
# ... (add cardinality constraint)

# Define quadratic objective
obj_expr = gp.quicksum(benefit[i, j] * x[i] * x[j] for i in N for j in N if i != j)
m.setObjective(obj_expr, sense=gp.GRB.MAXIMIZE)

# solve with status / termination checks
m.setParam('NonConvex', 2)
m.setParam('TimeLimit', 30)
m.setParam('MIPGap', 0.0)
m.setParam('Threads', 4)
m.setParam('Seed', 42)

m.optimize()

if m.status in (gp.GRB.OPTIMAL, gp.GRB.SUBOPTIMAL):
    selected = [i for i in N if x[i].X > 0.5]
    # ... verification and output
else:
    # Handle infeasible or other status
    print(f"Model status: {m.status}")
```

### Common Pitfalls
- Not setting the `NonConvex` parameter, causing the solver to reject the quadratic objective or solve a convex relaxation.
- Misinterpreting `SUBOPTIMAL` status (e.g., due to time limit) as a failure; it may still provide a valid feasible solution.
- Using a loose optimality gap when an exact solution is needed, potentially returning a suboptimal selection.
