---
name: Generalized Weighted Set Covering
description: |
  Model and solve binary selection problems with coverage requirements and linear cost minimization using either CP-SAT or MILP solvers.

---

# Workflow 1 (CP-SAT for Exact Binary Optimization)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Weighted Set Covering problem using OR-Tools' CP-SAT solver, which is optimized for binary variables and linear constraints. It focuses on efficient data structures and pre-solve analysis to reduce problem size.

### Step 1 - Define Core Data Structures
- Map the problem data into generic sets and parameters. Define a set of selectable `items` and a set of `requirements`.
- Create a dictionary `cost[i]` for the cost of selecting each item `i`.
- Create a sparse coverage mapping `covers[req] = [list_of_items]` indicating which items satisfy each requirement `req`.
- Define a dictionary `requirement[req]` for the minimum number of covering items needed for each requirement.

### Step 2 - Create Binary Variables and Objective
- For each item `i`, create a binary decision variable `x[i]`.
- Formulate the objective to minimize total selection cost: `Minimize sum(cost[i] * x[i] for i in items)`.

### Step 3 - Formulate Coverage Constraints
- For each requirement `req`, add a linear constraint: `sum(x[i] for i in covers[req]) >= requirement[req]`.
- This ensures the selected items collectively meet the minimum coverage count for every requirement.

### Step 4 - Pre-solve Analysis and Reduction
- Perform a feasibility check: for each `req`, verify `len(covers[req]) >= requirement[req]`. If false, the problem is inherently infeasible.
- Identify mandatory items: if for any `req`, `len(covers[req]) == requirement[req]`, then all items in `covers[req]` must be selected. Fix their variables to `1` to reduce model size.

### Formulation Template
```json
{
  "sets": [
    "items",
    "requirements"
  ],
  "parameters": [
    "cost[items]",
    "covers[requirements] -> list_of_items",
    "requirement[requirements]"
  ],
  "decision_variables": [
    "x[items] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    "coverage[req]: sum(x[i] for i in covers[req]) >= requirement[req], for all req in requirements"
  ]
}
```

### Common Pitfalls
- Using a dense coverage matrix for sparse problems, wasting memory and slowing model construction.
- Forgetting to perform pre-solve checks, leading to solver timeouts on trivially infeasible instances.
- Not fixing mandatory variables, missing an opportunity to reduce the search space.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' CP-SAT with configuration for reproducibility and performance. Implement rigorous solution validation and optimality verification.

### Step 1 - Configure and Run the Solver
- Instantiate the CP-SAT model and build it from the formulation.
- Configure the solver: set a time limit (`max_time_in_seconds`), number of parallel workers (`num_search_workers`), a random seed for determinism, and a zero relative gap to aim for optimality.
- Execute the solver and capture the status.

### Step 2 - Extract and Validate the Solution
- If the solver status is `OPTIMAL` or `FEASIBLE`, extract the values of the binary variables.
- Recompute the coverage for each requirement using the selected items and the `covers` mapping.
- Assert that all coverage constraints are satisfied. This catches any modeling or solver errors.

### Step 3 - Verify Optimality (Optional)
- To confirm a solution is optimal, add a new constraint forcing the objective value to be strictly less than the incumbent: `sum(cost[i] * x[i]) <= incumbent_cost - 1`.
- Re-solve the model. If the result is `INFEASIBLE`, it proves no better solution exists, verifying optimality.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model

model = cp_model.CpModel()
x = {i: model.NewBoolVar(f'x_{i}') for i in items}

# Objective
model.Minimize(sum(cost[i] * x[i] for i in items))

# Constraints
for req in requirements:
    model.Add(sum(x[i] for i in covers[req]) >= requirement[req])

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in items if solver.Value(x[i]) > 0.5]
    total_cost = sum(cost[i] for i in selected)
    # Validation
    for req in requirements:
        coverage_count = sum(1 for i in selected if i in covers[req])
        assert coverage_count >= requirement[req], f"Requirement {req} not met."
    print(f"Solution found. Cost: {total_cost}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Misinterpreting solver status codes (e.g., treating `FEASIBLE` as `OPTIMAL` without further verification).
- Not setting a random seed, leading to non-reproducible results across runs.
- Skipping solution validation, which can hide incorrect modeling assumptions.

# Workflow 2 (MILP Solver via Pyomo)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Linear Program (MILP) using Pyomo, targeting open-source solvers like CBC. It emphasizes a clean algebraic formulation with explicit sets and rules, suitable for integration into larger optimization systems.

### Step 1 - Define Pyomo Sets and Parameters
- Create Pyomo `Set` objects for `items` and `requirements` to provide clear indexing.
- Define `Param` objects for `cost`, `requirement`, and a `coverage_matrix` (a binary parameter `coverage_matrix[i, req]` indicating if item `i` covers requirement `req`).

### Step 2 - Declare Variables and Objective
- Declare binary variables `model.x[i]` for each item `i`.
- Define the objective as a `pyo.minimize` expression: `sum(cost[i] * model.x[i] for i in items)`.

### Step 3 - Implement Coverage Constraints via Rules
- Define a Pyomo `Constraint` indexed by the `requirements` set.
- For each requirement `req`, the rule returns: `sum(coverage_matrix[i, req] * model.x[i] for i in items) >= requirement[req]`.

### Step 4 - (Optional) Pre-process with Mandatory Items
- Before solving, analyze the `coverage_matrix` and `requirement` to identify items that are the sole cover for a requirement. Fix their lower bound to `1`.

### Formulation Template
```json
{
  "sets": [
    "items",
    "requirements"
  ],
  "parameters": [
    "cost[items]",
    "coverage_matrix[items, requirements] ∈ {0,1}",
    "requirement[requirements]"
  ],
  "decision_variables": [
    "x[items] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    "coverage[req]: sum(coverage_matrix[i, req] * x[i] for i in items) >= requirement[req], for all req in requirements"
  ]
}
```

### Common Pitfalls
- Using inefficient rule functions that recalculate data on each call; pre-compute data structures.
- Confusing Pyomo's 1-based indexing with Python's 0-based indexing when populating parameters.
- Not declaring the objective sense correctly (`minimize` vs `maximize`).

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via the `SolverFactory`. Configure for optimality, handle solver statuses carefully, and implement post-solve validation.

### Step 1 - Configure and Execute the Solver
- Instantiate the solver: `solver = pyo.SolverFactory("cbc")`.
- Set solver options: a time limit (`seconds`), optimality gap (`ratio = 0.0`), and number of threads.
- Solve the model with `load_solutions=False` to first check the solver status independently.

### Step 2 - Check Solver Status and Termination Condition
- Inspect `results.solver.status`. A status of `ok` is required.
- Inspect `results.solver.termination_condition`. Accept `optimal` or `feasible`.
- Only load the solution into the model if the status and termination condition are acceptable.

### Step 3 - Extract, Validate, and Output Results
- Load the solution. Extract selected items where `pyo.value(model.x[i]) > 0.5`.
- Compute the total cost and validate all coverage constraints by recalculating coverage counts.
- Output results in a structured format (e.g., JSON) for easy parsing.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items)
model.reqs = pyo.Set(initialize=requirements)

model.cost = pyo.Param(model.items, initialize=cost)
model.req_param = pyo.Param(model.reqs, initialize=requirement)
model.cov = pyo.Param(model.items, model.reqs, initialize=coverage_matrix)

model.x = pyo.Var(model.items, domain=pyo.Binary)

def obj_rule(m):
    return sum(m.cost[i] * m.x[i] for i in m.items)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def coverage_rule(m, r):
    return sum(m.cov[i, r] * m.x[i] for i in m.items) >= m.req_param[r]
model.coverage_con = pyo.Constraint(model.reqs, rule=coverage_rule)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options['seconds'] = 30
solver.options['ratio'] = -1.0  # Use 0.0 for optimality gap, -1.0 for solver default
solver.options['threads'] = 4

results = solver.solve(model, tee=False, load_solutions=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    model.solutions.load_from(results)
    selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
    total_cost = sum(cost[i] for i in selected)
    # Validation
    for r in model.reqs:
        coverage_count = sum(coverage_matrix[i, r] for i in selected)
        assert coverage_count >= requirement[r], f"Requirement {r} not met."
    print(f"Solution found. Cost: {total_cost}")
else:
    print(f"Solver failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Loading solutions without checking `termination_condition`, potentially loading suboptimal or invalid results.
- Setting an invalid optimality gap (e.g., a negative value for some solvers). Use `0.0` for exact solution targets.
- Not using `load_solutions=False`, which can cause crashes if the solver did not find a feasible solution.
