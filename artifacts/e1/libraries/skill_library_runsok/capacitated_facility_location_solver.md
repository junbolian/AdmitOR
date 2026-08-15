---
name: Capacitated Facility Location Solver
description: |
  Model and solve mixed-integer linear programs for selecting facilities and allocating flows to meet demand at minimum total cost, using either direct solver APIs or algebraic modeling frameworks.
---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., OR-Tools) for explicit, low-level model construction. It is suited for performance-critical applications and offers fine-grained control over variable creation, constraint building, and solver configuration.

### Step 1 - Define Data Structures
- Organize problem parameters into clear, indexable data structures: lists for facility capacities and fixed costs, a 2D list or dictionary for per-unit shipping costs, and a list for customer demands.
- Define sets for facilities (`I`) and customers (`J`) as ranges or lists to be used in loops.

### Step 2 - Create Decision Variables
- Create binary variables `y[i]` for each facility `i` to indicate if it is open.
- Create continuous, non-negative variables `x[i,j]` for the flow from facility `i` to customer `j`.

### Step 3 - Formulate Constraints
- **Demand Satisfaction:** For each customer `j`, enforce `sum_i x[i,j] == demand[j]`.
- **Capacity-Activation Link:** For each facility `i`, enforce `sum_j x[i,j] <= capacity[i] * y[i]`. This ensures no flow from a closed facility.
- **Optional Strengthening:** Add constraints `x[i,j] <= demand[j] * y[i]` to tighten the LP relaxation and improve solver performance.

### Step 4 - Define Objective Function
- Formulate the objective to minimize total cost: `sum_i fixed_cost[i] * y[i] + sum_i sum_j shipping_cost[i,j] * x[i,j]`.

### Formulation Template
```json
{
  "sets": ["I (facilities)", "J (customers)"],
  "parameters": ["capacity[i]", "fixed_cost[i]", "shipping_cost[i,j]", "demand[j]"],
  "decision_variables": ["y[i] ∈ {0,1}", "x[i,j] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum_i fixed_cost[i] * y[i] + sum_i sum_j shipping_cost[i,j] * x[i,j]"
  },
  "constraints": [
    "sum_i x[i,j] = demand[j], ∀j ∈ J",
    "sum_j x[i,j] ≤ capacity[i] * y[i], ∀i ∈ I",
    "x[i,j] ≤ demand[j] * y[i], ∀i ∈ I, ∀j ∈ J (optional)"
  ]
}
```

### Common Pitfalls
- Forgetting to link the binary `y` variables to the continuous `x` variables, allowing flow from unopened facilities.
- Using loose upper bounds for `x[i,j]` (e.g., `solver.infinity()`) without the optional strengthening constraints, which can slow down the MIP solve.
- Incorrectly indexing cost or demand arrays when building constraints in loops, leading to model infeasibility or incorrect results.

## Solving stage

### Strategy Overview
Solve the constructed model using a MILP solver backend (e.g., SCIP, CBC). Configure solver limits, solve, and rigorously check the solution status and feasibility.

### Step 1 - Initialize Solver and Set Parameters
- Instantiate a solver object (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set practical limits: time limit (`SetTimeLimit(ms)`), optimality gap tolerance (`SetRelativeGapTolerance()`), and number of threads (`SetNumThreads(n)`).

### Step 2 - Solve and Check Status
- Execute `solver.Solve()`.
- Check the result status: `OPTIMAL` is ideal; `FEASIBLE` indicates a heuristic solution within limits. Handle `INFEASIBLE` or `UNBOUNDED` statuses appropriately.

### Step 3 - Extract and Validate Solution
- If optimal or feasible, extract variable values: `y[i].solution_value()` and `x[i,j].solution_value()`.
- Programmatically verify core constraints: demand satisfaction and capacity-activation logic. Compute a cost breakdown (fixed vs. variable) to validate against the solver's objective value.

### Step 4 - Analyze and Report
- Identify opened facilities (`y[i] > 0.5`).
- Calculate capacity utilization for opened facilities.
- Output key metrics and the full solution in a structured format (e.g., JSON) for downstream use.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(60000)  # 60 seconds
# ... (Variable and constraint creation as per Modeling Stage)

# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL or status == solver.FEASIBLE:
    print(f"Objective value: {solver.Objective().Value()}")
    # Extract and validate solution
    total_fixed = sum(fixed_cost[i] * y[i].solution_value() for i in I)
    total_transport = sum(shipping_cost[i][j] * x[i,j].solution_value() for i in I for j in J)
    # ... (Further validation and reporting)
else:
    print("No optimal solution found.")
```

### Common Pitfalls
- Not setting a time limit or optimality gap for large problems, potentially causing excessively long runtimes.
- Assuming the solver status `FEASIBLE` implies optimality; always check the relative MIP gap if available.
- Failing to verify that the extracted solution satisfies all constraints, especially after a non-optimal termination.

# Workflow 2 (Algebraic Modeling Language)

## Modeling stage

### Strategy Overview
This workflow uses an Algebraic Modeling Language (AML) like Pyomo to declaratively define the model using sets, parameters, and rules. It enhances readability, maintainability, and is ideal for rapid prototyping and research.

### Step 1 - Declare Abstract Sets and Parameters
- Define abstract sets for facilities and customers.
- Declare parameters for costs, demands, and capacities, initializing them with data.

### Step 2 - Define Variables and Objective
- Declare binary variables for facility opening and continuous variables for allocation flows.
- Define the objective function as a declarative expression summing fixed and transportation costs.

### Step 3 - Define Constraints via Rules
- Create a demand satisfaction constraint using a rule that iterates over customers.
- Create a capacity-activation constraint using a rule that iterates over facilities.
- Optionally, add a strengthening constraint per facility-customer pair.

### Formulation Template
```json
{
  "sets": ["model.I", "model.J"],
  "parameters": ["model.cap", "model.f", "model.c", "model.d"],
  "decision_variables": ["model.y[I]", "model.x[I, J]"],
  "objective": {
    "sense": "min",
    "expression": "sum(model.f[i] * model.y[i] for i in model.I) + sum(model.c[i,j] * model.x[i,j] for i in model.I for j in model.J)"
  },
  "constraints": [
    "model.demand[J]: sum(model.x[i,j] for i in model.I) == model.d[j]",
    "model.capacity[I]: sum(model.x[i,j] for j in model.J) <= model.cap[i] * model.y[i]",
    "model.strengthen[I, J]: model.x[i,j] <= model.d[j] * model.y[i] (optional)"
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's `AbstractModel` with `ConcreteModel`; use `ConcreteModel` for immediate data integration unless a purely symbolic model is needed.
- Defining constraint rules with incorrect indexing or referencing parameters/variables incorrectly, leading to runtime errors.
- Omitting the domain specification for variables (e.g., `NonNegativeReals`, `Binary`), causing solver errors.

## Solving stage

### Strategy Overview
Solve the AML model using a compatible MILP solver (e.g., HiGHS, CBC via Pyomo's `SolverFactory`). Configure solver options, manage solution loading, and perform post-solution validation.

### Step 1 - Instantiate Solver and Configure
- Create a solver object: `SolverFactory('highs')`.
- Set solver options: time limit (`time_limit`), MIP gap tolerance (`mip_rel_gap`), and others as needed. Avoid conflicting settings (e.g., `threads` may not be supported by all solvers).

### Step 2 - Solve and Handle Solution Loading
- Execute solve with `results = solver.solve(model, load_solutions=False)` to maintain control.
- Check the solver termination condition from `results.solver.termination_condition` (e.g., `optimal`, `maxTimeLimit`).
- If optimal or feasible, load the solution into the model: `model.solutions.load_from(results)`.

### Step 3 - Validate and Analyze Solution
- Verify constraint satisfaction by iterating through the model constraints and checking the values.
- Compute cost components and facility utilization metrics from the populated model variables.
- Report opened facilities, allocation patterns, and cost breakdown.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=facility_indices)
model.J = pyo.Set(initialize=customer_indices)
# ... (Parameter and variable definition as per Modeling Stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, load_solutions=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    model.solutions.load_from(results)
    # Validate and analyze
    obj_val = pyo.value(model.obj)
    open_facs = [i for i in model.I if pyo.value(model.y[i]) > 0.5]
    # ... (Further analysis)
else:
    print(f"Solver terminated with condition: {results.solver.termination_condition}")
```

### Common Pitfalls
- Forgetting to set `load_solutions=False` and then trying to access variable values before they are loaded, resulting in `None`.
- Not checking the solver termination condition, misinterpreting a time-limit stop as optimality.
- Attempting to use solver-specific options not supported by the chosen backend, causing warnings or errors.
