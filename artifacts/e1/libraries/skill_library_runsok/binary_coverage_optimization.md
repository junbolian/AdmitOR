---
name: Binary Coverage Optimization
description: |
  Model and solve binary selection problems with coverage activation constraints and budget limits using dual variable structures and modern MIP solvers.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses the OR-Tools CP-SAT solver, which is designed for constraint programming and satisfiability problems expressed with linear constraints over integer/binary variables. The modeling approach directly maps the logical structure of coverage activation into linear inequalities.

### Step 1 - Define Dual Variable Structure
- Create two sets of binary decision variables: `x_j` for selecting items (e.g., facilities) and `y_i` for activating coverage outcomes (e.g., area coverage).
- This decouples the selection logic from the coverage outcome, leading to cleaner constraint formulation.

### Step 2 - Implement Coverage Activation Logic
- For each coverage outcome `i`, define a constraint: `y_i ≤ Σ_{j ∈ coverage[i]} x_j`.
- This ensures coverage can only be claimed (`y_i = 1`) if at least one covering item is selected, without forcing coverage when items are selected.
- Use a precomputed dictionary mapping each outcome to a list of covering items for efficient constraint generation.

### Step 3 - Apply Resource Constraints
- Formulate budget or resource limits as a linear sum: `Σ cost_j * x_j ≤ budget`.
- This is a standard linear constraint efficiently handled by the solver.

### Step 4 - Formulate Weighted Objective
- Define the objective to maximize total weighted coverage: `max Σ weight_i * y_i`.
- Weights represent the benefit (e.g., population, revenue) of covering each outcome.

### Formulation Template
```json
{
  "sets": [
    "I: Set of coverage outcomes (e.g., areas).",
    "J: Set of selectable items (e.g., facilities)."
  ],
  "parameters": [
    "weight_i: Benefit weight for covering outcome i ∈ I.",
    "cost_j: Cost of selecting item j ∈ J.",
    "budget: Total available budget.",
    "coverage_map: Dictionary mapping outcome i ∈ I to list of covering items j ∈ J."
  ],
  "decision_variables": [
    "x_j: Binary, 1 if item j is selected.",
    "y_i: Binary, 1 if outcome i is covered."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight_i * y_i for i in I)"
  },
  "constraints": [
    "Coverage Activation: y_i ≤ sum(x_j for j in coverage_map[i]) for each i in I.",
    "Budget: sum(cost_j * x_j for j in J) ≤ budget.",
    "Variable Domain: x_j, y_i ∈ {0, 1}."
  ]
}
```

### Common Pitfalls
- Forgetting to define the `y_i` variables as binary, leading to a relaxed problem.
- Incorrectly formulating the activation constraint as an equality, which would force coverage if any covering item is selected.
- Not precomputing the `coverage_map`, resulting in inefficient nested loops during model construction.

## Solving stage

### Strategy Overview
The solving stage involves configuring the CP-SAT solver, executing the model, and robustly extracting and verifying the solution. Emphasis is placed on status checking and structured output.

### Step 1 - Configure Solver Parameters
- Set `max_time_in_seconds` to control runtime.
- Set `num_search_workers` to leverage parallel processing.
- Set `random_seed` for reproducibility.
- For exact solutions, set `relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Invoke the solver and capture the status.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before attempting to access solution values.
- For other statuses (e.g., `INFEASIBLE`, `MODEL_INVALID`), return an informative payload with the status code.

### Step 3 - Extract and Validate Solution
- Extract selected items: `[j for j in J if solver.Value(x[j]) == 1]`.
- Extract covered outcomes: `[i for i in I if solver.Value(y[i]) == 1]`.
- Calculate derived metrics (total cost, total weight) from the extracted lists for validation and reporting.

### Step 4 - Output Standardized Results
- Structure the output as JSON with keys: `status`, `objective_value`, `selected_items`, `covered_outcomes`, `total_cost`, `total_weight`.
- This enables automated processing and comparison across different runs or formulations.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (variable and constraint creation based on formulation template)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = max_time
solver.parameters.num_search_workers = num_workers
solver.parameters.random_seed = seed
solver.parameters.relative_gap_limit = rel_gap

status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract solution
    selected = [j for j in J if solver.Value(x[j]) == 1]
    covered = [i for i in I if solver.Value(y[i]) == 1]
    # Calculate metrics and return JSON
else:
    # Handle failure, return status in JSON
```

### Common Pitfalls
- Accessing solution values without checking solver status, which causes runtime errors.
- Not setting a time limit for large instances, potentially causing the process to hang.
- Omitting the calculation of derived metrics, making solution validation and interpretation difficult.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to define the optimization problem, which is then solved by an external MIP solver (e.g., Gurobi, HiGHS, CBC). The approach emphasizes modularity, separation of data and model, and clear constraint expression.

### Step 1 - Structure Data and Sets
- Define Pyomo sets for outcomes (`model.I`) and items (`model.J`).
- Initialize parameters (`model.weight`, `model.cost`, `model.budget`) using data dictionaries or lambda functions for mapping.
- Store coverage relationships as a Pyomo parameter `model.coverage` initialized via a matrix or dictionary.

### Step 2 - Create Binary Decision Variables
- Declare `model.x` and `model.y` as `pyo.Var(..., domain=pyo.Binary)`.
- Use descriptive indices aligned with the defined sets.

### Step 3 - Build Activation and Budget Constraints
- Implement coverage constraints using a Pyomo `Constraint` list: `model.cover[i] = model.y[i] <= sum(model.coverage[i,j] * model.x[j] for j in model.J if (i,j) in coverage_data)`.
- Add the budget constraint: `sum(model.cost[j] * model.x[j] for j in model.J) <= model.budget`.

### Step 4 - Define the Maximization Objective
- Set the objective: `model.obj = pyo.Objective(expr=sum(model.weight[i] * model.y[i] for i in model.I), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": [
    "I: Pyomo Set of coverage outcomes.",
    "J: Pyomo Set of selectable items."
  ],
  "parameters": [
    "weight: Pyomo Param indexed by I, for benefit weights.",
    "cost: Pyomo Param indexed by J, for selection costs.",
    "budget: Scalar Pyomo Param or value.",
    "coverage: Pyomo Param indexed by (I,J), indicating coverage relationship (e.g., 0/1)."
  ],
  "decision_variables": [
    "x: Pyomo Var indexed by J, domain=Binary.",
    "y: Pyomo Var indexed by I, domain=Binary."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i] * y[i] for i in I)"
  },
  "constraints": [
    "CoverageActivation: y[i] <= sum(coverage[i,j] * x[j] for j in J) for each i in I.",
    "BudgetLimit: sum(cost[j] * x[j] for j in J) <= budget."
  ]
}
```

### Common Pitfalls
- Initializing Pyomo parameters with incorrect indexing, leading to key errors during model construction.
- Using Python loops to create constraints instead of Pyomo's rule-based construction, which can be slower for large models.
- Confusing Pyomo's 1-based indexing with Python's 0-based indexing when transferring data.

## Solving stage

### Strategy Overview
The solving stage involves selecting a MIP solver, configuring it with appropriate termination criteria, solving the Pyomo model, and implementing robust checks for solution status and feasibility.

### Step 1 - Select and Configure Solver
- Instantiate the solver via `SolverFactory('solver_name')` (e.g., 'gurobi', 'highs', 'cbc').
- Set solver options: `MIPGap` (or `mip_rel_gap`) to `0.0` for exact solutions, `TimeLimit` for runtime control, `Threads` for parallel processing, and `Seed` for reproducibility.

### Step 2 - Solve and Verify Status
- Execute `results = solver.solve(model, ...)`.
- Check both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`).
- Proceed only if status is `SolverStatus.ok` and termination is `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract and Verify Solution Details
- Extract selected items: `[j for j in model.J if pyo.value(model.x[j]) > 0.5]`.
- Extract covered outcomes: `[i for i in model.I if pyo.value(model.y[i]) > 0.5]`.
- Manually verify that for each covered outcome, at least one selected item provides coverage, as a sanity check against formulation errors.

### Step 4 - Report and Optionally Validate
- Print or return a structured summary including objective value, selected items with costs, covered outcomes with weights, and total cost vs. budget.
- For critical solutions, run a complementary model (e.g., minimize cost subject to achieving the same coverage) to verify optimality and explore alternative solutions.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, params, vars, constraints, objective as per formulation template)

# solve with status / termination checks
solver = pyo.SolverFactory('solver_name')
solver.options['MIPGap'] = mip_gap
solver.options['TimeLimit'] = time_limit
# ... set other options

results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}):
    # Extract solution using pyo.value
    selected = [j for j in model.J if pyo.value(model.x[j]) > 0.5]
    covered = [i for i in model.I if pyo.value(model.y[i]) > 0.5]
    # Calculate metrics and report
else:
    # Handle solver failure, report status and termination condition
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially misinterpreting suboptimal or failed solves.
- Accessing `pyo.value` on variables without ensuring the model has been solved, which may return the variable's initial value.
- Forgetting to set solver options like `TimeLimit`, leading to unexpectedly long runtimes.
