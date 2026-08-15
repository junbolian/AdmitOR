---
name: Multi-Period Generator Commitment MILP
description: |
  Model and solve multi-period generator commitment problems with integer generator counts, continuous power outputs, and startup decisions to minimize total operating cost, using MILP solvers.

---

# Workflow 1 (Pyomo with HiGHS Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's ConcreteModel to build a structured MILP, leveraging the HiGHS solver for its robust performance on linear problems. The formulation explicitly separates integer and continuous variables, with constraints linking generator states across time periods.

### Step 1 - Define Sets and Parameters
- Define a set `G` for generator types and a set `T` for time periods.
- Organize all cost and capacity parameters (e.g., `base_cost[g]`, `max_output[g]`, `demand[t]`) as dictionaries indexed by these sets for clean model construction.

### Step 2 - Create Decision Variables
- Create integer variable `n[g,t]` for the number of generators of type `g` online in period `t`, using `pyo.NonNegativeIntegers`.
- Create continuous variable `p[g,t]` for the power output of type `g` in period `t`, using `pyo.NonNegativeReals`.
- Create integer variable `s[g,t]` for the number of startups of type `g` in period `t`, using `pyo.NonNegativeIntegers`.

### Step 3 - Formulate Objective and Constraints
- Construct the total cost objective as the sum of base, per-unit output, and startup costs across all generators and periods.
- Implement demand satisfaction, generator capacity bounds, reserve requirements, availability limits, and startup linking constraints using indexed expressions.

### Formulation Template
```json
{
  "sets": ["G (generator types)", "T (time periods)"],
  "parameters": [
    "base_cost[g]", "per_mw_cost[g]", "startup_cost[g]",
    "min_output[g]", "max_output[g]", "max_generators[g]",
    "demand[t]", "reserve_requirement[t]", "initial_condition[g]"
  ],
  "decision_variables": [
    "n[g,t] ∈ ℤ⁺ (generator count)",
    "p[g,t] ∈ ℝ⁺ (power output)",
    "s[g,t] ∈ ℤ⁺ (startup count)"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{g∈G, t∈T} (base_cost[g] * n[g,t] + per_mw_cost[g] * p[g,t] + startup_cost[g] * s[g,t])"
  },
  "constraints": [
    "demand_satisfaction[t]: ∑_{g∈G} p[g,t] ≥ demand[t] ∀ t∈T",
    "capacity_lower[g,t]: p[g,t] ≥ min_output[g] * n[g,t] ∀ g∈G, t∈T",
    "capacity_upper[g,t]: p[g,t] ≤ max_output[g] * n[g,t] ∀ g∈G, t∈T",
    "availability[g,t]: n[g,t] ≤ max_generators[g] ∀ g∈G, t∈T",
    "reserve[t]: ∑_{g∈G} max_output[g] * n[g,t] ≥ reserve_requirement[t] ∀ t∈T",
    "startup_linking_initial[g]: n[g,0] ≤ s[g,0] + initial_condition[g] ∀ g∈G",
    "startup_linking[g,t]: n[g,t] ≤ n[g,t-1] + s[g,t] ∀ g∈G, t∈T, t>0"
  ]
}
```

### Common Pitfalls
- Avoid setting variable bounds to infinity when a reasonable upper limit (like `max_generators[g]`) exists, as it can slow down the solver.
- Avoid inconsistent indexing, such as using `t == -1` for initial conditions instead of `t == 0`.
- Avoid adding redundant constraints that are already enforced by variable bounds (e.g., `n[g,t] >= 0`).

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver with configured time and optimality gap limits. Always check solver status and termination condition before extracting and verifying the solution.

### Step 1 - Configure and Run Solver
- Instantiate the solver with `pyo.SolverFactory("highs")`.
- Set key options: `time_limit` for runtime control and `mip_rel_gap` for optimality tolerance.
- Solve the model with `tee=True` to view logs.

### Step 2 - Validate Solution Status
- Check `results.solver.status` for `SolverStatus.ok`.
- Check `results.solver.termination_condition` for `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If status is not acceptable, diagnose infeasibility or other issues.

### Step 3 - Extract and Verify Solution
- Extract variable values using `pyo.value(m.var[g,t])` and cast to appropriate types (`int` for integer variables).
- Programmatically verify all constraints by computing left-hand and right-hand sides.
- Compute a cost breakdown by component for analysis.

### Code Usage
```python
import pyomo.environ as pyo

# Build model 'm' according to formulation
# ...

# Configure and solve
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = -1.0  # Use -1.0 to set gap to 0.0
results = solver.solve(m, tee=True)

# Check status
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal,
                                              TerminationCondition.feasible)):
    total_cost = pyo.value(m.obj)
    # Extract and verify solution
    for g in m.G:
        for t in m.T:
            n_val = int(pyo.value(m.n[g, t]))
            p_val = float(pyo.value(m.p[g, t]))
            s_val = int(pyo.value(m.s[g, t]))
            # ... verification logic
else:
    # Handle failure: print status and diagnose
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Avoid ignoring solver status checks, which can lead to runtime errors when accessing solution values.
- Avoid excessive verification runs that duplicate the solver's feasibility checks; trust the solver unless debugging.
- Avoid manually fixing variable values to test alternatives without re-solving, as this can yield suboptimal or infeasible solutions.

---

# Workflow 2 (Pyomo with CBC Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's ConcreteModel with the CBC solver, a specialized open-source MILP solver. The modeling approach is similar to Workflow 1 but tailors constraint expression and solver options for CBC's interface.

### Step 1 - Define Model Structure
- Use `pyo.ConcreteModel()` and define sets `model.G` and `model.T`.
- Store parameters as model attributes or within a separate data dictionary for clarity.

### Step 2 - Declare Variables with Explicit Bounds
- Declare integer variables with explicit upper bounds (e.g., `pyo.Var(..., bounds=(0, max_generators[g]))`) to provide the solver with better bounds.
- Ensure startup variables are non-negative integers with an appropriate upper bound.

### Step 3 - Build Constraints with Period-Specific Logic
- Implement the initial period startup linking as a separate constraint set using `if t == 0` logic.
- Formulate reserve capacity using the sum of maximum possible output.

### Formulation Template
```json
{
  "sets": ["G (generator types)", "T (time periods)"],
  "parameters": [
    "base_cost[g]", "output_cost[g]", "startup_cost[g]",
    "capacity_min[g]", "capacity_max[g]", "max_available[g]",
    "demand[t]", "reserve_req[t]", "initial_generators[g]"
  ],
  "decision_variables": [
    "generators[g,t] ∈ ℤ⁺, 0 ≤ generators[g,t] ≤ max_available[g]",
    "power_output[g,t] ∈ ℝ⁺",
    "startups[g,t] ∈ ℤ⁺"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{g,t} (base_cost[g]*generators[g,t] + output_cost[g]*power_output[g,t] + startup_cost[g]*startups[g,t])"
  },
  "constraints": [
    "demand[t]: ∑_g power_output[g,t] ≥ demand[t]",
    "output_min[g,t]: power_output[g,t] ≥ capacity_min[g] * generators[g,t]",
    "output_max[g,t]: power_output[g,t] ≤ capacity_max[g] * generators[g,t]",
    "reserve[t]: ∑_g capacity_max[g] * generators[g,t] ≥ reserve_req[t]",
    "startup_init[g]: generators[g,0] ≤ startups[g,0] + initial_generators[g]",
    "startup_link[g,t>0]: generators[g,t] ≤ generators[g,t-1] + startups[g,t]"
  ]
}
```

### Common Pitfalls
- Avoid calculating reserve requirements manually within constraints; use precomputed parameters to prevent rounding errors.
- Avoid overcomplicating the formulation with redundant constraints already implied by variable bounds.
- Avoid allowing startup variables to take negative values by not setting a proper lower bound of zero.

## Solving stage

### Strategy Overview
Solve using the CBC solver via Pyomo's interface, configuring it for a time limit and zero optimality gap. Implement comprehensive solution verification and structured output.

### Step 1 - Solver Configuration and Execution
- Create solver instance with `pyo.SolverFactory("cbc")`.
- Set options: `seconds` for time limit, `ratio` for optimality gap (use `0.0` for exact), and `threads` for parallelism if needed.
- Execute solve with `tee=True` for progress output.

### Step 2 - Post-Solve Validation
- Check solver status and termination condition. Accept both optimal and feasible solutions.
- If the solve fails, output a JSON-structured error with solver details for diagnosis.

### Step 3 - Solution Extraction and Reporting
- Extract all variable values and compute derived metrics (total power, reserve margin).
- Print a period-by-period summary including constraint satisfaction status.
- Optionally, write results to a structured file (e.g., JSON, CSV).

### Code Usage
```python
import pyomo.environ as pyo

# Build model 'model' according to formulation
# ...

# Configure and solve
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model, tee=True)

# Validate and extract
from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal,
                                          TerminationCondition.feasible):
    total_cost = pyo.value(model.obj)
    solution_summary = {}
    for t in model.T:
        total_power = sum(pyo.value(model.power_output[g, t]) for g in model.G)
        # ... compile period details
    # Print or save summary
else:
    # Output failure details
    failure_info = {
        "solver_status": str(status),
        "termination_condition": str(term)
    }
    print(failure_info)
```

### Common Pitfalls
- Avoid running multiple solver instances with minor tweaks without reusing the model, as rebuilding adds overhead.
- Avoid hardcoding alternative solutions based on manual reasoning instead of letting the solver explore the full space.
- Avoid setting overly loose optimality gaps (`ratio`) if an exact solution is required.
