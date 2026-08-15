---
name: Fixed-Charge Network Flow Modeling and Solving
description: |
  Model and solve supply chain or network design problems with fixed connection costs and variable flow costs using mixed-integer linear programming.
---

# Workflow 1 (Pyomo with Commercial/Open-Source MILP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling language to create a portable MILP formulation, which can be solved by various backends like Gurobi or HiGHS. It emphasizes clean separation of model and data, robust parameter handling, and solver-agnostic construction.

### Step 1 - Define Sets and Parameters
- Define a set of nodes `N` and a set of directed arcs `A` (e.g., as a list of tuples `(i, j)`).
- Create parameter dictionaries for node supply/demand (`supply[i]`), arc capacity (`capacity[i,j]`), fixed connection cost (`fixed_cost[i,j]`), and variable flow cost (`var_cost[i,j]`). Use `pyo.Param` for immutable data.

### Step 2 - Create Decision Variables
- Define binary variables `y[i,j]` for arc activation (`pyo.Var(domain=pyo.Binary)`).
- Define continuous, non-negative variables `x[i,j]` for flow amounts (`pyo.Var(domain=pyo.NonNegativeReals)`).

### Step 3 - Formulate Flow Conservation Constraints
- For each node `i` in `N`, create a constraint: `sum(x[i,j] for j if (i,j) in A) - sum(x[j,i] for j if (j,i) in A) == supply[i]`. Precompute incoming/outgoing arc lists for efficiency and clarity.

### Step 4 - Link Activation and Flow with Big-M
- For each arc `(i,j)` in `A`, add the constraint `x[i,j] <= capacity[i,j] * y[i,j]`. This enforces that flow is zero if the connection is not established and respects capacity limits.

### Step 5 - Define the Objective Function
- Construct the objective to minimize total cost: `sum(fixed_cost[i,j] * y[i,j] for (i,j) in A) + sum(var_cost[i,j] * x[i,j] for (i,j) in A)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of nodes"},
    {"name": "A", "description": "Set of directed arcs (i,j)"}
  ],
  "parameters": [
    {"name": "supply", "index": "N", "description": "Net supply at node (positive for source, negative for sink)"},
    {"name": "capacity", "index": "A", "description": "Maximum flow allowed on arc"},
    {"name": "fixed_cost", "index": "A", "description": "Cost incurred if arc is activated"},
    {"name": "var_cost", "index": "A", "description": "Cost per unit of flow on arc"}
  ],
  "decision_variables": [
    {"name": "y", "index": "A", "type": "binary", "description": "1 if arc is activated, 0 otherwise"},
    {"name": "x", "index": "A", "type": "continuous_nonnegative", "description": "Amount of flow on arc"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i,j] * y[i,j]) + sum(var_cost[i,j] * x[i,j])"
  },
  "constraints": [
    {"name": "flow_conservation", "index": "N", "expression": "sum_outflow(i) - sum_inflow(i) = supply[i]"},
    {"name": "activation_logic", "index": "A", "expression": "x[i,j] <= capacity[i,j] * y[i,j]"}
  ]
}
```

### Common Pitfalls
- Incorrectly signing flow conservation (inflow - outflow vs. outflow - inflow). Always validate with a simple test case.
- Using an excessively large big-M value (like an arbitrary large number) instead of the natural `capacity` parameter, which weakens the formulation.
- Forgetting to precompute arc indices for inflow/outflow sums, leading to inefficient constraint building or key errors.

## Solving stage

### Strategy Overview
This solving stage focuses on using Pyomo's `SolverFactory` interface with configurable options for commercial (Gurobi) or open-source (HiGHS) MILP solvers. It emphasizes rigorous solution status checking, parameter tuning for performance, and post-solution validation.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory("solver_name")` (e.g., "gurobi", "highs").
- Set solver options: `solver.options['MIPGap'] = 0.0` (or `'mip_rel_gap'`), `solver.options['TimeLimit'] = time_limit`, `solver.options['Threads'] = num_threads`, `solver.options['Seed'] = seed` for reproducibility.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=True)` to solve and optionally print logs.
- Check `pyo.SolverStatus.ok` and `pyo.TerminationCondition.optimal` (or `.feasible`) before proceeding. Handle infeasible or error statuses with structured output.

### Step 3 - Extract and Validate Solution
- Extract active arcs where `pyo.value(model.y[i,j]) > 0.5` and flow values `pyo.value(model.x[i,j])`.
- Recompute total fixed and variable costs from extracted values to verify against the solver's objective value.
- Re-evaluate flow conservation constraints using solution flows to ensure numerical feasibility within a tolerance.

### Step 4 - Report and Analyze
- Print or return key solution components: list of activated arcs, flow amounts, and cost breakdown.
- For advanced validation, consider resolving with tighter optimality tolerances or different random seeds to confirm solution stability.

### Code Usage
```python
import pyomo.environ as pyo

# Assume `model` is a Pyomo ConcreteModel built per the modeling stage
solver = pyo.SolverFactory("gurobi")  # or "highs"
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 300
solver.options['Threads'] = 4

results = solver.solve(model, tee=False)

status = results.solver.status
termination = results.solver.termination_condition

if status == pyo.SolverStatus.ok and termination in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    # Extract solution
    active_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.y[i,j]) > 0.5]
    flows = {(i,j): pyo.value(model.x[i,j]) for (i,j) in model.A}
    # ... validation and reporting
else:
    # Handle failure
    output = {"status": "failed", "reason": f"solver status: {status}, termination: {termination}"}
```

### Common Pitfalls
- Not checking both solver status *and* termination condition, leading to extraction attempts from failed solves.
- Extracting variable values without first ensuring the solution is available (`pyo.value` may fail).
- Using solver-specific option names incorrectly (e.g., `'MIPGap'` for Gurobi vs. `'mip_rel_gap'` for HiGHS).

# Workflow 2 (Native Solver API - OR-Tools/SCIP)

## Modeling stage

### Strategy Overview
This workflow uses a solver-native API (e.g., OR-Tools, direct SCIP) to build the model directly within the solver's environment. It is suited for performance-critical applications or embedding within larger systems, offering fine-grained control over the solving process.

### Step 1 - Initialize Solver and Create Variable Arrays
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Create dictionaries to hold variable objects: binary `y[i,j] = solver.BoolVar('y_i_j')` and continuous `x[i,j] = solver.NumVar(0.0, capacity[i,j], 'x_i_j')`. Setting the upper bound to `capacity[i,j]` during creation is an initial bound.

### Step 2 - Build Flow Conservation Constraints
- For each node `i`, create a constraint object: `ct = solver.Constraint(demand[i], demand[i])`.
- Add coefficients for all outgoing flows (`x[i,j]`) with `+1` and incoming flows (`x[j,i]`) with `-1` to the constraint using `ct.SetCoefficient`.

### Step 3 - Enforce Activation-Flow Coupling
- For each arc `(i,j)`, add a linear constraint: `x[i,j] <= capacity[i,j] * y[i,j]`. This is implemented as `solver.Add(x[i,j] - capacity[i,j] * y[i,j] <= 0)`.

### Step 4 - Set the Objective Function
- Initialize the objective: `objective = solver.Objective()`.
- Set coefficients: `objective.SetCoefficient(y[i,j], fixed_cost[i,j])` and `objective.SetCoefficient(x[i,j], var_cost[i,j])` for all arcs.
- Set the objective sense to minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of nodes"},
    {"name": "A", "description": "Set of directed arcs (i,j)"}
  ],
  "parameters": [
    {"name": "demand", "index": "N", "description": "Net demand at node (negative for supply)"},
    {"name": "capacity", "index": "A", "description": "Maximum flow allowed on arc"},
    {"name": "fixed_cost", "index": "A", "description": "Cost incurred if arc is activated"},
    {"name": "var_cost", "index": "A", "description": "Cost per unit of flow on arc"}
  ],
  "decision_variables": [
    {"name": "y", "index": "A", "type": "binary", "description": "1 if arc is activated, 0 otherwise"},
    {"name": "x", "index": "A", "type": "continuous_nonnegative", "description": "Amount of flow on arc"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i,j] * y[i,j]) + sum(var_cost[i,j] * x[i,j])"
  },
  "constraints": [
    {"name": "flow_conservation", "index": "N", "expression": "sum_outflow(i) - sum_inflow(i) = demand[i]"},
    {"name": "activation_logic", "index": "A", "expression": "x[i,j] <= capacity[i,j] * y[i,j]"}
  ]
}
```

### Common Pitfalls
- Incorrectly setting variable bounds: `x[i,j]` should be bounded by `capacity[i,j]` for performance, but the activation constraint is still required.
- Adding coefficients to constraints in the wrong order or sign, especially for flow conservation.
- Not using unique names for variables, which can complicate debugging and solution extraction.

## Solving stage

### Strategy Overview
This stage involves configuring the native solver, executing the solve, and directly interrogating the solver's result objects. It provides low-level control over the solving process and immediate access to solution values.

### Step 1 - Configure Solver Parameters
- Set solver-specific parameters: `solver.SetTimeLimit(time_limit_ms)`, `solver.SetNumThreads(num_threads)`, and optimality tolerances if available (e.g., `solver.SetSolverSpecificParametersAsString`).

### Step 2 - Execute Solve and Check Result
- Call `status = solver.Solve()`.
- Check the result status: `if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE`. Handle other statuses (INFEASIBLE, UNBOUNDED) appropriately.

### Step 3 - Extract Solution Values
- For each arc, retrieve the solution: `y_val = y[i,j].solution_value()`, `x_val = x[i,j].solution_value()`.
- Identify active connections where `y_val > 0.5` and positive flows where `x_val > tolerance`.

### Step 4 - Post-Solution Validation and Reporting
- Recompute node balances from extracted flows to verify demand satisfaction.
- Calculate the objective value from extracted variable values and compare with `solver.Objective().Value()`.
- Generate a summary report of selected arcs, flows, and cost breakdown.

### Code Usage
```python
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(300000)  # milliseconds
solver.SetNumThreads(4)

# Assume variables `y`, `x` and model are built per the modeling stage
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    active_arcs = []
    total_fixed_cost = 0.0
    for (i,j) in A:
        if y[i,j].solution_value() > 0.5:
            active_arcs.append((i,j))
            total_fixed_cost += fixed_cost[i,j] * y[i,j].solution_value()
    # ... further extraction and validation
else:
    # Handle failure
    output = {"status": "failed", "reason": f"solver status code: {status}"}
```

### Common Pitfalls
- Confusing the solver's status codes (OPTIMAL vs. FEASIBLE) and not handling both.
- Not using a tolerance (e.g., `1e-5`) when checking continuous flow values or binary variable values for activity.
- Forgetting to convert time limits to the correct units (e.g., milliseconds for OR-Tools).
