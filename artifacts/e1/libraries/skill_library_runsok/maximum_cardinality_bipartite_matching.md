---
name: Maximum Cardinality Bipartite Matching
description: |
  Model and solve one-to-one assignment problems between two disjoint sets with binary preference restrictions to maximize the number of matches.
---

# Workflow 1 (MILP with Pyomo/Highs)

## Modeling stage

### Strategy Overview
Formulate the matching problem as a Mixed-Integer Linear Program (MILP) using binary assignment variables, linear constraints for one-to-one matching and preference compatibility, and a linear objective to maximize total assignments.

### Step 1 - Define Sets and Parameters
- Identify the two disjoint sets (e.g., `SetA`, `SetB`) and their elements.
- Define a binary parameter `compatible[a][b]` (or `preference[a][b]`) indicating allowed assignments (1) and prohibited assignments (0).

### Step 2 - Create Binary Assignment Variables
- Create a binary decision variable `assign[a][b]` for each potential pair `(a,b)` between the two sets, where `assign[a][b] = 1` indicates a match.

### Step 3 - Enforce One-to-One Matching Constraints
- Add a constraint for each element `a` in `SetA`: `sum(assign[a][b] for b in SetB) <= 1`.
- Add a constraint for each element `b` in `SetB`: `sum(assign[a][b] for a in SetA) <= 1`.

### Step 4 - Enforce Preference Compatibility
- Add a constraint for each pair `(a,b)`: `assign[a][b] <= compatible[a][b]`. This forces `assign[a][b]` to 0 where `compatible[a][b]` is 0.

### Step 5 - Define the Maximization Objective
- Set the objective to maximize the sum of all assignment variables: `maximize sum(assign[a][b] for a in SetA for b in SetB)`.

### Formulation Template
```json
{
  "sets": ["SetA", "SetB"],
  "parameters": [
    {
      "name": "compatible",
      "domain": ["SetA", "SetB"],
      "type": "binary",
      "description": "1 if assignment is allowed, 0 otherwise."
    }
  ],
  "decision_variables": [
    {
      "name": "assign",
      "domain": ["SetA", "SetB"],
      "type": "binary",
      "description": "1 if element a from SetA is matched to element b from SetB."
    }
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(assign[a][b] for a in SetA for b in SetB)"
  },
  "constraints": [
    "sum(assign[a][b] for b in SetB) <= 1 for all a in SetA",
    "sum(assign[a][b] for a in SetA) <= 1 for all b in SetB",
    "assign[a][b] <= compatible[a][b] for all a in SetA, b in SetB"
  ]
}
```

### Common Pitfalls
- Forgetting to validate that the `compatible` parameter contains only 0/1 values, which can cause solver errors.
- Creating assignment variables for all possible pairs instead of using the `compatible` constraint to handle sparsity, which can lead to unnecessary model bloat.
- Using strict equality (`==`) for the one-to-one constraints, which incorrectly prohibits unmatched elements.

## Solving stage

### Strategy Overview
Solve the MILP using the Highs solver via Pyomo, configuring for exact solutions, and implement robust status checking and solution extraction.

### Step 1 - Configure the Solver
- Instantiate the solver: `solver = SolverFactory('highs')`.
- Set key parameters: `time_limit` for runtime control, `mip_rel_gap=0.0` for exact optimality, and `threads` for parallel processing.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `TerminationCondition.feasible`).

### Step 3 - Extract and Validate the Solution
- If the solve was successful, compute the objective value: `float(pyo.value(model.obj))`.
- Extract the list of matches by iterating over variables: `[(a, b) for a in model.SetA for b in model.SetB if pyo.value(model.assign[a, b]) > 0.5]`.
- Optionally, verify that the solution respects all constraints (each element appears at most once, all matches are compatible).

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (using sets, parameters, variables, constraints as defined)
model = pyo.ConcreteModel()
# ... (model construction code) ...

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1.0  # Disable relative gap
solver.options['threads'] = 4

results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == pyo.SolverStatus.ok and term in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    assignments = [(a, b) for a in model.SetA for b in model.SetB if pyo.value(model.assign[a, b]) > 0.5]
    print(f"Optimal matches: {len(assignments)}")
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Only checking the solver status and not the termination condition, potentially accepting infeasible or unbounded results.
- Using a loose tolerance (e.g., `> 0`) instead of `> 0.5` to extract binary variable values, which can be unsafe with solver tolerances.
- Not setting a `time_limit` for larger instances, risking excessive runtime.

# Workflow 2 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Model the problem using the OR-Tools CP-SAT solver's native Boolean variables and constraints, directly encoding the one-to-one matching and preference restrictions.

### Step 1 - Define Data Structures
- Define the two sets as lists or ranges (e.g., `set_a`, `set_b`).
- Define the binary compatibility matrix `allowed[a][b]` (or a set of allowed pairs).

### Step 2 - Create Boolean Variables
- Create a Boolean variable `x[a][b]` for each potential pair `(a,b)` using `model.NewBoolVar(f'x_{a}_{b}')`.

### Step 3 - Add One-to-One Matching Constraints
- For each `a` in `set_a`, add a linear constraint: `sum(x[a][b] for b in set_b) <= 1`.
- For each `b` in `set_b`, add a linear constraint: `sum(x[a][b] for a in set_a) <= 1`.

### Step 4 - Add Preference Constraints
- For each pair `(a,b)`, if `allowed[a][b]` is 0, add the constraint `x[a][b] == 0`. This can be done efficiently by iterating over a precomputed set of disallowed pairs.

### Step 5 - Set Maximization Objective
- Set the objective to maximize the sum of all Boolean variables: `model.Maximize(sum(x[a][b] for a in set_a for b in set_b))`.

### Formulation Template
```json
{
  "sets": ["set_a", "set_b"],
  "parameters": [
    {
      "name": "allowed",
      "domain": ["set_a", "set_b"],
      "type": "binary",
      "description": "1 if assignment is allowed, 0 otherwise."
    }
  ],
  "decision_variables": [
    {
      "name": "x",
      "domain": ["set_a", "set_b"],
      "type": "boolean",
      "description": "True if element a from set_a is matched to element b from set_b."
    }
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(x[a][b] for a in set_a for b in set_b)"
  },
  "constraints": [
    "sum(x[a][b] for b in set_b) <= 1 for all a in set_a",
    "sum(x[a][b] for a in set_a) <= 1 for all b in set_b",
    "x[a][b] == 0 for all (a,b) where allowed[a][b] == 0"
  ]
}
```

### Common Pitfalls
- Adding the preference constraint as `x[a][b] <= allowed[a][b]` is less efficient in CP-SAT than explicitly fixing variables to 0 for disallowed pairs.
- Not precomputing the set of disallowed pairs, leading to inefficient constraint addition loops over all possible pairs.
- Using the same variable name `x` for both the dictionary and the variable object, causing shadowing issues.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, configured for deterministic performance and parallel search, with careful solution extraction.

### Step 1 - Configure the Solver
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set parameters: `max_time_in_seconds` for time limit, `num_search_workers` for parallelism (e.g., -1 for all cores), `random_seed` for reproducibility, and `relative_gap_limit = 0.0` for exact solutions.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`.

### Step 3 - Extract and Verify the Solution
- If the solve was successful, extract the objective value: `solver.ObjectiveValue()`.
- Extract the list of matches: `[(a, b) for (a, b), var in x.items() if solver.Value(var) == 1]`.
- Optionally, verify the solution against the original constraints for correctness.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
set_a = range(num_a)
set_b = range(num_b)
allowed = ...  # binary matrix

x = {}
for a in set_a:
    for b in set_b:
        x[(a, b)] = model.NewBoolVar(f'x_{a}_{b}')

# One-to-one constraints
for a in set_a:
    model.Add(sum(x[(a, b)] for b in set_b) <= 1)
for b in set_b:
    model.Add(sum(x[(a, b)] for a in set_a) <= 1)

# Preference constraints
for a in set_a:
    for b in set_b:
        if allowed[a][b] == 0:
            model.Add(x[(a, b)] == 0)

model.Maximize(sum(x.values()))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = -1
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    objective_value = solver.ObjectiveValue()
    assignments = [(a, b) for (a, b), var in x.items() if solver.Value(var) == 1]
    print(f"Optimal matches: {len(assignments)}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Misinterpreting the solver status (e.g., `cp_model.UNKNOWN` as a success).
- Not setting a `random_seed`, leading to non-reproducible results across runs.
- Forgetting to set `relative_gap_limit = 0.0` and accepting suboptimal solutions for problems requiring exact optimality.
