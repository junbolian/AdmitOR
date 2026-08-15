---
name: Cutting Stock with Pattern Usage Limits
description: |
  Model and solve cutting stock problems with pattern usage limits as integer linear programs, minimizing total rolls while satisfying demand and respecting pattern usage bounds.
---

# Workflow 1 (MILP with OR-Tools/SCIP)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using a direct, low-level API. Decision variables represent the integer count of each pattern used, bounded by pattern usage limits. The objective minimizes the sum of these variables, subject to demand satisfaction constraints.

### Step 1 - Define Data Structures
- Organize pattern yield data as a 2D list `pattern_yield[p][w]`, where each entry is the number of items of width `w` produced by one use of pattern `p`.
- Store demand as a list `demand[w]` and pattern usage limits as a list `usage_limit[p]`.

### Step 2 - Create Decision Variables
- Define non-negative integer variables `x[p]` for each pattern `p`.
- Set the upper bound of each variable directly to its corresponding `usage_limit[p]` during creation.

### Step 3 - Formulate Demand Constraints
- For each width `w`, create a linear constraint: `sum(pattern_yield[p][w] * x[p] for all p) >= demand[w]`.
- This ensures total production of each width meets or exceeds its demand.

### Step 4 - Define Objective Function
- Set the objective to minimize the total number of rolls used: `minimize sum(x[p] for all p)`.

### Formulation Template
```json
{
  "sets": [
    "P: set of cutting patterns",
    "W: set of product widths"
  ],
  "parameters": [
    "yield_pw[p][w]: integer yield of width w from pattern p",
    "demand_w[w]: integer demand for width w",
    "limit_p[p]: integer maximum usage for pattern p"
  ],
  "decision_variables": [
    "x_p[p]: non-negative integer, usage count of pattern p"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{p in P} x_p[p]"
  },
  "constraints": [
    "DemandSat_w[w]: sum_{p in P} yield_pw[p][w] * x_p[p] >= demand_w[w], for all w in W",
    "UsageLimit_p[p]: x_p[p] <= limit_p[p], for all p in P"
  ]
}
```

### Common Pitfalls
- Forgetting to convert placeholder values (e.g., -1 for "no yield") to 0 in the `pattern_yield` matrix, which can cause incorrect constraints.
- Not setting variable bounds during creation, leading to an unbounded problem or requiring separate limit constraints.

## Solving stage

### Strategy Overview
Use the OR-Tools wrapper for the SCIP solver, a high-performance MILP solver. Configure for performance, solve, and rigorously verify the solution's feasibility and optimality.

### Step 1 - Initialize Solver and Variables
- Create a SCIP solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Add integer variables with explicit lower (0) and upper (`usage_limit[p]`) bounds.

### Step 2 - Build Constraints and Objective
- Iterate over widths to create demand constraints, adding terms `pattern_yield[p][w] * x[p]` for each pattern.
- Set the objective coefficients to 1 for all `x[p]` variables.

### Step 3 - Configure and Execute Solve
- Set a time limit (`solver.SetTimeLimit`) and number of threads (`solver.SetNumThreads`) for performance.
- Call `solver.Solve()` and capture the result status.

### Step 4 - Verify and Validate Solution
- Check if a feasible solution was found (`solver.OPTIMAL` or `solver.FEASIBLE`).
- Post-solve, compute production per width and confirm it satisfies demand.
- Verify that all pattern usage variables respect their limits.

### Step 5 - Prove Optimality (Optional)
- To confirm the solution value `k` is optimal, add a new constraint `sum(x[p]) <= k-1` and re-solve. Infeasibility proves `k` is minimal.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# Create variables with bounds
x = {}
for p in range(num_patterns):
    x[p] = solver.IntVar(0, usage_limit[p], f'x_{p}')

# Demand constraints
for w in range(num_widths):
    constraint = solver.Constraint(demand[w], solver.infinity())
    for p in range(num_patterns):
        constraint.SetCoefficient(x[p], pattern_yield[p][w])

# Objective
objective = solver.Objective()
for p in range(num_patterns):
    objective.SetCoefficient(x[p], 1)
objective.SetMinimization()

# solve with status / termination checks
result_status = solver.Solve()
if result_status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_rolls = sum(x[p].solution_value() for p in range(num_patterns))
    # Validate constraints...
else:
    # Handle no solution found...
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good feasible solutions when the time limit is hit.
- Misinterpreting variable bounds as constraints, which can affect solver presolve performance.

# Workflow 2 (Structured Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Use Pyomo's structured, declarative modeling to create a clean, maintainable model. Define abstract sets and parameters, then use rules to generate constraints. This approach separates model logic from data, enhancing reusability.

### Step 1 - Define Abstract Model Components
- Declare `model.P` and `model.W` as `Set` components for patterns and widths.
- Define `model.yield_pw`, `model.demand_w`, and `model.limit_p` as `Param` components indexed over these sets.

### Step 2 - Declare Decision Variables
- Create a `Var` component `model.x` indexed over `model.P`, with domain `NonNegativeIntegers`.
- This inherently defines non-negative integer variables.

### Step 3 - Construct Constraints via Rules
- Define a `Constraint` rule for demand satisfaction: for each `w` in `model.W`, `sum(model.yield_pw[p, w] * model.x[p] for p in model.P) >= model.demand_w[w]`.
- Define a `Constraint` rule for pattern usage limits: for each `p` in `model.P`, `model.x[p] <= model.limit_p[p]`.

### Step 4 - Formulate the Objective
- Define an `Objective` rule: `sum(model.x[p] for p in model.P)` with sense `minimize`.

### Formulation Template
```json
{
  "sets": [
    "P: set of cutting patterns",
    "W: set of product widths"
  ],
  "parameters": [
    "yield_pw[p, w]: integer yield of width w from pattern p",
    "demand_w[w]: integer demand for width w",
    "limit_p[p]: integer maximum usage for pattern p"
  ],
  "decision_variables": [
    "x[p]: non-negative integer, usage count of pattern p"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{p in P} x[p]"
  },
  "constraints": [
    "DemandSat[w]: sum_{p in P} yield_pw[p, w] * x[p] >= demand_w[w], for all w in W",
    "UsageLimit[p]: x[p] <= limit_p[p], for all p in P"
  ]
}
```

### Common Pitfalls
- Using mutable default arguments (like lists) inside Pyomo rule functions, which can lead to incorrect model behavior.
- Not initializing all parameters before instantiating the concrete model, causing `KeyError` or uninitialized values.

## Solving stage

### Strategy Overview
Instantiate a concrete Pyomo model with data, then solve using a high-performance open-source MILP solver (HiGHS or CBC) via the `SolverFactory`. Focus on solver configuration, solution status checking, and post-solution validation.

### Step 1 - Instantiate Model and Select Solver
- Create a `ConcreteModel` and assign data to its `Param` components.
- Select a solver: `solver = SolverFactory('highs')` or `SolverFactory('cbc')`.

### Step 2 - Configure Solver Parameters
- Set key parameters: `time_limit=30` (seconds), `mip_rel_gap=0.0` (for optimality), and `threads=4` (for parallelism).

### Step 3 - Solve and Check Status
- Execute `results = solver.solve(model, tee=False)`.
- Verify `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 4 - Extract and Validate Solution
- Extract variable values using `pyo.value(model.x[p])` for all `p`.
- Compute total rolls and validate all constraints programmatically to ensure the solution is correct.

### Step 5 - Perform Lower Bound Analysis
- Solve the LP relaxation of the model to obtain a lower bound on the objective, useful for assessing optimality gap.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=range(num_patterns))
model.W = pyo.Set(initialize=range(num_widths))

def yield_rule(model, p, w):
    # Convert placeholders (e.g., -1) to 0
    val = pattern_yield_data[p][w]
    return 0 if val < 0 else val
model.yield_pw = pyo.Param(model.P, model.W, initialize=yield_rule)
model.demand_w = pyo.Param(model.W, initialize=lambda model, w: demand_data[w])
model.limit_p = pyo.Param(model.P, initialize=lambda model, p: limit_data[p])

model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

def demand_sat_rule(model, w):
    return sum(model.yield_pw[p, w] * model.x[p] for p in model.P) >= model.demand_w[w]
model.DemandSat = pyo.Constraint(model.W, rule=demand_sat_rule)

def usage_limit_rule(model, p):
    return model.x[p] <= model.limit_p[p]
model.UsageLimit = pyo.Constraint(model.P, rule=usage_limit_rule)

model.obj = pyo.Objective(expr=sum(model.x[p] for p in model.P), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1.0  # Use -1 for default, 0.0 for optimal
solver.options['threads'] = 4

results = solver.solve(model)
if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    total_rolls = sum(pyo.value(model.x[p]) for p in model.P)
    # Validate constraints...
else:
    # Handle solve failure...
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (found proven optimum); both checks are necessary.
- Not using `pyo.value()` to extract variable values from the Pyomo model object after solving.
