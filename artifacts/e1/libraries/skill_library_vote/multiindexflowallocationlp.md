---
name: MultiIndexFlowAllocationLP
description: |
  Model and solve multi-source, multi-product, multi-destination allocation problems with linear profit maximization and exact demand satisfaction using continuous flow variables.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define a structured, index-based Linear Programming (LP) model. It is well-suited for problems where data is organized in sets and parameters, and leverages open-source solvers like HiGHS or CBC for solution.

### Step 1 - Define Core Sets
- Identify and define the three fundamental index sets: sources (e.g., companies), products, and destinations (e.g., markets).
- Use Pyomo `Set` objects to initialize these sets, ensuring they are iterable and can be used to index parameters and variables.
- Example: `model.sources = pyo.Set(initialize=sources_list)`

### Step 2 - Declare Parameters
- Organize input data into Pyomo `Param` objects indexed over the relevant sets.
- Map demand data to a parameter indexed by `(product, destination)`.
- Map profit/cost coefficients to a parameter indexed by `(source, product, destination)`.
- Use a lambda function or dictionary for initialization to handle missing keys gracefully.

### Step 3 - Create Decision Variables
- Define the primary flow variable `x[source, product, destination]` representing the allocation quantity.
- Specify the domain as `pyo.NonNegativeReals` to enforce non-negativity and continuity.
- Use descriptive variable names that reflect the multi-dimensional flow.

### Step 4 - Formulate Objective Function
- Construct a linear objective to maximize total profit (or minimize total cost).
- Sum over all indices: `sum(profit[s,p,d] * x[s,p,d] for s,p,d)`.
- Assign the expression to a Pyomo `Objective` object with the appropriate sense (`maximize` or `minimize`).

### Step 5 - Add Demand Constraints
- For each `(product, destination)` pair, create a linear equality constraint.
- The left-hand side is the sum of flows from all sources for that product-destination pair.
- The right-hand side is the exact demand parameter value.
- Implement using a Pyomo `Constraint` with a rule function indexed over products and destinations.

### Formulation Template
```json
{
  "sets": ["sources", "products", "destinations"],
  "parameters": [
    {"name": "demand", "indices": ["products", "destinations"]},
    {"name": "profit", "indices": ["sources", "products", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "indices": ["sources", "products", "destinations"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s,p,d] * x[s,p,d] for all s,p,d)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "indices": ["products", "destinations"], "expression": "sum(x[s,p,d] for all s) == demand[p,d]"}
  ]
}
```

### Common Pitfalls
- Using the same variable name for a model component and a loop iterator, causing `UnboundLocalError`.
- Forgetting to initialize all required keys in parameter dictionaries, leading to missing data errors.
- Not verifying that the sum over sources in the demand constraint matches the parameter's indexing order.

## Solving stage

### Strategy Overview
This stage focuses on solving the Pyomo model using a configured LP solver (HiGHS or CBC), performing rigorous solution status checks, and extracting/verifying results programmatically.

### Step 1 - Instantiate Solver with Options
- Create a solver object using `SolverFactory("solver_name")` (e.g., `"highs"` or `"cbc"`).
- Set practical solver options: `time_limit`, `threads` for parallelism, and optimality tolerance if needed.
- Example: `solver.options["seconds"] = 30`

### Step 2 - Solve and Capture Results
- Execute the solve command: `results = solver.solve(model, tee=False)`.
- Capture the solver termination condition and status from the results object.
- Key attributes: `results.solver.termination_condition`, `results.solver.status`.

### Step 3 - Check Solution Status
- Verify the solve was successful before extracting values.
- Condition: `status == SolverStatus.ok` and `termination_condition` is `optimal` or `feasible`.
- If not met, handle the failure (e.g., log error, try different solver settings).

### Step 4 - Extract and Validate Solution
- Retrieve the objective value: `float(pyo.value(model.obj))`.
- Iterate through decision variables to collect non-zero values (use a small epsilon, e.g., `1e-6`).
- Optionally, recompute constraint left-hand sides to verify demand satisfaction numerically.

### Step 5 - Output Structured Results
- Print the objective value in a consistent, parseable format (e.g., `RESULT: {value}`).
- Log key allocation details (non-zero flows) for verification and insight.
- Include solver statistics (solve time, status) for diagnostics.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (assumes model is defined as per Modeling stage)
model = build_allocation_model(sources, products, destinations, demand_data, profit_data)

# Configure and solve
solver = pyo.SolverFactory("highs")  # or "cbc"
solver.options["time_limit"] = 30
solver.options["threads"] = 4
results = solver.solve(model)

# Check status
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = float(pyo.value(model.obj))
    print(f"RESULT: {obj_val}")
    # Extract variable values
    for idx in model.x.index_set():
        val = pyo.value(model.x[idx])
        if val > 1e-6:
            print(f"Flow {idx}: {val}")
else:
    print(f"Solver failed: Status={status}, Termination={term}")
```

### Common Pitfalls
- Attempting to access variable values (`pyo.value`) before confirming a successful solve, leading to errors.
- Not using an epsilon threshold when checking for non-zero flows, causing excessive output from near-zero values.
- Omitting the `float()` cast on the objective value, which may leave it as a Pyomo expression type.

# Workflow 2 (OR-Tools with GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`GLOP`) for a more procedural, API-driven modeling style. It is efficient for problems where variables and constraints are built via explicit loops, and is ideal for prototyping or integration into applications without a separate modeling language.

### Step 1 - Initialize Solver and Data Structures
- Create a linear solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Organize input data (profit, demand) into nested dictionaries or lists indexed by `(source, product, destination)` and `(product, destination)` respectively.
- Pre-compute dimensions (number of sources, products, destinations) for loop control.

### Step 2 - Create Decision Variables
- Use nested loops over all index combinations to create variables.
- Call `solver.NumVar(lb, ub, name)` with `lb=0` and `ub=solver.infinity()` for non-negative continuous variables.
- Store variables in a dictionary with tuple keys `(s, p, d)` for easy access when building constraints and objective.

### Step 3 - Build Demand Constraints
- For each `(product, destination)` pair, create a linear constraint with exact equality bounds.
- Use `solver.Constraint(rhs, rhs)` where `rhs = demand[p, d]`.
- Within the loop over sources, add the contribution: `constraint.SetCoefficient(x[(s, p, d)], 1)`.

### Step 4 - Set Objective Function
- Initialize the objective: `objective = solver.Objective()`.
- Set the optimization sense: `objective.SetMaximization()` (or `SetMinimization()`).
- Iterate over all variables, setting each coefficient to the corresponding profit value: `objective.SetCoefficient(var, profit[s,p,d])`.

### Step 5 - Finalize Model
- The model is implicitly finalized after adding all variables, constraints, and the objective.
- No explicit "build" call is required in OR-Tools before solving.

### Formulation Template
```json
{
  "sets": ["sources", "products", "destinations"],
  "parameters": [
    {"name": "demand", "indices": ["products", "destinations"]},
    {"name": "profit", "indices": ["sources", "products", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "indices": ["sources", "products", "destinations"], "domain": "Continuous >= 0"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s,p,d] * x[s,p,d] for all s,p,d)"
  },
  "constraints": [
    {"name": "demand", "indices": ["products", "destinations"], "expression": "sum(x[s,p,d] for all s) == demand[p,d]"}
  ]
}
```

### Common Pitfalls
- Inconsistent indexing between the variable dictionary and parameter dictionaries, leading to incorrect coefficient assignment.
- Forgetting to set the objective sense, defaulting to minimization.
- Creating constraints with incorrect bounds (not using the same value for lower and upper bound for an equality).

## Solving stage

### Strategy Overview
This stage involves invoking the OR-Tools solver, checking the result status, extracting the solution, and performing verification checks. The focus is on the solver's native result codes and efficient value retrieval.

### Step 1 - Invoke Solver
- Call `solver.Solve()` to execute the optimization.
- The method returns a status code (e.g., `pywraplp.Solver.OPTIMAL`).

### Step 2 - Interpret Solver Result
- Check the result status against the solver's enumerated constants.
- Primary success codes: `OPTIMAL` or `FEASIBLE`.
- Handle failure codes (`INFEASIBLE`, `UNBOUNDED`, `ABNORMAL`) with appropriate error messages or fallbacks.

### Step 3 - Extract Objective and Variable Values
- If successful, get the objective value: `solver.Objective().Value()`.
- Iterate through the variable dictionary, retrieving each variable's solution value with `.solution_value()`.
- Apply a small tolerance (e.g., `1e-6`) to filter and report only meaningful flows.

### Step 4 - Verify Constraint Satisfaction
- For each demand constraint, recompute the sum of solution values from all sources.
- Compare to the original demand parameter, checking the absolute difference is within a numerical tolerance (e.g., `1e-4`).
- Log any significant violations for debugging.

### Step 5 - Report Results
- Output the objective value in a clear, potentially machine-parsable format.
- Optionally, print a summary of the allocation pattern (non-zero flows).
- Include solver statistics like wall time or iteration count if needed.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')

# Assume variables 'x_var' dict and data structures are built as per Modeling stage
# ...

# Solve
result_status = solver.Solve()

# Check result
if result_status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    obj_val = solver.Objective().Value()
    print(f"RESULT: {obj_val}")
    
    # Verify constraints
    tolerance = 1e-4
    for p in products:
        for d in destinations:
            lhs = sum(x_var[(s, p, d)].solution_value() for s in sources)
            if abs(lhs - demand[(p, d)]) > tolerance:
                print(f"Warning: Demand mismatch for ({p},{d}): {lhs} vs {demand[(p,d)]}")
    
    # Print non-zero flows
    for idx, var in x_var.items():
        val = var.solution_value()
        if val > 1e-6:
            print(f"Flow {idx}: {val}")
else:
    print(f"Solver did not find an optimal solution. Status: {result_status}")
```

### Common Pitfalls
- Misinterpreting the solver status code (e.g., treating `FEASIBLE` as a failure).
- Not using `.solution_value()` on variables, mistakenly trying to print the variable object itself.
- Performing verification checks with an overly strict tolerance, flagging acceptable numerical noise as errors.
