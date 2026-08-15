---
name: Supply Allocation with Activation Constraints
description: |
  A skill for modeling and solving allocation problems with minimum delivery thresholds, supplier activation logic, and multiple-supplier requirements using MILP formulations.
---

# Workflow 1 (MILP with Big-M Activation)

## Modeling stage

### Strategy Overview
This workflow models the allocation problem as a Mixed-Integer Linear Program (MILP) using a Big-M formulation to link continuous allocation variables with binary activation variables. It is a standard approach suitable for most MILP solvers.

### Step 1 - Define Variables and Sets
- Define sets for `producers` and `contracts`.
- Create a continuous variable `x[i][j]` for the allocation amount from producer `i` to contract `j`.
- Create a binary variable `y[i][j]` to indicate if producer `i` is actively supplying contract `j`.

### Step 2 - Implement Activation Logic
- Enforce that allocation is zero if inactive: `x[i][j] <= capacity[i] * y[i][j]`. Use producer capacity as the Big-M constant.
- Enforce minimum delivery if active: `x[i][j] >= min_delivery[i] * y[i][j]`.

### Step 3 - Add Core Supply-Demand Constraints
- Add producer capacity constraint: `sum(x[i][j] for j in contracts) <= capacity[i]` for each `i`.
- Add contract demand constraint: `sum(x[i][j] for i in producers) >= demand[j]` for each `j`.

### Step 4 - Enforce Multiple Supplier Requirement
- For each contract `j`, require a minimum number of active suppliers: `sum(y[i][j] for i in producers) >= min_suppliers`.

### Formulation Template
```json
{
  "sets": [
    "producers",
    "contracts"
  ],
  "parameters": [
    "capacity[producers]",
    "demand[contracts]",
    "min_delivery[producers]",
    "cost[producers][contracts]",
    "min_suppliers"
  ],
  "decision_variables": [
    "x[producers][contracts] >= 0",
    "y[producers][contracts] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in producers for j in contracts)"
  },
  "constraints": [
    "capacity_constraint[i]: sum(x[i][j] for j in contracts) <= capacity[i]",
    "demand_constraint[j]: sum(x[i][j] for i in producers) >= demand[j]",
    "activation_upper[i][j]: x[i][j] <= capacity[i] * y[i][j]",
    "activation_lower[i][j]: x[i][j] >= min_delivery[i] * y[i][j]",
    "supplier_count[j]: sum(y[i][j] for i in producers) >= min_suppliers"
  ]
}
```

### Common Pitfalls
- Using an overly large Big-M value (like a global maximum) can weaken the LP relaxation and slow down solving. Use the tightest valid bound (e.g., `capacity[i]`).
- Forgetting to enforce `x[i][j] >= 0`; the Big-M constraint `x[i][j] <= M*y[i][j]` alone does not prevent negative values.
- Not verifying that `min_delivery[i] <= capacity[i]` for all producers, which could make the minimum delivery constraint trivially infeasible.

## Solving stage

### Strategy Overview
Solve the MILP model using a dedicated solver like SCIP or CBC via an algebraic modeling interface (e.g., OR-Tools). Focus on proper solver configuration, solution status checking, and post-solution validation.

### Step 1 - Solver Setup and Configuration
- Instantiate the solver (e.g., `Solver.CreateSolver("SCIP")`).
- Set a time limit (`SetTimeLimit`) and the number of threads (`SetNumThreads`) for performance.
- Optionally set a relative optimality gap tolerance if early termination is acceptable.

### Step 2 - Build Model and Solve
- Create variables and add constraints according to the formulation, using loops over sets.
- Define the objective function and invoke the solver.
- Store the solve status and termination condition.

### Step 3 - Validate Solution and Handle Results
- Check if the status is `OPTIMAL` or `FEASIBLE`. If not, proceed to infeasibility analysis.
- For a feasible solution, retrieve variable values and compute derived metrics (total cost, capacity utilization).
- Programmatically verify all constraints using a tolerance (e.g., 1e-6) to catch numerical issues.

### Code Usage
```python
# Example using OR-Tools
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# Create variables
x = {}
y = {}
for i in producers:
    for j in contracts:
        x[i, j] = solver.NumVar(0, solver.infinity(), f"x_{i}_{j}")
        y[i, j] = solver.IntVar(0, 1, f"y_{i}_{j}")

# Add constraints (refer to Formulation Template)
# ... constraint addition loops here ...

# Set objective
objective = solver.Objective()
for i in producers:
    for j in contracts:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# Solve with status / termination checks
result_status = solver.Solve()
if result_status == pywraplp.Solver.OPTIMAL or result_status == pywraplp.Solver.FEASIBLE:
    print(f"Objective value = {solver.Objective().Value()}")
    # Retrieve and process solution
    for i in producers:
        for j in contracts:
            if x[i, j].solution_value() > 1e-6:
                print(f"Allocation {i}->{j}: {x[i, j].solution_value()}")
else:
    print("No optimal or feasible solution found.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses; a feasible but non-optimal solution may still be useful.
- Comparing floating-point solution values directly without tolerance, leading to false constraint violations.
- Omitting post-solution validation, which can hide modeling errors or solver precision issues.

# Workflow 2 (Pyomo-based Formulation with Direct Activation)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for a declarative model definition, emphasizing clean separation of activation logic and constraints. It leverages Pyomo's expressive syntax and integrates seamlessly with commercial and open-source solvers.

### Step 1 - Declare Model Components
- Define Pyomo `Set` objects for `model.producers` and `model.contracts`.
- Declare `Param` objects for all input data (`capacity`, `demand`, `min_delivery`, `cost`, `min_suppliers`).

### Step 2 - Define Decision Variables
- Define `model.x` as a continuous, non-negative `Var` indexed over producers and contracts.
- Define `model.y` as a binary `Var` indexed over the same sets.

### Step 3 - Build Constraints with Pyomo Rules
- Create a rule for the producer capacity constraint, summing `model.x[i,j]` over `j`.
- Create a rule for the contract demand constraint, summing `model.x[i,j]` over `i`.
- Implement activation constraints directly: `model.x[i,j] >= model.min_delivery[i] * model.y[i,j]` and `model.x[i,j] <= model.capacity[i] * model.y[i,j]`.
- Create a rule for the multiple supplier requirement: `sum(model.y[i,j] for i) >= model.min_suppliers`.

### Step 4 - Define the Objective
- Define the objective as a `summation` of `model.cost[i,j] * model.x[i,j]` to be minimized.

### Formulation Template
```json
{
  "sets": [
    "producers",
    "contracts"
  ],
  "parameters": [
    "capacity[producers]",
    "demand[contracts]",
    "min_delivery[producers]",
    "cost[producers][contracts]",
    "min_suppliers"
  ],
  "decision_variables": [
    "x[producers][contracts] >= 0",
    "y[producers][contracts] ∈ {0,1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in producers for j in contracts)"
  },
  "constraints": [
    "supply_capacity[i]: sum(x[i][j] for j in contracts) <= capacity[i]",
    "demand_satisfaction[j]: sum(x[i][j] for i in producers) >= demand[j]",
    "min_if_active[i][j]: x[i][j] >= min_delivery[i] * y[i][j]",
    "max_if_active[i][j]: x[i][j] <= capacity[i] * y[i][j]",
    "multi_supplier[j]: sum(y[i][j] for i in producers) >= min_suppliers"
  ]
}
```

### Common Pitfalls
- Using Python loops inside Pyomo constraint rules for summation instead of Pyomo's built-in `summation()` or generator expressions, which can be inefficient for large models.
- Defining parameters as plain Python dictionaries instead of Pyomo `Param` objects, which limits portability and solver compatibility.
- Neglecting to deactivate the `max_if_active` constraint if `capacity[i]` is very large, as it becomes a loose Big-M constraint.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory, focusing on robust solver option management, detailed solution inspection, and automated feasibility verification.

### Step 1 - Configure Solver and Options
- Use `SolverFactory` to instantiate the solver (e.g., `"gurobi"`, `"highs"`, `"cbc"`).
- Set solver-specific options like time limit, MIP gap tolerance, and random seed for reproducibility.

### Step 2 - Solve and Capture Results
- Call `solver.solve(model, tee=True)` to solve and optionally show solver output.
- Capture the solver status and termination condition from the results object.

### Step 3 - Extract and Verify Solution
- Load solution into the model using `model.solutions.load_from(results)`.
- Iterate through constraints to verify satisfaction numerically with a tolerance.
- Extract non-zero allocations and active assignments for reporting.

### Code Usage
```python
# Example using Pyomo
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
model.producers = pyo.Set(initialize=producers)
model.contracts = pyo.Set(initialize=contracts)

# Define parameters (data dictionaries assumed to exist)
model.capacity = pyo.Param(model.producers, initialize=capacity_data)
model.demand = pyo.Param(model.contracts, initialize=demand_data)
model.min_delivery = pyo.Param(model.producers, initialize=min_delivery_data)
model.cost = pyo.Param(model.producers, model.contracts, initialize=cost_data)
model.min_suppliers = pyo.Param(initialize=min_suppliers_value)

# Define variables
model.x = pyo.Var(model.producers, model.contracts, domain=pyo.NonNegativeReals)
model.y = pyo.Var(model.producers, model.contracts, domain=pyo.Binary)

# Define constraints via rules
def supply_capacity_rule(model, i):
    return sum(model.x[i, j] for j in model.contracts) <= model.capacity[i]
model.supply_capacity = pyo.Constraint(model.producers, rule=supply_capacity_rule)

# ... additional constraint rules defined similarly ...

# Define objective
def total_cost_rule(model):
    return sum(model.cost[i, j] * model.x[i, j] for i in model.producers for j in model.contracts)
model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")
results = solver.solve(model, tee=False)

status = results.solver.status
termination = results.solver.termination_condition

if status == pyo.SolverStatus.ok and termination in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    print(f"Objective value: {pyo.value(model.total_cost)}")
    # Process solution
    for i in model.producers:
        for j in model.contracts:
            if pyo.value(model.x[i, j]) > 1e-6:
                print(f"Active allocation: {i}->{j} = {pyo.value(model.x[i, j])}")
else:
    print(f"Solver failed. Status: {status}, Termination: {termination}")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (problem solved optimally); both must be checked.
- Not using `pyo.value()` to extract numeric values from Pyomo components, leading to type errors.
- Assuming the solver loads the solution back into the model automatically; some solvers require explicit `model.solutions.load_from()`.
