---
name: Multi-Sourcing Fixed-Charge Network Flow
description: |
  Model and solve supply-demand allocation with minimum activation flows, multi-sourcing requirements, and linear costs using MILP formulations.
---

# Workflow 1 (OR-Tools MILP)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using the OR-Tools CP-SAT or MPSolver API. This approach is suitable for direct, high-performance solving with open-source backends (CBC, SCIP) and provides a clear, imperative modeling style.

### Step 1 - Define Sets and Parameters
- Define the set of supply nodes (e.g., `suppliers`) and demand nodes (e.g., `contracts`).
- Define parameters: `cost[s][d]`, `capacity[s]`, `demand[d]`, `min_flow[s]`, and the multi-sourcing requirement `K`.

### Step 2 - Create Decision Variables
- Create a continuous flow variable `x[s][d]` for the quantity allocated from supplier `s` to demand `d`.
- Create a binary activation variable `y[s][d]` to indicate if the allocation is active.

### Step 3 - Formulate Objective and Constraints
- **Objective**: Minimize total linear cost: `min sum(cost[s][d] * x[s][d])`.
- **Capacity Constraint**: Total outflow from a supplier cannot exceed its capacity: `sum(x[s][d] for d in contracts) <= capacity[s]`.
- **Demand Requirement**: Total inflow to a demand must meet its requirement: `sum(x[s][d] for s in suppliers) >= demand[d]`.
- **Minimum Activation Flow**: If active, flow must meet a minimum: `x[s][d] >= min_flow[s] * y[s][d]`.
- **Big-M Linking**: Flow must be zero if inactive: `x[s][d] <= capacity[s] * y[s][d]`.
- **Multi-Sourcing Requirement**: Each demand must be served by at least `K` suppliers: `sum(y[s][d] for s in suppliers) >= K`.

### Formulation Template
```json
{
  "sets": ["suppliers", "contracts"],
  "parameters": {
    "cost": "2D array cost[supplier][contract]",
    "capacity": "list capacity[supplier]",
    "demand": "list demand[contract]",
    "min_flow": "list min_flow[supplier]",
    "K": "integer minimum number of suppliers per contract"
  },
  "decision_variables": [
    "x[s][d] continuous, >=0",
    "y[s][d] binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s][d] * x[s][d] for s in suppliers for d in contracts)"
  },
  "constraints": [
    "sum(x[s][d] for d in contracts) <= capacity[s] for each s",
    "sum(x[s][d] for s in suppliers) >= demand[d] for each d",
    "x[s][d] >= min_flow[s] * y[s][d] for each s, d",
    "x[s][d] <= capacity[s] * y[s][d] for each s, d",
    "sum(y[s][d] for s in suppliers) >= K for each d"
  ]
}
```

### Common Pitfalls
- Using an overly large Big-M value (e.g., a global maximum) instead of the natural `capacity[s]`, which weakens the LP relaxation.
- Forgetting to add the Big-M linking constraint (`x <= M*y`), leaving the model unbounded when `y=0`.
- Not verifying that `K` is less than or equal to the number of suppliers, which can cause infeasibility.

## Solving stage

### Strategy Overview
Solve the MILP using the OR-Tools `pywraplp` MPSolver interface with the CBC backend. Focus on robust solver configuration, status checking, and structured solution extraction.

### Step 1 - Initialize Solver and Create Variables
- Create a solver instance (e.g., `solver = pywraplp.Solver.CreateSolver('CBC')`).
- Create `x` and `y` variables using loops over suppliers and contracts.

### Step 2 - Add Constraints and Objective
- Add all constraints using `solver.Add()` and `solver.Sum()` within nested loops.
- Build the objective function by setting coefficients for each `x` variable.

### Step 3 - Configure and Solve
- Set solver parameters: `solver.SetTimeLimit(60000)` for a time limit (in milliseconds), `solver.SetNumThreads(4)` for parallelism.
- Call `solver.Solve()` and capture the result status.

### Step 4 - Check Status and Extract Solution
- Check if `status` is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error messages.
- Extract variable values using `.solution_value()` and compute key metrics (e.g., supplier utilization, demand coverage).
- Print the objective value in a parseable format (e.g., `RESULT:{value}`).

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('CBC')
# ... create variables, constraints, objective as per modeling stage ...

# Solve with status / termination checks
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    print(f"RESULT:{solver.Objective().Value()}")
    # Extract and analyze solution
    for s in suppliers:
        for d in contracts:
            flow = x[s, d].solution_value()
            if flow > 1e-6:
                print(f"Supplier {s} -> Contract {d}: {flow}")
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not setting a time limit for large instances, leading to unpredictable runtimes.
- Misinterpreting the solver status (e.g., treating `FEASIBLE` as `OPTIMAL` without noting the potential optimality gap).
- Failing to verify that the extracted solution satisfies all constraints within a small tolerance.

# Workflow 2 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model paradigm, separating problem definition from solver specifics. This approach emphasizes declarative modeling, ease of maintenance, and solver portability, targeting the HiGHS solver for open-source MIP solving.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for `model.S` (suppliers) and `model.D` (contracts).
- Define `Param` objects for `cost`, `capacity`, `demand`, `min_flow`, and `K` using dictionaries or indexed rules.

### Step 2 - Define Variables and Objective
- Define `model.x` as a continuous, non-negative `Var` indexed over `(S, D)`.
- Define `model.y` as a binary `Var` indexed over `(S, D)`.
- Define the objective `model.obj` as a `sum(cost[s,d] * model.x[s,d])` to minimize.

### Step 3 - Declare Constraints
- **Capacity**: `model.capacity_constr = Constraint(model.S, rule=lambda m, s: sum(m.x[s,d] for d in m.D) <= capacity[s])`.
- **Demand**: `model.demand_constr = Constraint(model.D, rule=lambda m, d: sum(m.x[s,d] for s in m.S) >= demand[d])`.
- **Minimum Activation**: `model.min_flow_constr = Constraint(model.S, model.D, rule=lambda m, s, d: m.x[s,d] >= min_flow[s] * m.y[s,d])`.
- **Big-M Linking**: `model.bigM_constr = Constraint(model.S, model.D, rule=lambda m, s, d: m.x[s,d] <= capacity[s] * m.y[s,d])`.
- **Multi-Sourcing**: `model.multi_source_constr = Constraint(model.D, rule=lambda m, d: sum(m.y[s,d] for s in m.S) >= K)`.

### Formulation Template
```json
{
  "sets": ["S (suppliers)", "D (contracts)"],
  "parameters": {
    "cost": "Param(S, D)",
    "capacity": "Param(S)",
    "demand": "Param(D)",
    "min_flow": "Param(S)",
    "K": "scalar"
  },
  "decision_variables": [
    "x[S, D] in NonNegativeReals",
    "y[S, D] in Binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s,d] * x[s,d] for s in S for d in D)"
  },
  "constraints": [
    "sum(x[s,d] for d in D) <= capacity[s] for each s in S",
    "sum(x[s,d] for s in S) >= demand[d] for each d in D",
    "x[s,d] >= min_flow[s] * y[s,d] for each (s,d)",
    "x[s,d] <= capacity[s] * y[s,d] for each (s,d)",
    "sum(y[s,d] for s in S) >= K for each d in D"
  ]
}
```

### Common Pitfalls
- Incorrectly defining Pyomo `Param` rules, leading to uninitialized parameters.
- Using Python's built-in `sum` inside Pyomo constraint rules instead of the Pyomo `summation` function or a generator expression (the latter is acceptable in rule definitions).
- Not initializing the model with concrete data before solving, resulting in an abstract model that cannot be instantiated.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with concrete data, configure the HiGHS solver with performance settings, solve, and perform rigorous checks on the solver status and termination condition before processing results.

### Step 1 - Instantiate Model and Set Solver
- Create a `ConcreteModel` and populate its sets and parameters with data.
- Create a solver object: `solver = SolverFactory('highs')`.

### Step 2 - Configure Solver Options
- Set key options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`, `solver.options['mip_rel_gap'] = 1e-4`.
- Avoid setting invalid options like negative time limits or gaps.

### Step 3 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Import and check `SolverStatus` and `TerminationCondition` from `pyomo.opt`.
- Proceed only if `status is SolverStatus.ok` and `termination_condition` is `optimal` or `feasible`.

### Step 4 - Extract and Validate Solution
- Retrieve the objective value via `pyo.value(model.obj)`.
- Iterate over variables to extract flows and activation states.
- Optionally, programmatically verify that the solution satisfies all constraints within tolerance.
- Output the objective value in a parseable format (e.g., `RESULT:{value}`).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# Build model from formulation (concrete example)
model = pyo.ConcreteModel()
model.S = pyo.Set(initialize=suppliers)
model.D = pyo.Set(initialize=contracts)
# ... define parameters, variables, objective, constraints as per modeling stage ...

# Solve with status / termination checks
solver = SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

status = results.solver.status
termination = results.solver.termination_condition

if status == SolverStatus.ok and termination in (TerminationCondition.optimal, TerminationCondition.feasible):
    print(f"RESULT:{pyo.value(model.obj)}")
    # Access solution: model.x[s,d].value, model.y[s,d].value
else:
    print(f"Solver failed. Status: {status}, Termination: {termination}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, which can mask solver failures.
- Attempting to access variable values (`var.value`) before verifying a successful solve, leading to `None` errors.
- Using the `highs` solver without it being installed or available in the Pyomo solver path.
