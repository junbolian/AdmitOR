---
name: Facility Location MILP Skill
description: |
  Model and solve capacitated facility location problems as mixed-integer linear programs, handling fixed and variable costs with capacity-demand linking.
---

# Workflow 1 (Pyomo with Commercial/Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to create a portable MILP formulation, which can be interfaced with various solvers via SolverFactory.

### Step 1 - Define Sets and Parameters
- Define index sets for facilities and customers as Python lists or sets.
- Organize parameters (fixed costs, capacities, demands, variable costs) as dictionaries keyed by these indices for clarity and scalability.
- For incomplete or synthetic data, generate deterministic approximations (e.g., `base_cost + (i*factor + j) % mod`) to ensure reproducibility.

### Step 2 - Create Decision Variables
- Create binary variables `y[i]` for facility opening decisions (`domain=pyo.Binary`).
- Create continuous, non-negative variables `x[i,j]` for allocation amounts from facility `i` to customer `j` (`domain=pyo.NonNegativeReals`).

### Step 3 - Formulate Objective and Constraints
- Formulate the objective to minimize total cost: sum of `fixed_cost[i] * y[i]` plus sum of `variable_cost[i,j] * x[i,j]`.
- Add demand satisfaction constraints: for each customer `j`, sum of `x[i,j]` over all facilities must equal `demand[j]`.
- Add capacity-linking constraints: for each facility `i`, sum of `x[i,j]` over all customers must be less than or equal to `capacity[i] * y[i]`. This enforces that no allocation occurs from a closed facility.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": {
    "fixed_cost": {"index": "facilities"},
    "capacity": {"index": "facilities"},
    "demand": {"index": "customers"},
    "variable_cost": {"index": ["facilities", "customers"]}
  },
  "decision_variables": {
    "y": {"index": "facilities", "type": "binary"},
    "x": {"index": ["facilities", "customers"], "type": "continuous", "lb": 0}
  },
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i] for i in facilities) + sum(variable_cost[i,j] * x[i,j] for i in facilities for j in customers)"
  },
  "constraints": {
    "demand_satisfaction": {"index": "customers", "expression": "sum(x[i,j] for i in facilities) == demand[j]"},
    "capacity_linking": {"index": "facilities", "expression": "sum(x[i,j] for j in customers) <= capacity[i] * y[i]"}
  }
}
```

### Common Pitfalls
- Forgetting to link the capacity constraint to the binary variable, allowing allocation from closed facilities.
- Using an invalid optimality gap (e.g., negative value) in solver options.
- Not validating that total potential capacity (if all facilities open) meets total demand before solving, which guarantees infeasibility.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver instance, with careful handling of solver status, solution loading, and result extraction for analysis.

### Step 1 - Configure and Execute Solver
- Instantiate the solver via `SolverFactory("solver_name")` (e.g., "gurobi", "cbc", "highs").
- Set key options: time limit, optimality gap (MIPGap/ratioGap/mip_rel_gap), thread count, and random seed for reproducibility.
- Call `solver.solve(model, ...)` and capture the results object.

### Step 2 - Validate Solution Status and Load Results
- Check the solver termination condition (`results.solver.termination_condition`) and status (`results.solver.status`).
- Proceed only if status is `SolverStatus.ok` and termination is `optimal` or `feasible`.
- Use `model.solutions.load_from(results)` if solutions are not loaded automatically.

### Step 3 - Extract and Analyze Solution
- Extract facility openings: `y[i].value > 0.5` indicates an open facility.
- Extract allocation flows: `x[i,j].value`.
- Compute cost breakdowns: total fixed cost and total variable cost from variable values and parameters, verifying they sum to the reported objective value.
- Report key metrics: objective value, number of open facilities, capacity utilization, and demand coverage.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (following formulation steps)
model = pyo.ConcreteModel()
model.F = pyo.Set(initialize=facilities)
model.C = pyo.Set(initialize=customers)
# ... (define parameters, variables, constraints, objective)

# Solve with status / termination checks
solver = pyo.SolverFactory("gurobi")  # or "cbc", "highs"
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = -1e-4  # Use 0.0 for exact optimality
solver.options["Threads"] = 4
solver.options["Seed"] = 42

results = solver.solve(model, tee=False)  # tee=True for solver log

# Check status
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    # Load solution if needed
    # model.solutions.load_from(results)
    # Extract and analyze solution
    total_cost = pyo.value(model.obj)
    open_facs = [i for i in model.F if pyo.value(model.y[i]) > 0.5]
    # ... further analysis
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming the solution is loaded automatically; some solver interfaces require explicit `load_from`.
- Not checking both solver status and termination condition, leading to errors when extracting from infeasible or unbounded models.
- Mis-mapping solver option names between different backends (e.g., `MIPGap` vs `ratioGap`).

# Workflow 2 (OR-Tools CP-SAT / SCIP Backend)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver (or SCIP backend) with an imperative, programmatic API to build the model constraint-by-constraint, suitable for direct integration and deployment.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")` or `"CP-SAT"`.
- Store parameters in native Python data structures (lists, dicts) indexed by facility and customer IDs.

### Step 2 - Create Variables Imperatively
- Create binary variables for facility opening: `y[i] = solver.IntVar(0, 1, f"y_{i}")`.
- Create continuous allocation variables: `x[i,j] = solver.NumVar(0, solver.infinity(), f"x_{i}_{j}")`. For CP-SAT, use `solver.IntVar(0, large_number, ...)` if continuous variables are not supported and discretization is acceptable.

### Step 3 - Add Constraints Directly
- For each customer `j`, add a demand constraint: `solver.Add(sum(x[i,j] for i in facilities) == demand[j])`.
- For each facility `i`, add a capacity-linking constraint: `solver.Add(sum(x[i,j] for j in customers) <= capacity[i] * y[i])`.
- Optionally, add stronger individual linking constraints `x[i,j] <= demand[j] * y[i]` for each `i,j` to improve LP relaxation.

### Step 4 - Define the Objective Function
- Create an objective expression: `total_cost = sum(fixed_cost[i] * y[i] for i in facilities) + sum(variable_cost[i,j] * x[i,j] for i in facilities for j in customers)`.
- Assign it to the solver: `solver.Minimize(total_cost)` or build incrementally via `objective = solver.Objective()` and `SetCoefficient`.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": {
    "fixed_cost": {"index": "facilities"},
    "capacity": {"index": "facilities"},
    "demand": {"index": "customers"},
    "variable_cost": {"index": ["facilities", "customers"]}
  },
  "decision_variables": {
    "y": {"index": "facilities", "type": "binary"},
    "x": {"index": ["facilities", "customers"], "type": "continuous", "lb": —}
  },
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i]) + sum(variable_cost[i,j] * x[i,j])"
  },
  "constraints": {
    "demand": {"index": "customers", "expression": "sum(x[i,j] for i in facilities) == demand[j]"},
    "capacity_link": {"index": "facilities", "expression": "sum(x[i,j] for j in customers) <= capacity[i] * y[i]"}
  }
}
```

### Common Pitfalls
- Using CP-SAT solver for purely continuous models; it requires integer variables. Use SCIP backend for full MILP support.
- Forgetting to set a large upper bound for continuous variables when using integer-only solvers, leading to unintended bounds.
- Building the objective as a Python float expression instead of a solver-linear expression, causing errors.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' native solve method, configure performance settings, and extract solution values directly from variable objects.

### Step 1 - Configure Solver Settings
- Set a time limit: `solver.SetTimeLimit(limit_in_milliseconds)`.
- Set the number of threads: `solver.SetNumThreads(num_threads)`.
- For CP-SAT, set additional parameters like `solver.parameters.num_search_workers`.

### Step 2 - Invoke Solver and Check Status
- Call `status = solver.Solve()`.
- Check if `status` is `pywraplp.Solver.OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses appropriately.

### Step 3 - Extract and Verify Solution
- For open facilities: `y[i].solution_value() > 0.5`.
- For allocations: `x[i,j].solution_value()`.
- Recompute total cost from extracted values and compare to `solver.Objective().Value()` for verification.
- Perform sanity checks: demand satisfaction, capacity adherence, and non-negativity.

### Step 4 - (Optional) Enumerate or Explore Alternatives
- To verify optimality or explore near-optimal solutions, add constraints fixing certain `y[i]` variables to specific values and re-solve.
- Use solution callbacks or pool search if supported by the solver.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... create variables, add constraints, set objective

# Solve with status / termination checks
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

status = solver.Solve()

if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    print(f"Objective value: {solver.Objective().Value()}")
    # Extract solution
    open_facilities = []
    for i in facilities:
        if y[i].solution_value() > 0.5:
            open_facilities.append(i)
    # Compute cost breakdown
    total_fixed = sum(fixed_cost[i] * y[i].solution_value() for i in facilities)
    total_variable = sum(variable_cost[i][j] * x[i,j].solution_value() for i in facilities for j in customers)
    print(f"Fixed cost: {total_fixed}, Variable cost: {total_variable}")
else:
    print(f"No solution found. Status: {status}")
```

### Common Pitfalls
- Confusing `solver.Solve()` return status codes between OPTIMAL and FEASIBLE.
- Attempting to access `.solution_value()` on variables before checking solver status, leading to errors.
- Not accounting for solver-specific variable types; CP-SAT requires all variables to be integral.
