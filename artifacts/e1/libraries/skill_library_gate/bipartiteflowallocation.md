---
name: BipartiteFlowAllocation
description: |
  Model and solve bipartite flow allocation problems (e.g., supply chain, transportation) with linear profit/cost objectives and exact demand satisfaction constraints.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling style, defining sets and parameters clearly. This approach separates model logic from data, promoting reusability and clarity. The structure is a bipartite flow network with sources and destinations.

### Step 1 - Define Sets and Parameters
- Define two primary sets: `sources` and `destinations`. These represent the two sides of the bipartite network (e.g., factories and markets).
- Create a parameter dictionary `profit` keyed by `(source, destination)` tuples to store unit profit/cost coefficients.
- Create a parameter dictionary `demand` keyed by `destination` to store exact demand requirements.

### Step 2 - Create Decision Variables
- Define a continuous decision variable `flow[source, destination]` representing the quantity allocated from a source to a destination.
- Set the variable domain to `pyo.NonNegativeReals` to automatically enforce non-negativity constraints.

### Step 3 - Formulate Objective and Constraints
- Formulate the objective as the sum of `profit[s, d] * flow[s, d]` across all pairs, setting `sense=pyo.maximize` for profit or `pyo.minimize` for cost.
- For each destination `d`, create an equality constraint: the sum of `flow[s, d]` for all sources `s` must equal `demand[d]`. This ensures exact demand satisfaction.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "profit", "index": ["source", "destination"]},
    {"name": "demand", "index": ["destination"]}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["source", "destination"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s, d] * flow[s, d] for s in sources for d in destinations)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["destination"], "expression": "sum(flow[s, d] for s in sources) == demand[d]"}
  ]
}
```

### Common Pitfalls
- Forgetting to define the `profit` parameter for all `(source, destination)` pairs, which can lead to a KeyError during model construction.
- Using a single list for both sources and destinations without clear separation, which can cause indexing errors in constraints.
- Not using `NonNegativeReals` for the flow variable domain, requiring manual addition of lower-bound constraints.

## Solving stage

### Strategy Overview
Solve the constructed Pyomo model using the HiGHS or CBC solver via the `SolverFactory`. Configure solver options for performance and implement robust status checking to handle both optimal and feasible solutions gracefully.

### Step 1 - Configure and Execute Solver
- Instantiate the solver using `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set practical solver options such as a time limit (`time_limit`) and, for CBC, an optimality gap (`ratio`).
- Execute the solve with `solver.solve(model, tee=False)` to suppress verbose output unless debugging.

### Step 2 - Check Solution Status Robustly
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `TerminationCondition.feasible`). Accept either `optimal` or `feasible` as a valid result.
- If the status is not ok or termination is not acceptable, raise an error or return an appropriate message indicating infeasibility or other failure.

### Step 3 - Extract and Filter Solution
- Iterate through the `flow` variable index. Extract the value using `pyo.value(model.flow[s, d])`.
- Apply a small tolerance filter (e.g., `value > 1e-6`) to ignore numerically zero flows and produce a cleaner solution summary.
- Store non-zero flows in a structured dictionary keyed by `(source, destination)`.

### Step 4 - Validate and Package Results
- Perform a verification pass: for each destination, sum the extracted flows and compare to the original demand (within tolerance).
- Package results in a structured format (e.g., JSON) containing the solver status, objective value, and the filtered solution dictionary.
- For automated parsing, also print a simple result line like `RESULT:{objective_value}`.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (example using concrete model)
model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=sources_list)
model.destinations = pyo.Set(initialize=destinations_list)
model.profit = pyo.Param(model.sources, model.destinations, initialize=profit_dict)
model.demand = pyo.Param(model.destinations, initialize=demand_dict)
model.flow = pyo.Var(model.sources, model.destinations, domain=pyo.NonNegativeReals)
model.obj = pyo.Objective(expr=pyo.sum_product(model.profit, model.flow), sense=pyo.maximize)
def demand_rule(model, d):
    return sum(model.flow[s, d] for s in model.sources) == model.demand[d]
model.demand_con = pyo.Constraint(model.destinations, rule=demand_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    # Extract solution
    solution = {}
    for s in model.sources:
        for d in model.destinations:
            val = pyo.value(model.flow[s, d])
            if val > 1e-6:
                solution[(s, d)] = round(val, 4)
    total_profit = pyo.value(model.obj)
    print(f"RESULT:{total_profit}")
    # Package detailed results...
else:
    raise Exception(f"Solver failed with status: {status}, termination: {term}")
```

### Common Pitfalls
- Not checking both `SolverStatus` and `TerminationCondition`, leading to acceptance of invalid solutions (e.g., `infeasible`).
- Extracting variable values without a tolerance filter, resulting in cluttered output with many near-zero values.
- Omitting verification of demand satisfaction from the extracted solution, missing potential post-solve numerical errors.

# Workflow 2 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
Model the problem directly using the OR-Tools linear solver API (e.g., `GLOP`). This imperative style builds the model by creating variables and adding constraints row-by-row, which is efficient and closely maps to the solver's internal representation.

### Step 1 - Initialize Solver and Data Structures
- Create a linear solver instance using `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Organize data in parallel structures: lists for `sources` and `destinations`, a 2D list `profit[i][j]`, and a list `demand[j]`. Ensure indices align.

### Step 2 - Create Decision Variables
- Create a 2D list of decision variables `flow[i][j]` using `solver.NumVar(0, solver.infinity(), f'flow_{i}_{j}')`. The lower bound of `0` enforces non-negativity.

### Step 3 - Build Objective Function
- Initialize the objective using `solver.Objective()`.
- For each variable `flow[i][j]`, set its coefficient in the objective to `profit[i][j]` using `objective.SetCoefficient(flow[i][j], profit[i][j])`.
- Set the optimization sense to maximization (`objective.SetMaximization()`) or minimization.

### Step 4 - Add Demand Satisfaction Constraints
- For each destination `j`, create a constraint `solver.Constraint(demand[j], demand[j])` to enforce equality.
- For each source `i`, add the variable `flow[i][j]` to this constraint with a coefficient of `1` using `constraint.SetCoefficient(flow[i][j], 1)`.

### Formulation Template
```json
{
  "sets": ["sources (index i)", "destinations (index j)"],
  "parameters": [
    {"name": "profit", "index": ["i", "j"], "structure": "2D list"},
    {"name": "demand", "index": ["j"], "structure": "list"}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["i", "j"], "bounds": "[0, INF]"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i,j} profit[i][j] * flow[i][j]"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["j"], "expression": "sum_{i} flow[i][j] = demand[j]"}
  ]
}
```

### Common Pitfalls
- Mismatching indices between the `profit` matrix and the `flow` variable matrix, leading to incorrect objective coefficients.
- Forgetting to set the objective sense, defaulting to minimization.
- Creating constraints with the wrong bounds; using `solver.Constraint(lb, ub)` where `lb == ub` creates an equality constraint.

## Solving stage

### Strategy Overview
Solve the built model using the OR-Tools solver's `Solve()` method. Implement comprehensive result status checking and extract the solution, focusing on positive flows for clean reporting.

### Step 1 - Execute Solver and Check Status
- Call `solver.Solve()`.
- Check the result status using `solver.ResultStatus()`. Accept both `pywraplp.Solver.OPTIMAL` and `pywraplp.Solver.FEASIBLE` as successful outcomes.
- If the status is not acceptable, handle the failure appropriately (e.g., raise an error, return `None`).

### Step 2 - Extract and Filter Solution Values
- Iterate through all `flow[i][j]` variables. Retrieve the solution value using `flow[i][j].solution_value()`.
- Apply a tolerance filter (e.g., `value > 1e-6`) to include only positive flows in the final solution report.
- Store filtered flows in a list of dictionaries or a similar structured format.

### Step 3 - Verify Solution and Report
- Perform a verification pass: for each destination `j`, sum the extracted positive flows and compare to `demand[j]` (within tolerance).
- Print a concise result line `RESULT:{objective_value}` for automated parsing.
- Optionally, output a detailed JSON payload containing the status, objective value, and the filtered allocation dictionary.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# Assume sources_n, destinations_n, profit_matrix, demand_list are defined
flow = [[solver.NumVar(0, solver.infinity(), f'flow_{i}_{j}') for j in range(destinations_n)] for i in range(sources_n)]

objective = solver.Objective()
for i in range(sources_n):
    for j in range(destinations_n):
        objective.SetCoefficient(flow[i][j], profit_matrix[i][j])
objective.SetMaximization()

for j in range(destinations_n):
    constraint = solver.Constraint(demand_list[j], demand_list[j])
    for i in range(sources_n):
        constraint.SetCoefficient(flow[i][j], 1)

# Solve with status / termination checks
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_profit = objective.Value()
    solution = []
    for i in range(sources_n):
        for j in range(destinations_n):
            val = flow[i][j].solution_value()
            if val > 1e-6:
                solution.append({'source': i, 'dest': j, 'flow': val})
    print(f"RESULT:{total_profit}")
    # Package detailed results...
else:
    raise Exception(f"Solver did not find an optimal or feasible solution. Status: {status}")
```

### Common Pitfalls
- Only checking for `OPTIMAL` status and rejecting `FEASIBLE` solutions, which may be valid in some contexts.
- Not using a tolerance when filtering solution values, including many near-zero flows that obscure the meaningful allocation.
- Failing to verify that the extracted solution satisfies the demand constraints, potentially missing post-solve numerical discrepancies.
