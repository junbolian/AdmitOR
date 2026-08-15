---
name: Weighted Set Cover Solver
description: |
  Model and solve weighted set cover problems with binary selection variables, coverage constraints, and cost minimization using MILP solvers.
---

# Workflow 1 (OR-Tools MIP Backend)

## Modeling stage

### Strategy Overview
This workflow models the weighted set cover problem using the OR-Tools linear solver (pywraplp) interface, creating a MIP with binary variables and linear constraints for direct solving with SCIP or CBC.

### Step 1 - Define Selection Items and Coverage Mapping
- Identify the set of selectable items (e.g., facilities, hubs) and the set of elements (e.g., routes, zones) that require coverage.
- Construct a sparse coverage mapping: a dictionary where each element key maps to a list of item indices that can cover it.
- Define a cost parameter list, indexed by item, for the objective function.

### Step 2 - Create Binary Decision Variables
- Instantiate a solver object (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Create a list of binary decision variables, one for each selectable item, using `solver.IntVar(0, 1, name)`.

### Step 3 - Formulate Coverage Constraints
- For each element in the coverage mapping, create a linear constraint: `solver.Constraint(1, solver.infinity())`.
- For each covering item for that element, add its binary variable to the constraint with a coefficient of 1 using `constraint.SetCoefficient(x[i], 1)`.

### Step 4 - Set Weighted Minimization Objective
- Create the objective expression: `solver.Objective()`.
- For each item, add its cost coefficient to the corresponding binary variable using `objective.SetCoefficient(x[i], cost[i])`.
- Set the objective sense to minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "I: set of selectable items (index i)",
    "J: set of elements requiring coverage (index j)"
  ],
  "parameters": [
    "cost_i: cost of selecting item i",
    "cover_j: list of item indices i that can cover element j"
  ],
  "decision_variables": [
    "x_i ∈ {0,1}: binary selection variable for item i"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_i * x_i for i in I)"
  },
  "constraints": [
    "sum(x_i for i in cover_j) >= 1, for all j in J"
  ]
}
```

### Common Pitfalls
- Using dense matrices for coverage when the relationship is sparse, leading to unnecessary memory overhead.
- Forgetting to set the objective sense to minimization, which defaults to maximization.
- Creating constraints with incorrect bounds (e.g., using `0` instead of `1` as the lower bound for coverage).

## Solving stage

### Strategy Overview
Solve the formulated MIP using the OR-Tools wrapper, configure solver parameters for performance, extract the solution, and rigorously verify coverage and optimality.

### Step 1 - Configure Solver and Execute
- Set a time limit (e.g., `solver.SetTimeLimit(30000)` for 30 seconds) and number of threads (`solver.SetNumThreads(4)`) for performance control.
- Call `solver.Solve()` and capture the returned status code.

### Step 2 - Check Solver Status and Extract Solution
- Check if the status is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`.
- If acceptable, extract selected items by checking `x[i].solution_value() > 0.5` for each binary variable.
- Compute the total cost from the selected items and the cost parameters.

### Step 3 - Verify Solution Feasibility
- Programmatically verify that every element is covered by at least one selected item using the original coverage mapping.
- If any element is uncovered, log an error and treat the solution as invalid.

### Step 4 - Confirm Optimality (Optional)
- To confirm a solution is optimal, add a new constraint forcing the total cost to be less than the found cost (e.g., `sum(cost_i * x_i) <= found_cost - 1`).
- Re-solve the model; if it becomes infeasible, the original solution is optimal.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... [variable and constraint creation as per modeling steps] ...
objective = solver.Objective()
for i in range(num_items):
    objective.SetCoefficient(x[i], costs[i])
objective.SetMinimization()

# solve with status / termination checks
solver.SetTimeLimit(30000)
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [i for i in range(num_items) if x[i].solution_value() > 0.5]
    total_cost = sum(costs[i] for i in selected)
    # ... [verification steps] ...
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially rejecting valid solutions.
- Using a loose threshold (e.g., `> 0`) instead of `> 0.5` for extracting binary variable values due to solver tolerances.
- Omitting the feasibility verification step, which can miss modeling or solution loading errors.

# Workflow 2 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow models the problem using Pyomo's abstract modeling capabilities, defining sets, parameters, variables, and constraints declaratively, then solves it using an open-source MILP solver like CBC or HiGHS via SolverFactory.

### Step 1 - Define Pyomo Sets and Parameters
- Create Pyomo `Set` objects for the selection items (`model.I`) and coverage elements (`model.J`).
- Define a `Param` `model.cost`, indexed by `model.I`, to store item costs.
- Store coverage relationships in a Python dictionary (`cover_data`) mapping element `j` to a list of covering items `i`.

### Step 2 - Declare Binary Variables and Objective
- Declare binary decision variables `model.x` indexed by `model.I` with `domain=pyo.Binary`.
- Define the objective as a `pyo.Objective` with expression `sum(model.cost[i] * model.x[i] for i in model.I)` and `sense=pyo.minimize`.

### Step 3 - Implement Coverage Constraints via Rule
- Define a constraint rule function that, for a given element `j`, returns the expression `sum(model.x[i] for i in cover_data[j]) >= 1`.
- Create a Pyomo `Constraint` indexed by `model.J` using this rule.

### Formulation Template
```json
{
  "sets": [
    "I: Pyomo Set of selectable items",
    "J: Pyomo Set of elements requiring coverage"
  ],
  "parameters": [
    "cost: Pyomo Param indexed by I for selection costs",
    "cover_data: Python dict mapping j in J to list of i in I"
  ],
  "decision_variables": [
    "x: Pyomo Var indexed by I, domain=Binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "Coverage: sum(x[i] for i in cover_data[j]) >= 1, for all j in J"
  ]
}
```

### Common Pitfalls
- Defining constraint rules that rely on external global variables instead of model parameters, causing scoping issues.
- Using dense `cover_data` (e.g., a full matrix) within Pyomo rules, which can slow down model construction.
- Forgetting to initialize all Pyomo `Param` values, leading to runtime errors.

## Solving stage

### Strategy Overview
Instantiate a solver via Pyomo's SolverFactory, configure it with time limits and optimality gaps, solve the model, carefully check termination conditions, and load/verify the solution.

### Step 1 - Instantiate and Configure Solver
- Create a solver object: `solver = pyo.SolverFactory("cbc")`.
- Set key options: time limit (`solver.options['seconds'] = 30`), optimality gap (`solver.options['ratio'] = 0.0` for proven optimality), and threads (`solver.options['threads'] = 4`).

### Step 2 - Solve and Check Termination Status
- Execute `results = solver.solve(model, tee=False)`.
- Check both the solver status (`results.solver.status == pyo.SolverStatus.ok`) and the termination condition (`results.solver.termination_condition`).
- Accept solutions where termination condition is `pyo.TerminationCondition.optimal` or `pyo.TerminationCondition.feasible`.

### Step 3 - Load Solution and Extract Values
- If using `load_solutions=False`, manually load the solution: `model.solutions.load_from(results)`.
- Extract selected items: `selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]`.
- Compute total cost from the objective value or by summing costs of selected items.

### Step 4 - Independent Feasibility Verification
- Using the original `cover_data`, verify that for every element `j`, at least one item in `cover_data[j]` is in the `selected` list.
- This step catches potential discrepancies between the model and the solution.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=elements)
model.cost = pyo.Param(model.I, initialize=cost_dict)
model.x = pyo.Var(model.I, domain=pyo.Binary)
model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)
def coverage_rule(m, j):
    return sum(m.x[i] for i in cover_data[j]) >= 1
model.coverage = pyo.Constraint(model.J, rule=coverage_rule)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options['seconds'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    # ... [verification steps] ...
else:
    print("Solver failed to find an acceptable solution.")
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`), leading to acceptance of failed solves.
- Not using `pyo.value()` to extract variable values, which returns the underlying object instead of the numeric solution.
- Setting overly restrictive solver options (e.g., `ratio=0.0` on large instances) causing excessive solve times without a fallback.
