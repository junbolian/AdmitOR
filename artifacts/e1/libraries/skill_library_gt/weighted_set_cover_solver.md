---
name: Weighted Set Cover Solver
description: |
  Model and solve weighted set cover problems using binary selection variables, coverage constraints, and cost minimization objectives via MIP solvers.
---

# Workflow 1 (OR-Tools Backend)

## Modeling stage

### Strategy Overview
Formulate the problem as a Weighted Set Cover MIP using the OR-Tools `pywraplp` interface. This workflow is suited for direct solver access with explicit constraint building and is efficient for large-scale problems.

### Step 1 - Define Problem Data Structures
- Represent the list of selectable items and their associated costs.
- Define the coverage relationship, typically as a dictionary mapping each element (requirement) to a list of indices of items that cover it.
- Ensure data uses consistent 0-based indexing for programming.

### Step 2 - Create Binary Decision Variables
- Instantiate a solver object (e.g., SCIP, CBC).
- Create a list of binary variables `x[i] ∈ {0,1}` for each selectable item `i`.

### Step 3 - Formulate the Objective Function
- Define the objective as a linear weighted sum: `minimize Σ cost[i] * x[i]`.
- Set the objective sense to minimization in the solver.

### Step 4 - Add Coverage Constraints
- For each element `j` requiring coverage, create a linear constraint with a lower bound of 1.
- For the items `i` that cover element `j`, set the coefficient of `x[i]` to 1 in the corresponding constraint.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items (e.g., facilities, hubs)",
    "J: Set of elements requiring coverage (e.g., routes, zones)"
  ],
  "parameters": [
    "cost[i ∈ I]: Cost of selecting item i",
    "cover[j ∈ J]: List of item indices in I that cover element j"
  ],
  "decision_variables": [
    "x[i ∈ I] ∈ {0, 1}: Binary selection variable for item i"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "coverage[j ∈ J]: sum(x[i] for i in cover[j]) >= 1"
  ]
}
```

### Common Pitfalls
- Using 1-based indexing from problem data without converting to 0-based for the solver, causing index errors.
- Forgetting to set the objective sense to minimization, defaulting to maximization.
- Creating constraints with incorrect bounds (e.g., using equality `==1` instead of inequality `>=1`).

## Solving stage

### Strategy Overview
Solve the MIP model using the OR-Tools wrapper, configure solver limits, extract the solution, and perform post-solution verification to ensure correctness and optimality.

### Step 1 - Configure and Execute Solver
- Initialize the chosen solver backend (e.g., `"SCIP"`).
- Set practical limits: time limit (ms) and number of threads.
- Call `solver.Solve()` and capture the status code.

### Step 2 - Extract and Validate Solution
- Check if the solver status is `OPTIMAL` or `FEASIBLE`.
- Extract selected items where `x[i].solution_value() > 0.5` (accounting for numerical tolerance).
- Compute the total cost from the objective value.

### Step 3 - Verify Solution Feasibility
- Independently verify that every element `j` is covered by at least one selected item using the original coverage mapping.
- Raise an alert or error if any requirement is uncovered.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Initialize solver with configuration
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(timeout_ms)  # e.g., 30000
solver.SetNumThreads(num_threads)  # e.g., 4

# 2. Build model (variables, objective, constraints) as per Modeling Stage
# ... (Refer to Formulation Template for structure)

# 3. Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [i for i in range(num_items) if x[i].solution_value() > 0.5]
    total_cost = solver.Objective().Value()
    # 4. Verification
    for req_idx, covering_list in coverage_dict.items():
        if not any(item_idx in selected for item_idx in covering_list):
            raise ValueError(f"Requirement {req_idx} is not covered.")
else:
    raise RuntimeError(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, leading to runtime errors.
- Using a strict equality (`== 1.0`) to interpret binary variable values instead of a tolerance (`> 0.5`).
- Omitting solution verification, potentially accepting incorrect results due to solver or modeling errors.

# Workflow 2 (Pyomo Backend)

## Modeling stage

### Strategy Overview
Formulate the problem as a Weighted Set Cover MIP using the Pyomo modeling language. This workflow emphasizes declarative model construction, separation of data and model, and flexibility in solver choice.

### Step 1 - Define Abstract Sets and Parameters
- Create Pyomo `Set` objects for the collection of selectable items (`I`) and elements requiring coverage (`J`).
- Define `Param` objects for costs and coverage relationships, initializing them from input data.

### Step 2 - Declare Binary Decision Variables
- Create a Pyomo `Var` indexed over the item set `I` with `domain=pyo.Binary`.

### Step 3 - Formulate the Objective Function
- Define a Pyomo `Objective` with the expression `sum(cost[i] * x[i] for i in model.I)` and `sense=pyo.minimize`.

### Step 4 - Define Coverage Constraints via Rule
- Create a Pyomo `Constraint` indexed over the element set `J`.
- For each element `j`, the rule should return `sum(x[i] for i in covering_sets[j]) >= 1`.

### Formulation Template
```json
{
  "sets": [
    "model.I: Pyomo Set of selectable items",
    "model.J: Pyomo Set of elements to cover"
  ],
  "parameters": [
    "model.cost: Pyomo Param(model.I) for item costs",
    "model.cover: Dictionary mapping element j to list of items in I that cover it"
  ],
  "decision_variables": [
    "model.x: Pyomo Var(model.I, domain=pyo.Binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[i] * model.x[i] for i in model.I)"
  },
  "constraints": [
    "model.coverage_constr: Pyomo Constraint(model.J, rule=coverage_rule)"
  ]
}
```

### Common Pitfalls
- Using Python lists/dicts directly in constraint rules instead of Pyomo `Set`/`Param` objects, causing performance and scoping issues.
- Defining constraint rules with incorrect indexing or logic that doesn't vectorize over the Pyomo Set.
- Not separating the model building function from the solving logic, reducing reusability.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver (e.g., HiGHS, CBC), handle solver results robustly, extract the solution, and perform independent verification.

### Step 1 - Select and Configure Solver
- Instantiate a solver via `SolverFactory("solver_name")` (e.g., `"highs"`, `"cbc"`).
- Set solver options such as time limit (`seconds`), optimality gap (`ratio`), and threads.

### Step 2 - Execute Solver and Check Termination
- Call `solver.solve(model, ...)` with appropriate arguments.
- Check both `solver.status == SolverStatus.ok` and `termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Load Solution and Extract Results
- If the status checks pass, load the solution into the model.
- Extract selected items where `pyo.value(model.x[i]) > 0.5`.
- Compute the total cost from the objective value or by summing costs of selected items.

### Step 4 - Independent Verification and Reporting
- Verify coverage by checking each element against the selected items using the original coverage data.
- Report the solution and verification status.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build model (as per Modeling Stage)
def build_model(costs, coverage_dict):
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=range(len(costs)))
    model.J = pyo.Set(initialize=coverage_dict.keys())
    model.cost = pyo.Param(model.I, initialize=lambda m, i: costs[i])
    model.x = pyo.Var(model.I, domain=pyo.Binary)
    model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)
    def coverage_rule(m, j):
        return sum(m.x[i] for i in coverage_dict[j]) >= 1
    model.coverage = pyo.Constraint(model.J, rule=coverage_rule)
    return model

model = build_model(cost_list, coverage_mapping)

# 2. Configure and run solver
solver = pyo.SolverFactory("highs")
solver.options["seconds"] = time_limit
solver.options["ratio"] = optimality_gap  # e.g., 0.0
solver.options["threads"] = num_threads

results = solver.solve(model, tee=verbose_output)

# 3. Check results and extract solution
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = pyo.value(model.obj)
    # 4. Verification
    for j in coverage_mapping:
        if not any(i in selected for i in coverage_mapping[j]):
            raise ValueError(f"Element {j} is not covered.")
else:
    raise RuntimeError(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Accessing variable values (`pyo.value`) before checking solver status and loading the solution.
- Using overly complex solver configurations initially, which can obscure errors; start with defaults.
- Neglecting to verify the solution independently, trusting the solver's feasibility report without confirmation.
