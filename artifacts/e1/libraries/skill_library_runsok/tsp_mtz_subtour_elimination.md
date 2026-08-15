---
name: TSP_MTZ_Subtour_Elimination
description: |
  Model and solve traveling salesman problems using binary routing and integer position variables with Miller-Tucker-Zemlin subtour elimination constraints.
---

# Workflow 1 (MIP Solver via OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the TSP as a Mixed-Integer Program (MIP) using the Miller-Tucker-Zemlin (MTZ) formulation. It is designed for direct implementation with OR-Tools' `pywraplp` API, focusing on a compact constraint set suitable for MIP solvers like SCIP or CBC.

### Step 1 - Define Variables
- Create binary decision variable `x[i,j]` for each ordered node pair `(i,j)` where `i != j`, indicating if the route from node i to node j is taken.
- Create integer decision variable `u[i]` for each node i, representing its sequence position in the tour, with bounds `[0, n_nodes-1]`.

### Step 2 - Formulate Flow Conservation
- For each node i, add a constraint ensuring exactly one outgoing route: `sum_{j, j!=i} x[i,j] == 1`.
- For each node i, add a constraint ensuring exactly one incoming route: `sum_{j, j!=i} x[j,i] == 1`.

### Step 3 - Implement MTZ Subtour Elimination
- For each ordered node pair `(i,j)` where `i != j` and neither is the designated depot (node 0), add the MTZ constraint: `u[i] - u[j] + n_nodes * x[i,j] <= n_nodes - 1`.
- This prevents subtours by enforcing a logical sequence order.

### Step 4 - Set Initial Position and Bounds
- Fix the depot's position variable: `u[depot] == 0`.
- Optionally, set lower bounds for non-depot nodes: `u[i] >= 1` for `i != depot` to break symmetry.

### Step 5 - Define Objective Function
- Minimize the total travel cost: `sum_{i,j, i!=j} cost[i][j] * x[i,j]`.

### Formulation Template
```json
{
  "sets": [
    "NODES"
  ],
  "parameters": [
    {"name": "cost", "index": ["NODES", "NODES"], "description": "Travel cost from i to j, cost[i][i] = 0."},
    {"name": "n_nodes", "type": "scalar", "description": "Number of nodes."},
    {"name": "depot", "type": "scalar", "description": "Index of the starting/ending depot node."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["NODES", "NODES"], "type": "binary", "description": "1 if arc (i,j) is in the tour."},
    {"name": "u", "index": ["NODES"], "type": "integer", "bounds": "[0, n_nodes-1]", "description": "Position of node in tour sequence."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in NODES} sum_{j in NODES, j != i} cost[i][j] * x[i,j]"
  },
  "constraints": [
    {"name": "outgoing_flow", "expression": "sum_{j in NODES, j != i} x[i,j] == 1", "for_all": "i in NODES"},
    {"name": "incoming_flow", "expression": "sum_{j in NODES, j != i} x[j,i] == 1", "for_all": "i in NODES"},
    {"name": "mtz", "expression": "u[i] - u[j] + n_nodes * x[i,j] <= n_nodes - 1", "for_all": "i,j in NODES, i != j, i != depot, j != depot"},
    {"name": "depot_position", "expression": "u[depot] == 0"}
  ]
}
```

### Common Pitfalls
- Forgetting to exclude `i == j` when creating `x` variables, which creates invalid self-loop variables.
- Applying MTZ constraints to the depot node (i=depot or j=depot), which can incorrectly block the return arc to the depot.
- Using an insufficient upper bound for `u[i]` (e.g., `n_nodes` instead of `n_nodes-1`), which can make the model infeasible.

## Solving stage

### Strategy Overview
Solve the MIP model using OR-Tools' wrapper for MIP solvers. Configure solver parameters for performance, check solution status rigorously, and reconstruct the tour sequence from binary variable values.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `solver = pywraplp.Solver.CreateSolver('SCIP')`).
- Set a time limit: `solver.SetTimeLimit(time_limit_ms)`.
- Set the number of threads: `solver.SetNumThreads(num_threads)`.

### Step 2 - Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `status = solver.ResultStatus()`.
- Proceed only if status is `OPTIMAL` or `FEASIBLE`. Handle other statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) with appropriate error messages.

### Step 3 - Extract Solution and Reconstruct Tour
- For each binary variable `x[i,j]`, check if its solution value `> 0.5`.
- Starting from the depot, follow the chain of `x[i,j] == 1` arcs to reconstruct the full Hamiltonian cycle.
- Calculate the total cost independently by summing `cost[i][j]` for arcs in the tour to verify against the solver's objective value.

### Step 4 - Output Structured Results
- Return a dictionary or JSON object containing the solver status, objective value, tour as a list of node indices, and optionally the position variable values.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (create variables, add constraints, set objective)
solver.SetTimeLimit(60000)  # 60 seconds
solver.SetNumThreads(4)

# solve with status / termination checks
result_status = solver.Solve()
if result_status == solver.OPTIMAL or result_status == solver.FEASIBLE:
    # Extract solution
    tour = []
    current = depot
    while True:
        tour.append(current)
        for j in NODES:
            if j != current and x[current, j].solution_value() > 0.5:
                current = j
                break
        if current == depot:
            break
    # ... (calculate cost, prepare output)
else:
    # Handle non-optimal status
    raise Exception(f"Solver finished with status: {result_status}")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid but non-proven optimal solutions.
- Incorrect tour reconstruction logic that gets stuck in a loop if the solution contains subtours (indicating a modeling error in MTZ constraints).
- Assuming variable indices exist without checking, leading to KeyErrors when using sparse cost matrices.

# Workflow 2 (Pyomo with High-Level Solver Interface)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling to define the MTZ formulation, separating model construction from solver invocation. It is suited for solvers like Gurobi, CPLEX, or HiGHS accessed via Pyomo's `SolverFactory`.

### Step 1 - Define Abstract Sets and Parameters
- Declare a Set `N` for nodes.
- Declare a Parameter `c` indexed over `N x N` for travel costs, with a rule to set `c[i,i] = 0`.

### Step 2 - Create Variables with Bounds
- Define `model.x` as a `Var(N, N, within=Binary, initialize=0)` for routing, and add a constraint `model.x[i,i].fix(0)` for all i to prevent self-loops.
- Define `model.u` as a `Var(N, within=NonNegativeIntegers, bounds=(0, n_nodes-1))` for positions.

### Step 3 - Build Constraints with Conditional Generation
- Use `ConstraintList` or a rule with `Constraint.Skip` to create flow conservation constraints for each node.
- For MTZ constraints, generate only for `i != j` and `i != depot` and `j != depot` using a conditional rule to avoid unnecessary constraints.

### Step 4 - Anchor Depot and Set Objective
- Fix the depot's position: `model.u[depot].fix(0)`.
- Define the objective as `sum(c[i,j] * model.x[i,j] for i in N for j in N if i != j)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes."}
  ],
  "parameters": [
    {"name": "c", "index": ["N", "N"], "description": "Cost matrix, c[i,i] = 0."},
    {"name": "depot", "type": "scalar", "description": "Depot node index."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["N", "N"], "type": "binary", "description": "Routing variable."},
    {"name": "u", "index": ["N"], "type": "integer", "bounds": "[0, len(N)-1]", "description": "Position variable."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( c[i,j] * x[i,j] for i in N for j in N if i != j )"
  },
  "constraints": [
    {"name": "flow_out", "expression": "sum( x[i,j] for j in N if j != i ) == 1", "for_all": "i in N"},
    {"name": "flow_in", "expression": "sum( x[j,i] for j in N if j != i ) == 1", "for_all": "i in N"},
    {"name": "mtz", "expression": "u[i] - u[j] + len(N) * x[i,j] <= len(N) - 1", "for_all": "i,j in N, i != j, i != depot, j != depot"},
    {"name": "depot_fixed", "expression": "u[depot] == 0"}
  ]
}
```

### Common Pitfalls
- Using `model.x[i,i].fix(0)` after variable creation instead of setting it during initialization, which can be less efficient.
- Incorrectly indexing parameters in Pyomo rules, leading to `KeyError` if the cost dictionary is not defined for all `(i,j)` pairs.
- Forgetting to deactivate the `mtz` constraint for the depot, which can make the model infeasible.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory, configure solver-specific options, and implement robust checks for solution status and termination condition before extracting results.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = SolverFactory('gurobi')`.
- Set solver options: `solver.options['TimeLimit'] = time_limit`, `solver.options['MIPGap'] = mip_gap`, `solver.options['Threads'] = num_threads`.

### Step 2 - Solve and Validate Termination
- Call `results = solver.solve(model, tee=False)`.
- Check both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`).
- Proceed only if status is `ok` and termination is `optimal` or `feasible`. Log details for other outcomes.

### Step 3 - Extract and Verify Solution
- Access variable values: `model.x[i,j].value` and `model.u[i].value`.
- Reconstruct the tour by following arcs where `model.x[i,j].value > 0.5`.
- Optionally, compute the total cost from the extracted tour and compare with `model.obj()`.

### Step 4 - Handle Infeasibility or Errors
- For infeasible results, inspect constraint violations or use solver-specific IIS (Irreducible Inconsistent Subsystem) features if available.
- Return a structured error payload containing solver status, termination condition, and any diagnostic information.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
# ... (define parameters, variables, constraints, objective)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 60
solver.options['MIPGap'] = 0.0001
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                              pyo.TerminationCondition.feasible]):
    # Extract and process solution
    tour = [depot]
    current = depot
    while True:
        for j in model.N:
            if j != current and pyo.value(model.x[current, j]) > 0.5:
                current = j
                if current != depot:
                    tour.append(current)
                break
        if current == depot:
            break
    obj_val = pyo.value(model.obj)
else:
    # Handle failure
    raise Exception(f"Solver failed: {results.solver.status}, {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing Pyomo's `SolverStatus` (e.g., `ok`, `warning`) with `TerminationCondition` (e.g., `optimal`, `infeasible`). Both must be checked.
- Accessing `.value` on variables before verifying the solution is available, which may raise an AttributeError.
- Not setting a `mip_gap` > 0 for large instances, causing the solver to run indefinitely seeking proven optimality.
