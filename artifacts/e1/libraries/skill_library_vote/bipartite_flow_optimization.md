---
name: Bipartite Flow Optimization
description: |
  Model and solve balanced or capacitated bipartite flow problems (e.g., transportation, assignment) with linear costs using structured LP formulations and robust solver integration.

---

# Workflow 1 (Pyomo-based LP with Open-Source Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a bipartite flow network using Pyomo's abstract modeling capabilities. This approach cleanly separates data from model structure, enabling reusable formulation patterns for balanced or capacitated problems.

### Step 1 - Define Index Sets
- Declare two disjoint Pyomo `Set` objects for supply nodes (origins) and demand nodes (destinations).
- Initialize sets with generic range indices or explicit labels to enable clean constraint indexing.

### Step 2 - Declare Parameters
- Store supply and demand as `Param` objects indexed by their respective sets.
- Store cost and optional capacity as `Param` objects indexed by the Cartesian product of origin and destination sets, using nested dictionaries for initialization.

### Step 3 - Create Flow Variables
- Define a non-negative continuous decision variable `flow` indexed over all origin-destination pairs, using `domain=pyo.NonNegativeReals`.
- For capacitated problems, upper bounds can be enforced via constraints or directly via variable bounds.

### Step 4 - Formulate Supply and Demand Constraints
- Implement supply constraints as linear equalities: total outflow from each origin must equal its supply.
- Implement demand constraints as linear equalities: total inflow to each destination must equal its demand.
- Use Pyomo `Constraint` objects with rule functions for concise, indexed declaration.

### Step 5 - Define Linear Cost Objective
- Formulate the objective as the sum of per-unit costs multiplied by the corresponding flow variables.
- Set the objective sense to `minimize`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations"],
  "parameters": ["supply[origins]", "demand[destinations]", "cost[origins, destinations]", "capacity[origins, destinations] (optional)"],
  "decision_variables": ["flow[origins, destinations] ∈ ℝ⁺"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * flow[i,j] for i in origins, j in destinations)"
  },
  "constraints": [
    "supply_con[i]: sum(flow[i,j] for j in destinations) == supply[i]",
    "demand_con[j]: sum(flow[i,j] for i in origins) == demand[j]",
    "capacity_con[i,j]: flow[i,j] <= capacity[i,j] (if applicable)"
  ]
}
```

### Common Pitfalls
- Assuming infinite capacity for arcs when capacity data is incomplete; explicitly note missing data.
- Forgetting to verify total supply equals total demand before solving, which is required for feasibility with equality constraints.
- Using placeholder values (e.g., 1000) for unknown capacities without documenting the assumption, masking data gaps.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source LP solver (e.g., CBC, HiGHS) with appropriate configuration for performance and reliability. Implement robust solution checking and validation.

### Step 1 - Configure and Execute Solver
- Instantiate the solver via `SolverFactory("solver_name")` (e.g., "cbc", "highs").
- Set practical solver options: time limit (`seconds`), optimality gap (`ratio=0.0` for exact), and thread count for parallelism.
- Call `solver.solve(model, tee=False)` to execute.

### Step 2 - Check Solver Status and Termination
- Verify `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition` is `optimal` or `feasible` before extracting results.
- If status is not ok or termination is not acceptable, handle as an infeasible or error case.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value using `float(pyo.value(model.obj))`.
- Iterate through flow variables, extracting values with `pyo.value(model.flow[i,j])`.
- Programmatically verify all constraints: compute sums of flows for each origin/destination and compare against supply/demand within a small tolerance (e.g., 1e-6).
- For capacitated problems, verify no flow exceeds its arc capacity.

### Step 4 - Report Results
- Output the total cost in a parseable format (e.g., `RESULT:{value}`).
- Print a clean summary of non-zero flows (filtering values below a threshold like 1e-6).
- Include verification summaries for debugging and transparency.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (example structure)
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_origins))
model.J = pyo.Set(initialize=range(num_destinations))
# ... define parameters, variables, constraints, objective

# Solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_cost = float(pyo.value(model.obj))
    # Extract and verify flow values
else:
    # Handle infeasible/error case
```

### Common Pitfalls
- Failing to check both solver status *and* termination condition, leading to extraction from failed solves.
- Not verifying constraint satisfaction post-solve, which can miss numerical issues or solver errors.
- Using excessive trial-and-error with guessed parameter values instead of systematic sensitivity analysis.

# Workflow 2 (Direct API with Bounded Variables)

## Modeling stage

### Strategy Overview
Formulate the problem using a solver's direct API (e.g., OR-Tools, PuLP) where variable bounds are set during creation. This approach integrates capacity limits directly into variable definitions, often improving presolve efficiency.

### Step 1 - Organize Data Structures
- Store supply, demand, cost, and capacity as plain Python lists or nested dictionaries.
- Use consistent indexing: `i` for origins, `j` for destinations.

### Step 2 - Instantiate Solver and Variables
- Create a solver instance (e.g., `pulp.LpProblem` or `ortools.linear_solver.Solver`).
- In a nested loop over all origin-destination pairs, create a continuous non-negative variable.
- Set the variable's upper bound directly to the arc capacity (or a large number if uncapacitated) during creation.

### Step 3 - Add Supply and Demand Constraints
- For each origin, create a linear equality constraint: sum of outgoing flow variables equals supply.
- For each destination, create a linear equality constraint: sum of incoming flow variables equals demand.
- Use the solver's constraint addition method, setting coefficients to 1 for relevant variables.

### Step 4 - Set Linear Minimization Objective
- Initialize the solver's objective function.
- For each variable, add its coefficient as the per-unit transportation cost.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": ["origins (list)", "destinations (list)"],
  "parameters": ["supply_list", "demand_list", "cost_matrix", "capacity_matrix (optional)"],
  "decision_variables": ["flow[i][j] with lower_bound=0, upper_bound=capacity[i][j]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_matrix[i][j] * flow[i][j])"
  },
  "constraints": [
    "for each origin i: sum(flow[i][j] over j) == supply_list[i]",
    "for each destination j: sum(flow[i][j] over i) == demand_list[j]"
  ]
}
```

### Common Pitfalls
- Mixing solution validation with problem formulation; keep these steps separate.
- Using arbitrarily large placeholder upper bounds (e.g., 1000) without checking if they exceed reasonable limits, potentially hiding infeasibility.
- Creating incomplete formulations with placeholder values for missing parameters without documenting the uncertainty.

## Solving stage

### Strategy Overview
Solve the model using the solver's native solve method. Leverage direct variable bounds for efficiency and implement independent verification of the solution.

### Step 1 - Execute Solver
- Call the solver's solve method (e.g., `prob.solve()` for PuLP, `solver.Solve()` for OR-Tools).
- Optionally set a time limit on the solver if supported.

### Step 2 - Validate Solver Status
- Check the solver's reported status (e.g., `pulp.LpStatus[prob.status] == 'Optimal'`, or `solver.OPTIMAL` in OR-Tools).
- Accept both `OPTIMAL` and `FEASIBLE` statuses as successful solves.

### Step 3 - Extract Solution and Verify Feasibility
- Retrieve the objective value from the solver.
- Extract all variable values, filtering near-zero flows for a clean report.
- Implement an independent verification function that recomputes constraint sums from the extracted flows and compares them against original supply/demand data and capacity bounds.

### Step 4 - Cross-Validate with Alternative Solver
- For critical applications, solve the same model with a different solver backend (e.g., GLOP then CBC) to confirm solution consistency and optimality.

### Code Usage
```python
# Example using OR-Tools GLOP
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# Create variables with bounds
x = {}
for i in range(num_origins):
    for j in range(num_destinations):
        ub = capacity[i][j] if capacity else solver.infinity()
        x[i, j] = solver.NumVar(0, ub, f'x_{i}_{j}')
# Add constraints
for i in range(num_origins):
    constraint = solver.Constraint(supply[i], supply[i])
    for j in range(num_destinations):
        constraint.SetCoefficient(x[i, j], 1)
# ... add demand constraints and objective

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    # Extract flows and verify
else:
    # Handle failed solve
```

### Common Pitfalls
- Checking solution feasibility against only a subset of constraints; verify all supply, demand, and capacity constraints.
- Concluding constraints are "not binding" based on a single uncapacitated solution without sensitivity analysis.
- Making final decisions based on incomplete analysis when multiple capacity scenarios yield different costs; report the range instead.
