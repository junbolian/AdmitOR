---
name: MultiPeriodUnitCommitment
description: |
  Model and solve multi-period unit commitment problems with integer operational decisions, startup indicators, and power output variables to minimize total cost while satisfying demand and capacity margin constraints.
---

# Workflow 1 (Pyomo-CBC MILP)

## Modeling stage

### Strategy Overview
This workflow models unit commitment as a mixed-integer linear program (MILP) using Pyomo's abstract or concrete modeling environment. It cleanly separates integer operational status, continuous power output, and integer startup indicators to accurately capture fixed, variable, and startup costs. Time-coupled dynamics are enforced via constraints linking consecutive periods.

### Step 1 - Define Core Variable Types
- Declare integer variables for the number of operational units per generator type and period.
- Declare continuous variables for the power output per generator type and period.
- Declare integer variables for the number of startup events per generator type and period.

### Step 2 - Enforce Output and Operational Links
- For each generator type and period, constrain power output to be zero if no units are operational.
- Enforce that power output lies between the minimum and maximum output per unit, scaled by the number of operational units.

### Step 3 - Implement Time-Coupled Operational Dynamics
- For periods after the first, limit the number of startups by the number of units operational in the previous period.
- For periods after the first, constrain the current operational count to be less than or equal to the previous count plus startups, allowing for unit shutdowns.
- For the initial period, define startup limits based on initial conditions or separate parameters.

### Step 4 - Impose System-Wide Requirements
- Add a constraint for each period to ensure total power output meets or exceeds the demand.
- Add a separate constraint for each period to ensure total available capacity (maximum output of operational units) meets or exceeds the required capacity margin.

### Step 5 - Formulate Cost-Minimization Objective
- Sum fixed costs proportional to operational units, variable costs proportional to power output, and startup costs proportional to startup events across all generator types and periods.

### Formulation Template
```json
{
  "sets": [
    "G: Set of generator types.",
    "T: Set of time periods."
  ],
  "parameters": [
    "demand[t in T]: Power demand in period t.",
    "capacity_margin[t in T]: Required reserve capacity margin in period t.",
    "min_output[g in G]: Minimum output per unit of type g.",
    "max_output[g in G]: Maximum output per unit of type g.",
    "max_operational[g in G]: Maximum number of available units of type g.",
    "startup_limit_initial[g in G]: Maximum startups for type g in the first period.",
    "fixed_cost[g in G]: Fixed cost per operational unit of type g per period.",
    "variable_cost[g in G]: Variable cost per unit of power output for type g.",
    "startup_cost[g in G]: Cost per startup event for type g."
  ],
  "decision_variables": [
    "n_op[g in G, t in T]: Integer, number of operational units.",
    "p[g in G, t in T]: Continuous, total power output.",
    "s[g in G, t in T]: Integer, number of startup events."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[g] * n_op[g,t] + variable_cost[g] * p[g,t] + startup_cost[g] * s[g,t] for g in G for t in T)"
  },
  "constraints": [
    "output_lb[g in G, t in T]: min_output[g] * n_op[g,t] <= p[g,t]",
    "output_ub[g in G, t in T]: p[g,t] <= max_output[g] * n_op[g,t]",
    "operational_limit[g in G, t in T]: n_op[g,t] <= max_operational[g]",
    "startup_initial[g in G]: s[g,0] <= startup_limit_initial[g]",
    "startup_link[g in G, t in T | t > 0]: s[g,t] <= n_op[g,t-1]",
    "dynamics[g in G, t in T | t > 0]: n_op[g,t] <= n_op[g,t-1] + s[g,t]",
    "demand_satisfaction[t in T]: sum(p[g,t] for g in G) >= demand[t]",
    "capacity_margin_req[t in T]: sum(max_output[g] * n_op[g,t] for g in G) >= capacity_margin[t]"
  ]
}
```

### Common Pitfalls
- Adding artificial constraints to force specific generator usage after solving, which changes the problem and may report a suboptimal solution.
- Confusing the final result from a modified model with the optimal solution to the original problem. Always report from the unmodified model.
- Ignoring the solver's termination condition; a 'feasible' status does not guarantee optimality.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC solver via the `pyomo` command-line interface or Python script. Configure solver options for performance and determinism. After solving, rigorously verify solution feasibility against the original constraints and extract a detailed schedule.

### Step 1 - Configure and Execute Solver
- Instantiate the solver using `SolverFactory('cbc')`.
- Set a time limit (`seconds`), optimality gap (`ratio`), and number of threads (`threads`) for reproducible performance.
- Call `solver.solve(model, tee=True)` to solve and optionally display the log.

### Step 2 - Validate Solver Status and Solution
- Check that `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If status is not ok or termination is not acceptable, output a structured error message and do not proceed to read variable values.

### Step 3 - Verify Solution Feasibility
- Programmatically evaluate each constraint type (demand, capacity margin, output bounds, operational limits, startup limits, dynamics) using the solved variable values.
- Use a small numerical tolerance (e.g., `1e-6`) and report any violations.

### Step 4 - Extract and Report Results
- For each period, extract and print the operational counts, power outputs, startup counts, and cost breakdowns per generator type.
- Report the total objective value.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (using formulation template)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective ...

# Solve
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 300
solver.options['ratio'] = 0.0
solver.options['threads'] = 4
results = solver.solve(model, tee=False)

# Status / termination checks
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Proceed to verify and extract solution
    # ... verification code ...
    print(f"Total cost: {pyo.value(model.obj)}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Trusting a non-optimal termination condition and reporting the objective value as optimal.
- Re-solving the model to "fix" harmless numerical artifacts (e.g., `-0.0`), which can lead to a different, worse solution.
- Performing manual cost analysis to second-guess the solver's proven optimal solution.

# Workflow 2 (OR-Tools MIP)

## Modeling stage

### Strategy Overview
This workflow models unit commitment directly using the OR-Tools MIP solver interface (SCIP or CBC backend). It declares integer and continuous variables with explicit bounds, adds constraints via coefficient setting, and builds the objective incrementally. The formulation mirrors the MILP structure but is implemented using the solver's native API.

### Step 1 - Declare Variables with Bounds
- For each generator type and period, create an integer variable for operational units with lower bound 0 and upper bound equal to the maximum available units.
- Create a continuous variable for power output with lower bound 0 and no explicit upper bound (handled by constraints).
- Create an integer variable for startup events with appropriate upper bounds.

### Step 2 - Encode Generator Output Constraints
- For each generator type and period, add a constraint enforcing power output >= minimum output per unit * operational units.
- Add a constraint enforcing power output <= maximum output per unit * operational units.

### Step 3 - Model Startup Logic and Dynamics
- For the initial period, add constraints limiting startups based on initial conditions.
- For subsequent periods, add constraints limiting startups to the number of units operational in the previous period.
- For subsequent periods, add constraints linking operational counts across periods, allowing decreases without penalty.

### Step 4 - Add System Demand and Capacity Margin Constraints
- For each period, create a constraint with lower bound equal to the demand and set coefficients for the power output variables.
- For each period, create a separate constraint with lower bound equal to the capacity margin and set coefficients for the maximum output times operational variables.

### Step 5 - Build Linear Objective
- Create a minimization objective.
- For each variable, set its coefficient to its corresponding cost (fixed, variable, or startup).
- Sum across all generator types and periods.

### Formulation Template
```json
{
  "sets": [
    "G: Set of generator types.",
    "T: Set of time periods."
  ],
  "parameters": [
    "demand[t in T]: Power demand in period t.",
    "capacity_margin[t in T]: Required reserve capacity margin in period t.",
    "min_output[g in G]: Minimum output per unit of type g.",
    "max_output[g in G]: Maximum output per unit of type g.",
    "max_operational[g in G]: Maximum number of available units of type g.",
    "startup_limit_initial[g in G]: Maximum startups for type g in the first period.",
    "fixed_cost[g in G]: Fixed cost per operational unit of type g per period.",
    "variable_cost[g in G]: Variable cost per unit of power output for type g.",
    "startup_cost[g in G]: Cost per startup event for type g."
  ],
  "decision_variables": [
    "n_op[g in G, t in T]: Integer, number of operational units.",
    "p[g in G, t in T]: Continuous, total power output.",
    "s[g in G, t in T]: Integer, number of startup events."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[g] * n_op[g,t] + variable_cost[g] * p[g,t] + startup_cost[g] * s[g,t] for g in G for t in T)"
  },
  "constraints": [
    "output_lb[g in G, t in T]: min_output[g] * n_op[g,t] <= p[g,t]",
    "output_ub[g in G, t in T]: p[g,t] <= max_output[g] * n_op[g,t]",
    "operational_limit[g in G, t in T]: n_op[g,t] <= max_operational[g]",
    "startup_initial[g in G]: s[g,0] <= startup_limit_initial[g]",
    "startup_link[g in G, t in T | t > 0]: s[g,t] <= n_op[g,t-1]",
    "dynamics[g in G, t in T | t > 0]: n_op[g,t] <= n_op[g,t-1] + s[g,t]",
    "demand_satisfaction[t in T]: sum(p[g,t] for g in G) >= demand[t]",
    "capacity_margin_req[t in T]: sum(max_output[g] * n_op[g,t] for g in G) >= capacity_margin[t]"
  ]
}
```

### Common Pitfalls
- Forgetting to set an upper bound for integer variables, which defaults to infinity and can cause model errors.
- Incorrectly ordering constraint addition and coefficient setting, leading to missing or wrong constraints.
- Assuming the initial operational count must equal startups; they are separate unless explicitly constrained.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools MIP solver (SCIP or CBC). Set solver options for time limit and parallelism. After solving, check the solution status, extract variable values, and perform a posteriori feasibility verification.

### Step 1 - Initialize Solver and Set Options
- Create a solver instance, e.g., `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Set a time limit in milliseconds using `solver.SetTimeLimit(time_limit_ms)`.
- Set the number of threads using `solver.SetNumThreads(num_threads)`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Check if `status` is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`.
- If status is not acceptable, report the status and exit.

### Step 3 - Extract Solution and Compute Verification Metrics
- For each variable, retrieve its value using `.solution_value()`.
- Programmatically compute the left-hand side of each critical constraint (demand, capacity margin, output bounds) and compare against the right-hand side with tolerance.

### Step 4 - Report Detailed Schedule and Costs
- Iterate over periods and generator types to print operational counts, power outputs, and startup events.
- Compute and print the total cost and cost breakdown.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Initialize solver
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit(300000)  # milliseconds
solver.SetNumThreads(4)

# Build model (using formulation template)
# ... create variables, add constraints, set objective ...

# Solve and check status
status = solver.Solve()
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    # Extract and verify solution
    # ... extraction and verification code ...
    print(f"Total cost: {solver.Objective().Value()}")
else:
    print(f"Solver finished with status: {status}")
```

### Common Pitfalls
- Not checking the solver status before extracting variable values, which can lead to errors.
- Misinterpreting the flexible startup logic: startups in the initial period are limited but not forced to equal operational units unless modeled.
- Adding extra constraints for verification purposes, which inadvertently alters the problem being solved.
