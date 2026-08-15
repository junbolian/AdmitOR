---
name: Multi-Dimensional Flow Allocation
description: |
  Model and solve linear allocation problems with multi-dimensional flow variables, exact demand satisfaction, and a linear profit objective using structured data and solver-aware patterns.

---
# Workflow 1 (OR-Tools LP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear programming API for a direct, imperative model build. It is suited for rapid prototyping and deployment in environments where OR-Tools is the standard, focusing on efficient constraint construction and solver control.

### Step 1 - Define Multi-Index Decision Variables
- Create a continuous decision variable for each combination of source, destination, and product type.
- Use `solver.NumVar(lower_bound, upper_bound, name)` with a lower bound of 0 to enforce non-negativity directly, avoiding separate constraints.
- Store variables in a dictionary keyed by a tuple of indices for easy access during constraint building.

### Step 2 - Encode Demand Satisfaction as Equality Constraints
- For each destination-product pair, create a linear equality constraint: `solver.Constraint(rhs, rhs)` where `rhs` is the exact demand value.
- Within a loop over all sources, set the coefficient of the corresponding flow variable to 1.0 using `constraint.SetCoefficient`.
- This ensures the total flow from all sources to that destination-product pair exactly meets the demand.

### Step 3 - Formulate Linear Profit Objective
- Initialize the solver's objective function: `solver.Objective()`.
- Iterate over all variable indices, adding each variable to the objective with its corresponding unit profit coefficient using `objective.SetCoefficient`.
- Set the objective sense to maximization via `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "product_types"],
  "parameters": [
    {"name": "unit_profit", "dimensions": ["sources", "destinations", "product_types"]},
    {"name": "demand", "dimensions": ["destinations", "product_types"]}
  ],
  "decision_variables": [
    {"name": "flow", "dimensions": ["sources", "destinations", "product_types"], "type": "continuous", "lower_bound": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(unit_profit[s][d][p] * flow[s][d][p] for s in sources for d in destinations for p in product_types)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "sum(flow[s][d][p] for s in sources) == demand[d][p]", "for_all": ["destinations", "product_types"]}
  ]
}
```

### Common Pitfalls
- Forgetting to set the lower bound on `NumVar` to 0, leading to negative flows unless explicitly constrained.
- Mismatching the order of indices between the profit data structure and the variable creation loops, causing incorrect objective coefficients.
- Using `solver.infinity()` for an unbounded upper bound when a realistic capacity limit should be applied for model realism.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' GLOP solver, which is efficient for continuous linear problems. The focus is on robust solution status checking, numerical validation, and extraction of actionable allocation insights.

### Step 1 - Instantiate Solver and Solve
- Create the solver instance: `pywraplp.Solver.CreateSolver("GLOP")`.
- Call `solver.Solve()` to execute the optimization. Store the returned status code.

### Step 2 - Verify Solution Status and Feasibility
- Check if the status is `solver.OPTIMAL` or `solver.FEASIBLE`. If not, handle the infeasible/unbounded case appropriately (e.g., log error, return default).
- For a feasible solution, recompute key aggregated values (e.g., total flow to each demand pair) and compare against the original demand parameters within a small tolerance (e.g., `1e-6`) to confirm numerical accuracy.

### Step 3 - Extract and Report Results
- Retrieve the objective value using `objective.Value()`.
- Iterate through all decision variables, filtering for those where `variable.solution_value() > tolerance`.
- Report these non-zero allocations along with their indices and contribution to profit, providing interpretable output.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("GLOP")
flow = {}
for s in range(num_sources):
    for d in range(num_destinations):
        for p in range(num_products):
            flow[s, d, p] = solver.NumVar(0, solver.infinity(), f"flow_{s}_{d}_{p}")

for d in range(num_destinations):
    for p in range(num_products):
        constraint = solver.Constraint(demand[d][p], demand[d][p])
        for s in range(num_sources):
            constraint.SetCoefficient(flow[s, d, p], 1)

objective = solver.Objective()
for s in range(num_sources):
    for d in range(num_destinations):
        for p in range(num_products):
            objective.SetCoefficient(flow[s, d, p], unit_profit[s][d][p])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_profit = objective.Value()
    # Validation and extraction logic here
else:
    # Handle infeasible or error case
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Assuming `solver.OPTIMAL` is the only successful status; `solver.FEASIBLE` is also acceptable for a valid, potentially sub-optimal solution.
- Not using a tolerance when checking variable values, leading to false positives for near-zero flows due to floating-point arithmetic.
- Omitting post-solve validation of constraints, which can hide subtle model formulation or data errors.

# Workflow 2 (Pyomo Declarative)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's declarative modeling style, defining abstract sets and parameters for a clean, maintainable, and solver-agnostic formulation. It is ideal for complex, research-oriented models where separation of model logic from data is critical.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo Set objects for `model.sources`, `model.destinations`, and `model.product_types`.
- Define Pyomo Param objects for `model.unit_profit` (indexed by three sets) and `model.demand` (indexed by destination and product). Initialize them with nested dictionaries.
- This abstract structure allows the model to be built independently of concrete data.

### Step 2 - Declare Non-Negative Flow Variables
- Create a Pyomo Var `model.flow`, indexed by the three sets, with `domain=pyo.NonNegativeReals`. This automatically enforces the lower bound of 0.
- Using the `domain` argument is cleaner and more efficient than adding explicit non-negativity constraints.

### Step 3 - Construct Objective and Constraints via Rules
- Define the objective using a `pyo.Objective` with a rule that sums `model.unit_profit[s,d,p] * model.flow[s,d,p]` over all indices and sets `sense=pyo.maximize`.
- Create a `pyo.Constraint` indexed by destinations and products. The rule for each index pair returns the equality: `sum(model.flow[s,d,p] for s in model.sources) == model.demand[d,p]`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "product_types"],
  "parameters": [
    {"name": "unit_profit", "dimensions": ["sources", "destinations", "product_types"]},
    {"name": "demand", "dimensions": ["destinations", "product_types"]}
  ],
  "decision_variables": [
    {"name": "flow", "dimensions": ["sources", "destinations", "product_types"], "type": "continuous", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(unit_profit[s][d][p] * flow[s][d][p] for s in sources for d in destinations for p in product_types)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "expression": "sum(flow[s][d][p] for s in sources) == demand[d][p]", "for_all": ["destinations", "product_types"]}
  ]
}
```

### Common Pitfalls
- Initializing a Pyomo Param with a scalar default value instead of a properly nested dictionary, leading to indexing errors during model instantiation.
- Forgetting to pass the `model` instance as the first argument to constraint/objective rules.
- Defining constraints with a `rule` function that has an incorrect signature (must match the indexing sets).

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., for HiGHS or CBC), separating the abstract model from the solving backend. Emphasize comprehensive solver status checking and structured result output.

### Step 1 - Instantiate Model and Solver
- Create a concrete model instance by passing the data dictionary to `model.create_instance(data)`.
- Instantiate the solver using `pyo.SolverFactory("solver_name")`, e.g., `"highs"` for LP.

### Step 2 - Configure Solver and Solve
- Set practical solver options via `solver.options`, such as `time_limit` and `threads`.
- Execute the solve with `results = solver.solve(model)`. The `results` object contains termination and status information.

### Step 3 - Validate Solution and Extract Output
- Check that `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.
- Retrieve the objective value using `pyo.value(model.obj)`.
- Iterate through `model.flow`, extracting variable values where `pyo.value(model.flow[s,d,p]) > tolerance` to report the allocation plan.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=source_list)
model.destinations = pyo.Set(initialize=dest_list)
model.product_types = pyo.Set(initialize=product_list)

model.unit_profit = pyo.Param(model.sources, model.destinations, model.product_types, initialize=profit_dict)
model.demand = pyo.Param(model.destinations, model.product_types, initialize=demand_dict)

model.flow = pyo.Var(model.sources, model.destinations, model.product_types, domain=pyo.NonNegativeReals)

def obj_rule(model):
    return sum(model.unit_profit[s, d, p] * model.flow[s, d, p]
               for s in model.sources for d in model.destinations for p in model.product_types)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

def demand_rule(model, d, p):
    return sum(model.flow[s, d, p] for s in model.sources) == model.demand[d, p]
model.demand_con = pyo.Constraint(model.destinations, model.product_types, rule=demand_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    total_profit = pyo.value(model.obj)
    # Extract non-zero flows
else:
    # Handle solver failure
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus` (solver runtime status) with `TerminationCondition` (solution quality), leading to incorrect success/failure detection.
- Not deactivating the `pyomo` log output (`pyo.SolverFactory('highs').solve(model, tee=False)`) when running in automated pipelines, causing log clutter.
- Attempting to access `pyo.value` on an abstract (un-instantiated) model component, which will raise an error.
