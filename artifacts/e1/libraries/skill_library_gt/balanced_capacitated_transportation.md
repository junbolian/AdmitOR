---
name: Balanced Capacitated Transportation
description: |
  Model and solve balanced transportation problems with supply, demand, and per-route capacity constraints using linear programming.

---

# Workflow 1 (OR-Tools LP with Embedded Bounds)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to build a model where per-variable capacity constraints are efficiently handled via variable bounds, and supply/demand are enforced as linear equalities.

### Step 1 - Define Sets and Parameters
- Declare sets for supply nodes (e.g., `supply_nodes`) and demand nodes (e.g., `demand_nodes`).
- Define dictionaries for supply amounts (`supply[i]`), demand amounts (`demand[j]`), unit costs (`cost[i][j]`), and optional per-route capacities (`capacity[i][j]`).

### Step 2 - Create Flow Variables with Bounds
- Instantiate a matrix of non-negative decision variables `x[i][j]` using `solver.NumVar`.
- For each variable, set the lower bound to `0` and the upper bound to `capacity[i][j]` if capacity exists, otherwise to `solver.infinity()`.

### Step 3 - Add Supply and Demand Constraints
- For each supply node `i`, create a linear equality constraint: `sum_{j} x[i][j] = supply[i]`.
- For each demand node `j`, create a linear equality constraint: `sum_{i} x[i][j] = demand[j]`.

### Step 4 - Formulate Linear Cost Objective
- Create an objective expression: `sum_{i} sum_{j} cost[i][j] * x[i][j]`.
- Set the objective to minimization using `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["supply_nodes", "demand_nodes"],
  "parameters": {
    "supply": {"type": "dict", "keys": "supply_nodes"},
    "demand": {"type": "dict", "keys": "demand_nodes"},
    "cost": {"type": "dict", "keys": ["supply_nodes", "demand_nodes"]},
    "capacity": {"type": "dict", "keys": ["supply_nodes", "demand_nodes"], "optional": true}
  },
  "decision_variables": {
    "x": {"type": "continuous", "dimensions": ["supply_nodes", "demand_nodes"], "bounds": ["0", "capacity[i][j] or INF"]}
  },
  "objective": {
    "sense": "min",
    "expression": "sum_{i in supply_nodes} sum_{j in demand_nodes} cost[i][j] * x[i][j]"
  },
  "constraints": [
    {"name": "supply_balance", "expression": "sum_{j in demand_nodes} x[i][j] = supply[i]", "for_all": "i in supply_nodes"},
    {"name": "demand_balance", "expression": "sum_{i in supply_nodes} x[i][j] = demand[j]", "for_all": "j in demand_nodes"}
  ]
}
```

### Common Pitfalls
- Forgetting to verify that total supply equals total demand before building the model, which can lead to infeasibility.
- Setting variable upper bounds to `None` instead of `solver.infinity()` when capacity is unlimited.
- Using exact equality (`==`) for post-solution verification; use a numerical tolerance instead.

## Solving stage

### Strategy Overview
Solve the linear program using the GLOP backend, check solver status, extract the solution, and perform tolerance-based verification of all constraints.

### Step 1 - Instantiate Solver and Set Options
- Create a solver instance with `pywraplp.Solver.CreateSolver('GLOP')`.
- Optionally set time limits or other parameters via `solver.SetTimeLimit()`.

### Step 2 - Solve and Check Status
- Call `solver.Solve()`.
- Verify the result status is `OPTIMAL` or `FEASIBLE` before proceeding.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value via `objective.Value()`.
- Iterate over all variables to get the flow matrix, storing values where `x[i][j].solution_value() > tolerance`.
- Programmatically recompute supply and demand sums from the solution and compare against original parameters within a tolerance (e.g., `1e-6`).

### Step 4 - Output Structured Results
- Print the objective value and a summary of non-zero flows.
- Output a verification report listing any constraint violations.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (build variables, constraints, objective as per modeling stage)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f"Objective value: {solver.Objective().Value()}")
    # Extract and verify solution
    tolerance = 1e-6
    for i in supply_nodes:
        total_flow = sum(x[i, j].solution_value() for j in demand_nodes)
        if abs(total_flow - supply[i]) > tolerance:
            print(f"Warning: Supply constraint violation for {i}")
    # ... similar verification for demand constraints
else:
    print("No optimal or feasible solution found.")
```

### Common Pitfalls
- Assuming the solver status `FEASIBLE` implies optimality; check for `OPTIMAL` if the exact optimum is required.
- Not using a tolerance when checking constraint satisfaction, leading to false failures due to floating-point arithmetic.
- Omitting post-solution verification, which can mask model-building errors or solver issues.

# Workflow 2 (Pyomo with Explicit Constraint-Based Capacity)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to construct an abstract model where all constraints, including capacities, are explicitly defined as model components, offering flexibility for extensions and integration with a wide range of solvers.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `supply_nodes` and `demand_nodes`.
- Define `Param` components for `supply`, `demand`, `cost`, and `capacity` (with a default high value for uncapacitated arcs).

### Step 2 - Declare Flow Variables
- Create a `Var` component `model.x` indexed over `(supply_nodes, demand_nodes)` with `domain=pyo.NonNegativeReals`.

### Step 3 - Formulate All Constraints Explicitly
- Add a `Constraint` component for supply balance: `sum(model.x[i, j] for j in demand_nodes) == supply[i]`.
- Add a `Constraint` component for demand balance: `sum(model.x[i, j] for i in supply_nodes) == demand[j]`.
- Add a `Constraint` component for per-route capacities: `model.x[i, j] <= capacity[i, j]`.

### Step 4 - Define the Objective Function
- Create an `Objective` rule: `sum(cost[i, j] * model.x[i, j] for i in supply_nodes for j in demand_nodes)` and set `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["supply_nodes", "demand_nodes"],
  "parameters": {
    "supply": {"type": "param", "indexed_by": "supply_nodes"},
    "demand": {"type": "param", "indexed_by": "demand_nodes"},
    "cost": {"type": "param", "indexed_by": ["supply_nodes", "demand_nodes"]},
    "capacity": {"type": "param", "indexed_by": ["supply_nodes", "demand_nodes"], "default": "INF"}
  },
  "decision_variables": {
    "x": {"type": "continuous", "domain": "NonNegativeReals", "dimensions": ["supply_nodes", "demand_nodes"]}
  },
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in supply_nodes for j in demand_nodes)"
  },
  "constraints": [
    {"name": "supply_balance", "expression": "sum(x[i, j] for j in demand_nodes) == supply[i]", "for_all": "i in supply_nodes"},
    {"name": "demand_balance", "expression": "sum(x[i, j] for i in supply_nodes) == demand[j]", "for_all": "j in demand_nodes"},
    {"name": "route_capacity", "expression": "x[i, j] <= capacity[i, j]", "for_all": ["i in supply_nodes", "j in demand_nodes"]}
  ]
}
```

### Common Pitfalls
- Forgetting to initialize all parameters before instantiating the model, which can cause runtime errors.
- Using Python's built-in `sum` inside Pyomo rule functions instead of the `pyo.summation` function or generator expressions; while often acceptable, it can lead to performance issues in large models.
- Not providing a default value for the `capacity` parameter, making the model require data for every possible arc.

## Solving stage

### Strategy Overview
Instantiate a solver factory (e.g., for CBC or HiGHS), configure performance options, solve with careful status checking, and implement a robust two-phase solve-then-verify process.

### Step 1 - Select and Configure Solver
- Create a solver object using `pyo.SolverFactory('solver_name')` (e.g., `'cbc'` or `'appsi_highs'`).
- Set options such as time limit (`seconds`), optimality gap tolerance (`ratio`), and number of threads (`threads`).

### Step 2 - Solve with Status Control
- Execute `results = solver.solve(model, tee=False, load_solutions=False)` to avoid automatically loading an invalid solution.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Load and Extract Solution
- If the status is acceptable, load the solution into the model with `model.solutions.load_from(results)`.
- Extract the objective value via `pyo.value(model.obj)`.

### Step 4 - Perform Comprehensive Verification
- Iterate over all constraints to verify satisfaction within tolerance (e.g., `1e-6`).
- Iterate over variables to list all non-zero flows (above a tolerance).
- Print a summary of any violations.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, params, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = -1.0  # Use default optimality gap
results = solver.solve(model, tee=False, load_solutions=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    model.solutions.load_from(results)
    print(f"Objective value: {pyo.value(model.obj)}")
    # Verification loop
    tolerance = 1e-6
    for constr in model.component_objects(pyo.Constraint, active=True):
        # ... check each constraint body vs. bounds
else:
    print("Solver did not return a successful status.")
```

### Common Pitfalls
- Loading the solution automatically (`load_solutions=True`) without checking termination condition, potentially loading an infeasible or suboptimal point.
- Not using a tolerance when checking constraint satisfaction in verification loops.
- Assuming solver availability; always implement a fallback or check for installed solvers at runtime.
