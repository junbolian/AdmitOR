---
name: Bipartite Assignment with Minimum Participation
description: |
  Model and solve bipartite resource allocation problems with minimum participation requirements using continuous assignment and binary activation variables, with linear cost minimization.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a clean, declarative MILP. It is well-suited for open-source solvers like HiGHS or CBC, offering a portable and flexible framework for constraint specification and post-solution analysis.

### Step 1 - Define Sets and Parameters
- Define two distinct sets: `I` for sources (e.g., producers) and `J` for destinations (e.g., contracts).
- Create parameter dictionaries for source capacity `cap[i]`, destination demand `dem[j]`, per-unit cost `cost[i,j]`, minimum assignment if active `min_assign[i]`, and minimum required participants per destination `min_participants[j]`.

### Step 2 - Create Decision Variables
- Declare a continuous variable `x[i,j]` representing the quantity assigned from source `i` to destination `j`.
- Declare a binary variable `y[i,j]` indicating whether source `i` is active for destination `j`.

### Step 3 - Formulate Core Constraints
- Add **source capacity constraint**: `sum(x[i,j] for j in J) <= cap[i]` for each `i in I`.
- Add **destination demand constraint**: `sum(x[i,j] for i in I) >= dem[j]` for each `j in J`.
- Add **minimum participation constraint**: `sum(y[i,j] for i in I) >= min_participants[j]` for each `j in J`.

### Step 4 - Link Assignment and Activation Variables
- Implement **minimum assignment if active**: `x[i,j] >= min_assign[i] * y[i,j]` for each `(i,j)`.
- Implement **upper bound via activation**: `x[i,j] <= cap[i] * y[i,j]` for each `(i,j)`. This ensures `x[i,j]` is zero when `y[i,j]` is zero.

### Step 5 - Define Objective
- Set the objective to minimize total linear cost: `minimize sum(cost[i,j] * x[i,j] for i in I, j in J)`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": [
    "cap[i] (capacity of source i)",
    "dem[j] (demand of destination j)",
    "cost[i,j] (unit cost)",
    "min_assign[i] (minimum flow if active)",
    "min_participants[j] (minimum active sources per destination)"
  ],
  "decision_variables": [
    "x[i,j] (continuous, assignment quantity)",
    "y[i,j] (binary, activation indicator)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i,j] for j in J) <= cap[i], for all i in I",
    "sum(x[i,j] for i in I) >= dem[j], for all j in J",
    "sum(y[i,j] for i in I) >= min_participants[j], for all j in J",
    "x[i,j] >= min_assign[i] * y[i,j], for all (i,j)",
    "x[i,j] <= cap[i] * y[i,j], for all (i,j)"
  ]
}
```

### Common Pitfalls
- Using a non-tight big-M value (e.g., a global large number) in the upper linking constraint instead of the natural bound `cap[i]`, which weakens the formulation.
- Setting the optimality gap (`mip_rel_gap`) to a negative value; use `0.0` to request an optimal solution.
- Hard-coding parameter values within constraint expressions, which reduces model reusability.

## Solving stage

### Strategy Overview
This solving stage focuses on using Pyomo's `SolverFactory` with open-source MILP solvers. It emphasizes configuration for performance, rigorous solution status checking, and systematic post-solution validation.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object using `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Configure key options: set `time_limit` (seconds), `mip_rel_gap=0.0`, and `threads` for parallel processing.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model, tee=True)` to solve and display log output.
- Check the solve status: `model.solutions.status == SolverStatus.ok`.
- Check the termination condition: `model.solutions.termination_condition` should be `optimal` or `feasible`.

### Step 3 - Extract and Validate Solution
- Extract variable values using `value(model.x[i,j])` and `value(model.y[i,j])`.
- Programmatically verify all constraints (capacity, demand, participation counts, minimum assignments) using a small epsilon (e.g., `1e-6`) for numerical tolerance.
- Summarize key metrics: objective value, source utilization rates, and destination fulfillment status.

### Step 4 - Output Structured Results
- Print a matrix of non-zero assignments `(i, j, x[i,j], y[i,j])`.
- Output a JSON-serializable summary of the solution for integration with other systems.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 300
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=True)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    # Extract and validate solution
    for i in model.I:
        for j in model.J:
            x_val = pyo.value(model.x[i,j])
            y_val = pyo.value(model.y[i,j])
            # ... store and verify ...
else:
    raise Exception(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Forgetting to check both `solver.status` and `termination_condition`, leading to extraction errors from infeasible or error states.
- Not using `tee=True` during development, which hides valuable solver progress and diagnostic information.
- Performing validation checks without an epsilon tolerance, causing false failures due to floating-point precision.

# Workflow 2 (OR-Tools with SCIP)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools (Python `pywraplp`) for a procedural, solver-centric modeling approach. It directly leverages the SCIP solver for robust MILP performance and provides fine-grained control over solver parameters.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Prepare data as lists or dictionaries: capacities `cap[i]`, demands `dem[j]`, costs `cost[i][j]`, minimum assignments `min_assign[i]`, and minimum participants `min_participants[j]`.

### Step 2 - Create Variable Arrays
- Create a 2D array of continuous variables `x[i][j] = solver.NumVar(0, solver.infinity(), f"x_{i}_{j}")`.
- Create a corresponding 2D array of binary variables `y[i][j] = solver.IntVar(0, 1, f"y_{i}_{j}")`.

### Step 3 - Add Constraints via Nested Loops
- Add **source capacity**: `solver.Add(sum(x[i][j] for j in J) <= cap[i])` for each `i`.
- Add **destination demand**: `solver.Add(sum(x[i][j] for i in I) >= dem[j])` for each `j`.
- Add **minimum participation**: `solver.Add(sum(y[i][j] for i in I) >= min_participants[j])` for each `j`.

### Step 4 - Add Linking Constraints
- Add **minimum if active**: `solver.Add(x[i][j] >= min_assign[i] * y[i][j])` for each pair `(i,j)`.
- Add **upper bound linkage**: `solver.Add(x[i][j] <= cap[i] * y[i][j])` for each pair `(i,j)`.

### Step 5 - Set Linear Objective
- Initialize objective: `objective = solver.Objective()`.
- Set all coefficients: `objective.SetCoefficient(x[i][j], cost[i][j])`.
- Set minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["I (indexed by i)", "J (indexed by j)"],
  "parameters": [
    "cap[i]",
    "dem[j]",
    "cost[i][j]",
    "min_assign[i]",
    "min_participants[j]"
  ],
  "decision_variables": [
    "x[i][j] (solver.NumVar)",
    "y[i][j] (solver.IntVar, binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "sum_j x[i][j] <= cap[i]",
    "sum_i x[i][j] >= dem[j]",
    "sum_i y[i][j] >= min_participants[j]",
    "x[i][j] >= min_assign[i] * y[i][j]",
    "x[i][j] <= cap[i] * y[i][j]"
  ]
}
```

### Common Pitfalls
- Using `solver.infinity()` as the upper bound in the linking constraint instead of the tighter `cap[i]`, which reduces solver efficiency.
- Adding constraints in an order that obscures logical grouping, making debugging more difficult.
- Not naming variables when creating them, which leads to uninformative error messages.

## Solving stage

### Strategy Overview
This solving stage focuses on configuring the OR-Tools SCIP solver for performance, executing the solve, and extracting the solution with explicit checks for optimality or feasibility.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.SetTimeLimit(30000)` (milliseconds).
- Set the number of threads: `solver.SetNumThreads(4)`.
- Optionally set other SCIP-specific parameters via `solver.SetSolverSpecificParametersAsString()`.

### Step 2 - Solve and Inspect Result Status
- Execute `solver.Solve()`.
- Check the result status: `status = solver.Solve()`.
- Accept solutions that are `OPTIMAL` (`pywraplp.Solver.OPTIMAL`) or `FEASIBLE` (`pywraplp.Solver.FEASIBLE`).

### Step 3 - Extract Solution Values
- For each variable, retrieve its value: `x_val = x[i][j].solution_value()` and `y_val = y[i][j].solution_value()`.
- Use a small threshold (e.g., `1e-6`) to determine if a binary variable is effectively 1 or 0.

### Step 4 - Verify and Summarize
- Compute aggregates (total flow per source, per destination) to verify constraints are satisfied within tolerance.
- Print a summary table showing active assignments and their quantities.
- Calculate and report the total cost from the extracted solution.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... create variables and add constraints ...
objective = solver.Objective()
for i in I:
    for j in J:
        objective.SetCoefficient(x[i][j], cost[i][j])
objective.SetMinimization()

# solve with status / termination checks
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    # Extract solution
    solution = {}
    for i in I:
        for j in J:
            if x[i][j].solution_value() > 1e-6:
                solution[(i,j)] = (x[i][j].solution_value(), y[i][j].solution_value())
    # ... verify and output ...
else:
    print(f"No feasible solution found. Status: {status}")
```

### Common Pitfalls
- Confusing `solver.Solve()` (which returns status) with `solver.Objective().Value()` (which returns objective value) before checking status.
- Not using `.solution_value()` method and instead trying to print the variable object directly.
- Ignoring the `FEASIBLE` status, which may still provide a useful incumbent solution even if optimality isn't proven.
