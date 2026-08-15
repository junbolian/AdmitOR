---
name: Weighted Set Cover Solver
description: |
  Model and solve weighted set cover problems using binary selection variables, coverage constraints, and cost minimization via MILP or CP-SAT solvers.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem as a concrete Pyomo model using binary variables for selection, coverage constraints for each requirement, and a linear objective for cost minimization. This approach is portable across open-source solvers.

### Step 1 - Define Sets and Parameters
- Map the problem elements into indexed sets for items (e.g., facilities) and requirements (e.g., areas to cover).
- Store costs as a parameter dictionary indexed by item IDs.
- Represent coverage relationships as a dictionary mapping each requirement index to a list of covering item indices.

### Step 2 - Declare Decision Variables
- Create a binary decision variable for each item, e.g., `model.x[i] ∈ {0,1}`.
- Use `pyo.Var(model.items, domain=pyo.Binary)` for variable definition.

### Step 3 - Formulate Coverage Constraints
- For each requirement, add a constraint ensuring the sum of covering variables is at least 1.
- Implement via a Pyomo Constraint rule: `sum(model.x[j] for j in coverage_sets[req]) >= 1`.

### Step 4 - Define Weighted Objective
- Formulate the objective as the minimization of the weighted sum of selected items.
- Use `pyo.Objective(expr=sum(costs[i] * model.x[i] for i in model.items), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "items: indices of selectable items",
    "requirements: indices of elements that must be covered"
  ],
  "parameters": [
    "costs[item]: selection cost for each item",
    "coverage_sets[requirement]: list of item indices that cover this requirement"
  ],
  "decision_variables": [
    "x[item]: binary, 1 if item is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(costs[i] * x[i] for i in items)"
  },
  "constraints": [
    "cover[requirement]: sum(x[j] for j in coverage_sets[requirement]) >= 1, for all requirement"
  ]
}
```

### Common Pitfalls
- Using inefficient data structures (e.g., full matrix) for sparse coverage relationships; prefer dictionary-of-lists.
- Inconsistent 0-based vs 1-based indexing between problem data and model indices.
- Forgetting to verify the model's logical correctness with a small, verifiable instance.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source MILP solver (HiGHS or CBC) with configured time limits and optimality gaps. Extract and verify the solution.

### Step 1 - Configure and Run Solver
- Instantiate the solver via `pyo.SolverFactory("highs")` or `pyo.SolverFactory("cbc")`.
- Set key options: `time_limit`, `mip_rel_gap=0.0` for exact optimality, `threads` for parallelism.
- Execute `solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Inspect `results.solver.status` for `SolverStatus.ok`.
- Inspect `results.solver.termination_condition` for `TerminationCondition.optimal` (or `.feasible`).
- If status is not ok or termination is not optimal/feasible, handle as a failure.

### Step 3 - Extract Solution
- Retrieve selected items by filtering variables with value > 0.5: `[i for i in model.items if pyo.value(model.x[i]) > 0.5]`.
- Obtain objective value via `pyo.value(model.obj)`.

### Step 4 - Verify Coverage
- Independently verify that all requirements are covered by the selected items using the original `coverage_sets` data.
- This catches potential formulation or solver precision errors.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
def build_set_cover_model(costs, coverage_sets):
    model = pyo.ConcreteModel()
    model.items = pyo.Set(initialize=range(len(costs)))
    model.requirements = pyo.Set(initialize=range(len(coverage_sets)))
    model.x = pyo.Var(model.items, domain=pyo.Binary)
    model.obj = pyo.Objective(
        expr=sum(costs[i] * model.x[i] for i in model.items),
        sense=pyo.minimize
    )
    def cover_rule(m, r):
        return sum(m.x[j] for j in coverage_sets[r]) >= 1
    model.cover = pyo.Constraint(model.requirements, rule=cover_rule)
    return model

# Solve with status / termination checks
def solve_and_verify(model, coverage_sets):
    solver = pyo.SolverFactory("highs")
    solver.options["time_limit"] = 30
    solver.options["mip_rel_gap"] = 0.0
    results = solver.solve(model, tee=False)

    # Status checking
    if (results.solver.status == pyo.SolverStatus.ok and
        results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                                 pyo.TerminationCondition.feasible]):
        selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
        obj_val = pyo.value(model.obj)
        # Verification
        all_covered = all(
            any(j in selected for j in coverage_sets[r])
            for r in model.requirements
        )
        return obj_val, selected, all_covered
    else:
        # Handle failure
        return None
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to misinterpretation of suboptimal or failed runs.
- Using a loose optimality gap (`mip_rel_gap > 0`) when an exact optimum is required.
- Omitting the post-solve verification step, which can mask modeling errors.

# Workflow 2 (OR-Tools CP-SAT / MILP)

## Modeling stage

### Strategy Overview
Model the problem directly using OR-Tools' CP-SAT or MILP interface, creating binary variables and linear constraints. This workflow is suited for performance and integration with Google's solver technologies.

### Step 1 - Initialize Solver and Data Structures
- Choose solver backend: `"CP-SAT"` for constraint programming or `"SCIP"/"CBC"` for MILP.
- Maintain lists for costs and a dictionary mapping each requirement to its list of covering item indices.

### Step 2 - Create Binary Variables
- For each item, create a binary variable: `solver.BoolVar(f"x_{i}")` (CP-SAT) or `solver.IntVar(0, 1, f"x_{i}")` (MILP).
- Store variables in a list for indexed access.

### Step 3 - Add Coverage Constraints
- For each requirement, create a linear constraint: `sum(covering_variables) >= 1`.
- Use `solver.Add(sum(vars) >= 1)` for CP-SAT or `constraint.SetCoefficient(var, 1)` for MILP.

### Step 4 - Set Weighted Minimization Objective
- Define the objective as the sum of `cost[i] * variable[i]`.
- For CP-SAT: `solver.Minimize(sum(cost[i] * variable[i] for i in items))`.
- For MILP: populate an `Objective` object and call `SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "items: indices of selectable items",
    "requirements: indices of elements that must be covered"
  ],
  "parameters": [
    "costs[item]: selection cost for each item",
    "coverage[requirement]: list of item indices that cover this requirement"
  ],
  "decision_variables": [
    "x[item]: binary, 1 if item is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(costs[i] * x[i] for i in items)"
  },
  "constraints": [
    "cover[requirement]: sum(x[j] for j in coverage[requirement]) >= 1, for all requirement"
  ]
}
```

### Common Pitfalls
- Mixing CP-SAT and MILP API patterns (e.g., using `SetCoefficient` in a CP-SAT model).
- Incorrectly handling 0-based vs 1-based indices when mapping external data to solver variables.
- Neglecting to set solver parameters (time limit, threads) for performance control.

## Solving stage

### Strategy Overview
Solve the model with configured time limits and parallelism. Leverage solver-specific status codes to confirm optimality and extract the solution for verification.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.SetTimeLimit(seconds_in_milliseconds)` for MILP or `parameters.max_time_in_seconds` for CP-SAT.
- Enable parallel search: `solver.SetNumThreads(num)` for MILP or `parameters.num_search_workers` for CP-SAT.
- For exact solutions, set relative gap to zero (MILP) or enable logging for progress insight.

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve()` (MILP) or `solver.Solve(model, parameters)` (CP-SAT).
- Check status: `pywraplp.Solver.OPTIMAL` or `cp_model.OPTIMAL` for proven optimum; `FEASIBLE` for a feasible solution.

### Step 3 - Extract Selected Items
- For each variable, check if its solution value is > 0.5 (accounting for floating-point tolerance).
- Collect indices of selected items into a list.

### Step 4 - Verify Coverage and Report
- Using the original coverage data, verify every requirement is covered by at least one selected item.
- Compute the total cost from the objective value or by summing costs of selected items.

### Code Usage
```python
# Example using OR-Tools CP-SAT
from ortools.sat.python import cp_model

def solve_set_cover_cp_sat(costs, coverage_dict):
    model = cp_model.CpModel()
    num_items = len(costs)
    # Create variables
    x = [model.NewBoolVar(f"x_{i}") for i in range(num_items)]
    # Coverage constraints
    for req_idx, covering_items in coverage_dict.items():
        model.Add(sum(x[item_idx] for item_idx in covering_items) >= 1)
    # Objective
    model.Minimize(sum(costs[i] * x[i] for i in range(num_items)))
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 4
    status = solver.Solve(model)
    # Process results
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        selected = [i for i in range(num_items) if solver.Value(x[i])]
        obj_val = solver.ObjectiveValue()
        # Verification
        all_covered = all(
            any(item_idx in selected for item_idx in covering_items)
            for covering_items in coverage_dict.values()
        )
        return obj_val, selected, all_covered
    else:
        return None

# Example using OR-Tools MILP (SCIP/CBC)
from ortools.linear_solver import pywraplp

def solve_set_cover_milp(costs, coverage_dict):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    solver.SetTimeLimit(30000)  # milliseconds
    solver.SetNumThreads(4)
    num_items = len(costs)
    # Create variables
    x = [solver.IntVar(0, 1, f"x_{i}") for i in range(num_items)]
    # Coverage constraints
    for req_idx, covering_items in coverage_dict.items():
        constraint = solver.Constraint(1, solver.infinity())
        for item_idx in covering_items:
            constraint.SetCoefficient(x[item_idx], 1)
    # Objective
    objective = solver.Objective()
    for i in range(num_items):
        objective.SetCoefficient(x[i], costs[i])
    objective.SetMinimization()
    # Solve
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        selected = [i for i in range(num_items) if x[i].solution_value() > 0.5]
        obj_val = objective.Value()
        # Verification (same as above)
        all_covered = all(
            any(item_idx in selected for item_idx in covering_items)
            for covering_items in coverage_dict.values()
        )
        return obj_val, selected, all_covered
    else:
        return None
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; it only confirms a feasible solution was found.
- Not accounting for floating-point precision when checking binary variable values (use > 0.5 threshold).
- Failing to verify coverage after solving, which is critical for catching indexing errors in constraint construction.
