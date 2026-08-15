---
name: Bipartite Assignment with Capacity Constraints
description: |
  Model and solve bipartite assignment problems with integer variables, capacity/demand limits, and linear profit objectives using MILP solvers.

---

# Workflow 1 (Direct Assignment with OR-Tools/SCIP)

## Modeling stage

### Strategy Overview
Model the problem directly using a two-dimensional integer assignment variable for each compatible source-destination pair, applying capacity and demand constraints explicitly.

### Step 1 - Define Compatibility Structure
- Parse input data to create a binary compatibility matrix or list of compatible pairs.
- Filter out invalid indices (e.g., negative values) to prevent model construction errors.
- Use the compatibility structure to define the domain of assignment variables sparsely.

### Step 2 - Create Integer Assignment Variables
- For each compatible pair `(i, j)`, create an integer variable `y[i][j]` with bounds `[0, min(demand_limit[i], capacity[j])]`.
- For incompatible pairs, set the variable to `None` or skip creation to reduce model size.
- Ensure all variables are declared as non-negative integers.

### Step 3 - Formulate Capacity and Demand Constraints
- For each source `i`: Add constraint `sum_{j} y[i][j] <= demand_limit[i]`, summing only over compatible destinations.
- For each destination `j`: Add constraint `sum_{i} y[i][j] <= capacity[j]`, summing only over compatible sources.
- Incompatible pairs are implicitly zero via variable omission.

### Step 4 - Set Linear Profit Objective
- Define the objective as `maximize sum_{i,j} revenue[i] * y[i][j]`.
- The coefficient `revenue[i]` is the per-unit profit from source `i`.

### Formulation Template
```json
{
  "sets": [
    "I: set of sources (e.g., packages)",
    "J: set of destinations (e.g., routes)",
    "E: set of compatible pairs (i,j) where assignment is allowed"
  ],
  "parameters": [
    "demand_limit[i]: maximum units available from source i",
    "capacity[j]: maximum units that can be assigned to destination j",
    "revenue[i]: profit per unit from source i"
  ],
  "decision_variables": [
    "y[i][j] ∈ NonNegativeIntegers, for (i,j) in E: units assigned from i to j"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{(i,j) in E} revenue[i] * y[i][j]"
  },
  "constraints": [
    "for each i in I: sum_{j in J s.t. (i,j) in E} y[i][j] <= demand_limit[i]",
    "for each j in J: sum_{i in I s.t. (i,j) in E} y[i][j] <= capacity[j]"
  ]
}
```

### Common Pitfalls
- Creating variables for all `I x J` pairs, which bloats the model unnecessarily. Always use a sparse representation based on compatibility.
- Forgetting to handle invalid or negative indices in compatibility lists, leading to index errors.
- Setting variable upper bounds larger than the minimum of `demand_limit[i]` and `capacity[j]`, which can increase the solver's search space.

## Solving stage

### Strategy Overview
Solve the MILP model using the SCIP solver via OR-Tools, configuring it for optimality and performing rigorous solution validation.

### Step 1 - Configure Solver and Parameters
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set a time limit: `solver.SetTimeLimit(30000)` (in milliseconds).
- Set the number of threads for parallel processing: `solver.SetNumThreads(4)`.
- Optionally, set SCIP-specific parameters via `solver.SetSolverSpecificParametersAsString()`.

### Step 2 - Solve and Check Status
- Call `solver.Solve()`.
- Verify the status is `OPTIMAL` (not just `FEASIBLE`). For suboptimal solutions, check the best bound and gap.
- If status is not optimal, analyze solver logs or adjust parameters (e.g., increase time limit, tighten tolerances).

### Step 3 - Extract and Validate Solution
- Extract variable values: `y_val[i][j] = y[i][j].solution_value()` if variable exists and is not `None`.
- Compute aggregate statistics: total assigned per source and per destination.
- Validate that all constraints are satisfied (e.g., sums do not exceed limits).
- Calculate capacity utilization (`assigned / capacity`) and demand utilization (`assigned / demand_limit`) to identify bottlenecks.

### Step 4 - Post-Solution Analysis
- Compare the objective value to a theoretical upper bound (e.g., by greedily assigning highest-revenue units ignoring compatibility).
- Check which constraints are binding (tight) to understand the solution structure.
- Log key metrics for debugging and reporting.

### Code Usage
```python
# build model from formulation
import ortools.linear_solver.pywraplp as ort

solver = ort.Solver.CreateSolver("SCIP")
# ... (build variables, constraints, objective as per modeling stage)

# solve with status / termination checks
result_status = solver.Solve()
if result_status == ort.Solver.OPTIMAL:
    total_revenue = solver.Objective().Value()
    best_bound = solver.Objective().BestBound()
    # Validate optimality gap is zero (or acceptable)
    if abs(total_revenue - best_bound) < 1e-6:
        print(f"Optimal solution found: {total_revenue}")
        # Extract and validate solution...
    else:
        print(f"Solution feasible but gap non-zero: {total_revenue}, bound: {best_bound}")
else:
    print(f"Solver did not find optimal solution. Status: {result_status}")
```

### Common Pitfalls
- Assuming a `FEASIBLE` status means optimal; always check for `OPTIMAL` and verify the MIP gap.
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.
- Accessing `.solution_value()` on `None` variables, leading to attribute errors. Always check variable existence first.

# Workflow 2 (Two-Layer Assignment with Pyomo/CBC)

## Modeling stage

### Strategy Overview
Decouple the problem into two layers: a sales decision variable for total units per source and an assignment variable linking sources to destinations, connected by a flow conservation constraint.

### Step 1 - Define Sparse Compatibility Set
- Create a Pyomo Set `model.E` of compatible pairs `(i,j)` from input lists or matrix.
- Filter invalid indices during set construction to maintain data integrity.
- This set defines the domain for the assignment variables sparsely.

### Step 2 - Create Two-Layer Variables
- Define `model.x[i]` as `NonNegativeInteger` representing total units allocated from source `i`.
- Define `model.y[i,j]` as `NonNegativeInteger` for each `(i,j) in model.E`, representing units assigned from `i` to `j`.
- Initialize parameters (`demand_limit`, `capacity`, `revenue`) using dictionaries for clean data integration.

### Step 3 - Link Variables with Flow Conservation
- For each source `i`, add constraint: `sum_{j in J s.t. (i,j) in E} y[i,j] == x[i]`.
- This ensures all allocated units are assigned to compatible destinations.

### Step 4 - Apply Capacity and Demand Limits
- For each destination `j`: `sum_{i in I s.t. (i,j) in E} y[i,j] <= capacity[j]`.
- For each source `i`: `x[i] <= demand_limit[i]`.
- The objective is `maximize sum_{i} revenue[i] * x[i]`.

### Formulation Template
```json
{
  "sets": [
    "I: set of sources",
    "J: set of destinations",
    "E: set of compatible pairs (i,j)"
  ],
  "parameters": [
    "demand_limit[i]: maximum units from source i",
    "capacity[j]: maximum units to destination j",
    "revenue[i]: profit per unit from source i"
  ],
  "decision_variables": [
    "x[i] ∈ NonNegativeIntegers: total units allocated from source i",
    "y[i,j] ∈ NonNegativeIntegers, for (i,j) in E: units assigned from i to j"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in I} revenue[i] * x[i]"
  },
  "constraints": [
    "for each i in I: sum_{j in J s.t. (i,j) in E} y[i,j] == x[i]",
    "for each i in I: x[i] <= demand_limit[i]",
    "for each j in J: sum_{i in I s.t. (i,j) in E} y[i,j] <= capacity[j]"
  ]
}
```

### Common Pitfalls
- Forgetting the flow conservation constraint (`y[i,j]` sum equals `x[i]`), which decouples the variables and leads to incorrect solutions.
- Defining the `E` set incorrectly (e.g., including incompatible pairs), which creates unnecessary variables and constraints.
- Using the same per-unit revenue in the objective for both `x` and `y`, which would double-count profit.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver, configure for optimality, and implement robust solution extraction and validation.

### Step 1 - Instantiate Solver and Set Parameters
- Create solver instance: `solver = pyo.SolverFactory("cbc")`.
- Set solver options: `solver.options["seconds"] = 30` (time limit), `solver.options["ratio"] = 0.0` (optimality gap), `solver.options["threads"] = 4`.
- Pass options via `solve(..., options=...)` or set them globally.

### Step 2 - Solve and Check Termination Conditions
- Execute `results = solver.solve(model, tee=True)` (with `tee=True` for log output).
- Check solver status: `pyo.check_optimal_termination(results)` or inspect `results.solver.status` and `results.solver.termination_condition`.
- Accept `optimal` or `feasible` termination conditions; handle others (e.g., `infeasible`, `maxTimeLimit`) appropriately.

### Step 3 - Extract Solution and Compute Metrics
- Access variable values: `x_val = pyo.value(model.x[i])`, `y_val = pyo.value(model.y[i,j])`.
- Compute total assigned per source and per destination to validate constraints.
- Calculate utilization percentages and compare against limits.

### Step 4 - Analyze and Verify Optimality
- Compute a theoretical upper bound (e.g., sort sources by revenue, fill capacities greedily) to benchmark the solution.
- Identify binding constraints (e.g., destinations at full capacity) to understand the solution structure.
- Use solver logs to confirm presolve reductions, indicating an efficient formulation.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
# ... (define sets, parameters, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimal solution found.")
        # Extract solution...
    elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
        print("Feasible solution found (not proven optimal).")
        # Extract solution, check gap if available...
    else:
        print(f"Solver terminated with condition: {results.solver.termination_condition}")
else:
    print("Solver failed. Status:", results.solver.status)
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal results.
- Accessing variable values before verifying a solution exists, causing `ValueError` or `AttributeError`.
- Ignoring solver logs (`tee=True`), which contain valuable information about presolve reductions and solution progress.
