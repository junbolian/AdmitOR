---
name: Fixed-Charge Network Flow Modeling and Solving
description: |
  Model and solve supply chain, logistics, or network design problems with fixed connection costs and per-unit flow costs using mixed-integer linear programming.
---

# Workflow 1 (Pyomo with Commercial/Open-Source MILP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to build a clean, declarative model of the fixed-charge network flow problem. It is designed for use with high-performance MILP solvers like Gurobi, CPLEX, or open-source alternatives like HiGHS, providing a balance of expressiveness and solving power.

### Step 1 - Define Sets and Parameters
- Define a set of nodes (e.g., `model.N`) representing locations like facilities or hubs.
- Define a set of directed arcs (e.g., `model.A`) as a `pyo.Set(dimen=2)` initialized from a list of tuples `(i,j)`.
- Create Pyomo `Param` objects for node supply/demand (`supply[i]`), arc fixed costs (`fixed_cost[i,j]`), arc variable costs (`variable_cost[i,j]`), and arc capacities (`capacity[i,j]`).

### Step 2 - Create Decision Variables
- Create binary variables `model.y[i,j]` for arc activation decisions (`domain=pyo.Binary`).
- Create continuous, non-negative flow variables `model.x[i,j]` for material amounts (`domain=pyo.NonNegativeReals`).

### Step 3 - Formulate Objective Function
- Define the objective to minimize total cost: `sum(fixed_cost[i,j] * y[i,j] + variable_cost[i,j] * x[i,j] for (i,j) in model.A)`.

### Step 4 - Implement Flow Conservation Constraints
- For each node `i`, create a constraint where the total outflow minus total inflow equals the net supply: `sum(x[i,j] for j if (i,j) in A) - sum(x[j,i] for j if (j,i) in A) == supply[i]`. Use precomputed incoming/outgoing arc lists for efficiency.

### Step 5 - Link Flow to Activation via Capacity Constraints
- For each arc `(i,j)`, add the constraint `x[i,j] <= capacity[i,j] * y[i,j]`. This enforces that flow is zero if the connection is not active and respects the capacity limit.

### Formulation Template
```json
{
  "sets": ["N (nodes)", "A (arcs)"],
  "parameters": ["supply[N]", "fixed_cost[A]", "variable_cost[A]", "capacity[A]"],
  "decision_variables": ["y[A] (binary)", "x[A] (continuous, >=0)"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i,j] * y[i,j] + variable_cost[i,j] * x[i,j] for (i,j) in A)"
  },
  "constraints": [
    "flow_conservation[i]: sum(x[i,j] for j if (i,j) in A) - sum(x[j,i] for j if (j,i) in A) == supply[i], for all i in N",
    "activation_logic[i,j]: x[i,j] <= capacity[i,j] * y[i,j], for all (i,j) in A"
  ]
}
```

### Common Pitfalls
- Incorrect supply/demand sign convention: ensure positive values indicate net outflow (supply) and negative values indicate net inflow (demand) in the flow conservation constraint.
- Forgetting to exclude self-connections `(i,i)` from the arc set, which can lead to meaningless cycles.
- Using generator expressions inside Pyomo constraints that cause key errors; pre-filter arcs into lists.

## Solving stage

### Strategy Overview
This stage focuses on configuring a MILP solver, executing the solve, and robustly handling the results. It emphasizes checking solver status and termination conditions before extracting and validating the solution.

### Step 1 - Configure Solver with Performance Settings
- Instantiate the solver using `SolverFactory("solver_name")` (e.g., `"gurobi"`, `"highs"`).
- Set key parameters: `time_limit` for runtime control, `mip_rel_gap` (or `MIPGap`) to 0.0 for optimality, `threads` for parallelism, and `seed` for reproducibility.

### Step 2 - Solve with Robust Error Handling
- Call `solver.solve(model, tee=False, load_solutions=False)` to avoid automatic loading on failure.
- Wrap the solve in a try-except block to catch and report solver exceptions gracefully.

### Step 3 - Check Solution Status and Load Results
- Verify `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition` is `optimal` or `feasible`.
- Only if status is OK, load the solution into the model using `model.solutions.load_from(results)`.

### Step 4 - Extract and Validate Solution
- Iterate over arcs to collect active connections where `pyo.value(model.y[i,j]) > 0.5`.
- Retrieve flow values `pyo.value(model.x[i,j])` for active arcs.
- Perform post-solve validation: recompute net flow at each node and compare with supply/demand within a small tolerance (e.g., 1e-6).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model building code) ...

solver = pyo.SolverFactory("solver_name")  # e.g., "gurobi"
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0  # or 'MIPGap' for Gurobi

try:
    results = solver.solve(model, tee=False, load_solutions=False)
    status = results.solver.status
    term = results.solver.termination_condition

    if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
        model.solutions.load_from(results)
        # Extract solution: active_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.y[i,j]) > 0.5]
        # Validate flow conservation
    else:
        print(f"Solver failed: Status={status}, Termination={term}")
except Exception as e:
    print(f"Solver error: {e}")
```

### Common Pitfalls
- Setting invalid solver parameters (e.g., negative `MIPGap`), causing immediate errors.
- Assuming a solution exists without checking termination condition, leading to errors when accessing variable values.
- Not using `load_solutions=False`, which can cause Pyomo to load an infeasible or incomplete solution state.

# Workflow 2 (OR-Tools for Lightweight MILP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' `pywraplp` interface to construct the model directly in a solver-native manner. It is suitable for environments where Pyomo is unavailable or for integrating into lightweight applications, leveraging solvers like SCIP or CBC.

### Step 1 - Initialize Solver and Data Structures
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Organize problem data (supply/demand, costs, capacities) in dictionaries indexed by node pairs `(i,j)`.

### Step 2 - Create Variables with Explicit Bounds
- For each possible arc `(i,j)`, create a binary variable: `y[i,j] = solver.BoolVar(f"y_{i}_{j}")`.
- Create a continuous flow variable with an upper bound: `x[i,j] = solver.NumVar(0, capacity[i,j], f"x_{i}_{j}")`.

### Step 3 - Build Flow Conservation Constraints
- For each node `i`, compute the sum of inflow variables (`x[j,i]` for all `j`) and outflow variables (`x[i,j]` for all `j`).
- Add a linear constraint: `solver.Add(inflow_sum - outflow_sum == demand[i])`. Use explicit loops to build term lists, avoiding generator expressions.

### Step 4 - Enforce Activation Logic Constraints
- For each arc `(i,j)`, add the constraint: `solver.Add(x[i,j] <= capacity[i,j] * y[i,j])`.

### Step 5 - Set the Minimization Objective
- Build the objective expression by summing `fixed_cost[i,j] * y[i,j] + variable_cost[i,j] * x[i,j]` over all arcs.
- Call `solver.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": ["nodes", "arcs (list of tuples)"],
  "parameters": ["demand[node]", "fixed_cost[arc]", "variable_cost[arc]", "capacity[arc]"],
  "decision_variables": ["y[arc] (BoolVar)", "x[arc] (NumVar, 0 <= x <= capacity)"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i,j] * y[i,j] + variable_cost[i,j] * x[i,j])"
  },
  "constraints": [
    "flow_conservation[i]: sum(x[j,i] for j) - sum(x[i,j] for j) == demand[i]",
    "activation_logic[i,j]: x[i,j] <= capacity[i,j] * y[i,j]"
  ]
}
```

### Common Pitfalls
- Using Python generator expressions inside `solver.Sum()`, which may not be evaluated correctly; use explicit list comprehension instead.
- Forgetting to handle self-connection arcs `(i,i)`, which should be fixed to zero or excluded.
- Mismatch between variable naming and dictionary keys when building constraints, leading to key errors.

## Solving stage

### Strategy Overview
This stage involves executing the OR-Tools solver, checking its status, and parsing the solution. It is more procedural than Pyomo, requiring manual extraction of variable values and verification.

### Step 1 - Set Solver Parameters
- Set a time limit: `solver.SetTimeLimit(time_limit_ms)`.
- Set the number of threads for parallel processing if supported: `solver.SetNumThreads(num_threads)`.

### Step 2 - Invoke the Solver
- Call `status = solver.Solve()`.
- The result is an integer status code (e.g., `pywraplp.Solver.OPTIMAL`, `FEASIBLE`).

### Step 3 - Check Status and Extract Solution
- Check if `status == pywraplp.Solver.OPTIMAL` or `status == pywraplp.Solver.FEASIBLE`.
- If feasible, iterate over arcs to collect active connections where `y[i,j].solution_value() > 0.5`.
- Retrieve flow values using `x[i,j].solution_value()`.

### Step 4 - Validate Solution Feasibility
- Recompute net flow at each node using the extracted flow values.
- Compare with the original demand/supply values, allowing a small tolerance (e.g., 1e-3).
- Verify that for every active arc, the flow does not exceed its capacity.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# ... (solver and variable creation code) ...

solver.SetTimeLimit(30000)  # 30 seconds in milliseconds
solver.SetNumThreads(4)

status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    active_arcs = []
    for (i,j) in arcs:
        if y[i,j].solution_value() > 0.5:
            flow_val = x[i,j].solution_value()
            active_arcs.append(((i,j), flow_val))
    # Post-solve validation: verify flow conservation
else:
    print(f"Solver did not find a feasible solution. Status: {status}")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses before accessing solution values.
- Assuming solution values exist for all variables after a non-optimal status, which can cause attribute errors.
- Using an unsupported parameter (like `SetNumThreads`) for a specific solver backend, causing runtime errors.
