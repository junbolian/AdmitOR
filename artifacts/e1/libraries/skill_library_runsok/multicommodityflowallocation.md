---
name: MultiCommodityFlowAllocation
description: |
  Model and solve multi-commodity flow allocation problems with linear profit maximization, exact demand satisfaction, and non-negative flow variables using structured modeling and solver backends.
---

# Workflow 1 (Google OR-Tools LP)

## Modeling stage

### Strategy Overview
Model the problem as a pure linear program using Google OR-Tools' `pywraplp` interface. This approach is efficient for medium-scale problems and provides a direct, imperative API for variable and constraint creation.

### Step 1 - Define Sets and Parameters
- Declare clear lists for suppliers, products, and regions to structure the problem.
- Define demand as a 2D dictionary `demand[p][r]` and profit as a 3D dictionary `profit[s][p][r]`. Use zero as a default for missing profit entries to handle sparse data.

### Step 2 - Create Flow Variables
- Instantiate a three-dimensional array of continuous decision variables `x[s][p][r]` using nested loops.
- Set each variable's lower bound to `0` and upper bound to `solver.infinity()` to enforce non-negativity.

### Step 3 - Formulate Demand Satisfaction Constraints
- For each product `p` and region `r`, create a linear equality constraint: `sum_{s} x[s][p][r] == demand[p][r]`.
- Use a loop to set the coefficient of each variable `x[s][p][r]` to `1` within its respective constraint.

### Step 4 - Build Linear Profit Objective
- Initialize the objective for maximization.
- In a triple-nested loop, add the term `profit[s][p][r] * x[s][p][r]` to the objective.

### Formulation Template
```json
{
  "sets": ["suppliers", "products", "regions"],
  "parameters": [
    {"name": "demand", "dim": ["product", "region"]},
    {"name": "profit", "dim": ["supplier", "product", "region"]}
  ],
  "decision_variables": [
    {"name": "x", "dim": ["supplier", "product", "region"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{s,p,r} profit[s][p][r] * x[s][p][r]"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "sum_{s} x[s][p][r] == demand[p][r]", "forall": ["product", "region"]}
  ]
}
```

### Common Pitfalls
- Forgetting to set coefficients for all variables in a constraint, leading to incorrect sums.
- Assuming missing profit values are zero without documenting the assumption, which can skew results.
- Using variable names without indices, making debugging and result interpretation difficult.

## Solving stage

### Strategy Overview
Solve the constructed model using the GLOP linear programming solver. Implement systematic solution extraction and validation to ensure correctness and interpretability.

### Step 1 - Instantiate Solver and Solve
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Check Solution Status
- Verify the solver status is `OPTIMAL` or `FEASIBLE` before proceeding.
- If the status is not acceptable, print a warning and exit gracefully.

### Step 3 - Extract and Validate Results
- Compute the total profit by summing `x[s][p][r].solution_value() * profit[s][p][r]` for all variables and compare it to the solver's reported objective value.
- For each product-region pair, sum the allocated flows to confirm they equal the demand.

### Step 4 - Report Allocation Patterns
- Iterate through all variables and print non-zero allocations (`solution_value() > tolerance`), showing supplier-product-region assignments.
- Output the total profit in a parseable format (e.g., `RESULT: <value>`).

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation as per modeling stage)
objective.SetMaximization()
solver.Solve()

# solve with status / termination checks
if solver.Objective().Value() == float('inf') or solver.Objective().Value() == float('-inf'):
    print("Problem is unbounded.")
elif solver.Objective().Value() is None:
    print("No solution found.")
else:
    status = ['OPTIMAL', 'FEASIBLE', 'INFEASIBLE', 'UNBOUNDED', 'ABNORMAL', 'NOT_SOLVED']
    print('Solution status:', status[solver.Objective().Value()])
    if solver.Objective().Value() == 0:  # OPTIMAL
        total_profit = solver.Objective().Value()
        # ... (result extraction and validation)
```

### Common Pitfalls
- Not checking solver status, leading to errors when trying to access solution values from an infeasible model.
- Using a loose tolerance for checking non-zero flows, which can misrepresent the solution.
- Failing to compute and cross-verify the objective value from variable values, missing potential solver reporting errors.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo, separating data preparation from model construction. This approach is flexible, supports multiple solvers (HiGHS, CBC), and is well-suited for complex or large-scale problems.

### Step 1 - Prepare Data Structures
- Define sets for suppliers, products, and regions as Python lists or sets.
- Create parameter dictionaries: `demand[(p, r)]` and `profit[(s, p, r)]`. For incomplete profit data, implement a data generation function (e.g., arithmetic progression, constant extrapolation) and document the assumption.

### Step 2 - Build Abstract Model with Sets and Variables
- Instantiate a `ConcreteModel` or `AbstractModel`.
- Add `Set` components for suppliers, products, and regions.
- Add a `Var` component `model.x` indexed over the three sets with `domain=NonNegativeReals`.

### Step 3 - Define Objective and Constraints Declaratively
- Define the objective using a `sum()` comprehension over all sets: `sum(profit[s,p,r] * model.x[s,p,r] for s in S for p in P for r in R)`.
- Create a `Constraint` component indexed by product and region, where each rule returns the demand satisfaction equality.

### Formulation Template
```json
{
  "sets": ["S", "P", "R"],
  "parameters": [
    {"name": "demand", "dim": ["P", "R"]},
    {"name": "profit", "dim": ["S", "P", "R"]}
  ],
  "decision_variables": [
    {"name": "x", "dim": ["S", "P", "R"], "type": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(profit[s,p,r] * x[s,p,r] for s in S for p in P for r in R)"
  },
  "constraints": [
    {"name": "demand_con", "expression": "sum(x[s,p,r] for s in S) == demand[p,r]", "forall": ["p in P", "r in R"]}
  ]
}
```

### Common Pitfalls
- Using incorrect index order in parameter dictionaries, causing key errors during model construction.
- Defining constraint rules with side effects or mutable default arguments, leading to unpredictable behavior.
- Not separating data generation from the model, making it hard to test different data scenarios.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an efficient LP solver backend (HiGHS or CBC). Configure solver options for performance, rigorously check termination conditions, and extract results into interpretable formats.

### Step 1 - Select Solver and Configure Options
- Instantiate a solver factory: `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set options like time limit (`seconds`) and optimality gap tolerance (`ratio` or `gap`) if needed.

### Step 2 - Solve and Inspect Termination
- Call `solver.solve(model, tee=False)` and capture the results object.
- Check `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Validate and Analyze Solution
- If the solution is acceptable, compute total allocated demand per product-region pair to verify constraint satisfaction.
- Calculate the total profit from variable values and compare it to the solver's reported objective.

### Step 4 - Extract and Report Allocations
- Iterate through `model.x` and collect variable values where `pyo.value(model.x[s,p,r]) > tolerance`.
- Print a summary of allocations and the total profit in both human-readable and machine-parsable formats.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.S = pyo.Set(initialize=suppliers)
model.P = pyo.Set(initialize=products)
model.R = pyo.Set(initialize=regions)
model.x = pyo.Var(model.S, model.P, model.R, domain=pyo.NonNegativeReals)
# ... (objective and constraint definitions)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimal solution found.")
        # ... (result extraction)
    elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
        print("Feasible solution found.")
    else:
        print("Solver terminated with condition:", results.solver.termination_condition)
else:
    print("Solver failed.")
```

### Common Pitfalls
- Not checking both solver status and termination condition, potentially accepting suboptimal or infeasible solutions.
- Accessing variable values before verifying the solution status, which may raise exceptions.
- Using a single, hard-coded data generation method for incomplete profits without sensitivity analysis.
