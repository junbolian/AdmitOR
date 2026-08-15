---
name: Multi-Commodity Flow Allocation
description: |
  Model and solve multi-source, multi-destination, multi-product allocation problems as linear programs, ensuring demand satisfaction and maximizing total profit.
---

# Workflow 1 (Explicit Set-Based LP with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities with explicit `pyo.Set` definitions to create a structured, index-based model. It is well-suited for problems where sets are clearly defined and the model logic should be separated from data instantiation.

### Step 1 - Define Model Sets
- Declare explicit sets for all problem dimensions (e.g., `sources`, `destinations`, `commodities`) using `pyo.Set()`.
- Use these sets to index parameters and variables, ensuring clarity and preventing dimension mismatches.

### Step 2 - Initialize Multi-Dimensional Parameters
- Store parameters like `profit` and `demand` in dictionaries with tuple keys (e.g., `(source, destination, commodity)`).
- Initialize parameters using comprehensions or explicit loops for clarity and maintainability.

### Step 3 - Create Decision Variables
- Define a three-index decision variable `x[source, destination, commodity]` representing the allocation flow.
- Set the variable domain to `pyo.NonNegativeReals` during creation to implicitly enforce non-negativity.

### Step 4 - Formulate Demand Satisfaction Constraints
- For each `(destination, commodity)` pair, create an equality constraint summing the flow from all sources.
- Ensure the sum equals the exact `demand` parameter for that pair.

### Step 5 - Construct Linear Objective
- Formulate the objective to maximize total profit by summing `profit[src, dest, comm] * x[src, dest, comm]` across all indices.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "commodities"],
  "parameters": [
    {"name": "profit", "dimensions": ["sources", "destinations", "commodities"]},
    {"name": "demand", "dimensions": ["destinations", "commodities"]}
  ],
  "decision_variables": [
    {"name": "x", "dimensions": ["sources", "destinations", "commodities"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[src, dest, comm] * x[src, dest, comm] for src in sources for dest in destinations for comm in commodities)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "sum(x[src, dest, comm] for src in sources) == demand[dest, comm]", "for_all": ["dest in destinations", "comm in commodities"]}
  ]
}
```

### Common Pitfalls
- Using the same iterator name (e.g., `m`) in nested generator expressions, causing variable shadowing and errors.
- Forgetting to align the dimensions of the `demand` parameter with the constraint summation order.
- Initializing parameters with nested lists that are difficult to map to tuple keys, leading to lookup errors.

## Solving stage

### Strategy Overview
This solving stage uses a Pyomo `SolverFactory` with a focus on robust status checking, solution verification, and structured error handling. It is designed for reliability and automated parsing of results.

### Step 1 - Instantiate Solver with Time Limit
- Create a solver instance (e.g., `SolverFactory('cbc')`) and set a reasonable time limit (`seconds=30`) to prevent indefinite runs.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model)` and capture the results object.
- Check both `results.solver.status` (e.g., `SolverStatus.ok`) and `results.solver.termination_condition` (e.g., `TerminationCondition.optimal`) before proceeding.

### Step 3 - Load and Verify Solution
- If the status is optimal or feasible, load the solution into the model.
- Implement a verification loop to recompute constraint satisfaction (e.g., sum allocations per `(destination, commodity)` and compare to demand).

### Step 4 - Output Results and Handle Failures
- Print detailed allocation information, filtering variables with values below a small tolerance (e.g., `1e-6`) for clarity.
- Output the total objective value in a standardized format (e.g., `RESULT:{objective_value}`).
- If the solver fails, output a structured JSON error message containing the solver status and termination condition.

### Code Usage
```python
import pyomo.environ as pyo

# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, parameters, variables, constraints, objective)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        # Load solution and process
        model.solutions.load_from(results)
        # Verification and output
        print(f"RESULT:{pyo.value(model.objective)}")
    elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
        # Handle suboptimal feasible solution
        model.solutions.load_from(results)
        print(f"RESULT_FEASIBLE:{pyo.value(model.objective)}")
    else:
        # Handle non-optimal termination
        print(f'RESULT_JSON:{{"status": "{results.solver.status}", "termination": "{results.solver.termination_condition}"}}')
else:
    print(f'RESULT_JSON:{{"status": "{results.solver.status}", "termination": "{results.solver.termination_condition}"}}')
```

### Common Pitfalls
- Attempting to access variable values before checking `SolverStatus.ok` and loading the solution, leading to errors.
- Not setting a time limit, which can cause the process to hang on difficult instances.
- Failing to catch solver-specific exceptions (like `RuntimeError` on load), which can crash automated pipelines.

# Workflow 2 (Direct Coefficient LP with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses the OR-Tools Linear Solver API (e.g., `GLOP`) to build a model by directly creating variables and setting objective coefficients and constraint coefficients. It is efficient for continuous linear programs and offers a more imperative, coefficient-by-coefficient approach.

### Step 1 - Map Indices to Solver Variables
- Create a dictionary to map each `(source, destination, commodity)` tuple to a solver variable object.
- Use nested loops over all index combinations to instantiate variables with a lower bound of `0` (non-negativity).

### Step 2 - Build Demand Constraints
- For each `(destination, commodity)` pair, create a linear constraint object.
- For each source, add the corresponding variable with a coefficient of `1.0` to this constraint.
- Set the constraint's right-hand side equal to the `demand` parameter for that pair.

### Step 3 - Set Linear Objective Coefficients
- Define the objective function by iterating over all `(source, destination, commodity)` combinations.
- For each combination, set the coefficient of the corresponding variable to the `profit` parameter value.

### Step 4 - Finalize Model Structure
- Set the objective sense to maximization.
- The model is now fully defined by its variables, constraints, and objective coefficients.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "commodities"],
  "parameters": [
    {"name": "profit", "dimensions": ["sources", "destinations", "commodities"]},
    {"name": "demand", "dimensions": ["destinations", "commodities"]}
  ],
  "decision_variables": [
    {"name": "x", "dimensions": ["sources", "destinations", "commodities"], "domain": ">=0"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[src, dest, comm] * x[src, dest, comm])"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "sum(x[src, dest, comm] for src in sources) == demand[dest, comm]", "for_all": ["dest in destinations", "comm in commodities"]}
  ]
}
```

### Common Pitfalls
- Adding explicit non-negativity constraints instead of setting the variable lower bound, which increases model size unnecessarily.
- Mismatching the order of indices when populating constraints, leading to incorrect coefficient assignment.
- Forgetting to set the objective sense, defaulting to minimization.

## Solving stage

### Strategy Overview
This solving stage leverages the OR-Tools solver's direct interface for fast solving of continuous LPs. It includes systematic solution verification and cross-solver validation to ensure reliability and solution correctness.

### Step 1 - Select and Instantiate Solver
- Choose a continuous LP solver appropriate for the problem (e.g., `GLOP`).
- Instantiate the solver using `pywraplp.Solver.CreateSolver('GLOP')`.

### Step 2 - Solve and Check Result Status
- Call `solver.Solve()` and check the return status (e.g., `pywraplp.Solver.OPTIMAL` or `FEASIBLE`).

### Step 3 - Extract and Verify Solution
- If optimal/feasible, iterate over variables to extract their solution values.
- Implement verification by recomputing the total supply per `(destination, commodity)` and comparing it to the demand parameter.

### Step 4 - Output and Cross-Validate
- Print the total objective value and a filtered list of non-zero allocations (above a tolerance).
- For critical validation, re-solve the same model with a different solver backend (e.g., `CBC` via OR-Tools) and compare objective values to confirm optimality.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (create variables, constraints, objective)

# solve with status / termination checks
status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL:
    objective_value = solver.Objective().Value()
    # Verification loop
    # ...
    print(f"RESULT:{objective_value}")
    # Optional cross-validation with another solver
    # solver2 = pywraplp.Solver.CreateSolver('CBC')
    # ...
elif status == pywraplp.Solver.FEASIBLE:
    objective_value = solver.Objective().Value()
    print(f"RESULT_FEASIBLE:{objective_value}")
else:
    print(f'RESULT_JSON:{{"status": {status}}}')
```

### Common Pitfalls
- Assuming the solver always returns an optimal solution without checking the status code.
- Not using a tolerance when filtering near-zero values for display, which can clutter output.
- Encountering interface issues with certain solvers (e.g., HiGHS); have a fallback solver ready.
