---
name: Continuous Resource-Constrained Production Planning
description: |
  Model and solve linear programs for maximizing profit under resource and individual capacity constraints with continuous decision variables.

---

# Workflow 1 (OR-Tools LP with Explicit Bounds)

## Modeling stage

### Strategy Overview
Formulate the problem as a continuous linear program using a solver-native API (OR-Tools). Decision variables are defined with explicit lower and upper bounds to encode non-negativity and individual capacity limits directly, while a single linear constraint captures the shared resource limitation.

### Step 1 - Define Data Structures
- Organize problem parameters into parallel lists or arrays indexed by item.
- Store per-item profit, resource consumption per unit, and maximum production capacity.
- Define the total available resource as a scalar.

### Step 2 - Create Variables with Bounds
- Instantiate a continuous decision variable for each item.
- Set the variable's lower bound to 0 and its upper bound to the item's maximum production capacity.
- This step implicitly encodes the individual upper bound constraints.

### Step 3 - Formulate Resource Constraint
- Create a linear expression summing the resource consumption of each item multiplied by its production variable.
- Add a constraint that this sum must be less than or equal to the total resource limit.

### Step 4 - Set Linear Objective
- Create a linear expression summing the profit per unit multiplied by the production variable for each item.
- Set the solver's objective to maximize this expression.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit[i] (profit per unit of item i)",
    "resource_use[i] (resource units consumed per unit of item i)",
    "max_production[i] (maximum quantity for item i)",
    "total_resource (total available resource units)"
  ],
  "decision_variables": ["x[i] (production quantity of item i, continuous)"],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in I} profit[i] * x[i]"
  },
  "constraints": [
    "sum_{i in I} resource_use[i] * x[i] <= total_resource",
    "0 <= x[i] <= max_production[i] for all i in I"
  ]
}
```

### Common Pitfalls
- Forgetting to initialize the solver object before creating variables, leading to errors.
- Defining the resource constraint with the wrong inequality direction (>= instead of <=).
- Hard-coding parameter values within constraint definitions, reducing model flexibility.

## Solving stage

### Strategy Overview
Use the OR-Tools wrapper for the GLOP solver. Implement robust error handling for solver creation and solution status checks. After solving, verify the solution's feasibility and compute key performance metrics.

### Step 1 - Initialize Solver with Fallback
- Create a solver instance for a continuous LP backend (e.g., 'GLOP').
- Check if the solver was created successfully; exit or handle the error if `None`.

### Step 2 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the returned status. Proceed only if the status is `OPTIMAL` or `FEASIBLE`.

### Step 3 - Extract and Verify Solution
- Extract the objective value and all variable solution values.
- Recompute the total resource usage from the solution to verify the primary constraint is satisfied.
- Optionally, check that no variable exceeds its individual upper bound.

### Step 4 - Report Key Metrics
- Print the optimal total profit.
- Print the resource utilization (used/available).
- Print production quantities for items with non-zero output.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Define Data (Placeholders)
profit = [...]  # List of profit coefficients
resource_use = [...]  # List of resource consumption coefficients
max_production = [...]  # List of individual upper bounds
total_resource = ...  # Scalar resource limit
n_items = len(profit)

# 2. Initialize Solver
solver = pywraplp.Solver.CreateSolver('GLOP')
if solver is None:
    raise RuntimeError('Solver creation failed.')

# 3. Create Variables with Bounds
x = []
for i in range(n_items):
    var = solver.NumVar(0, max_production[i], f'x_{i}')
    x.append(var)

# 4. Add Resource Constraint
resource_expr = sum(resource_use[i] * x[i] for i in range(n_items))
solver.Add(resource_expr <= total_resource)

# 5. Set Objective
objective = solver.Objective()
for i in range(n_items):
    objective.SetCoefficient(x[i], profit[i])
objective.SetMaximization()

# 6. Solve and Check Status
status = solver.Solve()
if status not in [solver.OPTIMAL, solver.FEASIBLE]:
    raise RuntimeError(f'Solver failed with status: {status}')

# 7. Extract and Verify
total_profit = objective.Value()
total_resource_used = sum(resource_use[i] * x[i].solution_value() for i in range(n_items))
print(f'Optimal profit: {total_profit}')
print(f'Resource used: {total_resource_used}/{total_resource}')
# Add verification that total_resource_used <= total_resource
```

### Common Pitfalls
- Assuming the solver status `FEASIBLE` guarantees optimality; it may only indicate a feasible solution was found.
- Not handling the case where the solver object cannot be created (e.g., due to missing backend).
- Failing to verify constraint satisfaction post-solve, which can mask modeling errors.

# Workflow 2 (Pyomo with Solver Fallback)

## Modeling stage

### Strategy Overview
Build an abstract model using Pyomo, separating model construction from solver choice. Use indexed sets and parameters for clarity and maintainability. The model includes explicit constraints for both the shared resource and individual capacities.

### Step 1 - Define Abstract Sets and Parameters
- Create an indexed set for items.
- Define Pyomo `Param` objects for profit, resource consumption, maximum production, and the total resource limit.

### Step 2 - Declare Decision Variables
- Declare a continuous, non-negative variable for the production quantity of each item.

### Step 3 - Construct Explicit Constraints
- Create a single `Constraint` for the total resource limit using a summation expression.
- Create an indexed `Constraint` to enforce the individual upper bounds for each item.

### Step 4 - Formulate the Objective
- Define the objective as the maximization of the sum of profit multiplied by production variables.

### Formulation Template
```json
{
  "sets": ["I (items)"],
  "parameters": [
    "profit[i] (profit per unit of item i)",
    "resource_use[i] (resource units consumed per unit of item i)",
    "max_production[i] (maximum quantity for item i)",
    "total_resource (total available resource units)"
  ],
  "decision_variables": ["x[i] (production quantity of item i, continuous, >=0)"],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in I} profit[i] * x[i]"
  },
  "constraints": [
    "ResourceLimit: sum_{i in I} resource_use[i] * x[i] <= total_resource",
    "Capacity[i] for all i in I: x[i] <= max_production[i]"
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's `Var` domain (e.g., `NonNegativeReals`) with explicit upper bound constraints; both are needed.
- Using hard-coded indices in constraint rules instead of the passed model and index arguments.
- Incorrectly scoping parameters within constraint rule functions.

## Solving stage

### Strategy Overview
Use a solver factory to interface with multiple backends (e.g., CBC, GLPK, IPOPT). Implement a fallback mechanism to try alternative solvers if the primary fails. Perform post-solve analysis including efficiency ranking and constraint binding checks.

### Step 1 - Configure Primary Solver
- Create a solver object via `SolverFactory` with the primary solver name (e.g., 'cbc').
- Set appropriate options for continuous LPs (e.g., disable gap limit with `ratio = -1.0` for CBC).

### Step 2 - Solve with Fallback Logic
- Attempt to solve the model with the primary solver.
- If the solve fails or returns a non-optimal status, log the error and attempt with a secondary solver (e.g., 'glpk').

### Step 3 - Validate Solution and Status
- Check both the solver status and termination condition to confirm optimality or feasibility.
- Load the solution into the model instance only after confirming a successful solve.

### Step 4 - Post-Solve Analysis
- Compute the actual resource usage from the solution.
- Calculate profit-per-resource ratios for all items to explain the solution pattern.
- Identify which constraints are binding (e.g., resource limit, individual capacities).

### Code Usage
```python
import pyomo.environ as pyo

# 1. Build Model (Placeholders)
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(n_items)) # n_items defined elsewhere

model.profit = pyo.Param(model.I, initialize={i: profit[i] for i in model.I})
model.resource_use = pyo.Param(model.I, initialize={i: resource_use[i] for i in model.I})
model.max_prod = pyo.Param(model.I, initialize={i: max_production[i] for i in model.I})
model.total_resource = pyo.Param(initialize=total_resource)

model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)

def resource_limit_rule(m):
    return sum(m.resource_use[i] * m.x[i] for i in m.I) <= m.total_resource
model.resource_limit = pyo.Constraint(rule=resource_limit_rule)

def capacity_rule(m, i):
    return m.x[i] <= m.max_prod[i]
model.capacity_limits = pyo.Constraint(model.I, rule=capacity_rule)

model.obj = pyo.Objective(
    expr=sum(model.profit[i] * model.x[i] for i in model.I),
    sense=pyo.maximize
)

# 2. Solve with Fallback
solver_names = ['cbc', 'glpk']  # Primary and fallback
solved = False
results = None

for solver_name in solver_names:
    solver = pyo.SolverFactory(solver_name)
    if solver_name == 'cbc':
        solver.options['ratio'] = -1.0  # Example option
    try:
        results = solver.solve(model)
        # Check status
        if (results.solver.status == pyo.SolverStatus.ok and
            results.solver.termination_condition == pyo.TerminationCondition.optimal):
            solved = True
            print(f'Solved optimally with {solver_name}')
            break
        else:
            print(f'Solver {solver_name} did not find optimal solution.')
    except Exception as e:
        print(f'Solver {solver_name} failed with error: {e}')

if not solved:
    raise RuntimeError('All solvers failed to find an optimal solution.')

# 3. Extract and Analyze
pyo.Suffix.LOCAL = True
model.solutions.load_from(results)

total_profit = pyo.value(model.obj)
total_resource_used = sum(pyo.value(model.resource_use[i]) * pyo.value(model.x[i]) for i in model.I)
print(f'Optimal profit: {total_profit}')
print(f'Resource used: {total_resource_used}/{pyo.value(model.total_resource)}')

# 4. Efficiency Analysis (Optional)
efficiency = {i: pyo.value(model.profit[i]) / pyo.value(model.resource_use[i]) for i in model.I}
# Items with lower efficiency are more likely to be reduced in the optimal solution.
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition` after solving, leading to misinterpretation of results.
- Attempting to access variable values via `pyo.value()` before loading the solution into the model.
- Assuming a specific solver (e.g., 'cbc') is always available in the execution environment.
