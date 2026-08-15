---
name: Generic Job Shop Scheduling with Precedence Variables
description: |
  Model and solve job shop scheduling problems with machine capacity constraints using binary precedence variables and big-M constraints, minimizing makespan.
---

# Workflow 1 (CP-SAT for Exact Scheduling)

## Modeling stage

### Strategy Overview
This workflow models a job shop scheduling problem using OR-Tools CP-SAT. It uses integer variables for start times, a makespan variable, and binary precedence variables to sequence operations on shared machines via big-M constraints. It is designed for exact, optimal solutions.

### Step 1 - Define Core Variables
- Define integer variables `start_times[(j, o)]` for the start time of each operation `(job, operation)`.
- Define an integer variable `makespan` to represent the maximum completion time.
- For each pair of operations that share a machine, define a binary variable `precedes[(op1, op2)]` to indicate if `op1` starts before `op2`.

### Step 2 - Enforce Job Precedence Constraints
- For each job, add constraints ensuring each operation starts after the previous one finishes: `start_times[(j, o)] >= start_times[(j, o-1)] + processing_time[(j, o-1)]`.

### Step 3 - Implement Machine No-Overlap with Big-M
- For each machine, identify all operation pairs `(op1, op2)` that require the same resource.
- Add two complementary big-M constraints for each pair:
    - `start_times[op2] >= start_times[op1] + processing_time[op1] - M * (1 - precedes[(op1, op2)])`
    - `start_times[op1] >= start_times[op2] + processing_time[op2] - M * precedes[(op1, op2)]`
- Ensure mutual exclusivity: `precedes[(op1, op2)] + precedes[(op2, op1)] == 1` for unordered pairs.

### Step 4 - Define Makespan and Objective
- Add constraints that the makespan is at least the completion time of every operation: `makespan >= start_times[(j, o)] + processing_time[(j, o)]`.
- Set the objective to minimize the `makespan` variable.

### Formulation Template
```json
{
  "sets": [
    "Jobs",
    "Operations",
    "Machines",
    "OperationMachineAssignments"
  ],
  "parameters": [
    {"name": "processing_time", "index": ["job", "operation"], "type": "int"},
    {"name": "machine_for_operation", "index": ["job", "operation"], "type": "int"},
    {"name": "big_M", "type": "int"}
  ],
  "decision_variables": [
    {"name": "start_time", "index": ["job", "operation"], "type": "integer", "lb": 0},
    {"name": "makespan", "type": "integer", "lb": 0},
    {"name": "precedes", "index": ["operation_i", "operation_j"], "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "job_precedence: start_time[j,o] >= start_time[j,o-1] + processing_time[j,o-1] for all j, o>0",
    "makespan_definition: makespan >= start_time[j,o] + processing_time[j,o] for all j, o",
    "disjunctive_ordering_1: start_time[op_j] >= start_time[op_i] + processing_time[op_i] - big_M * (1 - precedes[op_i, op_j]) for all conflicting op_i, op_j",
    "disjunctive_ordering_2: start_time[op_i] >= start_time[op_j] + processing_time[op_j] - big_M * precedes[op_i, op_j] for all conflicting op_i, op_j",
    "mutual_exclusivity: precedes[op_i, op_j] + precedes[op_j, op_i] == 1 for all unordered conflicting pairs"
  ]
}
```

### Common Pitfalls
- Setting `big_M` too small, which can cut off feasible solutions, or too large, which can cause numerical instability and slow solving.
- Forgetting to enforce mutual exclusivity (`precedes[op_i, op_j] + precedes[op_j, op_i] == 1`), leading to incorrect or infeasible models.
- Not grouping operations by their assigned machine when generating conflict pairs, which creates unnecessary variables and constraints.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with parameters tuned for scheduling problems. Focus on verifying solution status and extracting a feasible schedule.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.parameters.max_time_in_seconds = time_limit`.
- Enable parallelism: `solver.parameters.num_search_workers = num_workers`.
- Set a random seed for reproducibility: `solver.parameters.random_seed = seed`.
- For an exact solution, set the relative gap limit to zero: `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Execute the solver: `status = solver.Solve(model)`.
- Check if the status is `OPTIMAL` or `FEASIBLE` before proceeding. Handle `INFEASIBLE` or `UNKNOWN` statuses with appropriate error messages or fallbacks.

### Step 3 - Extract and Validate Solution
- If the solve was successful, extract the value of each `start_time` variable and the `makespan`.
- Optionally, extract the active precedence variables to understand the sequence on each machine.
- Perform a sanity check: verify that no two operations on the same machine overlap and that all job precedence constraints are satisfied.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
# Configure parameters
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print(f"Makespan: {solver.Value(makespan)}")
    # Extract start times
    schedule = {}
    for j in jobs:
        for o in operations:
            schedule[(j, o)] = solver.Value(start_time[(j, o)])
    # ... further processing
elif status == cp_model.INFEASIBLE:
    print("Model is infeasible.")
else:
    print("Solver did not find a solution within limits.")
```

### Common Pitfalls
- Not checking solver status before accessing variable values, which can cause runtime errors.
- Using default solver parameters for large instances, which may result in long runtimes or suboptimal solutions.
- Assuming a flow shop structure (fixed machine sequence per job) when the problem is a general job shop, leading to an incorrect model.

# Workflow 2 (MIP Solver with Pyomo)

## Modeling stage

### Strategy Overview
This workflow models the same scheduling problem using Pyomo to create a Mixed-Integer Programming (MIP) formulation, suitable for solvers like HiGHS or CBC. It uses continuous start time variables, a makespan variable, and binary precedence variables with big-M constraints.

### Step 1 - Define Variables and Model
- Instantiate a Pyomo `ConcreteModel`.
- Define continuous variables `model.start_time[j, o]` with a non-negative lower bound.
- Define a continuous variable `model.makespan` with a non-negative lower bound.
- For each unordered pair of operations conflicting on a machine, define a binary variable `model.precedes[op_i, op_j]`.

### Step 2 - Add Job Precedence and Makespan Constraints
- Add constraints for each job's operation sequence: `model.start_time[j, o] >= model.start_time[j, o-1] + processing_time[j, o-1]`.
- Add constraints linking each operation's completion time to the makespan: `model.makespan >= model.start_time[j, o] + processing_time[j, o]`.

### Step 3 - Add Disjunctive Machine Constraints
- For each machine and each unordered pair of conflicting operations `(op_i, op_j)`, add two big-M constraints:
    - `model.start_time[op_j] >= model.start_time[op_i] + processing_time[op_i] - big_M * (1 - model.precedes[op_i, op_j])`
    - `model.start_time[op_i] >= model.start_time[op_j] + processing_time[op_j] - big_M * model.precedes[op_i, op_j]`
- Enforce sequencing symmetry: `model.precedes[op_i, op_j] + model.precedes[op_j, op_i] == 1`.

### Step 4 - Set Objective
- Set the model objective to minimize `model.makespan`.

### Formulation Template
```json
{
  "sets": [
    "Jobs",
    "Operations",
    "Machines",
    "ConflictingOperationPairs"
  ],
  "parameters": [
    {"name": "processing_time", "index": ["job", "operation"], "type": "float"},
    {"name": "big_M", "type": "float"}
  ],
  "decision_variables": [
    {"name": "start_time", "index": ["job", "operation"], "type": "continuous", "lb": 0},
    {"name": "makespan", "type": "continuous", "lb": 0},
    {"name": "precedes", "index": ["operation_i", "operation_j"], "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "job_precedence: start_time[j,o] >= start_time[j,o-1] + processing_time[j,o-1] for all j, o>0",
    "makespan_def: makespan >= start_time[j,o] + processing_time[j,o] for all j, o",
    "disjunctive_forward: start_time[op_j] >= start_time[op_i] + processing_time[op_i] - big_M * (1 - precedes[op_i, op_j]) for all (op_i, op_j) in ConflictingOperationPairs",
    "disjunctive_backward: start_time[op_i] >= start_time[op_j] + processing_time[op_j] - big_M * precedes[op_i, op_j] for all (op_i, op_j) in ConflictingOperationPairs",
    "sequence_symmetry: precedes[op_i, op_j] + precedes[op_j, op_i] == 1 for all unordered (op_i, op_j) in ConflictingOperationPairs"
  ]
}
```

### Common Pitfalls
- Using the same `big_M` value for all constraint pairs without considering operation-specific processing times, which can weaken the formulation.
- Incorrectly indexing the `precedes` variable over ordered pairs, which leads to duplicate variables and an over-constrained model.
- Defining the `ConflictingOperationPairs` set incorrectly (e.g., including pairs that do not share a machine), which bloats the model unnecessarily.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver, configuring it for optimality and performance. Extract and validate the solution, paying attention to solver termination conditions.

### Step 1 - Select and Configure Solver
- Instantiate a solver (e.g., `SolverFactory('appsi_highs')` or `'cbc'`).
- Set solver options for optimality: `opt.options['mip_rel_gap'] = 0.0`.
- Set a time limit: `opt.options['time_limit'] = time_limit`.
- Configure parallel threads: `opt.options['threads'] = num_threads`.

### Step 2 - Solve and Check Termination Status
- Execute the solver: `results = opt.solve(model, tee=True)`.
- Check the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`). Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Extract and Verify Schedule
- Load the solution into the model: `model.solutions.load_from(results)`.
- Extract the value of `model.makespan` and all `model.start_time` variables.
- Optionally, extract values of `model.precedes` variables to determine the sequence on each machine.
- Programmatically verify that the extracted schedule satisfies all constraints (no overlaps, precedence respected).

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
# ... (define sets, parameters, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs')  # or 'cbc'
solver.options['mip_rel_gap'] = 0.0
solver.options['time_limit'] = 30
solver.options['threads'] = 4

results = solver.solve(model, tee=False)  # Set tee=True for solver log

if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    print(f"Makespan: {pyo.value(model.makespan)}")
    # Extract start times
    schedule = {}
    for j in model.Jobs:
        for o in model.Operations:
            schedule[(j, o)] = pyo.value(model.start_time[j, o])
    # ... further processing and validation
else:
    print(f"Solver failed. Status: {results.solver.status}, Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Forgetting to load the solution (`model.solutions.load_from(results)`) before accessing variable values, resulting in `None` or default values.
- Not handling the case where the solver finds a feasible but not optimal solution, which may require different post-processing logic.
- Using overly verbose solver output (`tee=True`) in production without proper logging control, which can clutter logs.
