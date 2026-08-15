---
name: MultiCommodityFlowNetworkOptimization
description: |
  Model and solve multi-commodity flow problems on directed networks with layered capacity constraints and linear costs using structured formulations and robust solver integration.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for declarative model construction, separating sets, parameters, variables, constraints, and objective. It is designed for clarity and integration with open-source solvers like HiGHS (LP) or CBC (MIP).

### Step 1 - Define Sets and Parameters
- Define comprehensive sets for nodes, commodities, and directed arcs. Generate arcs programmatically for a complete directed graph.
- Structure parameters hierarchically using dictionaries with composite keys (e.g., `product_capacity[(i,j)][p]`, `net_flow[node][commodity]`) to enable clean access in constraint rules.

### Step 2 - Create Decision Variables
- Create a Pyomo `Var` object for flow on each arc-commodity pair, `model.x[i,j,p]`. Set lower bound to 0 and upper bound directly from the product-specific capacity parameter.

### Step 3 - Formulate Flow Conservation Constraints
- For each node and commodity, enforce flow conservation: `sum(inflow) - sum(outflow) = net_flow[node, commodity]`. Use Pyomo constraint rules with list comprehensions over the arc set.

### Step 4 - Layer Capacity Constraints
- Apply a joint capacity constraint per arc: `sum(model.x[i,j,p] for p in commodities) <= joint_capacity_limit`.
- Apply individual commodity capacity constraints per arc: `model.x[i,j,p] <= product_capacity[(i,j)][p]`.

### Step 5 - Define Linear Cost Objective
- Define the objective to minimize total linear cost: `sum(cost_per_unit * model.x[i,j,p] for (i,j) in arcs for p in commodities)`.

### Formulation Template
```json
{
  "sets": [
    "nodes",
    "commodities",
    "arcs (directed pairs of nodes)"
  ],
  "parameters": [
    "net_flow[node][commodity] (supply > 0, demand < 0)",
    "product_capacity[arc][commodity]",
    "joint_capacity[arc]",
    "cost_per_unit"
  ],
  "decision_variables": [
    "x[arc][commodity] (non-negative flow)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_per_unit * x[i,j,p] for (i,j) in arcs for p in commodities)"
  },
  "constraints": [
    "flow_conservation: for node i, commodity p: sum(x[j,i,p] for j in nodes if (j,i) in arcs) - sum(x[i,j,p] for j in nodes if (i,j) in arcs) = net_flow[i][p]",
    "joint_capacity: for arc (i,j): sum(x[i,j,p] for p in commodities) <= joint_capacity[i,j]",
    "commodity_capacity: for arc (i,j), commodity p: x[i,j,p] <= product_capacity[i,j][p]",
    "non_negativity: x[i,j,p] >= 0"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops when generating the directed arc set, which can lead to meaningless variables.
- Incorrectly signing the flow conservation rule (outflow - inflow vs. inflow - outflow); always align with the definition of `net_flow`.
- Using loose numerical tolerances when checking solution feasibility; recompute constraints with the same precision as the solver.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver factory (HiGHS for LP, CBC for MIP). Focus on robust status checking, solution verification, and extraction of non-zero flows.

### Step 1 - Configure and Execute Solver
- Instantiate the solver via `SolverFactory("solver_name")` (e.g., "highs" or "cbc").
- Set key options: `time_limit`, `mip_rel_gap=0.0` for exact solutions, and `threads` for parallel processing if supported.

### Step 2 - Check Solver Status and Termination
- After solving, check both `solver.status == SolverStatus.ok` and `model.solutions[0].termination_condition in {optimal, feasible}`.
- If status is not ok or termination is not optimal/feasible, report the condition and avoid extracting invalid results.

### Step 3 - Extract and Validate Results
- Extract the objective value via `pyo.value(model.obj)`.
- Iterate through flow variables, collecting those with value > tolerance (e.g., `1e-6`) to avoid numerical noise.
- Programmatically verify key constraints by recomputing flow balances and capacity usage from extracted flows.

### Step 4 - Output Standardized Results
- Print the total cost and a summary of non-zero flows.
- For automated parsing, output a line like `RESULT:{total_cost}`.
- Include detailed verification output only in debug mode.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (function implementing the formulation template)
model = build_model(data)

# Solve
solver = pyo.SolverFactory("highs")  # or "cbc"
solver.options['time_limit'] = 30
results = solver.solve(model)

# Check status
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Extract results
    total_cost = pyo.value(model.obj)
    flows = [(i,j,p, pyo.value(model.x[i,j,p])) for (i,j,p) in model.x if pyo.value(model.x[i,j,p]) > 1e-6]
    print(f"Total Cost: {total_cost}")
    print(f"RESULT:{total_cost}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming a solved model is optimal without checking `termination_condition`.
- Not setting a time limit, which can cause indefinite runs on large or difficult instances.
- Extracting variable values without verifying the solver status, leading to errors.

# Workflow 2 (OR-Tools with GLOP/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools for imperative model construction, creating variables and constraints directly via solver methods. It is efficient for linear and mixed-integer problems and provides fine-grained control.

### Step 1 - Initialize Solver and Create Variables
- Choose solver based on variable types: `GLOP` for continuous LP, `CBC` for MIP.
- Create flow variables using `solver.NumVar(lower_bound, upper_bound, name)`, where the upper bound is the product-specific capacity.

### Step 2 - Enforce Flow Conservation
- For each node and commodity, create a linear constraint: `sum(inflow_vars) - sum(outflow_vars) == net_flow_value`.
- Use solver methods to add the constraint, building coefficient lists programmatically.

### Step 3 - Apply Layered Capacity Constraints
- Add a joint capacity constraint per arc: `sum(flow_vars_for_all_commodities_on_arc) <= joint_capacity_limit`.
- The individual commodity capacity is already enforced via the variable upper bound.

### Step 4 - Define Linear Cost Objective
- Set the objective to minimize `sum(cost_per_unit * flow_variable)` across all arcs and commodities.

### Formulation Template
```json
{
  "sets": [
    "nodes",
    "commodities",
    "arcs (directed pairs of nodes)"
  ],
  "parameters": [
    "net_flow[node][commodity]",
    "product_capacity[arc][commodity]",
    "joint_capacity[arc]",
    "cost_per_unit"
  ],
  "decision_variables": [
    "x[arc][commodity] (solver.NumVar with bounds 0, product_capacity)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_per_unit * x[i,j,p])"
  },
  "constraints": [
    "flow_conservation: for node i, commodity p: sum(x[j,i,p]) - sum(x[i,j,p]) = net_flow[i][p]",
    "joint_capacity: for arc (i,j): sum(x[i,j,p]) <= joint_capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Manually managing coefficient lists for constraints can lead to indexing errors; use loops and clear data structures.
- Forgetting to set a practical time limit on the solver, risking long runtimes.
- Not using variable upper bounds to encode simple capacity constraints, which adds unnecessary constraints.

## Solving stage

### Strategy Overview
Solve the OR-Tools model with configured parameters, extract the solution, and perform rigorous verification of constraint satisfaction and objective value.

### Step 1 - Configure Solver and Solve
- Set a time limit using `solver.SetTimeLimit(milliseconds)` to prevent indefinite runs.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Validate Solution Status
- Check if the result is `OPTIMAL` or `FEASIBLE`. Handle other statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) with appropriate error messages.

### Step 3 - Extract and Verify Solution
- Extract variable values using `variable.solution_value()`.
- Compute a theoretical lower bound (e.g., `(cost_per_unit * total_absolute_net_flow) / 2`) for quick sanity checking.
- Programmatically re-evaluate all flow conservation and capacity constraints to verify feasibility within a small tolerance.

### Step 4 - Output Diagnostics
- Print a summary of shipments (non-zero flows) and total flow per arc.
- Output the total cost and a verification report.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')  # or 'CBC'
solver.SetTimeLimit(30000)

# Create variables and add constraints (based on formulation)
# ... (model construction code)

# Solve
status = solver.Solve()

# Check status and extract results
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    # Extract non-zero flows
    shipments = []
    for (i,j,p), var in flow_vars.items():
        val = var.solution_value()
        if val > 1e-6:
            shipments.append((i,j,p,val))
    print(f"Total Cost: {total_cost}")
    # Verify constraints
    verify_constraints(flow_vars, net_flow, joint_capacity)
else:
    print(f"Solver did not find a feasible solution. Status: {status}")
```

### Common Pitfalls
- Relying solely on solver status without verifying constraint satisfaction numerically.
- Not filtering near-zero flows, which clutters output with numerical noise.
- Omitting time limits, which is critical for production deployment.
