---
name: Multi-Resource Integer Allocation
description: |
  Model and solve integer linear programs for allocating products under multiple resource capacity and demand constraints, using either direct solver APIs or algebraic modeling frameworks.
---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., OR-Tools) for explicit, low-level model construction. It is suitable for performance-critical applications or when tight integration with a specific solver's features is required.

### Step 1 - Define Data Structures
- Create indexed lists or dictionaries for product revenue, demand limits, and resource capacities.
- Define a binary consumption matrix mapping products to resources they use.

### Step 2 - Create Integer Variables
- Instantiate integer decision variables for product quantities, directly setting lower bound (0) and upper bound (demand limit) during creation.

### Step 3 - Build Capacity Constraints
- For each resource, create a linear constraint with a right-hand side equal to its capacity.
- Iterate through products and set the coefficient for a variable to 1 only if the product consumes that resource, using the binary matrix.

### Step 4 - Set Linear Objective
- Define a maximization objective as the sum of revenue per product multiplied by its corresponding decision variable.

### Formulation Template
```json
{
  "sets": [
    "P: set of products",
    "R: set of resources"
  ],
  "parameters": [
    "revenue[p] ∈ ℝ⁺, p ∈ P",
    "demand_limit[p] ∈ ℤ⁺, p ∈ P",
    "capacity[r] ∈ ℤ⁺, r ∈ R",
    "consumes[p][r] ∈ {0,1}, p ∈ P, r ∈ R"
  ],
  "decision_variables": [
    "x[p] ∈ ℤ⁺, 0 ≤ x[p] ≤ demand_limit[p], p ∈ P"
  ],
  "objective": {
    "sense": "max",
    "expression": "∑_{p ∈ P} revenue[p] * x[p]"
  },
  "constraints": [
    "∑_{p ∈ P} consumes[p][r] * x[p] ≤ capacity[r], ∀ r ∈ R"
  ]
}
```

### Common Pitfalls
- Adding zero coefficients to constraints unnecessarily, which can bloat the model.
- Forgetting to check the binary matrix for correctness, leading to incorrect capacity constraints.
- Not embedding variable bounds during creation, resulting in extra, trivial constraints.

## Solving stage

### Strategy Overview
Solve the constructed model using a dedicated MIP solver (e.g., SCIP via OR-Tools), configure it for performance, and rigorously verify the solution's status and feasibility.

### Step 1 - Configure Solver
- Instantiate the solver (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set practical limits: time limit, number of threads, and optionally an optimality gap tolerance.

### Step 2 - Execute and Check Status
- Call the solver's `Solve()` method.
- Check the returned status against `OPTIMAL` and `FEASIBLE` codes before proceeding.

### Step 3 - Extract and Validate Solution
- If the status is acceptable, retrieve the objective value and variable values.
- Perform post-solution verification: recalculate total consumption for each resource and compare against capacities to ensure all constraints are satisfied.

### Step 4 - Report Results
- Output the objective value, non-zero variable values, and resource utilization percentages.
- Include solver status and any warnings (e.g., time limit hit) in the output.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)  # milliseconds
# ... (create variables, constraints, objective)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    # Extract variable values and verify constraints
    for r in resources:
        usage = sum(consumes[p][r] * x[p].solution_value() for p in products)
        print(f"Resource {r}: {usage}/{capacity[r]}")
    print(f"RESULT:{obj_val}")
else:
    print(f"SOLVER_FAILED:Status={status}")
```

### Common Pitfalls
- Assuming a `FEASIBLE` status guarantees optimality; it only confirms a valid solution was found.
- Not verifying constraint satisfaction post-solve, which can miss modeling errors.
- Ignoring solver time limits, which can cause hangs on large instances.

# Workflow 2 (Algebraic Modeling Language)

## Modeling stage

### Strategy Overview
This workflow uses an Algebraic Modeling Language (e.g., Pyomo) for declarative, high-level model definition. It enhances readability, maintainability, and ease of modification for complex or research-oriented problems.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for products and resources.
- Declare `Param` objects for revenue, demand limits, capacities, and the consumption matrix, indexed by the appropriate sets.

### Step 2 - Define Integer Variables
- Create a `Var` indexed by the product set with `domain=pyo.NonNegativeIntegers`.
- Implement demand upper bounds either as variable bounds or as explicit constraints.

### Step 3 - Construct Capacity Constraints Declaratively
- Define a constraint rule for each resource. Inside the rule, sum the product variables for all products that consume that resource, using the pre-defined parameter.

### Step 4 - Formulate Objective
- Define the objective as a `pyo.Objective` with `sense=pyo.maximize` and an expression summing revenue times variable over all products.

### Formulation Template
```json
{
  "sets": [
    "P: set of products",
    "R: set of resources"
  ],
  "parameters": [
    "revenue[p] ∈ ℝ⁺, p ∈ P",
    "demand_limit[p] ∈ ℤ⁺, p ∈ P",
    "capacity[r] ∈ ℤ⁺, r ∈ R",
    "consumes[p][r] ∈ {0,1}, p ∈ P, r ∈ R"
  ],
  "decision_variables": [
    "x[p] ∈ ℤ⁺, p ∈ P"
  ],
  "objective": {
    "sense": "max",
    "expression": "∑_{p ∈ P} revenue[p] * x[p]"
  },
  "constraints": [
    "x[p] ≤ demand_limit[p], ∀ p ∈ P",
    "∑_{p ∈ P} consumes[p][r] * x[p] ≤ capacity[r], ∀ r ∈ R"
  ]
}
```

### Common Pitfalls
- Using inefficient rule logic (e.g., iterating over all products for each resource) instead of filtering with the consumption matrix.
- Confusing Pyomo's `Constraint` (for expressions) with variable bounds.
- Not verifying that all parameters are correctly initialized before model instantiation.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a compatible solver (e.g., CBC, HiGHS) via the `SolverFactory` interface. Focus on robust status checking and systematic solution validation.

### Step 1 - Select and Configure Solver
- Create a solver object using `pyo.SolverFactory("solver_name")` (e.g., "cbc").
- Set key options: time limit (`seconds`), optimality gap tolerance (`ratio` or `mip_rel_gap`), and number of threads.

### Step 2 - Solve and Inspect Termination
- Execute `solver.solve(model, tee=False)`.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Validate and Extract Solution
- If termination is acceptable, retrieve the objective value using `pyo.value(model.obj)`.
- Perform automated verification: loop through resources, sum the consumption of solved variables, and compare to capacity.

### Step 4 - Report Structured Output
- Print the objective value in a parseable format (e.g., `RESULT:{value}`).
- Output key solution details: variable values and resource utilization statistics for auditing.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=products)
model.R = pyo.Set(initialize=resources)
# ... (define parameters, variables, constraints, objective)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model)

from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = pyo.value(model.obj)
    # Post-solve verification
    for r in model.R:
        usage = sum(pyo.value(model.consumes[p, r]) * pyo.value(model.x[p]) for p in model.P if pyo.value(model.consumes[p, r]) > 0)
        print(f"Resource {r}: {usage}/{pyo.value(model.capacity[r])}")
    print(f"RESULT:{obj_val}")
else:
    print(f"SOLVER_FAILED:Status={status},Termination={term}")
```

### Common Pitfalls
- Relying solely on the solver's "optimal" flag without performing independent feasibility checks.
- Misinterpreting `SolverStatus.ok` (solver ran) as a guarantee of solution optimality or feasibility.
- Not setting a time limit, which can cause the process to stall on difficult instances.
