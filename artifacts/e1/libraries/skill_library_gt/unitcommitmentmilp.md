---
name: UnitCommitmentMILP
description: |
  Build and solve unit commitment problems as mixed-integer linear programs, modeling discrete generator on/off decisions, startup costs, and operational constraints to minimize total cost.
---

# Workflow 1 (Pyomo ConcreteModel with Explicit Sets/Params)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's `ConcreteModel` with explicitly defined `Set` and `Param` objects for a structured, data-driven model. It cleanly separates data from logic, making the formulation easy to modify and validate.

### Step 1 - Define Sets and Parameters
- Define a `Set` for generators and a `Set` for time periods.
- Define `Param` objects for all cost coefficients (fixed, variable, startup), demand per period, generator capacity limits (min/max output), and operational limits (ramp, startup limit).
- Use `within` arguments (e.g., `pyo.NonNegativeReals`) to enforce parameter domains.

### Step 2 - Declare Decision Variables
- Declare `n_op[g,t]` (number of operational units) as a `pyo.NonNegativeInteger` variable, bounded by the total number of units available.
- Declare `n_start[g,t]` (number of startups) as a `pyo.NonNegativeInteger` variable, bounded by the startup limit per period.
- Declare `p[g,t]` (power output) as a `pyo.NonNegativeReals` variable.

### Step 3 - Formulate the Objective Function
- Construct the total cost as the sum of fixed costs (`n_op * fixed_cost`), variable costs (`p * var_cost`), and startup costs (`n_start * startup_cost`) across all generators and time periods.
- Set the objective sense to `minimize`.

### Step 4 - Enforce Operational Constraints
- **Demand Satisfaction**: For each time period, sum of `p[g,t]` must equal the demand.
- **Generator Capacity**: For each generator and period, enforce `p[g,t] >= min_output[g] * n_op[g,t]` and `p[g,t] <= max_output[g] * n_op[g,t]`. This links output to commitment status.
- **Capacity Margin**: For each period, sum of `max_output[g] * n_op[g,t]` must meet or exceed demand plus a required reserve margin.
- **Startup Limit**: For each generator and period, `n_start[g,t] <= startup_limit[g]`.
- **Temporal Dynamics**: For `t > 1`, enforce `n_op[g,t] <= n_op[g,t-1] + n_start[g,t]` and `n_start[g,t] <= n_op[g,t-1]`. For `t=1`, define initial conditions separately.

### Formulation Template
```json
{
  "sets": ["generators", "time_periods"],
  "parameters": [
    "fixed_cost[g]", "variable_cost[g]", "startup_cost[g]",
    "demand[t]", "min_output[g]", "max_output[g]",
    "startup_limit[g]", "initial_operational[g]", "reserve_margin[t]"
  ],
  "decision_variables": [
    "n_op[g,t] (NonNegativeInteger)",
    "n_start[g,t] (NonNegativeInteger)",
    "p[g,t] (NonNegativeReals)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[g] * n_op[g,t] + variable_cost[g] * p[g,t] + startup_cost[g] * n_start[g,t] for g in generators, t in time_periods)"
  },
  "constraints": [
    "demand_satisfaction[t]: sum(p[g,t] for g in generators) == demand[t]",
    "min_output_limit[g,t]: p[g,t] >= min_output[g] * n_op[g,t]",
    "max_output_limit[g,t]: p[g,t] <= max_output[g] * n_op[g,t]",
    "capacity_margin[t]: sum(max_output[g] * n_op[g,t] for g in generators) >= demand[t] + reserve_margin[t]",
    "startup_limit_constr[g,t]: n_start[g,t] <= startup_limit[g]",
    "operational_dynamics[g,t>1]: n_op[g,t] <= n_op[g,t-1] + n_start[g,t]",
    "startup_link[g,t>1]: n_start[g,t] <= n_op[g,t-1]",
    "initial_condition[g]: n_op[g,1] == initial_operational[g] + n_start[g,1]"
  ]
}
```

### Common Pitfalls
- Adding redundant constraints that are implicitly enforced by other constraints (e.g., `n_start[g,t] <= n_op[g,t-1]` may be redundant if `operational_dynamics` is already present).
- Hardcoding parameter dictionaries inside the model-building function instead of passing them as arguments, reducing flexibility.
- Not using `Constraint.Skip` for boundary conditions (like `t=1`), leading to cluttered constraint rules.

## Solving stage

### Strategy Overview
Solve the MILP using a dedicated solver like HiGHS, with rigorous status checking and post-solve validation to ensure solution quality and feasibility.

### Step 1 - Configure and Run the Solver
- Instantiate a solver object (e.g., `pyo.SolverFactory('appsi_highs')`).
- Set appropriate options such as a time limit (`time_limit`) and thread count (`threads`) for performance.
- Solve the model with `tee=False` for clean output unless debugging.

### Step 2 - Validate Solver Status and Termination
- Check `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If checks fail, raise an informative error or implement a fallback strategy.

### Step 3 - Extract and Verify the Solution
- Extract the objective value using `float(pyo.value(model.obj))`.
- Programmatically verify key constraints (demand, capacity margin, variable bounds) are satisfied within a small tolerance (e.g., `1e-6`).
- Decompose and report the total cost into its fixed, variable, and startup components for validation.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (assuming model is built as per Modeling stage)
model = build_unit_commitment_model(data)

# Solve
solver = pyo.SolverFactory('appsi_highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, tee=False)

# Validate status
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    total_cost = float(pyo.value(model.obj))
    print(f"RESULT:{total_cost}")
    # Post-solve verification (example: check demand satisfaction)
    for t in model.time_periods:
        total_output = sum(pyo.value(model.p[g,t]) for g in model.generators)
        if abs(total_output - pyo.value(model.demand[t])) > 1e-6:
            print(f"Warning: Demand mismatch in period {t}")
else:
    raise RuntimeError(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Using excessive solver configuration (time limit, threads) for small problems, adding unnecessary overhead.
- Running multiple verification passes that re-solve the model, duplicating computational effort.
- Not checking solver status before accessing solution values, risking runtime errors.
- Using `tee=True` in production, leading to verbose logs.

# Workflow 2 (Pyomo AbstractModel with Rule-based Constraints)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's `AbstractModel` with constraint rules defined as functions. It is well-suited for scenarios where model structure is fixed but data changes frequently, as the model can be instantiated with different data dictionaries.

### Step 1 - Declare Abstract Sets and Parameters
- Declare abstract `Set` and `Param` components without initializing them with data.
- Use `within` and `initialize` (with default values) for parameters to define their domains.

### Step 2 - Define Abstract Variables
- Declare variables (`n_op`, `n_start`, `p`) with appropriate domains (`NonNegativeIntegers`, `NonNegativeReals`) but without indexing.
- Use the `bounds` argument on variables (e.g., `bounds=(0, max_units)`) to enforce simple limits directly.

### Step 3 - Build Objective and Constraints via Rules
- Define the objective function using a rule that sums costs over the abstract sets.
- Define each constraint type (demand, capacity, dynamics) as a separate rule function. The rule receives the model and the relevant indices.
- Inside rule functions, use `if` conditions (e.g., `if t == 1`) to handle boundary cases, returning `Constraint.Skip` where appropriate.

### Step 4 - Instantiate Model with Data
- Create a data dictionary matching the abstract component names.
- Instantiate the abstract model with this data using `model_instance = model.create_instance(data)`.

### Formulation Template
```json
{
  "sets": ["generators", "time_periods"],
  "parameters": [
    "fixed_cost", "variable_cost", "startup_cost",
    "demand", "min_output", "max_output",
    "startup_limit", "initial_operational", "reserve_margin"
  ],
  "decision_variables": [
    "n_op[g,t] (NonNegativeInteger, bounds=(0, total_units[g]))",
    "n_start[g,t] (NonNegativeInteger, bounds=(0, startup_limit[g]))",
    "p[g,t] (NonNegativeReals)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[g] * n_op[g,t] + variable_cost[g] * p[g,t] + startup_cost[g] * n_start[g,t] for g in generators, t in time_periods)"
  },
  "constraints": [
    "demand_rule(t): sum(p[g,t] for g in generators) == demand[t]",
    "output_min_rule(g,t): p[g,t] >= min_output[g] * n_op[g,t]",
    "output_max_rule(g,t): p[g,t] <= max_output[g] * n_op[g,t]",
    "reserve_rule(t): sum(max_output[g] * n_op[g,t] for g in generators) >= demand[t] + reserve_margin[t]",
    "startup_limit_rule(g,t): n_start[g,t] <= startup_limit[g]",
    "dynamics_rule(g,t): if t==1: n_op[g,t] == initial_operational[g] + n_start[g,t]; else: n_op[g,t] <= n_op[g,t-1] + n_start[g,t]",
    "startup_link_rule(g,t): if t>1: n_start[g,t] <= n_op[g,t-1] else: Constraint.Skip"
  ]
}
```

### Common Pitfalls
- Forgetting to handle boundary conditions (t=1) in rule functions, leading to incorrect constraint generation or errors.
- Defining constraint rules that are overly complex or mix multiple logical conditions, reducing readability.
- Not using `Constraint.Skip` for cases where a constraint should not be generated, resulting in unnecessary or invalid constraints.

## Solving stage

### Strategy Overview
Instantiate the abstract model with problem data and solve using a MILP solver. Leverage the rule-based structure to easily swap datasets and re-solve.

### Step 1 - Prepare Data and Create Instance
- Load or construct a data dictionary where keys correspond to abstract parameter names, with values as `dict` or `list` for indexed data.
- Call `model.create_instance(data)` to generate a concrete model instance.

### Step 2 - Solve and Check Results
- Use a solver factory to create a solver object configured for MILP (e.g., `'gurobi'`, `'cbc'`).
- Solve the instance, capturing the results object.
- Perform the same rigorous checks on solver status and termination condition as in Workflow 1.

### Step 3 - Analyze and Report Solution
- Extract variable values using `pyo.value(var[index])`.
- Compute and print a cost breakdown (fixed, variable, startup) from the solution values.
- Optionally, generate a summary report of unit commitment decisions per period.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Define abstract model (assuming defined as per Modeling stage)
abstract_model = define_abstract_uc_model()

# Data dictionary (example structure)
data = {
    None: {
        'generators': {None: ['G1', 'G2']},
        'time_periods': {None: list(range(1, num_periods+1))},
        'fixed_cost': {'G1': val1, 'G2': val2},
        # ... populate all other parameters
    }
}

# Create instance and solve
instance = abstract_model.create_instance(data)
solver = pyo.SolverFactory('cbc')
results = solver.solve(instance)

# Check solution
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    obj_val = float(pyo.value(instance.obj))
    print(f"RESULT:{obj_val}")
    # Example: Print commitment schedule
    for g in instance.generators:
        for t in instance.time_periods:
            print(f"{g},{t}: n_op={pyo.value(instance.n_op[g,t])}, p={pyo.value(instance.p[g,t])}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Providing data in the wrong format for `create_instance`, causing instantiation errors.
- Not verifying that all necessary parameters are provided in the data dictionary, leading to incomplete models.
- Assuming the solver found an optimal solution without checking the termination condition, potentially using suboptimal or infeasible results.
