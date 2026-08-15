---
name: Bipartite Flow Optimization
description: |
  Model and solve bipartite flow problems (e.g., transportation, assignment) with supply, demand, and arc capacities using linear programming, with workflows for both OR-Tools and Pyomo backends.
---

# Workflow 1 (OR-Tools LP Solver)

## Modeling stage

### Strategy Overview
Model the problem as a bipartite flow network using Google OR-Tools' linear solver wrapper. This approach is ideal for rapid prototyping and solving pure linear programs with continuous variables, leveraging the efficient GLOP or CBC solvers directly through a procedural API.

### Step 1 - Define Data Structures
- Organize problem data into clear, indexed dictionaries or lists for supply nodes (origins) and demand nodes (destinations).
- Define parameters: `supply[i]` for each origin, `demand[j]` for each destination, `cost[i][j]` per-unit flow cost, and optional `capacity[i][j]` for arc limits.
- Use nested dictionaries or 2D arrays for cost and capacity to enable clean `(i, j)` indexing.

### Step 2 - Create Flow Variables
- Instantiate a linear solver (e.g., `pywraplp.Solver.CreateSolver('GLOP')`).
- For each origin-destination pair `(i, j)`, create a non-negative continuous variable `x[i][j]` using `solver.NumVar(lower_bound, upper_bound, name)`.
- Set the upper bound directly to `capacity[i][j]` if arc capacities exist, otherwise use `solver.infinity()`.

### Step 3 - Formulate Supply and Demand Constraints
- For each origin `i`, add a supply constraint: `sum_{j} x[i][j] <= supply[i]`.
- For each destination `j`, add a demand constraint: `sum_{i} x[i][j] == demand[j]` for balanced problems. Use `>=` for unbalanced supply.
- Construct constraints efficiently using list comprehensions or loops over the defined sets.

### Step 4 - Define Linear Cost Objective
- Create an objective expression: `sum_{i,j} cost[i][j] * x[i][j]`.
- Use `solver.Minimize(objective)` or `solver.Maximize(objective)` as required.

### Formulation Template
```json
{
  "sets": [
    "I: set of supply nodes (origins)",
    "J: set of demand nodes (destinations)"
  ],
  "parameters": [
    "supply[i]: non-negative available amount at origin i",
    "demand[j]: non-negative required amount at destination j",
    "cost[i][j]: unit flow cost from i to j",
    "capacity[i][j]: optional upper bound on flow from i to j (default: infinity)"
  ],
  "decision_variables": [
    "x[i][j]: non-negative continuous flow from origin i to destination j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I, j in J} cost[i][j] * x[i][j]"
  },
  "constraints": [
    "supply_limit[i]: sum_{j in J} x[i][j] <= supply[i], for all i in I",
    "demand_satisfaction[j]: sum_{i in I} x[i][j] == demand[j], for all j in J",
    "arc_capacity[i][j]: x[i][j] <= capacity[i][j], for all i in I, j in J (if applicable)"
  ]
}
```

### Common Pitfalls
- Forgetting to check if total supply meets total demand; using equality demand constraints in unbalanced problems will cause infeasibility.
- Not setting explicit upper bounds on variables when capacities exist, which can reduce solver performance.
- Using loose tolerances when checking solution values, leading to incorrect feasibility verification.

## Solving stage

### Strategy Overview
Solve the formulated linear program using the OR-Tools solver, implementing robust status checks, solution extraction, and post-solution validation to ensure correctness and feasibility.

### Step 1 - Configure and Invoke Solver
- Set solver parameters such as time limit (`solver.SetTimeLimit`) if needed.
- Call `solver.Solve()` to execute the optimization.

### Step 2 - Verify Solver Status
- Check the result status: `status in (solver.OPTIMAL, solver.FEASIBLE)`.
- If status is not optimal or feasible, report the specific status code and investigate model formulation or data.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value using `solver.Objective().Value()`.
- Iterate over all flow variables `x[i][j]` and collect their `solution_value()`.
- Programmatically verify all constraints using the extracted flows and a small tolerance (e.g., `1e-6`). Compute total outflow per origin and inflow per destination.

### Step 4 - Report Results
- Print the total cost and a summary of non-zero flows (where `flow > tolerance`).
- Optionally, output constraint satisfaction metrics for auditing.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation as per modeling stage)
solver.Solve()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    tolerance = 1e-6
    # Extract non-zero flows and verify constraints
    for i in origins:
        total_outflow = 0
        for j in destinations:
            flow = x[i][j].solution_value()
            total_outflow += flow
            if flow > tolerance:
                print(f"Flow {i}->{j}: {flow}")
        # Verify supply limit
        assert total_outflow <= supply[i] + tolerance, f"Supply violation at {i}"
    print(f"Total cost: {total_cost}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Extracting solution values without checking solver status first, leading to errors.
- Using an inappropriate solver (e.g., GLOP for integer problems); choose CBC for MIPs.
- Neglecting to verify constraints post-solution, potentially missing numerical inaccuracies.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the bipartite flow problem using Pyomo's abstract or concrete model syntax, which provides a declarative, solver-agnostic formulation. This workflow is suited for integration into larger optimization systems and offers access to a wide range of solvers like HiGHS (LP) or CBC (MIP).

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo Sets for origins (`model.I`) and destinations (`model.J`).
- Define Pyomo Parameters for `supply`, `demand`, `cost`, and optional `capacity` using `pyo.Param` within the model.
- Use indexing over the Cartesian product `model.I * model.J` for arc-specific parameters.

### Step 2 - Declare Flow Variables
- Create a continuous, non-negative variable `model.x` indexed over `(model.I, model.J)`.
- If arc capacities exist, set variable bounds directly within the variable declaration using the `bounds` argument.

### Step 3 - Construct Constraints via Rules
- Define a rule function for the supply constraint that, for each origin `i`, returns `sum(model.x[i,j] for j in model.J) <= model.supply[i]`.
- Define a similar rule for demand satisfaction: `sum(model.x[i,j] for i in model.I) == model.demand[j]`.
- Implement an optional arc capacity constraint rule: `model.x[i,j] <= model.capacity[i,j]`.

### Step 4 - Formulate Objective Function
- Define the objective using `model.obj = pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for i in model.I for j in model.J), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "I: Pyomo Set of supply nodes",
    "J: Pyomo Set of demand nodes"
  ],
  "parameters": [
    "supply: Pyomo Param indexed over I",
    "demand: Pyomo Param indexed over J",
    "cost: Pyomo Param indexed over I x J",
    "capacity: Pyomo Param indexed over I x J (optional)"
  ],
  "decision_variables": [
    "x: Pyomo Var indexed over I x J, domain=NonNegativeReals"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I, j in J)"
  },
  "constraints": [
    "supply_rule(i): sum(x[i,j] for j in J) <= supply[i]",
    "demand_rule(j): sum(x[i,j] for i in I) == demand[j]",
    "capacity_rule(i,j): x[i,j] <= capacity[i,j] (if parameter provided)"
  ]
}
```

### Common Pitfalls
- Confusing abstract and concrete model syntax; ensure parameters are initialized before use in a concrete model.
- Not providing default values for optional parameters like capacity, causing rule evaluation errors.
- Using inefficient rule definitions that perform redundant calculations; pre-compute sums where possible.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory (e.g., HiGHS for LP, CBC for MIP), configure solver options for performance, and implement comprehensive checks on solver status and termination condition before extracting and validating the solution.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory('highs')`.
- Set options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`. For LP, set `mip_rel_gap` to `-1` or `None`.

### Step 2 - Solve and Check Termination Status
- Execute `results = solver.solve(model, tee=False)`.
- Check both high-level solver status (`results.solver.status == SolverStatus.ok`) and detailed termination condition (`results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`).

### Step 3 - Extract and Verify Solution Values
- Retrieve the objective value: `total_cost = pyo.value(model.obj)`.
- Iterate over `model.x` to get flow values using `pyo.value(model.x[i,j])`.
- Programmatically verify all constraints against the solved values with a tolerance, ensuring supply, demand, and capacity limits are satisfied.

### Step 4 - Report and Handle Failures
- Print the total cost and a table of non-zero flows.
- If the solver did not converge optimally, log the termination condition and investigate model/data issues.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=origins_list)
model.J = pyo.Set(initialize=destinations_list)
# ... (parameter and variable definition as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    tolerance = 1e-6
    for i in model.I:
        for j in model.J:
            flow = pyo.value(model.x[i,j])
            if flow > tolerance:
                print(f"Flow {i}->{j}: {flow}")
    # Add constraint verification loops here
    print(f"Total cost: {total_cost}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming `SolverStatus.ok` alone guarantees a good solution; always check the termination condition.
- Not using `pyo.value()` to extract variable and objective values, leading to Pyomo expression objects.
- Forgetting to deactivate presolve or other solver features that might hide model errors during debugging.
