---
name: BinaryAssignmentWithCardinalityAndExclusions
description: |
  Solves binary assignment problems with cardinality constraints and pairwise incompatibilities, minimizing total cost, using either a high-level modeling framework or a direct solver API.

---
# Workflow 1 (High-Level Modeling Framework)

## Modeling stage

### Strategy Overview
This workflow uses a high-level algebraic modeling language (e.g., Pyomo) to declaratively define sets, parameters, variables, and constraints. It is ideal for rapid prototyping, clear separation of model logic from solver specifics, and leveraging automatic constraint propagation.

### Step 1 - Define Sets and Parameters
- Define the two sets of elements to be matched (e.g., `SET_A`, `SET_B`).
- Define a cost parameter as a dictionary mapping assignment pairs `(i, j)` to a numerical cost.
- Define a list of incompatible assignment pairs `INCOMPATIBLE_PAIRS` as tuples `((i1, j1), (i2, j2))`.
- Define the required total number of assignments `K` as a scalar parameter.

### Step 2 - Create Binary Decision Variables
- Create a binary decision variable `x[i, j]` for each `i` in `SET_A` and `j` in `SET_B`.
- The variable domain is `{0, 1}`, where `1` indicates an assignment.

### Step 3 - Formulate Cardinality Constraints
- Add a constraint limiting assignments per element in `SET_A`: `sum(x[i, j] for j in SET_B) <= 1` for each `i`.
- Add a constraint limiting assignments per element in `SET_B`: `sum(x[i, j] for i in SET_A) <= 1` for each `j`.
- Add a global constraint enforcing the exact total assignments: `sum(x[i, j] for all i, j) == K`.

### Step 4 - Encode Pairwise Incompatibilities
- For each pair `((i1, j1), (i2, j2))` in `INCOMPATIBLE_PAIRS`, add a linear constraint: `x[i1, j1] + x[i2, j2] <= 1`.
- This ensures at most one of the two incompatible assignments can be active.

### Step 5 - Define Linear Objective
- Define the objective to minimize total cost: `Minimize sum(cost[i, j] * x[i, j] for all i, j)`.

### Formulation Template
```json
{
  "sets": ["SET_A", "SET_B"],
  "parameters": ["cost[SET_A, SET_B]", "K", "INCOMPATIBLE_PAIRS"],
  "decision_variables": ["x[SET_A, SET_B] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in SET_A, j in SET_B)"
  },
  "constraints": [
    "sum(x[i, j] for j in SET_B) <= 1, ∀ i ∈ SET_A",
    "sum(x[i, j] for i in SET_A) <= 1, ∀ j ∈ SET_B",
    "sum(x[i, j] for all i, j) == K",
    "x[i1, j1] + x[i2, j2] <= 1, ∀ ((i1, j1), (i2, j2)) ∈ INCOMPATIBLE_PAIRS"
  ]
}
```

### Common Pitfalls
- Forgetting to define the `K` parameter, leading to an under- or over-constrained model.
- Incorrectly indexing the cost dictionary or incompatible pairs list, causing runtime errors.
- Using a strict equality (`==`) for per-element cardinality instead of `<=`, which may incorrectly force assignments.

## Solving stage

### Strategy Overview
The model is passed to a MILP solver (e.g., CBC, Gurobi) via the modeling framework's interface. This stage focuses on configuring the solver, handling the solve call, rigorously checking the solution status, and extracting results.

### Step 1 - Configure Solver and Solve
- Instantiate a solver object via the framework's factory (e.g., `SolverFactory("cbc")`).
- Set key solver parameters: a time limit (`seconds`), optimality gap tolerance (`ratio` or `MIPGap`), number of threads (`threads`), and a random seed for reproducibility.
- Call the solve method on the model object, optionally suppressing the solver log (`tee=False`).

### Step 2 - Validate Solver Status and Termination
- Retrieve the solver status and termination condition from the results object.
- Check if the status is `ok` and the termination condition is `optimal` or `feasible`. Proceed only if both checks pass.

### Step 3 - Extract and Verify Solution
- Extract the objective value from the model.
- Extract assignments by iterating over all variables `x[i, j]` and collecting those with a value > 0.5 (accounting for numerical tolerance).
- Programmatically verify that the extracted solution satisfies all cardinality and incompatibility constraints as a sanity check.

### Step 4 - Handle Failure Cases
- If the solver status is not `ok` or termination is `infeasible`, `unbounded`, or `maxTimeLimit`, output a structured error payload (e.g., JSON) indicating the failure reason.
- Consider solving a relaxed model (e.g., without incompatibility constraints) to diagnose infeasibility.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... [Model building steps using the Formulation Template above] ...

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False)
status = results.solver.status
term = results.solver.termination_condition

if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    # Extract solution
    obj_val = float(pyo.value(model.obj))
    assignments = [(i, j) for i in model.SET_A for j in model.SET_B if pyo.value(model.x[i, j]) > 0.5]
    # Optional verification
    for (i1, j1), (i2, j2) in model.INCOMPATIBLE_PAIRS:
        assert pyo.value(model.x[i1, j1]) + pyo.value(model.x[i2, j2]) <= 1 + 1e-6
else:
    # Handle failure
    output = {"status": "failure", "solver_status": str(status), "termination": str(term)}
```

### Common Pitfalls
- Not checking both solver status *and* termination condition, leading to extraction of invalid results.
- Using a loose optimality gap (`ratio` > 0) when an exact optimum is required.
- Forgetting to convert the objective value from a Pyomo expression to a float after solving.

# Workflow 2 (Direct Constraint Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a solver's direct Python API (e.g., OR-Tools CP-SAT, Gurobi Python API) to imperatively build the model. It offers fine-grained control over variable and constraint creation, and native support for logical (indicator) constraints, which can be more efficient for complex conditional exclusions.

### Step 1 - Initialize Model and Create Variables
- Instantiate the solver's model object (e.g., `cp_model.CpModel()`).
- Create a dictionary of binary decision variables `x[i, j]` using the model's NewBoolVar method.

### Step 2 - Add Cardinality Constraints via Linear Sums
- For each element `i` in `SET_A`, create a linear constraint: `sum(x[i, j] for j in SET_B) <= 1`.
- For each element `j` in `SET_B`, create a linear constraint: `sum(x[i, j] for i in SET_A) <= 1`.
- Add a global linear constraint for the exact total: `sum(x[i, j] for all i, j) == K`.

### Step 3 - Encode Incompatibilities with Linear or Indicator Constraints
- **Option A (Linear):** For each incompatible pair `((i1, j1), (i2, j2))`, add `x[i1, j1] + x[i2, j2] <= 1`.
- **Option B (Indicator - for conditional logic):** If incompatibility is conditional (e.g., "if A then not B"), use the solver's native indicator constraint: `model.Add(x[i2, j2] == 0).OnlyEnforceIf(x[i1, j1])`.

### Step 4 - Define Linear Objective
- Create a linear expression for the total cost: `sum(cost[i, j] * x[i, j] for all i, j)`.
- Set this as the model's objective to minimize.

### Formulation Template
```json
{
  "sets": ["SET_A", "SET_B"],
  "parameters": ["cost[SET_A, SET_B]", "K", "INCOMPATIBLE_PAIRS"],
  "decision_variables": ["x[SET_A, SET_B] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j] for i in SET_A, j in SET_B)"
  },
  "constraints": [
    "Linear Cardinality (per element and total)",
    "Linear or Indicator Incompatibility"
  ]
}
```

### Common Pitfalls
- Using 1-based indexing when the solver API expects 0-based, causing index errors.
- Inefficiently creating constraints inside nested loops for large sets; pre-compute sums where possible.
- Mixing indicator constraint syntax with linear constraints incorrectly, leading to model errors.

## Solving stage

### Strategy Overview
The solver is invoked directly on the built model. This stage involves setting search parameters, executing the solve, interpreting the result status, and parsing the variable assignments. It emphasizes low-level control and performance tuning.

### Step 1 - Configure Solver Parameters
- Access the solver's parameter proto or dictionary (e.g., `model.parameters` in CP-SAT).
- Set a maximum time limit (`max_time_in_seconds`).
- Set the number of parallel workers (`num_search_workers`).
- Set a random seed for reproducibility (`random_seed`).
- For exact optimization, disable relative gap (`relative_gap_limit = -1.0` or `MIPGap=0`).

### Step 2 - Execute Solve and Check Status
- Call the solver's `Solve()` method on the model.
- Capture the returned status code (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).

### Step 3 - Extract Solution if Feasible
- If the status is `OPTIMAL` or `FEASIBLE`, retrieve the objective value from the solver response.
- Iterate over the `x[i, j]` variable dictionary, using the solver's `Value()` or `SolutionValue()` method to get each variable's assignment (values are typically 0 or 1).
- Collect assignments where the value is 1.

### Step 4 - Provide Structured Output and Handle Failures
- Output a dictionary containing the solver status, objective value, and list of assignments.
- For non-feasible statuses, return a structured error message and consider logging the solver's full response for debugging.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
x = {}
for i in SET_A:
    for j in SET_B:
        x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")
# ... [Add constraints as per Modeling Steps 2-4] ...
# Define objective
objective_terms = [cost[i, j] * x[(i, j)] for i in SET_A for j in SET_B]
model.Minimize(sum(objective_terms))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = -1.0  # Disable relative gap

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    obj_val = solver.ObjectiveValue()
    assignments = [(i, j) for i in SET_A for j in SET_B if solver.Value(x[(i, j)]) == 1]
    result = {"status": "success", "objective": obj_val, "assignments": assignments}
else:
    status_map = {cp_model.UNKNOWN: "UNKNOWN", cp_MODEL.INFEASIBLE: "INFEASIBLE", ...}
    result = {"status": "failure", "solver_status": status_map.get(status, str(status))}
```

### Common Pitfalls
- Assuming the solver returns integer values for binary variables; always use the solver's `Value()` method.
- Not setting a time limit for large or complex instances, risking excessive runtime.
- Misinterpreting the `FEASIBLE` status as optimal; if optimality is required, check for `OPTIMAL` specifically.
