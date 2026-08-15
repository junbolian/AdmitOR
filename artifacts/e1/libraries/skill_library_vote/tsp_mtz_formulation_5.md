---
name: TSP_MTZ_Formulation
description: |
  Model and solve traveling salesman problems using Miller-Tucker-Zemlin subtour elimination with binary routing and integer position variables.
---

# Workflow 1 (Pyomo with MTZ)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to build a ConcreteModel, implementing the Miller-Tucker-Zemlin (MTZ) formulation for subtour elimination. It is well-suited for integration with high-performance solvers like Gurobi or HiGHS via Pyomo's solver interfaces.

### Step 1 - Define Sets and Parameters
- Define a set `CITIES` representing all locations.
- Define a parameter `cost[i,j]` representing the travel cost between city `i` and city `j`.

### Step 2 - Create Decision Variables
- Create binary variables `x[i,j]` for all `i, j` in `CITIES` where `i != j` to indicate if arc (i,j) is in the tour.
- Create integer variables `u[i]` for all `i` in `CITIES` representing the sequence position, with bounds `(0, len(CITIES)-1)`.

### Step 3 - Formulate Assignment Constraints
- Add constraints `sum(x[i,j] for j in CITIES if j != i) == 1` for each city `i` (single outgoing).
- Add constraints `sum(x[j,i] for j in CITIES if j != i) == 1` for each city `i` (single incoming).
- Optionally, add explicit constraints `x[i,i] == 0` to prevent self-loops.

### Step 4 - Apply MTZ Subtour Elimination
- Fix the starting city's position: `u[start_city] == 0`.
- For all `i` and `j` in `CITIES` where `i != j` and `i != start_city` and `j != start_city`, add the MTZ constraint: `u[i] - u[j] + n * x[i,j] <= n - 1`, where `n = len(CITIES)`.

### Step 5 - Define Objective
- Minimize the total tour cost: `sum(cost[i,j] * x[i,j] for i in CITIES for j in CITIES if i != j)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "CITIES", "description": "Set of all nodes/cities."}
  ],
  "parameters": [
    {"name": "cost", "index": ["CITIES", "CITIES"], "description": "Cost matrix for travel between cities."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["CITIES", "CITIES"], "type": "binary", "description": "1 if arc (i,j) is in the tour."},
    {"name": "u", "index": ["CITIES"], "type": "integer", "bounds": [0, "n-1"], "description": "Sequence position of city i."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i,j] * x[i,j] for i in CITIES for j in CITIES if i != j )"
  },
  "constraints": [
    {"name": "outgoing", "expression": "sum( x[i,j] for j in CITIES if j != i ) == 1", "for_each": "i in CITIES"},
    {"name": "incoming", "expression": "sum( x[j,i] for j in CITIES if j != i ) == 1", "for_each": "i in CITIES"},
    {"name": "mtz", "expression": "u[i] - u[j] + n * x[i,j] <= n - 1", "for_each": "i,j in CITIES where i != j and i != start_city and j != start_city"},
    {"name": "start_pos", "expression": "u[start_city] == 0"}
  ]
}
```

### Common Pitfalls
- Applying MTZ constraints to arcs involving the fixed start city can cause infeasibility; exclude `start_city` from the `for_each` index set for the MTZ constraint.
- Forgetting to set explicit bounds on integer position variables `u[i]`; they must be bounded to prevent unbounded solutions.
- Using `n` (number of cities) directly in the MTZ constraint expression without ensuring it's defined as a model parameter or Python variable.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver (e.g., Gurobi, HiGHS) via the `pyomo` solver factory. Configure solver options for performance and check solution status rigorously before extracting results.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object using `SolverFactory('solver_name')`.
- Set solver options such as time limit (`opt.options['time_limit'] = time_limit`) and number of threads (`opt.options['threads'] = threads`).

### Step 2 - Solve and Check Status
- Call `results = opt.solve(model, tee=False)` to solve the model.
- Check the solver status: `assert results.solver.status == SolverStatus.ok`.
- Check the termination condition: `assert results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]`.

### Step 3 - Extract and Validate Solution
- Extract the objective value: `model.obj()`.
- Reconstruct the tour by iterating from the start city: find `j` such that `pyo.value(model.x[start_city, j]) > 0.5`, then follow successive arcs.
- Optionally, recalculate the total cost from the extracted route and compare it to the reported objective value for validation.

### Step 4 - Output Results
- Print the objective value and the tour sequence in a standard format (e.g., `RESULT:{objective_value}`).
- For infeasible or error states, output a structured error payload (e.g., JSON) with solver status details.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# build model from formulation
model = pyo.ConcreteModel()
# ... [Populate model with sets, parameters, variables, constraints, objective as per formulation]

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'highs', 'cbc'
solver.options['time_limit'] = time_limit
solver.options['threads'] = threads
results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    obj_val = pyo.value(model.obj)
    # Extract tour from model.x
    # ... [Tour reconstruction logic]
    print(f"RESULT:{obj_val}")
else:
    error_info = {
        "status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
    print(f"ERROR:{error_info}")
```

### Common Pitfalls
- Accessing variable values (`pyo.value`) before confirming the solver status is `ok` and termination is acceptable, which can raise errors.
- Setting invalid solver options (e.g., a negative MIP gap) that cause the solver to fail silently.
- Not using `tee=True` during development to see solver logs, which hinders debugging of presolve reductions or infeasibility.

# Workflow 2 (OR-Tools with MTZ)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to build a MIP model with MTZ constraints. It is efficient for direct solver interaction and benefits from SCIP's or CBC's robust MIP capabilities within a lightweight API.

### Step 1 - Initialize Solver and Define Dimensions
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Define `n` as the number of cities and create index ranges.

### Step 2 - Create Binary Routing Variables
- Create a 2D dictionary or list of binary variables `x[i][j]` using `solver.BoolVar()` for all `i != j`.

### Step 3 - Create Integer Position Variables
- Create integer variables `u[i]` using `solver.IntVar(lb, ub, name)` with lower bound 0 and upper bound `n-1`.

### Step 4 - Add Assignment and MTZ Constraints
- For each city `i`, add constraint `sum(x[i][j] for j in range(n) if j != i) == 1`.
- For each city `i`, add constraint `sum(x[j][i] for j in range(n) if j != i) == 1`.
- Fix `u[start_city] = 0` by setting its lower and upper bounds to 0.
- For `i` in `range(1, n)` and `j` in `range(1, n)` where `i != j`, add MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.

### Step 5 - Set Objective
- Build the objective expression: `sum(cost[i][j] * x[i][j] for i in range(n) for j in range(n) if i != j)`.
- Set the solver objective to minimize this sum.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Number of cities, used as index range."}
  ],
  "parameters": [
    {"name": "cost", "index": ["N", "N"], "description": "2D cost matrix."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["N", "N"], "type": "binary", "description": "Routing variable."},
    {"name": "u", "index": ["N"], "type": "integer", "bounds": [0, "N-1"], "description": "Position variable."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i][j] * x[i][j] for i in N for j in N if i != j )"
  },
  "constraints": [
    {"name": "outgoing", "expression": "sum( x[i][j] for j in N if j != i ) == 1", "for_each": "i in N"},
    {"name": "incoming", "expression": "sum( x[j][i] for j in N if j != i ) == 1", "for_each": "i in N"},
    {"name": "mtz", "expression": "u[i] - u[j] + N * x[i][j] <= N - 1", "for_each": "i,j in N where i != j and i != start_idx and j != start_idx"},
    {"name": "start_fixed", "expression": "u[start_idx] == 0"}
  ]
}
```

### Common Pitfalls
- Using the same index `i` and `j` loops for MTZ constraints without excluding the start city, leading to infeasible constraints on the return arc.
- Forgetting to prevent self-loops, either by not creating `x[i][i]` variables or by explicitly setting them to 0.
- Miscalculating the coefficient `n` in the MTZ constraint if `n` is defined after variable creation.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' solver object, configure time and thread limits, and extract the solution by checking variable values. The workflow is direct and avoids additional modeling layer overhead.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.SetTimeLimit(time_limit_ms)`.
- Set the number of threads: `solver.SetNumThreads(threads)`.

### Step 2 - Invoke Solver
- Call `status = solver.Solve()` and capture the return status.

### Step 3 - Interpret Solver Status and Extract Solution
- Check if `status` is `pywraplp.Solver.OPTIMAL` or `FEASIBLE`.
- If feasible, extract the objective value: `solver.Objective().Value()`.
- Reconstruct the tour: starting from `start_city`, find `j` where `x[start_city][j].solution_value() > 0.5`, then iterate.

### Step 4 - Output and Error Handling
- Output the objective value and tour in a standard format.
- For non-optimal statuses (e.g., `INFEASIBLE`, `UNBOUNDED`), output an error message with the status.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
n = len(cost_matrix)
x = {}
u = {}
# ... [Create variables x[i][j] and u[i] as per formulation]
# ... [Add constraints as per formulation]
# ... [Set objective]

# solve with status / termination checks
solver.SetTimeLimit(time_limit_ms)
solver.SetNumThreads(threads)
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    obj_val = solver.Objective().Value()
    # Extract tour from x variables
    # ... [Tour reconstruction logic]
    print(f"RESULT:{obj_val}")
else:
    status_map = {pywraplp.Solver.OPTIMAL: 'OPTIMAL',
                  pywraplp.Solver.FEASIBLE: 'FEASIBLE',
                  pywraplp.Solver.INFEASIBLE: 'INFEASIBLE',
                  pywraplp.Solver.UNBOUNDED: 'UNBOUNDED',
                  pywraplp.Solver.ABNORMAL: 'ABNORMAL'}
    print(f"ERROR:Solver status: {status_map.get(status, 'UNKNOWN')}")
```

### Common Pitfalls
- Not converting time limit to milliseconds for `SetTimeLimit`.
- Checking binary variable activation with exact equality to 1; use `> 0.5` tolerance instead.
- Assuming the solver always returns an optimal solution without checking the status code, leading to runtime errors when accessing solution values.
