---
name: Mixed-Integer Linear Programming for Conditional Allocation
description: |
  Model and solve allocation problems with binary activation, continuous assignment, and conditional minimum delivery using MILP solvers, with explicit handling of solver status and solution verification.

---

# Workflow 1 (OR-Tools with SCIP Backend)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver (with SCIP backend) for mixed-integer linear programming. It is suitable for problems requiring a direct, low-level API for variable and constraint creation, with strong performance on medium-sized instances.

### Step 1 - Define Sets and Parameters
- Define index sets for `producers` and `contracts` as Python lists or ranges.
- Organize parameters as dictionaries: `capacity[p]`, `demand[c]`, `min_delivery[p]`, `min_contributors[c]`, and `cost[p][c]`.

### Step 2 - Create Decision Variables
- Create a continuous assignment variable `x[p, c]` for each producer-contract pair using `solver.NumVar(lb, ub, name)`.
- Create a binary activation variable `y[p, c]` for each pair using `solver.BoolVar(name)`.

### Step 3 - Formulate Constraints
- **Capacity Limit**: For each producer `p`, sum of `x[p, c]` over all contracts `c` ≤ `capacity[p]`.
- **Demand Satisfaction**: For each contract `c`, sum of `x[p, c]` over all producers `p` ≥ `demand[c]`.
- **Minimum Contributors**: For each contract `c`, sum of `y[p, c]` over all producers `p` ≥ `min_contributors[c]`.
- **Minimum Delivery if Active**: For each pair `(p, c)`, add two constraints:
    - `x[p, c] ≥ min_delivery[p] * y[p, c]` (enforces minimum if active).
    - `x[p, c] ≤ capacity[p] * y[p, c]` (forces zero allocation if inactive).

### Step 4 - Define Objective
- Formulate a linear cost minimization objective: sum of `cost[p][c] * x[p, c]` over all pairs.

### Formulation Template
```json
{
  "sets": ["producers", "contracts"],
  "parameters": [
    {"name": "capacity", "index": "producers"},
    {"name": "demand", "index": "contracts"},
    {"name": "min_delivery", "index": "producers"},
    {"name": "min_contributors", "index": "contracts"},
    {"name": "cost", "index": ["producers", "contracts"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "continuous", "index": ["producers", "contracts"]},
    {"name": "y", "type": "binary", "index": ["producers", "contracts"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[p][c] * x[p, c] for p in producers for c in contracts)"
  },
  "constraints": [
    {"name": "capacity_limit", "expression": "sum(x[p, c] for c in contracts) <= capacity[p] for p in producers"},
    {"name": "demand_satisfaction", "expression": "sum(x[p, c] for p in producers) >= demand[c] for c in contracts"},
    {"name": "minimum_contributors", "expression": "sum(y[p, c] for p in producers) >= min_contributors[c] for c in contracts"},
    {"name": "minimum_delivery_if_active_lb", "expression": "x[p, c] >= min_delivery[p] * y[p, c] for p in producers for c in contracts"},
    {"name": "minimum_delivery_if_active_ub", "expression": "x[p, c] <= capacity[p] * y[p, c] for p in producers for c in contracts"}
  ]
}
```

### Common Pitfalls
- Using an overly large big-M value (like `capacity[p]`) can weaken the linear relaxation; use the tightest valid upper bound available.
- Forgetting to set a time limit or thread count can lead to unpredictable runtime in production.
- Not verifying that the solver status is `OPTIMAL` or `FEASIBLE` before extracting solution values.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' `CpSolver`, configure performance parameters, extract the solution, and implement a robust verification routine to ensure all constraints are satisfied within tolerance.

### Step 1 - Configure and Solve
- Instantiate `CpSolver()` and set parameters: `solver.parameters.max_time_in_seconds`, `solver.parameters.num_search_workers`.
- Call `solver.Solve(model)` and capture the `status`.

### Step 2 - Check Solver Status and Extract Solution
- Check if `status` is `OPTIMAL` or `FEASIBLE`. If not, output an error payload with status details.
- If successful, iterate over all variable indices and store `solver.Value(x_var)` and `solver.Value(y_var)`.

### Step 3 - Verify Solution Integrity
- Recalculate aggregated values (total allocation per producer, per contract).
- Assert capacity, demand, minimum contributor, and minimum delivery constraints are satisfied within a numerical tolerance (e.g., `1e-6`).
- Log any violations for debugging.

### Step 4 - Report Results
- Print a summary including total cost, per-contract allocations (listing contributing producers and amounts), and producer utilization percentages.
- Optionally output results in a structured format (e.g., JSON) for downstream processing.

### Code Usage
```python
from ortools.sat.python import cp_model
import json

# Build model (model) from formulation steps above...
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    x_sol = {(p, c): solver.Value(x[p, c]) for p in producers for c in contracts}
    y_sol = {(p, c): solver.Value(y[p, c]) for p in producers for c in contracts}
    total_cost = sum(cost[p][c] * x_sol[(p, c)] for p in producers for c in contracts)
    print(f"RESULT:{total_cost}")
    # ... verification and reporting
else:
    error_payload = {
        "status": "failed",
        "reason": "infeasible_or_error",
        "solver_status": str(status)
    }
    print(f"RESULT_JSON:{json.dumps(error_payload)}")
```

### Common Pitfalls
- Assuming the solver always finds an optimal solution without checking status.
- Not using a tolerance when verifying equality or inequality constraints, leading to false failures due to floating-point arithmetic.
- Extracting variable values without confirming the solve was successful, which may return garbage values.

# Workflow 2 (Pyomo with HiGHS/Gurobi)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for high-level, declarative model construction, interfacing with solvers like HiGHS (open-source) or Gurobi (commercial). It is suitable for problems requiring maintainable, scalable model definitions and advanced solver features.

### Step 1 - Define Abstract Sets and Parameters
- Use `pyo.Set()` to define index sets `model.P` (producers) and `model.C` (contracts).
- Use `pyo.Param()` to define `model.capacity`, `model.demand`, `model.min_delivery`, `model.min_contributors`, and `model.cost`, indexing them appropriately.

### Step 2 - Declare Decision Variables
- Declare `model.x` as a continuous variable indexed over `(model.P, model.C)` with appropriate bounds (e.g., `bounds=(0, None)`).
- Declare `model.y` as a binary variable indexed over `(model.P, model.C)`.

### Step 3 - Construct Constraints via Rules
- Define a rule function for each constraint type, using `pyo.Constraint(model.P, model.C)` or `pyo.Constraint(model.P)` as needed.
- Implement the `minimum_delivery_if_active` logic using the same big-M formulation: `model.x[p, c] >= model.min_delivery[p] * model.y[p, c]` and `model.x[p, c] <= model.capacity[p] * model.y[p, c]`.

### Step 4 - Define Objective Function
- Define `model.obj` as a `pyo.Objective` with `sense=pyo.minimize` and the expression `sum(model.cost[p, c] * model.x[p, c] for p in model.P for c in model.C)`.

### Formulation Template
```json
{
  "sets": ["P", "C"],
  "parameters": [
    {"name": "capacity", "index": "P"},
    {"name": "demand", "index": "C"},
    {"name": "min_delivery", "index": "P"},
    {"name": "min_contributors", "index": "C"},
    {"name": "cost", "index": ["P", "C"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "continuous", "index": ["P", "C"]},
    {"name": "y", "type": "binary", "index": ["P", "C"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[p, c] * x[p, c] for p in P for c in C)"
  },
  "constraints": [
    {"name": "capacity_limit", "expression": "sum(x[p, c] for c in C) <= capacity[p] for p in P"},
    {"name": "demand_satisfaction", "expression": "sum(x[p, c] for p in P) >= demand[c] for c in C"},
    {"name": "minimum_contributors", "expression": "sum(y[p, c] for p in P) >= min_contributors[c] for c in C"},
    {"name": "minimum_delivery_if_active_lb", "expression": "x[p, c] >= min_delivery[p] * y[p, c] for p in P for c in C"},
    {"name": "minimum_delivery_if_active_ub", "expression": "x[p, c] <= capacity[p] * y[p, c] for p in P for c in C"}
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters or variables in rule functions, leading to `KeyError` or incorrect constraint scope.
- Using overly complex rule logic that hinders model inspection or performance.
- Not leveraging Pyomo's `Set` and `Param` objects, which reduces model clarity and scalability.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver (HiGHS or Gurobi), check both solver status and termination condition, extract and verify the solution, and handle failures gracefully with structured output.

### Step 1 - Configure Solver and Solve
- Instantiate a solver object via `pyo.SolverFactory('solver_name')`.
- Set key options: `TimeLimit`, `MIPGap` (or `mip_rel_gap`), `Threads`, and optionally `Seed` for reproducibility.
- Call `solver.solve(model, tee=False)` to execute, using `tee=True` for debugging.

### Step 2 - Validate Solver Outcome
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If checks fail, output a JSON payload with failure details.

### Step 3 - Extract and Verify Solution
- If successful, access variable values via `pyo.value(model.x[p, c])` and `pyo.value(model.y[p, c])`.
- Recompute aggregates and verify all constraints are satisfied within tolerance, similar to Workflow 1.

### Step 4 - Report and Output
- Print total cost and a detailed allocation summary.
- Optionally serialize key results (allocations, activations, utilizations) to a structured format.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# Build model (model) from formulation steps above...
solver = pyo.SolverFactory('gurobi')  # or 'highs'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4

results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = pyo.value(model.obj)
    print(f"RESULT:{total_cost}")
    # ... extraction, verification, and reporting
else:
    error_payload = {
        "status": "failed",
        "reason": "infeasible_or_error",
        "solver_status": str(status),
        "termination_condition": str(term)
    }
    print(f"RESULT_JSON:{json.dumps(error_payload)}")
```

### Common Pitfalls
- Assuming `SolverStatus.ok` alone guarantees a good solution; must also check `termination_condition`.
- Over-specifying solver options, which can cause errors with different solver versions or types.
- Not using `pyo.value()` to extract variable values, leading to direct access of variable objects.
