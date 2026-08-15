---
name: Resource Assignment Optimizer
description: |
  Model and solve linear resource assignment problems with capacity, demand, and per-assignment limits to minimize total cost.
---

# Workflow 1 (LP with Google OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as a continuous linear program using a bipartite graph structure. Variables represent assignment amounts, with bounds derived from the tightest of source capacity, destination demand, and per-assignment limits.

### Step 1 - Define Problem Data
- Define index sets for `sources` (resources) and `destinations` (demands).
- Create parameter arrays for `availability` (source capacity), `requirement` (destination demand), `cost` (per-unit assignment cost), and optional `assignment_limit` (per-pair maximum).
- Use dictionaries or 2D lists for structured data access.

### Step 2 - Create Decision Variables
- Create a continuous, non-negative decision variable `x[i][j]` for each source-destination pair.
- Compute the variable's upper bound as `min(availability[i], requirement[j], assignment_limit[i][j])` to embed feasibility.
- Use `solver.NumVar(lb, ub, name)` for variable creation.

### Step 3 - Formulate Constraints
- **Source Capacity**: For each source `i`, `sum(x[i][j] for j in destinations) <= availability[i]`.
- **Demand Satisfaction**: For each destination `j`, `sum(x[i][j] for i in sources) == requirement[j]` (equality ensures exact fulfillment).
- Per-assignment limits are enforced via variable bounds, not separate constraints.

### Step 4 - Define Objective
- Formulate a linear objective: `sum(cost[i][j] * x[i][j] for all i, j)`.
- Set the sense to minimization.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "availability", "index": "sources", "type": "float"},
    {"name": "requirement", "index": "destinations", "type": "float"},
    {"name": "cost", "index": ["sources", "destinations"], "type": "float"},
    {"name": "assignment_limit", "index": ["sources", "destinations"], "type": "float", "optional": true}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in sources for j in destinations)"
  },
  "constraints": [
    {"name": "source_capacity", "index": "sources", "expression": "sum(x[i][j] for j in destinations) <= availability[i]"},
    {"name": "demand_satisfaction", "index": "destinations", "expression": "sum(x[i][j] for i in sources) == requirement[j]"}
  ]
}
```

### Common Pitfalls
- Omitting per-assignment limits in variable bounds, leading to infeasible solutions.
- Using inequality (`<=`) for demand constraints when exact fulfillment is required.
- Not providing a default value (e.g., a large number) for optional `assignment_limit` parameters.

## Solving stage

### Strategy Overview
Use Google OR-Tools' linear solver wrapper (`pywraplp`) with the GLOP backend for pure LP problems. Focus on robust status checking and solution validation.

### Step 1 - Initialize Solver
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- For problems requiring integer variables, use `'CBC'` or `'SCIP'` instead.

### Step 2 - Build and Solve Model
- Instantiate variables and constraints as defined in the modeling stage.
- Set the objective and call `status = solver.Solve()`.
- Configure solver options (e.g., time limit) if needed: `solver.SetTimeLimit(ms)`.

### Step 3 - Check Solution Status
- Check if `status` is `solver.OPTIMAL` or `solver.FEASIBLE` before extracting results.
- If status indicates infeasibility or unboundedness, output a structured error message instead of variable values.

### Step 4 - Extract and Verify Solution
- Retrieve the objective value: `total_cost = solver.Objective().Value()`.
- Iterate through variables with `x[i,j].solution_value() > tolerance` to report assignments.
- Programmatically verify all constraints by summing the solution values and comparing to parameters within a tolerance (e.g., 1e-6).

### Code Usage
```python
import pywraplp

def solve_assignment_lp(sources, destinations, availability, requirement, cost, assignment_limit=None):
    solver = pywraplp.Solver.CreateSolver('GLOP')
    # 1. Create variables with bounds
    x = {}
    for i in sources:
        for j in destinations:
            ub = availability[i]
            if assignment_limit is not None:
                ub = min(ub, assignment_limit[i][j])
            ub = min(ub, requirement[j])
            x[i, j] = solver.NumVar(0.0, ub, f'x_{i}_{j}')
    # 2. Add constraints
    for i in sources:
        solver.Add(sum(x[i, j] for j in destinations) <= availability[i])
    for j in destinations:
        solver.Add(sum(x[i, j] for i in sources) == requirement[j])
    # 3. Set objective
    objective = solver.Objective()
    for i in sources:
        for j in destinations:
            objective.SetCoefficient(x[i, j], cost[i][j])
    objective.SetMinimization()
    # 4. Solve and check status
    status = solver.Solve()
    if status in (solver.OPTIMAL, solver.FEASIBLE):
        total_cost = objective.Value()
        # Optional: Verify constraints
        print(f'RESULT:{total_cost}')
        return total_cost, {(i,j): x[i,j].solution_value() for i in sources for j in destinations if x[i,j].solution_value() > 1e-6}
    else:
        error_info = {'status': solver.StatusName(status)}
        print(f'RESULT_JSON:{error_info}')
        return None, None
```

### Common Pitfalls
- Trusting a non-`OPTIMAL`/`FEASIBLE` status and attempting to extract variable values.
- Not using a tolerance when checking for non-zero assignments, leading to floating-point representation issues.
- Forgetting to set the objective sense to minimization.

# Workflow 2 (LP/MIP with Pyomo and HiGHS)

## Modeling stage

### Strategy Overview
Model the assignment problem using Pyomo's abstract or concrete model syntax, separating data from structure. Leverage `pyomo.environ` for clear constraint rules and use `NonNegativeReals` for continuous variables.

### Step 1 - Declare Model and Sets
- Create a `ConcreteModel()` or `AbstractModel()`.
- Define `model.sources` and `model.destinations` as `Set()` components.
- Use `Param()` components to declare `availability`, `requirement`, `cost`, and `assignment_limit`.

### Step 2 - Define Decision Variables
- Create a `Var` indexed over `model.sources * model.destinations` with domain `NonNegativeReals`.
- Optionally set variable bounds via a rule function that returns `(lb, ub)` using the same `min` logic as Workflow 1.

### Step 3 - Write Constraint Rules
- Define a rule for source capacity: `sum(model.x[i,j] for j in model.destinations) <= model.availability[i]`.
- Define a rule for demand satisfaction: `sum(model.x[i,j] for i in model.sources) == model.requirement[j]`.
- Implement each rule as a function returning the constraint expression.

### Step 4 - Construct Objective
- Define the objective using `Objective(expr=sum(model.cost[i,j] * model.x[i,j] for i,j in model.sources*model.destinations), sense=minimize)`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    {"name": "availability", "index": "sources", "type": "float"},
    {"name": "requirement", "index": "destinations", "type": "float"},
    {"name": "cost", "index": ["sources", "destinations"], "type": "float"},
    {"name": "assignment_limit", "index": ["sources", "destinations"], "type": "float", "optional": true}
  ],
  "decision_variables": [
    {"name": "x", "index": ["sources", "destinations"], "type": "continuous", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "minimize",
    "expression": "sum(cost[i,j] * x[i,j] for i in sources for j in destinations)"
  },
  "constraints": [
    {"name": "source_capacity", "index": "sources", "rule": "sum(x[i,j] for j in destinations) <= availability[i]"},
    {"name": "demand_satisfaction", "index": "destinations", "rule": "sum(x[i,j] for i in sources) == requirement[j]"}
  ]
}
```

### Common Pitfalls
- Using `AbstractModel` without properly initializing data before instantiation.
- Defining constraint rules that reference model components incorrectly (e.g., missing index arguments).
- Not specifying `sense=minimize` in the objective, defaulting to minimization but risking ambiguity.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver via the `appsi` interface or `solvers` module. Configure solver options for performance and rigorously check termination conditions.

### Step 1 - Select and Configure Solver
- Use `SolverFactory('appsi_highs')` or `SolverFactory('highs')`.
- Set solver options: `opt.options['time_limit'] = 30`, `opt.options['mip_rel_gap'] = -1` (for exact LP solve).

### Step 2 - Solve and Load Solution
- Call `results = opt.solve(model, tee=False)`.
- Use `load_solutions=False` and then `model.solutions.load_from(results)` for explicit control.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Validate and Report Solution
- Access the objective value: `model.obj.expr()` or `value(model.obj)`.
- Iterate through `model.x` to extract variable values where `value(model.x[i,j]) > tolerance`.
- Programmatically verify all constraints by evaluating the left-hand side against the right-hand side with tolerance.

### Code Usage
```python
from pyomo.environ import ConcreteModel, Set, Param, Var, NonNegativeReals, Objective, Constraint, SolverFactory, value, minimize
import pyomo.environ as pyo

def solve_assignment_pyomo(sources, destinations, availability, requirement, cost, assignment_limit=None):
    model = ConcreteModel()
    # 1. Sets and Parameters
    model.sources = Set(initialize=sources)
    model.destinations = Set(initialize=destinations)
    model.availability = Param(model.sources, initialize=availability)
    model.requirement = Param(model.destinations, initialize=requirement)
    model.cost = Param(model.sources, model.destinations, initialize=cost)
    if assignment_limit is not None:
        model.assignment_limit = Param(model.sources, model.destinations, initialize=assignment_limit)
    # 2. Variables with bound rule
    def x_bounds(m, i, j):
        ub = m.availability[i]
        if hasattr(m, 'assignment_limit'):
            ub = min(ub, m.assignment_limit[i, j])
        ub = min(ub, m.requirement[j])
        return (0, ub)
    model.x = Var(model.sources, model.destinations, bounds=x_bounds, domain=NonNegativeReals)
    # 3. Constraints
    def source_capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.destinations) <= m.availability[i]
    model.source_cap = Constraint(model.sources, rule=source_capacity_rule)
    def demand_satisfaction_rule(m, j):
        return sum(m.x[i, j] for i in m.sources) == m.requirement[j]
    model.demand_sat = Constraint(model.destinations, rule=demand_satisfaction_rule)
    # 4. Objective
    model.obj = Objective(expr=sum(m.cost[i, j] * m.x[i, j] for i in m.sources for j in m.destinations), sense=minimize)
    # 5. Solve
    solver = SolverFactory('appsi_highs')
    solver.options['time_limit'] = 30
    results = solver.solve(model, load_solutions=False)
    if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
        model.solutions.load_from(results)
        total_cost = value(model.obj)
        # Optional: Verify constraints
        print(f'RESULT:{total_cost}')
        return total_cost, {(i,j): value(model.x[i,j]) for i in model.sources for j in model.destinations if value(model.x[i,j]) > 1e-6}
    else:
        error_info = {'status': str(results.solver.status), 'termination_condition': str(results.solver.termination_condition)}
        print(f'RESULT_JSON:{error_info}')
        return None, None
```

### Common Pitfalls
- Assuming `load_solutions=True` always works; explicit load is more robust.
- Checking only `solver.status` without verifying `termination_condition`.
- Not using `value()` to extract numeric values from Pyomo components post-solve.
