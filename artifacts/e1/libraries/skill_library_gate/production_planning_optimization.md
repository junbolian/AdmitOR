---
name: Production Planning Optimization
description: |
  A structured approach to model and solve production planning problems with resource constraints, profit maximization, and integer requirements.

---

# Workflow 1 (Pyomo MIP with Explicit Sets)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's AbstractModel paradigm with explicit Pyomo Set objects for clean indexing. It is well-suited for problems with clear dimensional structure (e.g., products, stages) and emphasizes separation of data and model logic for reusability.

### Step 1 - Define Index Sets
- Create Pyomo Set objects for all index dimensions (e.g., `model.P`, `model.S`).
- Use these sets to index parameters, variables, and constraints.

### Step 2 - Load Parameters into Dictionaries
- Store all numerical data (profits, bounds, capacities, time requirements) in Python dictionaries *before* model construction.
- Use tuple keys for multi-dimensional parameters (e.g., `time_required[(s, p)]`).

### Step 3 - Declare Decision Variables
- Declare Pyomo Var objects indexed by the appropriate sets.
- Specify variable domain (`NonNegativeReals`, `NonNegativeIntegers`, `Binary`) based on problem context (e.g., integer for physical units).

### Step 4 - Construct Objective Function
- Define the objective (maximize profit or minimize cost) as a Pyomo Expression using summation over indexed variables and parameters.
- Assign it to `model.obj` with the correct sense.

### Step 5 - Write Indexed Constraints
- Formulate constraints (lower/upper bounds, resource capacities) using Pyomo Constraint objects.
- Use `model.P` and `model.S` within `rule` functions to create indexed constraints cleanly.

### Formulation Template
```json
{
  "sets": ["products", "stages"],
  "parameters": {
    "profit": {"index": "products", "type": "float"},
    "min_prod": {"index": "products", "type": "float"},
    "max_prod": {"index": "products", "type": "float"},
    "capacity": {"index": "stages", "type": "float"},
    "time_req": {"index": ["stages", "products"], "type": "float"}
  },
  "decision_variables": [
    {"name": "x", "index": "products", "domain": "NonNegativeIntegers"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[p] * x[p] for p in products)"
  },
  "constraints": [
    {"name": "min_prod", "expression": "x[p] >= min_prod[p] for p in products"},
    {"name": "max_prod", "expression": "x[p] <= max_prod[p] for p in products"},
    {"name": "stage_cap", "expression": "sum(time_req[s,p] * x[p] for p in products) <= capacity[s] for s in stages"}
  ]
}
```

### Common Pitfalls
- Using continuous variables (`NonNegativeReals`) when the problem context implies integer production quantities.
- Overcomplicating data structures with Pyomo Param objects when simple Python dictionaries are sufficient for model building.
- Not verifying that minimum production requirements are feasible given resource capacities before solving.

## Solving stage

### Strategy Overview
Solve the MIP model with a commercial solver (e.g., CBC, Gurobi) configured for optimality. Perform rigorous solution status checks and post-solve validation to ensure a usable result.

### Step 1 - Configure and Run Solver
- Instantiate a solver object (e.g., `SolverFactory('cbc')`).
- Set appropriate options: `ratio=0.0` for exact optimality, `seconds=30` for time limit, `threads=4` for parallelism (ensure no conflict with global scheduler).
- Execute `solver.solve(model, ...)` and capture the results object.

### Step 2 - Verify Solver Termination Status
- Check `results.solver.status` (e.g., `SolverStatus.ok`).
- Check `results.solver.termination_condition` (accept `optimal` or `feasible`).
- If status is not ok or termination is not acceptable, output a structured error message and do not proceed to solution extraction.

### Step 3 - Extract and Validate Solution
- Extract variable values using `pyo.value(model.x[p])` for all indices.
- Compute constraint slacks (e.g., `capacity[s] - sum(...)`) to verify feasibility within a small tolerance.
- Compare solution values against declared lower and upper bounds.

### Step 4 - Perform Post-Optimality Analysis
- Identify binding constraints (slack ≈ 0) to understand limiting resources.
- For variables not at their bounds, compute potential improvement given slack on binding constraints.
- Report key metrics: objective value, solve time, optimality gap.

### Code Usage
```python
import pyomo.environ as pyo

# Assume 'model' is built according to Modeling stage
solver = pyo.SolverFactory('cbc')
solver.options['ratio'] = 0.0
solver.options['seconds'] = 30
# solver.options['threads'] = 4  # Use if no conflict

results = solver.solve(model, tee=False)

# Status verification
from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    # Extract and validate solution
    for p in model.P:
        val = pyo.value(model.x[p])
        # ... validation logic
else:
    # Output failure structure
    output = {"status": str(status), "termination": str(term), "solution": None}
```

### Common Pitfalls
- Accepting fractional solutions for integer problems without rounding or re-solving as MIP.
- Ignoring solver error messages or non-optimal termination conditions.
- Not computing constraint slacks, leading to unverified feasibility.
- Setting conflicting solver options (e.g., `threads` after global initialization).

# Workflow 2 (Concrete LP Relaxation for Benchmarking)

## Modeling stage

### Strategy Overview
This workflow first builds a continuous (LP) relaxation of the problem using Pyomo's ConcreteModel for immediate execution. It serves to establish an upper bound, diagnose infeasibility, and understand problem structure before integer solving.

### Step 1 - Instantiate Concrete Model
- Use `pyo.ConcreteModel()` for immediate expression evaluation.
- Directly embed parameter dictionaries within model construction or as model attributes.

### Step 2 - Define Variables with Continuous Domain
- Declare variables with domain `pyo.NonNegativeReals` even if the final requirement is integer.
- This provides the LP relaxation's optimal objective value, which bounds the MIP optimum.

### Step 3 - Add Constraints Directly
- Add constraints using Python's immediate evaluation within the ConcreteModel context.
- This allows quick checks for obvious infeasibilities (e.g., min demand > capacity).

### Step 4 - Set Objective
- Define the objective function identically to the MIP formulation but with continuous variables.

### Formulation Template
```json
{
  "sets": ["products", "stages"],
  "parameters": {
    "profit": {"index": "products", "type": "float"},
    "min_prod": {"index": "products", "type": "float"},
    "max_prod": {"index": "products", "type": "float"},
    "capacity": {"index": "stages", "type": "float"},
    "time_req": {"index": ["stages", "products"], "type": "float"}
  },
  "decision_variables": [
    {"name": "x", "index": "products", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[p] * x[p] for p in products)"
  },
  "constraints": [
    {"name": "min_prod", "expression": "x[p] >= min_prod[p] for p in products"},
    {"name": "max_prod", "expression": "x[p] <= max_prod[p] for p in products"},
    {"name": "stage_cap", "expression": "sum(time_req[s,p] * x[p] for p in products) <= capacity[s] for s in stages"}
  ]
}
```

### Common Pitfalls
- Treating the LP solution as final for a problem requiring integer variables.
- Skipping the LP relaxation step, missing an opportunity to benchmark and diagnose.
- Not using the LP upper bound to assess the quality of a subsequent integer solution.

## Solving stage

### Strategy Overview
Solve the LP relaxation quickly, analyze its solution to inform the subsequent MIP solve (e.g., identify tight constraints, potential infeasibility), and use the objective as a benchmark for optimality gaps.

### Step 1 - Solve LP with Standard Settings
- Use an LP-capable solver (e.g., `cbc`, `glpk`).
- Run with default or minimal options for speed.

### Step 2 - Analyze LP Solution and Feasibility
- Extract the continuous solution.
- Compute resource utilizations and constraint slacks.
- Verify that the LP is feasible; if infeasible, the MIP will also be infeasible.
- If feasible, the LP objective value is an upper bound for the MIP maximization problem.

### Step 3 - Use LP Results to Guide MIP
- Identify constraints with near-zero slack in the LP—these are likely binding in the MIP.
- Use the LP solution to warm-start the MIP solver if supported.
- Calculate the optimality gap later as `(LP_obj - MIP_obj) / LP_obj`.

### Step 4 - Transition to MIP Solve
- Change variable domains from `NonNegativeReals` to `NonNegativeIntegers` in a new model or by modifying the existing one.
- Re-solve with MIP settings, using insights from the LP analysis.

### Code Usage
```python
import pyomo.environ as pyo

# Build ConcreteModel with continuous variables
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=products)
model.S = pyo.Set(initialize=stages)
model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)
# ... add objective and constraints

# Solve LP
solver = pyo.SolverFactory('cbc')
results_lp = solver.solve(model)

# Check LP status
if results_lp.solver.termination_condition == TerminationCondition.optimal:
    lp_obj = pyo.value(model.obj)
    # Analyze slacks, utilizations
    # ...
    # Now build/solve MIP
    # Change domain or create new model with integer variables
    # mip_model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)
    # ... solve MIP and compare to lp_obj
else:
    print("LP infeasible or failed, investigate constraints.")
```

### Common Pitfalls
- Solving the LP and MIP in sequence without using LP insights to guide MIP solving.
- Not calculating the optimality gap using the LP upper bound.
- Assuming LP feasibility guarantees MIP feasibility (due to integer requirements).
- Running excessive verification loops; establish a single verification protocol.
