---
name: Cardinality-Constrained Pairwise Selection
description: |
  Model and solve binary selection problems with cardinality constraints and pairwise activation objectives using either linearized CP-SAT or direct quadratic MIP approaches.

---
# Workflow 1 (Linearized CP-SAT)

## Modeling stage

### Strategy Overview
This workflow linearizes the quadratic pairwise activation objective using auxiliary Boolean variables and constraints, suitable for solvers like CP-SAT that handle linear constraints efficiently but not native quadratic terms.

### Step 1 - Define Core Selection Variables
- Create a binary decision variable `x[i]` for each element `i` in the selection set `N`. This variable indicates whether element `i` is selected.
- Use `model.NewBoolVar(f"x_{i}")` to instantiate each variable.

### Step 2 - Enforce Cardinality Constraint
- Add a linear constraint to enforce the selection of exactly `k` elements: `sum(x[i] for i in N) == k`.
- Use `model.Add(sum_expr == k)` where `sum_expr` is a linear expression of the `x` variables.

### Step 3 - Linearize Pairwise Activation
- For each unordered pair `(i, j)` where `i < j`, create an auxiliary binary variable `y[i,j]` representing the logical AND of `x[i]` and `x[j]`.
- Enforce the equivalence `y[i,j] == x[i] ∧ x[j]` using three linear constraints:
  1. `y[i,j] <= x[i]`
  2. `y[i,j] <= x[j]`
  3. `y[i,j] >= x[i] + x[j] - 1`

### Step 4 - Formulate Objective
- Define the objective as the maximization of the sum of pairwise benefits: `maximize sum(benefit[i,j] * y[i,j] for all pairs)`.
- Use `model.Maximize(objective_expr)` where `objective_expr` is a linear expression summing the weighted `y` variables.

### Formulation Template
```json
{
  "sets": [
    "N: set of selectable elements",
    "P: set of unordered pairs (i,j) where i<j and benefit is defined"
  ],
  "parameters": [
    "k: integer cardinality (number of elements to select)",
    "benefit_ij: parameter for pairwise benefit for pair (i,j) in P"
  ],
  "decision_variables": [
    "x_i: binary, 1 if element i in N is selected",
    "y_ij: binary, 1 if both i and j are selected (for (i,j) in P)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{(i,j) in P} benefit_ij * y_ij"
  },
  "constraints": [
    "sum_{i in N} x_i == k",
    "y_ij <= x_i for all (i,j) in P",
    "y_ij <= x_j for all (i,j) in P",
    "y_ij >= x_i + x_j - 1 for all (i,j) in P"
  ]
}
```

### Common Pitfalls
- Creating auxiliary variables for pairs where the benefit is zero, unnecessarily increasing model size.
- Misinterpreting asymmetric pairwise benefits as symmetric, leading to incorrect objective calculation.
- Forgetting to enforce `i < j` when generating pairs, resulting in duplicate variables and constraints.

## Solving stage

### Strategy Overview
Solve the linearized model using a CP-SAT solver (e.g., Google OR-Tools CP-SAT). Configure for exact solution, handle solver statuses, and verify results.

### Step 1 - Configure Solver
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds` for a runtime limit, `solver.parameters.num_search_workers` for parallelism, and `solver.parameters.random_seed` for reproducibility.
- For an exact solution, set `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Execute the solver: `status = solver.Solve(model)`.
- Check if the status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before proceeding. Handle `cp_model.INFEASIBLE` or `cp_model.UNKNOWN` appropriately (e.g., log error, adjust model).

### Step 3 - Extract and Verify Solution
- Retrieve selected elements: `selected = [i for i in N if solver.Value(x[i]) == 1]`.
- Obtain the objective value: `obj_value = solver.ObjectiveValue()`.
- For validation, recompute the objective directly from the `selected` list and the `benefit` matrix to ensure consistency with the solver's reported value.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (create variables, add constraints, set objective as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters (e.g., solver.parameters.max_time_in_seconds = time_limit)
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected_items = [i for i in N if solver.Value(x[i]) == 1]
    reported_obj = solver.ObjectiveValue()
    # Optional verification
    # ...
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Trusting solver output without independent verification, especially when using auxiliary variables.
- Not setting a time limit for large instances, potentially causing excessive runtime.
- Ignoring solver status and attempting to read solution values from an infeasible or unknown result.

# Workflow 2 (Direct Quadratic MIP)

## Modeling stage

### Strategy Overview
This workflow models the pairwise activation objective directly as a quadratic function, leveraging solvers with native support for quadratic objectives (e.g., HiGHS, Gurobi, CPLEX) to avoid manual linearization.

### Step 1 - Define Selection Variables
- Create binary decision variables `x[i]` for each element `i` in the selection set `N`.
- Use `model.binary_var(name=f"x_{i}")` or equivalent in your modeling framework.

### Step 2 - Apply Cardinality Constraint
- Add a linear constraint: `sum(x[i] for i in N) == k`.
- Use `model.add_constraint(sum_expr == k)`.

### Step 3 - Formulate Quadratic Objective
- Define the objective to maximize the sum of pairwise benefits multiplied by the product of selection variables: `maximize sum(benefit[i,j] * x[i] * x[j] for all pairs)`.
- Use `model.maximize(objective_expr)` where `objective_expr` is a quadratic expression. Ensure the modeling framework supports quadratic objectives.

### Step 4 - Handle Pair Directionality
- If pairwise benefits are symmetric, store parameters for unordered pairs `(i,j)` with `i < j` to avoid double-counting in the objective.
- If benefits are asymmetric, include both ordered terms `benefit[i,j] * x[i] * x[j]` and `benefit[j,i] * x[j] * x[i]` as needed.

### Formulation Template
```json
{
  "sets": [
    "N: set of selectable elements",
    "P: set of pairs (i,j) where benefit is defined (specify if ordered or unordered)"
  ],
  "parameters": [
    "k: integer cardinality",
    "benefit_ij: parameter for pairwise benefit for pair (i,j) in P"
  ],
  "decision_variables": [
    "x_i: binary, 1 if element i in N is selected"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{(i,j) in P} benefit_ij * x_i * x_j"
  },
  "constraints": [
    "sum_{i in N} x_i == k"
  ]
}
```

### Common Pitfalls
- Using a solver that does not support quadratic objectives, resulting in an error.
- Incorrectly modeling asymmetric pairwise interactions as symmetric, distorting the objective value.
- Creating an overly dense quadratic objective for large `N`, which can impact solver performance.

## Solving stage

### Strategy Overview
Solve the quadratic model using a MIP solver with quadratic support. Configure solver options, carefully handle solution loading, and implement a fallback verification strategy.

### Step 1 - Configure and Solve
- Instantiate the solver appropriate for your modeling framework (e.g., `SolverFactory('highs')` for Pyomo).
- Set solver options: `time_limit` for runtime control, `mip_rel_gap=0.0` for exact solutions, and `threads` for parallelism.
- Solve the model with `results = solver.solve(model, ...)`. Use `load_solutions=False` if supported to defer solution loading until after status check.

### Step 2 - Validate Solver Status
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `TerminationCondition.feasible`).
- Only load the solution into the model if the status indicates success. Manually load if needed: `model.solutions.load_from(results)`.

### Step 3 - Extract Solution and Implement Fallback
- Extract selected elements: `selected = [i for i in N if value(x[i]) > 0.5]`.
- For small combinatorial problems (`n choose k` is manageable), if the solver fails, implement a brute-force fallback using `itertools.combinations` to enumerate all selections and evaluate the objective directly.
- Always verify the objective value by recalculating from the selected items and the benefit matrix.

### Code Usage
```python
# build model from formulation (using a framework like Pyomo)
model = ConcreteModel()
# ... (create variables, add constraints, set quadratic objective)

# solve with status / termination checks
solver = SolverFactory('solver_name')
solver.options['time_limit'] = time_limit
solver.options['mip_rel_gap'] = 0.0
# Use load_solutions=False for control
results = solver.solve(model, load_solutions=False)

if results.solver.status == SolverStatus.ok and results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]:
    model.solutions.load_from(results)  # If load_solutions=False was used
    selected_items = [i for i in N if value(model.x[i]) > 0.5]
    # Optional verification and fallback
    # ...
else:
    # Consider fallback enumeration for small instances
    # ...
```

### Common Pitfalls
- Loading solutions automatically without checking termination condition, potentially reading invalid values.
- Setting invalid solver parameter values (e.g., negative MIP gap) without consulting documentation.
- Not having a fallback plan for small instances when the solver interface fails consistently.
