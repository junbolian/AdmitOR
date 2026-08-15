---
name: TSP_MTZ_Formulation
description: |
  Model and solve traveling salesman problems using Miller-Tucker-Zemlin subtour elimination with binary routing and integer position variables, across multiple solver backends.
---

# Workflow 1 (MIP Solver - OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the TSP as a Mixed-Integer Program (MIP) using the Miller-Tucker-Zemlin (MTZ) constraints. This approach uses binary variables for arc selection and integer variables for node ordering to eliminate subtours, suitable for exact solving with linear MIP solvers.

### Step 1 - Define Core Variables
- Create binary decision variables `x[i,j]` for each directed arc between distinct nodes, where `x[i,j] = 1` indicates the arc is part of the tour.
- Create integer decision variables `u[i]` for each node, representing its position in the tour sequence.

### Step 2 - Enforce Tour Structure
- Add constraints ensuring each node has exactly one incoming and one outgoing selected arc.
- Add constraints explicitly forbidding self-loops (`x[i,i] = 0`).

### Step 3 - Implement Subtour Elimination
- Fix the position of the designated start node (e.g., `u[0] = 0`).
- For all other nodes, set appropriate lower and upper bounds on the position variable (e.g., `1 <= u[i] <= n-1`).
- Add MTZ constraints: `u[i] - u[j] + n * x[i,j] <= n-1` for all `i, j` where `i != j` and neither is the start node. This prevents cycles that do not include the start node.

### Step 4 - Set Objective
- Formulate the objective to minimize the total travel cost: sum of `cost[i,j] * x[i,j]` over all arcs.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (e.g., 0..n-1)"
  ],
  "parameters": [
    "cost[i,j]: travel cost from node i to node j, for i,j in N, i != j"
  ],
  "decision_variables": [
    "x[i,j]: binary, 1 if arc (i,j) is in tour, for i,j in N, i != j",
    "u[i]: integer, position of node i in tour, for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i,j in N, i != j)"
  },
  "constraints": [
    "FlowOut[i]: sum(x[i,j] for j in N, j != i) == 1, for i in N",
    "FlowIn[j]: sum(x[i,j] for i in N, i != j) == 1, for j in N",
    "NoSelf[i]: x[i,i] == 0, for i in N",
    "StartPos: u[start_node] == 0",
    "PosBound[i]: 1 <= u[i] <= n-1, for i in N, i != start_node",
    "MTZ[i,j]: u[i] - u[j] + n * x[i,j] <= n-1, for i,j in N, i != j, i != start_node, j != start_node"
  ]
}
```

### Common Pitfalls
- Using an insufficiently large `M` constant in the MTZ constraint; using `n` (number of nodes) is safe and standard.
- Forgetting to exclude the start node from the MTZ constraints, which can make the model infeasible.
- Not adding explicit self-loop constraints, which some solvers may not implicitly forbid.

## Solving stage

### Strategy Overview
Solve the MIP model using the OR-Tools wrapper for a MIP solver (e.g., SCIP, CBC). Focus on proper solver instantiation, parameter setting for performance, and robust solution extraction with status checking.

### Step 1 - Initialize Solver and Variables
- Instantiate the solver (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Create variable dictionaries (`x` and `u`) using the solver's variable creation methods with appropriate bounds.

### Step 2 - Add Constraints and Objective
- Use list comprehensions to efficiently add all flow conservation, self-loop, and MTZ constraints to the solver object.
- Set the minimization objective using the solver's `Objective()` method.

### Step 3 - Configure and Execute Solve
- Set solver parameters such as time limit, relative gap tolerance, and number of threads.
- Call `solver.Solve()` and capture the result status.

### Step 4 - Extract and Validate Solution
- Check if the status is `OPTIMAL` or `FEASIBLE` before accessing variable values.
- Reconstruct the tour by starting at the designated node and following arcs where `x[i,j].solution_value() > 0.5`.
- Verify solution consistency by checking that all nodes are visited exactly once and the extracted tour cost matches the reported objective value.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... variable creation, constraint addition, objective setting ...

# solve with status / termination checks
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)
status = solver.Solve()

if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    # Extract tour from x[i,j] variables
    tour = [start_node]
    current = start_node
    for _ in range(len(nodes)-1):
        for j in nodes:
            if j != current and x[current, j].solution_value() > 0.5:
                tour.append(j)
                current = j
                break
    # ... process solution
else:
    # Handle infeasible or other status
    print(f"Solver did not find a feasible solution. Status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing `.solution_value()`, which can cause runtime errors.
- Using a naive O(n^2) loop to reconstruct the tour instead of following the `x` links.
- Setting an absolute optimality gap (`MIPGapAbs`) to zero, which can prevent the solver from terminating on large instances; use a small relative gap instead.

# Workflow 2 (AML with Pyomo and Gurobi)

## Modeling stage

### Strategy Overview
Model the TSP using an Algebraic Modeling Language (Pyomo) for clear, declarative constraint expression. This separates the model logic from solver-specific code and leverages advanced commercial solver features like presolving and cutting planes.

### Step 1 - Declare Model Components
- Define abstract sets for nodes.
- Declare parameters for the cost matrix.
- Declare decision variables: `x` as `Binary` and `u` as `NonNegativeIntegers` with appropriate bounds.

### Step 2 - Express Constraints Declaratively
- Use Pyomo `Constraint` objects with rule functions to define flow conservation, self-loop prohibition, and position bounds.
- Implement the MTZ constraints using a conditional rule that skips invalid index combinations (e.g., `i == j`, `i` or `j` is start node).

### Step 3 - Define Objective
- Use Pyomo's `Objective` component to express the total cost minimization.

### Formulation Template
```json
{
  "sets": [
    "N: Pyomo Set of node indices"
  ],
  "parameters": [
    "cost: Pyomo Param indexed by (N, N)"
  ],
  "decision_variables": [
    "x: Pyomo Var indexed by (N, N), domain=Binary",
    "u: Pyomo Var indexed by N, domain=NonNegativeIntegers, bounds=(0, n-1)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in N for j in N if i != j)"
  },
  "constraints": [
    "OutDegree[i]: sum(x[i,j] for j in N) == 1",
    "InDegree[j]: sum(x[i,j] for i in N) == 1",
    "NoSelf[i]: x[i,i] == 0",
    "FixStart: u[start_node] == 0",
    "OrderBound[i]: inequality(1, u[i], n-1) for i != start_node",
    "MTZ[i,j]: u[i] - u[j] + n * x[i,j] <= n-1 for i,j in N, i != j, i != start_node, j != start_node"
  ]
}
```

### Common Pitfalls
- Inefficiently iterating over all `(i,j)` pairs in constraint rules without filtering, leading to redundant constraints.
- Incorrectly using `Constraint.Skip` logic, which can accidentally omit necessary constraints.
- Not defining variable bounds on `u[i]`, which can lead to poor solver performance or unbounded variables.

## Solving stage

### Strategy Overview
Solve the Pyomo model by interfacing with the Gurobi solver. Configure solver options for performance and robustness, and implement detailed status checking to handle edge cases like infeasibility or time limits.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object via `pyo.SolverFactory("gurobi")`.
- Set key options: time limit, optimality gap tolerance (`MIPGap`), number of threads, and random seed for reproducibility.

### Step 2 - Solve and Capture Results
- Call `solver.solve(model, tee=False)` to execute the solve without verbose output.
- Capture the returned results object.

### Step 3 - Analyze Termination Status
- Check `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 4 - Extract and Post-Process Solution
- Access the objective value via `pyo.value(model.obj)`.
- Extract the tour by iterating over the `x` variables and finding those with a value close to 1.
- Optionally, re-solve with aggressive cuts and presolve to verify optimality for the found solution.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=range(n))
# ... define parameters, variables, constraints, objective ...

# solve with status / termination checks
solver = pyo.SolverFactory("gurobi")
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = -1e-4  # Use negative value to set relative gap
solver.options["Threads"] = 4
solver.options["Seed"] = 42

results = solver.solve(model, tee=False)
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = float(pyo.value(model.obj))
    # Extract solution: iterate over model.x[i,j]
    tour = [start_node]
    current = start_node
    visited = {start_node}
    while len(visited) < len(model.N):
        for j in model.N:
            if j not in visited and pyo.value(model.x[current, j]) > 0.5:
                tour.append(j)
                visited.add(j)
                current = j
                break
    # ... process solution
else:
    # Handle infeasibility or other termination conditions
    print(f"Solve failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Setting `MIPGap` to exactly 0.0, which Gurobi may reject; use a small positive or negative value instead.
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal stops.
- Accessing variable values directly without first checking the solve status, which may raise errors if the model is unsolved.
