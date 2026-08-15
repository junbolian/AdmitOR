---
name: MultiPeriodCapacityPlanning
description: |
  Model and solve multi-period capacity planning problems with discrete activation, continuous output, startup limits, and reserve margins using mixed-integer linear programming.
---

# Workflow 1 (Pyomo with Gurobi/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling to define a structured MILP, separating sets, parameters, and constraints for clarity and maintainability. It is suited for prototyping and integration with commercial (Gurobi) or open-source (CBC) solvers via a unified interface.

### Step 1 - Define Sets and Indices
- Create sets for time periods (e.g., `T`) and resource types (e.g., `G`) to index all variables and constraints.
- Use `pyo.Set` or Python lists to define these indices, ensuring they are ordered for time-dependent constraints.

### Step 2 - Declare Decision Variables
- Define integer variables for discrete counts (e.g., `n[t,g]` for number of active units) with domain `pyo.NonNegativeIntegers`.
- Define integer variables for startup events (e.g., `s[t,g]`) with the same domain.
- Define continuous variables for output levels (e.g., `x[t,g]`) with domain `pyo.NonNegativeReals`.

### Step 3 - Formulate the Objective Function
- Construct a linear objective summing fixed, variable, and startup costs across all periods and types.
- Use parameters like `fixed_cost[g]`, `variable_cost[g]`, and `startup_cost[g]` within the summation.

### Step 4 - Enforce Capacity and Output Linking
- For each time period and resource type, bound the continuous output by the number of active units: `min_output[g] * n[t,g] <= x[t,g] <= max_output[g] * n[t,g]`.
- Apply global capacity bounds on the number of active units per type if needed.

### Step 5 - Impose System-Wide Requirements
- Add a demand coverage constraint: for each period, the sum of outputs across types must meet or exceed the period's demand.
- Add a reserve margin constraint: for each period, the sum of maximum possible output (`max_output[g] * n[t,g]`) must meet or exceed the demand multiplied by a reserve factor.

### Step 6 - Model Startup and Operational Dynamics
- For the first period, enforce that all active units are startups: `n[0,g] == s[0,g]`. Apply an initial startup limit per type.
- For subsequent periods, link active units across time: `n[t,g] <= n[t-1,g] + s[t,g]`.
- Limit startups in period `t` to the number of units active in period `t-1`: `s[t,g] <= n[t-1,g]`.

### Formulation Template
```json
{
  "sets": ["T (time periods)", "G (resource types)"],
  "parameters": [
    "demand[T]",
    "reserve_factor",
    "min_output[G]",
    "max_output[G]",
    "fixed_cost[G]",
    "variable_cost[G]",
    "startup_cost[G]",
    "startup_limit_initial[G]"
  ],
  "decision_variables": [
    "n[T,G] (integer, active count)",
    "s[T,G] (integer, startup count)",
    "x[T,G] (continuous, output)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{t,g} (fixed_cost[g]*n[t,g] + variable_cost[g]*x[t,g] + startup_cost[g]*s[t,g])"
  },
  "constraints": [
    "output_lower_bound: min_output[g]*n[t,g] <= x[t,g] forall t,g",
    "output_upper_bound: x[t,g] <= max_output[g]*n[t,g] forall t,g",
    "demand_coverage: sum_g x[t,g] >= demand[t] forall t",
    "reserve_margin: sum_g max_output[g]*n[t,g] >= reserve_factor * demand[t] forall t",
    "startup_initial: n[0,g] == s[0,g]; s[0,g] <= startup_limit_initial[g] forall g",
    "operational_link: n[t,g] <= n[t-1,g] + s[t,g] forall t>0,g",
    "startup_limit: s[t,g] <= n[t-1,g] forall t>0,g"
  ]
}
```

### Common Pitfalls
- Adding redundant constraints that over-specify startup logic (e.g., both `s[t,g] <= n[t,g]` and `s[t,g] >= n[t,g] - n[t-1,g]`), which can cause infeasibility.
- Interpreting startup limits ambiguously without validating the formulation's feasibility in a simple test case.
- Neglecting to verify that the core problem (demand plus reserve) is feasible with minimal constraints before adding complex startup dynamics.

## Solving stage

### Strategy Overview
Solve the Pyomo model using `SolverFactory`, configuring solver parameters for performance and reliability. Always check solver status and termination condition, and implement post-solution validation to confirm constraint satisfaction.

### Step 1 - Select and Configure Solver
- Instantiate a solver object (e.g., `SolverFactory('gurobi')` or `SolverFactory('cbc')`).
- Set key parameters: `TimeLimit`, `MIPGap` (e.g., `1e-4`), `Threads`, and `Seed` for reproducibility.

### Step 2 - Solve and Check Status
- Call `solver.solve(model)` and capture the results object.
- Check `results.solver.status` and `results.solver.termination_condition`. Proceed only if status is `ok` and condition is `optimal` or `feasible`.

### Step 3 - Validate Solution Feasibility
- Extract variable values and programmatically verify each constraint type (demand, reserve, output bounds, startup limits) within a small tolerance.
- Print a detailed schedule (active counts, startups, output per type and period) for transparency.

### Step 4 - Report Results
- Output the total objective value in a clear, parseable format (e.g., `RESULT: <value>`).
- Optionally, compute and display a cost breakdown (fixed, variable, startup) to validate the objective calculation.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (concrete example)
model = pyo.ConcreteModel()
# ... populate model using the formulation template above ...

# Solve
solver = pyo.SolverFactory('gurobi')  # or 'cbc'
solver.options['TimeLimit'] = 300
solver.options['MIPGap'] = 1e-4
solver.options['Threads'] = 4
solver.options['Seed'] = 42
results = solver.solve(model)

# Status / termination checks
if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:
    print("Solution optimal.")
    # Extract and validate solution
    # ... validation code ...
    print(f"RESULT: {pyo.value(model.obj)}")
else:
    print("Solve failed or no optimal solution found.")
    # Handle infeasibility or other conditions
```

### Common Pitfalls
- Running multiple solver calls without intermediate feasibility checks, wasting time on repeated infeasible runs.
- Changing multiple constraints simultaneously between runs, making it impossible to identify the source of infeasibility.
- Relying solely on solver error messages; not using infeasibility certificates or manual feasibility checks early in debugging.

# Workflow 2 (ORTools CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT solver, modeling the problem with integer variables and linear constraints via the `cp_model` interface. It is well-suited for problems where all decision variables are naturally integer, and leverages CP-SAT's strength in logical constraints and search.

### Step 1 - Initialize Model and Create Indexing Structures
- Create a `cp_model.CpModel()` object.
- Define lists or ranges for time periods and resource types to use for indexing.

### Step 2 - Create Integer Decision Variables
- For active counts `n[t,g]`, create an integer variable with domain `[0, max_capacity[g]]` using `model.NewIntVar`.
- For startup counts `s[t,g]`, create a similar integer variable.
- For continuous output `x[t,g]`, since CP-SAT requires integer variables, scale the output by a factor (e.g., 1000) to represent it as an integer, or use a sufficiently large domain.

### Step 3 - Define Scaled Objective Function
- Construct a linear expression summing scaled cost terms. Ensure all coefficients are integers.
- Use `model.Minimize()` to set the objective.

### Step 4 - Implement Output and Capacity Constraints
- For each period and type, add constraints linking output to active count: `min_output[g] * n[t,g] <= x[t,g]` and `x[t,g] <= max_output[g] * n[t,g]`.
- Use `model.AddLinearConstraint` or `AddMultiplicationEquality` for product terms if using auxiliary variables.

### Step 5 - Enforce Demand and Reserve Margin
- For each period, add a constraint that the sum of outputs across types is >= demand.
- For reserve margin, add a constraint that the sum of `max_output[g] * n[t,g]` across types is >= `reserve_factor * demand[t]`.

### Step 6 - Encode Startup Logic with Linear Constraints
- For the first period: `n[0,g] == s[0,g]` and `s[0,g] <= startup_limit_initial[g]`.
- For `t>0`: add `n[t,g] <= n[t-1,g] + s[t,g]` and `s[t,g] <= n[t-1,g]`.

### Formulation Template
```json
{
  "sets": ["T (time periods)", "G (resource types)"],
  "parameters": [
    "demand[T] (integer, scaled if necessary)",
    "reserve_factor",
    "min_output[G] (integer, scaled)",
    "max_output[G] (integer, scaled)",
    "fixed_cost[G] (integer)",
    "variable_cost[G] (integer, scaled)",
    "startup_cost[G] (integer)",
    "startup_limit_initial[G]"
  ],
  "decision_variables": [
    "n[T,G] (integer, active count)",
    "s[T,G] (integer, startup count)",
    "x[T,G] (integer, scaled output)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{t,g} (fixed_cost[g]*n[t,g] + variable_cost[g]*x[t,g] + startup_cost[g]*s[t,g])"
  },
  "constraints": [
    "output_lower_bound: min_output[g]*n[t,g] <= x[t,g] forall t,g",
    "output_upper_bound: x[t,g] <= max_output[g]*n[t,g] forall t,g",
    "demand_coverage: sum_g x[t,g] >= demand[t] forall t",
    "reserve_margin: sum_g max_output[g]*n[t,g] >= reserve_factor * demand[t] forall t",
    "startup_initial: n[0,g] == s[0,g]; s[0,g] <= startup_limit_initial[g] forall g",
    "operational_link: n[t,g] <= n[t-1,g] + s[t,g] forall t>0,g",
    "startup_limit: s[t,g] <= n[t-1,g] forall t>0,g"
  ]
}
```

### Common Pitfalls
- Forgetting to scale continuous parameters (output, costs) to integers, leading to model errors.
- Creating overly large variable domains, which can slow down the CP-SAT search.
- Misinterpreting startup limits in a way that creates infeasible combinations of constraints; always test logic with small data.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured search parameters, extract the solution, and perform numerical validation. CP-SAT returns integer solutions directly, simplifying post-processing.

### Step 1 - Configure and Execute Solver
- Create a solver instance `cp_model.CpSolver()`.
- Set solver parameters like `cp_model.CpSolver().parameters.max_time_in_seconds` and `num_search_workers`.

### Step 2 - Solve and Check Solution Status
- Call `solver.Solve(model)` and check the returned status (`OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`).
- If status is `OPTIMAL` or `FEASIBLE`, proceed to extract variable values.

### Step 3 - Extract and Validate Solution
- For each variable, retrieve its value using `solver.Value(var)`.
- Programmatically verify all constraints using the extracted values, accounting for integer scaling.
- Print a summary schedule and cost breakdown.

### Step 4 - Report and Analyze
- Output the objective value. Compare the cost structure with manual calculations to ensure correctness.
- If the solution uses only one resource type, perform a quick manual trade-off analysis to sanity-check optimality.

### Code Usage
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... build model using formulation template ...

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 4
# Optional: set log search progress
# solver.parameters.log_search_progress = True

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print("Solution found.")
    # Extract variable values
    n_values = {(t,g): solver.Value(n[t,g]) for t in T for g in G}
    # ... extract others ...
    # Validate constraints
    # ... validation code ...
    objective_value = solver.ObjectiveValue()
    print(f"RESULT: {objective_value}")
else:
    print("No feasible solution found.")
    # Analyze infeasibility
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing valid solutions.
- Assuming `.Value()` returns an integer; it returns an int, but ensure scaling is reversed appropriately.
- Ignoring the opportunity to add a solution callback to monitor progress or collect multiple solutions.
