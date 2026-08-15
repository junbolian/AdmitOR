---
name: Assignment Sequencing with Subtour Elimination
description: |
  Model and solve assignment problems with sequencing requirements and subtour elimination using binary assignment and position auxiliary variables.

---

# Workflow 1 (CP-SAT with Explicit MTZ)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT to model a permutation problem with explicit Miller-Tucker-Zemlin (MTZ) constraints for subtour elimination. It is well-suited for exact solving of medium-sized instances with additional position-based restrictions.

### Step 1 - Define Core Assignment Variables
- Create binary decision variables `x[i][j]` for each ordered pair `(i, j)` where `i != j` to represent selection of an arc from element `i` to element `j`.
- Use `model.NewBoolVar(f"x_{i}_{j}")` to instantiate each variable.

### Step 2 - Introduce Positional Auxiliary Variables
- Create integer auxiliary variables `u[i]` for each element `i` to represent its position in the final sequence.
- Instantiate with `model.NewIntVar(lower_bound, upper_bound, f"u_{i}")`, typically with bounds `[0, n-1]` where `n` is the number of elements.

### Step 3 - Enforce Assignment Constraints
- For each element `j`, add a constraint that the sum of incoming arcs equals 1: `model.Add(sum(x[i][j] for i in nodes if i != j) == 1)`.
- For each element `i`, add a constraint that the sum of outgoing arcs equals 1: `model.Add(sum(x[i][j] for j in nodes if i != j) == 1)`.

### Step 4 - Apply Subtour Elimination via MTZ
- For all pairs `(i, j)` where `i != j` and `j` is not the designated root element, add the MTZ constraint: `model.Add(u[i] - u[j] + n * x[i][j] <= n - 1)`.
- This forces a strict ordering when an arc is selected, preventing cycles.

### Step 5 - Set Position Bounds and Fix Root
- Apply any explicit position bounds for specific elements using `model.Add(u[k] >= lb)` and `model.Add(u[k] <= ub)`.
- Fix the position of the root element (e.g., `0`) to break symmetry: `model.Add(u[root] == 0)`.

### Step 6 - Formulate the Objective
- Define the objective to minimize total cost: `model.Minimize(sum(cost[i][j] * x[i][j] for i, j in arcs))`.

### Formulation Template
```json
{
  "sets": [
    "N: set of all elements (size n)",
    "A: set of arcs (i,j) where i,j in N, i != j"
  ],
  "parameters": [
    "cost[i][j]: cost of assigning element i before element j, for (i,j) in A"
  ],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc (i,j) is selected, for (i,j) in A",
    "u[i]: integer, position of element i in sequence, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{ (i,j) in A } cost[i][j] * x[i][j]"
  },
  "constraints": [
    "assignment_incoming: sum_{ i in N, i != j } x[i][j] == 1, for all j in N",
    "assignment_outgoing: sum_{ j in N, j != i } x[i][j] == 1, for all i in N",
    "subtour_elimination_mtz: u[i] - u[j] + n * x[i][j] <= n - 1, for all (i,j) in A where j != root",
    "position_bounds: lb_k <= u[k] <= ub_k, for specified elements k",
    "root_fixation: u[root] == 0"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude the root element `j` from the MTZ constraints, which can lead to an infeasible model.
- Using too weak or incorrect bounds on auxiliary variables `u[i]`, failing to properly restrict the sequence.
- Creating assignment variables for `i == j` (self-loops), which wastes memory and can cause formulation errors.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with appropriate runtime and optimality controls, then extract and validate the sequence by following the selected arcs from the root.

### Step 1 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` to control runtime.
- Set `solver.parameters.num_search_workers` for parallel search.
- Set `solver.parameters.random_seed` for reproducibility.
- Optionally, set `solver.parameters.relative_gap_limit` to `0.0` for an exact solution.

### Step 2 - Solve and Check Status
- Execute `solver.Solve(model)`.
- Check the result status: `status in (cp_model.OPTIMAL, cp_model.FEASIBLE)`.
- If status is not optimal or feasible, handle as an infeasible or unsolved instance.

### Step 3 - Extract Solution and Reconstruct Sequence
- If feasible, obtain the objective value: `obj_val = solver.ObjectiveValue()`.
- Reconstruct the sequence: start at the root element, then iteratively find the next element `next` where `solver.Value(x[current][next]) == 1`.
- Collect the auxiliary variable values: `pos_val[i] = solver.Value(u[i])`.

### Step 4 - Validate Solution Integrity
- Manually compute the total cost from the extracted sequence and cost matrix to verify against `obj_val`.
- Verify all assignment and position bound constraints are satisfied by the extracted values.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... [variable and constraint creation as per modeling stage]
model.Minimize(objective_expr)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Apply parameter settings
solver.parameters.max_time_in_seconds = max_time
solver.parameters.num_search_workers = num_workers
# ... other parameters
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    tour = [root]
    current = root
    for _ in range(len(N) - 1):
        for next_node in N:
            if next_node != current and solver.Value(x[current][next_node]) == 1:
                tour.append(next_node)
                current = next_node
                break
    obj_val = solver.ObjectiveValue()
    # Output results
else:
    # Handle infeasible or unsolved case
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good feasible solutions when time limits are hit.
- Incorrect tour reconstruction logic that gets stuck in an infinite loop if the solution does not form a single cycle.
- Assuming the solver's objective value is correct without independent verification, which can mask modeling errors.

# Workflow 2 (MIP Solver via Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to formulate a Mixed-Integer Programming (MIP) model with MTZ constraints, designed for solving with external commercial or open-source solvers (e.g., Gurobi, CBC). It leverages Pyomo's expressive constraint rules and efficient solver interfaces.

### Step 1 - Declare Model and Sets
- Create a Pyomo `ConcreteModel()`.
- Define sets `model.N` for elements and `model.A` for valid arcs `(i,j)` where `i != j`.

### Step 2 - Define Parameters and Variables
- Declare a parameter `model.cost` indexed by `model.A` for assignment costs.
- Create binary variables `model.x` indexed by `model.A` using `pyo.Var(domain=pyo.Binary)`.
- Create continuous or integer variables `model.u` indexed by `model.N` for positions, using `pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, n-1))`.

### Step 3 - Implement Assignment Constraints
- Define a constraint rule for each element `j`: `sum(model.x[i,j] for i in model.N if i != j) == 1`.
- Define a constraint rule for each element `i`: `sum(model.x[i,j] for j in model.N if j != i) == 1`.

### Step 4 - Implement MTZ Subtour Elimination
- Define a constraint rule for arcs `(i,j)` in `model.A` where `j != root`: `model.u[i] - model.u[j] + n * model.x[i,j] <= n - 1`.
- Use `pyo.Constraint.Skip` to omit constraints where `i == j` or where `j == root` to improve model compactness.

### Step 5 - Impose Position Bounds and Root Fix
- Add constraints for specific element bounds: `model.u[k] >= lb` and `model.u[k] <= ub`.
- Fix the root's position: `model.u[root].fix(0)`.

### Step 6 - Set the Objective
- Define the objective: `model.obj = pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for (i,j) in model.A), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of elements",
    "A: subset of N x N where i != j"
  ],
  "parameters": [
    "cost[i,j]: scalar cost for arc (i,j) in A"
  ],
  "decision_variables": [
    "x[i,j]: binary, selection variable for (i,j) in A",
    "u[i]: integer, position variable for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{ (i,j) in A } cost[i,j] * x[i,j]"
  },
  "constraints": [
    "assign_in: sum_{ i in N, i != j } x[i,j] == 1, for j in N",
    "assign_out: sum_{ j in N, j != i } x[i,j] == 1, for i in N",
    "mtz: u[i] - u[j] + n * x[i,j] <= n - 1, for (i,j) in A where j != root",
    "bounds: lb <= u[k] <= ub, for specified k",
    "root_pos: u[root] == 0"
  ]
}
```

### Common Pitfalls
- Failing to skip unnecessary MTZ constraints (e.g., when `i==j`), leading to a larger, less efficient model.
- Using `model.u` variables with insufficient upper bounds, which can weaken the formulation.
- Not fixing the root variable, resulting in symmetric solutions and increased solve time.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external MIP solver with appropriate optimality tolerances and runtime limits, then extract and validate the solution.

### Step 1 - Select and Configure Solver
- Instantiate a solver interface (e.g., `pyo.SolverFactory('gurobi')`).
- Set solver options: `'MIPGap': 0.0` for optimality, `'TimeLimit': time_limit`, `'Threads': num_threads`, `'Seed': seed` for reproducibility.

### Step 2 - Solve and Inspect Termination Conditions
- Execute `solver.solve(model, tee=False)` (use `tee=True` for debug output).
- Check both the solver status `pyo.check_optimal_termination(results)` and the model status `model.solutions.status`.
- Proceed only if termination is optimal or feasible.

### Step 3 - Extract Variable Values and Build Sequence
- Access variable values: `x_val = model.x[i,j].value` (values near 1.0 indicate selection).
- Reconstruct the tour: start at root, repeatedly find `next` where `model.x[current,next].value > 0.5`.
- Collect position values: `u_val[i] = model.u[i].value`.

### Step 4 - Verify Solution and Output
- Compute the total cost from the extracted tour and cost parameter to validate the objective value.
- Ensure all constraints are satisfied by the extracted values.
- Package results (status, objective, tour, positions) into a structured output.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=elements)
model.A = pyo.Set(initialize=arcs, dimen=2)
# ... [parameter, variable, constraint, and objective definition as per modeling stage]

# solve with status / termination checks
solver = pyo.SolverFactory(solver_name)
solver.options['MIPGap'] = mip_gap
solver.options['TimeLimit'] = time_limit
# ... other options
results = solver.solve(model, tee=verbose)

if pyo.check_optimal_termination(results) or model.solutions.status == pyo.SolverStatus.ok:
    # Extract solution
    tour = [root]
    current = root
    while len(tour) < len(model.N):
        for j in model.N:
            if j != current and model.x[current, j].value > 0.5:
                tour.append(j)
                current = j
                break
    obj_val = pyo.value(model.obj)
    # Output results
else:
    # Handle infeasible or unsolved case
```

### Common Pitfalls
- Relying solely on the solver's termination status without checking the model status, potentially missing infeasibility.
- Using a loose `MIPGap` when an exact solution is required, leading to suboptimal results.
- Incorrectly accessing variable values (`.value` vs `.get_values()`) leading to extraction errors.
