---
name: Balanced Transportation Problem Solver
description: |
  Model and solve balanced transportation/assignment problems with supply-demand equality, capacity limits, and linear cost minimization using LP/MIP solvers.
---

# Workflow 1 (OR-Tools LP/MIP)

## Modeling stage

### Strategy Overview
Model the problem as a balanced transportation linear program using Google OR-Tools' `pywraplp` interface. This workflow is suited for rapid prototyping and leverages efficient LP/MIP solvers (GLOP, CBC, SCIP) with a procedural API.

### Step 1 - Define Data Structures and Verify Balance
- Represent supply (sources) and demand (destinations) as lists or arrays.
- Store cost and capacity per (source, destination) pair in 2D structures (e.g., list of lists, dictionaries).
- Verify total supply equals total demand; if unbalanced, add a dummy source or destination with zero cost to balance the problem.
- Example: `assert sum(supply) == sum(demand), "Problem is unbalanced, add dummy node."`

### Step 2 - Create Decision Variables
- Instantiate a solver object (e.g., `solver = pywraplp.Solver.CreateSolver('GLOP')`).
- Create continuous or integer decision variables `x[i][j]` representing assignment quantity from source i to destination j.
- Set variable bounds: lower bound 0, upper bound `capacity[i][j]` (or `solver.infinity()` if no capacity).
- Example: `x[i][j] = solver.NumVar(0, capacity[i][j], f'x_{i}_{j}')` for continuous.

### Step 3 - Formulate Supply and Demand Constraints
- For each source i, add a supply constraint: sum of assignments to all destinations equals supply[i].
- For each destination j, add a demand constraint: sum of assignments from all sources equals demand[j].
- Use `solver.Add(sum(x[i][j] for j in destinations) == supply[i])` for clarity.

### Step 4 - Define Linear Objective
- Build a linear expression summing `cost[i][j] * x[i][j]` over all i, j.
- Set the objective to minimization using `solver.Minimize(objective_expr)`.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "destinations"
  ],
  "parameters": [
    {"name": "supply", "index": "sources"},
    {"name": "demand", "index": "destinations"},
    {"name": "cost", "index": ["sources", "destinations"]},
    {"name": "capacity", "index": ["sources", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "type": "continuous", "bounds": "[0, capacity[i][j]]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in sources for j in destinations)"
  },
  "constraints": [
    {"name": "supply_constraint", "index": "sources", "expression": "sum(x[i][j] for j in destinations) == supply[i]"},
    {"name": "demand_constraint", "index": "destinations", "expression": "sum(x[i][j] for i in sources) == demand[j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to balance total supply and demand before creating equality constraints, leading to infeasibility.
- Using `solver.NumVar` without specifying upper bounds, implicitly allowing infinite assignment.
- Not checking solver status after solve, assuming optimality.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' solver wrappers, with explicit status checking and solution extraction. This stage handles both LP and MIP solving with configurable parameters.

### Step 1 - Configure and Execute Solver
- Select solver backend based on variable type: `'GLOP'` for continuous LP, `'CBC'` or `'SCIP'` for MIP.
- Set solver parameters if needed (e.g., time limit, threads).
- Call `solver.Solve()` and capture the result status.

### Step 2 - Check Solution Status
- Verify solver status is `OPTIMAL` or `FEASIBLE` before extracting values.
- Example: `if status in (solver.OPTIMAL, solver.FEASIBLE):`
- If status is not acceptable, report the status and investigate infeasibility/unboundedness.

### Step 3 - Extract and Verify Solution
- Retrieve objective value via `solver.Objective().Value()`.
- Extract variable values using `x[i][j].solution_value()` for all non-zero assignments.
- Optionally, programmatically verify constraints by recomputing sums and comparing to supply/demand values.

### Step 4 - Output Results
- Print objective value and a summary of assignments (e.g., non-zero flows).
- Include constraint verification for transparency (e.g., print actual vs required supply/demand per node).

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... variable and constraint creation ...
# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'Objective value: {solver.Objective().Value()}')
    for i in sources:
        for j in destinations:
            val = x[i][j].solution_value()
            if val > 1e-6:
                print(f'x[{i},{j}] = {val}')
else:
    print(f'Solver failed with status: {status}')
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; it only guarantees a feasible solution.
- Not handling numerical precision when checking variable values (use a small epsilon like 1e-6).
- Omitting solver parameter configuration for large problems, leading to long solve times.

# Workflow 2 (Pyomo with Highs/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling syntax, separating data from structure. This workflow is suited for integration with larger optimization systems and supports advanced solver backends like Highs or CBC via `SolverFactory`.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for sources and destinations.
- Declare `Param` objects for supply, demand, cost, and capacity, indexed by the appropriate sets.
- This creates a clean separation between model structure and data instantiation.

### Step 2 - Create Decision Variables with Bounds
- Define a Pyomo `Var` indexed by (source, destination) with domain `pyo.NonNegativeReals`.
- Set variable upper bounds directly using the `bounds` argument referencing the capacity parameter.
- Example: `model.x = pyo.Var(model.sources, model.destinations, domain=pyo.NonNegativeReals, bounds=(0, model.capacity))`

### Step 3 - Build Constraints Using Rules
- Define supply and demand constraints as Pyomo `Constraint` objects with rule functions.
- The rule function for supply takes the model and source index, returns the equality expression.
- Similarly, demand constraint rule uses destination index.
- This approach enables easy model inspection and modification.

### Step 4 - Formulate Objective
- Define a Pyomo `Objective` with rule summing `cost[i,j] * x[i,j]` and sense `minimize`.

### Formulation Template
```json
{
  "sets": [
    {"name": "sources"},
    {"name": "destinations"}
  ],
  "parameters": [
    {"name": "supply", "index": "sources"},
    {"name": "demand", "index": "destinations"},
    {"name": "cost", "index": ["sources", "destinations"]},
    {"name": "capacity", "index": ["sources", "destinations"]}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "domain": "NonNegativeReals", "bounds": "(0, capacity[i,j])"}
  ],
  "objective": {
    "sense": "minimize",
    "rule": "sum(cost[i,j] * x[i,j] for i in sources for j in destinations)"
  },
  "constraints": [
    {"name": "supply_constraint", "index": "sources", "rule": "sum(x[i,j] for j in destinations) == supply[i]"},
    {"name": "demand_constraint", "index": "destinations", "rule": "sum(x[i,j] for i in sources) == demand[j]"}
  ]
}
```

### Common Pitfalls
- Mixing abstract and concrete model syntax incorrectly, leading to initialization errors.
- Forgetting to initialize parameters before solving, resulting in uninitialized values.
- Not using `bounds` for capacity limits, instead creating separate constraints which increase model size.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., Highs for LP, CBC for MIP) with configurable options. Leverage Pyomo's status and termination condition checks for robust solution handling.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object via `pyo.SolverFactory('highs')` (or `'cbc'`).
- Set solver options such as time limit, optimality gap, and number of threads.
- Example: `solver.options['time_limit'] = 30`

### Step 2 - Solve and Capture Results
- Call `solver.solve(model)` and capture the results object.
- Access solver status and termination condition from the results object.

### Step 3 - Validate Solution Status
- Check that solver status is `ok` and termination condition is `optimal` or `feasible`.
- If termination is `optimal`, the solution is proven optimal. If `feasible`, it is a valid but not necessarily optimal solution.
- Handle other termination conditions (e.g., `infeasible`, `unbounded`) with appropriate messages.

### Step 4 - Extract and Report Solution
- Retrieve objective value using `pyo.value(model.obj)`.
- Iterate over variables to extract non-zero assignments, using `pyo.value(model.x[i,j])`.
- Optionally, compute and report constraint satisfaction for verification.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective ...
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)
if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print('Optimal solution found.')
    elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
        print('Feasible solution found (not proven optimal).')
    else:
        print(f'Termination condition: {results.solver.termination_condition}')
    print(f'Objective: {pyo.value(model.obj)}')
    # Extract variable values...
else:
    print('Solver failed.')
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`); both must be checked.
- Not using `pyo.value()` to extract objective and variable values, leading to Pyomo expression objects.
- Ignoring solver options for large models, resulting in excessive solve times or memory usage.
