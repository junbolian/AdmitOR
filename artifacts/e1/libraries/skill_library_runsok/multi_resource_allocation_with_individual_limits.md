---
name: Multi-Resource Allocation with Individual Limits
description: |
  Model and solve integer linear programs for allocating items across shared resources with per-item demand caps, maximizing linear revenue.

---

# Workflow 1 (OR-Tools MIP)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using the OR-Tools linear solver wrapper. This approach is suitable for direct, low-level model construction with explicit coefficient setting, ideal for scenarios where the constraint matrix is built programmatically from incidence mappings.

### Step 1 - Define Integer Variables
- Declare integer decision variables for each item, bounded below by zero and above by its individual demand limit.
- Use `solver.IntVar(lb, ub, name)` to create variables, ensuring the domain is integer.

### Step 2 - Map Resource Consumption
- Use a binary mapping (e.g., list of lists or dictionary) to indicate which items consume which shared resource.
- This sparse representation efficiently defines the coefficients for capacity constraints.

### Step 3 - Formulate Capacity Constraints
- For each shared resource, create a linear inequality constraint.
- Sum the allocation of all items that consume the resource, using the binary mapping to set coefficients, and enforce that the sum does not exceed the resource's capacity.

### Step 4 - Define Linear Objective
- Set the objective to maximize total revenue, defined as the sum of each item's allocation multiplied by its unit revenue.
- Use `objective.SetMaximization()` and set coefficients for each variable.

### Formulation Template
```json
{
  "sets": [
    "items",
    "resources"
  ],
  "parameters": [
    {"name": "revenue", "index": "items", "type": "float"},
    {"name": "demand_limit", "index": "items", "type": "int"},
    {"name": "capacity", "index": "resources", "type": "float"},
    {"name": "consumes", "index": ["resources", "items"], "type": "binary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "integer", "lb": 0, "ub": "demand_limit"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "capacity_limit", "index": "resources", "expression": "sum(consumes[r][i] * x[i] for i in items) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Forgetting to set the integer property of variables, resulting in a continuous Linear Program.
- Inefficiently iterating over all item-resource pairs when the consumption matrix is sparse, slowing down model building.
- Setting variable upper bounds as parameters without ensuring they are integers, which can cause solver errors.

## Solving stage

### Strategy Overview
Solve the built MIP model using the SCIP or CBC backend via OR-Tools. Configure solver parameters for performance and reliability, then rigorously check the solution status and validate results.

### Step 1 - Configure Solver and Parameters
- Instantiate the solver (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set a time limit (`solver.SetTimeLimit(ms)`) and number of threads (`solver.SetNumThreads(n)`) for performance control.

### Step 2 - Solve and Check Status
- Execute `solver.Solve()`.
- Check the result status: `OPTIMAL` confirms proven optimality; `FEASIBLE` indicates a valid integer solution was found within limits.

### Step 3 - Extract and Validate Solution
- Retrieve variable values using `x[i].solution_value()`.
- Validate the solution by recomputing resource usage and verifying it does not exceed capacities and that individual allocations respect demand limits.

### Step 4 - Analyze Binding Constraints
- Identify resources where usage equals capacity (binding constraints) to understand what limits the objective.
- For items with zero allocation, assess if they are excluded due to low effective revenue per constrained resource.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)  # 30 seconds
solver.SetNumThreads(4)

# Create variables
x = [solver.IntVar(0, demand_limit[i], f"x_{i}") for i in range(n_items)]

# Add capacity constraints
for r in range(n_resources):
    constraint = solver.Constraint(0, capacity[r])
    for i in range(n_items):
        if consumes[r][i]:
            constraint.SetCoefficient(x[i], 1)

# Set objective
objective = solver.Objective()
for i in range(n_items):
    objective.SetCoefficient(x[i], revenue[i])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    obj_val = objective.Value()
    solution = [x[i].solution_value() for i in range(n_items)]
    # Validation loop (example for one resource)
    for r in range(n_resources):
        usage = sum(solution[i] for i in range(n_items) if consumes[r][i])
        print(f"Resource {r}: usage={usage}, capacity={capacity[r]}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Interpreting `FEASIBLE` status as optimal; it only guarantees a valid integer solution, not the best one.
- Not converting solution values to integers, which may lead to floating-point comparisons in validation.
- Overlooking the need to check solver status before accessing solution values, which can cause runtime errors.

# Workflow 2 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling environment, emphasizing clear separation of sets, parameters, and constraints. This approach is well-suited for maintainable, declarative formulations and leverages the high-performance HiGHS solver for MILP.

### Step 1 - Define Model and Index Sets
- Create a Pyomo `ConcreteModel`.
- Define `Set` objects for items and resources to structure the model components.

### Step 2 - Declare Parameters
- Declare `Param` objects for revenue, demand limits, and resource capacities, indexed by their respective sets.
- Define a parameter or rule for the binary mapping of item consumption per resource.

### Step 3 - Create Integer Decision Variables
- Declare a `Var` with `domain=pyo.NonNegativeIntegers` for each item.
- Optionally, set variable upper bounds directly via a constraint (`model.x[p] <= demand[p]`) for clarity in the constraint list.

### Step 4 - Formulate Constraints via Rules
- Define a constraint rule for each resource that sums the allocation of consuming items, using the binary mapping, and enforces the capacity limit.
- Define demand limit constraints for each item if not using variable bounds.

### Step 5 - Define the Objective Function
- Define the objective as the sum of revenue times allocation, to be maximized.

### Formulation Template
```json
{
  "sets": [
    "items",
    "resources"
  ],
  "parameters": [
    {"name": "revenue", "index": "items", "type": "float"},
    {"name": "demand", "index": "items", "type": "int"},
    {"name": "capacity", "index": "resources", "type": "float"},
    {"name": "consumes", "index": ["resources", "items"], "type": "binary"}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "type": "integer", "lb": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "demand_limit", "index": "items", "expression": "x[i] <= demand[i]"},
    {"name": "resource_capacity", "index": "resources", "expression": "sum(consumes[r,i] * x[i] for i in items) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Using abstract models without properly initializing all parameters before instantiation, leading to errors.
- Defining constraint rules that inefficiently iterate over large, sparse mappings without filtering.
- Confusing Pyomo's `NonNegativeIntegers` domain (which includes zero) with `PositiveIntegers` (which starts at 1).

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via `SolverFactory`. Configure it for proof of optimality, handle solver statuses gracefully, and implement post-solution validation and sensitivity analysis.

### Step 1 - Configure HiGHS Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")`.
- Set key options: `mip_rel_gap=0.0` (or `-1.0` in HiGHS) to seek proven optimality, `time_limit` to control runtime, and `threads` for parallel processing.

### Step 2 - Solve and Inspect Termination
- Execute `results = solver.solve(model, tee=False)`.
- Check both `solver.status` (e.g., `SolverStatus.ok`) and `results.solver.termination_condition` (e.g., `TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract and Round Solution
- Retrieve variable values using `pyo.value(model.x[i])`.
- Convert to integers using `int(round(...))` to handle numerical tolerances, especially for validation.

### Step 4 - Post-Solution Validation and Analysis
- Recompute resource usage and demand limit adherence to verify the solution.
- Identify binding capacity constraints.
- For zero-valued items with positive revenue, perform a simple sensitivity test by forcing the item into the solution and observing the objective degradation.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=range(n_items))
model.resources = pyo.Set(initialize=range(n_resources))

model.revenue = pyo.Param(model.items, initialize=revenue_dict)
model.demand = pyo.Param(model.items, initialize=demand_dict)
model.capacity = pyo.Param(model.resources, initialize=capacity_dict)
# Assume consumes_dict is a dict of (r,i): 0/1
model.consumes = pyo.Param(model.resources, model.items, initialize=consumes_dict, default=0)

model.x = pyo.Var(model.items, domain=pyo.NonNegativeIntegers)

def demand_rule(model, i):
    return model.x[i] <= model.demand[i]
model.demand_con = pyo.Constraint(model.items, rule=demand_rule)

def capacity_rule(model, r):
    return sum(model.consumes[r, i] * model.x[i] for i in model.items) <= model.capacity[r]
model.capacity_con = pyo.Constraint(model.resources, rule=capacity_rule)

model.obj = pyo.Objective(expr=sum(model.revenue[i] * model.x[i] for i in model.items), sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = -1.0  # HiGHS setting for optimality
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    obj_val = float(pyo.value(model.obj))
    solution = {i: int(round(pyo.value(model.x[i]))) for i in model.items}
    # Validation
    for r in model.resources:
        usage = sum(solution[i] for i in model.items if model.consumes[r, i] == 1)
        print(f"Resource {r}: {usage}/{pyo.value(model.capacity[r])}")
else:
    print("Solver did not return a successful status.")
```

### Common Pitfalls
- Not rounding retrieved variable values before integer comparisons, leading to false validation failures due to floating-point precision.
- Misinterpreting `TerminationCondition.feasible` as a guarantee of optimality.
- Overlooking the need to check both `solver.status` and `termination_condition`; a solver might be `ok` but have hit a time limit (`maxTimeLimit`).
