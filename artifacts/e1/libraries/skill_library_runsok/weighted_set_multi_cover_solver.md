---
name: Weighted Set Multi-Cover Solver
description: |
  Solve weighted set covering problems with multiplicity (coverage requirements ≥1) using binary assignment variables and coverage constraints, minimizing total cost via MILP solvers.

---
# Workflow 1 (OR-Tools / SCIP Backend)

## Modeling stage

### Strategy Overview
Model the problem as a binary integer program using the OR-Tools linear solver wrapper. The structure emphasizes direct variable creation, constraint addition via sums over eligibility lists, and explicit objective coefficient setting.

### Step 1 - Define Data Structures
- Map problem elements to dictionaries for efficient access: `cost[i]` for item cost, `coverage_req[j]` for requirement per demand point, `eligible[j]` for list of covering items.
- Use consistent indexing (e.g., item IDs, location IDs) to link data to decision variables.

### Step 2 - Create Binary Decision Variables
- Instantiate a solver object (e.g., `pywraplp.Solver`).
- Create a dictionary of binary variables `x[i] = solver.IntVar(0, 1, f"x_{i}")` for each item `i`.

### Step 3 - Formulate Coverage Constraints
- For each demand point `j`, add a constraint: `solver.Add(sum(x[i] for i in eligible[j]) >= coverage_req[j], f"cover_{j}")`.
- Naming constraints aids in debugging and output interpretation.

### Step 4 - Set Weighted Minimization Objective
- Initialize the objective: `objective = solver.Objective()`.
- For each item `i`, set its coefficient: `objective.SetCoefficient(x[i], cost[i])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "I: set of items (e.g., teams, facilities)",
    "J: set of demand points (e.g., locations, tasks)"
  ],
  "parameters": [
    "cost[i ∈ I]: selection cost of item i",
    "coverage_req[j ∈ J]: minimum number of covering items required at j",
    "eligible[j ∈ J]: list of item indices i ∈ I that can cover j"
  ],
  "decision_variables": [
    "x[i ∈ I]: binary, 1 if item i is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(x[i] for i in eligible[j]) >= coverage_req[j] for all j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to name variables or constraints, making debug output cryptic.
- Using floating-point equality checks on binary solution values; use a tolerance (e.g., `> 0.5`).
- Not verifying that `eligible[j]` lists are non-empty for all `j` with `coverage_req[j] > 0`.

## Solving stage

### Strategy Overview
Solve the MILP model using the SCIP or CBC backend via OR-Tools. Configure solver limits, check termination status rigorously, extract the solution, and validate constraint satisfaction.

### Step 1 - Configure Solver and Solve
- Create solver: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set reasonable limits: `solver.SetTimeLimit(30000)`, `solver.SetNumThreads(4)`.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Check Solution Status
- Verify `status` is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`.
- If status is not feasible, handle infeasibility (e.g., analyze conflict, relax constraints).

### Step 3 - Extract and Validate Solution
- For each item `i`, check `x[i].solution_value() > 0.5` to determine selection.
- Compute actual coverage per demand point: `sum(x[i].solution_value() for i in eligible[j])`.
- Validate against `coverage_req[j]`; log any shortfalls.

### Step 4 - Verify Optimality (Optional)
- To prove optimality, add a constraint: `sum(cost[i] * x[i]) <= incumbent_value - epsilon`.
- Re-solve; infeasibility confirms no better solution exists.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Define variables, constraints, objective as per Modeling stage
# ...

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    selected_items = [i for i in I if x[i].solution_value() > 0.5]
    # Validation loop
    for j in J:
        covered = sum(x[i].solution_value() for i in eligible[j])
        assert covered >= coverage_req[j] - 1e-6, f"Coverage failed for {j}"
else:
    # Handle infeasibility or other statuses
    print("No feasible solution found")
```

### Common Pitfalls
- Not setting a time limit, risking long runs on large instances.
- Misinterpreting `FEASIBLE` as optimal; report status clearly.
- Omitting solution validation, which can miss numerical tolerance issues.

# Workflow 2 (Pyomo / CBC Backend)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract modeling capabilities. Define sets, parameters, variables, and constraints via rule functions, promoting separation of model structure from data.

### Step 1 - Define Pyomo Sets and Parameters
- Create `ConcreteModel()`.
- Define `model.I = pyo.Set(initialize=items)` and `model.J = pyo.Set(initialize=demand_points)`.
- Create `model.cost = pyo.Param(model.I, initialize=cost_dict)`, `model.req = pyo.Param(model.J, initialize=req_dict)`.
- Store eligibility as a parameter or external dictionary `eligible_teams[j]`.

### Step 2 - Declare Binary Variables
- Create `model.x = pyo.Var(model.I, domain=pyo.Binary)`.

### Step 3 - Formulate Objective
- Define minimization objective: `model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)`.

### Step 4 - Implement Coverage Constraints via Rule
- Define a rule function `def coverage_rule(model, j): return sum(model.x[i] for i in eligible_teams[j]) >= model.req[j]`.
- Create `model.coverage = pyo.Constraint(model.J, rule=coverage_rule)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "J: set of demand points"
  ],
  "parameters": [
    "cost[i ∈ I]: cost parameter",
    "req[j ∈ J]: coverage requirement parameter",
    "eligible[j ∈ J]: external list of covering items for j"
  ],
  "decision_variables": [
    "x[i ∈ I]: binary variable"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(x[i] for i in eligible[j]) >= req[j] for all j in J"
  ]
}
```

### Common Pitfalls
- Using mutable default arguments in constraint rule functions; define rules with explicit parameters.
- Confusing Pyomo `Param` with Python dictionaries; ensure parameters are initialized before model instantiation.
- Not indexing `eligible_teams` correctly within the rule; verify it accepts `j` as a key.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via `SolverFactory`. Configure solver options, handle solution loading carefully, and perform post-solve validation.

### Step 1 - Configure and Execute Solver
- Instantiate solver: `solver = pyo.SolverFactory("cbc")`.
- Set options: `solver.options["seconds"] = 30`, `solver.options["ratio"] = 0.0`, `solver.options["threads"] = 4`.
- Solve with `load_solutions=False`: `results = solver.solve(model, load_solutions=False)`.

### Step 2 - Check Termination Condition
- Inspect `results.solver.termination_condition` (e.g., `optimal`, `feasible`, `infeasible`).
- If optimal or feasible, load solution: `model.solutions.load_from(results)`.

### Step 3 - Extract Solution and Validate
- Retrieve objective value: `pyo.value(model.obj)`.
- Determine selected items: `[i for i in model.I if pyo.value(model.x[i]) > 0.5]`.
- Compute actual coverage per `j` and compare to `model.req[j]`; assert satisfaction.

### Step 4 - Optional Optimality Proof
- Add a cut: `model.obj_cut = pyo.Constraint(expr=sum(model.cost[i] * model.x[i] for i in model.I) <= incumbent - 1e-6)`.
- Re-solve; infeasibility confirms optimality.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=demand_points)
model.cost = pyo.Param(model.I, initialize=cost_dict)
model.req = pyo.Param(model.J, initialize=req_dict)
model.x = pyo.Var(model.I, domain=pyo.Binary)
model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)
def coverage_rule(m, j):
    return sum(m.x[i] for i in eligible_teams[j]) >= m.req[j]
model.coverage = pyo.Constraint(model.J, rule=coverage_rule)

# solve with status / termination checks
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
results = solver.solve(model, load_solutions=False)

if results.solver.termination_condition in ("optimal", "feasible"):
    model.solutions.load_from(results)
    objective_value = pyo.value(model.obj)
    # Validation loop
    for j in model.J:
        covered = sum(pyo.value(model.x[i]) for i in eligible_teams[j])
        assert covered >= pyo.value(model.req[j]) - 1e-6
else:
    print(f"Solver terminated: {results.solver.termination_condition}")
```

### Common Pitfalls
- Forgetting `load_solutions=False` and then trying to access variable values before loading.
- Not checking `termination_condition`; assuming `optimal` always.
- Using `pyo.value` on variables before solution loading, causing errors.
