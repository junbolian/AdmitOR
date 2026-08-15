---
name: Continuous Bipartite Assignment LP
description: |
  Model and solve continuous assignment problems between two sets (e.g., resources to tasks) with supply limits, demand satisfaction, and per-assignment caps, using linear programming to minimize total cost.
---

# Workflow 1 (OR-Tools / GLOP)

## Modeling stage

### Strategy Overview
Model the problem as a linear program using OR-Tools' `pywraplp` API, structuring it as a bipartite assignment with continuous flow variables. This approach is direct and leverages efficient LP solvers like GLOP for continuous problems.

### Step 1 - Define Index Sets and Parameters
- Declare two index sets: `I` for supply nodes (e.g., individuals) and `J` for demand nodes (e.g., projects).
- Load or define parameter arrays: `supply_capacity[i]`, `demand[j]`, `cost[i][j]`, and `max_per_assignment[i][j]`.

### Step 2 - Create Decision Variables with Bounds
- Instantiate a continuous decision variable `x[i,j]` for each `(i,j)` pair.
- Set variable bounds directly: lower bound `0` and upper bound `max_per_assignment[i][j]` to encode per-assignment limits.

### Step 3 - Add Supply and Demand Constraints
- For each `i` in `I`, add a supply constraint: `sum_{j in J} x[i,j] <= supply_capacity[i]`.
- For each `j` in `J`, add a demand constraint: `sum_{i in I} x[i,j] == demand[j]`.

### Step 4 - Formulate Linear Cost Objective
- Define the objective as the sum of `cost[i][j] * x[i,j]` over all `i` and `j`.
- Set the objective sense to minimization.

### Formulation Template
```json
{
  "sets": ["I (supply nodes)", "J (demand nodes)"],
  "parameters": [
    "supply_capacity[i] (capacity per supply node)",
    "demand[j] (requirement per demand node)",
    "cost[i][j] (unit cost per assignment)",
    "max_per_assignment[i][j] (upper bound per variable)"
  ],
  "decision_variables": ["x[i,j] (continuous assignment quantity)"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} cost[i][j] * x[i,j]"
  },
  "constraints": [
    "supply_limit_i: sum_{j in J} x[i,j] <= supply_capacity[i], for all i in I",
    "demand_satisfaction_j: sum_{i in I} x[i,j] == demand[j], for all j in J",
    "per_assignment_limit_ij: 0 <= x[i,j] <= max_per_assignment[i][j], for all i in I, j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to set variable upper bounds, requiring separate constraints for `max_per_assignment`.
- Using integer or boolean variables when the problem allows continuous fractional assignments, unnecessarily complicating the solve.
- Mismatching index order between cost matrix and variable loops, leading to incorrect objective coefficients.

## Solving stage

### Strategy Overview
Solve the built model using OR-Tools' GLOP solver, check for optimality, and extract the solution. Implement verification against constraints with tolerance and produce structured output.

### Step 1 - Select Solver and Solve
- Instantiate the GLOP linear solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Validate Solver Status
- Check if the status is `OPTIMAL` or `FEASIBLE` before accessing solution values.
- If status is not acceptable, report the status code and terminate processing.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value using `solver.Objective().Value()`.
- For each variable `x[i,j]`, get its solution value and store if above a small epsilon (e.g., `1e-6`).
- Programmatically verify all supply, demand, and bound constraints are satisfied within tolerance.

### Step 4 - Generate Structured Output
- Summarize total cost and overall assignment quantities.
- For each demand node `j`, list contributing supply nodes and their assigned amounts.
- For each supply node `i`, report total utilization against its capacity.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (build model as per Modeling Stage steps)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    total_cost = solver.Objective().Value()
    epsilon = 1e-6
    # Extract and verify solution
    assignments = []
    for i in I:
        for j in J:
            val = x[i, j].solution_value()
            if val > epsilon:
                assignments.append((i, j, val))
    # ... (generate output and verification reports)
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, risking runtime errors.
- Using exact equality (`==`) for floating-point comparisons in verification; always use tolerance.
- Omitting solution verification, which can mask subtle constraint violations due to numerical precision.

# Workflow 2 (Pyomo / HiGHS)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model paradigm, leveraging set-based definitions for scalability. This approach separates model specification from solver choice, allowing easy backend switching.

### Step 1 - Define Abstract Sets and Parameters
- Create Pyomo `Set` objects `model.I` and `model.J` for the two index dimensions.
- Define `Pyomo.Param` objects for `capacity`, `demand`, `cost`, and `max_hours` with appropriate indexing.

### Step 2 - Declare Continuous Variables with Bounds
- Declare a `Var` `model.x` indexed over `(I, J)` as a continuous variable.
- Specify bounds directly in the variable declaration using a rule: `bounds=lambda m, i, j: (0, max_hours[i][j])`.

### Step 3 - Construct Supply and Demand Constraints
- Add a `Constraint` rule for supply: `sum(model.x[i,j] for j in model.J) <= capacity[i]` for each `i`.
- Add a `Constraint` rule for demand: `sum(model.x[i,j] for i in model.I) == demand[j]` for each `j`.

### Step 4 - Define Linear Objective
- Use `Objective` rule to minimize `sum(cost[i][j] * model.x[i,j] for i in model.I for j in model.J)`.

### Formulation Template
```json
{
  "sets": ["I (supply nodes)", "J (demand nodes)"],
  "parameters": [
    "capacity[i] (supply limit)",
    "demand[j] (demand requirement)",
    "cost[i][j] (unit cost)",
    "max_hours[i][j] (assignment limit)"
  ],
  "decision_variables": ["x[i,j] (continuous, bounded)"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} cost[i][j] * x[i,j]"
  },
  "constraints": [
    "supply_rule(i): sum_{j in J} x[i,j] <= capacity[i], for all i in I",
    "demand_rule(j): sum_{i in I} x[i,j] == demand[j], for all j in J"
  ]
}
```

### Common Pitfalls
- Defining parameters as Python dictionaries without declaring them as `Pyomo.Param`, losing model portability.
- Using concrete model initialization with large datasets inefficiently; consider `AbstractModel` for data separation.
- Neglecting to set variable bounds, then adding separate constraints for `max_hours`, which is less efficient.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS LP solver via the `pyomo.SolverFactory` interface. Configure solver options, check termination conditions, and extract results into a portable data structure.

### Step 1 - Instantiate Solver and Set Options
- Create solver instance: `solver = SolverFactory('highs')`.
- Set options like time limit and threads: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`.

### Step 2 - Solve and Check Termination Status
- Call `results = solver.solve(model, tee=False)`.
- Verify `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Load Solution and Validate
- Load solution into model: `model.solutions.load_from(results)`.
- Iterate through `model.x` to extract values `pyo.value(model.x[i,j])` greater than a tolerance.
- Compute and report constraint satisfaction metrics for verification.

### Step 4 - Produce Output and Handle Failures
- Generate a dictionary or JSON with total cost, assignments, and utilization summaries.
- For infeasible or error statuses, output a structured error report with solver status and termination condition.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (build model as per Modeling Stage steps)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    total_cost = pyo.value(model.obj)
    epsilon = 1e-6
    assignments = []
    for i in model.I:
        for j in model.J:
            val = pyo.value(model.x[i, j])
            if val > epsilon:
                assignments.append((i, j, val))
    # ... (generate output and verification reports)
else:
    print(f"Solve failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially accepting suboptimal or failed solves.
- Forgetting to load the solution (`load_from`) before accessing variable values in some Pyomo patterns.
- Setting solver options incorrectly (e.g., wrong parameter names for the chosen solver backend).
