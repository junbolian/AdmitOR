---
name: Pairwise Selection Optimization
description: |
  Model and solve selection problems with pairwise interactions using binary variables, cardinality constraints, and logical linking, maximizing weighted sum of activated pairs.

---
# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Formulate the problem for a Constraint Programming/SAT (CP-SAT) solver using native Boolean variables and linear constraints. This approach is efficient for binary optimization with logical relationships and is well-suited for OR-Tools.

### Step 1 - Define Core Variables
- Create a binary variable `x[i]` for each element `i` in the set `N` to represent its selection status (1 if selected, 0 otherwise).
- Create a binary variable `y[(i, j)]` for each relevant ordered pair `(i, j)` in the set `P` to indicate if the pairwise interaction is active.

### Step 2 - Impose Cardinality
- Add a single linear equality constraint enforcing that exactly `K` elements are selected: `sum(x[i] for i in N) == K`.

### Step 3 - Link Selection and Activation
- For each pair `(i, j)` in `P`, add three linear constraints to enforce the logical equivalence `y[(i, j)] == (x[i] AND x[j])`:
  - `y[(i, j)] <= x[i]` (activation requires first element selected).
  - `y[(i, j)] <= x[j]` (activation requires second element selected).
  - `y[(i, j)] >= x[i] + x[j] - 1` (if both are selected, activation is forced).

### Step 4 - Formulate Objective
- Define the objective as the maximization of the weighted sum of all activated pairs: `sum(weight[(i, j)] * y[(i, j)] for (i, j) in P)`.

### Formulation Template
```json
{
  "sets": [
    "N: List of element indices",
    "P: List of ordered pairs (i, j) where i != j"
  ],
  "parameters": [
    "K: Integer, exact number of elements to select",
    "weight: Dictionary mapping pair (i, j) to a numerical benefit"
  ],
  "decision_variables": [
    "x[i]: Binary, selection of element i",
    "y[(i, j)]: Binary, activation of pair (i, j)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[(i, j)] * y[(i, j)] for (i, j) in P)"
  },
  "constraints": [
    "cardinality: sum(x[i] for i in N) == K",
    "link_upper_i: y[(i, j)] <= x[i] for all (i, j) in P",
    "link_upper_j: y[(i, j)] <= x[j] for all (i, j) in P",
    "link_lower: y[(i, j)] >= x[i] + x[j] - 1 for all (i, j) in P"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude the `i == j` case when generating ordered pair variables, which can create meaningless self-pair variables.
- Misinterpreting directed vs. undirected weights; ensure the pair set `P` and weight dictionary correctly reflect the problem's symmetry requirements.
- Assuming the logical linking constraints are redundant; omitting any of the three constraints breaks the `AND` equivalence.

## Solving stage

### Strategy Overview
Implement the model using the OR-Tools CP-SAT solver, configure it for performance and reproducibility, and robustly extract and verify the solution.

### Step 1 - Instantiate Model and Variables
- Create a CP-SAT model instance.
- Create Boolean variable lists/dictionaries using `NewBoolVar`.
.### Step 2 - Add Constraints
- Add the cardinality constraint using `Add(sum(x) == K)`.
- Iterate over the pair set `P` to add the three logical linking constraints for each pair.

### Step 3 - Set Objective and Solver Parameters
- Set the maximization objective using `Maximize(sum(weight * y))`.
- Configure the solver with a time limit (`max_time_in_seconds`), number of parallel workers (`num_search_workers`), and a random seed (`random_seed`) for reproducibility.

### Step 4 - Solve and Check Status
- Execute the solver and check the result status (`OPTIMAL` or `FEASIBLE`). Handle `UNKNOWN` or `INFEASIBLE` statuses with appropriate error handling or fallback logic.

### Step 5 - Extract and Interpret Solution
- Extract selected elements by checking `solver.Value(x[i]) == 1`.
- Extract activated pairs by checking `solver.Value(y[(i, j)]) == 1`.
- Calculate the achieved objective value from the solver for verification.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model
model = cp_model.CpModel()
N = range(num_elements)
P = [(i, j) for i in N for j in N if i != j]  # Example: all ordered pairs

x = [model.NewBoolVar(f"x_{i}") for i in N]
y = {(i, j): model.NewBoolVar(f"y_{i}_{j}") for (i, j) in P}

# Cardinality constraint
model.Add(sum(x) == K)

# Logical linking constraints
for (i, j) in P:
    model.Add(y[(i, j)] <= x[i])
    model.Add(y[(i, j)] <= x[j])
    model.Add(y[(i, j)] >= x[i] + x[j] - 1)

# Objective
objective_terms = [weights[(i, j)] * y[(i, j)] for (i, j) in P]
model.Maximize(sum(objective_terms))

# Solve with configuration
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

# Check status and extract solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in N if solver.Value(x[i]) == 1]
    activated = [(i, j) for (i, j) in P if solver.Value(y[(i, j)]) == 1]
    objective_value = solver.ObjectiveValue()
else:
    # Handle solver failure
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not setting a time limit for large instances, potentially causing the solver to run indefinitely.
- Forgetting to check solver status before accessing variable values, leading to runtime errors.
- Using floating-point weights that exceed the solver's integer-based precision; consider scaling weights to integers if necessary.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem using Pyomo's abstract or concrete modeling paradigm to create a Mixed-Integer Programming (MIP) model. This provides flexibility to use commercial (e.g., Gurobi, CPLEX) or open-source (e.g., HiGHS, CBC) solvers.

### Step 1 - Define Sets and Parameters
- Declare Pyomo `Set` objects for the element set `N` and the pair set `P`.
- Declare a Pyomo `Param` object for the weight dictionary, mapped over the set `P`.

### Step 2 - Define Decision Variables
- Declare binary variable `x` indexed over `N` for element selection.
- Declare binary variable `y` indexed over `P` for pair activation.

### Step 3 - Enforce Cardinality Constraint
- Add a single constraint enforcing `sum(x[i] for i in N) == K`.

### Step 4 - Enforce Logical Linking
- Add constraints indexed over `P` to enforce `y[i,j] == x[i] * x[j]` using the standard linearization:
  - `y[i,j] <= x[i]`
  - `y[i,j] <= x[j]`
  - `y[i,j] >= x[i] + x[j] - 1`

### Step 5 - Define Maximization Objective
- Define the objective as the maximization of `sum(weight[i,j] * y[i,j] for (i,j) in P)`.

### Formulation Template
```json
{
  "sets": [
    "N: Pyomo Set of element indices",
    "P: Pyomo Set of tuples (i, j) representing pairs"
  ],
  "parameters": [
    "K: Integer parameter, selection count",
    "weight: Pyomo Param indexed by P, pairwise benefit"
  ],
  "decision_variables": [
    "x: Pyomo Var indexed by N, domain=Binary",
    "y: Pyomo Var indexed by P, domain=Binary"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[i,j] * y[i,j] for (i,j) in P)"
  },
  "constraints": [
    "cardinality: sum(x[i] for i in N) == K",
    "link_upper_i: y[i,j] <= x[i] for all (i,j) in P",
    "link_upper_j: y[i,j] <= x[j] for all (i,j) in P",
    "link_lower: y[i,j] >= x[i] + x[j] - 1 for all (i,j) in P"
  ]
}
```

### Common Pitfalls
- Incorrectly defining the pair set `P` (e.g., including self-pairs or missing directed pairs), leading to an incorrect objective.
- Using Python's built-in `sum` inside Pyomo constraint rules instead of Pyomo's `summation` or generator expressions, which can cause construction errors.
- Not initializing the weight parameter for all indices in `P`, resulting in runtime errors.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model, connect to a MIP solver via `SolverFactory`, configure solver options for exactness and performance, and implement robust solution extraction with status checks.

### Step 1 - Build Concrete Model
- Populate the model with concrete data for sets `N`, `P`, parameter `weight`, and scalar `K`.

### Step 2 - Configure and Execute Solver
- Use `SolverFactory` to instantiate the desired solver (e.g., `'highs'`, `'gurobi'`).
- Set solver options such as `time_limit`, `mip_rel_gap` (to 0.0 for optimality), `threads`, and `seed`.
- Call `solve` on the model instance.

### Step 3 - Validate Solver Termination
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`). Proceed only if successful.

### Step 4 - Extract Solution
- Extract selected elements by filtering `pyo.value(x[i]) > 0.5`.
- Extract activated pairs by filtering `pyo.value(y[i,j]) > 0.5`.
- Retrieve the objective value via `pyo.value(model.obj)`.

### Step 5 - Optional Verification
- For small instances, implement brute-force enumeration to verify the solver's solution and confirm the interpretation of pair weights.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build concrete model
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=range(num_elements))
# Define P, e.g., all ordered pairs
model.P = pyo.Set(initialize=[(i, j) for i in model.N for j in model.N if i != j], dimen=2)
model.weights = pyo.Param(model.P, initialize=weight_dict)
model.K = pyo.Param(initialize=K, mutable=True)

model.x = pyo.Var(model.N, domain=pyo.Binary)
model.y = pyo.Var(model.P, domain=pyo.Binary)

# Objective
model.obj = pyo.Objective(expr=sum(model.weights[i,j] * model.y[i,j] for (i,j) in model.P), sense=pyo.maximize)

# Constraints
model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.N) == model.K)

def link_upper_i_rule(m, i, j):
    return m.y[i,j] <= m.x[i]
model.link_upper_i = pyo.Constraint(model.P, rule=link_upper_i_rule)

def link_upper_j_rule(m, i, j):
    return m.y[i,j] <= m.x[j]
model.link_upper_j = pyo.Constraint(model.P, rule=link_upper_j_rule)

def link_lower_rule(m, i, j):
    return m.y[i,j] >= m.x[i] + m.x[j] - 1
model.link_lower = pyo.Constraint(model.P, rule=link_lower_rule)

# Solve
solver = pyo.SolverFactory('highs')  # Or 'gurobi', 'cplex'
solver.options['time_limit'] = 300
solver.options['mip_rel_gap'] = 0.0
solver.options['threads'] = 8
solver.options['random_seed'] = 42

results = solver.solve(model, tee=False)

# Check status and extract
if results.solver.status == SolverStatus.ok and \
   results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    activated = [(i,j) for (i,j) in model.P if pyo.value(model.y[i,j]) > 0.5]
    objective_value = pyo.value(model.obj)
else:
    # Handle solver failure
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not using `pyo.value()` to access variable values after solving, leading to access of unsolved variable objects.
- Setting `mip_rel_gap` incorrectly for the chosen solver (e.g., using `0.0` for HiGHS is correct, but some solvers use `1e-4` as default).
- Omitting the check for `SolverStatus.ok` before checking the termination condition, which can mask critical solver failures.
