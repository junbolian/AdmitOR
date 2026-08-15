---
name: Flow Shop Scheduling with Disjunctive Constraints
description: |
  Model and solve flow shop scheduling problems with job precedence and machine capacity constraints using binary disjunctive variables and makespan minimization.

---

# Workflow 1 (CP-SAT Solver for Flow Shop)

## Modeling stage

### Strategy Overview
This workflow models a flow shop scheduling problem using integer start times and binary precedence variables, then solves it with OR-Tools' CP-SAT solver. It is designed for problems where all jobs follow the same machine sequence (e.g., all first operations on Machine 0, all second on Machine 1). The model enforces job precedence and machine disjunctive constraints via big-M formulations.

### Step 1 - Define Data and Machine Mapping
- Define sets for jobs, operations, and machines. Map each operation index to a specific machine (e.g., operation `o` is processed on machine `o` in a flow shop).
- Define parameters for processing times `processing_time[j, o]`. Calculate a large upper bound `M` for big-M constraints (e.g., sum of all processing times).

### Step 2 - Create Decision Variables
- Create integer variables `start_time[j, o]` for the start time of each operation.
- Create binary variables `precedes[op1, op2]` only for pairs of operations assigned to the same machine. Index pairs efficiently to avoid unnecessary variables.
- Create an integer variable `makespan` to represent the completion time of the last operation.

### Step 3 - Enforce Job Precedence Constraints
- For each job `j` and its consecutive operations `o` and `o+1`, add a constraint: `start_time[j, o+1] >= start_time[j, o] + processing_time[j, o]`.

### Step 4 - Enforce Machine Disjunctive Constraints
- For each pair of operations (`op1`, `op2`) sharing the same machine, add two big-M constraints:
    - `start_time[op2] >= start_time[op1] + processing_time[op1] - M * (1 - precedes[op1, op2])`
    - `start_time[op1] >= start_time[op2] + processing_time[op2] - M * precedes[op1, op2]`
- Add a constraint `precedes[op1, op2] + precedes[op2, op1] == 1` to enforce mutual exclusivity.

### Step 5 - Define Makespan and Objective
- For each operation, add a constraint: `makespan >= start_time[j, o] + processing_time[j, o]`.
- Set the objective to minimize `makespan`.

### Formulation Template
```json
{
  "sets": [
    "jobs",
    "operations",
    "machines"
  ],
  "parameters": [
    {"name": "processing_time", "index": ["job", "operation"]},
    {"name": "machine_assignment", "index": ["operation"]}
  ],
  "decision_variables": [
    {"name": "start_time", "type": "integer", "index": ["job", "operation"]},
    {"name": "precedes", "type": "binary", "index": ["operation_pair"]},
    {"name": "makespan", "type": "integer"}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "job_precedence",
    "machine_disjunctive",
    "makespan_definition"
  ]
}
```

### Common Pitfalls
- Creating binary precedence variables for operations on different machines, which unnecessarily increases model size.
- Using an excessively large big-M value, which can degrade solver performance and numerical stability.
- Ambiguity in machine assignment mapping; always verify the flow shop assumption matches the problem data.
- Incorrect indexing in constraint rules, leading to errors like "takes 3 positional arguments but 5 were given".

## Solving stage

### Strategy Overview
Solve the model using OR-Tools CP-SAT solver, configured for parallel search and optimality proof. Extract and validate the schedule, including start times, machine sequences, and precedence decisions.

### Step 1 - Configure Solver Parameters
- Instantiate the CP-SAT solver. Set `max_time_in_seconds` to a reasonable limit (e.g., 30).
- Enable parallel search with `num_search_workers` (e.g., 8). Set `random_seed` for reproducibility.
- Set `relative_gap_limit` to 0.0 to prioritize finding and proving optimality.

### Step 2 - Solve and Check Status
- Call the solver's `Solve` method. Capture the solution status (`OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`).
- If status is not `OPTIMAL` or `FEASIBLE`, report the status and terminate.

### Step 3 - Extract and Validate Solution
- If feasible, retrieve the value of `makespan` and all `start_time` variables.
- For each machine, list operations in order of their start times to verify no overlaps.
- Retrieve values of `precedes` variables to confirm the disjunctive sequencing.
- Optionally, print a Gantt chart or machine-wise schedule for verification.

### Step 4 - Report Results
- Report the optimal or best-found makespan.
- Output the schedule in a structured format (e.g., job-operation start times).
- If optimality was proven, state that the solution is optimal.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = -1.0  # Disable relative gap, use absolute

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    makespan_val = solver.Value(makespan)
    # Extract start times and precedence variables
    schedule = {(j, o): solver.Value(start_time[j, o]) for j in jobs for o in operations}
    # Validate and report
else:
    print(f"Solver status: {status}")
```

### Common Pitfalls
- Not checking solver status before extracting variable values, which can cause runtime errors.
- Misinterpreting `FEASIBLE` as `OPTIMAL`; always report the distinction.
- Overlooking the validation of machine assignments in the extracted schedule.
- Setting an insufficient time limit for the solver to prove optimality on larger instances.

# Workflow 2 (MIP Solver for Flow Shop)

## Modeling stage

### Strategy Overview
This workflow models the same flow shop scheduling problem but structures it for a traditional Mixed-Integer Programming (MIP) solver (e.g., Gurobi, CPLEX). It uses binary disjunctive variables with big-M constraints and focuses on solver parameters that emphasize optimality proof.

### Step 1 - Define Problem Data and Bounds
- Define sets for jobs, operations, and machines. Map operations to machines.
- Define processing time parameters. Compute a tight upper bound `M` for big-M constraints (e.g., sum of processing times for all jobs on the bottleneck machine).

### Step 2 - Create MIP Variables
- Create continuous or integer variables `start_time[j, o]` with appropriate bounds (e.g., 0 to `M`).
- Create binary variables `precedes[op1, op2]` for operation pairs on the same machine.
- Create a continuous variable `makespan` with a lower bound of 0.

### Step 3 - Add Job Precedence Constraints
- For each job `j` and operation `o` (except the last), add: `start_time[j, o+1] - start_time[j, o] >= processing_time[j, o]`.

### Step 4 - Add Pairwise Disjunctive Constraints
- For each pair (`op1`, `op2`) on the same machine, add:
    - `start_time[op2] - start_time[op1] >= processing_time[op1] - M * (1 - precedes[op1, op2])`
    - `start_time[op1] - start_time[op2] >= processing_time[op2] - M * precedes[op1, op2]`
- Optionally, add `precedes[op1, op2] + precedes[op2, op1] == 1` to explicitly enforce one direction.

### Step 5 - Define Makespan and Objective
- For each operation, add: `makespan >= start_time[j, o] + processing_time[j, o]`.
- Set the objective to minimize `makespan`.

### Formulation Template
```json
{
  "sets": [
    "jobs",
    "operations",
    "machines"
  ],
  "parameters": [
    {"name": "processing_time", "index": ["job", "operation"]},
    {"name": "machine_of_operation", "index": ["operation"]}
  ],
  "decision_variables": [
    {"name": "start_time", "type": "continuous", "index": ["job", "operation"]},
    {"name": "precedes", "type": "binary", "index": ["operation_pair"]},
    {"name": "makespan", "type": "continuous"}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "job_precedence",
    "machine_disjunctive",
    "makespan_definition"
  ]
}
```

### Common Pitfalls
- Using an overly large big-M value, which weakens the LP relaxation and slows convergence.
- Creating disjunctive constraints for operations that cannot overlap (e.g., operations of the same job), adding unnecessary complexity.
- Not providing variable bounds, which can lead to numerical issues or slower solving.
- Incorrectly indexing operation pairs, leading to constraints that are never activated or incorrectly activated.

## Solving stage

### Strategy Overview
Solve the MIP model using a solver like Gurobi or CPLEX, configured to prove optimality. Focus on parameter tuning for MIP focus and gap tolerance, followed by solution validation.

### Step 1 - Configure Solver for Optimality
- Set the MIP gap (`MIPGap`) to 0.0 to find and prove optimality.
- Set `MIPFocus` to 2 (or solver equivalent) to emphasize proving optimality over finding feasible solutions quickly.
- Set a `TimeLimit` appropriate for the problem size (e.g., 30 seconds).
- Configure thread usage (`Threads`) based on problem size; use fewer threads (e.g., 4) for small problems to reduce overhead.

### Step 2 - Solve and Check Termination Condition
- Call the solver's `optimize` method. Check the termination condition (`optimal`, `feasible`, `time_limit`, etc.).
- Verify the solver status indicates a successful solve (`ok`).

### Step 3 - Extract and Verify Solution
- If an optimal or feasible solution is found, retrieve the objective value (`makespan`) and variable values.
- Recompute the schedule: for each machine, sort operations by start time to ensure no overlaps.
- Check that all job precedence constraints are satisfied by comparing start times.
- Validate that the retrieved `precedes` variable values are consistent with the start time ordering.

### Step 4 - Analyze and Report
- Report the makespan and, if optimality was proven, state the optimality gap is 0%.
- Output the schedule in a machine-wise or job-wise format.
- If terminated by time limit, report the best bound and gap.

### Code Usage
```python
# build model from formulation
import gurobipy as gp
from gurobipy import GRB

model = gp.Model("flow_shop")
# ... (build variables and constraints as per modeling stage)

# solve with status / termination checks
model.setParam('MIPGap', 0.0)
model.setParam('TimeLimit', 30)
model.setParam('Threads', 4)
model.setParam('MIPFocus', 2)

model.optimize()

if model.status == GRB.OPTIMAL or model.status == GRB.SUBOPTIMAL:
    makespan_val = model.objVal
    # Extract variable values
    for v in model.getVars():
        print(f"{v.VarName} = {v.X}")
    # Validate constraints
else:
    print(f"Model status: {model.status}")
```

### Common Pitfalls
- Not checking both `model.status` and `model.objVal` before accessing solution values, risking errors.
- Setting `MIPGap=0.0` without a time limit, which may cause the solver to run indefinitely on difficult instances.
- Overlooking the need to validate that the solution satisfies all constraints, especially when the solver reports `SUBOPTIMAL`.
- Using default parameters for all problem sizes, which may be inefficient for small or large instances.
