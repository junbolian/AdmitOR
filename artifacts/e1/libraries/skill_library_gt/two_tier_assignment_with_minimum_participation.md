---
name: Two-Tier Assignment with Minimum Participation
description: |
  Model and solve assignment problems with continuous allocation and binary participation decisions, linking them via logical constraints to enforce minimum flows and participant counts.

---

# Workflow 1 (MILP with Explicit Big-M)

## Modeling stage

### Strategy Overview
This workflow uses a classic Mixed-Integer Linear Programming (MILP) formulation with explicit Big-M constraints to link binary selection and continuous flow variables, providing clear control over the logical relationship.

### Step 1 - Define Core Variables
- Create a continuous, non-negative variable `x[i][j]` for the quantity assigned from source `i` to sink `j`.
- Create a binary variable `y[i][j]` to indicate whether source `i` is selected to serve sink `j`.

### Step 2 - Implement Source and Sink Constraints
- **Capacity Limit**: For each source `i`, sum of outgoing flows must not exceed its capacity: `sum_j x[i][j] <= capacity[i]`.
- **Demand Satisfaction**: For each sink `j`, sum of incoming flows must meet or exceed its demand: `sum_i x[i][j] >= demand[j]`.
- **Minimum Participation Count**: For each sink `j`, enforce a minimum number of active sources: `sum_i y[i][j] >= min_participants[j]`.

### Step 3 - Link Variables with Logical Constraints
- **Minimum Assignment if Selected**: If a source is selected for a sink, the flow must be at least a minimum amount: `x[i][j] >= min_flow[i][j] * y[i][j]`.
- **Producer-Contract Assignment (Big-M)**: Flow can only occur if the source is selected: `x[i][j] <= M[i][j] * y[i][j]`. Set `M[i][j]` to a tight upper bound, such as `min(capacity[i], demand[j])`.

### Step 4 - Formulate Linear Objective
- Define the objective to minimize total linear cost: `minimize sum_i sum_j cost[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "sinks"
  ],
  "parameters": [
    "capacity[sources]",
    "demand[sinks]",
    "cost[sources][sinks]",
    "min_flow[sources][sinks]",
    "min_participants[sinks]",
    "M[sources][sinks]"
  ],
  "decision_variables": [
    "x[sources][sinks] >= 0",
    "y[sources][sinks] in {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in sources} sum_{j in sinks} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "capacity_limit[i in sources]: sum_{j in sinks} x[i][j] <= capacity[i]",
    "demand_satisfaction[j in sinks]: sum_{i in sources} x[i][j] >= demand[j]",
    "minimum_participation_count[j in sinks]: sum_{i in sources} y[i][j] >= min_participants[j]",
    "minimum_assignment_if_selected[i in sources][j in sinks]: x[i][j] >= min_flow[i][j] * y[i][j]",
    "producer_contract_assignment[i in sources][j in sinks]: x[i][j] <= M[i][j] * y[i][j]"
  ]
}
```

### Common Pitfalls
- Using an excessively large, non-tight `M` value, which weakens the LP relaxation and slows solver convergence.
- Forgetting to enforce the `minimum_participation_count` constraint, leading to solutions with insufficient active sources per sink.
- Not validating that `min_flow[i][j]` is less than or equal to the chosen `M[i][j]` to avoid creating infeasible constraints.

## Solving stage

### Strategy Overview
Solve the MILP model using a dedicated solver via a low-level API (e.g., OR-Tools, PuLP). Focus on explicit solver configuration, status checking, and post-solution verification.

### Step 1 - Initialize Solver and Build Model
- Instantiate a MILP solver (e.g., `SCIP`, `CBC`).
- Programmatically create variables and constraints according to the formulation template.

### Step 2 - Configure Solver Parameters
- Set a time limit to prevent excessive runtime: `solver.SetTimeLimit(timeout_ms)`.
- Optionally set a relative optimality gap tolerance: `solver.SetRelativeGapTolerance(mip_gap)`.
- Configure the number of threads for parallel processing if supported.

### Step 3 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the returned status against `OPTIMAL` and `FEASIBLE` codes. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error messages.

### Step 4 - Extract and Verify Solution
- If the solve was successful, retrieve the objective value and variable solutions.
- Programmatically verify all constraints are satisfied within a small numerical tolerance (e.g., 1e-6) to ensure model fidelity.

### Code Usage
```python
# build model from formulation
import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... create variables x, y from data ...
# ... add all constraints ...
# ... set objective ...

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    # Extract solution values
    solution_x = {(i,j): x[i][j].solution_value() for i in sources for j in sinks}
    solution_y = {(i,j): y[i][j].solution_value() for i in sources for j in sinks}
    # Add verification logic here
else:
    raise Exception(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming a `FEASIBLE` status guarantees optimality; always check for `OPTIMAL` if an exact solution is required.
- Neglecting to verify the solution against the original constraints, potentially missing numerical issues.
- Forgetting to set a time limit, which can cause the process to hang on large or difficult instances.

# Workflow 2 (Pyomo with Implicit Variable Bounds)

## Modeling stage

### Strategy Overview
This workflow uses a modeling framework (Pyomo) to abstract constraint creation, employing implicit variable bounds (`x[i][j] <= capacity[i] * y[i][j]`) to link variables, which can lead to a cleaner model specification.

### Step 1 - Declare Abstract Model Components
- Define Pyomo `Set` objects for `sources` and `sinks`.
- Declare all `Param` objects for costs, capacities, demands, minimum flows, and participant requirements.

### Step 2 - Define Variables with Implicit Domains
- Create a `Var` for continuous assignment `model.x[i,j]` with domain `NonNegativeReals`.
- Create a `Var` for binary participation `model.y[i,j]` with domain `Binary`.

### Step 3 - Construct Constraints Using Rule Functions
- **Capacity Limit**: Define a rule that sums `model.x[i,j]` over `j` for each `i`.
- **Demand Satisfaction**: Define a rule that sums `model.x[i,j]` over `i` for each `j`.
- **Minimum Participation**: Define a rule that sums `model.y[i,j]` over `i` for each `j`.
- **Linking Constraints**: Implement rules for `model.x[i,j] >= min_flow[i,j] * model.y[i,j]` and `model.x[i,j] <= capacity[i] * model.y[i,j]`.

### Step 4 - Build Objective Expression
- Use a `summation()` or list comprehension to create the linear cost objective: `minimize sum(cost[i,j] * model.x[i,j])`.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "sinks"
  ],
  "parameters": [
    "capacity[sources]",
    "demand[sinks]",
    "cost[sources][sinks]",
    "min_flow[sources][sinks]",
    "min_participants[sinks]"
  ],
  "decision_variables": [
    "x[sources][sinks] >= 0",
    "y[sources][sinks] in {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in sources} sum_{j in sinks} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "capacity_limit[i in sources]: sum_{j in sinks} x[i][j] <= capacity[i]",
    "demand_satisfaction[j in sinks]: sum_{i in sources} x[i][j] >= demand[j]",
    "minimum_participation_count[j in sinks]: sum_{i in sources} y[i][j] >= min_participants[j]",
    "minimum_assignment_if_selected[i in sources][j in sinks]: x[i][j] >= min_flow[i][j] * y[i][j]",
    "implicit_upper_bound[i in sources][j in sinks]: x[i][j] <= capacity[i] * y[i][j]"
  ]
}
```

### Common Pitfalls
- Using `capacity[i]` as the upper bound in the linking constraint when a tighter bound (like `min(capacity[i], demand[j])`) is available, which can slightly weaken formulation.
- Defining Pyomo `Rule` functions that inadvertently modify global data, leading to incorrect model behavior.
- Omitting the `minimum_assignment_if_selected` constraint, which is necessary to force a minimum flow when selected.

## Solving stage

### Strategy Overview
Utilize Pyomo's `SolverFactory` to interface with various MILP solvers (e.g., HiGHS, Gurobi). Leverage the framework's utilities for model management, solving, and result extraction.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = SolverFactory('highs')`.
- Set solver options: `solver.options['time_limit'] = timeout`, `solver.options['mip_rel_gap'] = tolerance`.

### Step 2 - Solve and Inspect Termination Condition
- Call `results = solver.solve(model, tee=False)`.
- Check both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`). Accept `optimal` or `feasible` for a usable solution.

### Step 3 - Load Results and Validate
- Ensure results are loaded into the model: `model.solutions.load_from(results)`.
- Extract variable values using `model.x[i,j].value` and `model.y[i,j].value`.
- Write a verification function that checks all constraints using the extracted values and a numerical tolerance.

### Step 4 - Report Key Metrics
- Calculate and report summary statistics: total cost, capacity utilization rates, demand fulfillment percentages, and actual participant counts per sink.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=sources)
model.sinks = pyo.Set(initialize=sinks)
# ... define parameters, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs')
results = solver.solve(model)
if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    total_cost = pyo.value(model.obj)
    # Extract solution
    solution_x = {(i,j): pyo.value(model.x[i,j]) for i in model.sources for j in model.sinks}
    # Add verification and reporting logic here
else:
    raise Exception(f"Solver terminated with condition: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing Pyomo's `solver.status` (e.g., `ok`) with the `termination_condition` (e.g., `optimal`); both must be checked.
- Not using `pyo.value()` to access objective and variable values, leading to errors.
- Setting conflicting solver options (e.g., both `threads` and `parallel` flags) that may cause the solver to fail.
