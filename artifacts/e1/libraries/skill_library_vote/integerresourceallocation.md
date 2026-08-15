---
name: IntegerResourceAllocation
description: |
  Model and solve integer production planning problems with linear profit maximization, resource capacity constraints, and individual upper bounds using either OR-Tools or Pyomo.

---

# Workflow 1 (OR-Tools with SCIP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to build a Mixed-Integer Programming (MIP) model. It is suited for problems where decision variables are non-negative integers, and constraints are linear. The model is constructed using parallel arrays for data, and variable bounds are set explicitly for efficiency.

### Step 1 - Define Data Structures
- Store problem data in parallel lists or dictionaries, indexed by a common set of item identifiers.
- Define parameters: `profit_per_unit`, `resource_consumption_per_unit`, `individual_upper_limit`, and a scalar `total_resource_capacity`.

### Step 2 - Create Integer Variables
- Instantiate a solver object using `pywraplp.Solver.CreateSolver("SCIP")`.
- For each item, create a non-negative integer variable using `solver.IntVar(lower_bound, upper_bound, name)`. Use `0` as the lower bound and the item's `individual_upper_limit` as the upper bound.

### Step 3 - Formulate Objective Function
- Construct a linear expression for total profit: `sum(profit_per_unit[i] * variable[i] for i in items)`.
- Set the objective to maximize this expression using `solver.Maximize()`.

### Step 4 - Add Linear Constraints
- For the shared resource constraint, create a linear inequality: `sum(resource_consumption_per_unit[i] * variable[i] for i in items) <= total_resource_capacity`.
- Add this constraint to the solver using `solver.Add()`.

### Formulation Template
```json
{
  "sets": ["items"],
  "parameters": {
    "profit_per_unit": {"type": "float", "index": "items"},
    "resource_consumption_per_unit": {"type": "float", "index": "items"},
    "individual_upper_limit": {"type": "int", "index": "items"},
    "total_resource_capacity": {"type": "float"}
  },
  "decision_variables": {
    "x": {"type": "nonnegative_integer", "index": "items"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[i] * x[i] for i in items)"
  },
  "constraints": [
    {
      "name": "resource_capacity",
      "expression": "sum(resource_consumption_per_unit[i] * x[i] for i in items) <= total_resource_capacity"
    }
  ]
}
```

### Common Pitfalls
- Forgetting to set variable upper bounds, forcing the solver to use default large bounds which can slow down the search.
- Using `solver.NumVar` instead of `solver.IntVar`, which would create continuous variables and yield a non-integer solution.
- Not using list comprehensions for summations, leading to verbose and error-prone loop-based code.

## Solving stage

### Strategy Overview
Solve the MIP model using the SCIP solver backend. Configure performance parameters, execute the solve, rigorously check the solution status, and extract results including primal values, dual values, and derived metrics.

### Step 1 - Configure Solver Parameters
- Set a time limit using `solver.SetTimeLimit(ms)` to ensure termination.
- Optionally, set the number of threads with `solver.SetNumThreads(n)` for parallel processing.

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: verify `status` is either `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`. If not, handle the infeasible or error state appropriately.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value using `solver.Objective().Value()`.
- For each variable, get the solution value using `variable.solution_value()` and convert to integer.
- Compute derived metrics (e.g., total resource used) from the solution to validate constraint satisfaction.

### Step 4 - Perform Sensitivity and Analysis
- Retrieve the dual value (shadow price) of the resource capacity constraint using `constraint.DualValue()` to understand its marginal value.
- Calculate efficiency ratios (`profit_per_unit[i] / resource_consumption_per_unit[i]`) to analyze the solution's prioritization logic.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (variable creation, objective, constraints)
solver.SetTimeLimit(30000)  # 30 seconds

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    solution = {var.name(): int(var.solution_value()) for var in solver.variables()}
    # ... (extract duals, compute metrics)
else:
    # Handle no solution found
    print("Solve failed.")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Interpreting shadow prices from integer problems without caution, as their meaning can differ from linear programming.
- Forgetting to convert `variable.solution_value()` to an integer, potentially leading to float values for integer variables.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to construct an abstract or concrete model, defining sets, parameters, variables, objectives, and constraints in a structured, declarative style. It is solved using external solvers like HiGHS or CBC, offering flexibility and integration with the broader Pyomo ecosystem.

### Step 1 - Define Model and Sets
- Create a `pyo.ConcreteModel()`.
- Define a Pyomo `Set` to represent the items, e.g., `model.I = pyo.Set(initialize=items_list)`.

### Step 2 - Declare Parameters
- Store input data in Python dictionaries.
- Map them to Pyomo `Param` objects, e.g., `model.profit = pyo.Param(model.I, initialize=profit_dict)`.
- Define scalar parameters like `model.total_capacity = pyo.Param(initialize=capacity_value)`.

### Step 3 - Create Integer Variables
- Define non-negative integer decision variables indexed by the set: `model.x = pyo.Var(model.I, domain=pyo.NonNegativeIntegers, bounds=(0, upper_limit_dict))`.

### Step 4 - Formulate Objective and Constraints
- Set the objective to maximize total profit: `model.obj = pyo.Objective(expr=sum(model.profit[i] * model.x[i] for i in model.I), sense=pyo.maximize)`.
- Add the resource capacity constraint: `model.resource_constraint = pyo.Constraint(expr=sum(model.resource_use[i] * model.x[i] for i in model.I) <= model.total_capacity)`.
- Individual upper bounds are typically handled via variable bounds defined in Step 3.

### Formulation Template
```json
{
  "sets": ["I"],
  "parameters": {
    "profit": {"type": "float", "index": "I"},
    "resource_use": {"type": "float", "index": "I"},
    "total_capacity": {"type": "float"}
  },
  "decision_variables": {
    "x": {"type": "nonnegative_integer", "index": "I", "bounds": "(0, upper_limit)"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    {
      "name": "resource_constraint",
      "expression": "sum(resource_use[i] * x[i] for i in I) <= total_capacity"
    }
  ]
}
```

### Common Pitfalls
- Using Pyomo reserved keywords (e.g., 'items', 'sum', 'model') as set or variable names, causing conflicts.
- Forgetting to initialize parameters before model instantiation in a ConcreteModel, leading to build errors.
- Defining individual upper bound constraints explicitly when they are already enforced via variable bounds, creating redundant constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MIP solver (HiGHS or CBC). Set solver options for performance, execute the solve, check termination conditions, and extract integer solutions with proper type conversion.

### Step 1 - Configure and Execute Solver
- Instantiate a solver object: `solver = pyo.SolverFactory("highs")` or `solver = pyo.SolverFactory("cbc")`.
- Set key options: `solver.options['time_limit'] = seconds`, `solver.options['mip_rel_gap'] = 0.0` for exact solution, and `solver.options['threads'] = n`.

### Step 2 - Solve and Verify Status
- Execute `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` equals `SolverStatus.ok`.
- Verify `results.solver.termination_condition` is either `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract and Process Results
- Retrieve the objective value: `objective_value = float(pyo.value(model.obj))`.
- Extract integer variable values: `solution = {i: int(pyo.value(model.x[i])) for i in model.I}`.
- Compute derived metrics (e.g., total resource used) for validation and reporting.

### Step 4 - Output Standardization
- Format the final objective value in a simple, parseable string (e.g., `RESULT:{objective_value}`).
- Optionally, output a detailed solution breakdown for human inspection.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, parameters, variables, objective, constraints)
solver = pyo.SolverFactory("highs")
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0

# solve with status / termination checks
results = solver.solve(model, tee=False)
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    objective_value = float(pyo.value(model.obj))
    solution = {i: int(pyo.value(model.x[i])) for i in model.I}
    # ... (compute metrics)
else:
    # Handle solve failure
    print("Solve failed.")
```

### Common Pitfalls
- Not importing `SolverStatus` and `TerminationCondition` for status checks.
- Using `pyo.value()` on variables without checking if a solution exists first.
- Forgetting to convert `pyo.value(model.x[i])` to an `int`, which returns a float and may cause type issues downstream.
