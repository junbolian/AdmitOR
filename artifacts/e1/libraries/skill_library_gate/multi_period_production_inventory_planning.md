---
name: Multi-Period Production-Inventory Planning
description: |
  Model and solve multi-period production-inventory problems with resource capacity, sales limits, and inventory targets to maximize profit, using structured variable separation and solver-agnostic workflows.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define a clear, index-based model, separating data from structure. It is designed for linear problems and integrates with open-source solvers like HiGHS and CBC.

### Step 1 - Define Core Variable Types
- Define three separate, non-negative decision variables for each product `p` and period `t`: `production[p,t]`, `inventory[p,t]`, and `sales[p,t]`.
- Set explicit upper bounds on variables where possible (e.g., `inventory[p,t].bounds = (0, max_inventory)`).

### Step 2 - Enforce Inventory Balance
- For the initial period (`t=0`), add the constraint: `production[p,0] == sales[p,0] + inventory[p,0]`.
- For subsequent periods (`t>0`), add the constraint: `inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t]`.

### Step 3 - Incorporate Resource and Business Constraints
- Add machine capacity constraints: `sum(usage[p,m] * production[p,t] for p in products) <= capacity[m,t]` for each machine `m` and period `t`.
- Add sales limit constraints: `sales[p,t] <= sales_limit[p,t]`.
- Add a terminal inventory target constraint: `inventory[p, final_period] == target_inventory`.

### Step 4 - Formulate the Objective
- Define the objective to maximize total profit: `sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t] for p in products for t in periods)`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "machines"],
  "parameters": [
    "profit_per_unit[product]",
    "holding_cost",
    "sales_limit[product, period]",
    "machine_usage[product, machine]",
    "capacity[machine, period]",
    "max_inventory",
    "target_inventory[product]"
  ],
  "decision_variables": [
    "production[product, period] >= 0",
    "inventory[product, period] >= 0",
    "sales[product, period] >= 0"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t])"
  },
  "constraints": [
    "inventory_balance_initial: production[p,0] == sales[p,0] + inventory[p,0]",
    "inventory_balance: inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t] for t>0",
    "machine_capacity: sum(usage[p,m] * production[p,t]) <= capacity[m,t]",
    "sales_limit: sales[p,t] <= sales_limit[p,t]",
    "inventory_limit: inventory[p,t] <= max_inventory",
    "target_inventory: inventory[p, final_period] == target_inventory[p]"
  ]
}
```

### Common Pitfalls
- Forgetting to handle the initial inventory balance period separately, leading to index errors.
- Using tuples as dictionary keys for solution extraction without converting them to JSON-serializable strings.
- Not setting explicit bounds on variables, which can lead to a less efficient presolve.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver factory (HiGHS or CBC), with robust status checking, solution verification, and structured output.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set solver options: `solver.options['time_limit'] = time_limit`, `solver.options['threads'] = num_threads`.
- Execute the solve: `results = solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Check if the solver status is `SolverStatus.ok`.
- Check if the termination condition is `TerminationCondition.optimal` or `TerminationCondition.feasible`. Proceed only if these conditions are met.

### Step 3 - Extract and Verify Solution
- Extract variable values into a structured dictionary (e.g., `sol['production'][(p,t)] = pyo.value(model.production[p,t])`).
- Implement a verification loop that checks all constraints with a numerical tolerance (e.g., `1e-6`) to confirm feasibility.

### Step 4 - Format and Output Results
- Print the objective value in a standard format: `print(f"RESULT:{pyo.value(model.objective)})`.
- Output key plan components (production, sales, inventory) by product and period for analysis.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (using model defined in Modeling stage)
model = pyo.ConcreteModel()
# ... (model construction based on Formulation Template)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 300
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    # Extract solution
    solution_dict = {}
    for p in model.products:
        for t in model.periods:
            solution_dict[f'production_{p}_{t}'] = pyo.value(model.production[p,t])
            # ... extract other variables
    print(f"RESULT:{pyo.value(model.objective)}")
    # Optional: Verify constraints with tolerance
else:
    print({'status': 'failed',
           'reason': 'infeasible_or_error',
           'solver_status': str(results.solver.status),
           'termination_condition': str(results.solver.termination_condition)})
```

### Common Pitfalls
- Failing to check both solver status and termination condition, leading to incorrect interpretation of infeasible or error states.
- Not using a tolerance when verifying constraints, causing false failures due to floating-point precision.
- Omitting error handling for JSON serialization when solution dictionary keys are non-serializable objects like tuples.

# Workflow 2 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver API for a more procedural, variable-by-variable modeling style. It is well-suited for rapid prototyping and leverages efficient C++ backends like GLOP (LP) or CBC (MIP).

### Step 1 - Instantiate Solver and Create Variables
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')` or `'CBC'`.
- Create three arrays of decision variables using `solver.NumVar(lb, ub, name)` for `production[p,t]`, `inventory[p,t]`, and `sales[p,t]`. Set upper bounds from parameters (e.g., `sales_limit[p,t]`) directly in the variable creation.

### Step 2 - Build Inventory Balance Constraints
- For `t=0`: Add constraint `production[p,0] == sales[p,0] + inventory[p,0]`.
- For `t>0`: Add constraint `inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t]`.

### Step 3 - Add Capacity and Limit Constraints
- For each machine and period, create a constraint: `sum(usage[p,m] * production[p,t] for p in products) <= capacity[m,t]`.
- Add sales limit constraints (often already enforced via variable bounds).
- Add inventory limit constraints: `inventory[p,t] <= max_inventory`.
- Add target inventory constraint: `inventory[p, final_period] == target_inventory`.

### Step 4 - Define the Objective Function
- Initialize the objective: `objective = solver.Objective()`.
- Set coefficients for `sales[p,t]` as `profit_per_unit[p]` and for `inventory[p,t]` as `-holding_cost`.
- Set the objective sense to maximization: `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "machines"],
  "parameters": [
    "profit_per_unit[product]",
    "holding_cost",
    "sales_limit[product, period]",
    "machine_usage[product, machine]",
    "capacity[machine, period]",
    "max_inventory",
    "target_inventory[product]"
  ],
  "decision_variables": [
    "production[product, period] in [0, INF]",
    "inventory[product, period] in [0, max_inventory]",
    "sales[product, period] in [0, sales_limit[product, period]]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t])"
  },
  "constraints": [
    "inventory_balance_initial: production[p,0] - sales[p,0] - inventory[p,0] == 0",
    "inventory_balance: inventory[p,t-1] + production[p,t] - sales[p,t] - inventory[p,t] == 0",
    "machine_capacity: sum(usage[p,m] * production[p,t]) <= capacity[m,t]",
    "target_inventory: inventory[p, final_period] == target_inventory[p]"
  ]
}
```

### Common Pitfalls
- Manually building constraint sums with loops instead of using Python's `sum()` function, reducing readability.
- Not setting a time limit for the solver, which can cause hangs on large or complex instances.
- Defining the objective by setting coefficients in nested loops but forgetting to include all terms (e.g., missing holding costs).

## Solving stage

### Strategy Overview
Solve the OR-Tools model, set solver parameters, analyze results for binding constraints, and output a comprehensive production plan.

### Step 1 - Configure Solver and Solve
- Set a time limit: `solver.SetTimeLimit(limit_in_milliseconds)`.
- Call `solver.Solve()` to execute the optimization.

### Step 2 - Analyze Solver Result
- Check the solve status: `if solver.ResultStatus() == pywraplp.Solver.OPTIMAL` or `FEASIBLE`.
- If optimal/feasible, retrieve the objective value: `objective_value = solver.Objective().Value()`.

### Step 3 - Extract Solution and Perform Post-Optimal Analysis
- Extract variable values into structured arrays or dictionaries.
- Optionally, analyze binding constraints (e.g., machine utilization at 100%) to identify bottlenecks and validate the solution's logic.

### Step 4 - Output and Verify with Alternative Solvers
- Print a comprehensive solution summary, including quantities by product/period and resource utilization percentages.
- For verification, run the same model with a different solver backend (e.g., GLOP vs. CBC) to confirm solution stability.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('CBC')
# Create variables, e.g., production[p,t] = solver.NumVar(0, solver.infinity(), f'prod_{p}_{t}')
# ... (variable and constraint construction based on Formulation Template)

# Solve with status / termination checks
solver.SetTimeLimit(300000)  # 300 seconds in milliseconds
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    print(f"RESULT:{solver.Objective().Value()}")
    # Extract solution
    for p in products:
        for t in periods:
            prod_val = production[p,t].solution_value()
            # ... extract other variables
    # Optional: Analyze binding constraints
    # for c in range(solver.NumConstraints()):
    #     if c.dual_value() != 0:  # For LP
    #         print(f"Constraint {c.name()} is binding")
else:
    print(f"Solver did not find an optimal or feasible solution. Status: {status}")
```

### Common Pitfalls
- Assuming the solver status `OPTIMAL` is the only successful outcome, ignoring `FEASIBLE` statuses that may still provide a usable plan.
- Not using the solver's time limit function, risking indefinite runtime on difficult instances.
- Forgetting to convert time units (seconds vs. milliseconds) when setting the solver time limit.
