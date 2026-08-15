---
name: BinaryFlowNetworkSolver
description: |
  Model and solve binary flow network problems (e.g., shortest path, arc selection) using flow conservation and binary arc variables, with robust solving and solution extraction.
---

# Workflow 1 (OR-Tools SCIP MIP)

## Modeling stage

### Strategy Overview
Model the binary flow network as a Mixed-Integer Program (MIP) using the OR-Tools linear solver wrapper. This approach is suitable for direct, low-level model construction and solving with the SCIP solver, focusing on efficient variable and constraint generation via Python comprehensions.

### Step 1 - Define Sets and Parameters
- Define the set of nodes `N` (e.g., `nodes = ["A", "B", "C"]`).
- Define a cost dictionary `cost` keyed by directed arc tuples `(i, j)` for `i != j`, representing the cost of using that arc.
- Identify the source node `s` and sink node `t`.

### Step 2 - Create Binary Decision Variables
- For each directed arc `(i, j)` where `i` and `j` are in `N` and `i != j`, create a binary variable `x[(i, j)]`.
- Use `solver.BoolVar(f"x_{i}_{j}")` to create the variable and store it in a dictionary for easy access.

### Step 3 - Formulate Flow Conservation Constraints
- **Source Constraint**: Enforce `outflow_s - inflow_s = 1`. Compute outflow as `sum(x[(s, j)] for j in N if j != s)` and inflow as `sum(x[(i, s)] for i in N if i != s)`.
- **Sink Constraint**: Enforce `inflow_t - outflow_t = 1`. Compute inflow as `sum(x[(i, t)] for i in N if i != t)` and outflow as `sum(x[(t, j)] for j in N if j != t)`.
- **Intermediate Node Constraints**: For each node `k` not `s` or `t`, enforce `inflow_k == outflow_k`, where `inflow_k = sum(x[(i, k)] for i in N if i != k)` and `outflow_k = sum(x[(k, j)] for j in N if j != k)`.

### Step 4 - Define the Objective Function
- Formulate the objective to minimize total cost: `sum(cost[(i, j)] * x[(i, j)] for (i, j) in cost.keys())`.

### Formulation Template
```json
{
  "sets": ["N (nodes)"],
  "parameters": ["cost[(i,j)] (arc cost)", "s (source)", "t (sink)"],
  "decision_variables": ["x[(i,j)] ∈ {0,1} (arc selection)"],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j)} cost[(i,j)] * x[(i,j)]"
  },
  "constraints": [
    "source_flow: ∑_j x[s,j] - ∑_i x[i,s] = 1",
    "sink_flow: ∑_i x[i,t] - ∑_j x[t,j] = 1",
    "∀ k ∈ N \\ {s,t}: ∑_i x[i,k] = ∑_j x[k,j]"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops (`i != j`) when creating variables and summing flows, which can lead to invalid models.
- Incorrectly implementing the net flow sign for source/sink (must be `+1` for source outflow net, `+1` for sink inflow net).
- Using a dense cost matrix for sparse networks; prefer a dictionary keyed only by existing arcs.

## Solving stage

### Strategy Overview
Solve the built MIP using the SCIP solver via OR-Tools, with careful configuration for optimality, extraction of the solution path, and verification of results.

### Step 1 - Configure and Run the Solver
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set a time limit if needed: `solver.SetTimeLimit(time_limit_ms)`.
- Call `solver.Solve()` to initiate the solving process.

### Step 2 - Check Solver Status and Extract Solution
- Check the result status: `status = solver.Solve()`.
- Verify `status in (solver.OPTIMAL, solver.FEASIBLE)` before proceeding.
- Extract the objective value: `obj_val = solver.Objective().Value()`.

### Step 3 - Identify Selected Arcs and Build Path
- Iterate over all binary variables `x[(i, j)]`.
- Collect arcs where `var.solution_value() > 0.5` (accounting for numerical tolerance) into a list `selected_arcs`.
- Optionally, reconstruct the ordered path from `s` to `t` from the selected arcs.

### Step 4 - Output and Verify Results
- Output a structured result containing status, objective value, and selected arcs.
- Perform a sanity check: verify that the selected arcs form a simple path from `s` to `t` and satisfy flow conservation.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (build variables, constraints, objective as per modeling stage)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    selected_arcs = [(i, j) for (i, j), var in x.items() if var.solution_value() > 0.5]
    # Output results
else:
    # Handle infeasible/unbounded/no solution
```

### Common Pitfalls
- Not checking solver status, leading to errors when trying to extract values from an infeasible model.
- Using a strict equality (`== 1.0`) to test binary variable values; use a tolerance (e.g., `> 0.5`).
- Omitting a time limit for potentially large instances, risking long runtimes.

# Workflow 2 (Pyomo with CBC/SCIP)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract modeling capabilities, separating model construction from data. This approach is ideal for integration with various solvers (e.g., CBC, SCIP via AMPL interface) and supports advanced features like parameterized models and reusable templates.

### Step 1 - Define Abstract Sets and Parameters
- Define a Pyomo `Set` `model.N` for nodes.
- Define a Pyomo `Param` `model.c` over an `Arc` set, initialized from a cost dictionary. The `Arc` set can be defined explicitly from the dictionary keys to handle sparse networks.
- Declare source `s` and sink `t` as model parameters or external identifiers.

### Step 2 - Declare Binary Variables and Objective
- Declare a Pyomo `Var` `model.x` indexed by `model.N × model.N` (or `model.Arc`) with `domain=pyo.Binary`.
- Define the objective as `model.obj = pyo.Objective(expr=sum(model.c[i,j] * model.x[i,j] for (i,j) in model.Arc), sense=pyo.minimize)`.

### Step 3 - Implement Flow Conservation with Conditional Rules
- Create a `Constraint` `model.flow` indexed by `model.N`.
- In the constraint rule, use conditional logic: for `k == s`, enforce net outflow = 1; for `k == t`, enforce net inflow = 1; for all other `k`, enforce inflow equals outflow.
- Explicitly add constraints `model.x[i,i] == 0` to forbid self-loops.

### Step 4 - (Optional) Add Model Validations
- Add assertions or constraints to ensure `s` and `t` are distinct and within `model.N`.
- For sparse networks, ensure the `Arc` set includes only defined connections to avoid referencing non-existent parameters.

### Formulation Template
```json
{
  "sets": ["N (nodes)", "Arc ⊆ N × N (defined arcs)"],
  "parameters": ["c[i,j] (arc cost)", "s (source)", "t (sink)"],
  "decision_variables": ["x[i,j] ∈ {0,1} (arc selection)"],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j) ∈ Arc} c[i,j] * x[i,j]"
  },
  "constraints": [
    "∀ i ∈ N: x[i,i] = 0",
    "flow_s: ∑_{(s,j) ∈ Arc} x[s,j] - ∑_{(i,s) ∈ Arc} x[i,s] = 1",
    "flow_t: ∑_{(i,t) ∈ Arc} x[i,t] - ∑_{(t,j) ∈ Arc} x[t,j] = 1",
    "∀ k ∈ N \\ {s,t}: ∑_{(i,k) ∈ Arc} x[i,k] = ∑_{(k,j) ∈ Arc} x[k,j]"
  ]
}
```

### Common Pitfalls
- Defining the `Arc` set as the full Cartesian product `N × N` in sparse networks, creating many unnecessary variables and parameters.
- Forgetting to handle self-loops, which can lead to degenerate solutions.
- Incorrectly indexing parameters or variables in constraint rules due to set membership errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a compatible MIP solver (e.g., CBC, SCIP) via the `SolverFactory`, with proper configuration for optimality gap, time limits, and solution extraction that handles numerical tolerances.

### Step 1 - Configure the Solver Instance
- Instantiate the solver: `solver = pyo.SolverFactory('cbc')`.
- Set solver options: e.g., `solver.options['seconds'] = time_limit`, `solver.options['ratio'] = 0.0` for optimality gap, and `solver.options['threads'] = threads`.
- For deterministic results, set a random seed if supported by the solver.

### Step 2 - Solve and Check Termination Status
- Call `results = solver.solve(model, tee=False)` (use `tee=True` for debug output).
- Check the solver status: `status = results.solver.status`.
- Check the termination condition: `term = results.solver.termination_condition`.
- Proceed only if `status == SolverStatus.ok` and `term in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Extract and Interpret the Solution
- Extract the objective value: `obj_val = pyo.value(model.obj)`.
- Iterate over the `Arc` set and collect arcs where `pyo.value(model.x[i,j]) > 0.5` into a solution list.
- Compute and optionally report node inflows/outflows for verification.

### Step 4 - Package Results for Downstream Use
- Return a dictionary or object containing the model, solver results, objective value, selected arcs, and status information.
- For failed solves, provide clear error information (e.g., infeasible, unbounded, time limit).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (build sets, params, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = time_limit
solver.options['ratio'] = 0.0
results = solver.solve(model)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    obj_val = pyo.value(model.obj)
    selected_arcs = [(i, j) for (i, j) in model.Arc if pyo.value(model.x[i,j]) > 0.5]
    # Output results
else:
    # Handle solve failure
```

### Common Pitfalls
- Not setting `ratio` (optimality gap) to `0.0`, leading the solver to return a suboptimal solution.
- Confusing `solver.status` and `solver.termination_condition`; both must be checked for a valid solution.
- Accessing variable values without first checking solver status, which may raise exceptions.
