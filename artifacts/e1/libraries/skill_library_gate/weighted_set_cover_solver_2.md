---
name: Weighted Set Cover Solver
description: |
  Model and solve weighted set cover problems using binary decision variables, coverage constraints, and cost minimization objectives, with robust verification and solver-agnostic workflows.

---

# Workflow 1 (OR-Tools MIP Backend)

## Modeling stage

### Strategy Overview
This workflow models the weighted set cover problem as a Mixed-Integer Program (MIP) using Google OR-Tools' linear solver wrapper. It is designed for direct, low-level control over the solver and constraints, suitable for integration into larger systems or when fine-tuning solver parameters is required.

### Step 1 - Define Problem Data Structures
- Map the problem elements (e.g., `elements`) and covering sets (e.g., `sets`) using clear, indexable data structures.
- Create a dictionary `coverage` mapping each element to a list of set indices that cover it.
- Create a list `costs` containing the cost associated with each set.

### Step 2 - Instantiate Solver and Create Variables
- Instantiate a MIP-capable solver (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Create a list of binary decision variables `x[j]` for each set `j`, using `solver.IntVar(0, 1, name)`.

### Step 3 - Formulate Coverage Constraints
- For each element `i` in the coverage dictionary, create a linear constraint: `sum(x[j] for j in coverage[i]) >= 1`.
- Use `solver.Constraint(1, solver.infinity(), constraint_name)` and `SetCoefficient` to build the constraint.

### Step 4 - Define the Minimization Objective
- Create the objective function: `objective = sum(costs[j] * x[j] for j in all_sets)`.
- Use `solver.Objective().SetMinimization()` and set coefficients for each variable.

### Formulation Template
```json
{
  "sets": ["all_sets", "all_elements"],
  "parameters": ["costs[all_sets]", "coverage[all_elements] -> list_of_sets"],
  "decision_variables": ["x[all_sets] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(costs[j] * x[j] for j in all_sets)"
  },
  "constraints": ["sum(x[j] for j in coverage[i]) >= 1, for all i in all_elements"]
}
```

### Common Pitfalls
- Inconsistent indexing between the `coverage` dictionary and the variable list, leading to incorrect constraints.
- Forgetting to set the objective sense to minimization, defaulting to maximization.
- Using a solver backend that does not support MIP (e.g., GLOP) for this binary problem.

## Solving stage

### Strategy Overview
Solving involves configuring the OR-Tools solver, executing it, and rigorously verifying the solution's feasibility and optimality status. This stage emphasizes post-solve validation to catch potential solver errors.

### Step 1 - Configure Solver and Execute
- Set practical solver parameters like time limit (`solver.SetTimeLimit(timeout_ms)`) and number of threads.
- Call `solver.Solve()` to initiate the optimization.

### Step 2 - Check Solver Status and Extract Solution
- Check the result status: `solver.ResultStatus()` for `OPTIMAL` or `FEASIBLE`.
- If successful, extract selected sets where `x[j].solution_value() > 0.5`.
- Retrieve the objective value via `solver.Objective().Value()`.

### Step 3 - Perform Manual Feasibility Verification
- For each element, verify that at least one selected set (from the coverage list) is active.
- This guards against potential numerical tolerances or solver errors.

### Step 4 - Handle Non-Optimal Outcomes
- For `INFEASIBLE` status, analyze the model for data errors (e.g., an element with empty coverage list).
- For timeouts or other limits, report the best feasible solution found, if any.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (variable, constraint, objective creation as per modeling stage)

# solve with status / termination checks
solver.SetTimeLimit(time_limit_ms)
result_status = solver.Solve()

if result_status in [solver.OPTIMAL, solver.FEASIBLE]:
    selected = [j for j in all_sets if x[j].solution_value() > 0.5]
    total_cost = solver.Objective().Value()
    # Perform manual verification
    for element in all_elements:
        if not any(x[j].solution_value() > 0.5 for j in coverage[element]):
            raise AssertionError(f"Coverage failed for element {element}")
    print(f"Solution found. Cost: {total_cost}")
else:
    print(f"Solver failed with status: {result_status}")
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; always check for `OPTIMAL` if proof is required.
- Not using a tolerance (e.g., `> 0.5`) when checking binary variable values due to floating-point arithmetic.
- Ignoring solver status and attempting to extract a solution from a failed solve, causing runtime errors.

# Workflow 2 (Pyomo with High-Level Solver Factory)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to create a clean, declarative model of the set cover problem. It separates problem data from model logic, facilitating easy modification and integration with various solvers via the SolverFactory interface.

### Step 1 - Define Abstract Sets and Parameters
- Use `pyo.Set` to define index sets for `Sets` and `Elements`.
- Use `pyo.Param` to define the `cost` for each set and the `coverage` relationship, potentially using a sparse binary parameter.

### Step 2 - Declare Decision Variables and Objective
- Declare binary variables `model.x` indexed by `model.Sets` using `pyo.Var(domain=pyo.Binary)`.
- Define the objective as `model.obj = pyo.Objective(expr=sum(model.cost[j] * model.x[j] for j in model.Sets), sense=pyo.minimize)`.

### Step 3 - Build Coverage Constraints Declaratively
- Create a constraint rule `def coverage_rule(model, i)` that returns `sum(model.x[j] for j in model.Sets if model.coverage[i, j] == 1) >= 1`.
- Use `pyo.Constraint(model.Elements, rule=coverage_rule)` to instantiate all constraints.

### Formulation Template
```json
{
  "sets": ["Sets", "Elements"],
  "parameters": ["cost[Sets]", "coverage[Elements, Sets] ∈ {0,1}"],
  "decision_variables": ["x[Sets] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[j] * x[j] for j in Sets)"
  },
  "constraints": ["sum(x[j] for j in Sets where coverage[i,j]==1) >= 1, for all i in Elements"]
}
```

### Common Pitfalls
- Defining the `coverage` parameter as a dense matrix for large, sparse problems, causing memory issues.
- Incorrectly indexing parameters within constraint rules, leading to `KeyError`.
- Mixing Pyomo's `ConcreteModel` and `AbstractModel` paradigms inconsistently within the same script.

## Solving stage

### Strategy Overview
Solving leverages Pyomo's `SolverFactory` to connect to a backend solver (e.g., CBC, HiGHS). The focus is on checking both the high-level solver status and the detailed termination condition, followed by solution validation.

### Step 1 - Instantiate Solver and Set Options
- Instantiate the solver: `solver = pyo.SolverFactory("highs")`.
- Configure options such as `time_limit`, `threads`, and `mip_rel_gap` (set to `0.0` for optimality).

### Step 2 - Solve and Inspect Results Object
- Execute `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Extract and Validate Solution
- Extract selected sets: `[j for j in model.Sets if pyo.value(model.x[j]) > 0.5]`.
- Retrieve the objective value: `pyo.value(model.obj)`.
- Run a post-solve verification loop over all elements to confirm coverage.

### Step 4 - Prove Optimality (Optional)
- To confirm optimality, add a cut: `model.obj <= incumbent_value - epsilon` and re-solve. Infeasibility proves the original solution was optimal.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.Sets = pyo.Set(initialize=all_sets)
model.Elements = pyo.Set(initialize=all_elements)
model.cost = pyo.Param(model.Sets, initialize=cost_dict)
model.coverage = pyo.Param(model.Elements, model.Sets, initialize=coverage_dict, default=0)
model.x = pyo.Var(model.Sets, domain=pyo.Binary)
def obj_rule(model):
    return sum(model.cost[j] * model.x[j] for j in model.Sets)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
def cover_rule(model, i):
    return sum(model.x[j] for j in model.Sets if model.coverage[i, j] == 1) >= 1
model.coverage_constr = pyo.Constraint(model.Elements, rule=cover_rule)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options['time_limit'] = time_limit
solver.options['threads'] = num_threads
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    selected = [j for j in model.Sets if pyo.value(model.x[j]) > 0.5]
    total_cost = pyo.value(model.obj)
    # Validation
    for i in model.Elements:
        if not any(pyo.value(model.x[j]) > 0.5 for j in model.Sets if model.coverage[i, j] == 1):
            raise AssertionError(f"Coverage failed for element {i}")
    print(f"Solution found. Cost: {total_cost}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran) with `TerminationCondition.optimal` (problem solved optimally).
- Not setting `mip_rel_gap` to `0.0` when seeking an optimal solution, potentially accepting suboptimal results.
- Attempting to access `pyo.value` on variables from an unsolved or infeasible model, causing errors.
