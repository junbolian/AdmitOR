---
name: Fixed-Charge Network Flow Modeling
description: |
  Model and solve network flow problems with fixed connection costs and variable flow costs using mixed-integer linear programming, with workflows for Pyomo/Gurobi and OR-Tools/SCIP.
---

# Workflow 1 (Pyomo with Gurobi/HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's structured modeling environment to build a mixed-integer linear program (MILP) for fixed-charge network flow. It emphasizes clean separation of sets, parameters, variables, and constraints, suitable for integration with high-performance solvers like Gurobi or HiGHS.

### Step 1 - Define Network Structure
- Create sets for nodes and directed arcs. Generate all possible ordered pairs `(i, j)` where `i != j` to represent potential connections.
- Define supply/demand parameters for each node, using a sign convention where positive values indicate net supply (outflow) and negative values indicate net demand (inflow).

### Step 2 - Parameterize Costs and Capacities
- Store fixed connection costs, variable flow costs per unit, and arc capacities as Pyomo `Param` objects indexed by the arc set.
- Ensure all required data is provided or generated deterministically (e.g., using formulas or seeded random values) before model instantiation.

### Step 3 - Create Decision Variables
- Define binary variables `y[i,j]` for arc activation (connection selection).
- Define continuous, non-negative variables `x[i,j]` for flow amounts on each arc.

### Step 4 - Formulate Constraints
- **Flow Conservation:** For each node `i`, enforce `sum(x[i,j] for all j) - sum(x[j,i] for all j) == supply[i]`.
- **Activation-Capacity Coupling:** For each arc `(i,j)`, enforce `x[i,j] <= capacity[i,j] * y[i,j]`. This ensures flow is zero if the connection is not selected and respects the arc capacity.

### Step 5 - Define Objective Function
- Minimize the sum of fixed and variable costs: `sum(fixed_cost[i,j] * y[i,j] + var_cost[i,j] * x[i,j])` over all arcs.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i, j in N, i != j"
  ],
  "parameters": [
    "supply[N]: net supply (positive) or demand (negative) at each node",
    "fixed_cost[A]: cost incurred if arc is activated",
    "var_cost[A]: cost per unit of flow on arc",
    "capacity[A]: maximum flow allowed on arc"
  ],
  "decision_variables": [
    "y[A] ∈ {0,1}: binary activation variable for arc",
    "x[A] ≥ 0: continuous flow variable on arc"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{A} (fixed_cost[i,j] * y[i,j] + var_cost[i,j] * x[i,j])"
  },
  "constraints": [
    "flow_conservation[N]: sum_{j} x[i,j] - sum_{j} x[j,i] == supply[i] for all i in N",
    "activation_capacity[A]: x[i,j] <= capacity[i,j] * y[i,j] for all (i,j) in A"
  ]
}
```

### Common Pitfalls
- Using incomplete or guessed parameter values when only ranges are provided; always request specific data or treat the model as a parameterized template.
- Incorrectly implementing flow conservation sign conventions, leading to infeasibility.
- Multiplying `Param` objects and `Var` objects incorrectly inside generator expressions; define constraints within rule functions.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver (Gurobi or HiGHS) with appropriate performance and termination settings. Focus on verifying solver status, extracting results, and rigorously validating solution feasibility.

### Step 1 - Configure Solver and Options
- Instantiate the solver via `SolverFactory("gurobi")` or `SolverFactory("highs")`.
- Set key options: `TimeLimit` for runtime control, `MIPGap` (or `mip_rel_gap`) for optimality tolerance (e.g., 1e-4), `Threads` for parallelism, and `Seed` for reproducibility.

### Step 2 - Solve and Check Status
- Call `solver.solve(model, tee=True)` to execute and log progress.
- Check both `solver.status == SolverStatus.ok` and `termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}` before attempting to load the solution.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value with `pyo.value(model.obj)`.
- Identify active arcs where `pyo.value(model.y[i,j]) > 0.5` and their corresponding flows `pyo.value(model.x[i,j])`.
- Perform post-solution verification: recompute net flow at each node and compare to supply/demand values within a small tolerance (e.g., 1e-6). Ensure capacity and activation constraints hold.

### Step 4 - Output Structured Results
- Print or return a structured summary including total cost, cost breakdown (fixed vs. variable), list of active connections with flows, and verification status.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (example snippet)
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(initialize=arcs, dimen=2)
# ... define parameters, variables, objective, constraints per formulation

# Solve with Gurobi
solver = pyo.SolverFactory("gurobi")
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = -1e-4
solver.options["Threads"] = 4
solver.options["Seed"] = 42
results = solver.solve(model, tee=True)

# Check status and extract
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    active_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.y[i,j]) > 0.5]
    # ... verification and output
else:
    # Handle failed solve
    print("Solve failed:", results.solver.termination_condition)
```

### Common Pitfalls
- Not checking termination condition, leading to errors when trying to access solution values from an infeasible or unbounded model.
- Setting invalid solver parameters (e.g., negative MIPGap).
- Assuming solver status "ok" alone guarantees a feasible solution; always check termination condition.

# Workflow 2 (OR-Tools with SCIP)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT/MIP solver (with SCIP backend) for a more imperative, code-centric modeling style. It is well-suited for embedding within larger applications and offers fine-grained control over variable and constraint creation.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Precompute data structures: lists of nodes, arcs, and dictionaries for costs, capacities, and demands.

### Step 2 - Create Variables with Bounds
- For each arc `(i,j)`, create a binary variable `y[i,j] = solver.BoolVar(name)` for activation.
- Create a continuous flow variable `x[i,j] = solver.NumVar(0, capacity[i,j], name)`, directly setting the upper bound to the arc capacity.

### Step 3 - Build Flow Conservation Constraints
- For each node `i`, explicitly loop over all arcs to collect inflow terms (arcs ending at `i`) and outflow terms (arcs starting from `i`).
- Add the constraint: `solver.Sum(inflow_terms) - solver.Sum(outflow_terms) == demand[i]`.

### Step 4 - Link Flow to Activation
- For each arc `(i,j)`, add the linear constraint `x[i,j] <= capacity[i,j] * y[i,j]`. This couples the continuous and binary variables.

### Step 5 - Set Linear Objective
- Build the objective expression as `solver.Sum(fixed_cost[i,j] * y[i,j] + var_cost[i,j] * x[i,j])` over all arcs.
- Set the objective to minimization: `solver.Minimize(obj_expr)`.

### Formulation Template
```json
{
  "sets": [
    "N: list of nodes",
    "A: list of directed arcs (i,j)"
  ],
  "parameters": [
    "demand[N]: net demand (positive for sink, negative for source)",
    "fixed_cost[A], var_cost[A]: cost parameters",
    "capacity[A]: maximum flow"
  ],
  "decision_variables": [
    "y[A] ∈ {0,1}: binary activation",
    "x[A] ∈ [0, capacity[A]]: continuous flow"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{A} (fixed_cost[i,j] * y[i,j] + var_cost[i,j] * x[i,j])"
  },
  "constraints": [
    "flow_conservation[N]: sum_{a in incoming(i)} x[a] - sum_{a in outgoing(i)} x[a] == demand[i]",
    "activation_capacity[A]: x[i,j] <= capacity[i,j] * y[i,j]"
  ]
}
```

### Common Pitfalls
- Using generator expressions that may cause key errors when building inflow/outflow lists; prefer explicit loops.
- Forgetting to set upper bounds on flow variables during creation, which can lead to a looser formulation.
- Not precomputing incoming/outgoing arc lists, resulting in O(n²) constraint building for each node.

## Solving stage

### Strategy Overview
Solve the OR-Tools model, check the result status, and extract the solution. Emphasize robust error handling and post-solution validation to ensure correctness.

### Step 1 - Execute Solve
- Call `solver.Solve()` to run the optimization.
- The solver will use the SCIP backend by default for MIP problems.

### Step 2 - Verify Solver Status
- Check the result status: `status = solver.Solve()`.
- Accept `pywraplp.Solver.OPTIMAL` or `FEASIBLE` statuses before extracting variable values.

### Step 3 - Extract Solution Values
- For each binary variable `y[i,j]`, check `y[i,j].solution_value() > 0.5` to identify active connections.
- For each flow variable `x[i,j]`, retrieve `x[i,j].solution_value()` (values below a small epsilon can be considered zero).
- Compute the objective value via `solver.Objective().Value()`.

### Step 4 - Validate Solution
- Recompute net flow at each node using the extracted flow values and compare to the original demand within tolerance (e.g., 0.001).
- Verify that for every arc, `flow <= capacity * activation_flag`.
- Print a summary of active arcs, flows, and cost breakdown.

### Step 5 - Handle Failures Gracefully
- If status is not optimal or feasible, return a structured error message indicating the solver status (e.g., `INFEASIBLE`, `UNBOUNDED`).
- For infeasible cases, verify that total supply equals total demand as a first check.

### Code Usage
```python
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
# ... create variables, constraints, objective as per modeling stage

status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    active_arcs = []
    for (i,j) in arcs:
        if y[i,j].solution_value() > 0.5:
            active_arcs.append(((i,j), x[i,j].solution_value()))
    # Post-solution validation
    for i in nodes:
        inflow = sum(x[j,i].solution_value() for (j,k) in arcs if k == i)
        outflow = sum(x[i,j].solution_value() for (j,k) in arcs if j == i)
        if abs((inflow - outflow) - demand[i]) > 1e-6:
            print(f"Flow conservation violation at node {i}")
    # Output results
    print(f"Total cost: {total_cost}")
    print(f"Active connections: {active_arcs}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming `solver.Solve()` returns a boolean; it returns an integer status code that must be compared to `OPTIMAL` or `FEASIBLE`.
- Not handling the case where the solver finds a feasible but not proven optimal solution.
- Attempting to access `.solution_value()` on variables when the solver status indicates failure, causing runtime errors.
