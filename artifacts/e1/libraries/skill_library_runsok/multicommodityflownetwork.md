---
name: MultiCommodityFlowNetwork
description: |
  Model and solve multi-commodity flow problems with shared and individual arc capacities, flow conservation per commodity, and linear transportation costs.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define sets, parameters, and variables declaratively. It is well-suited for problems where data can be cleanly separated from model structure, and leverages open-source solvers like HiGHS (LP) or CBC (MIP).

### Step 1 - Define Core Sets
- Identify and define the three fundamental index sets: nodes, commodities, and directed arcs.
- Generate the arc set programmatically to avoid manual listing errors, excluding self-loops.

### Step 2 - Declare Flow Variables
- Create a single indexed variable `x[i, j, p]` representing the flow of commodity `p` on directed arc `(i, j)`.
- Set the variable domain to `pyo.NonNegativeReals` to enforce non-negativity.

### Step 3 - Implement Flow Conservation
- For each node `i` and commodity `p`, enforce the balance constraint: `sum(inflow) - sum(outflow) = net_flow[i, p]`.
- Use comprehensions within constraint rules to sum over the appropriate variable indices.

### Step 4 - Layer Capacity Constraints
- First, add joint capacity constraints limiting the total flow of all commodities on each arc.
- Second, add commodity-specific capacity constraints as upper bounds on individual flows.

### Step 5 - Set Linear Cost Objective
- Define a linear objective to minimize total transportation cost, summing `unit_cost * x[i, j, p]` over all arcs and commodities.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes."},
    {"name": "K", "description": "Set of all commodities."},
    {"name": "A", "description": "Set of directed arcs (i, j) where i != j."}
  ],
  "parameters": [
    {"name": "net_flow", "index": ["N", "K"], "description": "Net supply (>0) or demand (<0) of commodity k at node i."},
    {"name": "joint_cap", "index": ["A"], "description": "Total capacity for all commodities on arc (i, j)."},
    {"name": "commodity_cap", "index": ["A", "K"], "description": "Capacity specific to commodity k on arc (i, j)."},
    {"name": "unit_cost", "description": "Cost per unit of flow on any arc for any commodity."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["A", "K"], "domain": "NonNegativeReals", "description": "Flow of commodity k on arc (i, j)."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( unit_cost * x[i, j, k] for (i, j) in A for k in K )"
  },
  "constraints": [
    {"name": "flow_conservation", "index": ["N", "K"], "expression": "sum( x[j, i, k] for (j, i) in A if i == i_fixed ) - sum( x[i_fixed, j, k] for (i_fixed, j) in A if i_fixed == i_fixed ) == net_flow[i_fixed, k]"},
    {"name": "joint_capacity", "index": ["A"], "expression": "sum( x[i, j, k] for k in K ) <= joint_cap[i, j]"},
    {"name": "commodity_capacity", "index": ["A", "K"], "expression": "x[i, j, k] <= commodity_cap[i, j, k]"}
  ]
}
```

### Common Pitfalls
- Attempting to use loop variable names like `i` directly inside Pyomo constraint rule functions, causing `NameError`. Access the fixed model indices instead.
- Defining the arc set manually for large networks, which is error-prone. Use a generator expression.
- Forgetting to apply both joint and commodity-specific capacity constraints, which can lead to an incomplete model.

## Solving stage

### Strategy Overview
This solving stage focuses on using Pyomo's `SolverFactory` with configurable, open-source solvers. It emphasizes systematic solution verification and structured output for automation.

### Step 1 - Select and Configure Solver
- Instantiate a solver via `pyo.SolverFactory("solver_name")` (e.g., "highs" for LP, "cbc" for MIP).
- Set key options: `time_limit`, `mip_rel_gap` (for MIP), and `threads` for parallel processing.

### Step 2 - Solve with Status Checks
- Execute `solver.solve(model, tee=False)` (use `tee=True` for debugging).
- Immediately check both the solver status (`pyo.SolverStatus.ok`) and termination condition (`pyo.TerminationCondition.optimal`) before accessing solution values.

### Step 3 - Verify Solution Feasibility
- Programmatically recompute net flows and capacity utilization from the variable values in the solved model.
- Compare against input parameters within a small tolerance (e.g., `1e-6`) to validate constraint satisfaction.

### Step 4 - Extract and Report Solution
- Iterate through flow variables and collect only those with values exceeding a reporting threshold (e.g., `> 1e-6`).
- Print a clean `RESULT:{objective_value}` line for automated parsing. For failures, output structured error information.

### Code Usage
```python
import pyomo.environ as pyo

# 1. Build model (using abstract or concrete patterns)
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective as per modeling stage

# 2. Select and configure solver
solver = pyo.SolverFactory('highs')  # Use 'cbc' for MIP problems
solver.options['time_limit'] = 30
# For MIP: solver.options['ratio'] = 0.0

# 3. Solve and check status
results = solver.solve(model, tee=False)
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    # 4. Process solution
    model.solutions.load_from(results)
    total_cost = pyo.value(model.obj)
    # ... verification and extraction logic
    print(f"RESULT:{total_cost}")
else:
    # Handle failure
    print(f"ERROR:Solver failed with status {results.solver.termination_condition}")
```

### Common Pitfalls
- Accessing variable values without checking solver status, leading to errors on infeasible or unbounded models.
- Using a loose optimality gap (`ratio`) for MIPs when an exact solution is required.
- Omitting solution verification, which can miss subtle numerical issues or solver errors.

# Workflow 2 (ORTools with GLOP/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT (for MIP) or Linear Solver (GLOP for LP) APIs, which follow an imperative, builder-style pattern. It is efficient for directly encoding problems with explicit loops and is ideal for integration into larger applications.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance (`solver = pywraplp.Solver.CreateSolver('GLOP')` or `'CBC'`).
- Prepare data structures (e.g., dictionaries) to map problem indices to solver variable objects.

### Step 2 - Create Flow Variables Systematically
- Use nested loops over arcs and commodities to create variables `x[(i, j, p)]`.
- Set variable bounds: lower bound `0.0`, upper bound `commodity_capacity[i, j, p]`.

### Step 3 - Add Constraints via Explicit Summation
- For flow conservation, create constraints by iterating over nodes and commodities, using `solver.Sum()` to aggregate inflows and outflows.
- For joint capacity, iterate over arcs and sum all commodity flows for that arc in a single constraint.

### Step 4 - Define Linear Objective
- Since costs are often uniform, set the objective coefficient to the same value for all variables within the variable creation loop.
- Call `solver.Minimize()` or `solver.Maximize()`.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of all nodes."},
    {"name": "K", "description": "Set of all commodities."},
    {"name": "A", "description": "Set of directed arcs (i, j) where i != j."}
  ],
  "parameters": [
    {"name": "net_flow", "index": ["N", "K"], "description": "Net supply (>0) or demand (<0) of commodity k at node i."},
    {"name": "joint_cap", "index": ["A"], "description": "Total capacity for all commodities on arc (i, j)."},
    {"name": "commodity_cap", "index": ["A", "K"], "description": "Capacity specific to commodity k on arc (i, j)."},
    {"name": "unit_cost", "description": "Cost per unit of flow on any arc for any commodity."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["A", "K"], "domain": "[0, commodity_cap]", "description": "Flow of commodity k on arc (i, j)."}
  ],
  "objective": {
    "sense": "min",
    "expression": "unit_cost * sum( x[i, j, k] for (i, j) in A for k in K )"
  },
  "constraints": [
    {"name": "flow_conservation", "index": ["N", "K"], "expression": "sum( x[j, i, k] for j in N if (j, i) in A ) - sum( x[i, j, k] for j in N if (i, j) in A ) == net_flow[i, k]"},
    {"name": "joint_capacity", "index": ["A"], "expression": "sum( x[i, j, k] for k in K ) <= joint_cap[i, j]"}
  ]
}
```

### Common Pitfalls
- Forgetting to add the non-negativity lower bound when creating variables; OR-Tools defaults can vary.
- Incorrectly constructing the summation for flow conservation, leading to missing terms.
- Applying commodity-specific capacity as a variable upper bound but neglecting to also add it as an explicit constraint for clarity and potential dual value retrieval.

## Solving stage

### Strategy Overview
This solving stage leverages OR-Tools' efficient C++ backend. It focuses on a tight solve-execute-verify cycle with integrated lower-bound calculations for solution validation.

### Step 1 - Execute Solve Command
- Call `solver.Solve()` or `solver.Solve(time_limit)`.
- The solver object internally manages the solution state.

### Step 2 - Check Result Status
- Evaluate `solver.ResultStatus()` against enums like `OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`.
- Do not proceed to value extraction unless the status indicates a successful solve.

### Step 3 - Validate with Theoretical Bounds
- For uniform cost networks, compute a simple lower bound: `(sum(abs(net_flow)) * unit_cost) / 2`.
- Compare the solver's objective value to this bound as a sanity check for optimality.

### Step 4 - Extract and Filter Solution
- Iterate through the dictionary of created variables and retrieve their `.solution_value()`.
- Apply a threshold (e.g., `> 1e-6`) to filter and report only non-zero flows.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')  # Use 'CBC' for MIP
# 2. Build model imperatively
x = {}
for i in N:
    for j in N:
        if i != j:
            for p in K:
                # Create variable with bounds
                x[(i, j, p)] = solver.NumVar(0.0, commodity_cap[(i, j, p)], f'x_{i}_{j}_{p}')
# ... add constraints and objective as per modeling stage

# 3. Solve and check status
status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL:
    # 4. Process solution
    total_cost = solver.Objective().Value()
    # ... verification and extraction logic
    print(f"RESULT:{total_cost}")
else:
    print(f"ERROR:Solver status: {status}")
```

### Common Pitfalls
- Assuming `solver.Solve()` returns a solution object; it returns a status code, and values are attached to the variable objects.
- Not using a tolerance when comparing floating-point solution values to expected bounds or constraints.
- Overlooking the need to recalculate derived quantities (like total flow) from the solution for verification, trusting the solver's reported objective alone.
