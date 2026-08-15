---
name: Network Flow with Arc and Node Capacities
description: |
  Model and solve linear network flow problems with capacity constraints on both arcs and nodes, minimizing total cost while respecting flow conservation and capacity limits.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract model definition, leveraging its expressive constraint syntax. It is well-suited for sparse networks, using dictionaries for parameters and conditional constraint generation to handle missing arcs efficiently. The model cleanly separates flow conservation, arc capacity, and node capacity constraints.

### Step 1 - Define Sets and Parameters
- Represent the node set as a list of unique identifiers (e.g., `nodes`).
- Store arc-specific data (cost, capacity) in dictionaries keyed by `(i, j)` tuples to handle sparse networks.
- Define node-specific data (net demand, capacity) in dictionaries keyed by node ID.

### Step 2 - Create Flow Variables
- Instantiate continuous flow variables `model.x[i, j]` for each arc present in the cost or capacity dictionary.
- Set variable bounds directly during creation: `lower=0, upper=arc_capacity.get((i, j), None)`.

### Step 3 - Implement Flow Conservation Constraints
- For each node `i`, calculate total inflow (`sum(model.x[j, i] for j in nodes if (j, i) in arcs)`) and outflow (`sum(model.x[i, j] for j in nodes if (i, j) in arcs)`).
- Enforce the constraint: `inflow - outflow == net_demand[i]`.

### Step 4 - Apply Node Capacity Constraints
- For nodes with a defined capacity, add a constraint limiting total inflow: `sum(model.x[j, i] for j in nodes if (j, i) in arcs) <= node_capacity[i]`.
- Use `pyo.Constraint.Skip` for nodes without a capacity limit.

### Step 5 - Formulate the Objective
- Define the objective to minimize total cost: `sum(cost[i, j] * model.x[i, j] for (i, j) in arcs)`.

### Formulation Template
```json
{
  "sets": [
    "N: Set of nodes",
    "A: Set of arcs (subset of N x N)"
  ],
  "parameters": [
    "cost_{ij}: Unit cost on arc (i,j) ∈ A",
    "arc_capacity_{ij}: Maximum flow on arc (i,j) ∈ A",
    "net_demand_i: Net demand/supply at node i ∈ N (demand > 0, supply < 0)",
    "node_capacity_i: Maximum inflow at node i ∈ N (optional)"
  ],
  "decision_variables": [
    "x_{ij}: Flow on arc (i,j) ∈ A, continuous, non-negative"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j) ∈ A} cost_{ij} * x_{ij}"
  },
  "constraints": [
    "Flow conservation: ∑_{j: (j,i) ∈ A} x_{ji} - ∑_{j: (i,j) ∈ A} x_{ij} = net_demand_i, ∀ i ∈ N",
    "Arc capacity: x_{ij} ≤ arc_capacity_{ij}, ∀ (i,j) ∈ A",
    "Node capacity (if applicable): ∑_{j: (j,i) ∈ A} x_{ji} ≤ node_capacity_i, ∀ i ∈ N with capacity defined"
  ]
}
```

### Common Pitfalls
- Creating variables or constraints for non-existent arcs, leading to KeyErrors or unnecessary model bloat. Always check membership in the arc set.
- Forgetting to handle nodes with zero net demand, which still require a flow conservation constraint.
- Mixing node capacity and flow conservation into a single, complex constraint, reducing model clarity.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS (preferred for LP) or CBC (MIP-capable) solver via the `pyomo` solver factory. The focus is on robust solver configuration, comprehensive solution status checking, and post-solution validation of constraints.

### Step 1 - Configure and Execute Solver
- Instantiate the solver (e.g., `solver = pyo.SolverFactory('appsi_highs')` or `solver = pyo.SolverFactory('cbc')`).
- Set solver parameters: `solver.options['time_limit'] = time_limit`, `solver.options['threads'] = thread_count`.
- Call `results = solver.solve(model, tee=verbose)`.

### Step 2 - Check Solver Status and Termination
- Verify the solve was successful: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition is acceptable: `assert results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]`.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value: `obj_val = pyo.value(model.obj)`.
- Iterate over flow variables, collecting those with value > `tolerance` (e.g., 1e-6).
- Programmatically verify key constraints (flow balance, capacities) are satisfied within tolerance.

### Step 4 - Handle Failures Gracefully
- If the solver fails or returns infeasible, catch the assertion error and return a structured error message with solver status and termination condition.
- Log or report the infeasibility for debugging.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (model) from formulation defined earlier
# ...

# Solve
solver = pyo.SolverFactory('appsi_highs')  # or 'cbc'
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, tee=False)

# Check status / termination
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    obj_val = pyo.value(model.obj)
    # Extract non-zero flows
    solution_flows = {}
    for idx, var in model.x.items():
        val = pyo.value(var)
        if val > 1e-6:
            solution_flows[idx] = val
    # ... (validation logic)
else:
    raise Exception(f"Solver failed: Status={results.solver.status}, Termination={results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming `SolverStatus.ok` alone guarantees an optimal solution; always check `termination_condition`.
- Not using a tolerance when checking variable values against zero, leading to incorrect filtering due to numerical noise.
- Omitting post-solution validation, which can miss subtle constraint violations.

# Workflow 2 (OR-Tools with GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools linear solver wrapper, constructing the model via a direct, imperative API. It is optimized for performance on pure linear programs. Variable bounds are set at creation to encode arc capacities, and constraints are added incrementally.

### Step 1 - Initialize Solver and Data Structures
- Create a linear solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Use dictionaries (`cost`, `arc_capacity`, `node_capacity`, `net_demand`) for parameter storage.

### Step 2 - Create Bounded Flow Variables
- For each arc `(i, j)` in the parameter dictionaries, create a variable: `x[(i, j)] = solver.NumVar(0, arc_capacity[(i, j)], f'x_{i}_{j}')`.
- This directly enforces the arc capacity bound.

### Step 3 - Build Flow Conservation Constraints
- For each node `i`, compute inflow by summing `x.get((j, i), 0)` and outflow by summing `x.get((i, j), 0)`.
- Add the equality constraint: `solver.Add(inflow - outflow == net_demand[i], f'balance_{i}')`.

### Step 4 - Add Node Capacity Constraints
- For each node `i` with a defined `node_capacity`, compute total inflow.
- Add the inequality constraint: `solver.Add(inflow <= node_capacity[i], f'nodecap_{i}')`.

### Step 5 - Define Linear Objective
- Build the objective expression by iterating over arcs: `solver.Objective().SetCoefficient(x[(i, j)], cost[(i, j)])`.
- Set the objective sense to minimization: `solver.Objective().SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "N: Set of nodes",
    "A: Set of arcs (implicitly defined by parameter dictionaries)"
  ],
  "parameters": [
    "cost_{ij}: Unit cost on arc (i,j) with data",
    "arc_capacity_{ij}: Maximum flow on arc (i,j) (upper bound for variable)",
    "net_demand_i: Net demand at node i",
    "node_capacity_i: Maximum inflow at node i (optional)"
  ],
  "decision_variables": [
    "x_{ij}: Flow variable with lower=0, upper=arc_capacity_{ij}"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑ cost_{ij} * x_{ij}"
  },
  "constraints": [
    "Flow conservation: ∑_j x_{ji} - ∑_j x_{ij} = net_demand_i, ∀ i ∈ N",
    "Node capacity: ∑_j x_{ji} ≤ node_capacity_i, ∀ i ∈ N with capacity defined"
  ]
}
```

### Common Pitfalls
- Using `solver.NumVar(0, solver.infinity(), ...)` for uncapacitated arcs instead of a large numeric bound, which can sometimes lead to numerical issues.
- Forgetting to handle missing arcs in inflow/outflow sums, which requires using `.get(key, 0)`.
- Adding redundant constraints (like `x <= arc_capacity`) when the bound is already set on the variable.

## Solving stage

### Strategy Overview
Solve the model using the built-in `GLOP` LP solver, which is efficient for continuous network flow problems. The workflow emphasizes setting solver parameters, extracting the solution, and performing a thorough validation of results.

### Step 1 - Configure Solver and Solve
- Set solver time limit: `solver.SetTimeLimit(time_limit_ms)`.
- Set number of threads: `solver.SetNumThreads(thread_count)`.
- Call `status = solver.Solve()`.

### Step 2 - Interpret Solver Status
- Check if an optimal or feasible solution was found: `if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]`.
- Handle other statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) with appropriate error messages.

### Step 3 - Extract and Filter Solution
- Retrieve the objective value: `obj_val = solver.Objective().Value()`.
- Iterate over all flow variables, storing those where `var.solution_value() > tolerance`.
- Optionally, compute reduced costs or dual values for advanced validation.

### Step 4 - Validate Against Original Constraints
- Recompute inflows, outflows, and check flow conservation and capacity constraints using the extracted solution values.
- Log any violations beyond a specified tolerance.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (create variables, constraints, objective as per modeling stage)

# Configure and solve
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)
status = solver.Solve()

# Check status / termination
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    obj_val = solver.Objective().Value()
    solution_flows = {}
    tolerance = 1e-6
    # Assuming 'x' is the dict of flow variables
    for idx, var in x.items():
        val = var.solution_value()
        if val > tolerance:
            solution_flows[idx] = val
    # ... (validation logic)
elif status == solver.INFEASIBLE:
    raise Exception("Model is infeasible.")
elif status == solver.UNBOUNDED:
    raise Exception("Model is unbounded.")
else:
    raise Exception(f"Solver stopped with status: {status}")
```

### Common Pitfalls
- Confusing `solver.OPTIMAL` with `solver.FEASIBLE`; both indicate a valid solution, but only `OPTIMAL` guarantees optimality.
- Not setting a time limit for potentially large instances, risking long runtimes.
- Skipping solution validation, which is crucial for catching modeling errors or solver inaccuracies.
