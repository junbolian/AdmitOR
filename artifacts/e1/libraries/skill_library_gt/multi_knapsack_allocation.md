---
name: Multi-Knapsack Allocation
description: |
  Model and solve integer allocation problems with multiple linear capacity constraints to maximize linear revenue.
---

# Workflow 1 (OR-Tools / SCIP)

## Modeling stage

### Strategy Overview
This workflow uses the OR-Tools MIP solver interface (pywraplp) to build a compact integer linear program. It emphasizes direct variable bounds and a binary consumption matrix for efficient constraint generation, suitable for problems with many items and resources.

### Step 1 - Define Data Structures
- Organize problem data into separate lists or arrays for clarity and reusability.
- Represent resource-item consumption relationships with a binary matrix (e.g., `consumption_matrix[resource][item] == 1`).

### Step 2 - Create Variables with Bounds
- Instantiate integer decision variables (`solver.IntVar`) with lower bound 0 and an upper bound equal to the item's demand limit.
- This embeds simple upper bound constraints directly, reducing the total number of explicit constraints.

### Step 3 - Formulate Capacity Constraints
- For each resource (knapsack), create a linear inequality constraint (`solver.Constraint`).
- Sum the allocations of items that consume the resource, using the binary matrix to filter contributions.

### Step 4 - Define Linear Objective
- Create a maximization objective (`solver.Objective`).
- Set coefficients equal to the revenue per unit for each corresponding decision variable.

### Formulation Template
```json
{
  "sets": ["Items", "Resources"],
  "parameters": {
    "revenue": {"type": "float", "index": "Items"},
    "demand_limit": {"type": "int", "index": "Items"},
    "capacity": {"type": "float", "index": "Resources"},
    "consumption": {"type": "binary", "index": ["Resources", "Items"]}
  },
  "decision_variables": {
    "x": {"type": "integer", "index": "Items", "bounds": "[0, demand_limit[i]]"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in Items)"
  },
  "constraints": {
    "capacity_constraint": {
      "expression": "sum(consumption[r][i] * x[i] for i in Items) <= capacity[r]",
      "index": "Resources"
    }
  }
}
```

### Common Pitfalls
- Forgetting to convert `solution_value()` to an integer (`int()`) for integer variables, leading to type inconsistencies.
- Using general constraints for simple upper bounds instead of variable bounds, which unnecessarily increases model size.
- Not verifying the solver status is `OPTIMAL` before extracting results, potentially accepting suboptimal or infeasible solutions.

## Solving stage

### Strategy Overview
This stage configures the SCIP solver via OR-Tools, solves the model, rigorously checks the solution status, and validates the results against the original problem constraints.

### Step 1 - Configure Solver
- Instantiate the SCIP solver: `pywraplp.Solver.CreateSolver("SCIP")`.
- Set practical limits: a time limit (e.g., `SetTimeLimit(30000)`) and number of threads (e.g., `SetNumThreads(4)`).

### Step 2 - Solve and Check Status
- Execute `solver.Solve()` and capture the status.
- Proceed only if `status == pywraplp.Solver.OPTIMAL` to ensure an optimal solution was found and proven.

### Step 3 - Extract and Validate Solution
- Extract variable values using `x[i].solution_value()` and convert to integers.
- Independently compute resource usage and check against capacities and demand limits to validate the solution's feasibility.

### Step 4 - Analyze Solution Structure
- Identify binding constraints where resource usage equals capacity.
- Identify variables at their upper bounds to understand the solution's active limits.

### Code Usage
```python
# 1. Solver Setup
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# 2. Build Model (refer to Modeling stage steps)
# ... [Variable, constraint, and objective creation code] ...

# 3. Solve
status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL:
    # 4. Extract Solution
    solution = [int(x[i].solution_value()) for i in range(n_items)]
    total_value = objective.Value()
    # 5. Validate
    # ... [Recalculate usage and compare to constraints] ...
else:
    # Handle non-optimal status (e.g., FEASIBLE, INFEASIBLE, UNBOUNDED)
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Assuming a `FEASIBLE` status is sufficient without checking optimality, potentially accepting a suboptimal solution.
- Neglecting to validate the solver's output, which may contain small numerical violations of integer or capacity constraints.
- Setting an overly aggressive time limit or optimality gap that prevents the solver from proving optimality.

# Workflow 2 (Pyomo / HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to create a declarative model, separating data (via `Set` and `Param`) from structure. It is well-suited for complex, data-driven problems and integrates seamlessly with various solvers like HiGHS.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for indexing (e.g., `model.P` for items, `model.L` for resources).
- Declare `Param` objects for all input data (revenue, demand, capacity, consumption mapping).

### Step 2 - Create Decision Variables
- Define integer decision variables (`Var`) indexed by the appropriate set.
- Apply upper bounds directly using the `bounds` argument (e.g., `(0, model.demand[p])`).

### Step 3 - Build Capacity Constraints
- Use a pre-defined mapping (e.g., `model.packages_in_leg[l]`) to create constraints.
- For each resource, sum the allocations of consuming items and enforce the capacity limit.

### Step 4 - Define Maximization Objective
- Construct the objective as a linear expression of revenues and variables.
- Set the sense to `maximize`.

### Formulation Template
```json
{
  "sets": ["P", "L"],
  "parameters": {
    "revenue": {"type": "pyo.Param", "domain": "pyo.Reals", "index": "P"},
    "demand": {"type": "pyo.Param", "domain": "pyo.NonNegativeIntegers", "index": "P"},
    "capacity": {"type": "pyo.Param", "domain": "pyo.NonNegativeReals", "index": "L"},
    "consumes": {"type": "pyo.Set", "index": ["L", "P"]}
  },
  "decision_variables": {
    "x": {"type": "pyo.Var", "domain": "pyo.NonNegativeIntegers", "index": "P", "bounds": "(0, demand[p])"}
  },
  "objective": {
    "sense": "maximize",
    "expression": "sum(revenue[p] * x[p] for p in P)"
  },
  "constraints": {
    "capacity_constraint": {
      "expression": "sum(x[p] for p in consumes[l]) <= capacity[l]",
      "index": "L"
    }
  }
}
```

### Common Pitfalls
- Using Python lists/dicts directly within Pyomo rules instead of Pyomo `Param` objects, which breaks solver communication.
- Defining constraints over entire sets without filtering, leading to incorrect sums for sparse consumption relationships.
- Not initializing `Param` dictionaries before model instantiation, causing initialization errors.

## Solving stage

### Strategy Overview
This stage uses the HiGHS solver via Pyomo's `SolverFactory`, configures it for rigorous MILP solving, checks termination conditions, and performs post-solution validation and analysis.

### Step 1 - Instantiate and Configure Solver
- Create a solver object: `SolverFactory("highs")`.
- Set solver options: `mip_rel_gap=0` (or a small tolerance) and a `time_limit` for practical termination.

### Step 2 - Solve and Interpret Results
- Execute `solver.solve(model)`.
- Check both `solver.status` (should be `ok`) and `model.solutions[0].termination_condition` (prefer `optimal` or accept `feasible`).

### Step 3 - Process Solution Values
- Extract variable values using `pyo.value(model.x[p])`.
- Round to the nearest integer and cast to `int` for integer variables.

### Step 4 - Validate and Analyze
- Programmatically recompute resource usage to verify all constraints are satisfied within a small tolerance.
- Identify binding constraints and variables at their bounds to interpret the solution.

### Code Usage
```python
# 1. Solver Setup
solver = SolverFactory('highs')
solver_options = {'time_limit': 30, 'mip_rel_gap': 0.0}
# 2. Build Model (refer to Modeling stage steps)
# ... [Pyomo model creation code] ...
# 3. Solve
results = solver.solve(model, options=solver_options)
# 4. Check Status
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    # 5. Extract and Process
    solution = {p: int(round(pyo.value(model.x[p]))) for p in model.P}
    # 6. Validate and Analyze
    # ... [Recalculate usage and check constraints] ...
else:
    # Handle other termination conditions (e.g., maxTimeLimit, feasible)
    print(f"Solver terminated with: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `solver.status` (process status) with `termination_condition` (solution quality), leading to misinterpretation of results.
- Not rounding `pyo.value()` outputs for integer variables, which may be slightly non-integer due to solver tolerances.
- Failing to set `mip_rel_gap` or `time_limit`, allowing the solver to run indefinitely or stop with a large optimality gap.
