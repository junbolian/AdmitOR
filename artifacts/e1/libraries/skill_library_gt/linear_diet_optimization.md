---
name: Linear Diet Optimization
description: |
  Model and solve linear cost minimization problems with continuous non-negative decision variables subject to two-sided linear nutrient balance constraints.

---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., OR-Tools) for explicit, low-level model construction. It is ideal for straightforward linear programs where fine-grained control over constraint building and solver interaction is desired.

### Step 1 - Define Data Structures
- Organize problem data into clear, indexed arrays: a cost vector per food item, minimum and maximum requirement vectors per nutrient, and a nutrient content matrix (foods × nutrients).
- Use zero-based integer indexing for foods and nutrients to facilitate systematic loops.

### Step 2 - Declare Decision Variables
- Create continuous, non-negative decision variables for each food item, representing the quantity to purchase or consume.
- Set lower bound to 0 and upper bound to infinity (or a large practical limit) to enforce non-negativity.

### Step 3 - Formulate Two-Sided Constraints
- For each nutrient, create two separate linear inequality constraints: a lower bound (minimum) and an upper bound (maximum).
- Construct each constraint by summing the product of each food's quantity variable and its nutrient content coefficient.

### Step 4 - Set Linear Objective
- Define the objective function as the sum of the cost of each food multiplied by its quantity variable.
- Set the sense to minimization.

### Formulation Template
```json
{
  "sets": [
    {"name": "foods", "description": "Index set for available food items."},
    {"name": "nutrients", "description": "Index set for relevant nutrients."}
  ],
  "parameters": [
    {"name": "cost", "set": "foods", "description": "Unit cost per food item."},
    {"name": "nutrient_min", "set": "nutrients", "description": "Minimum required amount for each nutrient."},
    {"name": "nutrient_max", "set": "nutrients", "description": "Maximum allowed amount for each nutrient."},
    {"name": "nutrient_content", "sets": ["foods", "nutrients"], "description": "Amount of nutrient in a unit of food."}
  ],
  "decision_variables": [
    {"name": "x", "set": "foods", "domain": "NonNegativeReals", "description": "Quantity of each food item."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[f] * x[f] for f in foods)"
  },
  "constraints": [
    {"name": "min_req", "set": "nutrients", "expression": "sum(nutrient_content[f,n] * x[f] for f in foods) >= nutrient_min[n]"},
    {"name": "max_req", "set": "nutrients", "expression": "sum(nutrient_content[f,n] * x[f] for f in foods) <= nutrient_max[n]"}
  ]
}
```

### Common Pitfalls
- Forgetting to create separate constraint objects for lower and upper bounds, leading to incorrect or missing constraints.
- Hard-coding data values within the model building loops, which reduces reusability for different problem instances.
- Neglecting to set an upper bound on variables, which is unnecessary for non-negativity but may be required for solver stability in some APIs.

## Solving stage

### Strategy Overview
The solving stage involves invoking a dedicated LP solver (e.g., GLOP, CBC) through its Python wrapper, checking the solution status rigorously, and validating the results against the original constraints.

### Step 1 - Select and Configure Solver
- Instantiate a linear solver suitable for continuous problems (e.g., `GLOP` for pure LP).
- Set solver-specific options such as time limits or feasibility tolerances if needed.

### Step 2 - Solve and Check Status
- Call the solver's `Solve()` method.
- Immediately check the returned status. Accept `OPTIMAL` or `FEASIBLE` statuses; handle `INFEASIBLE`, `UNBOUNDED`, or `ABNORMAL` statuses with informative error messages.

### Step 3 - Extract and Validate Solution
- Extract the objective value and all variable values.
- Independently recompute the total nutrient amounts from the solution and the nutrient content matrix.
- Compare these computed totals against the minimum and maximum bounds with a numerical tolerance (e.g., 1e-6) to verify constraint satisfaction.

### Step 4 - Report Results
- Format and output the total cost and the quantities of selected foods (e.g., those above a small epsilon).
- Optionally, identify which nutrient constraints are binding (tight) to provide insight into the solution.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# Assume data arrays are defined: cost, nutrient_min, nutrient_max, nutrient_content
n_foods = len(cost)
n_nutrients = len(nutrient_min)

# Decision variables
x = [solver.NumVar(0, solver.infinity(), f'x_{i}') for i in range(n_foods)]

# Nutrient constraints
for j in range(n_nutrients):
    constr_min = solver.Constraint(nutrient_min[j], solver.infinity(), f'min_{j}')
    constr_max = solver.Constraint(-solver.infinity(), nutrient_max[j], f'max_{j}')
    for i in range(n_foods):
        coeff = nutrient_content[i][j]
        constr_min.SetCoefficient(x[i], coeff)
        constr_max.SetCoefficient(x[i], coeff)

# Objective
objective = solver.Objective()
for i in range(n_foods):
    objective.SetCoefficient(x[i], cost[i])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    solution = [x[i].solution_value() for i in range(n_foods)]
    # Verification
    nutrient_totals = [sum(solution[i] * nutrient_content[i][j] for i in range(n_foods)) for j in range(n_nutrients)]
    tolerance = 1e-6
    all_ok = all((nutrient_min[j] - tolerance <= nutrient_totals[j] <= nutrient_max[j] + tolerance) for j in range(n_nutrients))
    if all_ok:
        print(f'RESULT:{total_cost}')
        # Output non-zero quantities
        for i, qty in enumerate(solution):
            if qty > tolerance:
                print(f'  food_{i}: {qty:.4f}')
    else:
        print('ERROR: Solution violates constraints upon verification.')
else:
    print(f'Solver failed with status: {status}')
```

### Common Pitfalls
- Assuming the solver's solution is automatically correct without independent verification against the original constraints.
- Using loose or no tolerance when comparing floating-point numbers for constraint validation, leading to false failures.
- Not handling all possible solver statuses, causing the code to crash on infeasible or unbounded problems.

# Workflow 2 (Algebraic Modeling Language)

## Modeling stage

### Strategy Overview
This workflow uses an Algebraic Modeling Language (AML) like Pyomo to declaratively define the optimization model using sets, parameters, and rules. It promotes separation of model logic from data, enhancing readability and maintainability for complex or frequently modified problems.

### Step 1 - Define Abstract Sets and Parameters
- Declare index sets for foods and nutrients to structure the model abstractly.
- Define all input data (costs, bounds, nutrient content) as indexed parameters over these sets, facilitating easy data injection.

### Step 2 - Declare Variables and Objective
- Create a continuous, non-negative variable for each food item.
- Define the objective function as a linear expression over these variables using the cost parameter.

### Step 3 - Implement Constraint Rules
- Create two constraint components, one for minimum and one for maximum nutrient requirements.
- For each component, implement a rule function that, given a nutrient index, returns the appropriate linear inequality expression by summing over all foods.

### Formulation Template
```json
{
  "sets": [
    {"name": "foods", "description": "Index set for available food items."},
    {"name": "nutrients", "description": "Index set for relevant nutrients."}
  ],
  "parameters": [
    {"name": "cost", "set": "foods", "description": "Unit cost per food item."},
    {"name": "nutrient_min", "set": "nutrients", "description": "Minimum required amount for each nutrient."},
    {"name": "nutrient_max", "set": "nutrients", "description": "Maximum allowed amount for each nutrient."},
    {"name": "nutrient_content", "sets": ["foods", "nutrients"], "description": "Amount of nutrient in a unit of food."}
  ],
  "decision_variables": [
    {"name": "x", "set": "foods", "domain": "NonNegativeReals", "description": "Quantity of each food item."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[f] * x[f] for f in foods)"
  },
  "constraints": [
    {"name": "min_req", "set": "nutrients", "expression": "sum(nutrient_content[f,n] * x[f] for f in foods) >= nutrient_min[n]"},
    {"name": "max_req", "set": "nutrients", "expression": "sum(nutrient_content[f,n] * x[f] for f in foods) <= nutrient_max[n]"}
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's `Set` initialization with data assignment; parameters must be initialized after the model instance is created with concrete data.
- Writing constraint rules that incorrectly reference model components due to misunderstanding of the `model` argument passed to the rule.
- Omitting the `sense` argument in the `Objective` declaration, defaulting to minimization but making intent less clear.

## Solving stage

### Strategy Overview
The solving stage uses a solver factory to interface with backend solvers (e.g., CBC, HiGHS). It focuses on checking both the solver status and the model's termination condition, followed by solution extraction and validation.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object via `SolverFactory`.
- Configure options such as time limit (`seconds`) and optimality tolerance (`ratio` or `gap`) as appropriate for the problem scale.

### Step 2 - Solve and Check Termination
- Execute the solve command on the model instance.
- Check both `solver.status` (e.g., `ok`) and `results.solver.termination_condition` (e.g., `optimal`, `feasible`). Both must indicate success to proceed.

### Step 3 - Extract and Filter Solution
- Retrieve the objective value via `pyo.value(model.obj)`.
- Iterate over decision variables, extracting their values and filtering out near-zero quantities (below a tolerance like 1e-6) for a cleaner output.

### Step 4 - Verify Constraint Satisfaction
- Recompute nutrient totals from the extracted solution and the original data.
- Validate that all totals lie within the specified bounds, accounting for numerical tolerance.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Create an abstract model
model = pyo.AbstractModel()

# Sets
model.F = pyo.Set()  # Foods
model.N = pyo.Set()  # Nutrients

# Parameters
model.cost = pyo.Param(model.F)
model.nutrient_min = pyo.Param(model.N)
model.nutrient_max = pyo.Param(model.N)
model.nutrient_content = pyo.Param(model.F, model.N)

# Variables
model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

# Objective
def obj_rule(m):
    return sum(m.cost[f] * m.x[f] for f in m.F)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Constraints
def min_rule(m, n):
    return sum(m.nutrient_content[f, n] * m.x[f] for f in m.F) >= m.nutrient_min[n]
def max_rule(m, n):
    return sum(m.nutrient_content[f, n] * m.x[f] for f in m.F) <= m.nutrient_max[n]
model.min_constraint = pyo.Constraint(model.N, rule=min_rule)
model.max_constraint = pyo.Constraint(model.N, rule=max_rule)

# Create a concrete instance with data
# Assume data_dict is a dictionary mapping sets/params to data
instance = model.create_instance(data_dict)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(instance, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    total_cost = pyo.value(instance.obj)
    # Extract non-zero quantities
    tolerance = 1e-6
    for f in instance.F:
        qty = pyo.value(instance.x[f])
        if qty > tolerance:
            print(f'food_{f}: {qty:.4f}')
    # Verification (optional but recommended)
    # ... recompute nutrient totals from instance.x and instance.nutrient_content
    print(f'RESULT:{total_cost}')
else:
    print(f'Solve failed. Status: {status}, Termination: {term}')
```

### Common Pitfalls
- Checking only the solver status (`ok`) without verifying the termination condition, potentially accepting suboptimal or failed solves.
- Attempting to access variable values (`pyo.value`) before ensuring the solve was successful, leading to errors.
- Not using a tolerance when filtering near-zero variable values, which can incorrectly hide very small but non-zero solution components.
