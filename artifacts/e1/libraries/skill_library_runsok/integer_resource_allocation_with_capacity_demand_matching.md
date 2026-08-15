---
name: Integer Resource Allocation with Capacity-Demand Matching
description: |
  Model and solve integer linear programs for resource allocation where discrete units of multiple resource types are assigned to tasks to meet demand at minimum cost, subject to resource availability and capacity-weighted contribution constraints.
---

# Workflow 1 (OR-Tools MIP with SCIP/CBC)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using the OR-Tools Python wrapper. This approach is procedural, building the model via direct solver API calls, which is efficient for problems with clear matrix structures and benefits from fine-grained solver control.

### Step 1 - Define Data Structures
- Organize problem dimensions: create lists for resource types `I` and tasks `J`.
- Store parameters in 2D arrays (lists of lists) for cost `cost[i][j]` and capacity contribution `cap[i][j]`.
- Store resource availability `avail[i]` and task demand `demand[j]` as 1D lists.

### Step 2 - Create Integer Decision Variables
- Instantiate a solver object (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Create a 2D array of integer variables `x[i][j]` using `solver.IntVar(lb, ub, name)`.
- Set lower bound (`lb`) to 0 and upper bound (`ub`) to the resource's availability or `solver.infinity()`.

### Step 3 - Formulate Resource Capacity Constraints
- For each resource `i` in `I`, create a linear constraint: `sum_{j in J} x[i][j] <= avail[i]`.
- Use `solver.Constraint(0, avail[i])` and `SetCoefficient` to build the sum.

### Step 4 - Formulate Demand Satisfaction Constraints
- For each task `j` in `J`, create a linear constraint: `sum_{i in I} cap[i][j] * x[i][j] >= demand[j]`.
- Use `solver.Constraint(demand[j], solver.infinity())` and `SetCoefficient` with the capacity coefficient.

### Step 5 - Define Linear Cost Objective
- Create the objective expression: `sum_{i in I} sum_{j in J} cost[i][j] * x[i][j]`.
- Use `solver.Objective()` and `SetCoefficient` for each variable, then call `SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["I (resource types)", "J (tasks)"],
  "parameters": [
    "avail[i] ∈ ℝ⁺ for i in I",
    "demand[j] ∈ ℝ⁺ for j in J",
    "cap[i][j] ∈ ℝ⁺ for i in I, j in J",
    "cost[i][j] ∈ ℝ⁺ for i in I, j in J"
  ],
  "decision_variables": ["x[i][j] ∈ ℤ⁺ for i in I, j in J"],
  "objective": {
    "sense": "min",
    "expression": "∑_{i∈I} ∑_{j∈J} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "∑_{j∈J} x[i][j] ≤ avail[i] for all i ∈ I",
    "∑_{i∈I} cap[i][j] * x[i][j] ≥ demand[j] for all j ∈ J"
  ]
}
```

### Common Pitfalls
- Using floating-point values for integer variable bounds; ensure `lb` and `ub` are integers.
- Inconsistent matrix dimensions: verify `cost` and `cap` have shape `|I| x |J|`.
- Forgetting to set the objective sense to minimization.

## Solving stage

### Strategy Overview
Solve the built MIP model using SCIP or CBC backend, configure performance parameters, and rigorously check solver status before extracting and validating the solution.

### Step 1 - Configure Solver Performance
- Set a time limit using `solver.SetTimeLimit(milliseconds)`.
- Enable parallel processing with `solver.SetNumThreads(num_threads)`.
- For exact optimality, set the MIP gap tolerance to zero via solver-specific parameters if needed.

### Step 2 - Execute Solve and Check Status
- Call `status = solver.Solve()`.
- Verify the status is `OPTIMAL` or `FEASIBLE` before proceeding. Do not proceed on `UNKNOWN` or `INFEASIBLE`.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value using `objective.Value()`.
- Iterate over all `x[i][j]` and extract non-zero assignments using `.solution_value()`.
- Programmatically verify both constraint families: sum of assignments per resource ≤ availability, and weighted sum per task ≥ demand.

### Step 4 - Report Structured Results
- Compile a summary of total cost, resource utilization rates, and task coverage.
- Output non-zero assignments in a clear format (e.g., list of dictionaries) for downstream use.

### Code Usage
```python
# Example using OR-Tools (conceptual)
from ortools.linear_solver import pywraplp

# 1. Create solver
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# 2. Build model (variables, constraints, objective) as per Modeling stage

# 3. Solve
status = solver.Solve()

# 4. Check status and extract results
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    assignments = []
    for i in range(num_resources):
        for j in range(num_tasks):
            val = x[i][j].solution_value()
            if val > 0.5:  # Threshold for integer variables
                assignments.append({"resource": i, "task": j, "count": int(val)})
    # ... validation and reporting
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing `.solution_value()`, which can cause runtime errors.
- Assuming `FEASIBLE` implies optimality; distinguish between optimal and feasible-but-suboptimal results.
- Neglecting to verify the solution against original constraints, risking acceptance of numerically invalid results.

# Workflow 2 (Pyomo with CBC/Highs)

## Modeling stage

### Strategy Overview
Formulate the problem using Pyomo's abstract or concrete modeling framework. This declarative approach separates model definition from solver interaction, promoting clarity, maintainability, and easier integration with Pyomo's ecosystem and solver managers.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for resource types `model.I` and tasks `model.J`.
- Declare `Param` objects for `availability`, `demand`, `capacity`, and `cost`, indexed over the appropriate sets.

### Step 2 - Declare Integer Decision Variables
- Create a Pyomo `Var` object `model.x`, indexed by `model.I` and `model.J`.
- Set the domain to `pyo.NonNegativeIntegers` to enforce non-negative integer assignments.

### Step 3 - Construct Capacity Constraints via Rules
- Define a `Constraint` rule for resource availability: `sum(model.x[i,j] for j in model.J) <= model.availability[i]`.
- Use Pyomo's rule-based constraint definition for clean separation of logic.

### Step 4 - Construct Demand Constraints via Rules
- Define a `Constraint` rule for demand satisfaction: `sum(model.capacity[i,j] * model.x[i,j] for i in model.I) >= model.demand[j]`.

### Step 5 - Define the Minimization Objective
- Create an `Objective` with expression `sum(model.cost[i,j] * model.x[i,j] for i in model.I for j in model.J)` and `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["I (resource types)", "J (tasks)"],
  "parameters": [
    "availability[i] ∈ ℝ⁺ for i in I",
    "demand[j] ∈ ℝ⁺ for j in J",
    "capacity[i,j] ∈ ℝ⁺ for i in I, j in J",
    "cost[i,j] ∈ ℝ⁺ for i in I, j in J"
  ],
  "decision_variables": ["x[i,j] ∈ ℤ⁺ for i in I, j in J"],
  "objective": {
    "sense": "min",
    "expression": "∑_{i∈I} ∑_{j∈J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "∑_{j∈J} x[i,j] ≤ availability[i] for all i ∈ I",
    "∑_{i∈I} capacity[i,j] * x[i,j] ≥ demand[j] for all j ∈ J"
  ]
}
```

### Common Pitfalls
- Using Python loops inside Pyomo expressions instead of generator expressions or `sum()`.
- Forgetting to initialize all parameters before solving, leading to `KeyError` or uninitialized values.
- Mixing 0-based Python indexing with 1-based mathematical notation without clear mapping.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver like CBC or HiGHS via `SolverFactory`. Configure solver options, check termination conditions rigorously, and load the solution only after confirming success.

### Step 1 - Instantiate and Configure Solver
- Create solver object: `solver = pyo.SolverFactory("cbc")`.
- Set key options: time limit (`seconds`), optimality gap (`ratio`), and threads (`threads`).

### Step 2 - Solve with Robust Status Checking
- Execute `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `optimal` or `feasible`. Do not proceed on `unknown` or `infeasible`.

### Step 3 - Load and Extract Solution
- If status checks pass, load the solution into the model.
- Iterate over `model.x` to retrieve values using `pyo.value(model.x[i,j])`.
- Apply a small threshold (e.g., `> 0.5`) to filter non-zero integer assignments, guarding against floating-point precision.

### Step 4 - Perform Post-Solution Validation
- Recalculate total usage per resource and total capacity per task from the extracted solution.
- Compare against original parameters to verify all constraints are satisfied.
- Recompute the objective value independently as a sanity check.

### Code Usage
```python
# Example using Pyomo (conceptual)
import pyomo.environ as pyo

# 1. Build Concrete Model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_resources))
model.J = pyo.Set(initialize=range(num_tasks))
# ... define Parameters, Variable model.x, Objective, Constraints as per Modeling stage

# 2. Solve
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False)

# 3. Check status and termination
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    # 4. Extract and validate
    total_cost = pyo.value(model.obj)
    assignments = []
    for i in model.I:
        for j in model.J:
            val = pyo.value(model.x[i,j])
            if val > 0.5:
                assignments.append({"resource": i, "task": j, "count": int(round(val))})
    # ... validation logic
else:
    print(f"Solver failed: {results.solver.status}, {results.solver.termination_condition}")
```

### Common Pitfalls
- Loading solutions without checking termination condition, potentially loading an invalid or empty solution.
- Setting invalid solver option values (e.g., negative gap tolerance) causing solver errors.
- Not using `pyo.value()` to extract variable values, leading to Pyomo expression objects instead of numbers.
