---
name: BipartiteAssignmentOptimization
description: |
  Model and solve bipartite assignment problems with integer flows, capacity and demand limits, and linear profit objectives using either sparse variable construction or explicit compatibility constraints.
---

# Workflow 1 (Sparse Variable Construction)

## Modeling stage

### Strategy Overview
This workflow models the bipartite assignment problem by only creating decision variables for compatible source-sink pairs, reducing model size and improving solver performance. It uses a compatibility matrix to guide sparse variable creation and enforces capacity and demand constraints directly on the created variables.

### Step 1 - Define Compatibility Structure
- Extract the list of compatible pairs between the first set (e.g., packages) and the second set (e.g., routes) from the problem data.
- Construct a binary compatibility matrix `compatible[source][sink]` or a list of compatible sinks for each source to guide variable creation.
- **Usage**: `compatible = [[0]*num_sources for _ in range(num_sinks)]`; populate based on given lists.

### Step 2 - Create Integer Assignment Variables
- For each compatible `(source, sink)` pair, create an integer decision variable `y[source][sink]`.
- Set the variable's upper bound to the minimum of the source's demand limit and the sink's capacity to embed simple feasibility.
- For incompatible pairs, store `None` or skip creation entirely to maintain a sparse structure.
- **Usage**: `solver.IntVar(0, min(demand[source], capacity[sink]), f"y_{source}_{sink}")`.

### Step 3 - Enforce Bipartite Constraints
- Add a constraint for each source: the sum of its assigned units across all compatible sinks must be less than or equal to its demand limit.
- Add a constraint for each sink: the sum of assigned units from all compatible sources must be less than or equal to its capacity.
- **Usage**: Use `solver.Add(sum(y[source][sink] for sink ... if y[source][sink] is not None) <= demand[source])`.

### Step 4 - Set Linear Profit Objective
- Define the objective to maximize total profit, summing over all created variables weighted by their per-unit revenue coefficient.
- Ensure the objective sense is set to maximization.
- **Usage**: `objective.SetCoefficient(y[source][sink], revenue[source])` for each variable; `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": [
    "S (sources)",
    "T (sinks)"
  ],
  "parameters": [
    "demand_limit[s] for s in S",
    "capacity[t] for t in T",
    "revenue[s] for s in S",
    "compatible[s][t] binary for s in S, t in T"
  ],
  "decision_variables": [
    "y[s][t] ∈ NonNegativeIntegers, defined only if compatible[s][t] == 1"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{s in S, t in T} revenue[s] * y[s][t]"
  },
  "constraints": [
    "sum_{t in T} y[s][t] <= demand_limit[s] for all s in S",
    "sum_{s in S} y[s][t] <= capacity[t] for all t in T"
  ]
}
```

### Common Pitfalls
- Forgetting to handle `None` variables when summing in constraints, leading to type errors.
- Setting variable bounds too loosely (e.g., only to demand limit) and missing tighter capacity-based bounds, which can slow presolve.
- Not verifying the compatibility matrix is consistent with problem dimensions, causing index errors.

## Solving stage

### Strategy Overview
Solve the sparse integer model using a MIP solver configured for performance. Focus on verifying optimality, extracting the sparse solution, and validating constraint satisfaction.

### Step 1 - Configure Solver and Limits
- Instantiate a solver suitable for integer programming (e.g., SCIP, CBC).
- Set a time limit and the number of threads for parallel processing.
- Optionally, set an optimality gap tolerance to zero for exact solutions.
- **Usage**: `solver.SetTimeLimit(300000)`; `solver.SetNumThreads(4)`.

### Step 2 - Solve and Check Status
- Execute the solver and capture the result status.
- Check for an `OPTIMAL` or `FEASIBLE` status before proceeding to solution extraction. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate diagnostics.
- **Usage**: `status = solver.Solve()`; `if status == pywraplp.Solver.OPTIMAL:`.

### Step 3 - Extract and Validate Solution
- Iterate over the sparse variable structure, retrieving the solution value for each defined variable.
- Compute aggregate totals per source and per sink to verify demand and capacity constraints are satisfied within tolerance.
- Report key metrics like total profit, capacity utilization, and demand fulfillment.
- **Usage**: `value = y[s][t].solution_value()`; compute `sum_t value` for each source.

### Step 4 - Analyze and Report
- Print a summary of assignments, highlighting which source-sink pairs have positive flow.
- Compare the achieved objective value to a simple upper bound (e.g., sum of top revenues times total capacity) as a sanity check.
- **Usage**: Print a table of non-zero `y[s][t]` values and total profit.

### Code Usage
```python
# build model from formulation
import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(300000)
solver.SetNumThreads(4)

# ... (build sparse model as per Modeling Stage steps)

# solve with status / termination checks
status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL:
    print(f"Optimal profit: {solver.Objective().Value()}")
    # Extract and validate solution
    total_by_source = {s: 0 for s in sources}
    total_by_sink = {t: 0 for t in sinks}
    for s in sources:
        for t in sinks:
            var = y[s][t]
            if var is not None:
                val = var.solution_value()
                if val > 1e-6:
                    total_by_source[s] += val
                    total_by_sink[t] += val
    # ... validation checks
else:
    print(f"Solver did not find optimal solution. Status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing `.solution_value()`, which crashes on non-optimal/feasible statuses.
- Using a loose optimality gap, which may stop at a suboptimal solution when an exact optimum is required.
- Overlooking the performance benefit of setting variable bounds during creation, leaving it to the solver's presolve.

# Workflow 2 (Explicit Compatibility Constraints)

## Modeling stage

### Strategy Overview
This workflow creates a variable for every possible source-sink pair and uses explicit constraints to force zero flow for incompatible pairs. It leverages a modeling framework's ability to skip or conditionally generate constraints, resulting in a clean, declarative model.

### Step 1 - Define Full Variable Set
- Create an integer decision variable `x[source, sink]` for every combination of source and sink, with a standard non-negative integer domain.
- Do not filter based on compatibility at variable creation; let constraints handle infeasibility.
- **Usage**: `model.x = pyo.Var(model.S, model.T, domain=pyo.NonNegativeIntegers)`.

### Step 2 - Enforce Compatibility via Constraints
- Add a constraint for each `(source, sink)` pair that sets `x[source, sink] == 0` if the pair is incompatible.
- Use the modeling framework's constraint skipping feature (e.g., `pyo.Constraint.Skip`) for compatible pairs to avoid adding trivial constraints.
- **Usage**: `model.compat_con = pyo.Constraint(model.S, model.T, rule=compatibility_rule)` where the rule returns `model.x[p,r] == 0` or `pyo.Constraint.Skip`.

### Step 3 - Apply Capacity and Demand Limits
- Add a constraint for each sink: the sum of flows from all sources must not exceed the sink's capacity.
- Add a constraint for each source: the sum of flows to all sinks must not exceed the source's demand limit.
- These constraints sum over all variables; the compatibility constraints will ensure incompatible contributions are zero.
- **Usage**: `model.capacity_con = pyo.Constraint(model.T, rule=lambda m, t: sum(m.x[s,t] for s in m.S) <= capacity[t])`.

### Step 4 - Define Linear Objective
- Formulate the objective to maximize total profit, summing the product of each variable and its per-unit revenue coefficient over all source-sink pairs.
- **Usage**: `model.obj = pyo.Objective(expr=sum(revenue[s] * model.x[s,t] for s in model.S for t in model.T), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": [
    "S (sources)",
    "T (sinks)"
  ],
  "parameters": [
    "demand_limit[s] for s in S",
    "capacity[t] for t in T",
    "revenue[s] for s in S",
    "compatible[s][t] binary for s in S, t in T"
  ],
  "decision_variables": [
    "x[s,t] ∈ NonNegativeIntegers for all s in S, t in T"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{s in S, t in T} revenue[s] * x[s,t]"
  },
  "constraints": [
    "x[s,t] == 0 for all s in S, t in T where compatible[s][t] == 0",
    "sum_{s in S} x[s,t] <= capacity[t] for all t in T",
    "sum_{t in T} x[s,t] <= demand_limit[s] for all s in S"
  ]
}
```

### Common Pitfalls
- Creating an overly large model by not using constraint skipping for compatible pairs, which can burden the solver with many trivial `0 == 0` constraints.
- Incorrectly implementing the compatibility rule, leading to `Constraint.Skip` for incompatible pairs and allowing illegal flow.
- Forgetting that the capacity/demand constraints sum over all variables, relying solely on compatibility constraints for bounds.

## Solving stage

### Strategy Overview
Solve the model using a MIP solver via a modeling framework (e.g., Pyomo with CBC). Configure solver options for performance, rigorously check termination conditions, and extract the full assignment matrix.

### Step 1 - Configure Solver Options
- Select an appropriate solver (e.g., CBC, HiGHS) through the modeling framework's factory.
- Set a time limit, optimality gap (to 0 for exact solutions), and thread count for parallel processing.
- **Usage**: `solver = pyo.SolverFactory("cbc")`; `solver.options["seconds"] = 30`; `solver.options["threads"] = 4`.

### Step 2 - Solve and Verify Termination
- Execute the solver and capture the results object.
- Check that the solver status is `ok` and the termination condition is `optimal` (or `feasible` if a time limit was hit) before extracting the solution.
- **Usage**: `results = solver.solve(model, tee=False)`; `if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:`.

### Step 3 - Extract Solution and Compute Aggregates
- Retrieve the value for every variable `x[source, sink]`.
- Compute the total flow per source and per sink to validate against demand limits and capacities.
- Identify non-zero assignments, particularly for compatible pairs.
- **Usage**: `value = pyo.value(model.x[s,t])`; `source_total[s] += value`.

### Step 4 - Validate and Report
- Verify that all variables for incompatible pairs have a value of zero (within solver tolerance).
- Print a summary showing the assignment matrix, total profit, and constraint utilization percentages.
- **Usage**: Print a formatted table of assignments and check `abs(value) < 1e-6` for incompatible pairs.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.S = pyo.Set(initialize=sources)
model.T = pyo.Set(initialize=sinks)
# ... (define parameters, variables, constraints, objective as per Modeling Stage)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0  # Optimality gap
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    print(f"Optimal profit: {pyo.value(model.obj)}")
    # Extract and validate solution
    for s in model.S:
        for t in model.T:
            val = pyo.value(model.x[s,t])
            # ... analysis and validation
else:
    print(f"Solver failed: Status={results.solver.status}, Termination={results.solver.termination_condition}")
```

### Common Pitfalls
- Accessing variable values without checking solver status/termination condition, which may lead to errors or incorrect values.
- Setting a non-zero optimality gap (`ratio`) when an exact integer optimum is required, accepting suboptimal solutions.
- Not leveraging the modeling framework's ability to skip constraints, resulting in a less efficient model.
