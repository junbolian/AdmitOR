---
name: Sequence-Dependent Scheduling with Time Windows
description: |
  Model and solve scheduling problems with sequence-dependent separation constraints, time windows, and piecewise linear deviation penalties using either CP-SAT or MILP solvers.
---

# Workflow 1 (CP-SAT with Precedence Variables)

## Modeling stage

### Strategy Overview
This workflow models the problem using OR-Tools CP-SAT, which natively handles integer variables and logical constraints. It uses binary precedence variables to define the sequence and linearizes deviation penalties for efficient solving.

### Step 1 - Define Core Variables
- Define integer variables for the scheduled time of each entity, bounded by its earliest and latest time window.
- Create binary precedence variables for each ordered pair of entities (i < j) to indicate if one precedes the other.
- Introduce non-negative continuous or integer deviation variables to capture earliness and lateness relative to a target time.

### Step 2 - Enforce Ordering and Separation
- Enforce mutual exclusivity of precedence: for each pair (i, j), ensure exactly one ordering variable is active.
- Model sequence-dependent separation constraints using logical implications (e.g., `OnlyEnforceIf`) or a big-M formulation, linking the precedence variable to a minimum time gap.
- Optionally add transitivity constraints (e.g., `precedence[i][j] + precedence[j][k] - 1 <= precedence[i][k]`) to strengthen the model and improve solving performance.

### Step 3 - Model Deviations and Objective
- For each entity, add a constraint linking its scheduled time, target time, and deviation variables: `scheduled_time - target = late_deviation - early_deviation`.
- Define the objective as the minimization of a weighted sum of earliness and lateness penalties.

### Formulation Template
```json
{
  "sets": [
    "Entities",
    "OrderedPairs (i, j) where i < j"
  ],
  "parameters": [
    "earliest[entity]",
    "latest[entity]",
    "target[entity]",
    "separation[entity_i][entity_j]",
    "early_penalty[entity]",
    "late_penalty[entity]"
  ],
  "decision_variables": [
    "time[entity] (integer, domain: [earliest, latest])",
    "precedes[entity_i][entity_j] (boolean, for i < j)",
    "early[entity] (integer, >=0)",
    "late[entity] (integer, >=0)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_over_entities( early_penalty * early + late_penalty * late )"
  },
  "constraints": [
    "time_window: earliest <= time <= latest",
    "mutual_exclusion: precedes[i][j] + precedes[j][i] == 1 for i < j",
    "separation_logic: (time[j] >= time[i] + separation[i][j]) only if precedes[i][j]",
    "deviation_def: time - target == late - early"
  ]
}
```

### Common Pitfalls
- Using an insufficiently large big-M value for separation constraints, which can cut off valid solutions.
- Forgetting to enforce the non-negativity of deviation variables, leading to incorrect objective calculation.
- Omitting transitivity constraints, which can result in a loose model and longer solve times.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools CP-SAT solver, configuring it for a balance of speed and proof of optimality. Focus on extracting and validating the sequence and schedule from the solver's solution.

### Step 1 - Configure and Run Solver
- Instantiate the CP-SAT solver and set key parameters: a time limit (`max_time_in_seconds`), number of parallel workers (`num_search_workers`), and an optional random seed for reproducibility.
- Set the objective sense and add the model's constraints and objective to the solver.
- Call the `Solve()` method and capture the result status.

### Step 2 - Validate Solution and Extract Results
- Check the solver status for optimality or feasibility before proceeding.
- Extract the values of all decision variables (times, precedence, deviations) from the solution.
- Reconstruct the sequence by performing a topological sort on the active precedence variables.
- Run a post-solve verification function that explicitly checks all time window and separation constraints against the extracted schedule.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (create variables and constraints as per formulation)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    solution_times = {e: solver.Value(time_var[e]) for e in entities}
    # ... extract other variables
    # Verify constraints
    if verify_solution(solution_times, separation_matrix):
        print("Solution is valid.")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking solver status, leading to errors when trying to access variable values from an infeasible run.
- Assuming the solver's internal checks are sufficient; always implement independent verification of key constraints.
- Misinterpreting the precedence variables when reconstructing the order (e.g., forgetting they are defined only for i < j).

# Workflow 2 (MILP with Big-M Separation)

## Modeling stage

### Strategy Overview
This workflow formulates the problem as a Mixed-Integer Linear Program (MILP) suitable for solvers like Gurobi, CBC, or SCIP. It uses a classic big-M formulation for separation constraints and linear deviation variables.

### Step 1 - Define Variables and Bounds
- Define continuous variables for the scheduled time of each entity, with lower and upper bounds set by the time windows.
- Create binary precedence variables for all ordered pairs to represent the sequence.
- Declare non-negative continuous deviation variables for earliness and lateness.

### Step 2 - Implement Big-M Constraints
- Enforce mutual exclusivity for each pair of precedence variables.
- Formulate separation constraints using a sufficiently large big-M constant: `time[j] >= time[i] + separation[i][j] - M * (1 - precedes[i][j])`.
- Define the deviation relationship linearly: `time - target == late - early`.

### Step 3 - Assemble Objective
- Formulate the objective as a linear function: minimize the sum of weighted early and late deviations.

### Formulation Template
```json
{
  "sets": [
    "Entities",
    "OrderedPairs (i, j) where i != j"
  ],
  "parameters": [
    "earliest[entity]",
    "latest[entity]",
    "target[entity]",
    "separation[entity_i][entity_j]",
    "early_penalty[entity]",
    "late_penalty[entity]",
    "Big_M (sufficiently large constant)"
  ],
  "decision_variables": [
    "time[entity] (continuous, bounds: [earliest, latest])",
    "precedes[entity_i][entity_j] (binary, for i != j)",
    "early[entity] (continuous, >=0)",
    "late[entity] (continuous, >=0)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( early_penalty * early + late_penalty * late )"
  },
  "constraints": [
    "time_window: earliest <= time <= latest",
    "mutual_exclusion: precedes[i][j] + precedes[j][i] == 1 for i < j",
    "separation_bigM: time[j] >= time[i] + separation[i][j] - Big_M * (1 - precedes[i][j]) for all i, j, i != j",
    "deviation_linear: time - target == late - early"
  ]
}
```

### Common Pitfalls
- Choosing a Big-M value that is too small, which makes the model infeasible, or too large, which weakens the LP relaxation and slows solving.
- Defining precedence variables for both (i,j) and (j,i) but only adding mutual exclusion for i<j, leading to undefined variable errors.
- Using non-linear functions (like absolute value) for deviations instead of the linear decomposition.

## Solving stage

### Strategy Overview
Solve the MILP using a traditional MIP solver via an interface like Pyomo or directly with a solver API. Configure for optimality, handle solver statuses carefully, and implement robust solution extraction.

### Step 1 - Configure Solver and Solve
- Instantiate the solver (e.g., Gurobi, CBC) through the chosen modeling interface.
- Set solver parameters: a time limit (`TimeLimit`), optimality gap tolerance (`MIPGap`), thread count (`Threads`), and a seed (`Seed`) for reproducibility.
- Invoke the solver and capture the termination condition and status.

### Step 2 - Process Results and Verify
- Check if the termination condition is `optimal` or `feasible` before extracting results.
- Retrieve variable values. Derive the sequence by identifying active precedence variables (`precedes[i][j] > 0.5`).
- Compute the objective value from the extracted deviations as an independent check.
- Validate the solution by ensuring all separation and time window constraints hold within a small numerical tolerance.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (define sets, parameters, variables, constraints, objective as per formulation)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi') # or 'cbc', 'scip'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Extract solution
    solution_times = {e: pyo.value(model.time[e]) for e in model.entities}
    # ... extract other variables
    # Post-solve verification
    if verify_solution_milp(solution_times, separation_data):
        print("Valid solution found.")
else:
    print("Solver did not return a feasible solution.")
```

### Common Pitfalls
- Confusing solver `status` with `termination_condition`; both must be checked to understand the result.
- Not accounting for solver tolerances when checking binary variable values (e.g., using `> 0.5` instead of `== 1`).
- Failing to load the solution into the model object before accessing variable values in some interfaces.
