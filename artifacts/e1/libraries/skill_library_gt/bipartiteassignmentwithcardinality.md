---
name: BipartiteAssignmentWithCardinality
description: |
  Model and solve bipartite assignment problems with one-to-one matching constraints and a fixed total number of assignments, minimizing total cost.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, designed for constraint programming and integer optimization. It is well-suited for problems with combinatorial constraints and benefits from built-in search strategies and parallelization.

### Step 1 - Define Sets and Parameters
- Define two finite sets, `SetA` and `SetB`, representing the elements to be matched.
- Define a 2D cost matrix `cost[i][j]` as a parameter, representing the cost of assigning element `i` from `SetA` to element `j` from `SetB`.
- Define a scalar parameter `K` for the exact number of total assignments required.

### Step 2 - Create Binary Decision Variables
- Create a binary decision variable `x[i][j]` for each possible pair `(i, j)` using `model.NewBoolVar()`.
- The variable `x[i][j]` equals 1 if the assignment is active, and 0 otherwise.

### Step 3 - Formulate One-to-One Matching Constraints
- For each element `i` in `SetA`, add a constraint `sum(x[i][j] for j in SetB) <= 1`.
- For each element `j` in `SetB`, add a constraint `sum(x[i][j] for i in SetA) <= 1`.
- This ensures each element is assigned to at most one partner.

### Step 4 - Formulate Exact Cardinality Constraint
- Add a global constraint `sum(x[i][j] for i in SetA for j in SetB) == K`.
- This enforces the exact total number of active assignments.

### Step 5 - Define Linear Minimization Objective
- Define the objective as `minimize sum(cost[i][j] * x[i][j] for i in SetA for j in SetB)`.

### Formulation Template
```json
{
  "sets": ["SetA", "SetB"],
  "parameters": [
    {"name": "cost", "type": "dict", "keys": ["i", "j"]},
    {"name": "K", "type": "scalar"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["i", "j"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in SetA for j in SetB)"
  },
  "constraints": [
    {"name": "one_per_A", "expression": "sum(x[i][j] for j in SetB) <= 1 for all i in SetA"},
    {"name": "one_per_B", "expression": "sum(x[i][j] for i in SetA) <= 1 for all j in SetB"},
    {"name": "total_assignments", "expression": "sum(x[i][j] for i in SetA for j in SetB) == K"}
  ]
}
```

### Common Pitfalls
- Forgetting to enforce the `<= 1` constraints in both directions, which can lead to invalid many-to-one assignments.
- Setting the parameter `K` to a value larger than `min(len(SetA), len(SetB))`, which makes the problem trivially infeasible.
- Using floating-point numbers for `cost` without scaling, which can cause precision issues in the solver.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver with practical limits for time and optimality. Extract and verify the solution, ensuring it meets all constraints and matches the reported objective value.

### Step 1 - Configure Solver Parameters
- Initialize the solver: `solver = cp_model.CpSolver()`.
- Set a time limit: `solver.parameters.max_time_in_seconds = 30`.
- Enable parallel search: `solver.parameters.num_search_workers = 8`.
- Set a random seed for reproducibility: `solver.parameters.random_seed = 42`.
- Enforce exact solution search: `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Invoke the solver: `status = solver.Solve(model)`.
- Check for a feasible or optimal solution: `if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):`.

### Step 3 - Extract and Validate Solution
- Iterate over all `(i, j)` pairs. If `solver.Value(x[i][j]) == 1`, record the assignment.
- Store the list of active assignments `[(i, j, cost[i][j]), ...]`.
- Optionally, compute the sum of costs for the selected assignments and verify it equals `solver.ObjectiveValue()`.

### Step 4 - Implement Verification Protocol
- Programmatically verify constraints: each row and column sum of assignments is ≤ 1, and the total number of assignments equals `K`.
- For debugging, print a clear summary including status, objective value, and assignment details.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (create variables, add constraints, set objective)
# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = []
    total_cost = 0
    for i in SetA:
        for j in SetB:
            if solver.Value(x[i][j]) == 1:
                assignments.append((i, j, cost[i][j]))
                total_cost += cost[i][j]
    print(f"Objective value: {solver.ObjectiveValue()}")
    print(f"Assignments: {assignments}")
    # Add verification checks here
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing valid but non-optimal solutions.
- Assuming variable values are integers without calling `solver.Value()`, which returns a Python `int`.
- Omitting solution verification, which can mask modeling errors if the solver returns an incorrect status.

# Workflow 2 (MIP with Pyomo and HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for algebraic modeling and the HiGHS solver for mixed-integer programming. It is ideal for users familiar with declarative modeling and integrates well with scientific Python ecosystems.

### Step 1 - Declare Abstract Sets and Parameters
- Declare abstract sets `model.SetA` and `model.SetB` using `pyo.Set()`.
- Define a parameter `model.cost` indexed by `(i, j)` using `pyo.Param(model.SetA, model.SetB, initialize=cost_dict)`.
- Define a scalar parameter `model.K` for the required number of assignments.

### Step 2 - Define Binary Variables with Pyomo
- Define binary decision variables `model.x` indexed over `model.SetA` and `model.SetB` with `domain=pyo.Binary`.

### Step 3 - Enforce Matching and Cardinality Constraints
- Add constraints `model.row_sum` using `pyo.Constraint(model.SetA, rule=lambda m, i: sum(m.x[i, j] for j in m.SetB) <= 1)`.
- Add constraints `model.col_sum` using `pyo.Constraint(model.SetB, rule=lambda m, j: sum(m.x[i, j] for i in m.SetA) <= 1)`.
- Add a global cardinality constraint `model.total_assignments` using `pyo.Constraint(expr=sum(m.x[i, j] for i in m.SetA for j in m.SetB) == m.K)`.

### Step 4 - Construct Linear Objective
- Define the objective as `model.obj = pyo.Objective(expr=sum(m.cost[i, j] * m.x[i, j] for i in m.SetA for j in m.SetB), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["SetA", "SetB"],
  "parameters": [
    {"name": "cost", "type": "dict", "keys": ["i", "j"]},
    {"name": "K", "type": "scalar"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indices": ["i", "j"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in SetA for j in SetB)"
  },
  "constraints": [
    {"name": "one_per_A", "expression": "sum(x[i, j] for j in SetB) <= 1 for all i in SetA"},
    {"name": "one_per_B", "expression": "sum(x[i, j] for i in SetA) <= 1 for all j in SetB"},
    {"name": "total_assignments", "expression": "sum(x[i, j] for i in SetA for j in SetB) == K"}
  ]
}
```

### Common Pitfalls
- Initializing the `cost` parameter with a dictionary that has missing keys for some `(i, j)` pairs, causing KeyError during model construction.
- Using `==` instead of `<=` in the one-to-one constraints, which incorrectly forces every element to have an assignment.
- Not scaling the objective when costs are very large or small, which can lead to numerical instability in the solver.

## Solving stage

### Strategy Overview
Instantiate a concrete model, configure the HiGHS solver with appropriate options for MIP solving, handle potential infeasibility, and extract the solution for validation.

### Step 1 - Instantiate Model and Configure Solver
- Create a solver instance: `solver = pyo.SolverFactory('appsi_highs')` or `solver = pyo.SolverFactory('highs')`.
- Set solver options: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0`, `solver.options['threads'] = 4`.

### Step 2 - Solve with Robust Error Handling
- Wrap the solve call in a try-except block to catch `ValueError` or `RuntimeError` on infeasibility.
- Check the solver termination condition and status after solving: `results = solver.solve(model, tee=False)`.

### Step 3 - Extract Solution and Verify
- Iterate over `model.x`. If `pyo.value(model.x[i, j]) > 0.5`, record the assignment.
- Compute the objective value from the extracted assignments for cross-validation.
- For small instances, implement a brute-force check to verify optimality or infeasibility.

### Step 4 - Output Structured Results
- Package results into a dictionary or JSON object containing solution status, objective value, and list of assignments.
- Print a clear summary for user inspection.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.SetA = pyo.Set(initialize=SetA)
model.SetB = pyo.Set(initialize=SetB)
model.cost = pyo.Param(model.SetA, model.SetB, initialize=cost_dict)
model.K = pyo.Param(initialize=K)
model.x = pyo.Var(model.SetA, model.SetB, domain=pyo.Binary)
# ... (add constraints and objective)
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -0.0
try:
    results = solver.solve(model)
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        assignments = []
        for i in model.SetA:
            for j in model.SetB:
                if pyo.value(model.x[i, j]) > 0.5:
                    assignments.append((i, j, pyo.value(model.cost[i, j])))
        print(f"Objective value: {pyo.value(model.obj)}")
        print(f"Assignments: {assignments}")
    else:
        print(f"Solver terminated with condition: {results.solver.termination_condition}")
except Exception as e:
    print(f"Solver failed with error: {e}")
```

### Common Pitfalls
- Not checking `pyo.value(model.x[i, j]) > 0.5` due to floating-point precision, potentially missing active assignments.
- Ignoring the solver termination condition and assuming `optimal` means a feasible solution was found and loaded.
- Failing to load the solution into the model object before accessing variable values, resulting in `None`.
