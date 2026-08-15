---
name: Cardinality-Constrained Pairwise Selection
description: |
  Model and solve combinatorial selection problems where pairwise interactions contribute to the objective and a fixed number of items must be selected.
---

# Workflow 1 (Direct Quadratic Formulation)

## Modeling stage

### Strategy Overview
Formulate the problem directly using binary selection variables and a quadratic objective representing pairwise benefits. This approach leverages modern solvers' native support for quadratic terms, avoiding explicit linearization for simpler code.

### Step 1 - Define Core Sets and Parameters
- Define a set `I` representing all candidate items (e.g., `I = range(n)`).
- Define a parameter `benefit[i][j]` representing the value gained if item `i` and item `j` are both selected. Use a placeholder matrix.
- Define a scalar parameter `k` for the required number of items to select.

### Step 2 - Declare Decision Variables
- Create a binary decision variable `x[i]` for each item `i` in `I`. `x[i] = 1` indicates selection.

### Step 3 - Formulate Cardinality Constraint
- Add a single linear constraint: the sum of all `x[i]` must equal `k`.

### Step 4 - Formulate Quadratic Objective
- Define the objective as the sum of `benefit[i][j] * x[i] * x[j]` over all ordered pairs `(i, j)` where `i != j`. For symmetric benefits, sum over `i < j` and multiply by 2, or use ordered pairs directly.
- Set the objective sense to maximize.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of candidate items"}
  ],
  "parameters": [
    {"name": "benefit", "type": "matrix", "dimensions": ["I", "I"], "description": "Pairwise benefit matrix"},
    {"name": "k", "type": "scalar", "description": "Required number of selected items"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "index": "I", "description": "Selection variable for each item"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in I} sum_{j in I, j != i} benefit[i][j] * x[i] * x[j]"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum_{i in I} x[i] == k"}
  ]
}
```

### Common Pitfalls
- Using an unordered pair sum (`i < j`) for an asymmetric benefit matrix, which incorrectly halves the objective value.
- Forgetting to set the solver's non-convex parameter when using a solver like Gurobi for quadratic binary problems.
- Defining the benefit matrix with non-zero diagonal terms (`i == j`), which adds unnecessary self-interaction terms to the objective.

## Solving stage

### Strategy Overview
Use a modeling framework (e.g., Pyomo) coupled with a solver capable of handling non-convex quadratic objectives (e.g., Gurobi, CPLEX). Configure the solver for optimality and runtime control, then extract and verify the solution.

### Step 1 - Build Model from Formulation
- Instantiate a concrete model.
- Populate the `benefit` parameter (e.g., from a nested list or dictionary).
- Declare the `x` variables using `pyomo.environ.Var` with `within=pyomo.environ.Binary`.
- Add the cardinality constraint using `pyomo.environ.Constraint`.
- Add the quadratic objective using `pyomo.environ.Objective` with the `sense` parameter.

### Step 2 - Configure and Run Solver
- Select a solver like `gurobi` or `cplex`.
- Set key options: `TimeLimit` for runtime control, `MIPGap=0.0` for exact optimality, `Threads` for parallelism, `Seed` for reproducibility.
- For quadratic models, set `NonConvex=2` (Gurobi) to handle non-convex terms.
- Call the solver and capture the results object.

### Step 3 - Check Status and Extract Solution
- Check the solver termination condition (e.g., `results.solver.termination_condition`). Proceed only if optimal or feasible.
- Extract the values of `x[i]` into a list or dictionary.
- Calculate the selected indices where `x[i].value > 0.5`.

### Step 4 - Verify Objective Value (Optional)
- For validation, recompute the objective value directly from the selected indices and the `benefit` matrix.
- Compare this computed value to the solver's reported objective value to catch any modeling errors.

### Code Usage
```python
import pyomo.environ as pyo

# Build model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(n))
model.x = pyo.Var(model.I, within=pyo.Binary)
model.benefit = pyo.Param(model.I, model.I, initialize=benefit_dict, default=0)
model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.I) == k)
model.obj = pyo.Objective(
    expr=sum(model.benefit[i,j] * model.x[i] * model.x[j] for i in model.I for j in model.I if j != i),
    sense=pyo.maximize
)

# Solve
solver = pyo.SolverFactory('gurobi')
solver.options['NonConvex'] = 2
solver.options['TimeLimit'] = time_limit
results = solver.solve(model)

# Check status and extract
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    # ... proceed with solution
```

### Common Pitfalls
- Not checking solver status before accessing variable values, leading to runtime errors.
- Using a solver (e.g., HiGHS) that does not support non-convex quadratic objectives without linearization.
- Omitting the `NonConvex` parameter for quadratic binary problems in Gurobi, causing the solver to reject the model.

# Workflow 2 (Linearized Formulation)

## Modeling stage

### Strategy Overview
Linearize the quadratic objective by introducing auxiliary binary variables `y[i][j]` to represent the product `x[i]*x[j]`. This reformulation creates a larger but linear MIP, compatible with a wider range of solvers, including those that do not support quadratic terms.

### Step 1 - Define Core Sets and Parameters
- Define a set `I` representing all candidate items.
- Define a parameter `benefit[i][j]` for pairwise benefits.
- Define the cardinality parameter `k`.

### Step 2 - Declare Primary Selection Variables
- Create binary decision variables `x[i]` for each item `i`.

### Step 3 - Declare Auxiliary Pair Variables
- Create binary decision variables `y[i][j]` for each ordered pair `(i, j)` where `i != j`. `y[i][j] = 1` indicates both `x[i]` and `x[j]` are selected.

### Step 4 - Add Linearization Constraints
- For each pair `(i, j)`, add constraints linking `y[i][j]` to `x[i]` and `x[j]`:
    - `y[i][j] <= x[i]`
    - `y[i][j] <= x[j]`
    - `y[i][j] >= x[i] + x[j] - 1`
- These constraints enforce `y[i][j] = x[i] * x[j]`.

### Step 5 - Formulate Linear Objective and Cardinality Constraint
- Define the objective as the sum of `benefit[i][j] * y[i][j]` over all relevant pairs.
- Add the cardinality constraint: `sum_i x[i] == k`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of candidate items"},
    {"name": "Pairs", "description": "Set of ordered pairs (i,j) where i != j"}
  ],
  "parameters": [
    {"name": "benefit", "type": "matrix", "dimensions": ["I", "I"], "description": "Pairwise benefit matrix"},
    {"name": "k", "type": "scalar", "description": "Required number of selected items"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "index": "I", "description": "Selection variable for each item"},
    {"name": "y", "type": "binary", "index": "Pairs", "description": "Auxiliary variable for x[i]*x[j]"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{(i,j) in Pairs} benefit[i][j] * y[i][j]"
  },
  "constraints": [
    {"name": "cardinality", "expression": "sum_{i in I} x[i] == k"},
    {"name": "linearize_lower1", "index": "Pairs", "expression": "y[i][j] <= x[i]"},
    {"name": "linearize_lower2", "index": "Pairs", "expression": "y[i][j] <= x[j]"},
    {"name": "linearize_upper", "index": "Pairs", "expression": "y[i][j] >= x[i] + x[j] - 1"}
  ]
}
```

### Common Pitfalls
- Creating auxiliary variables for diagonal pairs (`i == j`), which are unnecessary and add model bloat.
- Forgetting one of the three linearization constraints, which breaks the equivalence `y[i][j] = x[i] * x[j]`.
- Using this O(n²) variable formulation for very large `n` without considering performance implications.

## Solving stage

### Strategy Overview
Build the linearized MIP model using a modeling library and solve it with any competent MIP solver (e.g., CBC, Gurobi, CPLEX). The linear structure ensures broad solver compatibility.

### Step 1 - Build Linearized Model
- Instantiate the model and define sets `I` and `Pairs`.
- Declare `x` and `y` as binary variables.
- Add the three linearization constraints for each pair in `Pairs` using loops or vectorized operations.
- Add the cardinality constraint and linear objective.

### Step 2 - Configure and Run Solver
- Select a MIP solver (e.g., `cbc`, `gurobi`).
- Set standard options: `TimeLimit`, `MIPGap`.
- Solve the model.

### Step 3 - Process Solution
- Check the solver termination condition.
- Extract the values of `x[i]` to determine the selected items.
- The `y` variables can typically be ignored after solving.

### Step 4 - Verify Solution (Optional)
- Recompute the objective using the selected `x` values and the original quadratic expression to validate the linearization.

### Code Usage
```python
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(n))
# Define Pairs set, e.g., all ordered pairs i != j
model.Pairs = pyo.Set(initialize=[(i,j) for i in model.I for j in model.I if i != j])

model.x = pyo.Var(model.I, within=pyo.Binary)
model.y = pyo.Var(model.Pairs, within=pyo.Binary)

model.benefit = pyo.Param(model.I, model.I, initialize=benefit_dict, default=0)

# Linearization constraints
def linearize_lower1_rule(model, i, j):
    return model.y[i,j] <= model.x[i]
model.con1 = pyo.Constraint(model.Pairs, rule=linearize_lower1_rule)

def linearize_lower2_rule(model, i, j):
    return model.y[i,j] <= model.x[j]
model.con2 = pyo.Constraint(model.Pairs, rule=linearize_lower2_rule)

def linearize_upper_rule(model, i, j):
    return model.y[i,j] >= model.x[i] + model.x[j] - 1
model.con3 = pyo.Constraint(model.Pairs, rule=linearize_upper_rule)

# Cardinality constraint
model.cardinality = pyo.Constraint(expr=sum(model.x[i] for i in model.I) == k)

# Linear objective
model.obj = pyo.Objective(
    expr=sum(model.benefit[i,j] * model.y[i,j] for (i,j) in model.Pairs),
    sense=pyo.maximize
)

# Solve with a linear MIP solver
solver = pyo.SolverFactory('cbc')
results = solver.solve(model)

# Extract solution
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
```

### Common Pitfalls
- The model size grows quadratically with `n`; for large problems, this can lead to memory issues or long solve times.
- Using this formulation when a direct quadratic approach with a capable solver would be more efficient and concise.
- Incorrectly indexing the `benefit` parameter when creating the objective, leading to key errors.
