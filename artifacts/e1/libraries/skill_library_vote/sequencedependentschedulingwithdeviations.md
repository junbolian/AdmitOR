---
name: SequenceDependentSchedulingWithDeviations
description: |
  Model and solve scheduling problems with sequence-dependent separation constraints, time windows, and linear penalties for deviations from target times using either CP-SAT or MILP solvers.
---

# Workflow 1 (CP-SAT with Precedence Variables)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Constraint Programming (CP) or Mixed-Integer Programming (MIP) model using OR-Tools' CP-SAT solver. It employs binary precedence variables to define a total order and uses big-M constraints to enforce sequence-dependent separations. Linear deviation variables handle early/late penalties.

### Step 1 - Define Core Variables
- Define integer decision variables for the scheduled time of each entity, bounded by its earliest and latest time window.
- Create binary decision variables for each ordered pair of entities to indicate precedence (1 if i precedes j).
- Create non-negative integer or continuous variables to capture early and late deviation from each entity's target time.

### Step 2 - Enforce Ordering Logic
- Add mutual exclusivity constraints: for each pair (i, j) with i < j, enforce that exactly one precedence variable is 1 (e.g., `precedes[i][j] + precedes[j][i] == 1`).
- Optionally add transitivity constraints to strengthen the linear relaxation and ensure a total order: for all distinct i, j, k, `precedes[i][j] + precedes[j][k] - 1 <= precedes[i][k]`.

### Step 3 - Model Separation Constraints
- For each ordered pair (i, j), add a big-M constraint: `time[j] >= time[i] + separation[i][j] - M * (1 - precedes[i][j])`. The big-M value must be sufficiently large (e.g., `max_latest - min_earliest + max_separation`).

### Step 4 - Linearize Deviation Penalties
- For each entity, add a constraint linking its time, target, and deviation variables: `time[i] - target[i] == late_dev[i] - early_dev[i]`.
- Bound the deviation variables appropriately: `early_dev[i] <= target[i] - earliest[i]` and `late_dev[i] <= latest[i] - target[i]`.

### Step 5 - Formulate Objective
- Define the objective to minimize the total weighted deviation: `minimize sum(early_penalty[i] * early_dev[i] + late_penalty[i] * late_dev[i])`.

### Formulation Template
```json
{
  "sets": [
    "Entities"
  ],
  "parameters": [
    {"name": "earliest", "type": "int", "index": "i"},
    {"name": "latest", "type": "int", "index": "i"},
    {"name": "target", "type": "int", "index": "i"},
    {"name": "separation", "type": "int", "index": ["i", "j"]},
    {"name": "early_penalty", "type": "float", "index": "i"},
    {"name": "late_penalty", "type": "float", "index": "i"},
    {"name": "big_M", "type": "int"}
  ],
  "decision_variables": [
    {"name": "time", "type": "int", "index": "i", "domain": "[earliest_i, latest_i]"},
    {"name": "precedes", "type": "binary", "index": ["i", "j"], "domain": "{0,1}"},
    {"name": "early_dev", "type": "int", "index": "i", "domain": "[0, target_i - earliest_i]"},
    {"name": "late_dev", "type": "int", "index": "i", "domain": "[0, latest_i - target_i]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_i (early_penalty_i * early_dev_i + late_penalty_i * late_dev_i)"
  },
  "constraints": [
    "mutual_exclusion: for i<j, precedes[i][j] + precedes[j][i] == 1",
    "transitivity (optional): for distinct i,j,k, precedes[i][j] + precedes[j][k] - 1 <= precedes[i][k]",
    "separation: for all i,j, time[j] >= time[i] + separation[i][j] - big_M * (1 - precedes[i][j])",
    "deviation_def: for all i, time[i] - target[i] == late_dev[i] - early_dev[i]"
  ]
}
```

### Common Pitfalls
- Using an insufficiently large big-M value, which can cut off feasible solutions. Calculate it based on problem data extremes.
- Forgetting to bound deviation variables, which can lead to unbounded subproblems or excessive search.
- Omitting transitivity constraints in models requiring a strict total order, which can allow cycles in the precedence graph.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' CP-SAT solver, which handles integer variables and logical constraints efficiently. Configure solver parameters for performance and reliability, extract the solution, and perform post-solve verification.

### Step 1 - Configure Solver Parameters
- Set a time limit (`max_time_in_seconds`) appropriate for the problem size.
- Enable parallel search (`num_search_workers`) to utilize multiple CPU cores.
- Set a random seed for reproducibility.
- For exact solutions, set `relative_gap_limit` to 0.0.

### Step 2 - Solve and Check Status
- Invoke the solver and capture the status result.
- Check if the status is `OPTIMAL` or `FEASIBLE` before attempting to access solution values. If `INFEASIBLE` or `UNKNOWN`, terminate gracefully with an informative message.

### Step 3 - Extract and Interpret Solution
- Retrieve the values for the time variables.
- Determine the final sequence by sorting entities based on their solved time values.
- Retrieve values for deviation variables to calculate the total penalty.

### Step 4 - Post-Solve Verification
- Implement a verification function that independently checks all constraints: time windows, separation for the extracted order, and deviation calculations.
- Use a small tolerance (e.g., 1e-5) for numerical comparisons due to solver precision.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract solution values
    solution_times = {i: solver.Value(time_var[i]) for i in entities}
    # ... extract other variables
    # Verify constraints
    if verify_solution(solution_times, ...):
        print("Solution verified.")
    else:
        print("Solution failed verification.")
else:
    print(f"Solver finished with status: {status}. No solution found.")
```

### Common Pitfalls
- Accessing solution values without checking solver status, leading to runtime errors.
- Relying solely on solver-reported feasibility; always implement independent verification for critical applications.
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.

# Workflow 2 (MILP with Pyomo and Commercial Solver)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract modeling capabilities. It uses binary precedence variables and big-M constraints, then solves with a commercial solver like Gurobi or an open-source alternative like SCIP via a unified interface.

### Step 1 - Define Abstract Sets and Parameters
- Declare an abstract set for the entities.
- Define all necessary parameters (earliest, latest, target, separation, penalties) as Pyomo `Param` components indexed by the entity set or pairs.

### Step 2 - Create Decision Variables
- Create continuous variables for landing times, bounded by the time window parameters.
- Create binary variables for each ordered pair to indicate precedence.
- Create non-negative continuous variables for early and late deviations.

### Step 3 - Build Constraints
- Add mutual exclusion constraints for each pair of precedence variables.
- Add big-M separation constraints for all ordered pairs.
- Add constraints defining the relationship between time, target, and deviation variables.
- (Optional) Add transitivity constraints to strengthen the formulation.

### Step 4 - Define the Objective
- Define the objective function as the minimization of the total weighted deviation.

### Formulation Template
```json
{
  "sets": [
    "Entities"
  ],
  "parameters": [
    {"name": "earliest", "type": "float", "index": "i"},
    {"name": "latest", "type": "float", "index": "i"},
    {"name": "target", "type": "float", "index": "i"},
    {"name": "separation", "type": "float", "index": ["i", "j"]},
    {"name": "early_penalty", "type": "float", "index": "i"},
    {"name": "late_penalty", "type": "float", "index": "i"},
    {"name": "big_M", "type": "float"}
  ],
  "decision_variables": [
    {"name": "time", "type": "continuous", "index": "i", "bounds": "[earliest_i, latest_i]"},
    {"name": "precedes", "type": "binary", "index": ["i", "j"]},
    {"name": "early_dev", "type": "continuous", "index": "i", "bounds": "[0, target_i - earliest_i]"},
    {"name": "late_dev", "type": "continuous", "index": "i", "bounds": "[0, latest_i - target_i]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_i (early_penalty_i * early_dev_i + late_penalty_i * late_dev_i)"
  },
  "constraints": [
    "mutual_exclusion: for i<j, precedes[i,j] + precedes[j,i] == 1",
    "separation: for all i,j, time[j] >= time[i] + separation[i,j] - big_M * (1 - precedes[i,j])",
    "deviation_def: for all i, time[i] - target[i] == late_dev[i] - early_dev[i]"
  ]
}
```

### Common Pitfalls
- Using the same big-M value for all constraints without considering the specific maximum possible time difference, which can weaken the LP relaxation.
- Defining deviation variables without upper bounds, which can lead to numerical issues or unbounded subproblems in the solver.
- Incorrectly indexing parameters or variables in Pyomo rules, leading to model construction errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver backend (e.g., Gurobi, CPLEX, SCIP). Configure solver-specific parameters for optimality and performance, handle solver termination statuses rigorously, and extract the solution for validation and reporting.

### Step 1 - Select and Configure Solver
- Instantiate the solver via `SolverFactory('solver_name')`.
- Set solver parameters: `TimeLimit` for runtime control, `MIPGap` to 0.0 for exact optimality, `Threads` for parallelism, and `Seed` for reproducibility.

### Step 2 - Solve and Interrogate Results
- Execute the solve command (`solver.solve(model, tee=False)`).
- Check the solver status (`solver.status`) and termination condition (`solver.termination_condition`). Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Extract Solution and Order
- Access variable values using `model.variable[index].value`.
- Determine the sequence by sorting entities based on their solved time values.
- Calculate the total penalty from the deviation variables.

### Step 4 - Validate and Report
- Pass the extracted times and order to a verification function that checks all constraints against the original problem data.
- Structure the output (e.g., sequence list, times, deviations) in a reusable format like JSON.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.entities = pyo.Set(initialize=entity_list)
# ... (define parameters, variables, constraints, and objective)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'cplex', 'scip'
solver.options['TimeLimit'] = 60
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 123

results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    # Extract solution
    solution_times = {i: pyo.value(model.time[i]) for i in model.entities}
    # ... extract other variables
    # Verify solution
    if verify_solution_pyomo(solution_times, ...):
        print("Optimal/Feasible solution found and verified.")
else:
    print(f"Solver failed: Status={results.solver.status}, Termination={results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both the solver status and termination condition, potentially interpreting suboptimal or interrupted runs as optimal.
- Assuming the solver's internal feasibility tolerance; always use an explicit tolerance in verification routines.
- Forgetting to deactivate the `tee` flag in production code, which can clutter logs with solver progress output.
