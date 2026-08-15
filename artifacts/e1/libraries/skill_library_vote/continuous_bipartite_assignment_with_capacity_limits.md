---
name: Continuous Bipartite Assignment with Capacity Limits
description: |
  Model and solve linear cost minimization for allocating continuous quantities from sources to destinations, respecting supply capacities, exact demand satisfaction, and per-assignment upper bounds.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Use Pyomo's structured modeling to define sets, parameters, variables, and constraints explicitly, creating a clear separation between model logic and data. This approach is highly maintainable and leverages Pyomo's solver-agnostic abstraction.

### Step 1 - Define Sets and Parameters
- Define two sets: `sources` (e.g., resources, employees) and `destinations` (e.g., tasks, projects).
- Organize all input data as Pyomo `Param` objects or Python dictionaries: `availability[s]`, `requirement[d]`, `cost[s,d]`, and `per_assignment_limit[s,d]`.
- Use nested dictionaries or 2D arrays for matrix-like parameters for efficient indexing.

### Step 2 - Create Decision Variables
- Define a continuous, non-negative decision variable `x[s,d]` representing the quantity assigned from source `s` to destination `d`.
- Optionally, set the variable's upper bound directly using the `per_assignment_limit` parameter during creation to simplify constraints.

### Step 3 - Formulate Constraints
- **Supply Capacity:** For each source `s`, add constraint: `sum(x[s,d] for d in destinations) <= availability[s]`.
- **Demand Satisfaction:** For each destination `d`, add constraint: `sum(x[s,d] for s in sources) == requirement[d]`. Use equality for exact fulfillment.
- **Per-Assignment Limit:** For each pair `(s,d)`, add constraint: `x[s,d] <= per_assignment_limit[s,d]`. This can be integrated as a variable bound instead of a separate constraint.

### Step 4 - Define Objective
- Formulate a linear minimization objective: `minimize sum(cost[s,d] * x[s,d] for s in sources for d in destinations)`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "availability", "index": "sources"},
    {"name": "requirement", "index": "destinations"},
    {"name": "cost", "index": ["sources", "destinations"]},
    {"name": "per_assignment_limit", "index": ["sources", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s,d] * x[s,d])"
  },
  "constraints": [
    {"name": "supply_limit", "index": "sources", "expression": "sum(x[s,d]) <= availability[s]"},
    {"name": "demand_satisfaction", "index": "destinations", "expression": "sum(x[s,d]) == requirement[d]"},
    {"name": "assignment_limit", "index": ["sources", "destinations"], "expression": "x[s,d] <= per_assignment_limit[s,d]"}
  ]
}
```

### Common Pitfalls
- Hardcoding large numbers as upper bounds for missing `per_assignment_limit` data, which can mask infeasibility or create unrealistic solutions.
- Mixing data structures (e.g., dictionaries for costs but lists for availability) increases maintenance complexity.
- Defining the per-assignment limit both as a variable bound and a separate constraint, creating redundant model components.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an efficient LP solver (HiGHS or CBC) with appropriate configuration for deterministic results. Implement robust solution loading and post-solution verification to ensure correctness.

### Step 1 - Configure and Run Solver
- Instantiate the solver: `solver = SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set key options: `time_limit` for runtime control, `mip_rel_gap` (or `ratio`) to `0.0` for an exact optimality tolerance, and avoid unrecognized options like `threads` for CBC.
- Solve with `load_solutions=False` to gain control over solution loading.

### Step 2 - Check Solver Status
- Check if the solver status is `SolverStatus.ok`.
- Check the termination condition is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- Only proceed to load and process the solution if both checks pass.

### Step 3 - Load Solution and Extract Results
- Manually load the solution into the model: `model.solutions.load_from(results)`.
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate over variables `model.x[s,d]` and extract values using `pyo.value()` or `.value`, applying a small tolerance (e.g., `1e-6`) to identify non-zero assignments.

### Step 4 - Verify Solution Feasibility
- Programmatically verify all constraints: recompute sums for supply and demand constraints, and check per-assignment limits against the solution values.
- Recalculate the total cost from the extracted variable values to validate the objective value.
- Print utilization metrics (e.g., source usage/capacity, demand fulfillment) for validation.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (example structure)
model = pyo.ConcreteModel()
model.S = pyo.Set(initialize=sources)
model.D = pyo.Set(initialize=destinations)
model.x = pyo.Var(model.S, model.D, domain=pyo.NonNegativeReals, bounds=(0, per_assignment_limit))
# ... add objective and constraints ...

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, load_solutions=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    model.solutions.load_from(results)
    objective_value = pyo.value(model.obj)
    # Extract and verify solution
else:
    # Handle failure: print results.solver.termination_condition
```

### Common Pitfalls
- Attempting to access variable attributes like `.expr.to_string()` on Pyomo `VarData` objects, causing runtime errors.
- Setting invalid solver options (e.g., negative optimality gap, unrecognized `threads` parameter) leading to warnings or errors.
- Forgetting to load the solution after solving with `load_solutions=False`, resulting in inaccessible variable values.

# Workflow 2 (OR-Tools LP with GLOP/CBC)

## Modeling stage

### Strategy Overview
Use OR-Tools' `pywraplp` API to construct the model imperatively. This workflow is efficient for prototyping and leverages Google's optimized LP solvers, with variable bounds integrated directly during creation.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')` for continuous LP or `'CBC'` for MIP.
- Organize data as Python lists or nested dictionaries: `availability[]`, `requirement[]`, `cost[][]`, `per_assignment_limit[][]`.

### Step 2 - Create Variables with Integrated Bounds
- Create decision variables `x[i][j]` in nested loops over sources and destinations.
- Use `solver.NumVar(lower_bound, upper_bound, name)` where the `upper_bound` is the `per_assignment_limit[i][j]`. This integrates the individual limit directly.

### Step 3 - Add Supply and Demand Constraints
- **Supply Capacity:** For each source `i`, create a constraint: `sum(x[i][j] for j in destinations) <= availability[i]`. Use `solver.Constraint(-inf, availability[i])` and `SetCoefficient`.
- **Demand Satisfaction:** For each destination `j`, create a constraint: `sum(x[i][j] for i in sources) == requirement[j]`. Use `solver.Constraint(requirement[j], requirement[j])` for equality.

### Step 4 - Define Linear Objective
- Create the objective: `objective = solver.Objective()`.
- For each variable `x[i][j]`, set its coefficient using `objective.SetCoefficient(x[i][j], cost[i][j])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "availability", "index": "sources"},
    {"name": "requirement", "index": "destinations"},
    {"name": "cost", "index": ["sources", "destinations"]},
    {"name": "per_assignment_limit", "index": ["sources", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "domain": "continuous", "lower_bound": 0, "upper_bound": "per_assignment_limit"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j])"
  },
  "constraints": [
    {"name": "supply", "index": "sources", "expression": "sum(x[i,j]) <= availability[i]"},
    {"name": "demand", "index": "destinations", "expression": "sum(x[i,j]) == requirement[j]"}
  ]
}
```

### Common Pitfalls
- Defining per-assignment limits as separate constraints instead of variable upper bounds, which increases model size unnecessarily.
- Using loose or infinite upper bounds when specific `per_assignment_limit` data is available, missing an opportunity to tighten the model.
- Ambiguity in problem statements leading to incorrect assumptions for missing limit values; always verify feasibility of assumptions.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' wrapper for GLOP or CBC. Implement solution verification and cross-validation, potentially using a second solver to confirm optimality for critical problems.

### Step 1 - Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `solver.OPTIMAL` or `solver.FEASIBLE`. Handle `solver.INFEASIBLE` or `solver.UNBOUNDED` with appropriate error messages.

### Step 2 - Extract Solution Values
- Extract the objective value using `objective.Value()`.
- Iterate over all variables, using `.solution_value()` to get their assignments.
- Apply a tolerance (e.g., `1e-6`) to filter and report only non-zero assignments.

### Step 3 - Verify Constraints Programmatically
- Recompute the total assignment from each source and compare against `availability[i]` with tolerance.
- Recompute the total assignment to each destination and compare against `requirement[j]` with tolerance.
- Check that no assignment exceeds its `per_assignment_limit[i][j]`.
- Recalculate the total cost from variable values and cost coefficients to validate the reported objective.

### Step 4 - Cross-Validate with Alternate Solver (Optional)
- For verification, solve the same model instance with a different solver backend (e.g., CBC after GLOP).
- Compare objective values and key assignment values to confirm solution stability and correctness.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... create variables x[i][j] with bounds ...
# ... add supply and demand constraints ...
# ... set objective ...

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    # Extract variable values: x[i][j].solution_value()
    # Verify constraints
else:
    # Handle infeasible/unbounded status
```

### Common Pitfalls
- Not checking solver status before accessing `.solution_value()` or `.Value()`, which can cause crashes.
- Relying solely on solver-reported feasibility without programmatic verification, potentially missing numerical issues.
- Using complex string parsing to reconstruct cost coefficients from the model for post-processing; instead, store cost data separately for direct access.
