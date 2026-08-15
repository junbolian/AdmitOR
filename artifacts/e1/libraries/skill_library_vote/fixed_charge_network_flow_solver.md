---
name: Fixed-Charge Network Flow Solver
description: |
  Model and solve network flow problems with fixed route activation costs and variable flow costs using mixed-integer programming, with robust solver configuration and solution validation.
---

# Workflow 1 (High-Level Modeling with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's high-level, structured modeling syntax to define a fixed-charge network flow problem. It emphasizes clear separation of sets, parameters, variables, and constraints for maintainability and ease of debugging.

### Step 1 - Define Model Structure
- Instantiate a Pyomo `ConcreteModel` to contain all problem components.
- Define the `Set` of nodes and the `Set` of directed arcs, which can be a subset of all possible node pairs.

### Step 2 - Declare Parameters
- Add parameters for `supply` (positive for supply nodes, negative for demand nodes), `capacity`, `fixed_cost`, and `variable_cost` for each arc.
- Use `Param` components indexed over the appropriate sets for efficient data handling.

### Step 3 - Create Decision Variables
- Define binary variables `y[arc]` for route activation (`Var(within=Binary)`).
- Define continuous variables `x[arc]` for flow quantities (`Var(within=NonNegativeReals, bounds=(0, capacity[arc]))`).

### Step 4 - Formulate Objective and Constraints
- Add the objective to minimize total fixed and variable costs: `sum(fixed_cost[a] * y[a] + variable_cost[a] * x[a] for a in arcs)`.
- Add flow conservation constraints: for each node `i`, `sum(x[i,j] for j) - sum(x[j,i] for j) == supply[i]`.
- Add capacity linking constraints: for each arc `a`, `x[a] <= capacity[a] * y[a]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of nodes"},
    {"name": "A", "description": "Set of directed arcs (i,j)"}
  ],
  "parameters": [
    {"name": "supply", "index": "N", "description": "Net supply (>0) or demand (<0) at each node"},
    {"name": "capacity", "index": "A", "description": "Maximum flow on an arc"},
    {"name": "fixed_cost", "index": "A", "description": "Cost to activate an arc"},
    {"name": "variable_cost", "index": "A", "description": "Cost per unit flow on an arc"}
  ],
  "decision_variables": [
    {"name": "y", "index": "A", "type": "binary", "description": "1 if arc is active, 0 otherwise"},
    {"name": "x", "index": "A", "type": "continuous", "description": "Flow quantity on arc"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[a] * y[a] + variable_cost[a] * x[a] for a in A)"
  },
  "constraints": [
    {"name": "flow_conservation", "index": "N", "expression": "sum(x[i,j] for (i,j) in A) - sum(x[j,i] for (j,i) in A) == supply[i]"},
    {"name": "capacity_link", "index": "A", "expression": "x[a] <= capacity[a] * y[a]"}
  ]
}
```

### Common Pitfalls
- Forgetting to ensure total supply equals total demand, which can lead to infeasibility.
- Defining the arc set as all possible node pairs in dense networks, which creates unnecessary variables and slows the solve.
- Not providing upper bounds for flow variables, missing an opportunity to give the solver better bounding information.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via the `pyomo` command-line interface or Python script, with explicit checks for solver status and termination condition to ensure solution validity.

### Step 1 - Instantiate and Configure Solver
- Create a solver object using `SolverFactory('cbc')`.
- Set solver options such as `seconds` for time limit, `ratio` for optimality gap tolerance, and `threads` for parallel processing.

### Step 2 - Solve and Check Status
- Call `solver.solve(model, tee=True)` to execute the solve and print logs.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible` before proceeding.

### Step 3 - Extract and Validate Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate over arcs to collect active routes where `pyo.value(model.y[a]) > 0.5` and their corresponding flows `pyo.value(model.x[a])`.
- Optionally, post-solve validation code should recalculate net flows at each node to verify flow conservation.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (following Modeling stage steps)
model = pyo.ConcreteModel()
# ... define sets, params, variables, objective, constraints

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=True)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    print(f"Objective: {pyo.value(model.obj)}")
    for a in model.A:
        if pyo.value(model.y[a]) > 0.5:
            print(f"Active arc {a}: flow = {pyo.value(model.x[a])}")
else:
    print("Solver failed:", results.solver.termination_condition)
```

### Common Pitfalls
- Assuming a `SolverStatus.ok` means an optimal solution was found; always check the termination condition.
- Not using `tee=True` during development, missing valuable debug output from the solver.
- Extracting variable values without checking if the solver actually found a feasible solution, leading to errors.

# Workflow 2 (Direct Solver API with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (Google OR-Tools) for finer control and potentially faster model building. It is suited for environments where Pyomo is not available or when integrating into larger applications.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver('SCIP')`).
- Define data dictionaries for parameters (`capacity`, `fixed_cost`, `variable_cost`, `net_outflow`) indexed by arcs or nodes.

### Step 2 - Create Variables with Explicit Bounds
- Create binary variables `y[arc]` using `solver.IntVar(0, 1, name)`.
- Create continuous flow variables `x[arc]` using `solver.NumVar(0, capacity[arc], name)` to embed upper bounds.

### Step 3 - Build Constraints via Explicit Summation
- For flow conservation, iterate over nodes: calculate total outflow and inflow by summing over relevant arcs, then add constraint `outflow - inflow == net_outflow[node]`.
- For capacity linking, iterate over arcs: add constraint `x[arc] <= capacity[arc] * y[arc]`.

### Step 4 - Set Linear Objective
- Initialize the solver's objective function.
- Iterate over arcs to set coefficients for `y[arc]` (fixed cost) and `x[arc]` (variable cost).
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of nodes"},
    {"name": "A", "description": "Set of directed arcs"}
  ],
  "parameters": [
    {"name": "net_outflow", "index": "N", "description": "Net supply/demand at node"},
    {"name": "capacity", "index": "A", "description": "Maximum flow on an arc"},
    {"name": "fixed_cost", "index": "A", "description": "Cost to activate an arc"},
    {"name": "variable_cost", "index": "A", "description": "Cost per unit flow on an arc"}
  ],
  "decision_variables": [
    {"name": "y", "index": "A", "type": "integer", "bounds": "[0,1]", "description": "Arc activation"},
    {"name": "x", "index": "A", "type": "continuous", "bounds": "[0, capacity]", "description": "Flow on arc"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[a] * y[a] + variable_cost[a] * x[a] for a in A)"
  },
  "constraints": [
    {"name": "flow_conservation", "index": "N", "expression": "sum_outflow(i) - sum_inflow(i) == net_outflow[i]"},
    {"name": "capacity_link", "index": "A", "expression": "x[a] <= capacity[a] * y[a]"}
  ]
}
```

### Common Pitfalls
- Incorrectly building the inflow/outflow sums due to mismatched arc indices, breaking flow conservation.
- Forgetting to add the coefficient for the binary variable in the objective, effectively ignoring fixed costs.
- Using a solver that does not support mixed-integer programming (e.g., GLOP) for this problem type.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools wrapper, leveraging its direct control over the solver and access to detailed status codes. Includes a preliminary feasibility check via a relaxed LP.

### Step 1 - Optional Feasibility Check
- For debugging, solve a relaxed LP version (variables `x` continuous, ignore `y` and fixed costs) to verify flow conservation and capacity constraints are satisfiable.

### Step 2 - Solve MIP and Interpret Status
- Call `solver.Solve()`.
- Check the solver's return status (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNBOUNDED`) to determine success and guide error handling.

### Step 3 - Extract and Verify Solution
- If optimal or feasible, extract variable values using `Variable.solution_value()`.
- Programmatically verify that extracted flows satisfy all constraints as a sanity check.
- Present active routes, flow quantities, and cost breakdown.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... define arcs, parameters, create y and x variables

# Flow conservation constraints
for i in nodes:
    outflow_expr = sum(x[i,j] for j in nodes if (i,j) in arcs)
    inflow_expr = sum(x[j,i] for j in nodes if (j,i) in arcs)
    solver.Add(outflow_expr - inflow_expr == net_outflow[i])

# Capacity linking constraints
for (i,j) in arcs:
    solver.Add(x[i,j] <= capacity[i,j] * y[i,j])

# Objective
objective = solver.Objective()
for (i,j) in arcs:
    objective.SetCoefficient(y[i,j], fixed_cost[i,j])
    objective.SetCoefficient(x[i,j], variable_cost[i,j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    print(f"Objective: {objective.Value()}")
    for (i,j) in arcs:
        if y[i,j].solution_value() > 0.5:
            print(f"Active arc ({i},{j}): flow = {x[i,j].solution_value()}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Misinterpreting the solver status code; `FEASIBLE` does not guarantee optimality.
- Not using the `solution_value()` method and instead trying to print the variable object directly.
- Overlooking the need to scale large cost or capacity parameters, which can cause numerical issues for the solver.
