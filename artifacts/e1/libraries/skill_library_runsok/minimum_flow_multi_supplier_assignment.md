---
name: Minimum-Flow Multi-Supplier Assignment
description: |
  Model and solve assignment problems with minimum activation thresholds, multiple supplier requirements, and linear costs using MILP formulations.

---
# Workflow 1 (Pyomo with Gurobi/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling to define a MILP with binary activation variables linked to continuous flow via big-M constraints, suitable for commercial (Gurobi) or open-source (CBC) solvers.

### Step 1 - Define Sets and Parameters
- Declare index sets for supply nodes (`SUPPLIERS`) and demand nodes (`DEMANDS`).
- Define parameters: `cost`, `capacity`, `demand_requirement`, and `minimum_flow` as dictionaries with tuple keys `(i, j)` or single-index keys.
- Use Pyomo's `Set`, `Param`, or native Python structures for data initialization.

### Step 2 - Create Decision Variables
- Add continuous flow variables `x[i, j] >= 0`.
- Add binary activation variables `y[i, j] ∈ {0,1}`.
- Instantiate using `pyo.Var` with appropriate domains (`pyo.NonNegativeReals`, `pyo.Binary`).

### Step 3 - Formulate Constraints
- **Supply Capacity**: `sum(x[i, j] for j in DEMANDS) <= capacity[i]` for each `i`.
- **Demand Requirement**: `sum(x[i, j] for i in SUPPLIERS) >= demand_requirement[j]` for each `j`.
- **Minimum Activation Flow**: `x[i, j] >= minimum_flow[i] * y[i, j]` for each `(i, j)`.
- **Big-M Upper Bound**: `x[i, j] <= capacity[i] * y[i, j]` for each `(i, j)` (using supply capacity as natural big-M).
- **Multiple Supplier Requirement**: `sum(y[i, j] for i in SUPPLIERS) >= K` for each `j`, where `K` is the required minimum number of active suppliers.

### Step 4 - Set Objective
- Define a linear cost minimization objective: `sum(cost[i, j] * x[i, j] for i, j)`.

### Formulation Template
```json
{
  "sets": ["SUPPLIERS", "DEMANDS"],
  "parameters": [
    "cost[(i,j)]",
    "capacity[i]",
    "demand_requirement[j]",
    "minimum_flow[i]",
    "K"
  ],
  "decision_variables": [
    "x[(i,j)] >= 0 (continuous flow)",
    "y[(i,j)] ∈ {0,1} (binary activation)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in SUPPLIERS, j in DEMANDS)"
  },
  "constraints": [
    "sum(x[i,j] for j in DEMANDS) <= capacity[i] ∀i",
    "sum(x[i,j] for i in SUPPLIERS) >= demand_requirement[j] ∀j",
    "x[i,j] >= minimum_flow[i] * y[i,j] ∀(i,j)",
    "x[i,j] <= capacity[i] * y[i,j] ∀(i,j)",
    "sum(y[i,j] for i in SUPPLIERS) >= K ∀j"
  ]
}
```

### Common Pitfalls
- Using an arbitrary large big-M value instead of a natural upper bound like `capacity[i]`, which weakens the LP relaxation.
- Forgetting to define the `K` parameter for the multiple supplier constraint, leading to a model error.
- Mismatching index order between parameter dictionaries and variable indices, causing KeyErrors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver (Gurobi or CBC), with robust status checking and solution extraction.

### Step 1 - Configure Solver and Parameters
- Instantiate solver via `SolverFactory("solver_name")` (e.g., `"gurobi"`, `"cbc"`).
- Set key parameters: `TimeLimit`, `MIPGap` (must be ≥ 0), `Threads`, and `Seed` for reproducibility.
- Validate parameter values (e.g., non-negative MIPGap) to avoid solver errors.

### Step 2 - Solve and Check Status
- Call `solver.solve(model, tee=True)` to solve and optionally print progress.
- Check `results.solver.status` (`SolverStatus.ok`) and `results.solver.termination_condition` (`optimal` or `feasible`).
- If status is not ok or termination is not acceptable, handle as an infeasible or error case.

### Step 3 - Extract and Verify Solution
- If solve was successful, retrieve the objective value via `pyo.value(model.obj)`.
- Iterate over variables to extract non-zero flows (`x[i,j].value`) and activation decisions (`y[i,j].value > 0.5`).
- Programmatically verify key constraints (capacity, demand, supplier count) with a tolerance (e.g., 1e-6) to ensure numerical feasibility.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# Assume `model` is built according to the modeling steps
solver = pyo.SolverFactory("gurobi")  # Or "cbc"
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = -1e-4  # Error: must be ≥0
solver.options["MIPGap"] = 1e-4   # Correct
solver.options["Threads"] = 4
solver.options["Seed"] = 42

results = solver.solve(model, tee=True)
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = float(pyo.value(model.obj))
    # Extract solution details
    solution_flows = {(i,j): pyo.value(model.x[i,j]) for (i,j) in model.x if pyo.value(model.x[i,j]) > 1e-6}
    solution_activation = {(i,j): pyo.value(model.y[i,j]) for (i,j) in model.y if pyo.value(model.y[i,j]) > 0.5}
    print(f"RESULT:{obj_val}")
    # Optional: print or return detailed allocation
else:
    # Handle failure: log status and termination condition
    payload = {"solver_status": str(status), "termination_condition": str(term)}
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or limit-reached solutions.
- Reading variable values without checking solve status first, which may raise errors.
- Setting `MIPGap` to a negative value, which causes a solver error.

# Workflow 2 (OR-Tools CP-SAT / MIP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT or MIP solver with a more procedural, flat-index modeling style, ideal for large-scale problems or when integration with the OR-Tools ecosystem is preferred.

### Step 1 - Map Indices to Flat Variables
- Map each supplier-demand pair `(i, j)` to a unique integer index for variable creation.
- Alternatively, use nested loops or dictionaries to manage variable references.

### Step 2 - Create Variables and Constraints
- Create continuous flow variables `x[ij]` with `solver.NumVar(0, capacity[i], name)`.
- Create binary activation variables `y[ij]` with `solver.BoolVar(name)`.
- Add supply capacity constraint: `sum(x[ij] for j) <= capacity[i]` using `solver.Add`.
- Add demand requirement constraint: `sum(x[ij] for i) >= demand_requirement[j]`.
- Link flow and activation: `x[ij] >= min_flow[i] * y[ij]` and `x[ij] <= capacity[i] * y[ij]`.
- Enforce multiple suppliers: `sum(y[ij] for i) >= K` for each demand `j`.

### Step 3 - Set Linear Objective
- Define objective as `sum(cost[ij] * x[ij] for all ij)` using `solver.Minimize`.

### Formulation Template
```json
{
  "sets": ["SUPPLIERS", "DEMANDS"],
  "parameters": [
    "cost[ij]",
    "capacity[i]",
    "demand_requirement[j]",
    "minimum_flow[i]",
    "K"
  ],
  "decision_variables": [
    "x[ij] ∈ [0, capacity[i]] (continuous)",
    "y[ij] ∈ {0,1} (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[ij] * x[ij] for all pairs ij)"
  },
  "constraints": [
    "sum(x[ij] for j) <= capacity[i] ∀i",
    "sum(x[ij] for i) >= demand_requirement[j] ∀j",
    "x[ij] >= minimum_flow[i] * y[ij] ∀ij",
    "x[ij] <= capacity[i] * y[ij] ∀ij",
    "sum(y[ij] for i) >= K ∀j"
  ]
}
```

### Common Pitfalls
- Using `solver.IntVar` for flow variables instead of `solver.NumVar`, which unnecessarily discretizes the flow.
- Forgetting to set an upper bound on continuous variables, which defaults to infinity and may cause solver issues.
- Incorrectly ordering indices in nested loops when creating constraints, leading to mismatched variable references.

## Solving stage

### Strategy Overview
Solve using OR-Tools' MIP solver (SCIP, CBC) or CP-SAT, with explicit time limits and thread control, followed by solution value extraction and validation.

### Step 1 - Initialize Solver and Set Parameters
- Choose solver backend: `pywraplp.Solver.CreateSolver('SCIP')` or `'CBC_MIXED_INTEGER_PROGRAMMING'`.
- Set parameters: `solver.SetTimeLimit(30000)` (in milliseconds), `solver.SetNumThreads(4)`.
- For CP-SAT, use `cp_model.CpModel()` and `cp_sat` solver with similar time limits.

### Step 2 - Solve and Interpret Result Status
- Call `solver.Solve()` and check the return status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.).
- If status is `OPTIMAL` or `FEASIBLE`, proceed to extract solution values.

### Step 3 - Extract Solution and Verify Feasibility
- Retrieve variable values using `.solution_value()` for each flow and activation variable.
- Compute aggregate metrics (total flow per supplier, per demand) and validate against constraints with a tolerance.
- Report the objective value via `solver.Objective().Value()`.

### Code Usage
```python
from ortools.linear_solver import pywraplp
import json

solver = pywraplp.Solver.CreateSolver('SCIP')
# Or 'CBC_MIXED_INTEGER_PROGRAMMING'
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# Assume variables and constraints are added per modeling steps
status = solver.Solve()

if status in [solver.OPTIMAL, solver.FEASIBLE]:
    obj_val = solver.Objective().Value()
    # Extract non-zero flows and activations
    solution_data = {}
    for idx, var in flow_vars.items():
        val = var.solution_value()
        if val > 1e-6:
            solution_data[idx] = val
    print(f"RESULT:{obj_val}")
    # Optional: print solution_data
else:
    # Handle infeasible or error status
    status_map = {solver.OPTIMAL: 'OPTIMAL', solver.FEASIBLE: 'FEASIBLE',
                  solver.INFEASIBLE: 'INFEASIBLE', solver.UNBOUNDED: 'UNBOUNDED',
                  solver.ABNORMAL: 'ABNORMAL', solver.NOT_SOLVED: 'NOT_SOLVED'}
    payload = {"solver_status": status_map.get(status, str(status))}
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Confusing the OR-Tools status codes (e.g., `FEASIBLE` vs `OPTIMAL`) and incorrectly handling suboptimal solutions.
- Not using a tolerance when checking variable values against zero, leading to false positives for very small numerical values.
- Omitting the time limit parameter for large instances, risking excessive runtime.
