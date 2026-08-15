---
name: ContinuousAssignmentLP
description: |
  Model and solve linear assignment problems with supply limits, demand requirements, per-pair capacity bounds, and linear cost minimization using continuous variables.
---

# Workflow 1 (Pyomo with LP Solver)

## Modeling stage

### Strategy Overview
Model the assignment problem as a Linear Program (LP) using Pyomo's abstract modeling capabilities. Define sets for sources and destinations, use continuous non-negative variables for assignment quantities, and structure constraints and objective using Pyomo's `Constraint` and `Objective` components for clarity and solver portability.

### Step 1 - Define Core Sets and Parameters
- Define two index sets: `sources` (e.g., employees, warehouses) and `destinations` (e.g., projects, customers). Use integer or string identifiers.
- Organize all input data as Python dictionaries keyed by these indices: `availability[s]`, `requirement[d]`, `cost[s,d]`, and `limit[s,d]`.

### Step 2 - Create Decision Variables
- Create a continuous, non-negative Pyomo variable `model.x[s,d]` for each source-destination pair, representing the assignment quantity.
- Optionally, set the variable's upper bound directly to `limit[s,d]` during creation to implicitly enforce per-pair limits.

### Step 3 - Formulate Constraints
- Add a **supply limit** constraint for each source `s`: `sum(model.x[s,d] for d in destinations) <= availability[s]`.
- Add a **demand satisfaction** constraint for each destination `d`: `sum(model.x[s,d] for s in sources) >= requirement[d]`. Use `==` for exact fulfillment if required.
- If not enforced via variable bounds, add an **individual assignment limit** constraint for each pair `(s,d)`: `model.x[s,d] <= limit[s,d]`.

### Step 4 - Define Linear Objective
- Define the objective to minimize total linear cost: `sum(cost[s,d] * model.x[s,d] for s in sources for d in destinations)` with `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "availability", "index": "sources"},
    {"name": "requirement", "index": "destinations"},
    {"name": "cost", "index": ["sources", "destinations"]},
    {"name": "limit", "index": ["sources", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s,d] * x[s,d])"
  },
  "constraints": [
    {"name": "supply_limit", "index": "sources", "expression": "sum(x[s,d]) <= availability[s]"},
    {"name": "demand_satisfaction", "index": "destinations", "expression": "sum(x[s,d]) >= requirement[d]"},
    {"name": "per_pair_limit", "index": ["sources", "destinations"], "expression": "x[s,d] <= limit[s,d]"}
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply capacity meets or exceeds total demand before solving, which can lead to infeasibility.
- Using nested list-of-lists for cost/limit data instead of dictionaries, which can cause indexing errors with non-integer set elements.
- Adding per-pair limit constraints as separate rows when they can be more efficiently handled as variable upper bounds.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an efficient LP solver (e.g., HiGHS, CBC) configured for exact solutions. Implement robust solution status checking, load the solution explicitly, and perform post-solve verification of all constraints.

### Step 1 - Instantiate and Configure Solver
- Create a solver object using `pyo.SolverFactory("highs")` or `pyo.SolverFactory("cbc")`.
- Set key solver options: `time_limit=30`, `ratio=0.0` (for optimality gap), and `threads=4` for performance.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False, load_solutions=False)`.
- Check that `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible` before proceeding.

### Step 3 - Load and Extract Solution
- If status checks pass, load the solution into the model: `model.solutions.load_from(results)`.
- Extract the objective value using `total_cost = pyo.value(model.obj)`.
- Iterate over variables `model.x[s,d]` and collect non-zero assignments (e.g., `> 1e-6`).

### Step 4 - Verify Solution and Output
- Programmatically verify all constraints: compute sums per source/destination and compare against parameters with a tolerance (e.g., `1e-6`).
- Output the objective value in a parseable format (e.g., `RESULT:{total_cost}`) and optionally a detailed assignment breakdown.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation (follow steps above)
model = pyo.ConcreteModel()
# ... define sets, variables, constraints, objective

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False, load_solutions=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    model.solutions.load_from(results)
    total_cost = pyo.value(model.obj)
    # Extract and verify solution
else:
    # Handle solver failure
    print(f"SOLVER_FAILED:{results.solver.termination_condition}")
```

### Common Pitfalls
- Attempting to read variable values (`pyo.value(model.x[s,d])`) before loading the solution, which returns the initial value (often zero).
- Not using `load_solutions=False` and manual loading, which can lead to errors if the solver status is not optimal/feasible.
- Setting solver options like `threads` on a globally shared solver instance, which can cause interface errors.

# Workflow 2 (OR-Tools LP with GLOP/CBC)

## Modeling stage

### Strategy Overview
Model the assignment problem directly using the OR-Tools linear solver API. Create variables with explicit bounds, build constraints via `solver.Add()`, and set the objective using `SetCoefficient`. This imperative style is efficient and closely maps to the solver's internal representation.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("GLOP")` for LP or `"CBC"` for MIP/LP.
- Store input data in lists or dictionaries: `availability`, `requirement`, `cost`, `limit`.

### Step 2 - Create Bounded Variables
- For each source-destination pair `(i,j)`, create a continuous variable: `x[i,j] = solver.NumVar(0, limit[i,j], name)`.
- Setting the upper bound to `limit[i,j]` directly encodes the per-pair capacity limit.

### Step 3 - Add Supply and Demand Constraints
- For each source `i`, add a supply constraint: `solver.Add(sum(x[i,j] for j in destinations) <= availability[i])`.
- For each destination `j`, add a demand constraint: `solver.Add(sum(x[i,j] for i in sources) == requirement[j])`. Use `>=` if over-delivery is allowed.

### Step 4 - Define Linear Minimization Objective
- Create an objective object: `objective = solver.Objective()`.
- For each variable `x[i,j]`, set its coefficient: `objective.SetCoefficient(x[i,j], cost[i,j])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "availability", "index": "sources"},
    {"name": "requirement", "index": "destinations"},
    {"name": "cost", "index": ["sources", "destinations"]},
    {"name": "limit", "index": ["sources", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "type": "continuous", "lb": 0, "ub": "limit[s,d]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s,d] * x[s,d])"
  },
  "constraints": [
    {"name": "supply_limit", "index": "sources", "expression": "sum(x[s,d]) <= availability[s]"},
    {"name": "demand_satisfaction", "index": "destinations", "expression": "sum(x[s,d]) == requirement[d]"}
  ]
}
```

### Common Pitfalls
- Using `solver.NumVar(0, solver.infinity(), name)` and forgetting to add separate per-pair limit constraints, violating capacity bounds.
- Adding constraints with `solver.Add(sum(...) == value)` for demand when total supply does not exactly equal total demand, causing infeasibility.
- Not verifying the solver was created successfully (`solver` is not `None`).

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' wrapper, check the result status, extract the objective and variable values, and perform post-solution verification. Use multiple solvers (e.g., GLOP then CBC) for cross-validation if needed.

### Step 1 - Solve and Check Result Status
- Call `solver.Solve()`.
- Check the result status against `pywraplp.Solver.OPTIMAL` and `pywraplp.Solver.FEASIBLE`. Proceed only if status indicates success.

### Step 2 - Extract Objective and Variable Values
- Retrieve the objective value: `total_cost = objective.Value()`.
- Iterate over all variables `x[i,j]` and collect their solution values using `x[i,j].solution_value()`.

### Step 3 - Verify Constraint Satisfaction
- Recompute the sum of assignments for each source and destination from the solution values.
- Verify each sum is within tolerance of the corresponding supply limit or demand requirement.
- Verify no individual assignment exceeds its `limit[i,j]`.

### Step 4 - Output and Optional Cross-Validation
- Output the total cost in a parseable format (e.g., `<total_cost>value</total_cost>`).
- For validation, optionally re-solve with a different solver backend (e.g., CBC after GLOP) and compare objective values.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
# ... create variables, add constraints, set objective

# Solve with status / termination checks
result_status = solver.Solve()
if result_status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    # Extract variable values and verify
    for i in sources:
        for j in destinations:
            val = x[i,j].solution_value()
            if val > 1e-6:
                # Record assignment
else:
    # Handle solver failure
    print(f"SOLVER_FAILED:{result_status}")
```

### Common Pitfalls
- Confusing `solver.Solve()` return status with `solver.OPTIMAL` constant; always compare against the constants.
- Setting solver time limit via `solver.SetTimeLimit(ms)` on CBC but attempting to use non-existent `solver.params` attribute.
- Not using a tolerance when checking constraint satisfaction, leading to false failures due to floating-point precision.
