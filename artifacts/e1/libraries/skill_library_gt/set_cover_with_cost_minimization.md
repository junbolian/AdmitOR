---
name: Set Cover with Cost Minimization
description: |
  Model and solve set cover problems with binary selection variables and linear coverage constraints to minimize total cost, using either CP-SAT or MIP solvers via Pyomo.

---

# Workflow 1 (CP-SAT via ortools)

## Modeling stage

### Strategy Overview
Formulate the set cover problem directly for the CP-SAT solver, leveraging its native efficiency with binary variables and linear constraints. The model uses explicit dictionaries for coverage relationships and costs.

### Step 1 - Define Data Structures
- Map each selectable item (e.g., program, facility) to a unique index and a cost parameter.
- Create a coverage dictionary mapping each element (e.g., topic, customer) to a list of item indices that cover it.
- Use Python dictionaries or lists for clear, index-based access during model building.

### Step 2 - Create Binary Variables
- Instantiate a `CpModel()` object.
- For each item index, create a binary decision variable using `model.NewBoolVar(f"x_{i}")`.
- Store variables in a list or dictionary keyed by item index for easy reference.

### Step 3 - Formulate Coverage Constraints
- For each element in the coverage dictionary, retrieve its list of covering item indices.
- Construct a linear constraint: `sum(covering_variables) >= 1`.
- Add the constraint to the model using `model.Add(sum_expr >= 1)`.

### Step 4 - Define Linear Objective
- Construct the objective expression as a linear sum: `sum(cost[i] * x[i] for all items i)`.
- Set the model's objective to minimize this expression using `model.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items (indices)",
    "E: set of elements to be covered (indices)"
  ],
  "parameters": [
    "cost_i: cost of selecting item i, for i in I",
    "cover_e: list of item indices in I that cover element e, for e in E"
  ],
  "decision_variables": [
    "x_i ∈ {0,1}: 1 if item i is selected, for i in I"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} cost_i * x_i"
  },
  "constraints": [
    "coverage_e: sum_{i in cover_e} x_i >= 1, for each e in E"
  ]
}
```

### Common Pitfalls
- Forgetting to ensure all indices in `cover_e` lists are valid members of set `I`.
- Using non-linear expressions (e.g., multiplication of two variables) in the objective or constraints, which CP-SAT does not support.
- Storing variables in an unordered structure, leading to mismatched indices when building constraints.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured time and optimality tolerances, then rigorously verify solution feasibility and optimality. Output structured results for integration.

### Step 1 - Configure and Run Solver
- Create a `CpSolver()` instance.
- Set solver parameters: `solver.parameters.max_time_in_seconds = <time_limit>`, `solver.parameters.num_search_workers = <num_threads>`, `solver.parameters.random_seed = <seed>`, `solver.parameters.relative_gap_limit = 0.0` for exact solution.
- Execute `solver.Solve(model)` and capture the status.

### Step 2 - Validate Solution Status
- Check if the status is `OPTIMAL` or `FEASIBLE`. For `OPTIMAL`, the solution is proven optimal.
- If status is `INFEASIBLE`, analyze model formulation for errors.
- If status is `UNKNOWN` and time limit reached, consider relaxing the gap limit or increasing time.

### Step 3 - Extract and Verify Solution
- If feasible, iterate over all binary variables: if `solver.Value(x_i) > 0.5`, mark item `i` as selected.
- Compute total cost by summing `cost[i]` for selected items.
- Perform verification: for each element `e`, check if at least one selected item index is in its `cover_e` list. Log any uncovered elements.

### Step 4 - Confirm Optimality (Optional)
- To double-check optimality, add a new constraint to the model: `sum(cost[i] * x[i]) < current_best_cost`.
- Re-solve; if the result is `INFEASIBLE`, it confirms no better solution exists.

### Code Usage
```python
# build model from formulation
import ortools.sat.python.cp_model as cp

model = cp.CpModel()
# ... (create variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = cp.CpSolver()
# Set parameters
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in [cp.OPTIMAL, cp.FEASIBLE]:
    # Extract solution
    selected_items = [i for i in I if solver.Value(x[i]) > 0.5]
    total_cost = sum(cost[i] for i in selected_items)
    # Verification logic...
    # Output results
    print(f"RESULT:STATUS=SUCCESS")
    print(f"RESULT:OBJECTIVE={total_cost}")
else:
    print(f"RESULT:STATUS=FAILURE")
```

### Common Pitfalls
- Not checking both `OPTIMAL` and `FEASIBLE` statuses before extracting results.
- Using a non-zero `relative_gap_limit` while expecting a proven optimal solution.
- Omitting solution verification, which can miss infeasibilities due to model or data errors.

# Workflow 2 (MIP via Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the set cover problem using Pyomo's abstract modeling components, creating a ConcreteModel with sets, variables, and constraints. This approach is solver-agnostic and leverages Pyomo's integration with MIP solvers like HiGHS and CBC.

### Step 1 - Define Model and Sets
- Create a Pyomo `ConcreteModel()`.
- Define `Set` components for items (`model.I`) and elements (`model.E`).
- Use these sets to index parameters and variables.

### Step 2 - Declare Parameters and Variables
- Define a cost parameter `model.cost = Param(model.I, initialize=<cost_dict>)`.
- Define binary variables `model.x = Var(model.I, within=Binary)`.
- Store coverage relationships as a parameter or a rule: `model.cover = Param(model.E, initialize=<cover_dict>)` where each value is a list of item indices.

### Step 3 - Build Coverage Constraints via Rule
- Define a constraint rule `def coverage_rule(model, e): return sum(model.x[i] for i in model.cover[e]) >= 1`.
- Add the constraint to the model: `model.coverage = Constraint(model.E, rule=coverage_rule)`.

### Step 4 - Define the Objective Function
- Create the objective expression: `sum(model.cost[i] * model.x[i] for i in model.I)`.
- Set the model objective: `model.obj = Objective(expr=objective_expr, sense=minimize)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "E: set of elements to be covered"
  ],
  "parameters": [
    "cost[i] for i in I",
    "cover[e] for e in E (list of items in I that cover e)"
  ],
  "decision_variables": [
    "x[i] ∈ {0,1} for i in I"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} cost[i] * x[i]"
  },
  "constraints": [
    "sum_{i in cover[e]} x[i] >= 1 for each e in E"
  ]
}
```

### Common Pitfalls
- Initializing the `cover` parameter with lists containing invalid item keys, causing key errors during constraint building.
- Using mutable default arguments in Pyomo rule functions.
- Forgetting to call `model.construct()` or equivalent if using an AbstractModel (ConcreteModel builds immediately).

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver (HiGHS or CBC) with configured time limits and optimality gaps. Check solver status and termination condition rigorously before extracting and verifying results.

### Step 1 - Configure and Execute Solver
- Instantiate a solver via `SolverFactory('<solver_name>')` (e.g., `'highs'` or `'cbc'`).
- Set solver options: `'time_limit'`: `<time_limit>`, `'mip_rel_gap'`: 0.0 for optimality, `'threads'`: `<num_threads>`.
- Execute `results = solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Verify `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition`. Accept `optimal` or `feasible` for solution extraction. Treat `maxTimeLimit` as a feasible but potentially suboptimal result.
- If status is not `ok` or termination is `infeasible`, debug model or data.

### Step 3 - Extract Selected Items and Compute Cost
- Iterate over `model.x`: if `pyo.value(model.x[i]) > 0.5`, select item `i`.
- Compute total cost by summing `model.cost[i]` for selected items, or retrieve `pyo.value(model.obj)`.

### Step 4 - Verify Coverage and Output
- For each element `e`, verify `sum(pyo.value(model.x[i]) for i in model.cover[e]) >= 1`.
- Output a structured result (e.g., JSON) containing status, objective value, selected items, and verification flag.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=item_indices)
model.E = pyo.Set(initialize=element_indices)
# ... (define parameters, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver_options = {'time_limit': 30, 'mip_rel_gap': 0.0, 'threads': 4}
results = solver.solve(model, options=solver_options)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Extract solution
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = sum(pyo.value(model.cost[i]) for i in selected_items)
    # Verification logic...
    # Output results
    print(f"RESULT:STATUS=SUCCESS")
    print(f"RESULT:OBJECTIVE={total_cost}")
else:
    print(f"RESULT:STATUS=FAILURE")
```

### Common Pitfalls
- Confusing `solver.status` (process status) with `termination_condition` (solution quality).
- Not converting Pyomo variable values to floats with `pyo.value()` before comparison.
- Assuming the solver returns integer values for binary variables; always use a tolerance (e.g., `> 0.5`).
