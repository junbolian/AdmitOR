---
name: BipartiteFlowAllocation
description: |
  Model and solve bipartite flow allocation problems with demand satisfaction and profit maximization using linear programming.
---

# Workflow 1 (Google OR-Tools LP)

## Modeling stage

### Strategy Overview
Model the problem as a bipartite flow network using Google OR-Tools' linear programming interface, focusing on efficient variable creation and constraint building for continuous allocation.

### Step 1 - Define Problem Sets and Parameters
- Define two distinct sets: `sources` (e.g., companies, factories) and `destinations` (e.g., markets, customers).
- Create a 2D list or dictionary `profit[s][d]` to store the profit coefficient for each source-destination pair.
- Create a list `demand[d]` to store the demand quantity required at each destination.

### Step 2 - Create Decision Variables
- Instantiate a linear solver (e.g., `GLOP`) using `pywraplp.Solver.CreateSolver("GLOP")`.
- Create a dictionary of continuous, non-negative decision variables `flow[s][d]` using `solver.NumVar(0, solver.infinity(), name)`.
- Use a descriptive naming pattern like `f"flow_{s}_{d}"` for traceability in the solution output.

### Step 3 - Formulate Demand Satisfaction Constraints
- For each destination `d`, create a linear equality constraint: `sum(flow[s][d] for all s) == demand[d]`.
- Build the constraint by iterating over all sources and using `constraint.SetCoefficient(flow[s][d], 1)`.

### Step 4 - Define the Maximization Objective
- Set the objective sense to maximize using `solver.Maximize()`.
- Construct the objective expression by summing `profit[s][d] * flow[s][d]` for all source-destination pairs.
- Add each term to the objective using `objective.SetCoefficient(flow[s][d], profit[s][d])`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "profit", "index": ["sources", "destinations"], "type": "float"},
    {"name": "demand", "index": ["destinations"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["sources", "destinations"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s][d] * flow[s][d] for all s, d)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["destinations"], "expression": "sum(flow[s][d] for all s) == demand[d]"}
  ]
}
```

### Common Pitfalls
- Forgetting to set the objective sense to maximize, which defaults to minimization.
- Creating variables with implicit upper bounds that unintentionally restrict the solution space.
- Not using a tolerance (e.g., `1e-6`) when checking for non-zero flows in the solution, leading to verbose output.

## Solving stage

### Strategy Overview
Solve the linear program using the configured OR-Tools solver, implement robust status checking, and extract the solution with validation.

### Step 1 - Execute the Solver
- Call `solver.Solve()` to initiate the optimization.
- Set solver time limits or other parameters if necessary (e.g., `solver.set_time_limit`).

### Step 2 - Check Solution Status
- Check if the solver status is `pywraplp.Solver.OPTIMAL` or `FEASIBLE`.
- If the status is not optimal or feasible, log the status and handle the failure (e.g., return `None`, raise an informative error).

### Step 3 - Extract and Validate Results
- Retrieve the objective value using `solver.Objective().Value()`.
- Iterate through all `flow` variables and collect their `.solution_value()` into a dictionary.
- Filter the dictionary to report only allocations above a small tolerance (e.g., `1e-6`).
- Optionally, validate the solution by recalculating total profit and verifying demand constraints are satisfied.

### Step 4 - Output Structured Results
- Print a machine-parsable result line: `RESULT:{objective_value}`.
- Optionally, output a detailed JSON summary: `RESULT_JSON:{"objective": value, "allocations": filtered_solution_dict}`.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation as per modeling stage)
solver.Maximize(objective)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    solution = {}
    for s in sources:
        for d in destinations:
            var = flow[s][d]
            val = var.solution_value()
            if val > 1e-6:
                solution[f"flow_{s}_{d}"] = val
    print(f"RESULT:{objective_value}")
else:
    print("Solver did not find an optimal solution.")
```

### Common Pitfalls
- Assuming the solver always finds an optimal solution without checking the status.
- Extracting variable values without verifying the solve was successful, leading to errors.
- Not using a tolerance when checking variable values, which can include near-zero numerical noise.

# Workflow 2 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract modeling capabilities, separating model construction from data, and leveraging the HiGHS solver for efficient LP solving.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `model.sources` and `model.destinations`.
- Declare indexed `Param` objects: `model.profit` (indexed by source, destination) and `model.demand` (indexed by destination).
- Initialize parameters from a structured data dictionary, e.g., `profit_data = {(s, d): value}`.

### Step 2 - Create Decision Variables with Domain
- Declare a Pyomo `Var` object `model.flow`, indexed over `model.sources` and `model.destinations`.
- Set the domain to `pyo.NonNegativeReals` to enforce non-negativity implicitly.
- Optionally, set bounds or initialize values if required.

### Step 3 - Formulate Constraints via Rules
- Define a `Constraint` object `model.demand_satisfaction`, indexed by `model.destinations`.
- Create a rule function that returns the equality: `sum(model.flow[s, d] for s in model.sources) == model.demand[d]`.

### Step 4 - Define the Objective Function
- Create an `Objective` object `model.total_profit`.
- Set the sense to `pyo.maximize`.
- Define the expression as `sum(model.profit[s, d] * model.flow[s, d] for s in model.sources for d in model.destinations)`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "profit", "index": ["sources", "destinations"], "type": "float"},
    {"name": "demand", "index": ["destinations"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "flow", "index": ["sources", "destinations"], "type": "continuous", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s, d] * flow[s, d] for all s, d)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["destinations"], "expression": "sum(flow[s, d] for all s) == demand[d]"}
  ]
}
```

### Common Pitfalls
- Confusing Pyomo `ConcreteModel` (data-driven) with `AbstractModel` (data-separated) approaches.
- Using Python loops inside Pyomo expressions instead of built-in summations, which can be inefficient.
- Not properly initializing indexed parameters, leading to `KeyError` during model construction.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with data, configure the HiGHS solver, solve the instance, and implement comprehensive solution extraction and validation.

### Step 1 - Instantiate Model and Configure Solver
- Create a `ConcreteModel()` instance and populate it with data.
- Configure the solver: `solver = pyo.SolverFactory('highs')`.
- Set solver options such as time limit (`seconds`) and optimality gap tolerance (`ratio`).

### Step 2 - Solve and Check Termination
- Execute `results = solver.solve(model, tee=False)`.
- Check both the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`).
- Proceed only if status is `SolverStatus.ok` and termination is `optimal` or `feasible`.

### Step 3 - Extract and Process Solution
- Retrieve the objective value using `pyo.value(model.total_profit)`.
- Iterate over `model.flow` and extract variable values with `pyo.value(model.flow[s, d])`.
- Apply a tolerance filter (e.g., `1e-6`) to build a dictionary of non-zero allocations.

### Step 4 - Validate and Output Results
- Optionally, verify the solution by checking that demand constraints are satisfied with the extracted flows.
- Output a concise result string: `RESULT:{objective_value}`.
- Optionally, output a detailed JSON payload for further analysis.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=sources_list)
model.destinations = pyo.Set(initialize=destinations_list)
model.profit = pyo.Param(model.sources, model.destinations, initialize=profit_dict)
model.demand = pyo.Param(model.destinations, initialize=demand_dict)
model.flow = pyo.Var(model.sources, model.destinations, domain=pyo.NonNegativeReals)
def demand_rule(model, d):
    return sum(model.flow[s, d] for s in model.sources) == model.demand[d]
model.demand_con = pyo.Constraint(model.destinations, rule=demand_rule)
model.obj = pyo.Objective(expr=sum(model.profit[s, d] * model.flow[s, d] for s in model.sources for d in model.destinations), sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)
from pyomo.opt import SolverStatus, TerminationCondition
if results.solver.status == SolverStatus.ok and results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]:
    objective_value = pyo.value(model.obj)
    solution = {}
    for s in model.sources:
        for d in model.destinations:
            val = pyo.value(model.flow[s, d])
            if val > 1e-6:
                solution[f"flow_{s}_{d}"] = val
    print(f"RESULT:{objective_value}")
else:
    print("Solver did not converge to an optimal solution.")
```

### Common Pitfalls
- Not importing necessary Pyomo status enums (`SolverStatus`, `TerminationCondition`) for proper solution checking.
- Accessing variable values directly without using `pyo.value()`, which may not reflect the solved state.
- Forgetting to pass the model instance to the `solve` method.
