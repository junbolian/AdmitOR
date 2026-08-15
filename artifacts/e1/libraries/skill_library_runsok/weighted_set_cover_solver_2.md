---
name: Weighted Set Cover Solver
description: |
  Model and solve weighted set cover problems using binary selection variables, set cover constraints, and weighted sum minimization across multiple solver backends.
---

# Workflow 1 (MIP Solver with OR-Tools or Pyomo)

## Modeling stage

### Strategy Overview
Formulate the weighted set cover problem as a Mixed-Integer Program (MIP) using a high-level modeling library. This approach provides a clear algebraic representation, separation of model and data, and flexibility in solver choice.

### Step 1 - Define Sets and Parameters
- Identify the set of selectable items (e.g., facilities, resources) and the set of elements to be covered (e.g., service areas, requirements).
- Define a cost parameter for each item and a coverage mapping from each element to the list of items that cover it.
- Use dictionaries or lists for efficient data storage and access during model construction.

### Step 2 - Create Binary Decision Variables
- Instantiate a binary decision variable for each selectable item, where a value of 1 indicates selection.
- Use the modeling library's variable constructor (e.g., `pyo.Var(domain=pyo.Binary)` or `solver.IntVar(0, 1, ...)`).

### Step 3 - Formulate the Weighted Objective
- Construct the objective function as the sum of each item's cost multiplied by its selection variable.
- Set the sense to minimization.

### Step 4 - Enforce Set Cover Constraints
- For each element to be covered, create a constraint that the sum of selection variables for all items covering that element is at least 1.
- Iterate through the coverage mapping to build these constraints efficiently.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "J: set of elements to cover"
  ],
  "parameters": [
    "cost_i: cost of selecting item i ∈ I",
    "cover_j: list of items i ∈ I that cover element j ∈ J"
  ],
  "decision_variables": [
    "x_i ∈ {0,1}: 1 if item i is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} cost_i * x_i"
  },
  "constraints": [
    "∑_{i ∈ cover_j} x_i ≥ 1, ∀ j ∈ J"
  ]
}
```

### Common Pitfalls
- Using 1-indexed data (e.g., facility numbers) directly in 0-indexed Python lists, causing index errors. Always convert indices appropriately.
- Assuming the solver's solution is feasible without explicit verification. Always implement a post-solution coverage check.
- Forgetting to set a time limit or optimality gap, which can lead to excessively long runtimes for large instances.

## Solving stage

### Strategy Overview
Solve the MIP model using a dedicated solver backend (e.g., HiGHS, CBC, SCIP) configured for performance and optimality. Handle solver statuses robustly and verify the solution's feasibility and coverage.

### Step 1 - Configure and Run the Solver
- Instantiate the solver factory (e.g., `pyo.SolverFactory("highs")` or `pywraplp.Solver.CreateSolver("SCIP")`).
- Set key parameters: a time limit, optimality gap (`mip_rel_gap=0.0` or `relative_gap_limit=0.0`), and number of threads for parallelism.
- Call the solver's solve method, optionally enabling output logs for debugging.

### Step 2 - Check Solver Status and Termination
- After solving, inspect the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- Proceed only if the status indicates a valid solution; otherwise, handle the error with informative output.

### Step 3 - Extract and Verify the Solution
- Retrieve the objective value and iterate over decision variables, collecting items where the solution value exceeds 0.5 as selected.
- Perform an independent verification: for each element, check if at least one selected item belongs to its coverage list.
- If verification fails, log the uncovered elements and treat the solution as invalid.

### Step 4 - Output Standardized Results
- Format the results into a consistent structure (e.g., JSON) containing the status, total cost, list of selected items, and verification outcome.
- Print or return the results for downstream use.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Define data: sets I, J; dict cost; dict coverage
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=elements)
model.x = pyo.Var(model.I, domain=pyo.Binary)
model.obj = pyo.Objective(expr=sum(cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)
def coverage_rule(m, j):
    return sum(m.x[i] for i in coverage[j]) >= 1
model.coverage = pyo.Constraint(model.J, rule=coverage_rule)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = pyo.value(model.obj)
    # Verification loop
    all_covered = all(any(s in coverage[j] for s in selected) for j in model.J)
    output = {"status": "success", "cost": total_cost, "selected": selected, "verified": all_covered}
else:
    output = {"status": "failed", "message": f"Solver terminated with {term}"}
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to extraction errors from incomplete solves.
- Using floating-point equality (`== 1.0`) to test binary variable values; use a tolerance (e.g., `> 0.5`) instead.
- Omitting the independent verification step, which can miss infeasible solutions due to solver tolerances or model errors.

# Workflow 2 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem using Google OR-Tools' CP-SAT solver, which is designed for combinatorial problems with Boolean logic. This approach uses a constraint programming paradigm with efficient propagation and search, often effective for set cover instances.

### Step 1 - Map Items and Coverage
- Define the list of selectable items and the list of elements to cover.
- Store costs in a list and coverage relationships as a list of lists, where each sublist contains the indices of items covering a specific element.

### Step 2 - Create Boolean Decision Variables
- For each selectable item, create a Boolean decision variable using `model.NewBoolVar()`.
- These variables can be used directly in linear constraints and the objective.

### Step 3 - Define Linear Coverage Constraints
- For each element, create a linear constraint: the sum of Boolean variables for covering items must be at least 1.
- Use `model.Add(sum(variables) >= 1)`.

### Step 4 - Set Weighted Minimization Objective
- Create a linear expression summing each item's cost multiplied by its Boolean variable.
- Pass this expression to `model.Minimize()`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items",
    "J: set of elements to cover"
  ],
  "parameters": [
    "cost_i: cost of selecting item i ∈ I",
    "cover_j: list of item indices i ∈ I that cover element j ∈ J"
  ],
  "decision_variables": [
    "b_i ∈ {0,1}: Boolean variable for item i"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} cost_i * b_i"
  },
  "constraints": [
    "∑_{i ∈ cover_j} b_i ≥ 1, ∀ j ∈ J"
  ]
}
```

### Common Pitfalls
- Using integer variables instead of Boolean variables, which reduces solver efficiency for this problem class.
- Neglecting to convert 1-indexed input data (common in coverage lists) to 0-indexed for Python, causing index-out-of-range errors.
- Building the objective with floating-point costs when CP-SAT requires integer coefficients; scale costs to integers if necessary.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured search parameters for optimality. Leverage the solver's ability to prove optimality and use parallel search workers. Implement robust solution extraction and verification.

### Step 1 - Configure Solver Parameters
- Set a maximum time limit (`model.parameters.max_time_in_seconds`).
- Enable parallel search (`model.parameters.num_search_workers`).
- Set a relative gap limit to 0 for exact solutions (`model.parameters.relative_gap_limit = 0.0`).
- Optionally set a random seed for reproducibility.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the result status: `cp_model.OPTIMAL` confirms optimality; `cp_model.FEASIBLE` indicates a feasible solution.

### Step 3 - Extract Selected Items
- If the status is optimal or feasible, iterate over Boolean variables and collect those with solution value `True`.
- Compute the total cost by summing costs of selected items or by evaluating the objective expression.

### Step 4 - Verify Coverage and Validate
- Perform an independent verification: for each element, check if any selected item index appears in its coverage list.
- For small instances, consider an exhaustive enumeration (e.g., checking all k-combinations) to confirm optimality.
- Output results in a standardized format.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# Data: list costs, list of lists coverage
n_items = len(costs)
vars = [model.NewBoolVar(f"x_{i}") for i in range(n_items)]

# Objective
model.Minimize(sum(costs[i] * vars[i] for i in range(n_items)))

# Coverage constraints
for j, covering_items in enumerate(coverage_lists):
    model.Add(sum(vars[i] for i in covering_items) >= 1)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in range(n_items) if solver.Value(vars[i])]
    total_cost = sum(costs[i] for i in selected)
    # Verification
    all_covered = all(any(s in cov for s in selected) for cov in coverage_lists)
    output = {"status": "success", "cost": total_cost, "selected": selected, "verified": all_covered}
else:
    output = {"status": "failed", "message": f"Solver status: {status}"}
```

### Common Pitfalls
- Not handling the `cp_model.FEASIBLE` status, which may still provide a usable solution if optimality is not required.
- Forgetting to scale non-integer costs, causing CP-SAT to reject the model; multiply by a factor to convert to integers.
- Skipping the independent verification step, risking acceptance of an infeasible solution due to modeling errors.
