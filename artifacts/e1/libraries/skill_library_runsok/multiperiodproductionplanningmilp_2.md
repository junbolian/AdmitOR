---
name: MultiPeriodProductionPlanningMILP
description: |
  Model and solve multi-period production planning with setup costs, resource capacities, and inventory balance as a mixed-integer linear program.
---

# Workflow 1 (Pyomo with CBC/Highs)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling syntax to build a structured MILP, leveraging open-source solvers like CBC or HiGHS for optimization. It emphasizes clear separation of data, model, and solving logic for maintainability.

### Step 1 - Define Sets and Parameters
- Define index sets for products (`P`) and time periods (`T`).
- Define parameters for demand (`demand[p,t]`), production cost (`prod_cost[p,t]`), setup cost (`setup_cost[p,t]`), holding cost (`hold_cost[p,t]`), resource consumption (`resource_cons[p]`), and resource capacity (`capacity[t]`).
- Calculate a product-period-specific `production_limit[p,t]` (e.g., cumulative remaining demand) to serve as a tight big-M value.

### Step 2 - Create Decision Variables
- Create continuous variable `x[p,t]` for production quantity, with lower bound 0 and upper bound `production_limit[p,t]`.
- Create continuous variable `i[p,t]` for inventory level, with lower bound 0.
- Create binary variable `y[p,t]` for setup indicator.

### Step 3 - Formulate Inventory Balance Constraints
- For the first period (`t=1`), enforce `x[p,1] = demand[p,1] + i[p,1]` (assuming zero initial inventory).
- For subsequent periods (`t>1`), enforce `i[p,t-1] + x[p,t] = demand[p,t] + i[p,t]`.

### Step 4 - Link Production to Setup Activation
- Add big-M constraint `x[p,t] <= production_limit[p,t] * y[p,t]` for each product and period.

### Step 5 - Enforce Resource Capacity Constraints
- For each period, sum resource consumption across all products: `sum(p in P, resource_cons[p] * x[p,t]) <= capacity[t]`.

### Step 6 - Define Objective Function
- Minimize total cost: `sum(p in P, t in T, prod_cost[p,t]*x[p,t] + setup_cost[p,t]*y[p,t] + hold_cost[p,t]*i[p,t])`.

### Formulation Template
```json
{
  "sets": ["P", "T"],
  "parameters": [
    "demand[P,T]",
    "prod_cost[P,T]",
    "setup_cost[P,T]",
    "hold_cost[P,T]",
    "resource_cons[P]",
    "capacity[T]",
    "production_limit[P,T]"
  ],
  "decision_variables": [
    "x[P,T] (continuous, >=0)",
    "i[P,T] (continuous, >=0)",
    "y[P,T] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(p in P, t in T, prod_cost[p,t]*x[p,t] + setup_cost[p,t]*y[p,t] + hold_cost[p,t]*i[p,t])"
  },
  "constraints": [
    "inventory_balance_first: x[p,1] = demand[p,1] + i[p,1] forall p in P",
    "inventory_balance: i[p,t-1] + x[p,t] = demand[p,t] + i[p,t] forall p in P, t in T, t>1",
    "setup_activation: x[p,t] <= production_limit[p,t] * y[p,t] forall p in P, t in T",
    "resource_capacity: sum(p in P, resource_cons[p] * x[p,t]) <= capacity[t] forall t in T"
  ]
}
```

### Common Pitfalls
- Using an arbitrarily large, uniform big-M value instead of a tight, product-period-specific `production_limit`, which degrades solver performance.
- Forgetting to handle the initial inventory condition in the balance constraint, leading to an infeasible or incorrect model.
- Not adding a small epsilon tolerance (e.g., 1e-6) when checking constraint satisfaction post-solve, causing false violations due to numerical precision.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or HiGHS solver with configured time limits and optimality tolerances. Implement systematic solution verification and detailed reporting.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver object: `solver = SolverFactory('cbc')` or `SolverFactory('highs')`.
- Set solver options: `solver.options['seconds'] = 60`, `solver.options['ratio'] = 0.0001`, `solver.options['threads'] = 4`.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Check termination condition: `results.solver.termination_condition` should be `optimal` or `feasible`.
- Check solver status: `results.solver.status` should be `ok`.

### Step 3 - Extract and Validate Solution
- Extract variable values using `pyo.value(model.x[p,t])`.
- Implement a verification function that recalculates inventory, checks capacity and setup activation constraints with a tolerance (e.g., 1e-6), and reports any violations.

### Step 4 - Report Results and Cost Breakdown
- Calculate and print total cost, plus separate sums for production, setup, and holding costs.
- Print a production schedule and inventory levels for non-zero values.
- Report resource utilization per period.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (using ConcreteModel)
model = pyo.ConcreteModel()
# ... define sets, params, variables, constraints, objective ...

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 60
solver.options['ratio'] = 0.0001
results = solver.solve(model, tee=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal and results.solver.status == pyo.SolverStatus.ok:
    # Extract solution
    for p in model.P:
        for t in model.T:
            x_val = pyo.value(model.x[p,t])
            # ... store values ...
    # Validate and report
    verify_solution(model, tolerance=1e-6)
    print_cost_breakdown(model)
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `termination_condition` and `solver.status`, leading to misinterpretation of suboptimal or failed solves.
- Extracting variable values without verifying the solve was successful, causing runtime errors.
- Omitting solution verification, which can miss subtle infeasibilities introduced by solver tolerances.

# Workflow 2 (OR-Tools with SCIP)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT (for linear constraints) or the SCIP wrapper to build and solve the MILP directly in Python. It is suited for rapid prototyping and deployment with a focus on performance and integrated solution checking.

### Step 1 - Initialize Model and Create Index Mappings
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Create dictionaries or lists to map product and period indices to OR-Tools variable indices.

### Step 2 - Define Variables with Bounds
- Create production variable `x[p,t] = solver.NumVar(0, production_limit[p,t], f'x_{p}_{t}')`.
- Create inventory variable `i[p,t] = solver.NumVar(0, solver.infinity(), f'i_{p}_{t}')`.
- Create setup variable `y[p,t] = solver.BoolVar(f'y_{p}_{t}')`.

### Step 3 - Add Inventory Balance Constraints
- For `t=1`: `solver.Add(x[p,1] == demand[p,1] + i[p,1])`.
- For `t>1`: `solver.Add(i[p,t-1] + x[p,t] == demand[p,t] + i[p,t])`.

### Step 4 - Add Setup Activation with Big-M
- Add constraint: `solver.Add(x[p,t] <= production_limit[p,t] * y[p,t])`.

### Step 5 - Add Resource Capacity Constraints
- For each period `t`, create a linear expression `sum_expr = sum(resource_cons[p] * x[p,t] for p in P)` and add `solver.Add(sum_expr <= capacity[t])`.

### Step 6 - Set Objective Function
- Build objective expression: `obj_expr = sum(prod_cost[p,t]*x[p,t] + setup_cost[p,t]*y[p,t] + hold_cost[p,t]*i[p,t] for p in P, t in T)`.
- Set minimization: `solver.Minimize(obj_expr)`.

### Formulation Template
```json
{
  "sets": ["P", "T"],
  "parameters": [
    "demand[P,T]",
    "prod_cost[P,T]",
    "setup_cost[P,T]",
    "hold_cost[P,T]",
    "resource_cons[P]",
    "capacity[T]",
    "production_limit[P,T]"
  ],
  "decision_variables": [
    "x[P,T] (continuous, 0..production_limit)",
    "i[P,T] (continuous, >=0)",
    "y[P,T] (boolean)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(p in P, t in T, prod_cost[p,t]*x[p,t] + setup_cost[p,t]*y[p,t] + hold_cost[p,t]*i[p,t])"
  },
  "constraints": [
    "inventory_balance_first: x[p,1] = demand[p,1] + i[p,1] forall p in P",
    "inventory_balance: i[p,t-1] + x[p,t] = demand[p,t] + i[p,t] forall p in P, t in T, t>1",
    "setup_activation: x[p,t] <= production_limit[p,t] * y[p,t] forall p in P, t in T",
    "resource_capacity: sum(p in P, resource_cons[p] * x[p,t]) <= capacity[t] forall t in T"
  ]
}
```

### Common Pitfalls
- Using `solver.infinity()` as the big-M value, which creates a numerically weak formulation.
- Forgetting to set appropriate upper bounds on production variables, leaving them unbounded and potentially causing solver issues.
- Incorrectly ordering indices when creating variables or constraints, leading to mismatched data.

## Solving stage

### Strategy Overview
Solve using OR-Tools' SCIP solver with configurable time and gap limits. Leverage OR-Tools' solution value extraction and implement post-solve validation.

### Step 1 - Configure Solver Parameters
- Set time limit: `solver.SetTimeLimit(60000)` (milliseconds).
- Set number of threads: `solver.SetNumThreads(4)`.
- Optionally set relative MIP gap: Configure via solver-specific parameters if supported.

### Step 2 - Solve and Interpret Result Status
- Call `status = solver.Solve()`.
- Check status: `status == pywraplp.Solver.OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` appropriately.

### Step 3 - Extract Solution and Compute Metrics
- If solution exists, extract variable values using `.solution_value()`.
- Compute inventory levels from extracted production values to verify balance.
- Calculate resource utilization and cost breakdown.

### Step 4 - Validate Constraints Programmatically
- Loop through all constraints, evaluate the left-hand side with solution values, and compare to right-hand side with a tolerance (e.g., 1e-6).
- Specifically check that `x[p,t] > 0` implies `y[p,t] == 1` within tolerance.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... create variables, add constraints, set objective ...

# Solve with status / termination checks
solver.SetTimeLimit(60000)
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    # Extract solution values
    for p in P:
        for t in T:
            x_val = x[p,t].solution_value()
            # ... store values ...
    # Validate
    verify_ortools_solution(solver, variables_dict, tolerance=1e-6)
    print(f"Total cost: {total_cost}")
else:
    print(f"No optimal/feasible solution found. Status: {status}")
```

### Common Pitfalls
- Not handling the `FEASIBLE` status, which indicates a suboptimal but valid solution.
- Assuming variable objects are directly accessible after solve; must use `.solution_value()`.
- Neglecting to verify that setup binaries are correctly activated for non-zero production, a common source of logical errors.
