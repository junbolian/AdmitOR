---
name: Balanced Transportation Problem
description: |
  Model and solve balanced bipartite flow problems with supply and demand nodes using linear programming.

---

# Workflow 1 (Google OR-Tools LP)

## Modeling stage

### Strategy Overview
Model the balanced transportation problem as a linear program using Google OR-Tools' linear solver wrapper. This approach is suitable for prototyping and leverages efficient, high-performance LP solvers like GLOP.

### Step 1 - Define Problem Sets and Parameters
- Identify the two distinct sets: `origins` (supply nodes) and `destinations` (demand nodes).
- Define parameters: `supply[i]` for each origin, `demand[j]` for each destination, and a cost matrix `cost[i][j]`.
- Verify the problem is balanced: total supply must equal total demand.

### Step 2 - Create Flow Variables
- Create non-negative continuous decision variables `x[i][j]` for flow from origin `i` to destination `j`.
- Use `solver.NumVar(0, solver.infinity(), f'x_{i}_{j}')` within nested loops over `origins` and `destinations`.

### Step 3 - Formulate Supply and Demand Constraints
- For each origin `i`, add a constraint: `sum_{j} x[i][j] == supply[i]`.
- For each destination `j`, add a constraint: `sum_{i} x[i][j] == demand[j]`.
- Use `solver.Add()` and `SetCoefficient` to build constraints efficiently.

### Step 4 - Define Linear Objective
- Formulate the objective to minimize total transportation cost: `sum_{i} sum_{j} cost[i][j] * x[i][j]`.
- Use `solver.Minimize()` and set coefficients for all variables.

### Formulation Template
```json
{
  "sets": ["origins", "destinations"],
  "parameters": ["supply[origin]", "demand[destination]", "cost[origin][destination]"],
  "decision_variables": ["x[origin][destination] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum_{origin} sum_{destination} cost[origin][destination] * x[origin][destination]"
  },
  "constraints": [
    "sum_{destination} x[origin][destination] == supply[origin], for all origin",
    "sum_{origin} x[origin][destination] == demand[destination], for all destination"
  ]
}
```

### Common Pitfalls
- Forgetting to verify problem balance before building the model, leading to infeasibility.
- Using inefficient loops for constraint creation on large-scale instances.
- Not handling zero-supply origins or zero-demand destinations, which can cause unnecessary variable creation.

## Solving stage

### Strategy Overview
Solve the linear program using the OR-Tools solver wrapper, selecting an appropriate LP backend (e.g., GLOP). Implement robust solution checking and validation.

### Step 1 - Initialize Solver and Solve
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Invoke `solver.Solve()` to obtain the solution status.

### Step 2 - Check Solver Status and Extract Solution
- Check the solver result: `status = solver.Solve()`.
- If `status` is `solver.OPTIMAL` or `solver.FEASIBLE`, proceed to extract the objective value and variable values.
- Extract the objective value: `solver.Objective().Value()`.

### Step 3 - Validate Solution and Output
- Verify all supply and demand constraints are satisfied within a numerical tolerance (e.g., `abs(actual - required) < 1e-10`).
- Print key metrics: total cost, total flow from each origin, total flow to each destination.
- Optionally, cross-verify with another solver (e.g., CBC) for numerical stability.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (Create variables, constraints, objective as per modeling steps)
# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL or status == solver.FEASIBLE:
    objective_value = solver.Objective().Value()
    # Extract and validate flows
    for i in origins:
        total_flow = sum(solver.LookupVariable(f'x_{i}_{j}').solution_value() for j in destinations)
        # Validate against supply[i]
else:
    # Handle solver failure
    print('Solver did not find an optimal solution.')
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid solutions.
- Assuming solver infeasibility without first verifying problem balance.
- Neglecting to validate constraint satisfaction post-solution, leading to acceptance of numerically unstable results.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling syntax, creating a structured, solver-agnostic representation. This approach is ideal for integration into larger optimization pipelines and for use with open-source solvers like HiGHS or CBC.

### Step 1 - Define Pyomo Sets and Parameters
- Declare Pyomo `Set` objects: `model.I` for origins and `model.J` for destinations.
- Declare Pyomo `Param` objects: `model.supply` indexed by `I`, `model.demand` indexed by `J`, and `model.cost` indexed by `I x J`.
- Initialize parameters from data dictionaries for clarity.

### Step 2 - Declare Decision Variables
- Create a Pyomo `Var`: `model.x` indexed by `I` and `J`, with domain `pyo.NonNegativeReals`.

### Step 3 - Formulate Constraints with Pyomo Rules
- Define a `Constraint` for supply: `model.supply_con = pyo.Constraint(model.I, rule=lambda m, i: sum(m.x[i,j] for j in m.J) == m.supply[i])`.
- Define a `Constraint` for demand: `model.demand_con = pyo.Constraint(model.J, rule=lambda m, j: sum(m.x[i,j] for i in m.I) == m.demand[j])`.

### Step 4 - Define the Objective Function
- Create an `Objective`: `model.obj = pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for i in model.I for j in model.J), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["I (origins)", "J (destinations)"],
  "parameters": ["supply[i]", "demand[j]", "cost[i][j]"],
  "decision_variables": ["x[i,j] in NonNegativeReals"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "sum_{j in J} x[i,j] == supply[i], for all i in I",
    "sum_{i in I} x[i,j] == demand[j], for all j in J"
  ]
}
```

### Common Pitfalls
- Using mutable data structures (like lists) directly in Pyomo rule functions, which can lead to unexpected behavior.
- Not pre-checking problem balance, causing the solver to report infeasibility.
- Creating the model with unbalanced data without implementing a dummy node strategy.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., HiGHS or CBC). Configure solver options for performance and implement comprehensive checks on solver status and termination condition.

### Step 1 - Configure and Execute Solver
- Create a solver instance: `solver = pyo.SolverFactory('highs')` (or `'cbc'`).
- Set practical options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`.
- Solve the model: `results = solver.solve(model, tee=False)`.

### Step 2 - Implement Robust Solution Checking
- Check solver status: `results.solver.status` should be `SolverStatus.ok`.
- Check termination condition: `results.solver.termination_condition` should be `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If checks pass, extract the objective value: `float(pyo.value(model.obj))`.

### Step 3 - Validate and Extract Solution Details
- Post-solution, validate that all supply and demand constraints are satisfied within tolerance (e.g., `abs(value - target) < 1e-6`).
- Extract individual flow values: `pyo.value(model.x[i,j])`.
- Filter and report non-zero flows using a threshold (e.g., `> 1e-6`).

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=origins)
model.J = pyo.Set(initialize=destinations)
# ... (Define parameters, variables, constraints, objective as per modeling steps)
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    objective_value = float(pyo.value(model.obj))
    # Extract and validate solution
else:
    # Handle solver failure
    print('Solver did not converge to an optimal or feasible solution.')
```

### Common Pitfalls
- Confusing solver status with termination condition; both must be checked for a valid solution.
- Not setting a time limit for large instances, potentially causing the solve to hang.
- Failing to handle edge cases like degenerate solutions, where multiple flow patterns yield the same objective value.
