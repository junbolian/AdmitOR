---
name: Linear Program with Bounded Nutrient Constraints
description: |
  Model and solve linear cost minimization problems with continuous non-negative variables and two-sided linear inequality constraints for nutrient balance, using systematic data organization and solver-agnostic verification.
---

# Workflow 1 (Pyomo with Rule-Based Construction)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to create a clean separation between data and model logic. It employs constraint rules for efficient generation of nutrient balance constraints, making the model highly maintainable and scalable for problems with many items and requirements.

### Step 1 - Define Index Sets and Parameters
- Declare explicit sets for `items` (e.g., foods) and `requirements` (e.g., nutrients) to structure the problem.
- Organize data into separate parameters: `cost` per item, `min_req` and `max_req` per requirement, and a `content` matrix (requirement × item).

### Step 2 - Declare Decision Variables
- Create continuous, non-negative decision variables representing the quantity of each item to select.
- Ensure variable domain is set to `pyo.NonNegativeReals` to prevent negative quantities.

### Step 3 - Formulate the Objective Function
- Define a linear cost minimization objective by summing the product of each item's cost and its selected quantity.
- Set the objective sense to `pyo.minimize`.

### Step 4 - Generate Bounded Constraints via Rules
- For each requirement, create a lower bound constraint rule that ensures the total content (sum of item quantities × content coefficients) meets the minimum.
- For each requirement, create an upper bound constraint rule that ensures the total content does not exceed the maximum.
- Implement these as separate `pyo.Constraint` objects using the defined sets and rules.

### Formulation Template
```json
{
  "sets": [
    {"name": "items", "description": "Index set for selectable items."},
    {"name": "requirements", "description": "Index set for balance requirements."}
  ],
  "parameters": [
    {"name": "cost", "index": "items", "description": "Unit cost per item."},
    {"name": "min_req", "index": "requirements", "description": "Minimum required amount for each requirement."},
    {"name": "max_req", "index": "requirements", "description": "Maximum allowed amount for each requirement."},
    {"name": "content", "index": ["requirements", "items"], "description": "Amount of requirement per unit of item."}
  ],
  "decision_variables": [
    {"name": "x", "index": "items", "domain": "NonNegativeReals", "description": "Quantity of item to select."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in items)"
  },
  "constraints": [
    {"name": "min_constraint", "index": "requirements", "expression": "sum(content[r,i] * x[i] for i in items) >= min_req[r]"},
    {"name": "max_constraint", "index": "requirements", "expression": "sum(content[r,i] * x[i] for i in items) <= max_req[r]"}
  ]
}
```

### Common Pitfalls
- Forgetting to initialize all parameters before model instantiation, which causes rule evaluation errors.
- Defining constraint rules with incorrect index order, leading to mismatched data during summation.
- Not using a tolerance when checking for non-zero variables in the solution, potentially missing small but meaningful quantities.

## Solving stage

### Strategy Overview
This solving stage uses the HiGHS solver via Pyomo's SolverFactory for high-performance linear programming. It emphasizes robust solution status checking, post-solution verification of constraint satisfaction, and clear extraction of results.

### Step 1 - Select and Configure Solver
- Instantiate the solver using `pyo.SolverFactory("highs")` for linear programs.
- Set practical options such as `time_limit` and `threads` to manage computational resources.

### Step 2 - Solve and Check Termination Status
- Execute the solve command and capture the results object.
- Verify both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`) before proceeding.

### Step 3 - Post-Solution Verification
- Calculate the actual value for each requirement constraint using the solved variable values.
- Compare these values against the min/max bounds with a numerical tolerance (e.g., 1e-6) to confirm feasibility and catch precision issues.

### Step 4 - Extract and Report Results
- Retrieve the objective value.
- Filter and report non-zero decision variables (where quantity > tolerance).
- Optionally, identify binding constraints where the total content is within tolerance of a bound.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (using placeholder data)
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=range(num_items))
model.requirements = pyo.Set(initialize=range(num_reqs))
model.cost = pyo.Param(model.items, initialize=cost_data)
model.min_req = pyo.Param(model.requirements, initialize=min_req_data)
model.max_req = pyo.Param(model.requirements, initialize=max_req_data)
model.content = pyo.Param(model.requirements, model.items, initialize=content_data)

model.x = pyo.Var(model.items, domain=pyo.NonNegativeReals)
model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.items), sense=pyo.minimize)

def min_rule(m, r):
    return sum(m.content[r, i] * m.x[i] for i in m.items) >= m.min_req[r]
def max_rule(m, r):
    return sum(m.content[r, i] * m.x[i] for i in m.items) <= m.max_req[r]
model.min_constraint = pyo.Constraint(model.requirements, rule=min_rule)
model.max_constraint = pyo.Constraint(model.requirements, rule=max_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["threads"] = 4
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    print(f"Optimal cost: {pyo.value(model.obj):.2f}")
    # Post-solution verification
    tolerance = 1e-6
    for r in model.requirements:
        total = sum(pyo.value(model.content[r, i]) * pyo.value(model.x[i]) for i in model.items)
        print(f"Requirement {r}: total = {total:.6f}, min = {pyo.value(model.min_req[r])}, max = {pyo.value(model.max_req[r])}")
else:
    print("Solve failed or did not converge to a feasible solution.")
```

### Common Pitfalls
- Assuming a solution is valid without checking the termination condition, potentially using suboptimal or infeasible results.
- Not using a tolerance when comparing constraint totals to bounds, misinterpreting numerical noise as a violation.
- Extracting variable values without first checking if the solver status is `ok`, which can cause errors if the solve failed.

# Workflow 2 (Direct Matrix-Based LP Construction)

## Modeling stage

### Strategy Overview
This workflow bypasses high-level modeling libraries to construct the linear program directly using coefficient matrices and vectors. It is suited for integration with solvers that accept standard LP formats (e.g., via `scipy.optimize.linprog` or solver-specific APIs) and offers fine-grained control over the problem structure.

### Step 1 - Organize Data into Matrices and Vectors
- Create a cost vector `c` where each element corresponds to the unit cost of an item.
- Construct a nutrient content matrix `A` where rows are requirements and columns are items.
- Define lower bound vector `lb_req` and upper bound vector `ub_req` for each requirement.

### Step 2 - Map Constraints to Standard LP Form
- Transform the two-sided nutrient constraints `lb_req <= A * x <= ub_req` into the standard form `A_ub * x <= b_ub` and `A_eq * x = b_eq` as required by the target solver API.
- For solvers requiring separate lower and upper bounds on variables, set variable bounds `0 <= x <= inf`.

### Step 3 - Define the Objective and Variable Bounds
- State the objective as the linear dot product `c @ x` to be minimized.
- Explicitly set variable bounds to ensure non-negativity.

### Formulation Template
```json
{
  "sets": [
    {"name": "n_items", "description": "Number of selectable items."},
    {"name": "n_requirements", "description": "Number of balance requirements."}
  ],
  "parameters": [
    {"name": "c", "dim": ["n_items"], "description": "Cost vector per item."},
    {"name": "A", "dim": ["n_requirements", "n_items"], "description": "Content matrix (requirements × items)."},
    {"name": "lb_req", "dim": ["n_requirements"], "description": "Lower bound vector for requirements."},
    {"name": "ub_req", "dim": ["n_requirements"], "description": "Upper bound vector for requirements."}
  ],
  "decision_variables": [
    {"name": "x", "dim": ["n_items"], "bounds": "[0, inf]", "description": "Quantity vector for items."}
  ],
  "objective": {
    "sense": "min",
    "expression": "c @ x"
  },
  "constraints": [
    {"name": "requirement_bounds", "form": "lb_req <= A @ x <= ub_req", "description": "Two-sided linear inequality constraints."}
  ]
}
```

### Common Pitfalls
- Incorrectly shaping the coefficient matrix `A`, leading to mismatched dimensions during constraint evaluation.
- Forgetting to convert `inf` bounds to a large numerical value for solvers that do not handle infinity directly.
- Not preserving the order of items and requirements between the cost vector, content matrix, and bound vectors.

## Solving stage

### Strategy Overview
This stage solves the LP using a direct matrix interface, such as `scipy.optimize.linprog` or a commercial solver's API. It focuses on constructing the constraint matrix in the solver's required format, handling numerical infinities, and parsing the often dictionary-structured solver output.

### Step 1 - Format Constraints for Solver API
- For solvers requiring inequality form, stack `A` and `-A` to create constraints for `A @ x <= ub_req` and `-A @ x <= -lb_req`.
- Replace any `inf` values in upper bounds with a large finite number (e.g., `1e9`) if the solver does not support infinity.

### Step 2 - Invoke Solver with Proper Options
- Call the solver function (e.g., `linprog`) with the cost vector, constraint matrices/vectors, and variable bounds.
- Set solver-specific options for time limit, optimality tolerance, and verbosity.

### Step 3 - Interpret Solver Output and Status
- Check the solver's success flag or status message to determine if an optimal solution was found.
- If successful, extract the solution vector `x` and the objective value.

### Step 4 - Validate Solution Against Original Bounds
- Recalculate `A @ x` using the solution vector.
- Verify that the result lies within the original `lb_req` and `ub_req` bounds, accounting for numerical tolerance.

### Code Usage
```python
import numpy as np
from scipy.optimize import linprog

# Build model from formulation (using placeholder data)
# c: cost vector, shape (n_items,)
# A: content matrix, shape (n_requirements, n_items)
# lb_req, ub_req: bound vectors, shape (n_requirements,)

# 1. Format constraints for scipy's linprog (A_ub * x <= b_ub)
# Combine A @ x <= ub_req and -A @ x <= -lb_req
A_ub = np.vstack([A, -A])
b_ub = np.hstack([ub_req, -lb_req])
# Replace inf in b_ub with a large number
large_val = 1e9
b_ub = np.where(np.isinf(b_ub), np.sign(b_ub) * large_val, b_ub)

# Variable bounds: 0 <= x <= inf
bounds = [(0, None)] * len(c)

# 2. Solve with status / termination checks
options = {'disp': True, 'time_limit': 30}
result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs', options=options)

if result.success:
    x_opt = result.x
    print(f"Optimal cost: {result.fun:.2f}")
    # Post-solution verification
    totals = A @ x_opt
    tolerance = 1e-6
    for i in range(len(totals)):
        if not (lb_req[i] - tolerance <= totals[i] <= ub_req[i] + tolerance):
            print(f"Warning: Requirement {i} total {totals[i]:.6f} outside bounds [{lb_req[i]}, {ub_req[i]}]")
else:
    print(f"Solver failed: {result.message}")
```

### Common Pitfalls
- Incorrectly stacking matrices for the inequality constraints, reversing the sign and direction of bounds.
- Not handling `inf` values in bounds, causing solver errors.
- Relying solely on the solver's success flag without recalculating constraint totals, which may miss subtle numerical violations.
