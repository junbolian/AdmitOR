---
name: TSP with Position-Based Subtour Elimination
description: |
  Model the Traveling Salesperson Problem using binary arc selection and node position variables with Miller-Tucker-Zemlin constraints, then solve with a MIP solver, handling solution extraction and validation.
---

# Workflow 1 (MIP Solver with Explicit Big-M)

## Modeling stage

### Strategy Overview
This workflow uses a standard Miller-Tucker-Zemlin (MTZ) formulation with an explicit Big-M constant to eliminate subtours. It is a compact model suitable for MIP solvers like SCIP or CBC, focusing on clear constraint logic and variable bounds.

### Step 1 - Define Variables
- Create binary decision variable `x[i,j]` for each ordered pair of distinct nodes `(i,j)` to represent arc selection.
- Create integer decision variable `u[i]` for each node `i` to represent its position in the tour, with bounds `[0, n_nodes-1]`.

### Step 2 - Enforce Flow Conservation
- For each node `i`, add a constraint summing `x[i,j]` over all `j != i` equal to 1 (single departure).
- For each node `j`, add a constraint summing `x[i,j]` over all `i != j` equal to 1 (single arrival).

### Step 3 - Implement MTZ Subtour Elimination
- For each ordered pair `(i,j)` where `j` is not the designated depot (e.g., node 0), add the constraint: `u[j] >= u[i] + 1 - M * (1 - x[i,j])`.
- Set the Big-M constant `M` to the total number of nodes `n_nodes`.

### Step 4 - Set Position Reference and Bounds
- Fix the position of the depot node: `u[depot] = 0`.
- For all non-depot nodes `i`, enforce `1 <= u[i] <= n_nodes - 1`.

### Step 5 - Define Objective
- Minimize the sum of `cost[i,j] * x[i,j]` over all arcs `(i,j)` where `i != j`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (cities)",
    "A: set of arcs (i,j) where i,j in N, i != j"
  ],
  "parameters": [
    "cost[i,j]: travel cost on arc (i,j) for all (i,j) in A",
    "depot: index of the starting/ending node (e.g., 0)",
    "n_nodes: total number of nodes |N|"
  ],
  "decision_variables": [
    "x[i,j]: binary, 1 if arc (i,j) is traversed, for (i,j) in A",
    "u[i]: integer, position of node i in the tour, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for (i,j) in A)"
  },
  "constraints": [
    "sum(x[i,j] for j in N, j != i) == 1, for all i in N",
    "sum(x[i,j] for i in N, i != j) == 1, for all j in N",
    "u[j] >= u[i] + 1 - n_nodes * (1 - x[i,j]), for all (i,j) in A where j != depot",
    "u[depot] == 0",
    "1 <= u[i] <= n_nodes - 1, for all i in N, i != depot"
  ]
}
```

### Common Pitfalls
- Using a Big-M value smaller than `n_nodes`, which can cut off valid tours.
- Applying the MTZ constraint to arcs returning to the depot (`j == depot`), which incorrectly prevents the final return leg of the cycle.
- Forgetting to bound position variables for non-depot nodes, leading to unbounded or duplicate positions.

## Solving stage

### Strategy Overview
Solve the MIP model using a solver like OR-Tools' SCIP or CBC wrapper. Configure solver parameters for performance, check termination status rigorously, and reconstruct the tour from arc variables.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set a time limit (e.g., `solver.SetTimeLimit(30000)` for 30 seconds in milliseconds).
- Set the number of threads for parallel processing (e.g., `solver.SetNumThreads(4)`).
- Optionally, set a relative optimality gap (e.g., `solver.SetRelativeGapLimit(0.0001)`).

### Step 2 - Build Model from Formulation
- Instantiate variables and constraints as defined in the modeling stage using the solver's API.
- Ensure the Big-M constant `M` is set to `n_nodes`.

### Step 3 - Solve and Check Status
- Call `solver.Solve()`.
- Check if the solver status is `OPTIMAL` or `FEASIBLE` before attempting to extract solution values.

### Step 4 - Extract and Validate Solution
- Extract selected arcs by iterating over `x[i,j]` variables and collecting those where `.solution_value() > 0.5`.
- Reconstruct the tour sequence by starting at the depot and following the selected arcs.
- Retrieve position variable values `u[i].solution_value()` to verify ordering consistency.
- Optionally, recalculate the total cost from the reconstructed tour to validate the objective value.

### Step 5 - Handle Failure or Suboptimal Results
- If status is not `OPTIMAL` or `FEASIBLE`, log the status and termination reason.
- For time-limited runs, report the best bound and gap if available.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Create variables
x = {}
for i in N:
    for j in N:
        if i != j:
            x[i,j] = solver.BoolVar(f"x_{i}_{j}")
u = {}
for i in N:
    lb = 0 if i == depot else 1
    ub = n_nodes - 1
    u[i] = solver.IntVar(lb, ub, f"u_{i}")

# Add constraints
# ... (add flow, MTZ, position constraints as per formulation)

# Set objective
objective_expr = sum(cost[i,j] * x[i,j] for i in N for j in N if i != j)
solver.Minimize(objective_expr)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Extract solution
    tour = [depot]
    current = depot
    while len(tour) < n_nodes:
        for j in N:
            if j != current and x[current,j].solution_value() > 0.5:
                tour.append(j)
                current = j
                break
    print(f"Tour: {tour}")
    print(f"Objective: {solver.Objective().Value()}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing `.solution_value()`, which can cause runtime errors.
- Incorrectly reconstructing the tour by not handling the final return arc; the sequence should include all nodes exactly once.
- Setting a negative MIP gap limit, which is invalid for most solvers (use a small positive value like `0.0001`).

# Workflow 2 (High-Level Modeling with Pyomo/Gurobi)

## Modeling stage

### Strategy Overview
This workflow uses a high-level modeling library (Pyomo) with an efficient commercial solver (Gurobi). It employs the alternative `u[i] - u[j] + n*x[i,j] <= n-1` MTZ formulation, emphasizing solver parameter tuning for optimality.

### Step 1 - Define Abstract Sets and Parameters
- Declare an abstract set for nodes and a parameter for the cost matrix.
- Define the number of nodes `n` and the depot index as parameters.

### Step 2 - Create Variables with Bounds
- Create binary variable `model.x[i,j]` for all `i != j`.
- Create integer variable `model.u[i]` with bounds `0 <= model.u[i] <= n-1`.

### Step 3 - Apply Flow and MTZ Constraints
- Add constraints for single departure and arrival per node.
- For all `i != j` where `j != depot`, add the constraint: `model.u[i] - model.u[j] + n * model.x[i,j] <= n - 1`.
- Fix the depot position: `model.u[depot] == 0`.

### Step 4 - Set Objective
- Minimize the sum of `cost[i,j] * model.x[i,j]`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes"
  ],
  "parameters": [
    "cost: indexed parameter cost[i,j] for i,j in N, i != j",
    "depot: index of the start/end node",
    "n: scalar, |N|"
  ],
  "decision_variables": [
    "x[i,j]: binary, for i,j in N, i != j",
    "u[i]: integer, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i,j in N if i != j)"
  },
  "constraints": [
    "sum(x[i,j] for j in N, j != i) == 1, for all i in N",
    "sum(x[i,j] for i in N, i != j) == 1, for all j in N",
    "u[i] - u[j] + n * x[i,j] <= n - 1, for all i,j in N, i != j, j != depot",
    "u[depot] == 0",
    "u[i] >= 1, for all i in N, i != depot",
    "u[i] <= n - 1, for all i in N"
  ]
}
```

### Common Pitfalls
- Using the constraint `u[i] - u[j] + n*x[i,j] <= n-1` for arcs where `j == depot`, which prevents the cycle from closing.
- Not fixing the depot position, leading to symmetric solutions and increased solve time.
- Omitting explicit lower bounds (`u[i] >= 1`) for non-depot nodes, which can allow position zero for multiple nodes.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model, send it to the Gurobi solver via a `SolverFactory`, configure optimality tolerances and runtime limits, and extract solutions with robust status checking.

### Step 1 - Instantiate Concrete Model
- Create a `ConcreteModel()` in Pyomo.
- Populate the model with data (sets, parameters, variables, constraints, objective) as defined in the abstract formulation.

### Step 2 - Configure Solver and Set Options
- Create a solver object: `SolverFactory('gurobi')`.
- Set solver options: `'MIPGap'=0.0001`, `'TimeLimit'=30`, `'Threads'=4`, `'Seed'=42` for reproducibility.

### Step 3 - Solve and Check Termination Conditions
- Call `solver.solve(model, tee=False)`.
- Check both the solver status (`model.solver.status`) and termination condition (`model.solver.termination_condition`). Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 4 - Extract Solution and Reconstruct Tour
- Load the solution into the model instance.
- Iterate over `model.x` to find arcs with `value(model.x[i,j]) > 0.5`.
- Build the tour sequence by starting at the depot and following selected arcs.
- Retrieve position values `value(model.u[i])` for validation.

### Step 5 - Output Structured Results
- Return a dictionary or JSON containing the tour, total cost, solver status, and runtime.
- For failed solves, include the termination condition and any error messages.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=node_indices)
model.A = pyo.Set(initialize=[(i,j) for i in model.N for j in model.N if i != j])

model.cost = pyo.Param(model.A, initialize=cost_dict)
model.depot = depot_index
model.n = n_nodes

model.x = pyo.Var(model.A, within=pyo.Binary)
model.u = pyo.Var(model.N, within=pyo.NonNegativeIntegers, bounds=(0, n_nodes-1))

def outflow_rule(model, i):
    return sum(model.x[i,j] for j in model.N if j != i) == 1
model.outflow = pyo.Constraint(model.N, rule=outflow_rule)

def inflow_rule(model, j):
    return sum(model.x[i,j] for i in model.N if i != j) == 1
model.inflow = pyo.Constraint(model.N, rule=inflow_rule)

def mtz_rule(model, i, j):
    if j != model.depot and i != j:
        return model.u[i] - model.u[j] + model.n * model.x[i,j] <= model.n - 1
    return pyo.Constraint.Skip
model.mtz = pyo.Constraint(model.N, model.N, rule=mtz_rule)

model.depot_pos = pyo.Constraint(expr=model.u[model.depot] == 0)

def obj_rule(model):
    return sum(model.cost[i,j] * model.x[i,j] for (i,j) in model.A)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = 0.0001
solver.options['TimeLimit'] = 30
solver.options['Threads'] = 4
solver.options['Seed'] = III

results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    # Load solution
    model.solutions.load_from(results)
    # Extract tour
    tour = [model.depot]
    current = model.depot
    visited = set(tour)
    while len(visited) < n_nodes:
        for j in model.N:
            if j != current and pyo.value(model.x[current,j]) > 0.5:
                tour.append(j)
                current = j
                visited.add(j)
                break
    print(f"Optimal tour: {tour}")
    print(f"Total cost: {pyo.value(model.obj)}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Accessing variable values without first checking solver status and loading the solution, resulting in `None` or default values.
- Setting `MIPGap` to a negative value (use `0.0` for optimality or a small positive tolerance).
- Not using `Constraint.Skip` for conditional MTZ constraints, which creates invalid constraints for the depot return arc.
