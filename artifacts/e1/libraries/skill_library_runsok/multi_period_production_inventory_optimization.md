---
name: Multi-Period Production-Inventory Optimization
description: |
  Model and solve multi-period production-inventory-sales problems with resource capacity, inventory balance, and profit maximization objectives, using structured linear programming formulations and systematic solver integration.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Build a structured, index-based model using Pyomo's `ConcreteModel` pattern, defining sets, parameters, variables, constraints, and objective in a modular fashion for clarity and maintainability. This approach is well-suited for complex, multi-dimensional problems and integrates seamlessly with open-source solvers.

### Step 1 - Define Core Sets and Parameters
- Define index sets for products (`p`) and time periods (`t`) using `pyo.Set`.
- Define all time-varying and product-specific parameters (e.g., `profit_per_unit[p]`, `holding_cost`, `sales_limit[p,t]`, `machine_capacity[m,t]`, `resource_usage[m,p]`) as `pyo.Param` objects, initializing them with nested dictionaries for efficient lookup.
- Use `pyo.Param(mutable=True)` for parameters that may be altered in scenario analysis.

### Step 2 - Create Decision Variables
- Create three core variable families: `production[p,t]`, `inventory[p,t]`, and `sales[p,t]` using `pyo.Var`.
- Set appropriate bounds directly in the variable definition: `bounds=(0, None)` for production and sales, `bounds=(0, inventory_capacity)` for inventory, and `bounds=(0, sales_limit[p,t])` for sales to embed limits efficiently.
- Choose `domain=pyo.NonNegativeReals` for continuous LP or `domain=pyo.NonNegativeIntegers` for MIP formulations.

### Step 3 - Implement Inventory Balance Constraints
- For the initial period (`t=0`), implement `production[p,0] == sales[p,0] + inventory[p,0]` using a constraint rule.
- For subsequent periods (`t>0`), implement `inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t]` using a separate constraint rule.
- Use `pyo.Constraint.Skip` within a single rule to handle the period logic cleanly, avoiding redundant constraints.

### Step 4 - Add Resource Capacity and Limit Constraints
- For each machine/resource type `m` and period `t`, sum resource consumption: `sum(resource_usage[m,p] * production[p,t] for p in products) <= machine_capacity[m,t]`.
- Model machine downtime by setting `machine_capacity[m,t] = 0` in the parameter, not by adding extra constraints.
- Enforce terminal inventory targets with equality constraints: `inventory[p, final_period] == target_inventory`.

### Step 5 - Formulate Profit Maximization Objective
- Define revenue as `sum(profit_per_unit[p] * sales[p,t] for p in products for t in periods)`.
- Define total holding cost as `sum(holding_cost * inventory[p,t] for p in products for t in periods)`.
- Set the objective to maximize `revenue - total_holding_cost` using `pyo.Objective(sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "machines"],
  "parameters": [
    "profit_per_unit[product]",
    "holding_cost",
    "sales_limit[product, period]",
    "inventory_capacity",
    "machine_capacity[machine, period]",
    "resource_usage[machine, product]",
    "target_inventory[product]"
  ],
  "decision_variables": [
    "production[product, period] ∈ NonNegativeReals",
    "sales[product, period] ∈ [0, sales_limit[product, period]]",
    "inventory[product, period] ∈ [0, inventory_capacity]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t])"
  },
  "constraints": [
    "initial_balance: production[p,0] = sales[p,0] + inventory[p,0]",
    "inventory_balance: inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0",
    "machine_capacity: sum(resource_usage[m,p] * production[p,t]) <= machine_capacity[m,t]",
    "terminal_inventory: inventory[p, final_period] = target_inventory[p]"
  ]
}
```

### Common Pitfalls
- Forgetting to handle the initial period separately in inventory balance, leading to an undefined `inventory[p,-1]`.
- Using loose bounds (e.g., `None`) for inventory variables, which can lead to numerical instability and unrealistic solutions.
- Defining sales limits as separate constraints instead of variable bounds, which adds unnecessary overhead to the solver.
- Not checking for zero capacity parameters, which can cause division-by-zero errors in post-solution analysis.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source solver (HiGHS or CBC) with proper configuration, status checking, and comprehensive post-solution verification. Structure the solving logic for robustness and reusability.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set solver options for performance: `solver.options["time_limit"] = 30`, `solver.options["threads"] = 4`. For MIP, set `solver.options["mip_rel_gap"] = 0.0` for exact solutions.
- Solve the model with `results = solver.solve(model, tee=False)`.

### Step 2 - Validate Solver Status and Termination
- Check if the solver process completed: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `assert results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]`.
- If status is not ok or termination is not optimal/feasible, output a structured error payload and do not proceed to solution extraction.

### Step 3 - Extract and Post-Process Solution
- Load the solution into the model: `model.solutions.load_from(results)`.
- Extract variable values using `pyo.value(model.production[p,t])`, `pyo.value(model.sales[p,t])`, `pyo.value(model.inventory[p,t])`.
- Post-process to handle numerical precision: set any variable value with `abs(value) < 1e-6` to exactly `0.0`.

### Step 4 - Perform Comprehensive Solution Verification
- Recompute inventory balances for all periods and products, checking `abs(lhs - rhs) < 1e-6`.
- Calculate machine usage per period and compare against capacity, verifying `usage <= capacity + 1e-6`.
- Check sales and inventory variable values against their upper bounds.
- Verify terminal inventory targets are met exactly.
- Print a verification summary table for debugging.

### Step 5 - Analyze Solution and Output Results
- Calculate and print total revenue, total holding cost, and net profit.
- Print production, sales, and inventory schedules in a readable table format.
- Compute resource utilization percentages (`usage / capacity * 100`) to identify bottleneck machines.
- For MIP solutions, compare the objective value with the continuous LP relaxation to understand the integrality gap.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (assumes model is a pyo.ConcreteModel built per Modeling stage)
def solve_pyomo_model(model):
    solver = pyo.SolverFactory("highs")
    solver.options["time_limit"] = 30
    solver.options["threads"] = 4

    results = solver.solve(model, tee=False)

    # Status and termination checks
    if (results.solver.status != pyo.SolverStatus.ok or
        results.solver.termination_condition not in [
            pyo.TerminationCondition.optimal,
            pyo.TerminationCondition.feasible
        ]):
        print({"status": "solver_failed",
               "reason": results.solver.termination_condition})
        return None

    # Load and post-process solution
    model.solutions.load_from(results)
    for var in model.component_objects(pyo.Var, active=True):
        for index in var:
            val = pyo.value(var[index])
            if abs(val) < 1e-6:
                var[index].value = 0.0

    # Verification and analysis logic here
    # ...
    return model
```

### Common Pitfalls
- Extracting variable values without checking solver status first, potentially reading invalid solutions.
- Not using tolerance checks (`1e-6`) when verifying constraints due to floating-point arithmetic.
- Forgetting to load the solution into the model with `model.solutions.load_from(results)` before accessing `pyo.value`.
- Setting an overly restrictive `mip_rel_gap=0.0` on large MIPs, causing the solver to run indefinitely.

# Workflow 2 (OR-Tools with GLOP/CBC)

## Modeling stage

### Strategy Overview
Construct the model directly using the OR-Tools linear solver API (`pywraplp`), creating variables and constraints imperatively. This workflow is efficient for prototyping and benefits from OR-Tools' built-in performance features and direct solver control.

### Step 1 - Initialize Solver and Define Core Data Structures
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver("GLOP")` for LP or `"CBC"` for MIP.
- Define product and period lists or ranges as Python lists.
- Store parameters in nested dictionaries (e.g., `profit[product]`, `sales_limit[product][period]`, `capacity[machine][period]`).

### Step 2 - Create Variables with Embedded Bounds
- Use nested loops over products and periods to create variables: `production[p][t] = solver.NumVar(0.0, solver.infinity(), f"prod_{p}_{t}")`.
- For sales variables, embed the sales limit as the upper bound: `sales[p][t] = solver.NumVar(0.0, sales_limit[p][t], f"sales_{p}_{t}")`.
- For inventory variables, set the upper bound to the inventory capacity: `inventory[p][t] = solver.NumVar(0.0, inventory_capacity, f"inv_{p}_{t}")`.
- Use `solver.IntVar` for integer formulations.

### Step 3 - Build Inventory Balance Constraints
- For the initial period (`t=0`), add constraints: `solver.Add(production[p][0] == sales[p][0] + inventory[p][0])`.
- For periods `t > 0`, add constraints: `solver.Add(inventory[p][t-1] + production[p][t] == sales[p][t] + inventory[p][t])`.
- Use descriptive constraint names via the `name` parameter for easier debugging.

### Step 4 - Add Machine Capacity and Terminal Constraints
- For each machine `m` and period `t`, create a linear expression: `expr = sum(resource_usage[m][p] * production[p][t] for p in products)`.
- Add the capacity constraint: `solver.Add(expr <= capacity[m][t])`.
- Add terminal inventory equality constraints: `solver.Add(inventory[p][final_period] == target_inventory[p])`.

### Step 5 - Set Profit Maximization Objective
- Initialize the objective: `objective = solver.Objective()`.
- Incrementally set coefficients: `objective.SetCoefficient(sales[p][t], profit_per_unit[p])` for revenue and `objective.SetCoefficient(inventory[p][t], -holding_cost)` for holding costs.
- Set the optimization sense: `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["products", "periods", "machines"],
  "parameters": [
    "profit_per_unit[product]",
    "holding_cost",
    "sales_limit[product][period]",
    "inventory_capacity",
    "machine_capacity[machine][period]",
    "resource_usage[machine][product]",
    "target_inventory[product]"
  ],
  "decision_variables": [
    "production[product][period] (solver.NumVar/IntVar)",
    "sales[product][period] (bounded by sales_limit)",
    "inventory[product][period] (bounded by inventory_capacity)"
  ],
  "objective": {
    "sense": "max",
    "expression": "objective.SetCoefficient for sales (+) and inventory (-)"
  },
  "constraints": [
    "initial_balance: production[p][0] == sales[p][0] + inventory[p][0]",
    "inventory_balance: inventory[p][t-1] + production[p][t] == sales[p][t] + inventory[p][t]",
    "machine_capacity: sum(resource_usage[m][p] * production[p][t]) <= capacity[m][t]",
    "terminal_inventory: inventory[p][final_period] == target_inventory[p]"
  ]
}
```

### Common Pitfalls
- Using `solver.infinity()` for inventory variable bounds, which can lead to unbounded problems and solver errors.
- Forgetting to set the objective sense (`SetMaximization`/`SetMinimization`), resulting in default minimization.
- Creating constraints inside loops without proper indexing, leading to duplicate or missing constraints.
- Not using `solver.OPTIMAL` or `solver.FEASIBLE` status checks before accessing solution values.

## Solving stage

### Strategy Overview
Solve the OR-Tools model, configure solver parameters for performance, rigorously check solution status, and implement a detailed verification routine to ensure constraint satisfaction and solution validity.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.SetTimeLimit(30000)` (milliseconds).
- Set the number of threads for parallel processing: `solver.SetNumThreads(4)`.
- For MIP, set a relative optimality gap: `solver.SetRelativeGap(0.01)` for a 1% gap, if exact solution is not required.

### Step 2 - Solve and Check Status
- Execute the solver: `status = solver.Solve()`.
- Check for optimality: `if status == pywraplp.Solver.OPTIMAL:`.
- Also accept feasible solutions: `if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:`.
- If status is not acceptable, print an error and exit the solution extraction phase.

### Step 3 - Extract Solution Values
- Access the objective value: `total_profit = objective.Value()`.
- Extract variable values using `.solution_value()`: `prod_val = production[p][t].solution_value()`.
- Store values in dictionaries or lists for further analysis.

### Step 4 - Verify All Constraints Programmatically
- Recompute inventory balances for all periods and products, checking against a tolerance (e.g., `1e-6`).
- Calculate actual machine usage per period and compare to capacity.
- Verify that sales and inventory values do not exceed their bounds.
- Confirm terminal inventory targets are met.
- Print a detailed verification report listing any violations.

### Step 5 - Output Analysis and Insights
- Print a formatted table showing production, sales, and inventory plans.
- Calculate and display total revenue, total holding cost, and net profit.
- Compute and highlight bottleneck resources (where usage == capacity).
- For integer solutions, compare the objective with the continuous relaxation to report the integrality gap.
- Perform sensitivity analysis by calculating profit per unit of constrained resource (e.g., profit per machine-hour) to explain product mix decisions.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model (assumes solver, variables, constraints, objective are defined per Modeling stage)
def solve_ortools_model(solver):
    # Configure solver
    solver.SetTimeLimit(30000)
    solver.SetNumThreads(4)

    # Solve
    status = solver.Solve()

    # Status check
    if status not in [solver.OPTIMAL, solver.FEASIBLE]:
        print(f"Solver failed with status: {status}")
        return None

    # Extract objective
    total_profit = solver.Objective().Value()

    # Extract and post-process variable values
    solution_dict = {}
    # ... extraction logic ...

    # Verification logic
    tolerance = 1e-6
    # ... check inventory balances, capacities, limits ...

    return solution_dict, total_profit
```

### Common Pitfalls
- Assuming `solver.Solve()` returns only `OPTIMAL`; always handle `FEASIBLE` status for practical problems.
- Not using a tolerance when checking equality constraints (`==`), leading to false failures due to floating-point arithmetic.
- Accessing `.solution_value()` on variables before confirming a successful solve, which may raise an error.
- Omitting verification of terminal inventory constraints, which are critical for many multi-period problems.
