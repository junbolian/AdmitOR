---
name: Set Cover Optimization
description: |
  Model and solve binary selection problems with coverage requirements using integer programming to minimize total cost.

---

# Workflow 1 (OR-Tools MIP)

## Modeling stage

### Strategy Overview
Formulate the set cover problem as a binary integer program using the OR-Tools linear solver wrapper, focusing on a procedural, variable-by-variable and constraint-by-constraint building pattern.

### Step 1 - Map Problem Elements
- Identify the two core sets: the set of selectable items (e.g., facilities, locations) and the set of elements to be covered (e.g., zones, requirements).
- Define the coverage relationship as a dictionary mapping each element to a list of items that can cover it.
- Collect the cost parameter for each selectable item.

### Step 2 - Define Decision Variables
- Create a list of binary decision variables, one for each selectable item. Use `solver.IntVar(0, 1, name)`.
- Use consistent indexing between variables, costs, and coverage data.

### Step 3 - Formulate Coverage Constraints
- For each element in the coverage dictionary, create a linear constraint.
- Set the lower bound of the constraint to 1 (ensuring at least one covering item is selected).
- For each item in the element's covering list, add that item's decision variable with a coefficient of 1 to the constraint.

### Step 4 - Define Objective Function
- Create a linear objective expression summing the cost of each item multiplied by its binary variable.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "I: Set of elements to cover (e.g., zones)",
    "J: Set of selectable items (e.g., locations)"
  ],
  "parameters": [
    "cost_j: Cost of selecting item j ∈ J",
    "cover_i: List of items j ∈ J that cover element i ∈ I"
  ],
  "decision_variables": [
    "x_j ∈ {0, 1}: 1 if item j is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{j ∈ J} cost_j * x_j"
  },
  "constraints": [
    "Coverage: ∑_{j ∈ cover_i} x_j ≥ 1, ∀ i ∈ I"
  ]
}
```

### Common Pitfalls
- Mismatched indices between variable list and coverage dictionary, leading to incorrect constraints.
- Forgetting to set the objective sense to minimization.
- Using a loose optimality gap or no time limit for large instances, resulting in long solve times.

## Solving stage

### Strategy Overview
Solve the built model using the SCIP or CBC backend, carefully check solver status, extract the solution using a robust threshold, and verify the result.

### Step 1 - Configure and Run Solver
- Instantiate the solver (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set practical limits: `SetTimeLimit(milliseconds)` and `SetNumThreads(number)`.
- Call `solver.Solve()`.

### Step 2 - Check Solver Status
- Capture the return status of the solve call.
- Accept solutions where status is `OPTIMAL` or `FEASIBLE`. Reject `INFEASIBLE` or `UNBOUNDED`.

### Step 3 - Extract and Interpret Solution
- Iterate through decision variables. A variable is considered selected if `variable.solution_value() > 0.5`.
- Collect the indices of selected items.
- Obtain the objective value via `solver.Objective().Value()`.

### Step 4 - Verify Solution Coverage
- Using the original coverage dictionary and the list of selected items, verify that every element is covered by at least one selected item.
- This step catches modeling errors and confirms solution validity.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Build Model from Formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (Define variables, constraints, objective as per Modeling Stage)

# 2. Solve with Status / Termination Checks
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)
status = solver.Solve()

# 3. Process Results
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    selected_items = []
    for j in range(num_items):
        if x[j].solution_value() > 0.5:
            selected_items.append(j)
    total_cost = solver.Objective().Value()
    # ... (Optional verification)
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Using a naive threshold (e.g., `== 1.0`) for binary variable interpretation, which can fail due to solver tolerances.
- Not checking for `FEASIBLE` status, thereby missing good solutions when optimality isn't proven.
- Omitting solution verification, which can leave subtle modeling errors undetected.

# Workflow 2 (Pyomo with CBC/HiGHS)

## Modeling stage

### Strategy Overview
Model the set cover problem using Pyomo's abstract `ConcreteModel` pattern, leveraging sets, objectives, and constraints defined by rules for a declarative and structured approach.

### Step 1 - Define Model Sets and Parameters
- Create a Pyomo `ConcreteModel`.
- Define two `pyo.Set` objects: one for selectable items and one for elements to cover.
- Declare cost and coverage as parameters, typically using Python dictionaries indexed by the model sets.

### Step 2 - Declare Decision Variables
- Create a `pyo.Var` indexed over the set of selectable items.
- Specify the domain as `pyo.Binary`.

### Step 3 - Construct Objective Function
- Define the objective as a `pyo.Objective` using a summation expression over the set of items: `sum(cost[j] * model.x[j] for j in model.items)`.
- Set the sense to `pyo.minimize`.

### Step 4 - Implement Coverage Constraints via Rule
- Define a constraint rule function that takes the model and an element index.
- The rule returns the inequality: `sum(model.x[j] for j in coverage[element]) >= 1`.
- Create a `pyo.Constraint` indexed over the set of elements, using this rule.

### Formulation Template
```json
{
  "sets": [
    "model.I: Pyomo Set of elements to cover",
    "model.J: Pyomo Set of selectable items"
  ],
  "parameters": [
    "cost: Dict[j ∈ model.J] -> cost value",
    "coverage: Dict[i ∈ model.I] -> list of j ∈ model.J"
  ],
  "decision_variables": [
    "model.x[j]: Pyomo Binary variable for item j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[j] * model.x[j] for j in model.J)"
  },
  "constraints": [
    "model.cover_constraint[i]: sum(model.x[j] for j in coverage[i]) >= 1"
  ]
}
```

### Common Pitfalls
- Defining constraint rules that incorrectly capture the coverage mapping due to Python scope issues.
- Using `model.x` directly in a rule without ensuring the index `j` belongs to the correct covering list for element `i`.
- Not initializing Pyomo sets with the correct data, leading to empty models.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or HiGHS solver via `SolverFactory`, configure performance parameters, check termination conditions rigorously, and extract the solution.

### Step 1 - Configure Solver and Options
- Instantiate the solver: `SolverFactory("cbc")` or `SolverFactory("highs")`.
- Set key options: time limit (`seconds`), optimality gap (`ratio` for CBC, `mip_rel_gap` for HiGHS), and threads (`threads`).

### Step 2 - Execute Solve and Check Status
- Call `solver.solve(model, tee=False)`.
- Check that `results.solver.status` is `SolverStatus.ok`.
- Check that `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract Selected Items
- Use `pyo.value(model.x[j]) > 0.5` to determine if a binary variable is selected.
- Iterate over the set of items to collect indices where this condition holds.

### Step 4 - Validate and Report
- Compute the objective value via `pyo.value(model.obj)`.
- Perform coverage verification using the list of selected items and the original coverage dictionary.
- Report the solution, total cost, and verification outcome.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build Model from Formulation
model = pyo.ConcreteModel()
model.J = pyo.Set(initialize=items_list)
model.I = pyo.Set(initialize=elements_list)
model.x = pyo.Var(model.J, domain=pyo.Binary)
model.obj = pyo.Objective(expr=sum(cost[j]*model.x[j] for j in model.J), sense=pyo.minimize)
def cover_rule(m, i):
    return sum(m.x[j] for j in coverage[i]) >= 1
model.cover = pyo.Constraint(model.I, rule=cover_rule)

# 2. Solve with Status / Termination Checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    selected = [j for j in model.J if pyo.value(model.x[j]) > 0.5]
    obj_val = pyo.value(model.obj)
    # ... (Optional verification)
```

### Common Pitfalls
- Confusing `solver.status` with `termination_condition`; both must be checked for a valid solution.
- Using an invalid optimality gap value (e.g., negative for HiGHS' `mip_rel_gap`).
- Attempting to access `pyo.value` on a variable before checking solve status, which may raise an error.
