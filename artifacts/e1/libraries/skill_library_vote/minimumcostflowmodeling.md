---
name: MinimumCostFlowModeling
description: |
  Model and solve minimum cost flow problems on directed networks with supply/demand nodes and capacitated arcs using linear programming.
---

# Workflow 1 (Pyomo with Explicit Constraint Rules)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling with explicit constraint rules, ideal for clear separation of model components and integration with open-source solvers like CBC. It emphasizes set-based definitions and rule-based constraint construction.

### Step 1 - Define Network Structure
- Define the set of nodes `N` and the set of directed arcs `A` as a 2-dimensional set of ordered pairs `(i, j)`.
- Use dictionaries to initialize parameters for node demand `demand[i]`, arc cost `cost[i,j]`, and arc capacity `capacity[i,j]`.

### Step 2 - Declare Flow Variables
- Create a non-negative continuous variable `x[i,j]` for each arc `(i,j)` in set `A`.
- Optionally, enforce capacity limits by setting an upper bound on the variable during declaration (e.g., `bounds=(0, capacity[i,j])`).

### Step 3 - Formulate Flow Conservation
- For each node `i` in `N`, enforce the balance: total inflow minus total outflow equals net demand.
- Implement this via a `Constraint` rule that sums variables for incoming arcs `(j,i)` and outgoing arcs `(i,j)`, checking membership in `A`.

### Step 4 - Set Linear Cost Objective
- Define the objective to minimize the total linear transportation cost: sum of `cost[i,j] * x[i,j]` over all arcs.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes."},
    {"name": "A", "description": "Set of directed arcs as ordered pairs (i,j).", "dimen": 2}
  ],
  "parameters": [
    {"name": "demand", "index": "N", "description": "Net demand at node i (positive for demand, negative for supply)."},
    {"name": "cost", "index": "A", "description": "Unit cost of flow on arc (i,j)."},
    {"name": "capacity", "index": "A", "description": "Maximum flow allowed on arc (i,j)."}
  ],
  "decision_variables": [
    {"name": "x", "index": "A", "domain": "NonNegativeReals", "description": "Flow amount on arc (i,j)."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for (i,j) in A)"
  },
  "constraints": [
    {"name": "flow_balance", "index": "N", "expression": "sum(x[j,i] for j in N if (j,i) in A) - sum(x[i,j] for j in N if (i,j) in A) == demand[i]"},
    {"name": "capacity_limit", "index": "A", "expression": "x[i,j] <= capacity[i,j]"}
  ]
}
```

### Common Pitfalls
- Using generator expressions that reference variables for arcs not in set `A`, causing `KeyError`. Always filter arcs using `if (i,j) in A` *before* variable lookup.
- Misplacing the sign convention for demand (supply should be negative). Ensure `inflow - outflow = demand` with demand positive for net inflow nodes.
- Defining capacity constraints as separate `Constraint` objects when variable bounds are sufficient, adding unnecessary model overhead.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via `SolverFactory`. Focus on robust solution extraction, status verification, and post-solution validation of flow balances.

### Step 1 - Configure and Execute Solver
- Instantiate the solver (e.g., `SolverFactory('cbc')`).
- Set appropriate limits: time limit (`seconds`), optimality tolerance (`ratio`), and thread count for performance.
- Call `solver.solve(model, ...)` and capture the results object.

### Step 2 - Validate Solver Status
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- If status is not acceptable, raise an error or report failure before attempting solution extraction.

### Step 3 - Extract and Filter Solution
- Retrieve the objective value via `pyo.value(model.obj)`.
- Iterate over all arcs `(i,j)` in `A`, collect flow values for `model.x[i,j]` where the value exceeds a small tolerance (e.g., `1e-6`).
- Optionally, compute and display node balances to verify constraint satisfaction.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# Build model from formulation (assuming model 'm' is defined per template)
# ... (model construction code)

# Solve with status / termination checks
solver = SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(m)

status = results.solver.status
termination = results.solver.termination_condition

if status == SolverStatus.ok and termination in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = pyo.value(m.obj)
    # Extract non-zero flows
    active_flows = []
    for (i, j) in m.A:
        flow_val = pyo.value(m.x[i, j])
        if flow_val > 1e-6:
            active_flows.append((i, j, flow_val))
    print(f"Objective: {objective_value}")
    print(f"Active flows: {active_flows}")
else:
    print(f"Solver failed with status: {status}, termination: {termination}")
```

### Common Pitfalls
- Not checking solver status before accessing variable values, leading to runtime errors on infeasible/unbounded models.
- Using a loose tolerance for checking non-zero flows, which can clutter output with numerically insignificant values.
- Omitting post-solution balance verification, missing potential modeling errors or numerical inaccuracies.

# Workflow 2 (OR-Tools with Variable Bounds)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`), which is optimized for direct construction of LP models. It leverages variable bounds for capacity limits and list comprehensions for efficient constraint building.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance using `pywraplp.Solver.CreateSolver('GLOP')` for linear problems.
- Define dictionaries for arc costs and capacities, indexed by `(i,j)` tuples.
- Create a list `arcs` containing all directed arcs present in the network.

### Step 2 - Create Flow Variables with Bounds
- For each arc `(i,j)` in the `arcs` list, create a continuous variable `x[(i,j)]` using `solver.NumVar(lower_bound, upper_bound, name)`.
- Set `lower_bound = 0` and `upper_bound = capacity[(i,j)]` directly, incorporating capacity limits.

### Step 3 - Build Flow Conservation Constraints
- For each node `i`, compute its inflow terms (variables `x[(j,i)]` where `(j,i)` in `arcs`) and outflow terms (variables `x[(i,j)]` where `(i,j)` in `arcs`).
- Add a linear constraint: `sum(inflow) - sum(outflow) == demand[i]` using `solver.Add(...)`.

### Step 4 - Define Linear Cost Objective
- Set the objective to minimize `sum(cost[(i,j)] * x[(i,j)] for (i,j) in arcs)` using `solver.Minimize()`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "List of all nodes."},
    {"name": "arcs", "description": "List of directed arcs as tuples (source, destination)."}
  ],
  "parameters": [
    {"name": "demand", "index": "N", "description": "Net demand at node i."},
    {"name": "cost", "index": "arcs", "description": "Unit cost per arc, accessed via tuple key."},
    {"name": "capacity", "index": "arcs", "description": "Capacity per arc, accessed via tuple key."}
  ],
  "decision_variables": [
    {"name": "x", "index": "arcs", "domain": "Continuous, bounded [0, capacity]", "description": "Flow variable for each arc."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[arc] * x[arc] for arc in arcs)"
  },
  "constraints": [
    {"name": "flow_balance", "index": "N", "expression": "sum(x.get((j,i), 0) for j in N if (j,i) in arcs) - sum(x.get((i,j), 0) for j in N if (i,j) in arcs) == demand[i]"}
  ]
}
```

### Common Pitfalls
- Using a single list of arcs without a clear way to filter inflows/outflows per node, leading to inefficient constraint building.
- Forgetting to handle cases where a node has no incoming or outgoing arcs, resulting in empty sums; ensure the constraint expression can handle zero terms.
- Defining capacity limits as separate `solver.Add(x <= capacity)` constraints instead of using variable bounds, which is less efficient.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' built-in LP solver. Focus on efficient constraint construction, solver parameter tuning, and concise extraction of the operational solution (non-zero flows).

### Step 1 - Set Solver Parameters and Solve
- Set a time limit using `solver.SetTimeLimit(ms)` to prevent excessive runtime.
- Call `solver.Solve()` and check the result status (`pywraplp.Solver.OPTIMAL` or `FEASIBLE`).

### Step 2 - Extract and Report Solution
- Retrieve the objective value via `solver.Objective().Value()`.
- Iterate over the `arcs` list, get the solution value for each variable `x[arc].solution_value()`, and record flows above a tolerance.
- Print a summary of the objective and active flows.

### Step 3 - Optional Solution Verification
- For each node, recompute inflow and outflow from the solution values to verify the balance constraint holds within a small tolerance.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# Assume arcs, cost, capacity, demand dictionaries are defined
x = {}
for (i, j) in arcs:
    x[(i, j)] = solver.NumVar(0, capacity[(i, j)], f'x_{i}_{j}')

# Flow conservation constraints
for i in nodes:
    inflow_terms = [x[(j, i)] for (j, k) in arcs if k == i]
    outflow_terms = [x[(i, j)] for (j, k) in arcs if j == i]
    solver.Add(solver.Sum(inflow_terms) - solver.Sum(outflow_terms) == demand[i])

# Objective
objective_terms = [cost[(i, j)] * x[(i, j)] for (i, j) in arcs]
solver.Minimize(solver.Sum(objective_terms))

# Solve with status / termination checks
solver.SetTimeLimit(30000)  # 30 seconds in milliseconds
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    print(f'Objective value = {solver.Objective().Value()}')
    print('Non-zero flows:')
    for (i, j) in arcs:
        flow_val = x[(i, j)].solution_value()
        if flow_val > 1e-6:
            print(f'  {i} -> {j}: {flow_val}')
else:
    print('The problem does not have an optimal solution.')
```

### Common Pitfalls
- Not using `solver.Sum()` for aggregating terms in OR-Tools, leading to incorrect constraint expressions.
- Accessing variables via incorrect keys when building inflow/outflow lists, causing `KeyError`. Ensure the arc list filtering logic matches the variable dictionary keys.
- Ignoring the solver status and assuming optimality, which may lead to interpreting invalid results.
