---
name: Set Cover with Cost Minimization
description: |
  Model and solve set cover problems with binary selection variables, coverage constraints, and a total cost minimization objective using modern MILP/SAT solvers.

---
# Workflow 1 (SAT Solver via OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Model the set cover problem as a 0-1 integer program and solve using a SAT-based solver (CP-SAT) for exact solutions, leveraging its efficient handling of binary variables and linear constraints.

### Step 1 - Define Data Structures
- Map the problem input into two core dictionaries: one for item costs and one for coverage relationships.
- Store `costs` as a dictionary mapping each selectable item to its cost (e.g., `{item_id: cost_value}`).
- Store `coverage` as a dictionary mapping each element that must be covered to a list of items that cover it (e.g., `{element_id: [item_id_1, item_id_2, ...]}`).

### Step 2 - Instantiate Model and Variables
- Create a `CpModel` object to serve as the model container.
- For each selectable item, create a binary decision variable using `model.NewBoolVar()`. Store these in a dictionary keyed by item ID.

### Step 3 - Formulate Coverage Constraints
- For each element in the `coverage` dictionary, add a linear constraint to the model.
- The constraint sums the binary variables for all covering items and requires the sum to be greater than or equal to 1: `sum(x[i] for i in coverage[element]) >= 1`.

### Step 4 - Define the Objective Function
- Formulate the objective to minimize the total selection cost.
- Use a linear expression: `sum(costs[i] * x[i] for i in all_items)`.
- Set this as the minimization objective using `model.Minimize()`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items.",
    "E: Set of elements that must be covered."
  ],
  "parameters": [
    "cost_i: Cost of selecting item i ∈ I.",
    "cover_e: List of items i ∈ I that cover element e ∈ E."
  ],
  "decision_variables": [
    "x_i ∈ {0, 1}: 1 if item i is selected, 0 otherwise."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} cost_i * x_i"
  },
  "constraints": [
    "Coverage: ∑_{i ∈ cover_e} x_i ≥ 1, ∀ e ∈ E."
  ]
}
```

### Common Pitfalls
- Forgetting to include all elements in the coverage dictionary, leading to uncovered requirements.
- Incorrectly defining the coverage mapping (e.g., mapping items to elements instead of elements to items), which complicates constraint generation.
- Using integer variables instead of boolean variables, which reduces solver efficiency.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver with parameters for performance and reliability, then rigorously verify the solution's feasibility and optimality.

### Step 1 - Configure Solver Parameters
- Instantiate a `CpSolver` object.
- Set key parameters: `max_time_in_seconds` for a runtime limit, `num_search_workers` to leverage multiple CPU cores, and `random_seed` for reproducibility.
- For an exact solution, set `relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Execute the solver on the model and capture the status.
- Interpret the status: `OPTIMAL` indicates a proven optimal solution was found; `FEASIBLE` indicates a valid solution was found within limits.

### Step 3 - Extract and Verify the Solution
- If the status is `OPTIMAL` or `FEASIBLE`, extract the selected items by iterating over variables where the solver value equals 1.
- Compute the total cost from the selected items or retrieve the objective value from the solver.
- Perform a post-solution verification: for each element, check that at least one selected item is in its coverage list.

### Step 4 - Confirm Optimality (Optional)
- To rigorously confirm optimality, add a new constraint to the model forcing the total cost to be less than the found best cost minus a small epsilon.
- Re-solve the model; if the result is `INFEASIBLE`, the original solution is optimal.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# Assume `all_items` and `coverage` dict are defined
x = {i: model.NewBoolVar(f"x_{i}") for i in all_items}
# Coverage constraints
for element, covering_items in coverage.items():
    model.Add(sum(x[i] for i in covering_items) >= 1)
# Objective
model.Minimize(sum(costs[i] * x[i] for i in all_items))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in all_items if solver.Value(x[i]) == 1]
    total_cost = sum(costs[i] for i in selected)
    # Verification loop
    for element, covering_items in coverage.items():
        if not any(i in selected for i in covering_items):
            raise AssertionError(f"Element {element} not covered.")
else:
    # Handle no solution found
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding valid solutions.
- Misinterpreting solver status codes (e.g., `UNKNOWN` vs. `FEASIBLE`).
- Skipping post-solution verification, which can miss errors in model formulation or data.

# Workflow 2 (MILP Solver via Pyomo)

## Modeling stage

### Strategy Overview
Model the set cover problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract or concrete modeling, then solve with an efficient MILP solver like HiGHS or CBC.

### Step 1 - Define Model and Sets
- Create a Pyomo `ConcreteModel` or `AbstractModel`.
- Define Pyomo `Set` objects for the selectable items and the elements to be covered.

### Step 2 - Declare Parameters and Variables
- Define a `Param` for item costs, indexed by the item set.
- Define binary decision variables using `Var(..., domain=Binary)`, indexed by the item set.

### Step 3 - Build Coverage Constraints
- Define a `Constraint` list indexed by the element set.
- For each element, the constraint body sums the binary variables of its covering items (accessed via a precomputed list or mapping). Enforce the sum to be >= 1.

### Step 4 - Set the Objective
- Define an `Objective` rule that sums the product of cost and variable for all items.
- Set the sense to `minimize`.

### Formulation Template
```json
{
  "sets": [
    "model.I: Set of selectable items.",
    "model.E: Set of elements that must be covered."
  ],
  "parameters": [
    "model.cost: model.cost[i], i ∈ I, cost of item i."
  ],
  "decision_variables": [
    "model.x: model.x[i] ∈ {0, 1}, i ∈ I."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[i] * model.x[i] for i in model.I)"
  },
  "constraints": [
    "model.Cover: sum(model.x[i] for i in cover[e]) >= 1, ∀ e ∈ model.E."
  ]
}
```

### Common Pitfalls
- Using Pyomo's `Param` with complex indexing or mutable defaults, which can cause initialization errors.
- Defining constraints by iterating over Python data structures outside Pyomo's rule functions, which breaks the abstract model pattern.
- Not pre-computing the `cover[e]` lists, leading to inefficient constraint generation inside rules.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with a MILP solver, configure it for performance, solve the instance, and extract results with proper status checks.

### Step 1 - Select and Configure the Solver
- Instantiate a solver object using `SolverFactory('solver_name')` (e.g., `'highs'` or `'cbc'`).
- Set solver options: `time_limit` for runtime, `mip_rel_gap` to 0.0 for optimality, and `threads` for parallel processing.

### Step 2 - Solve and Inspect Termination
- Call `solver.solve(model)` and capture the results object.
- Check both the solver status (`results.solver.status`) and the termination condition (`results.solver.termination_condition`). Accept `optimal` or `feasible` for a valid solution.

### Step 3 - Extract the Solution
- If the solve was successful, iterate through the model's binary variables.
- Consider a variable selected if its value is greater than 0.5 (accounting for solver tolerances).
- Compute the total cost from the selected items or retrieve the objective value from the model.

### Step 4 - Validate and Confirm Optimality
- Validate coverage by checking each element against the selected items.
- To confirm optimality, add a new constraint to the model limiting the objective to be less than the found cost minus epsilon, and re-solve. Infeasibility confirms optimality.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=all_items)
model.E = pyo.Set(initialize=all_elements)
model.cost = pyo.Param(model.I, initialize=costs)
model.x = pyo.Var(model.I, domain=pyo.Binary)

def cover_rule(model, e):
    # Assume `coverage_dict` maps element e to list of items
    return sum(model.x[i] for i in coverage_dict[e]) >= 1
model.Cover = pyo.Constraint(model.E, rule=cover_rule)

def obj_rule(model):
    return sum(model.cost[i] * model.x[i] for i in model.I)
model.Obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1.0  # HiGHS syntax for gap 0.0
solver.options['threads'] = 4
results = solver.solve(model)

if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = sum(costs[i] for i in selected)
    # Verification loop
    for e in model.E:
        if not any(i in selected for i in coverage_dict[e]):
            raise AssertionError(f"Element {e} not covered.")
else:
    # Handle no solution found
    print("No feasible solution found.")
```

### Common Pitfalls
- Confusing solver status (`SolverStatus.ok`) with termination condition; both must be checked.
- Not using `pyo.value()` to extract variable values, leading to type errors.
- Setting `mip_rel_gap=0.0` for solvers that expect a different syntax (e.g., HiGHS uses `mip_rel_gap=-1.0` for gap 0).
