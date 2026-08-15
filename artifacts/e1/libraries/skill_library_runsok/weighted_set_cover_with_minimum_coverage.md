---
name: Weighted Set Cover with Minimum Coverage
description: |
  Model and solve binary selection problems with weighted costs and coverage constraints requiring minimum selections from subsets, using either direct solver APIs or algebraic modeling frameworks.
---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., OR-Tools) for explicit control over variable and constraint construction, ideal for performance-critical or tightly integrated applications.

### Step 1 - Define Data Structures
- Organize problem data into dictionaries for costs and coverage relationships.
- Represent each coverage requirement as a tuple containing a set of eligible elements and a minimum required count.

### Step 2 - Create Binary Variables
- Instantiate a binary decision variable for each selectable element (e.g., `x[i] ∈ {0,1}`).
- Use solver-specific methods like `solver.IntVar(0, 1, name)`.

### Step 3 - Formulate Coverage Constraints
- For each requirement, create a linear constraint: `∑_{i ∈ S} x[i] ≥ k`.
- Use the solver's constraint builder, accumulating a coefficient of 1 for each variable in the requirement set.

### Step 4 - Set Weighted Objective
- Define the objective as minimizing the weighted sum of selected variables: `min ∑ cost[i] * x[i]`.
- Set coefficients and minimization sense via the solver's objective object.

### Formulation Template
```json
{
  "sets": ["ELEMENTS", "REQUIREMENTS"],
  "parameters": [
    {"name": "cost", "index": "ELEMENTS", "type": "float"},
    {"name": "requirement_set", "index": "REQUIREMENTS", "type": "set"},
    {"name": "min_required", "index": "REQUIREMENTS", "type": "int"}
  ],
  "decision_variables": [
    {"name": "x", "index": "ELEMENTS", "domain": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in ELEMENTS)"
  },
  "constraints": [
    {"name": "coverage", "index": "REQUIREMENTS", "expression": "sum(x[i] for i in requirement_set[r]) >= min_required[r]"}
  ]
}
```

### Common Pitfalls
- Using dense matrices for sparse coverage relationships, wasting memory and slowing constraint generation.
- Forgetting to handle floating-point tolerances when extracting binary variable values (e.g., using `> 0.5`).
- Neglecting to set solver time limits or thread counts for larger problem instances.

## Solving stage

### Strategy Overview
Solve the constructed model using a Mixed-Integer Programming (MIP) solver backend, configure it for performance, and implement robust solution extraction and verification.

### Step 1 - Configure Solver
- Select an appropriate MIP solver (e.g., `SCIP`, `CBC`).
- Set practical limits: time limit (`SetTimeLimit`), optimality gap (`SetDoubleParam`), and thread count (`SetNumThreads`).

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the returned status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`) before proceeding.

### Step 3 - Extract and Verify Solution
- Extract selected elements by filtering variables where `solution_value() > 0.5`.
- Compute the total cost from the objective value.
- Programmatically verify all coverage constraints are satisfied by the selected set.

### Step 4 - Prove Optimality (Optional)
- To confirm optimality, add a new constraint forcing the objective value below the incumbent (e.g., `∑ cost[i]*x[i] ≤ incumbent - epsilon`).
- Re-solve; infeasibility proves no better solution exists.

### Code Usage
```python
# Example using OR-Tools
from ortools.linear_solver import pywraplp

# 1. Data preparation (placeholders)
elements = [...]  # list of element IDs
cost = {...}  # dict: element_id -> cost
requirements = [...]  # list of tuples: (set_of_elements, min_required)

# 2. Solver setup
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)  # 30 seconds
solver.SetNumThreads(4)

# 3. Variable creation
x = {i: solver.IntVar(0, 1, f"x_{i}") for i in elements}

# 4. Constraint addition
for idx, (req_set, min_req) in enumerate(requirements, 1):
    constraint = solver.Constraint(min_req, solver.infinity(), f"req_{idx}")
    for i in req_set:
        constraint.SetCoefficient(x[i], 1)

# 5. Objective setup
objective = solver.Objective()
for i in elements:
    objective.SetCoefficient(x[i], cost[i])
objective.SetMinimization()

# 6. Solve and extract
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [i for i in elements if x[i].solution_value() > 0.5]
    total_cost = objective.Value()
    # Add verification logic here
else:
    # Handle infeasible or error status
    selected = []
    total_cost = None
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; check termination conditions explicitly.
- Not handling solver errors or time-out scenarios gracefully.
- Omitting solution verification, which can mask modeling errors.

# Workflow 2 (Algebraic Modeling with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses an algebraic modeling language (Pyomo) to declaratively define sets, parameters, variables, and constraints, promoting model clarity, maintainability, and solver portability.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for indices (e.g., `model.ELEMENTS`, `model.REQUIREMENTS`).
- Declare `Param` objects for cost data and coverage requirements, indexed appropriately.

### Step 2 - Declare Binary Decision Variables
- Create a `Var` object with domain `pyo.Binary`, indexed by the element set.

### Step 3 - Formulate Constraints via Rules
- Define a constraint rule function that, for each requirement, sums the variables of covering elements.
- Use the rule to instantiate a `Constraint` object indexed by the requirement set.

### Step 4 - Define Objective Expression
- Create an `Objective` object with the expression `sum(cost[i] * model.x[i] for i in model.ELEMENTS)` and sense `minimize`.

### Formulation Template
```json
{
  "sets": ["ELEMENTS", "REQUIREMENTS"],
  "parameters": [
    {"name": "cost", "index": "ELEMENTS", "type": "float"},
    {"name": "covering_elements", "index": "REQUIREMENTS", "type": "set"},
    {"name": "min_required", "index": "REQUIREMENTS", "type": "int"}
  ],
  "decision_variables": [
    {"name": "x", "index": "ELEMENTS", "domain": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in ELEMENTS)"
  },
  "constraints": [
    {"name": "coverage", "index": "REQUIREMENTS", "expression": "sum(x[i] for i in covering_elements[r]) >= min_required[r]"}
  ]
}
```

### Common Pitfalls
- Mixing data preparation logic within Pyomo rule functions, reducing readability.
- Using inefficient data structures (like lists) for large, sparse coverage lookups within rules.
- Forgetting to deactivate the `tee` flag in production to avoid excessive solver output.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver factory, handle solution loading carefully, and implement a post-solve verification and result packaging pipeline.

### Step 1 - Instantiate and Configure Solver
- Use `SolverFactory` to create a solver instance (e.g., `"cbc"`, `"highs"`).
- Set options: time limit (`seconds`), optimality gap tolerance (`ratio`), thread count (`threads`).

### Step 2 - Solve with Status Checks
- Call `solver.solve(model, ...)` with appropriate arguments.
- Check `results.solver.status` and `results.solver.termination_condition` before loading the solution.

### Step 3 - Load Solution and Extract Results
- If status is ok, load values into the model using `model.solutions.load_from(results)`.
- Extract selected elements by filtering variables where `pyo.value(var) > 0.5`.
- Compute the objective value via `pyo.value(model.obj)`.

### Step 4 - Verify and Package Output
- Re-compute coverage for each requirement using the selected elements to validate feasibility.
- Package results (status, objective value, selected list, verification flag) into a structured format like JSON.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Define data structures (placeholders)
cost_dict = {...}  # element_id -> cost
covering_elements = {...}  # requirement_id -> set of element IDs
min_required_dict = {...}  # requirement_id -> minimum count

# 2. Build Pyomo ConcreteModel
model = pyo.ConcreteModel()
model.ELEMENTS = pyo.Set(initialize=cost_dict.keys())
model.REQUIREMENTS = pyo.Set(initialize=min_required_dict.keys())

model.cost = pyo.Param(model.ELEMENTS, initialize=cost_dict)
model.covering_elements = pyo.Param(model.REQUIREMENTS, initialize=covering_elements, within=pyo.Any)
model.min_required = pyo.Param(model.REQUIREMENTS, initialize=min_required_dict)

model.x = pyo.Var(model.ELEMENTS, domain=pyo.Binary)

def obj_rule(m):
    return sum(m.cost[i] * m.x[i] for i in m.ELEMENTS)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def coverage_rule(m, r):
    return sum(m.x[i] for i in m.covering_elements[r]) >= m.min_required[r]
model.coverage = pyo.Constraint(model.REQUIREMENTS, rule=coverage_rule)

# 3. Solve
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False)

# 4. Check status and extract
if results.solver.status == SolverStatus.ok:
    if results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible):
        # Load solution explicitly
        model.solutions.load_from(results)
        selected = [i for i in model.ELEMENTS if pyo.value(model.x[i]) > 0.5]
        total_cost = pyo.value(model.obj)
        # Add verification logic here
    else:
        # Handle suboptimal or stopped solves
        selected = []
        total_cost = None
else:
    # Handle solver error
    selected = []
    total_cost = None
```

### Common Pitfalls
- Not using `load_solutions=False` and explicit loading when using solvers like HiGHS, leading to `NoFeasibleSolutionError`.
- Assuming the solver's `optimal` status is always returned; check for `feasible` as well.
- Neglecting to verify constraint satisfaction post-solve, which is crucial for catching modeling or solver tolerance issues.
