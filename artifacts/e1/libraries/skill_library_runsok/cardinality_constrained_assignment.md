---
name: Cardinality-Constrained Assignment
description: |
  Model and solve binary assignment problems with per-element and total cardinality constraints to minimize total cost.

---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Formulate the problem using OR-Tools CP-SAT, a constraint programming solver designed for discrete optimization. This approach is well-suited for binary assignment problems with combinatorial constraints, offering efficient search and built-in support for logical constraints.

### Step 1 - Define Binary Assignment Variables
- Create a binary decision variable `x[i][j]` for each potential assignment between elements of the first set `I` and the second set `J`.
- Use `model.NewBoolVar()` to instantiate each variable, storing them in a dictionary keyed by tuple `(i, j)` for clarity and easy access.

### Step 2 - Enforce One-to-One Matching Constraints
- For each element `i` in set `I`, add a constraint `sum(x[i][j] for j in J) <= 1` to ensure it is assigned to at most one element in `J`.
- For each element `j` in set `J`, add a constraint `sum(x[i][j] for i in I) <= 1` to ensure it receives at most one assignment from `I`.

### Step 3 - Enforce Exact Total Assignment Constraint
- Add a global constraint `sum(x[i][j] for i in I for j in J) == K`, where `K` is the required total number of assignments. This is distinct from the per-element constraints.

### Step 4 - Formulate the Cost Minimization Objective
- Define a cost parameter `c[i][j]` for each potential assignment.
- Construct the objective expression `sum(c[i][j] * x[i][j] for i in I for j in J)` and call `model.Minimize()` on it.

### Formulation Template
```json
{
  "sets": [
    "I = {0, ..., nI-1}",
    "J = {0, ..., nJ-1}"
  ],
  "parameters": [
    "c[i][j]: cost of assigning i to j, for all i in I, j in J",
    "K: exact total number of assignments required"
  ],
  "decision_variables": [
    "x[i][j] ∈ {0, 1}: 1 if i is assigned to j, else 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i∈I} ∑_{j∈J} c[i][j] * x[i][j]"
  },
  "constraints": [
    "∑_{j∈J} x[i][j] ≤ 1, ∀ i ∈ I",
    "∑_{i∈I} x[i][j] ≤ 1, ∀ j ∈ J",
    "∑_{i∈I} ∑_{j∈J} x[i][j] = K"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce both row (`i`) and column (`j`) constraints, which breaks the one-to-one matching structure.
- Using a `<=` constraint for the total assignment count when an exact number `== K` is required.
- Mismatching the indices of the cost matrix `c[i][j]` with the variable indices `x[i][j]`, leading to incorrect objective values.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver to find an optimal or feasible solution. Handle solver statuses correctly to extract the objective value and the set of active assignments.

### Step 1 - Configure Solver Parameters
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set key parameters for performance and determinism: `max_time_in_seconds` for a runtime limit, `num_search_workers` for parallelism, `random_seed` for reproducibility, and `relative_gap_limit = 0.0` to require an exact optimal solution.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if the status is `OPTIMAL` or `FEASIBLE` before attempting to extract solution values. Handle `INFEASIBLE` or `UNKNOWN` statuses with appropriate error messages or fallback logic.

### Step 3 - Extract Solution and Objective Value
- Retrieve the objective value via `solver.ObjectiveValue()`.
- Iterate over all variable indices `(i, j)` and collect those where `solver.Value(x[(i, j)]) == 1` into a list of assignments.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation (using placeholders: I, J, c, K)
model = cp_model.CpModel()
x = {}
for i in range(len(I)):
    for j in range(len(J)):
        x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")

# Add constraints
for i in range(len(I)):
    model.Add(sum(x[(i, j)] for j in range(len(J))) <= 1)
for j in range(len(J)):
    model.Add(sum(x[(i, j)] for i in range(len(I))) <= 1)
model.Add(sum(x[(i, j)] for i in range(len(I)) for j in range(len(J))) == K)

# Set objective
model.Minimize(sum(c[i][j] * x[(i, j)] for i in range(len(I)) for j in range(len(J))))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    total_cost = solver.ObjectiveValue()
    assignments = [(i, j) for (i, j), var in x.items() if solver.Value(var) == 1]
    # Proceed with solution
else:
    # Handle infeasible or unknown status
    pass
```

### Common Pitfalls
- Not checking solver status before accessing `ObjectiveValue()`, which can raise an error or return misleading data.
- Using a non-zero `relative_gap_limit` when an exact optimal solution is required, potentially accepting suboptimal results.
- Forgetting to set `num_search_workers` appropriately for the available CPU cores, underutilizing parallel search capabilities.

# Workflow 2 (MIP Solver via Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem using Pyomo, an algebraic modeling language, and solve it with a Mixed-Integer Programming (MIP) solver backend (e.g., SCIP, CBC). This approach provides a declarative modeling style and leverages the robustness of traditional MIP solvers for linear assignment problems.

### Step 1 - Declare Sets and Parameters
- Define Pyomo `Set` objects for the source set `I` and target set `J`.
- Define a `Param` block `c[i, j]` to store assignment costs, indexed over the Cartesian product `I × J`.
- Define a scalar parameter `K` for the required total number of assignments.

### Step 2 - Define Binary Decision Variables
- Declare a `Var` block `x[i, j]` with domain `Binary`, representing the assignment decision.

### Step 3 - Construct Constraints Algebraically
- Use Pyomo's `Constraint` component with rule functions to enforce `sum(x[i, j] for j in J) <= 1` for each `i` in `I`.
- Similarly, enforce `sum(x[i, j] for i in I) <= 1` for each `j` in `J`.
- Add a global constraint `sum(x[i, j] for i in I for j in J) == K`.

### Step 4 - Define the Objective Function
- Use the `Objective` component to minimize `sum(c[i, j] * x[i, j] for i in I for j in J)`.

### Formulation Template
```json
{
  "sets": [
    "I (indexed by i)",
    "J (indexed by j)"
  ],
  "parameters": [
    "c[i, j] on I*J",
    "K (scalar)"
  ],
  "decision_variables": [
    "x[i, j] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i∈I} ∑_{j∈J} c[i, j] * x[i, j]"
  },
  "constraints": [
    "row_cap[i]: ∑_{j∈J} x[i, j] ≤ 1, ∀ i ∈ I",
    "col_cap[j]: ∑_{i∈I} x[i, j] ≤ 1, ∀ j ∈ J",
    "total_assign: ∑_{i∈I} ∑_{j∈J} x[i, j] = K"
  ]
}
```

### Common Pitfalls
- Incorrectly defining the index set for parameters or variables, leading to `KeyError` during model construction.
- Using Python's built-in `sum` inside Pyomo constraint rules instead of Pyomo's `summation` or a explicit `for` loop, which may not create proper expression objects.
- Not verifying that the cost parameter `c` is defined for all `(i, j)` pairs present in the variable index set.

## Solving stage

### Strategy Overview
Instantiate a MIP solver via Pyomo's `SolverFactory`, configure it with appropriate tolerances and limits, solve the model, and rigorously check termination conditions before extracting the solution.

### Step 1 - Select and Configure Solver
- Create a solver object: `solver = SolverFactory('scip')` (or `'cbc'`, `'gurobi'`).
- Set solver options: `solver.options['limits/time']` for a time limit, `solver.options['parallel']` for thread count, and `solver.options['mip/gap']` for optimality tolerance (set to 0 for exact solution).

### Step 2 - Solve and Validate Termination
- Call `results = solver.solve(model, tee=False)`.
- Check both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`). Accept `optimal` or `feasible` conditions before proceeding.

### Step 3 - Extract Assignment Solution
- Retrieve the objective value from `model.obj()` (or `results.problem.lower_bound`).
- Iterate over the `x` variable index set and collect indices where `pyo.value(x[i, j]) > 0.5` (accounting for solver numerical tolerance).

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(len(I)))  # Placeholder I
model.J = pyo.Set(initialize=range(len(J)))  # Placeholder J

def cost_init(model, i, j):
    return c[i][j]  # Placeholder cost matrix c
model.c = pyo.Param(model.I, model.J, initialize=cost_init)
model.K = pyo.Param(initialize=K)  # Placeholder K

model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

def row_rule(model, i):
    return sum(model.x[i, j] for j in model.J) <= 1
model.row_cap = pyo.Constraint(model.I, rule=row_rule)

def col_rule(model, j):
    return sum(model.x[i, j] for i in model.I) <= 1
model.col_cap = pyo.Constraint(model.J, rule=col_rule)

def total_rule(model):
    return sum(model.x[i, j] for i in model.I for j in model.J) == model.K
model.total_assign = pyo.Constraint(rule=total_rule)

def obj_rule(model):
    return sum(model.c[i, j] * model.x[i, j] for i in model.I for j in model.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Solve with status / termination checks
solver = pyo.SolverFactory('scip')
solver.options['limits/time'] = 30
solver.options['parallel'] = 8
solver.options['mip/gap'] = 0.0

results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                              pyo.TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    assignments = [(i, j) for i in model.I for j in model.J if pyo.value(model.x[i, j]) > 0.5]
    # Proceed with solution
else:
    # Handle solver failure or infeasibility
    pass
```

### Common Pitfalls
- Confusing `SolverStatus.ok` (solver ran normally) with `TerminationCondition.optimal` (found proven optimum). Both checks are necessary.
- Not setting `mip/gap` (or `ratioGap`) to zero, allowing the solver to stop early with a suboptimal solution for this exact problem.
- Directly accessing `model.x[i, j]` without calling `pyo.value()` on it, which returns the Pyomo variable object, not its numerical solution.
