---
name: Fixed-Charge Network Flow Design
description: |
  Model and solve network design problems with fixed connection costs and continuous flow costs using binary activation and continuous flow variables.

---

# Workflow 1 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling to define a fixed-charge network flow problem, suitable for open-source solving with HiGHS. It emphasizes clean set and parameter definitions to separate data from model logic.

### Step 1 - Define Sets and Parameters
- Define a set of nodes `N` and a set of directed arcs `A` as a subset of `N × N`.
- Define parameters: fixed cost `f[i,j]`, variable cost `c[i,j]`, capacity `u[i,j]` for each arc, and net supply/demand `b[i]` for each node.

### Step 2 - Create Decision Variables
- Create binary variables `x[i,j]` for arc activation.
- Create non-negative continuous variables `y[i,j]` for flow on each arc.

### Step 3 - Formulate Objective and Constraints
- Formulate the objective to minimize total cost: sum of fixed costs (`f[i,j] * x[i,j]`) plus variable costs (`c[i,j] * y[i,j]`).
- Add capacity linking constraint: `y[i,j] <= u[i,j] * x[i,j]` for each arc.
- Add flow conservation constraint: sum of inflow minus sum of outflow equals net supply `b[i]` for each node.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of nodes"},
    {"name": "A", "description": "Set of directed arcs (i,j) where i,j in N"}
  ],
  "parameters": [
    {"name": "f", "index": "A", "description": "Fixed cost for activating arc"},
    {"name": "c", "index": "A", "description": "Variable cost per unit flow on arc"},
    {"name": "u", "index": "A", "description": "Flow capacity of arc if activated"},
    {"name": "b", "index": "N", "description": "Net supply (positive) or demand (negative) at node"}
  ],
  "decision_variables": [
    {"name": "x", "index": "A", "type": "binary", "description": "1 if arc is activated"},
    {"name": "y", "index": "A", "type": "continuous", "lb": 0, "description": "Flow amount on arc"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{A} ( f[i,j] * x[i,j] + c[i,j] * y[i,j] )"
  },
  "constraints": [
    {"name": "capacity_link", "index": "A", "expression": "y[i,j] <= u[i,j] * x[i,j]"},
    {"name": "flow_conservation", "index": "N", "expression": "sum_{j: (j,i) in A} y[j,i] - sum_{j: (i,j) in A} y[i,j] == b[i]"}
  ]
}
```

### Common Pitfalls
- Creating variables for non-existent arcs (e.g., self-loops if prohibited). Ensure variable index set matches the defined arc set `A`.
- Hardcoding parameter values inside constraint rules. Reference model parameters (`model.f`, `model.u`) instead.
- Incorrectly indexing flow conservation constraints, leading to `KeyError`. Use conditional sums `sum(model.y[j,i] for j in model.N if (j,i) in model.A)`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via the `highs` direct interface or `appsi_highs`. Focus on robust status checking and solution extraction for automation.

### Step 1 - Instantiate Solver and Set Options
- Instantiate the HiGHS solver object via `SolverFactory('highs')`.
- Set appropriate options such as `time_limit` and `threads`. Avoid invalid parameters like `mip_rel_gap`.

### Step 2 - Solve and Check Status
- Call `solver.solve(model, load_solutions=False)` to prevent automatic loading.
- Check both `solver.status == SolverStatus.ok` and `termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Extract and Validate Solution
- If status is acceptable, load the solution into the model using `model.solutions.load_from(results)`.
- Extract active arcs by iterating over `model.x` and checking `value > 0.5`. Retrieve corresponding flow values from `model.y`.
- Optionally, perform post-solution validation of flow conservation and capacity constraints.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (using abstract or concrete pattern)
model = pyo.ConcreteModel()
# ... (model definition based on formulation template)

# Solve
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30.0  # placeholder
results = solver.solve(model, load_solutions=False)

# Check status
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    model.solutions.load_from(results)
    # Extract solution
    active_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.x[i,j]) > 0.5]
    total_cost = pyo.value(model.obj)
    # ... further processing
else:
    # Handle infeasible or error status
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Setting `mip_rel_gap = -1` or other invalid options for HiGHS. Use default optimality gap or set `mip_rel_gap = 0.0`.
- Accessing variable values before checking solver status and loading the solution, leading to stale or undefined values.
- Not separating diagnostic prints from structured output, breaking automated result parsing.

# Workflow 2 (PuLP with CBC)

## Modeling stage

### Strategy Overview
This workflow uses PuLP's intuitive, linear expression-based API to model the same fixed-charge network flow problem, targeting the CBC solver. It is well-suited for rapid prototyping and educational use.

### Step 1 - Initialize Problem and Create Variables
- Instantiate a `pulp.LpProblem` with a name and sense (`LpMinimize`).
- Create binary (`LpVariable` with `cat='Binary'`) and continuous (`cat='Continuous'`, `lowBound=0`) dictionaries indexed by arcs.

### Step 2 - Add Objective and Constraints Directly
- Build the objective by summing `fixed_cost * binary_var + variable_cost * flow_var` over all arcs using dictionary comprehension.
- Add capacity linking constraints via loops: `flow_var <= capacity * binary_var`.
- Add flow conservation constraints by summing inflows and outflows for each node.

### Step 3 - Handle Data Structures
- Use Python dictionaries or pandas DataFrames to store cost, capacity, and demand parameters.
- Ensure data structures align with the arc list to avoid missing keys.

### Formulation Template
```json
{
  "sets": [
    {"name": "nodes", "description": "List of node identifiers"},
    {"name": "arcs", "description": "List of tuples (i,j) representing directed arcs"}
  ],
  "parameters": [
    {"name": "fixed_cost", "index": "arcs", "description": "Fixed cost dictionary"},
    {"name": "variable_cost", "index": "arcs", "description": "Variable cost dictionary"},
    {"name": "capacity", "index": "arcs", "description": "Capacity dictionary"},
    {"name": "demand", "index": "nodes", "description": "Net supply/demand dictionary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "arcs", "type": "binary", "description": "Activation variable dictionary"},
    {"name": "y", "index": "arcs", "type": "continuous", "lb": 0, "description": "Flow variable dictionary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( fixed_cost[a] * x[a] + variable_cost[a] * y[a] for a in arcs )"
  },
  "constraints": [
    {"name": "capacity_link", "index": "arcs", "expression": "y[a] <= capacity[a] * x[a]"},
    {"name": "flow_conservation", "index": "nodes", "expression": "sum( y[(j,i)] for (j,i) in arcs if j in nodes ) - sum( y[(i,j)] for (i,j) in arcs if j in nodes ) == demand[i]"}
  ]
}
```

### Common Pitfalls
- Forgetting to filter arcs when constructing flow conservation sums, potentially leading to KeyError. Use list comprehension with a condition `if (j,i) in arcs`.
- Using the same variable name for both the PuLP variable object and its value after solving, causing confusion.
- Neglecting to set `lowBound=0` for flow variables, allowing negative flows.

## Solving stage

### Strategy Overview
Solve the PuLP model using the built-in CBC solver. Leverage PuLP's simple solve call and status attributes, with explicit solution value extraction.

### Step 1 - Solve and Check Status
- Call `problem.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=30))` (or other solvers).
- Check the status via `pulp.LpStatus[problem.status]`. Accept `'Optimal'` or `'Feasible'`.

### Step 2 - Extract Solution Values
- If status is acceptable, iterate over the variable dictionaries and use `pulp.value(var)` to get the solution.
- Collect active arcs where `pulp.value(x[a]) > 0.5`.
- Retrieve the objective value from `problem.objective.value()`.

### Step 3 - Output Structured Results
- Compile results (objective, list of active arcs, flow values) into a dictionary or JSON for downstream use.
- Optionally, compute derived metrics like total flow or capacity utilization.

### Code Usage
```python
import pulp

# Build model
prob = pulp.LpProblem('FixedChargeNetworkFlow', pulp.LpMinimize)
# ... (create variables and add constraints based on formulation template)

# Solve
solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=30)  # placeholder time limit
prob.solve(solver)

# Check status
status = pulp.LpStatus[prob.status]
if status in ('Optimal', 'Feasible'):
    # Extract solution
    active_arcs = [a for a in arcs if pulp.value(x[a]) > 0.5]
    flow_values = {a: pulp.value(y[a]) for a in arcs}
    total_cost = pulp.value(prob.objective)
    # ... compile results
else:
    # Handle infeasible or error
    print(f"Solver status: {status}")
```

### Common Pitfalls
- Not specifying `timeLimit` as a keyword argument (not `time_limit`) for `PULP_CBC_CMD`.
- Accessing `pulp.value` on a variable that was not part of the problem or before solving.
- Using `prob.objective` directly without `.value()` to get the numerical result.
