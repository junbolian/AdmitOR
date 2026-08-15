---
name: TSP_MTZ_Solver_Workflow
description: |
  Model and solve traveling salesman problems using Miller-Tucker-Zemlin subtour elimination, with workflows for CP-SAT and MIP solvers.

---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver, which is designed for constraint programming and integer problems. It models the TSP with binary arc variables and integer positional variables, enforcing flow conservation and MTZ constraints directly within the CP-SAT model builder.

### Step 1 - Define Sets and Parameters
- Define a set `N` representing all nodes (cities). Use a list of indices, e.g., `nodes = range(num_nodes)`.
- Define a parameter `cost` as a 2D dictionary mapping arcs `(i, j)` to their travel cost. Ensure `cost[i][i]` is not used.

### Step 2 - Create Decision Variables
- Create binary decision variables `x[i][j]` for all `i, j in N` where `i != j` using `model.NewBoolVar()`. These represent arc selection.
- Create integer positional variables `u[i]` for all `i in N` using `model.NewIntVar(lb, ub, name)`. Set lower bound `lb=0` and upper bound `ub=len(N)-1`.

### Step 3 - Formulate Constraints
- **Single Departure**: For each node `i`, add `sum(x[i][j] for j in N if j != i) == 1`.
- **Single Visit**: For each node `j`, add `sum(x[i][j] for i in N if i != j) == 1`.
- **MTZ Subtour Elimination**: For all `i, j in N` where `i != j`, `i != depot`, `j != depot`, add `u[i] - u[j] + n * x[i][j] <= n - 1`, where `n = len(N)`.
- **Anchor Depot**: Fix the depot's position, e.g., `model.Add(u[depot_index] == 0)`.

### Step 4 - Define Objective
- Formulate the objective to minimize total cost: `sum(cost[i][j] * x[i][j] for i in N for j in N if i != j)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes (cities)."}
  ],
  "parameters": [
    {"name": "cost", "description": "Travel cost from node i to node j, for i,j in N, i!=j."}
  ],
  "decision_variables": [
    {"name": "x", "description": "Binary variable: 1 if arc (i,j) is used in the tour."},
    {"name": "u", "description": "Integer variable: position of node i in the tour sequence."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in N for j in N if i != j)"
  },
  "constraints": [
    {"name": "depart_once", "expression": "sum(x[i][j] for j in N if j != i) == 1, for all i in N"},
    {"name": "arrive_once", "expression": "sum(x[i][j] for i in N if i != j) == 1, for all j in N"},
    {"name": "mtz", "expression": "u[i] - u[j] + |N| * x[i][j] <= |N| - 1, for all i,j in N, i!=j, i!=depot, j!=depot"},
    {"name": "fix_depot", "expression": "u[depot] == 0"}
  ]
}
```

### Common Pitfalls
- Forgetting to exclude `i == j` when creating `x` variables, which can lead to invalid self-loops.
- Incorrectly setting the upper bound for `u[i]`; it should be `n-1`, not `n`.
- Applying MTZ constraints for arcs involving the depot, which is unnecessary and can over-constrain the model.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configurable time and optimality tolerances. Extract the solution, reconstruct the tour by following selected arcs, and verify consistency.

### Step 1 - Configure Solver
- Instantiate `CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds` for runtime limit, `solver.parameters.num_search_workers` for parallelism, `solver.parameters.random_seed` for reproducibility, and `solver.parameters.relative_gap_limit = 0.0` for exact solution.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if `status` is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNKNOWN` statuses appropriately (e.g., raise error or return empty result).

### Step 3 - Extract Solution and Reconstruct Route
- If feasible/optimal, get objective value: `total_cost = solver.ObjectiveValue()`.
- Extract arc values: `arc_used = {(i,j): solver.Value(x[i][j]) for i,j in arcs}`.
- Reconstruct the tour: start at the depot, iteratively find the next node `j` where `arc_used[(current, j)] == 1`, and append to route list until returning to depot.

### Step 4 - Output and Verify
- Return a structured result containing status, objective value, route list, and positional variable values.
- Optionally, verify the solution by summing the costs of consecutive nodes in the route and comparing to the solver's objective value.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build model as per Modeling Stage)
# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    objective_value = solver.ObjectiveValue()
    # Extract variable values and reconstruct tour
    # ... (implementation)
else:
    # Handle infeasible or unknown status
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Not checking solver status before extracting values, leading to runtime errors.
- Setting `relative_gap_limit` to a negative value, which is invalid; use `0.0` for exact solutions.
- Inefficient route reconstruction that may get stuck in a loop; use a visited set or limit iterations to the number of nodes.

# Workflow 2 (MIP with Pyomo and Commercial Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for algebraic modeling, targeting commercial MIP solvers like Gurobi or CPLEX. It formulates the TSP with MTZ constraints as a mixed-integer linear program, leveraging the solver's advanced cutting planes and heuristics.

### Step 1 - Define Abstract Sets and Parameters
- Define an abstract set `N` using `pyo.Set()`.
- Define a parameter `cost` indexed over `N x N` using `pyo.Param(mutable=True)`.

### Step 2 - Create Decision Variables
- Create binary variables `x[i,j]` for `i,j in N, i != j` using `pyo.Var(within=pyo.Binary)`.
- Create integer positional variables `u[i]` for `i in N` using `pyo.Var(within=pyo.NonNegativeIntegers, bounds=(lb, ub))`.

### Step 3 - Formulate Constraints via Rules
- **Flow Conservation**: Define Pyomo `Constraint` rules for `model.depart` and `model.arrive` that sum `x` variables.
- **MTZ Constraints**: Define a `Constraint` rule for `model.mtz` that implements `u[i] - u[j] + n*x[i,j] <= n-1` for applicable `i,j`.
- **Depot Fixing**: Add a constraint `model.fix_depot` setting `u[depot] == 0`.

### Step 4 - Define Objective
- Define the objective using `pyo.Objective(expr=sum(cost[i,j]*x[i,j] for i,j in arcs), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes."}
  ],
  "parameters": [
    {"name": "cost", "description": "Cost matrix, cost[i,j] for i,j in N, i!=j."}
  ],
  "decision_variables": [
    {"name": "x", "description": "Binary arc selection variable."},
    {"name": "u", "description": "Integer position variable."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in N for j in N if i != j)"
  },
  "constraints": [
    {"name": "depart_once", "expression": "sum(x[i,j] for j in N if j != i) == 1, for all i in N"},
    {"name": "arrive_once", "expression": "sum(x[i,j] for i in N if i != j) == 1, for all j in N"},
    {"name": "mtz", "expression": "u[i] - u[j] + |N| * x[i,j] <= |N| - 1, for all i,j in N, i!=j, i!=depot, j!=depot"},
    {"name": "fix_depot", "expression": "u[depot] == 0"}
  ]
}
```

### Common Pitfalls
- Using `pyo.Param` without `mutable=True` if costs need to be changed between model instances.
- Forgetting to filter `i != j` in the objective summation, which could include zero-cost self-loops and distort the solution.
- Incorrectly indexing the MTZ constraint over all `i,j` including the depot, which can create infeasibility.

## Solving stage

### Strategy Overview
Instantiate a Pyomo model, send it to a MIP solver via a compatible interface (e.g., `pyo.SolverFactory('gurobi')`), configure solver options, solve, and process the results.

### Step 1 - Configure Solver and Options
- Create a solver object: `solver = pyo.SolverFactory('solver_name')`.
- Set options: `solver.options['TimeLimit'] = time_limit`, `solver.options['Threads'] = thread_count`, `solver.options['MIPGap'] = tolerance` (use `0.0` for optimality), and `solver.options['Seed'] = seed`.

### Step 2 - Solve and Check Termination Condition
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.termination_condition`. Accept `optimal` or `feasible`. Handle `infeasible` or `other` accordingly.

### Step 3 - Extract Solution and Build Route
- If solved successfully, access variable values: `x_val = model.x[i,j].value` (round to nearest integer for binary variables).
- Reconstruct the tour by starting at the depot and following arcs where `x_val` is approximately 1.
- Extract positional values: `u_val = model.u[i].value`.

### Step 4 - Output and Validate
- Return a dictionary with status, objective value (`model.obj()`), route, and positional values.
- Validate by checking that the reconstructed route is a Hamiltonian cycle and that the computed cost matches the reported objective.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
# ... (build model as per Modeling Stage)
# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'cbc', 'cplex'
solver.options['TimeLimit'] = 30
solver.options['Threads'] = 4
solver.options['MIPGap'] = 0.0
solver.options['Seed'] = 42

results = solver.solve(model, tee=False)
if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    objective_value = pyo.value(model.obj)
    # Extract variable values and reconstruct tour
    # ... (implementation)
else:
    # Handle unsuccessful termination
    print(f"Solver terminated with: {results.solver.termination_condition}")
```

### Common Pitfalls
- Setting `MIPGap` to a negative value, which causes an error; use `0.0` for exact solutions.
- Not rounding binary variable values (which may be slightly non-integer due to tolerances) before route reconstruction.
- Assuming the solver object is re-entrant; create a new solver instance for each solve if reusing the model with different data.
