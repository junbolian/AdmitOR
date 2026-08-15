---
name: Assignment Problem with Cardinality and Pairwise Constraints
description: |
  Model and solve binary assignment problems with cardinality constraints, pairwise exclusions, and linear cost minimization using modern MIP/CP-SAT solvers.

---
# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, ideal for combinatorial assignment problems with logical constraints. It leverages efficient Boolean variable handling and native support for linear constraints.

### Step 1 - Define Binary Assignment Variables
- Create a dictionary of Boolean variables `x[i, j]` for each potential assignment between elements of set `I` and set `J`.
- Use `model.NewBoolVar(f"x_{i}_{j}")` for clear naming and easy access via tuple keys.

### Step 2 - Formulate Linear Cost Objective
- Define a cost parameter `cost[i, j]` for each assignment pair.
- Build the objective expression as the sum of `cost[i, j] * x[i, j]` over all `i, j`.
- Set the model objective to minimize this sum using `model.Minimize(objective_expr)`.

### Step 3 - Enforce Cardinality Constraints
- For each element `i` in set `I`, add a constraint `sum(x[i, j] for j in J) <= 1` to enforce at most one assignment per `i`.
- For each element `j` in set `J`, add a constraint `sum(x[i, j] for i in I) <= 1` to enforce at most one assignment per `j`.
- Add a global constraint `sum(x[i, j] for all i, j) == K` to enforce an exact total number of assignments `K`.

### Step 4 - Implement Pairwise Exclusion Constraints
- For each required pairwise restriction, define a tuple `(i1, j1, i2, j2, max_sum)`.
- Add a linear constraint `x[i1, j1] + x[i2, j2] <= max_sum` to the model.

### Formulation Template
```json
{
  "sets": [
    "I = [...]",
    "J = [...]"
  ],
  "parameters": [
    "cost[i in I, j in J] = ...",
    "K = ...",
    "pairwise_constraints = [(i1, j1, i2, j2, max_sum), ...]"
  ],
  "decision_variables": [
    "x[i in I, j in J] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i, j] for j in J) <= 1, for all i in I",
    "sum(x[i, j] for i in I) <= 1, for all j in J",
    "sum(x[i, j] for all i in I, j in J) == K",
    "x[i1, j1] + x[i2, j2] <= max_sum, for all (i1, j1, i2, j2, max_sum) in pairwise_constraints"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce both dimensions of cardinality constraints, leading to invalid many-to-many assignments.
- Using floating-point costs directly in CP-SAT; scale to integers if necessary for exact arithmetic.
- Not handling missing cost data explicitly, which can cause `KeyError`; ensure the cost dictionary is complete or use a default high penalty.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with performance-oriented parameters, extract the solution, and validate all constraints. This stage focuses on robust execution and result verification.

### Step 1 - Configure and Run Solver
- Initialize the solver: `solver = cp_model.CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds = TIMEOUT`, `solver.parameters.num_search_workers = NUM_WORKERS`, `solver.parameters.random_seed = SEED` for reproducibility.
- Execute the solve: `status = solver.Solve(model)`.

### Step 2 - Check Solution Status and Extract Results
- Verify the solve status: `if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):`.
- Extract the objective value: `total_cost = solver.ObjectiveValue()`.
- Iterate through all `x[i, j]` variables and collect assignments where `solver.Value(x[i, j]) == 1`.

### Step 3 - Validate Solution and Output
- Programmatically verify that the extracted assignments satisfy all cardinality and pairwise constraints.
- Print a clear summary including status, total cost, and list of assignments.
- Format the final cost output as `RESULT:{total_cost}` for automated parsing.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (variable creation, objective, constraints as per modeling stage)
# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    total_cost = solver.ObjectiveValue()
    assignments = [(i, j) for (i, j), var in x.items() if solver.Value(var) == 1]
    print(f"RESULT:{total_cost}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid suboptimal solutions.
- Assuming variable values are exactly 0 or 1; always compare using `== 1` for clarity.
- Omitting post-solve validation, which can miss subtle constraint violations.

# Workflow 2 (MIP with Pyomo and Gurobi)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model formulation and Gurobi as the MIP solver, suitable for problems where a traditional algebraic modeling language is preferred. It emphasizes clear set-based indexing and parameter management.

### Step 1 - Define Sets and Indexed Variables
- Declare Pyomo sets `model.I` and `model.J` for the two assignment dimensions.
- Create binary variables `model.x` indexed over `model.I * model.J` using `pyo.Var(..., domain=pyo.Binary)`.

### Step 2 - Build Objective with Cost Parameter
- Define a Pyomo parameter `model.cost` indexed by `(I, J)`.
- Construct the objective as the sum of `model.cost[i, j] * model.x[i, j]` and set it for minimization.

### Step 3 - Enforce Constraints via Rules
- Implement a Pyomo `ConstraintList` or use rule-based constraints.
- Add cardinality constraints: `sum(model.x[i, j] for j in model.J) <= 1` for each `i`, and vice versa.
- Add the total assignment constraint: `sum(model.x[i, j] for i in model.I, j in model.J) == K`.
- Add pairwise exclusion constraints by iterating over a list of `(i1, j1, i2, j2, max_sum)` tuples.

### Step 4 - Handle Incomplete Cost Data
- For assignments with unknown cost, set `model.cost[i, j]` to a sufficiently large penalty value (e.g., `M`) to discourage selection while maintaining feasibility.

### Formulation Template
```json
{
  "sets": [
    "I = {...}",
    "J = {...}"
  ],
  "parameters": [
    "cost[i in I, j in J] = ... (use a large M for unknown entries)",
    "K = ...",
    "exclusion_list = [(i1, j1, i2, j2, max_sum), ...]"
  ],
  "decision_variables": [
    "x[i in I, j in J] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i, j] for j in J) <= 1, ∀ i ∈ I",
    "sum(x[i, j] for i in I) <= 1, ∀ j ∈ J",
    "sum(x[i, j] for i in I, j in J) == K",
    "x[i1, j1] + x[i2, j2] <= max_sum, ∀ (i1, j1, i2, j2, max_sum) ∈ exclusion_list"
  ]
}
```

### Common Pitfalls
- Defining Pyomo `Set` objects incorrectly, leading to indexing errors; initialize with concrete lists.
- Forgetting to deactivate the default `Objective` rule when adding a new objective in a `ConcreteModel`.
- Using the same large penalty `M` for all unknown costs, which can mask degeneracy; consider scaled penalties if cost ranges vary.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the Gurobi solver with appropriate tolerances and time limits. Focus on extracting and verifying the solution through Pyomo's result interfaces.

### Step 1 - Configure Solver and Solve
- Instantiate the solver: `solver = pyo.SolverFactory('gurobi')`.
- Set solver options: `solver.options['TimeLimit'] = TIMEOUT`, `solver.options['MIPGap'] = 0.0` for optimality, `solver.options['Seed'] = SEED`.
- Execute the solve: `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Termination Status
- Check the solver status: `if results.solver.status == pyo.SolverStatus.ok:`.
- Check the termination condition: `if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):`.

### Step 3 - Extract and Report Solution
- Retrieve the objective value: `total_cost = pyo.value(model.obj)`.
- Iterate over the `model.x` variable to find indices where `pyo.value(model.x[i, j]) > 0.5`.
- Output the total cost in the parseable format `RESULT:{total_cost}` and optionally list assignments.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_LIST)
model.J = pyo.Set(initialize=J_LIST)
model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)
# ... (objective and constraints as per modeling stage)
# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = -1.0  # Use -1.0 for optimality tolerance
results = solver.solve(model)
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    print(f"RESULT:{total_cost}")
else:
    print("Solver failed to find a feasible solution.")
```

### Common Pitfalls
- Confusing `solver.status` with `termination_condition`; both must be checked to confirm a valid solution.
- Not accounting for solver tolerances when checking binary variable values; use a threshold (e.g., `> 0.5`).
- Assuming the model is solved in-place; `solve` returns a results object, but the model object is also updated.
