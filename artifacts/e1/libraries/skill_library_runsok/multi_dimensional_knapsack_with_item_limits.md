---
name: Multi-Dimensional Knapsack with Item Limits
description: |
  Model and solve integer linear programs where items with individual demand limits consume multiple shared resources, maximizing linear profit subject to per-resource capacity constraints.
---

# Workflow 1 (OR-Tools / SCIP Backend)

## Modeling stage

### Strategy Overview
This workflow models the problem using Google OR-Tools' linear solver wrapper, leveraging its efficient C++ backends (SCIP, CBC) and explicit variable/constraint construction API. It emphasizes direct variable bounding and sparse constraint building.

### Step 1 - Define Data Structures
- Represent items and resources as indexed sets (e.g., lists or ranges).
- Store per-item profit, demand limit (upper bound), and per-resource capacity as dictionaries or lists.
- Encode resource consumption sparsely: for each resource, maintain a list of items that consume it.

### Step 2 - Create Integer Variables with Bounds
- Instantiate a `solver` object (e.g., `pywraplp.Solver.CreateSolver('SCIP')`).
- For each item, create an integer decision variable `x[i]` with lower bound 0 and upper bound equal to its demand limit, directly enforcing the per-item constraint.

### Step 3 - Build Capacity Constraints
- For each resource, create a linear constraint with upper bound equal to its capacity.
- Iterate over the list of items consuming that resource, setting each variable's coefficient to 1 in the constraint.

### Step 4 - Set Linear Objective
- Define the objective as the sum of `profit[i] * x[i]` across all items.
- Set the objective sense to maximization.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "R: set of resources"
  ],
  "parameters": [
    "profit_i: profit per unit of item i ∈ I",
    "demand_i: maximum units of item i ∈ I",
    "capacity_r: capacity of resource r ∈ R",
    "consumes_ir: 1 if item i uses resource r, else 0 (or list of items per resource)"
  ],
  "decision_variables": [
    "x_i: integer, units selected of item i ∈ I, 0 ≤ x_i ≤ demand_i"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in I} profit_i * x_i"
  },
  "constraints": [
    "capacity_r: sum_{i in I} consumes_ir * x_i ≤ capacity_r, for each r ∈ R"
  ]
}
```

### Common Pitfalls
- Forgetting to set variable upper bounds, leading to unbounded or unrealistic solutions.
- Building dense constraint matrices for large, sparse problems, causing memory bloat.
- Using floating-point coefficients for unit consumption, which can introduce numerical issues; prefer integer coefficients (1).

## Solving stage

### Strategy Overview
This stage configures the OR-Tools solver, executes the model, rigorously checks the solution status and feasibility, and extracts detailed results including binding constraints and utilization metrics.

### Step 1 - Configure Solver Parameters
- Set a time limit appropriate for problem size using `solver.SetTimeLimit(ms)`.
- Configure parallel threads with `solver.SetNumThreads(n)` for performance.
- Optionally set relative MIP gap to zero for exact optimality: `solver.params.mip_gap = 0.0`.

### Step 2 - Solve and Check Status
- Call `solver.Solve()` and capture the result status.
- Accept statuses `OPTIMAL` or `FEASIBLE`. Treat `UNBOUNDED` or `INFEASIBLE` as failures requiring model review.

### Step 3 - Validate Solution Feasibility
- Extract variable values and compute actual resource consumption per constraint.
- Verify each capacity constraint is satisfied within a small tolerance (e.g., 1e-6).
- Verify each variable does not exceed its demand limit.

### Step 4 - Extract and Report Results
- Retrieve the objective value and all variable values.
- Calculate resource utilization percentages and identify binding constraints (where slack ≈ 0).
- Output a structured result including the optimal value, key decisions, and bottleneck analysis.

### Code Usage
```python
# Import and create solver
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (build model as per modeling stage)

# Configure solver
solver.SetTimeLimit(30000)  # 30 seconds
solver.SetNumThreads(4)

# Solve
status = solver.Solve()

# Check status and extract results
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    solution = {i: x[i].solution_value() for i in items}
    # Validate and report
    print(f"RESULT:{objective_value}")
else:
    print("Solve failed or no solution found.")
```

### Common Pitfalls
- Not checking solver status, leading to errors when accessing solution values from failed solves.
- Ignoring numerical tolerances in feasibility checks, causing false constraint violations.
- Omitting resource utilization analysis, missing insights into limiting factors.

# Workflow 2 (Pyomo / Highs Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a ConcreteModel with Sets, Variables, Objective, and Constraints, then solves it with the open-source Highs MILP solver. It is well-suited for clear, declarative model definitions and integration with the Pyomo ecosystem.

### Step 1 - Declare Sets and Parameters
- Define Pyomo Sets for items and resources.
- Initialize Pyomo Params for profits, demand limits, capacities, and a binary consumption matrix.

### Step 2 - Define Integer Decision Variables
- Create a Pyomo Variable `model.x` indexed over items, with domain `pyo.NonNegativeIntegers`.
- Apply upper bounds via constraints or directly within variable definition if supported.

### Step 3 - Formulate Capacity Constraints
- For each resource, create a constraint summing `consumes[(i, r)] * model.x[i]` over all items, less than or equal to the resource's capacity.

### Step 4 - Formulate Demand Constraints
- For each item, add a simple upper bound constraint: `model.x[i] <= demand[i]`.

### Step 5 - Set Linear Maximization Objective
- Define the objective as the sum of `profit[i] * model.x[i]` and set sense to maximize.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "R: set of resources"
  ],
  "parameters": [
    "profit: I → profit per unit",
    "demand: I → maximum units",
    "capacity: R → resource capacity",
    "consumes: I × R → binary consumption indicator"
  ],
  "decision_variables": [
    "x_i: NonNegativeInteger, units selected of item i ∈ I"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in I} profit[i] * x_i"
  },
  "constraints": [
    "demand_i: x_i ≤ demand[i], for each i ∈ I",
    "capacity_r: sum_{i in I} consumes[(i, r)] * x_i ≤ capacity[r], for each r ∈ R"
  ]
}
```

### Common Pitfalls
- Defining the consumption matrix as a dense Param for large problems, impacting memory; use sparse data initialization.
- Confusing Pyomo Set initialization order, causing uninitialized indices in constraints.
- Applying demand limits as variable bounds instead of constraints, which may not be supported by all solvers via Pyomo.

## Solving stage

### Strategy Overview
This stage uses Pyomo's `SolverFactory` to interface with the Highs solver, configures it for exact MIP solving, performs rigorous solution status and feasibility checks, and enables post-solve validation and analysis.

### Step 1 - Instantiate and Configure Solver
- Create a solver object: `solver = pyo.SolverFactory('highs')`.
- Set options: `time_limit` (seconds), `mip_rel_gap=0.0`, and `threads` for parallelism.

### Step 2 - Solve and Inspect Termination
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Extract and Validate Solution
- Load variable values into a dictionary using `pyo.value(model.x[i])`.
- Programmatically recompute objective value and constraint slacks to validate correctness within tolerance.

### Step 4 - Perform Post-Solve Analysis
- Identify binding capacity constraints (slack ≈ 0) to pinpoint bottleneck resources.
- Calculate utilization percentages for all resources.
- Optionally, perform sensitivity tests by fixing variables to explore trade-offs.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (as per modeling stage)
model = pyo.ConcreteModel()
# ... define sets, params, variables, objective, constraints

# Solve
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)

# Check status and extract
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    solution = {i: pyo.value(model.x[i]) for i in model.I}
    obj_val = pyo.value(model.obj)
    print(f"RESULT:{obj_val}")
else:
    print(f"Solver terminated with status: {status}, condition: {term}")
```

### Common Pitfalls
- Not importing `SolverStatus` and `TerminationCondition`, leading to opaque status checks.
- Assuming `optimal` termination is guaranteed; always handle `feasible` or other conditions gracefully.
- Neglecting to load solution values into the model instance before accessing them with `pyo.value`.
