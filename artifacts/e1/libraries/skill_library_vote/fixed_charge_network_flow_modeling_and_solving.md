---
name: Fixed-Charge Network Flow Modeling and Solving
description: |
  Model fixed-charge network flow problems as mixed-integer programs with binary activation and continuous flow variables, then solve using MIP solvers with robust status checking and solution validation.

---

# Workflow 1 (Pyomo with Gurobi)

## Modeling stage

### Strategy Overview
Formulate the problem as a directed graph using Pyomo's abstract modeling constructs. Define binary variables for arc activation and continuous variables for flow, linking them via capacity constraints. The objective minimizes the sum of fixed and variable costs.

### Step 1 - Define Sets and Parameters
- Define a set of nodes `N` and a set of arcs `A` as tuples `(i,j)`.
- Create parameter dictionaries for `demand` (keyed by node), `fixed_cost`, `variable_cost`, and `capacity` (keyed by arc).

### Step 2 - Declare Decision Variables
- Create binary variable `x[i,j]` for arc activation.
- Create non-negative continuous variable `f[i,j]` for flow.

### Step 3 - Formulate Objective and Constraints
- Objective: Minimize `sum(fixed_cost[i,j] * x[i,j] + variable_cost[i,j] * f[i,j] for (i,j) in A)`.
- Flow Conservation: For each node `i`, enforce `sum(f[j,i] for j if (j,i) in A) - sum(f[i,j] for j if (i,j) in A) == demand[i]`.
- Capacity Linking: For each arc `(i,j)`, enforce `f[i,j] <= capacity[i,j] * x[i,j]`.

### Formulation Template
```json
{
  "sets": ["N (nodes)", "A (arcs, as tuples (i,j))"],
  "parameters": ["demand[N]", "fixed_cost[A]", "variable_cost[A]", "capacity[A]"],
  "decision_variables": ["x[A] ∈ {0,1}", "f[A] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "∑_{A} (fixed_cost[i,j] * x[i,j] + variable_cost[i,j] * f[i,j])"
  },
  "constraints": [
    "flow_conservation[i ∈ N]: ∑_{(j,i)∈A} f[j,i] - ∑_{(i,j)∈A} f[i,j] = demand[i]",
    "capacity_linking[(i,j)∈A]: f[i,j] ≤ capacity[i,j] * x[i,j]"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-arcs from the arc set, which can lead to trivial, invalid solutions.
- Using incorrect sign in flow conservation (inflow minus outflow vs. outflow minus inflow) relative to the sign convention for `demand`.
- Defining `capacity` as a scalar instead of an arc-specific parameter, which oversimplifies the model.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the Gurobi solver via the Pyomo interface. Configure solver options for performance and reliability, then rigorously check termination status before extracting and validating the solution.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory('gurobi')`.
- Set key options: `TimeLimit`, `MIPGap`, `Threads`, and `Seed` for reproducibility.
- Solve with `tee=True` to stream the log: `results = solver.solve(model, tee=True)`.

### Step 2 - Check Solution Status
- Import `SolverStatus` and `TerminationCondition` from `pyomo.opt`.
- Verify `results.solver.status == SolverStatus.ok`.
- Verify `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value: `pyo.value(model.obj)`.
- Iterate over variables to collect active arcs (`x[i,j] > 0.5`) and flow values.
- Optionally, recompute flow balance at each node and total cost from extracted values for validation.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (function defined elsewhere, e.g., build_model())
model = build_model()

solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
# Add other options as needed (Threads, Seed, etc.)

results = solver.solve(model, tee=True)  # tee=True shows solver log

# Status check
status_ok = results.solver.status == SolverStatus.ok
term_ok = results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]

if status_ok and term_ok:
    total_cost = pyo.value(model.obj)
    print(f"RESULT:{total_cost}")
    # Extract solution details for validation
    active_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.x[i,j]) > 0.5]
    # ... further processing
else:
    # Output structured failure information
    failure_info = {
        "status": "failed",
        "reason": "Solver did not return an acceptable solution.",
        "solver_status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
    print(f"FAILURE:{failure_info}")
```

### Common Pitfalls
- Assuming a non-zero solver return code or an `ok` status alone guarantees an optimal solution.
- Not setting a `TimeLimit`, which can cause the solve to hang on difficult instances.
- Failing to handle `feasible` termination conditions, which provide a valid but potentially suboptimal solution.

# Workflow 2 (OR-Tools with SCIP)

## Modeling stage

### Strategy Overview
Model the problem directly using Google OR-Tools' linear solver wrapper. Create the model, variables, and constraints using the solver's native API, enforcing the same fixed-charge network flow logic.

### Step 1 - Initialize Solver and Data Structures
- Create solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Store node and arc data in lists or dictionaries (e.g., `demand`, `costs`, `capacities`).

### Step 2 - Create Variables with Bounds
- For each arc `(i,j)` where `i != j`, create:
  - `x[i,j] = solver.BoolVar(f'x_{i}_{j}')`
  - `f[i,j] = solver.NumVar(0, capacity[i][j], f'f_{i}_{j}')`
- For `i == j`, create dummy variables fixed to zero to prevent self-flow.

### Step 3 - Add Constraints and Objective
- Objective: Minimize `solver.Sum(fixed_cost[i][j] * x[i,j] + variable_cost[i][j] * f[i,j])`.
- Flow Conservation: For each node `i`, add `solver.Add(sum_inflow - sum_outflow == demand[i])`.
- Capacity Linking: For each arc `(i,j)`, add `solver.Add(f[i,j] <= capacity[i][j] * x[i,j])`.

### Formulation Template
```json
{
  "sets": ["nodes", "arcs (as pairs (i,j), i != j)"],
  "parameters": ["demand[node]", "fixed_cost[arc]", "variable_cost[arc]", "capacity[arc]"],
  "decision_variables": ["x[arc] ∈ {0,1}", "f[arc] ∈ [0, capacity[arc]]"],
  "objective": {
    "sense": "min",
    "expression": "∑_{arc} (fixed_cost[i,j] * x[i,j] + variable_cost[i,j] * f[i,j])"
  },
  "constraints": [
    "flow_conservation[node]: ∑_{j} f[j,node] - ∑_{j} f[node,j] = demand[node]",
    "capacity_linking[arc]: f[i,j] ≤ capacity[i,j] * x[i,j]",
    "no_self_flow[node]: x[node,node] = 0, f[node,node] = 0"
  ]
}
```

### Common Pitfalls
- Using `solver.IntVar` instead of `solver.BoolVar` for binary variables, which increases the search space unnecessarily.
- Neglecting to fix diagonal (self-flow) variables to zero, which can create degenerate solutions.
- Incorrectly indexing parameter dictionaries within constraints, leading to KeyErrors or incorrect model logic.

## Solving stage

### Strategy Overview
Solve the model using the SCIP solver via OR-Tools. Set practical limits, solve, and then perform explicit checks on the solver status and solution feasibility.

### Step 1 - Set Solver Limits and Solve
- Set a time limit: `solver.SetTimeLimit(30000)` for 30 seconds.
- Optionally set threads: `solver.SetNumThreads(4)`.
- Call `solver.Solve()` to execute.

### Step 2 - Verify Solver Result Status
- Check the result status: `status = solver.Solve()`.
- Accept solutions where `status == pywraplp.Solver.OPTIMAL` or `status == pywraplp.Solver.FEASIBLE`.

### Step 3 - Extract and Validate Solution
- If status is acceptable, retrieve the objective value: `solver.Objective().Value()`.
- Iterate over variables: use `x[i,j].solution_value() > 0.5` to identify active arcs and get corresponding `f[i,j].solution_value()`.
- Validate by recomputing node balances and checking capacity constraints.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Assume data structures (nodes, demand_dict, cost_dict, capacity_dict) are defined
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(30000)  # in milliseconds

# Variable creation
x, f = {}, {}
for i in nodes:
    for j in nodes:
        if i != j:
            x[i,j] = solver.BoolVar(f'x_{i}_{j}')
            f[i,j] = solver.NumVar(0, capacity_dict[i][j], f'f_{i}_{j}')
        else:
            # Create and fix self-flow variables to zero
            x[i,i] = solver.BoolVar(f'x_{i}_{i}')
            f[i,i] = solver.NumVar(0, 0, f'f_{i}_{i}')
            solver.Add(x[i,i] == 0)
            solver.Add(f[i,i] == 0)

# Objective
obj_expr = []
for (i,j) in arcs:
    obj_expr.append(fixed_cost_dict[i][j] * x[i,j])
    obj_expr.append(variable_cost_dict[i][j] * f[i,j])
solver.Minimize(solver.Sum(obj_expr))

# Flow conservation constraints
for i in nodes:
    inflow = solver.Sum(f[j,i] for j in nodes if (j,i) in arcs)
    outflow = solver.Sum(f[i,j] for j in nodes if (i,j) in arcs)
    solver.Add(inflow - outflow == demand_dict[i])

# Capacity linking constraints
for (i,j) in arcs:
    solver.Add(f[i,j] <= capacity_dict[i][j] * x[i,j])

# Solve
status = solver.Solve()

# Result handling
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    print(f"RESULT:{total_cost}")
    # Extract solution
    active_arcs = [(i,j) for (i,j) in arcs if x[i,j].solution_value() > 0.5]
    # ... validation and further processing
else:
    # Solver did not find a feasible solution
    print("FAILURE:Solver returned status", status)
```

### Common Pitfalls
- Trusting a `FEASIBLE` status as optimal without noting the potential optimality gap.
- Not using `.solution_value()` method to retrieve variable values, which differs from Pyomo's `pyo.value()`.
- Omitting post-solution validation, which can miss subtle constraint violations due to floating-point arithmetic.
