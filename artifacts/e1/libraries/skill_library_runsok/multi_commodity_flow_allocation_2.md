---
name: Multi-Commodity Flow Allocation
description: |
  Model and solve multi-source, multi-product, multi-market allocation problems as linear programs with demand satisfaction constraints and profit maximization objectives.

---

# Workflow 1 (Google OR-Tools LP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear programming interface for a direct, imperative modeling style. It is suited for problems where the model structure is built procedurally with loops, and the solver (GLOP) is optimized for pure linear programs.

### Step 1 - Define Data Structures
- Organize problem data into nested lists or dictionaries that align with the dimensions of the decision variables (e.g., sources, products, markets).
- Map parameters such as `profit[source][product][market]` and `demand[market][product]` for efficient access during model construction.

### Step 2 - Create Decision Variables
- Declare non-negative continuous flow variables for each source-product-market combination using `solver.NumVar`.
- Use descriptive naming conventions (e.g., `x_s_p_m`) to aid in debugging and solution interpretation.

### Step 3 - Formulate Demand Constraints
- For each market-product pair, create a linear equality constraint with bounds equal to the exact demand.
- Sum the flow variables from all sources into this constraint to enforce demand satisfaction.

### Step 4 - Define Linear Objective
- Construct the objective function as a linear sum of profit coefficients multiplied by their corresponding flow variables.
- Set the objective sense to maximize.

### Formulation Template
```json
{
  "sets": ["sources", "products", "markets"],
  "parameters": [
    {"name": "profit", "dim": ["source", "product", "market"], "type": "float"},
    {"name": "demand", "dim": ["market", "product"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "dim": ["source", "product", "market"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s][p][m] * x[s][p][m] for s in sources for p in products for m in markets)"
  },
  "constraints": [
    {
      "name": "demand_satisfaction",
      "expression": "sum(x[s][p][m] for s in sources) == demand[m][p]",
      "for_all": ["m in markets", "p in products"]
    }
  ]
}
```

### Common Pitfalls
- Inefficiently nesting loops when adding coefficients, leading to slow model building for large-scale instances.
- Forgetting to set the upper and lower bounds of equality constraints to the same demand value.
- Using inconsistent indexing orders between parameters and variables, causing incorrect coefficient mapping.

## Solving stage

### Strategy Overview
The solving stage involves invoking the GLOP solver through the OR-Tools wrapper, systematically building the model from the formulation, and implementing robust checks for solution status and correctness.

### Step 1 - Solver Initialization
- Instantiate the linear solver using `pywraplp.Solver.CreateSolver('GLOP')`.
- Verify the solver is available before proceeding with model construction.

### Step 2 - Model Construction Loop
- Implement nested loops over all indices to create variables and add them to the objective.
- Build constraints by iterating over each market-product pair, creating a constraint object, and adding the appropriate variable coefficients from all sources.

### Step 3 - Solve and Check Status
- Call `solver.Solve()` and check the return status (`OPTIMAL`, `FEASIBLE`, etc.).
- Proceed to solution extraction only if the status indicates a successful solve.

### Step 4 - Solution Validation and Output
- Verify constraint satisfaction by recalculating the left-hand side of each demand constraint from the solution values and comparing to the right-hand side within a tolerance.
- Print the objective value with a standardized prefix (e.g., `RESULT: <value>`) for automated parsing, followed by an optional detailed allocation report.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Instantiate solver
solver = pywraplp.Solver.CreateSolver('GLOP')
if not solver:
    raise RuntimeError('Solver GLOP not available.')

# Build model (example snippet for variable and objective creation)
x = {}
for s in sources:
    for p in products:
        for m in markets:
            x[s, p, m] = solver.NumVar(0, solver.infinity(), f'x_{s}_{p}_{m}')
            objective.SetCoefficient(x[s, p, m], profit[s][p][m])

# Build constraints
for m in markets:
    for p in products:
        ct = solver.Constraint(demand[m][p], demand[m][p])
        for s in sources:
            ct.SetCoefficient(x[s, p, m], 1)

# Solve
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    # Validation and output
    total_profit = solver.Objective().Value()
    print(f'RESULT: {total_profit}')
else:
    print('Solve failed.')
```

### Common Pitfalls
- Assuming the solver always returns an optimal solution without checking the status code.
- Not using a tolerance when verifying constraint satisfaction, leading to false failures due to floating-point arithmetic.
- Extracting variable values without ensuring the solve was successful, which may return default or garbage values.

---

# Workflow 2 (Pyomo with Highs/CBC)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo modeling language for a declarative, algebraic approach. It separates model specification from solver execution, enhancing clarity and maintainability for complex multi-dimensional problems, and interfaces with solvers like HiGHS or CBC.

### Step 1 - Declare Abstract Sets
- Define Pyomo `Set` components for each indexing dimension (e.g., sources, products, markets) to structure the model abstractly.
- This promotes reusability and clear separation of model logic from data.

### Step 2 - Define Parameters with Dictionaries
- Initialize multi-dimensional parameters (profit, demand) using Pyomo `Param` components with dictionary initialization.
- Use tuple keys that match the set dimension order for consistency and readability.

### Step 3 - Declare Non-Negative Variables
- Create a continuous, non-negative `Var` indexed over the Cartesian product of the relevant sets to represent flow quantities.
- Use `within=pyo.NonNegativeReals` to enforce the domain.

### Step 4 - Formulate Constraints and Objective Declaratively
- Use Pyomo's `Constraint` and `Objective` components with rule functions that express the demand satisfaction and profit maximization logic algebraically.
- This keeps the formulation close to its mathematical representation.

### Formulation Template
```json
{
  "sets": ["sources", "products", "markets"],
  "parameters": [
    {"name": "profit", "dim": ["source", "product", "market"], "type": "Param"},
    {"name": "demand", "dim": ["market", "product"], "type": "Param"}
  ],
  "decision_variables": [
    {"name": "x", "dim": ["source", "product", "market"], "type": "Var", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(profit[s, p, m] * x[s, p, m] for s in sources for p in products for m in markets)"
  },
  "constraints": [
    {
      "name": "demand_satisfaction",
      "expression": "sum(x[s, p, m] for s in sources) == demand[m, p]",
      "for_all": ["m in markets", "p in products"]
    }
  ]
}
```

### Common Pitfalls
- Shadowing Pyomo model instance names (e.g., `model`) with loop variables inside rule functions, causing reference errors.
- Incorrectly ordering indices in parameter dictionary keys relative to set definitions, leading to key errors.
- Using mutable default arguments in rule functions, which can cause unexpected behavior across multiple model builds.

## Solving stage

### Strategy Overview
The solving stage involves selecting an appropriate LP solver (HiGHS or CBC) via Pyomo's `SolverFactory`, configuring solver options, executing the solve, and performing rigorous post-solution validation and output formatting.

### Step 1 - Solver Factory and Options
- Instantiate the solver using `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set practical options such as time limit, optimality gap tolerance, and number of threads for performance.

### Step 2 - Solve and Check Termination Conditions
- Execute `solver.solve(model, options=...)` and capture the results object.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`) to confirm a valid solution.

### Step 3 - Post-Solution Verification
- Implement a verification loop that computes the left-hand side of each demand constraint from the solved variable values and compares it to the parameter value within a small tolerance.
- Log any violations for debugging.

### Step 4 - Standardized Result Output
- Extract the objective value from the model and print it with a consistent prefix (e.g., `RESULT: <value>`).
- Optionally, print a non-zero allocation summary for human inspection.

### Code Usage
```python
import pyomo.environ as pyo

# Create a ConcreteModel
model = pyo.ConcreteModel()

# Define sets (example)
model.sources = pyo.Set(initialize=['s1', 's2'])
model.products = pyo.Set(initialize=['p1', 'p2'])
model.markets = pyo.Set(initialize=['m1', 'm2'])

# Define parameters with dictionary data
profit_data = {('s1', 'p1', 'm1'): 10.0, ...} # Fill with actual data
model.profit = pyo.Param(model.sources, model.products, model.markets, initialize=profit_data)

demand_data = {('m1', 'p1'): 100.0, ...}
model.demand = pyo.Param(model.markets, model.products, initialize=demand_data)

# Define variable
model.x = pyo.Var(model.sources, model.products, model.markets, within=pyo.NonNegativeReals)

# Define objective
def obj_rule(model):
    return sum(model.profit[s, p, m] * model.x[s, p, m] for s in model.sources for p in model.products for m in model.markets)
model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# Define constraints
def demand_rule(model, m, p):
    return sum(model.x[s, p, m] for s in model.sources) == model.demand[m, p]
model.demand_constraint = pyo.Constraint(model.markets, model.products, rule=demand_rule)

# Solve
solver = pyo.SolverFactory('highs')
results = solver.solve(model, options={'time_limit': 30})

# Check status and output
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    print(f'RESULT: {pyo.value(model.objective)}')
else:
    print('Solve failed.')
```

### Common Pitfalls
- Confusing `SolverStatus` (solver execution) with `TerminationCondition` (problem solution quality) when checking results.
- Not using `pyo.value()` to extract the objective function value, leading to accessing the expression object instead.
- Omitting tolerance checks in post-solution verification, causing false reports of constraint violations due to numerical precision.
