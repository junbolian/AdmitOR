---
name: Capacitated Facility Location Minimization
description: |
  Model and solve binary integer programs for minimizing facility count under capacity and assignment constraints using two complementary solver workflows.
---

# Workflow 1 (CP-SAT for Exact Binary Optimization)

## Modeling stage

### Strategy Overview
This workflow models the problem as a pure binary integer program suitable for constraint programming and SAT solvers, focusing on logical constraints and exact solution methods.

### Step 1 - Define Binary Decision Variables
- Create a binary variable `y_j` for each potential facility `j` to indicate if it is opened (1) or closed (0).
- Create a binary variable `x_i_j` for each resource `i` and facility `j` to indicate assignment.

### Step 2 - Enforce Assignment Constraints
- For each resource `i`, add a constraint that the sum of its assignment variables across all facilities equals 1: `∑_j x_i_j = 1`.
- This ensures every resource is assigned to exactly one facility.

### Step 3 - Link Assignment to Facility Opening
- For each resource `i` and facility `j`, add a logical linking constraint: `x_i_j ≤ y_j`.
- This prevents assignment to a facility that is not opened.

### Step 4 - Enforce Capacity Constraints
- For each facility `j`, add a knapsack-style capacity constraint: `∑_i weight_i * x_i_j ≤ capacity_j * y_j`.
- The `y_j` term ensures the constraint is only active if the facility is opened.

### Step 5 - Set Objective Function
- Define the objective to minimize the total number of opened facilities: `min ∑_j y_j`.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "facilities"
  ],
  "parameters": [
    {"name": "weight_i", "domain": "resources", "type": "float"},
    {"name": "capacity_j", "domain": "facilities", "type": "float"}
  ],
  "decision_variables": [
    {"name": "y_j", "domain": "facilities", "type": "binary"},
    {"name": "x_i_j", "domain": ["resources", "facilities"], "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y_j for j in facilities)"
  },
  "constraints": [
    {"name": "assignment", "expression": "sum(x_i_j for j in facilities) == 1", "domain": "resources"},
    {"name": "linking", "expression": "x_i_j <= y_j", "domain": ["resources", "facilities"]},
    {"name": "capacity", "expression": "sum(weight_i * x_i_j for i in resources) <= capacity_j * y_j", "domain": "facilities"}
  ]
}
```

### Common Pitfalls
- Forgetting the `y_j` term in the capacity constraint, which incorrectly imposes capacity limits on closed facilities.
- Using non-binary variables for `x_i_j` or `y_j`, which violates the pure binary formulation required by CP-SAT.
- Defining insufficiently large index sets, leading to out-of-bounds errors during constraint generation.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools CP-SAT, configuring it for optimality proofs and parallel search, followed by systematic solution verification.

### Step 1 - Configure Solver Parameters
- Set a time limit (`max_time_in_seconds`) to bound runtime.
- Enable parallel search (`num_search_workers`) to leverage multiple CPU cores.
- Set a random seed (`random_seed`) for reproducibility.
- Disable relative gap termination (`relative_gap_limit = 0.0`) to force search for proven optimum.

### Step 2 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the status is `OPTIMAL` or `FEASIBLE` before proceeding to extract values.

### Step 3 - Extract and Verify Solution
- Extract opened facilities: `[j for j in facilities if solver.Value(y_j) == 1]`.
- Extract assignments: `{(i, j) for i in resources for j in facilities if solver.Value(x_i_j) == 1}`.
- Calculate the load on each opened facility: `sum(weight_i * solver.Value(x_i_j) for i in resources)` and verify it does not exceed capacity.

### Step 4 - Prove Optimality via Infeasibility Test
- If an optimal solution uses `k` facilities, add a new constraint `sum(y_j for j in facilities) <= k-1` to the model.
- Re-solve; if the result is `INFEASIBLE`, the original solution is proven optimal.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... create variables and constraints as per formulation ...

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract solution
    used_facilities = [j for j in facilities if solver.Value(y_j) == 1]
    # ... further extraction and verification ...
else:
    # Handle no solution found
    pass
```

### Common Pitfalls
- Not checking solver status before calling `solver.Value()`, which can crash on infeasible models.
- Setting `relative_gap_limit` to a positive value, which may stop the solver before proving optimality.
- Forgetting to reset or copy the model before adding the optimality-proving constraint, corrupting the original solution state.

# Workflow 2 (MIP Solver via Algebraic Modeling)

## Modeling stage

### Strategy Overview
This workflow uses an algebraic modeling library (e.g., Pyomo) to construct a mixed-integer program, solved by external MIP solvers like Gurobi or HiGHS, emphasizing model abstraction and solver portability.

### Step 1 - Abstract Model Construction
- Define an abstract model with `Set` components for resources and facilities.
- Declare `Param` components for resource weights and facility capacities.

### Step 2 - Declare Decision Variables
- Declare `Var` components `y` (indexed by facilities) and `x` (indexed by resources and facilities) as binary variables.

### Step 3 - Build Constraints Algebraically
- Construct the assignment constraint as a `ConstraintList` with one rule per resource.
- Build linking and capacity constraints using indexed `Constraint` rules that iterate over the appropriate sets.

### Step 4 - Define Objective
- Define an `Objective` component with the expression `sum(model.y[j] for j in model.facilities)` and sense `minimize`.

### Step 5 - Validate Model Bounds
- Ensure all parameters are positive and capacities are sufficient to hold at least one resource, preventing trivial infeasibility.

### Formulation Template
```json
{
  "sets": [
    "I = set of resources",
    "J = set of facilities"
  ],
  "parameters": [
    {"name": "w_i", "domain": "I", "type": "nonnegative float"},
    {"name": "C_j", "domain": "J", "type": "positive float"}
  ],
  "decision_variables": [
    {"name": "y_j", "domain": "J", "type": "binary"},
    {"name": "x_i_j", "domain": ["I", "J"], "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y_j over J)"
  },
  "constraints": [
    {"name": "assign", "expression": "sum(x_i_j over J) == 1", "domain": "I"},
    {"name": "link", "expression": "x_i_j <= y_j", "domain": ["I", "J"]},
    {"name": "cap", "expression": "sum(w_i * x_i_j over I) <= C_j * y_j", "domain": "J"}
  ]
}
```

### Common Pitfalls
- Using concrete data during model construction, which reduces reusability across instances.
- Incorrectly ordering indices in constraint rules, leading to shape mismatches.
- Omitting the `* y_j` factor in the capacity constraint, making it linear instead of bilinear and incorrect.

## Solving stage

### Strategy Overview
Instantiate the abstract model with data, solve using a configured MIP solver, and implement a verification loop to confirm optimality.

### Step 1 - Instantiate Model and Configure Solver
- Create a solver instance (e.g., `SolverFactory('gurobi')`).
- Set optimality tolerance (`MIPGap` or `mip_rel_gap`) to 0.0.
- Set a time limit (`TimeLimit` or `time_limit`).
- Configure parallelism (`Threads`) and a random seed if supported.

### Step 2 - Solve with Robust Status Handling
- Call `solver.solve(model, tee=False)`.
- Check both the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`) before loading solutions.

### Step 3 - Extract and Analyze Solution
- Load the solution into the model object.
- Identify used facilities: `[j for j in model.J if pyo.value(model.y[j]) > 0.5]`.
- Map resource assignments and compute facility loads for validation.

### Step 4 - Verify Optimality via Bound Testing
- Compute a theoretical lower bound: `ceil(total_weight / max_capacity)`.
- If the solution value equals this bound, optimality is strongly suggested.
- For formal proof, add a constraint `sum(model.y[j] for j in model.J) <= k-1` and re-solve; infeasibility confirms optimality.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.AbstractModel()
# ... define sets, params, variables, constraints, objective ...
instance = model.create_instance(data)

# solve with status / termination checks
solver = pyo.SolverFactory('solver_name')
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 30
results = solver.solve(instance, load_solutions=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    instance.solutions.load_from(results)
    # Extract and verify solution
    used = [j for j in instance.J if pyo.value(instance.y[j]) > 0.5]
else:
    # Handle infeasible or error status
    pass
```

### Common Pitfalls
- Loading solutions without checking termination condition, potentially loading invalid intermediate results.
- Setting `MIPGap` to a very small positive number instead of 0.0, allowing early suboptimal termination.
- Not using `load_solutions=False` when performing the infeasibility test for optimality proof, causing conflicts with the previously loaded solution.
