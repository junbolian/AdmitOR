---
name: Multi-Dimensional Flow Allocation
description: |
  Model and solve linear programs for allocating flows from multiple sources to multiple destinations across product types, maximizing profit while satisfying exact demand.

---

# Workflow 1 (OR-Tools / GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to construct a multi-index flow model. It is designed for direct, imperative model building with explicit variable and constraint creation, suitable for prototyping and integration into larger systems.

### Step 1 - Define Multi-Dimensional Variables
- Structure decision variables as a multi-dimensional dictionary or array, indexed by source, destination, and product type.
- Instantiate each variable as a continuous `NumVar` with a lower bound of 0 to enforce non-negativity directly.
- Use descriptive naming patterns (e.g., `x_c_m_p`) for traceability.

### Step 2 - Enforce Demand Satisfaction Constraints
- For each combination of destination and product type, create a single linear equality constraint.
- Set the constraint's lower and upper bounds to the exact demand value to enforce strict satisfaction.
- Iterate over all sources to sum their contributions to this constraint using `SetCoefficient`.

### Step 3 - Build Linear Objective
- Define the objective function using the solver's `Objective()` method.
- Iterate over all variable indices, adding each variable's contribution multiplied by its corresponding unit profit coefficient.
- Set the objective sense to maximization.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "destinations",
    "products"
  ],
  "parameters": [
    "profit[source][destination][product]",
    "demand[destination][product]"
  ],
  "decision_variables": [
    "x[source][destination][product] >= 0"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s][d][p] * x[s][d][p])"
  },
  "constraints": [
    "sum(x[s][d][p] for s in sources) == demand[d][p] for each d in destinations, p in products"
  ]
}
```

### Common Pitfalls
- Forgetting to set the lower bound of flow variables to 0, leading to invalid negative allocations.
- Mismatching the order of indices between profit/demand data structures and variable creation loops.
- Creating separate non-negativity constraints instead of using variable bounds, which reduces model efficiency.

## Solving stage

### Strategy Overview
Solve the built model using the GLOP linear programming solver, which is optimized for continuous LPs. The focus is on verifying solution status, extracting results, and performing post-solve validation.

### Step 1 - Configure and Execute Solver
- Instantiate the solver using `pywraplp.Solver.CreateSolver('GLOP')`.
- Call `solver.Solve()` to initiate the optimization.

### Step 2 - Verify Solution Status
- Check the solver's result status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.).
- Proceed to extract variable values and objective only if the status indicates `OPTIMAL` or `FEASIBLE`.

### Step 3 - Extract and Validate Results
- Retrieve the objective value via `solver.Objective().Value()`.
- Iterate over all variables, storing solution values for those exceeding a negligible threshold (e.g., > 1e-6).
- Optionally, recompute the total profit and verify demand constraints are satisfied within a small numerical tolerance.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation as per modeling stage)

# solve with status / termination checks
result_status = solver.Solve()
if result_status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    # Extract non-zero flows
    solution = {}
    for var_name, var in variables.items():
        val = var.solution_value()
        if val > 1e-6:
            solution[var_name] = val
    # Optional validation
    # ...
else:
    print(f"Solver did not find a solution. Status: {result_status}")
```

### Common Pitfalls
- Assuming `OPTIMAL` is the only acceptable status; `FEASIBLE` solutions are also valid for some use cases.
- Not using a tolerance when checking variable values, leading to excessive output from near-zero flows.
- Failing to handle different solver status codes, causing crashes on infeasible or unbounded problems.

---

# Workflow 2 (Pyomo / HiGHS)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, a Python-based algebraic modeling language, to declaratively define the flow model. It leverages Pyomo's `ConcreteModel`, `Set`, `Var`, `Constraint`, and `Objective` components for a structured, maintainable, and solver-agnostic formulation.

### Step 1 - Declare Index Sets
- Define Pyomo `Set` objects for each dimension: sources, destinations, and product types.
- Initialize sets with the corresponding list of element identifiers to structure the model domain.

### Step 2 - Define Variables with Domain
- Declare a single Pyomo `Var` indexed over the Cartesian product of the three sets.
- Specify `domain=pyo.NonNegativeReals` to enforce non-negativity as part of the variable definition.

### Step 3 - Construct Objective and Constraints
- Build the objective using a `sum` expression over all indices, multiplying each variable by its profit coefficient.
- Define a `Constraint` component indexed by destination and product type. For each index, create a rule that sums flows from all sources and enforces equality with the demand parameter.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "destinations",
    "products"
  ],
  "parameters": [
    "profit[source][destination][product]",
    "demand[destination][product]"
  ],
  "decision_variables": [
    "x[source, destination, product] in NonNegativeReals"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s][d][p] * x[s, d, p])"
  },
  "constraints": [
    "sum(x[s, d, p] for s in sources) == demand[d][p] for each d in destinations, p in products"
  ]
}
```

### Common Pitfalls
- Using `AbstractModel` when immediate data population is intended; `ConcreteModel` is often simpler for script-based workflows.
- Defining constraint rules with incorrect indexing or forgetting to return the expression.
- Storing parameters as plain Python dictionaries without linking them to Pyomo `Param` objects, which can limit model portability.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS LP solver via the `SolverFactory` interface. The process includes setting solver options, checking termination conditions, and extracting solution data into usable Python structures.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object using `SolverFactory('highs')`.
- Configure options such as time limit and number of threads via `options` dictionary.

### Step 2 - Solve and Check Termination
- Execute `solver.solve(model, ...)`.
- Verify the solver status (`model.solutions.status`) is `SolverStatus.ok` and the termination condition (`model.solutions.termination_condition`) is `optimal` or `feasible`.

### Step 3 - Process Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate over the variable index set, accessing `pyo.value(model.x[idx])` for each variable.
- Filter and store allocations above a defined tolerance.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=source_list)
# ... (add other sets, variables, objective, constraints as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    objective_value = pyo.value(model.obj)
    # Extract non-zero flows
    solution = {}
    for idx in model.x.index_set():
        val = pyo.value(model.x[idx])
        if val > 1e-6:
            solution[idx] = val
    # Optional validation
    # ...
else:
    print(f"Solver failed. Status: {results.solver.status}, "
          f"Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `solver.status` with `termination_condition`; both must be checked for a complete solution state.
- Accessing variable values before verifying the solution is valid, which may raise errors.
- Not setting a time limit for large-scale problems, potentially causing the script to hang.
