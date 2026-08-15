---
name: Integer Assignment with Capacity-Weighted Demand
description: |
  Model and solve integer resource assignment problems with capacity-weighted demand satisfaction and linear costs using either direct solver APIs or algebraic modeling frameworks.

---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
Model the problem directly using a solver's native API (e.g., OR-Tools, HiGHS C-API). This approach builds the model via coefficient loops, offering fine-grained control and avoiding abstraction overhead, suitable for performance-focused or embedded applications.

### Step 1 - Define Data Structures
- Extract and store all problem data in indexed structures (e.g., lists of lists, dictionaries) before model construction.
- Validate all parameters (availability, demand, capacity, cost) for non-negativity and logical consistency.

### Step 2 - Create Integer Decision Variables
- Instantiate one integer variable `x[i][j]` for each supply type `i` and demand location `j`.
- Set variable bounds: lower bound `0`, upper bound `availability[i]` to aid solver pruning.

### Step 3 - Formulate Supply Constraints
- For each supply type `i`, create a linear constraint: `sum_j x[i][j] <= availability[i]`.
- Use a coefficient of `1` for each variable in its respective supply constraint.

### Step 4 - Formulate Demand Constraints
- For each demand location `j`, create a linear constraint: `sum_i capacity[i][j] * x[i][j] >= demand[j]`.
- Use the `capacity` matrix as coefficients within the constraint, not as variable bounds.

### Step 5 - Define Linear Cost Objective
- Define the objective as `minimize sum_i sum_j cost[i][j] * x[i][j]`.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "I: set of supply types",
    "J: set of demand locations"
  ],
  "parameters": [
    "availability[i ∈ I]: integer supply limit",
    "demand[j ∈ J]: integer demand requirement",
    "capacity[i ∈ I, j ∈ J]: per-unit contribution to demand j",
    "cost[i ∈ I, j ∈ J]: per-unit assignment cost"
  ],
  "decision_variables": [
    "x[i ∈ I, j ∈ J]: integer units of i assigned to j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "supply_limit[i in I]: sum_{j in J} x[i,j] <= availability[i]",
    "demand_satisfaction[j in J]: sum_{i in I} capacity[i,j] * x[i,j] >= demand[j]"
  ]
}
```

### Common Pitfalls
- Using incomplete or placeholder data (e.g., `-1`, `0`) for missing capacities/costs, leading to infeasibility.
- Confusing capacity coefficients with variable bounds, incorrectly modeling the demand constraint.
- Forgetting to set integer variable bounds, causing the solver to treat them as continuous.

## Solving stage

### Strategy Overview
Solve the constructed model using a Mixed-Integer Programming (MIP) solver backend (e.g., SCIP, CBC). Configure solver pragmatically, solve, and rigorously verify the solution's feasibility and correctness.

### Step 1 - Initialize Solver and Configure
- Instantiate a MIP solver via its API wrapper (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set practical limits: time limit (e.g., `SetTimeLimit(30000)`), optional thread count.

### Step 2 - Build Model and Solve
- Use nested loops to add variables, constraints, and objective coefficients to the solver object.
- Call the solver's `Solve()` method and capture the returned status.

### Step 3 - Check Solver Status and Extract Solution
- Check if status indicates optimality or feasibility (e.g., `OPTIMAL`, `FEASIBLE`).
- If successful, extract the objective value and all variable values using `solution_value()`.
- If failed, output a structured error with the solver status code.

### Step 4 - Post-Solve Validation
- Programmatically recompute total assignments per supply type and verify against `availability`.
- Recompute capacity-weighted contributions per demand location and verify against `demand`.
- Print a verification summary to confirm solution correctness.

### Code Usage
```python
# Example using OR-Tools (pywraplp)
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(TIME_LIMIT_MS)

# 2. Create variables
x = {}
for i in I:
    for j in J:
        x[i, j] = solver.IntVar(0, availability[i], f"x_{i}_{j}")

# 3. Add supply constraints
for i in I:
    ct = solver.Constraint(0, availability[i])
    for j in J:
        ct.SetCoefficient(x[i, j], 1)

# 4. Add demand constraints
for j in J:
    ct = solver.Constraint(demand[j], solver.infinity())
    for i in I:
        ct.SetCoefficient(x[i, j], capacity[i][j])

# 5. Set objective
objective = solver.Objective()
for i in I:
    for j in J:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# 6. Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f"RESULT:{objective.Value()}")
    # Extract and validate solution...
else:
    print(f"SOLVER_FAILURE:{status}")
```

### Common Pitfalls
- Reading `solution_value()` without checking solver status first, risking runtime errors.
- Omitting post-solve validation, potentially accepting an infeasible solution due to solver tolerances.
- Using excessive solver parameter tuning prematurely; defaults often suffice.

# Workflow 2 (Algebraic Modeling with Pyomo)

## Modeling stage

### Strategy Overview
Model the problem using an algebraic modeling language (Pyomo). This approach separates problem formulation from solver choice, enhancing readability, reusability, and ease of modification for complex or evolving models.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for supply types (`I`) and demand locations (`J`).
- Declare Pyomo `Param` objects for `availability`, `demand`, `capacity`, and `cost`, indexed by the appropriate sets.

### Step 2 - Declare Integer Decision Variables
- Declare a Pyomo `Var` object `x` indexed over `I` and `J` with domain `pyo.NonNegativeIntegers`.
- Optionally set variable bounds via initialization rules or constraints.

### Step 3 - Formulate Constraints via Rules
- Define a `Constraint` for supply limits using a rule: for each `i` in `I`, `sum(x[i,j] for j in J) <= availability[i]`.
- Define a `Constraint` for demand satisfaction using a rule: for each `j` in `J`, `sum(capacity[i,j] * x[i,j] for i in I) >= demand[j]`.

### Step 4 - Define Objective Function
- Define an `Objective` with sense `minimize` and expression `sum(cost[i,j] * x[i,j] for i in I for j in J)`.

### Step 5 - Instantiate Model with Concrete Data
- Create a `ConcreteModel` and populate all `Param` objects with validated, complete data dictionaries.

### Formulation Template
```json
{
  "sets": [
    "I: set of supply types",
    "J: set of demand locations"
  ],
  "parameters": [
    "availability[i ∈ I]: integer supply limit",
    "demand[j ∈ J]: integer demand requirement",
    "capacity[i ∈ I, j ∈ J]: per-unit contribution to demand j",
    "cost[i ∈ I, j ∈ J]: per-unit assignment cost"
  ],
  "decision_variables": [
    "x[i ∈ I, j ∈ J]: integer units of i assigned to j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "supply_limit[i in I]: sum_{j in J} x[i,j] <= availability[i]",
    "demand_satisfaction[j in J]: sum_{i in I} capacity[i,j] * x[i,j] >= demand[j]"
  ]
}
```

### Common Pitfalls
- Using an `AbstractModel` but failing to provide complete data during instantiation.
- Incorrectly indexing parameters or variables within constraint rules, leading to `KeyError`.
- Defining constraints with `==` instead of `>=` for demand satisfaction, making the model overly restrictive.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a compatible solver (e.g., HiGHS, CBC) via the `SolverFactory`. Leverage Pyomo's standardized interface for solver configuration, solution extraction, and status reporting.

### Step 1 - Select and Configure Solver
- Instantiate a solver object using `pyo.SolverFactory("solver_name")` (e.g., `"highs"`, `"cbc"`).
- Set solver options: `time_limit`, `mip_gap` (relative tolerance).

### Step 2 - Solve and Inspect Termination
- Call `solver.solve(model, options=...)` and capture the `results` object.
- Check `results.solver.status` is `ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Extract and Validate Solution
- If solve was successful, access the objective value via `pyo.value(model.obj)`.
- Iterate over `model.x` to extract non-zero variable values.
- Programmatically validate the solution against the original constraints for feasibility assurance.

### Step 4 - Report Structured Output
- Print the objective value and a summary of assignments (e.g., non-zero variables).
- In case of solver failure, report the status and termination condition for debugging.

### Code Usage
```python
import pyomo.environ as pyo

# 1. Create concrete model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_SET)
model.J = pyo.Set(initialize=J_SET)

# 2. Define parameters (data provided via initialize dict)
model.availability = pyo.Param(model.I, initialize=AVAIL_DICT)
model.demand = pyo.Param(model.J, initialize=DEMAND_DICT)
model.capacity = pyo.Param(model.I, model.J, initialize=CAPACITY_DICT)
model.cost = pyo.Param(model.I, model.J, initialize=COST_DICT)

# 3. Define variables
model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)

# 4. Define objective
model.obj = pyo.Objective(
    expr=pyo.sum(model.cost[i,j] * model.x[i,j] for i in model.I for j in model.J),
    sense=pyo.minimize
)

# 5. Define constraints
def supply_rule(m, i):
    return sum(m.x[i, j] for j in m.J) <= m.availability[i]
model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

def demand_rule(m, j):
    return sum(m.capacity[i, j] * m.x[i, j] for i in m.I) >= m.demand[j]
model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

# 6. Solve
solver = pyo.SolverFactory("highs")
results = solver.solve(model, options={"time_limit": TIME_LIMIT})

# 7. Check status and extract
if results.solver.status == pyo.SolverStatus.ok and \
   results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                            pyo.TerminationCondition.feasible):
    print(f"RESULT:{pyo.value(model.obj)}")
    # Extract and validate solution...
else:
    print(f"SOLVER_FAILURE:{results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming a solve was successful based only on the absence of exceptions; always check solver status.
- Accessing variable values before the solver has populated the model object, resulting in `None`.
- Not setting a `time_limit` or `mip_gap`, allowing the solver to run indefinitely or return suboptimal solutions.
