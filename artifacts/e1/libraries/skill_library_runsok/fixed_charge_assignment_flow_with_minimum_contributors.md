---
name: Fixed-Charge Assignment Flow with Minimum Contributors
description: |
  Model and solve assignment-flow problems with minimum contributors per task, conditional minimum flows, and linear costs using MILP formulations and modern solvers.

---
# Workflow 1 (Pyomo with HiGHS/Gurobi)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling to define a mixed-integer linear program (MILP) with binary assignment and continuous flow variables, suitable for solvers like HiGHS (open-source) or Gurobi (commercial). It emphasizes a clean separation of model logic from data and solver configuration.

### Step 1 - Define Sets and Parameters
- Declare abstract sets for `producers` and `contracts`.
- Define parameters: `capacity[producers]`, `demand[contracts]`, `min_producers[contracts]`, `min_delivery[producers]`, and a complete `unit_cost[producers, contracts]` matrix.
- If cost data is incomplete, generate a deterministic, reproducible cost matrix (e.g., `base_cost + (producer_index % 3) - (contract_index % 2)`) to ensure a solvable instance.

### Step 2 - Create Decision Variables
- Define continuous, non-negative flow variables `x[producer, contract]`.
- Define binary assignment variables `y[producer, contract]` to indicate if a producer is active for a contract.

### Step 3 - Formulate Constraints
- **Capacity**: `sum(x[producer, contract] for contract in contracts) <= capacity[producer]` for each producer.
- **Demand Satisfaction**: `sum(x[producer, contract] for producer in producers) >= demand[contract]` for each contract.
- **Minimum Contributors**: `sum(y[producer, contract] for producer in producers) >= min_producers[contract]` for each contract.
- **Minimum Flow if Active**: `x[producer, contract] >= min_delivery[producer] * y[producer, contract]` for each producer-contract pair.
- **Upper Bound Linking**: `x[producer, contract] <= capacity[producer] * y[producer, contract]` for each pair (using capacity as a natural Big-M).

### Step 4 - Define Objective
- Minimize total linear cost: `sum(unit_cost[producer, contract] * x[producer, contract] for producer in producers for contract in contracts)`.

### Formulation Template
```json
{
  "sets": ["producers", "contracts"],
  "parameters": [
    "capacity[producers]",
    "demand[contracts]",
    "min_producers[contracts]",
    "min_delivery[producers]",
    "unit_cost[producers, contracts]"
  ],
  "decision_variables": [
    "x[producers, contracts] >= 0 (continuous)",
    "y[producers, contracts] in {0,1} (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(unit_cost[p,c] * x[p,c] for p in producers for c in contracts)"
  },
  "constraints": [
    "capacity[p]: sum(x[p,c] for c in contracts) <= capacity[p] for each p",
    "demand[c]: sum(x[p,c] for p in producers) >= demand[c] for each c",
    "min_contributors[c]: sum(y[p,c] for p in producers) >= min_producers[c] for each c",
    "min_flow_if_active[p,c]: x[p,c] >= min_delivery[p] * y[p,c] for each p,c",
    "upper_bound_link[p,c]: x[p,c] <= capacity[p] * y[p,c] for each p,c"
  ]
}
```

### Common Pitfalls
- Using an overly large Big-M value for the upper bound linking constraint, which weakens the LP relaxation; use the natural bound `capacity[p]`.
- Forgetting to generate a complete cost matrix, leading to undefined parameters and solver errors.
- Not checking for trivial infeasibility (e.g., total minimum delivery from required contributors exceeds contract demand).

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver (HiGHS or Gurobi), perform rigorous solution status checks, and validate the feasibility of the returned solution against all constraints.

### Step 1 - Instantiate Model and Solver
- Create a Pyomo `ConcreteModel` populated with the defined sets, parameters, variables, and constraints.
- Instantiate a solver object: `SolverFactory('highs')` or `SolverFactory('gurobi')`.
- Set solver options: `'mip_rel_gap': 0.0` for optimality, `'time_limit': time_limit_seconds`. Avoid setting thread options if they conflict with the environment.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model, tee=True)` to solve and optionally print logs.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `TerminationCondition.feasible`). Proceed only if both indicate success.

### Step 3 - Extract and Validate Solution
- Extract the objective value and variable values (`model.x[p,c].value`, `model.y[p,c].value`).
- Programmatically verify all constraints (capacity, demand, minimum contributors, minimum flow if active) hold within a small tolerance. This catches potential modeling or solver issues.

### Step 4 - Analyze and Report
- Compute producer utilization: `total_flow[p] / capacity[p]`.
- For each contract, list the assigned producers and their flows.
- Identify unused producers (0% utilization) to assess network redundancy.

### Code Usage
```python
import pyomo.environ as pyo

# 1. Build model (using the formulation template)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective

# 2. Solve with HiGHS
solver = pyo.SolverFactory('highs')
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)

# 3. Check status and termination
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    print(f"Objective: {pyo.value(model.obj)}")
    # 4. Extract and validate solution
    # ... retrieve variable values and perform constraint checks
else:
    print("Solve failed or was interrupted.")
```

### Common Pitfalls
- Assuming a solver return status of `ok` means an optimal solution was found; always check the termination condition.
- Not validating the solution, which can mask subtle infeasibilities due to numerical tolerances.
- Setting solver thread options in managed environments (e.g., notebooks) which can cause conflicts.

# Workflow 2 (OR-Tools with SCIP/CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to construct a MILP model imperatively. It is well-suited for deployment where a lightweight, self-contained solver (SCIP) or a high-performance CP-SAT solver is preferred.

### Step 1 - Initialize Solver and Data Structures
- Create solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')` or `'SAT'` for CP-SAT.
- Load or generate parameter arrays for capacity, demand, minimum contributors, minimum delivery, and a complete cost matrix.

### Step 2 - Create Variables
- Create continuous flow variables `x[i][j] = solver.NumVar(0, capacity[i], f'x_{i}_{j}')`.
- Create binary assignment variables `y[i][j] = solver.IntVar(0, 1, f'y_{i}_{j}')`.

### Step 3 - Add Constraints Imperatively
- **Capacity**: For each producer `i`, `solver.Add(sum(x[i][j] for j in contracts) <= capacity[i])`.
- **Demand**: For each contract `j`, `solver.Add(sum(x[i][j] for i in producers) >= demand[j])`.
- **Minimum Contributors**: For each contract `j`, `solver.Add(sum(y[i][j] for i in producers) >= min_producers[j])`.
- **Minimum Flow if Active**: For each pair `(i,j)`, `solver.Add(x[i][j] >= min_delivery[i] * y[i][j])`.
- **Upper Bound Linking**: For each pair `(i,j)`, `solver.Add(x[i][j] <= capacity[i] * y[i][j])`.

### Step 4 - Set Objective
- Create objective expression: `objective = sum(cost[i][j] * x[i][j] for i,j in pairs)`.
- Call `solver.Minimize(objective)`.

### Formulation Template
```json
{
  "sets": ["producers", "contracts"],
  "parameters": [
    "capacity[producers]",
    "demand[contracts]",
    "min_producers[contracts]",
    "min_delivery[producers]",
    "unit_cost[producers, contracts]"
  ],
  "decision_variables": [
    "x[producers, contracts] in [0, capacity[producer]] (continuous)",
    "y[producers, contracts] in {0,1} (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(unit_cost[i][j] * x[i][j])"
  },
  "constraints": [
    "capacity[i]: sum(x[i][:]) <= capacity[i]",
    "demand[j]: sum(x[:][j]) >= demand[j]",
    "min_contributors[j]: sum(y[:][j]) >= min_producers[j]",
    "min_flow_if_active[i,j]: x[i][j] >= min_delivery[i] * y[i][j]",
    "upper_bound_link[i,j]: x[i][j] <= capacity[i] * y[i][j]"
  ]
}
```

### Common Pitfalls
- Using `solver.IntVar` for binary variables instead of `solver.BoolVar` when using CP-SAT backend (CP-SAT requires BoolVar).
- Not setting a time limit or optimality gap, which can lead to excessively long runs on large instances.
- Manually constructing large summation loops inefficiently; use list comprehensions for clarity and performance.

## Solving stage

### Strategy Overview
Configure the OR-Tools solver with performance settings (time limit, threads), execute the solve, and extract the solution with robust status checking. This approach is efficient for prototyping and integration into larger applications.

### Step 1 - Configure Solver
- Set a time limit: `solver.SetTimeLimit(time_limit_milliseconds)`.
- Set number of threads: `solver.SetNumThreads(num_threads)` (avoid if using CP-SAT, which manages its own).
- For SCIP, set optimality gap if needed: `solver.SetRelativeGap(relative_gap)`.

### Step 2 - Solve and Interpret Result
- Call `status = solver.Solve()`.
- Map the returned status to `OPTIMAL`, `FEASIBLE`, or `INFEASIBLE` using the solver's constants (`pywraplp.Solver.OPTIMAL`).

### Step 3 - Extract Solution if Feasible
- If status is `OPTIMAL` or `FEASIBLE`, retrieve the objective value (`solver.Objective().Value()`).
- Iterate over variables to get `x[i][j].solution_value()` and `y[i][j].solution_value()`.

### Step 4 - Post-Solve Validation and Analysis
- Programmatically verify all constraints using the extracted values.
- Compute key metrics: producer utilization, contract coverage, and total cost.
- Report assignments in a structured format (e.g., per contract list of active producers and flows).

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(60000)  # 60 seconds
solver.SetNumThreads(4)

# 2. Build model (using the formulation template)
# ... create variables, add constraints, set objective

# 3. Solve and check status
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    print(f"Objective: {solver.Objective().Value()}")
    # 4. Extract solution
    for i in producers:
        for j in contracts:
            flow_val = x[i][j].solution_value()
            assign_val = y[i][j].solution_value()
            # ... store or analyze
    # 5. Validate constraints
    # ... perform checks
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Confusing `solver.FEASIBLE` (a feasible solution found) with `solver.OPTIMAL` (optimal solution proven). Both are acceptable for practical use.
- Not handling the case where a variable's `solution_value()` is called before a solution exists, which may raise an error.
- Forgetting to scale the time limit correctly (OR-Tools uses milliseconds).
