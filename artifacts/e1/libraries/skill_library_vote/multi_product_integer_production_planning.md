---
name: Multi-Product Integer Production Planning
description: |
  Model and solve linear profit maximization problems with integer production quantities, individual bounds, and a shared resource capacity constraint.
---

# Workflow 1 (OR-Tools / CBC Backend)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (pywraplp) to construct a Mixed-Integer Linear Program (MILP). It directly encodes variable bounds into the variable domain and uses a vectorized approach for constraints and the objective, suitable for straightforward, medium-scale problems.

### Step 1 - Define Data Structures
- Organize problem parameters in parallel lists or arrays indexed by product.
- Store `profit_per_unit`, `resource_consumption_per_unit`, `min_production`, and `max_production` for each product.
- Define the total available `resource_capacity`.

### Step 2 - Instantiate Solver and Variables
- Create a MILP solver instance using `CBC` as the backend.
- For each product, define an integer decision variable using `solver.IntVar(lower_bound, upper_bound, name)`, directly incorporating individual production bounds.

### Step 3 - Formulate Resource Capacity Constraint
- Create a linear constraint: `sum(resource_consumption_per_unit[i] * x[i]) <= resource_capacity`.
- Use `solver.Add()` to add this constraint to the model.

### Step 4 - Set Linear Maximization Objective
- Define the objective as `sum(profit_per_unit[i] * x[i])`.
- Use `objective = solver.Objective()` and `SetCoefficient()` for each variable, then call `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": ["profit_per_unit", "resource_consumption_per_unit", "min_production", "max_production", "resource_capacity"],
  "decision_variables": ["x[product] ∈ NonNegativeIntegers"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[product] * x[product])"
  },
  "constraints": [
    "sum(resource_consumption_per_unit[product] * x[product]) <= resource_capacity",
    "x[product] >= min_production[product] for each product",
    "x[product] <= max_production[product] for each product"
  ]
}
```

### Common Pitfalls
- Forgetting to set the objective sense to maximization, resulting in a default minimization.
- Adding redundant constraints for variable bounds that are already defined in `IntVar`.
- Using `NumVar` instead of `IntVar` for production quantities, which can yield non-integer solutions.

## Solving stage

### Strategy Overview
Solve the model using the configured CBC solver, check for optimal or feasible status, extract and validate the solution, and provide structured outputs. Configure performance settings like time limits for larger instances.

### Step 1 - Configure Solver Parameters
- Set a time limit using `solver.SetTimeLimit(milliseconds)` to prevent excessive runtime.
- Optionally set the number of threads with `solver.SetNumThreads(num)` for parallel processing.

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve()` and capture the result status.
- Verify the status is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE` before proceeding.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value via `solver.Objective().Value()`.
- For each variable, get the integer solution value using `x[i].solution_value()`.
- Compute derived metrics (e.g., total resource used) to verify all constraints are satisfied.

### Step 4 - Output Structured Results
- Print a simple result line (e.g., `RESULT:{objective_value}`) for automated parsing.
- Optionally output a detailed JSON payload containing status, objective, variable values, and constraint utilization.

### Code Usage
```python
import ortools.linear_solver.pywraplp as ortools

# Build model from formulation
solver = ortools.Solver.CreateSolver('CBC')
# ... define variables, constraints, objective as per modeling stage

# Solve with status / termination checks
status = solver.Solve()
if status in (ortools.Solver.OPTIMAL, ortools.Solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    solution = {f'x_{i}': var.solution_value() for i, var in enumerate(x_vars)}
    print(f"RESULT:{obj_val}")
    # Output detailed results...
else:
    print('{"status": "failed", "reason": "infeasible_or_error"}')
```

### Common Pitfalls
- Not checking for `FEASIBLE` status, which may miss good but non-optimal solutions.
- Assuming solution values are integers without explicit casting, though `IntVar` guarantees integrality.
- Neglecting to handle solver failures, leading to crashes when accessing solution values.

# Workflow 2 (Pyomo / Highs or CBC Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to create a structured, scalable Integer Linear Program (ILP). It leverages Pyomo's `Set`, `Param`, and `Var` components for clean separation of data and model, facilitating maintenance and analysis of larger problems.

### Step 1 - Define Abstract Model Structure
- Create a `ConcreteModel()`.
- Define a `Set` for products to index all parameters and variables.
- Declare `Param` components for `profit`, `resource_consumption`, `min_prod`, and `max_prod`, initialized from data dictionaries.

### Step 2 - Declare Integer Decision Variables
- Define a `Var` indexed by the product set with `domain=pyo.NonNegativeIntegers`.
- Optionally, set variable bounds within the `Var` declaration using `bounds=` argument.

### Step 3 - Formulate Objective and Constraints
- Define the objective using `Objective(expr=sum(...), sense=pyo.maximize)`.
- Add the resource capacity constraint as a `Constraint` with expression `sum(resource_consumption[i] * x[i]) <= total_capacity`.
- Individual bounds can be added as separate constraints or embedded in variable bounds.

### Step 4 - Perform Feasibility Pre-check
- Calculate the minimum required resource: `sum(min_prod[i] * resource_consumption[i])`.
- Compare against `total_capacity` to catch trivially infeasible instances early.

### Formulation Template
```json
{
  "sets": ["products"],
  "parameters": ["profit", "resource_consumption", "min_prod", "max_prod", "total_capacity"],
  "decision_variables": ["model.x[product] ∈ NonNegativeIntegers"],
  "objective": {
    "sense": "max",
    "expression": "sum(model.profit[product] * model.x[product])"
  },
  "constraints": [
    "sum(model.resource_consumption[product] * model.x[product]) <= model.total_capacity",
    "model.x[product] >= model.min_prod[product] for each product",
    "model.x[product] <= model.max_prod[product] for each product"
  ]
}
```

### Common Pitfalls
- Using `NonNegativeReals` domain for production quantities, which violates integer requirements.
- Incorrectly indexing parameters or variables, leading to runtime errors.
- Forgetting to set `sense=pyo.maximize` on the objective, defaulting to minimization.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver (e.g., Highs or CBC), robustly check termination status, load solutions only if successful, and implement fallback heuristics or LP relaxation for bound analysis if needed.

### Step 1 - Configure and Execute Solver
- Instantiate a solver via `pyo.SolverFactory("solver_name")` (e.g., "highs" or "cbc").
- Set key options: `time_limit`, `mip_rel_gap=0.0` for exact solutions.

### Step 2 - Robust Solution Loading
- Solve with `load_solutions=False` to separate solving from solution loading.
- Check `SolverStatus.ok` and `TerminationCondition` for optimal or feasible outcomes before loading results.

### Step 3 - Extract and Verify Solution
- Load the solution using `model.solutions.load_from(results)`.
- Extract variable values via `pyo.value(model.x[product])` and compute the objective.
- Validate all constraints programmatically to ensure solution integrity.

### Step 4 - Implement Fallback Strategies
- If the solver fails, apply a greedy heuristic: satisfy minimums, then allocate remaining capacity by highest profit-to-resource ratio.
- For bound analysis, solve the LP relaxation first to obtain an upper bound on profit.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
model.products = pyo.Set(initialize=product_indices)
# ... define parameters, variables, objective, constraints as per modeling stage

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1.0  # Use -1 for default, 0.0 for exact
results = solver.solve(model, load_solutions=False)

status = results.solver.status
term = results.solver.termination_condition
if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    print(f"RESULT:{obj_val}")
    # Output detailed results...
else:
    # Implement fallback heuristic or output failure
    print('{"status": "failed", "reason": "infeasible_or_error"}')
```

### Common Pitfalls
- Loading solutions unconditionally, which can overwrite the model with invalid results on solver failure.
- Setting conflicting solver options (e.g., `threads` on a globally managed scheduler).
- Not verifying that extracted variable values are integers after solving an ILP.
