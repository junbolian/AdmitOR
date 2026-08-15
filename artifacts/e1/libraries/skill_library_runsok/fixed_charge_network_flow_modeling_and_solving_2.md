---
name: Fixed-Charge Network Flow Modeling and Solving
description: |
  Model and solve network flow problems with route establishment costs and per-unit flow costs using mixed-integer linear programming, with workflows for Pyomo and direct solver APIs.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's high-level, declarative modeling to construct a fixed-charge network flow problem. It is ideal for rapid prototyping and clear separation of model structure from solution logic.

### Step 1 - Define Sets and Parameters
- Declare sets for nodes and arcs using `pyo.Set`.
- Initialize parameters for supply/demand (`net_outflow`), arc capacities, fixed costs, and variable costs using `pyo.Param` with dictionary initialization for clarity and maintainability.

### Step 2 - Create Decision Variables
- Create binary variables `y[arc]` for route activation (`domain=pyo.Binary`).
- Create continuous, non-negative variables `x[arc]` for flow amounts (`domain=pyo.NonNegativeReals`).

### Step 3 - Enforce Flow Conservation
- For each node `i`, add a constraint: `sum(x[i,j] for j in out_arcs) - sum(x[j,i] for j in in_arcs) == net_outflow[i]`.
- Compute outflow and inflow lists separately in the constraint rule for clarity.

### Step 4 - Link Flow to Activation via Capacity
- For each arc, add a constraint: `x[arc] <= capacity[arc] * y[arc]`. This ensures flow is zero if the route is inactive and respects the capacity if active.

### Step 5 - Define Linear Objective
- Minimize the sum of fixed and variable costs: `sum(fixed_cost[arc] * y[arc] + variable_cost[arc] * x[arc] for arc in arcs)`.

### Formulation Template
```json
{
  "sets": ["N (nodes)", "A (arcs)"],
  "parameters": [
    "net_outflow[N] (supply > 0, demand < 0)",
    "capacity[A]",
    "fixed_cost[A]",
    "variable_cost[A]"
  ],
  "decision_variables": [
    "y[A] ∈ {0,1} (route activation)",
    "x[A] ≥ 0 (flow)"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{A} (fixed_cost * y + variable_cost * x)"
  },
  "constraints": [
    "flow_conservation[N]: ∑_{j} x[i,j] - ∑_{j} x[j,i] = net_outflow[i] ∀ i ∈ N",
    "capacity_linking[A]: x[i,j] ≤ capacity[i,j] * y[i,j] ∀ (i,j) ∈ A"
  ]
}
```

### Common Pitfalls
- Forgetting to define `net_outflow` for all nodes, leading to an unbalanced network.
- Using a single constraint rule that incorrectly aggregates in/out arcs, causing indexing errors.
- Not initializing parameters with complete dictionaries, resulting in missing key errors during model construction.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver via the `SolverFactory` interface. Focus on robust solver configuration, solution status verification, and post-solve validation.

### Step 1 - Configure Solver and Options
- Instantiate the solver: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set key options: `time_limit` (e.g., 30), `mip_rel_gap` (e.g., 0.0 for optimality), and `threads` (e.g., 4) for performance.

### Step 2 - Solve and Check Status
- Execute `results = solver.solve(model, tee=True)`.
- Check `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`. Only proceed with solution extraction if these checks pass.

### Step 3 - Extract and Validate Solution
- Extract the objective value: `pyo.value(model.obj)`.
- Collect active routes where `pyo.value(model.y[arc]) > 0.5` and flows where `pyo.value(model.x[arc]) > 0`.
- Programmatically verify flow conservation and capacity constraints as a sanity check.

### Step 4 - Handle Failure Gracefully
- If the solve fails (status not ok or termination not optimal/feasible), output a structured error message or JSON payload indicating the failure reason and solver status.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# Build model (model defined in Modeling stage)
model = build_fcnf_model()

# Configure solver
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4

# Solve and check status
results = solver.solve(model, tee=False)
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    # Extract solution
    active_routes = [arc for arc in model.A if pyo.value(model.y[arc]) > 0.5]
    flows = {arc: pyo.value(model.x[arc]) for arc in model.A}
    # Validate (e.g., check flow conservation)
    print(f"RESULT:{objective_value}")
    print(f"RESULT_JSON:{json.dumps({'status':'success','objective':objective_value,'active_routes':active_routes,'flows':flows})}")
else:
    print(f"RESULT_JSON:{json.dumps({'status':'failed','reason':'solver_failure','solver_status':str(status),'termination_condition':str(term)})}")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to extraction from invalid solutions.
- Setting `mip_rel_gap` to a negative value, causing solver errors.
- Omitting the `tee` flag or status checks, making debugging difficult when the solve fails silently.

# Workflow 2 (Direct Solver API with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., OR-Tools) for programmatic, low-level model construction. It offers fine-grained control and is suitable for integration into larger applications or when Pyomo is not available.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Store network data (nodes, arcs, supply, capacity, costs) in native Python dictionaries or lists for efficient access during model building.

### Step 2 - Create Variables Programmatically
- Iterate over arcs. For each arc, create a binary variable `y[arc] = solver.BoolVar("")` and a continuous variable `x[arc] = solver.NumVar(0, capacity[arc], "")`.

### Step 3 - Enforce Flow Conservation via Loops
- For each node `i`, create a constraint: `solver.Add(sum(x[i,j] for j in out_arcs) - sum(x[j,i] for j in in_arcs) == net_outflow[i])`. Pre-compute the lists of outgoing and incoming arcs.

### Step 4 - Link Flow and Activation
- For each arc, add the constraint: `solver.Add(x[arc] <= capacity[arc] * y[arc])`.

### Step 5 - Set Linear Objective
- Build the objective expression by iterating over arcs: `solver.Minimize(sum(fixed_cost[arc] * y[arc] + variable_cost[arc] * x[arc] for arc in arcs))`.

### Formulation Template
```json
{
  "sets": ["N (nodes)", "A (arcs)"],
  "parameters": [
    "net_outflow[N] (supply > 0, demand < 0)",
    "capacity[A]",
    "fixed_cost[A]",
    "variable_cost[A]"
  ],
  "decision_variables": [
    "y[A] ∈ {0,1} (route activation)",
    "x[A] ∈ [0, capacity] (flow)"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{A} (fixed_cost * y + variable_cost * x)"
  },
  "constraints": [
    "flow_conservation[N]: ∑_{j} x[i,j] - ∑_{j} x[j,i] = net_outflow[i] ∀ i ∈ N",
    "capacity_linking[A]: x[i,j] ≤ capacity[i,j] * y[i,j] ∀ (i,j) ∈ A"
  ]
}
```

### Common Pitfalls
- Incorrectly setting variable bounds (e.g., not capping `x` at `capacity` in `NumVar`), which can lead to a weaker LP relaxation.
- Building the objective with a Python loop that creates a new expression object each iteration, potentially causing performance issues for large models.
- Failing to pre-aggregate arcs by node for the flow conservation constraints, resulting in inefficient constraint addition.

## Solving stage

### Strategy Overview
Solve the model using the configured OR-Tools solver, applying performance settings, and implement robust solution extraction and validation routines.

### Step 1 - Apply Solver Settings
- Set a time limit: `solver.SetTimeLimit(30000)` (milliseconds).
- Configure parallelism: `solver.SetNumThreads(4)`.
- Set an optimality gap tolerance if supported by the solver backend.

### Step 2 - Solve and Inspect Result Status
- Execute `status = solver.Solve()`.
- Check if `status` is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `NOT_SOLVED` statuses with appropriate error reporting.

### Step 3 - Extract and Verify Solution
- If solve is successful, get the objective value: `solver.Objective().Value()`.
- Iterate over arcs to collect active routes (`y[arc].solution_value() > 0.5`) and flow values (`x[arc].solution_value()`).
- Optionally, recompute flow balances and capacity adherence to validate the solution.

### Step 4 - Debug Infeasibility
- If the initial solve fails, create and solve a simplified LP relaxation (e.g., by relaxing `y` variables to continuous) or a pure transportation subproblem to isolate the source of infeasibility.

### Code Usage
```python
from ortools.linear_solver import pywraplp
import json

# Initialize solver
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Build model (model defined in Modeling stage)
# ... variable and constraint creation ...

# Solve
status = solver.Solve()

if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    active_routes = []
    flows = {}
    for arc in arcs:
        if y[arc].solution_value() > 0.5:
            active_routes.append(arc)
        flows[arc] = x[arc].solution_value()
    # Add validation checks here
    print(f"RESULT:{objective_value}")
    print(f"RESULT_JSON:{json.dumps({'status':'success','objective':objective_value,'active_routes':active_routes,'flows':flows})}")
else:
    print(f"RESULT_JSON:{json.dumps({'status':'failed','reason':'infeasible_or_not_solved','solver_status':status})}")
```

### Common Pitfalls
- Confusing OR-Tools status enums (e.g., `OPTIMAL` vs `FEASIBLE`) and not handling both.
- Not using `solution_value()` method on variables, leading to incorrect value extraction.
- Neglecting to set a time limit, causing the solver to run indefinitely on large or difficult instances.
