---
name: Binary Selection with Implied Coverage
description: |
  Model and solve binary selection problems with budget constraints and coverage implications to maximize weighted coverage.

---

# Workflow 1 (CP-SAT with Explicit Implication)

## Modeling stage

### Strategy Overview
This workflow uses OR-Tools CP-SAT to model binary selection and coverage with explicit forward and reverse logical implication constraints, ensuring a precise one-to-one relationship between selection and coverage states.

### Step 1 - Define Binary Variables
- Create a binary decision variable for each selectable resource (e.g., `x_i`).
- Create a separate auxiliary binary variable for each coverage state to be implied (e.g., `y_j`).

### Step 2 - Enforce Budget Constraint
- Formulate a linear constraint summing the cost of selected resources, ensuring the total does not exceed a given budget limit.

### Step 3 - Model Coverage Implications
- For each coverage state, add a forward implication constraint: `y_j >= x_i` for every resource `i` that can cause coverage `j`.
- For each coverage state, add a reverse implication constraint: `y_j <= sum(x_i for i in covering_resources[j])`.

### Step 4 - Formulate Weighted Objective
- Define the objective as maximizing the sum of each coverage variable multiplied by its associated weight.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of selectable resources"},
    {"name": "J", "description": "Set of coverage states"}
  ],
  "parameters": [
    {"name": "cost_i", "set": "I", "description": "Cost of selecting resource i"},
    {"name": "weight_j", "set": "J", "description": "Weight (benefit) of achieving coverage state j"},
    {"name": "budget", "description": "Total available budget"},
    {"name": "covers_j", "set": "J", "description": "List of resource indices in I that can achieve coverage state j"}
  ],
  "decision_variables": [
    {"name": "x", "set": "I", "type": "binary", "description": "1 if resource i is selected"},
    {"name": "y", "set": "J", "type": "binary", "description": "1 if coverage state j is achieved"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight_j[j] * y[j] for j in J)"
  },
  "constraints": [
    {"name": "budget_limit", "expression": "sum(cost_i[i] * x[i] for i in I) <= budget"},
    {"name": "coverage_forward", "set": "J", "expression": "For each j in J, for each i in covers_j[j]: y[j] >= x[i]"},
    {"name": "coverage_reverse", "set": "J", "expression": "For each j in J: y[j] <= sum(x[i] for i in covers_j[j])"}
  ]
}
```

### Common Pitfalls
- Omitting the reverse implication constraint, which incorrectly allows coverage to be 1 even when no covering resource is selected.
- Using a single `y_j == sum(...)` constraint, which is too restrictive and may prevent valid selections if a resource covers multiple states.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, configuring it for performance and reproducibility, and carefully extracting and interpreting results.

### Step 1 - Instantiate Model and Variables
- Create a `CpModel` object.
- Instantiate binary variables using `NewBoolVar`.

### Step 2 - Add Constraints and Objective
- Add the budget constraint as a linear inequality using `Add`.
- Add the forward and reverse implication constraints using loops over coverage mappings.
- Set the objective using `Maximize`.

### Step 3 - Configure and Run Solver
- Create a `CpSolver` and set key parameters: time limit, number of parallel workers, random seed, and optimality gap.
- Execute the solver and capture the status.

### Step 4 - Extract and Validate Solution
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- Retrieve variable values using `solver.Value()`.
- Compute derived metrics like total cost and achieved coverage.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()

# Variable creation
x = [model.NewBoolVar(f"x_{i}") for i in range(num_resources)]
y = [model.NewBoolVar(f"y_{j}") for j in range(num_coverage_states)]

# Budget constraint
model.Add(sum(cost[i] * x[i] for i in range(num_resources)) <= budget)

# Coverage implication constraints
for j in range(num_coverage_states):
    for i in coverage_map[j]:  # coverage_map[j] = list of resource indices covering state j
        model.Add(y[j] >= x[i])
    model.Add(y[j] <= sum(x[i] for i in coverage_map[j]))

# Objective
model.Maximize(sum(weight[j] * y[j] for j in range(num_coverage_states)))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    selected_resources = [i for i in range(num_resources) if solver.Value(x[i])]
    covered_states = [j for j in range(num_coverage_states) if solver.Value(y[j])]
    total_cost = sum(cost[i] * solver.Value(x[i]) for i in range(num_resources))
    objective_value = solver.ObjectiveValue()
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not setting a random seed, leading to non-reproducible results.
- Forgetting to check for `FEASIBLE` status when optimality is not guaranteed, causing solution extraction to fail.
- Misinterpreting variable values (they are 0 or 1, no tolerance needed).

# Workflow 2 (Pyomo with Implicit Implication)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to model the problem with a single, implicit coverage implication constraint per state, leveraging the objective to drive coverage variables to 1 when feasible, suitable for MIP solvers like Gurobi or HiGHS.

### Step 1 - Define Binary Variables
- Create a Pyomo `Var` with `within=Binary` for each selectable resource.
- Create a separate Pyomo `Var` with `within=Binary` for each coverage state.

### Step 2 - Enforce Budget Constraint
- Formulate a linear budget constraint using a `Constraint` rule summing `cost * resource_var`.

### Step 3 - Model Coverage Implications
- For each coverage state, add a single constraint: `coverage_var <= sum(resource_var for resource in covering_set)`.
- This allows the objective to maximize the coverage variable, but prevents it from being 1 unless at least one covering resource is selected.

### Step 4 - Formulate Weighted Objective
- Define a Pyomo `Objective` rule to maximize the sum of `weight * coverage_var`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of selectable resources"},
    {"name": "J", "description": "Set of coverage states"}
  ],
  "parameters": [
    {"name": "cost_i", "set": "I", "description": "Cost of selecting resource i"},
    {"name": "weight_j", "set": "J", "description": "Weight (benefit) of achieving coverage state j"},
    {"name": "budget", "description": "Total available budget"},
    {"name": "covers_j", "set": "J", "description": "List of resource indices in I that can achieve coverage state j"}
  ],
  "decision_variables": [
    {"name": "x", "set": "I", "type": "binary", "description": "1 if resource i is selected"},
    {"name": "y", "set": "J", "type": "binary", "description": "1 if coverage state j is achieved"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(weight_j[j] * y[j] for j in J)"
  },
  "constraints": [
    {"name": "budget_limit", "expression": "sum(cost_i[i] * x[i] for i in I) <= budget"},
    {"name": "coverage_implication", "set": "J", "expression": "For each j in J: y[j] <= sum(x[i] for i in covers_j[j])"}
  ]
}
```

### Common Pitfalls
- Using `y[j] == sum(...)` which over-constrains the model and may eliminate optimal solutions where a selected resource covers multiple states.
- Forgetting that the objective must actively maximize `y[j]`; without this, `y[j]` may remain 0 even when coverage is possible.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver via the SolverFactory interface, with careful handling of solver status, termination conditions, and solution loading.

### Step 1 - Build Model and Select Solver
- Construct the Pyomo `ConcreteModel` with sets, variables, constraints, and objective.
- Instantiate a solver using `SolverFactory('solver_name')`.

### Step 2 - Configure Solver Options
- Set solver-specific options such as time limit, optimality gap (`MIPGap` or `mip_rel_gap`), and random seed for reproducibility.

### Step 3 - Solve and Check Status
- Execute the solve with `load_solutions=False` to prevent automatic loading on failure.
- Check the solver status (`SolverStatus.ok`) and termination condition (`optimal` or `feasible`).

### Step 4 - Load and Extract Solution
- If the solve was successful, load the solution into the model.
- Extract selected resources and covered states by checking variable values with a numerical tolerance (e.g., `> 0.5`).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()

model.I = pyo.Set(initialize=range(num_resources))
model.J = pyo.Set(initialize=range(num_coverage_states))

model.x = pyo.Var(model.I, within=pyo.Binary)
model.y = pyo.Var(model.J, within=pyo.Binary)

def budget_rule(m):
    return sum(cost[i] * m.x[i] for i in m.I) <= budget
model.budget_con = pyo.Constraint(rule=budget_rule)

def coverage_rule(m, j):
    return m.y[j] <= sum(m.x[i] for i in coverage_map[j])
model.coverage_con = pyo.Constraint(model.J, rule=coverage_rule)

def obj_rule(m):
    return sum(weight[j] * m.y[j] for j in m.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'highs'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Seed'] = 42

results = solver.solve(model, load_solutions=False)

if results.solver.status == pyo.SolverStatus.ok:
    term_cond = results.solver.termination_condition
    if term_cond in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
        model.solutions.load_from(results)
        selected_resources = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
        covered_states = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
        total_cost = sum(cost[i] * pyo.value(model.x[i]) for i in selected_resources)
        objective_value = pyo.value(model.obj)
    else:
        print(f"Solver terminated with condition: {term_cond}")
else:
    print("Solver failed.")
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) without checking termination condition, which can lead to errors or incorrect values.
- Using a strict `== 1.0` check for binary variables, ignoring solver numerical tolerances.
- Not setting a time limit or optimality gap, potentially causing excessively long runtimes.
