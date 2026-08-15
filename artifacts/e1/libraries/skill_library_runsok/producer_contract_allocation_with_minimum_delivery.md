---
name: Producer-Contract Allocation with Minimum Delivery
description: |
  A MILP workflow for allocating supply to demand with per-producer minimum delivery requirements, using continuous assignment and binary activation variables, solved via modern MIP solvers with comprehensive feasibility verification.

---

# Workflow 1 (Pyomo with CBC/SCIP)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a clean, declarative MILP. It separates data definition from model construction, making it easy to swap datasets and solvers. The formulation uses a big-M approach to link continuous allocation and binary activation decisions.

### Step 1 - Define Sets and Parameters
- Define index sets for producers `I` and contracts `J`.
- Load or define parameters: `capacity[i]`, `demand[j]`, `min_delivery[i]`, `min_contributors[j]`, and `cost[i,j]`. Use placeholders for data sources.
- Validate data consistency (e.g., total capacity vs. total demand) to preempt infeasibility.

### Step 2 - Declare Decision Variables
- Create continuous variable `x[i,j] >= 0` for the amount allocated from producer `i` to contract `j`.
- Create binary variable `y[i,j] in {0,1}` indicating if producer `i` is selected to supply contract `j`.

### Step 3 - Formulate Constraints
- **Supply Limit**: `sum(x[i,j] for j in J) <= capacity[i]` for each `i in I`.
- **Demand Satisfaction**: `sum(x[i,j] for i in I) >= demand[j]` for each `j in J`.
- **Minimum Contributors**: `sum(y[i,j] for i in I) >= min_contributors[j]` for each `j in J`.
- **Minimum Delivery if Selected**: `x[i,j] >= min_delivery[i] * y[i,j]` for each `i,j`.
- **Linking/Upper Bound**: `x[i,j] <= capacity[i] * y[i,j]` for each `i,j` (ensures zero allocation if not selected).

### Step 4 - Define Objective
- Minimize total linear cost: `sum(cost[i,j] * x[i,j] for i in I, j in J)`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": [
    {"name": "capacity", "index": "I"},
    {"name": "demand", "index": "J"},
    {"name": "min_delivery", "index": "I"},
    {"name": "min_contributors", "index": "J"},
    {"name": "cost", "index": ["I", "J"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "continuous", "index": ["I", "J"], "lb": 0},
    {"name": "y", "type": "binary", "index": ["I", "J"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I, j in J)"
  },
  "constraints": [
    {"name": "supply_limit", "expression": "sum(x[i,j] for j in J) <= capacity[i]", "index": "I"},
    {"name": "demand_satisfaction", "expression": "sum(x[i,j] for i in I) >= demand[j]", "index": "J"},
    {"name": "min_contributors_req", "expression": "sum(y[i,j] for i in I) >= min_contributors[j]", "index": "J"},
    {"name": "min_delivery_if_selected", "expression": "x[i,j] >= min_delivery[i] * y[i,j]", "index": ["I", "J"]},
    {"name": "linking", "expression": "x[i,j] <= capacity[i] * y[i,j]", "index": ["I", "J"]}
  ]
}
```

### Common Pitfalls
- Interpreting minimum delivery as a total per producer instead of per contract, leading to an infeasible or incorrect model.
- Skipping the linking constraint (`x[i,j] <= M * y[i,j]`), allowing allocation without activation.
- Not checking basic feasibility (e.g., sum of smallest `min_delivery` for required `min_contributors` exceeds `demand`) before solving.
- Defining ambiguous cost matrices; infer logical patterns from partial data instead of using arbitrary random values.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or SCIP solver via the `SolverFactory` interface. Focus on robust termination checks, solution validation, and clear output formatting for automation.

### Step 1 - Instantiate Solver and Set Options
- Create solver object: `solver = SolverFactory('cbc')` (or `'scip'`).
- Set time limit: `solver.options['seconds'] = 30`.
- Set optimality tolerance: `solver.options['ratio'] = -1.0` (CBC) or appropriate gap tolerance.
- Optionally set thread count for parallel processing.

### Step 2 - Solve and Check Termination Status
- Execute `results = solver.solve(model)`.
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`. Treat both as acceptable for a valid solution.

### Step 3 - Extract and Verify Solution
- If solved successfully, load variable values: `model.x[i,j].value`, `model.y[i,j].value`.
- Perform post-solve verification of all constraints with a tolerance (e.g., `1e-6`) to guard against numerical issues.
- Print key metrics: objective value, allocation matrix, activation matrix, and constraint satisfaction summary.

### Step 4 - Handle Failures
- If infeasible, do not re-solve blindly. Analyze infeasibility by checking relaxed constraints or computing the minimum required capacity.
- Output a structured JSON result on failure, including solver status and termination condition for diagnostics.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation (using the template above)
model = pyo.ConcreteModel()
# ... (model construction steps)
# Define all sets, params, variables, constraints, objective

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Extract and process solution
    obj_val = pyo.value(model.objective)
    print(f"RESULT:{obj_val}")
    # ... verification and output
else:
    # Handle failure
    print(f"RESULT_JSON:{{'status': '{results.solver.status}', 'termination': '{results.solver.termination_condition}'}}")
```

### Common Pitfalls
- Ignoring solver termination conditions; accepting `infeasible` or `unbounded` as success.
- Not verifying solution feasibility post-solve, leading to downstream errors.
- Using hard-coded equality comparisons for floating-point variable values.
- Omitting time limits, causing hangs on difficult instances.

# Workflow 2 (OR-Tools with SCIP/CP-SAT)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver API (`pywraplp`) for a more imperative, code-driven model construction. It is well-suited for deployment environments where OR-Tools is preferred and offers direct access to SCIP or the high-performance CP-SAT solver for MIPs.

### Step 1 - Initialize Solver and Data Structures
- Create solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Define data containers (lists/dicts) for parameters: `capacity`, `demand`, `min_delivery`, `min_contributors`, `cost`.
- Use zero-based indexing for producers and contracts.

### Step 2 - Create Variables
- Create a 2D array of continuous variables `x[i][j] = solver.NumVar(0, capacity[i], f'x_{i}_{j}')`.
- Create a 2D array of binary variables `y[i][j] = solver.BoolVar(f'y_{i}_{j}')`.

### Step 3 - Add Constraints Imperatively
- **Supply Limit**: For each `i`, `solver.Add(sum(x[i][j] for j in J) <= capacity[i])`.
- **Demand Satisfaction**: For each `j`, `solver.Add(sum(x[i][j] for i in I) >= demand[j])`.
- **Minimum Contributors**: For each `j`, `solver.Add(sum(y[i][j] for i in I) >= min_contributors[j])`.
- **Minimum Delivery if Selected**: For each `i,j`, `solver.Add(x[i][j] >= min_delivery[i] * y[i][j])`.
- **Linking/Upper Bound**: For each `i,j`, `solver.Add(x[i][j] <= capacity[i] * y[i][j])`.

### Step 4 - Set Objective
- Build objective expression: `obj_expr = sum(cost[i][j] * x[i][j] for i in I for j in J)`.
- Set minimization: `solver.Minimize(obj_expr)`.

### Formulation Template
```json
{
  "sets": ["I", "J"],
  "parameters": [
    {"name": "capacity", "index": "I"},
    {"name": "demand", "index": "J"},
    {"name": "min_delivery", "index": "I"},
    {"name": "min_contributors", "index": "J"},
    {"name": "cost", "index": ["I", "J"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "continuous", "index": ["I", "J"], "lb": 0, "ub": "capacity[i]"},
    {"name": "y", "type": "binary", "index": ["I", "J"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I, j in J)"
  },
  "constraints": [
    {"name": "supply_limit", "expression": "sum(x[i][j] for j in J) <= capacity[i]", "index": "I"},
    {"name": "demand_satisfaction", "expression": "sum(x[i][j] for i in I) >= demand[j]", "index": "J"},
    {"name": "min_contributors_req", "expression": "sum(y[i][j] for i in I) >= min_contributors[j]", "index": "J"},
    {"name": "min_delivery_if_selected", "expression": "x[i][j] >= min_delivery[i] * y[i][j]", "index": ["I", "J"]},
    {"name": "linking", "expression": "x[i][j] <= capacity[i] * y[i][j]", "index": ["I", "J"]}
  ]
}
```

### Common Pitfalls
- Forgetting to set upper bounds on continuous variables, which can slow down the solver.
- Using Python's `sum` inside OR-Tools constraints incorrectly; ensure you are summing OR-Tools variable objects.
- Mis-indexing when creating large numbers of variables, leading to `IndexError` or incorrect constraints.
- Not pre-computing parameter patterns (like cost) leading to inconsistent or missing data.

## Solving stage

### Strategy Overview
Solve using OR-Tools' efficient C++ backend. Configure solver parameters for performance, execute solve, and implement detailed solution extraction and validation routines.

### Step 1 - Configure Solver Parameters
- Set time limit: `solver.SetTimeLimit(30000)` (milliseconds).
- Enable verbose output if needed: `solver.EnableOutput()`.
- Set number of threads: `solver.SetNumThreads(4)`.

### Step 2 - Solve and Interpret Result
- Call `status = solver.Solve()`.
- Map returned status: `pywraplp.Solver.OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.
- Treat `OPTIMAL` and `FEASIBLE` as successful solves.

### Step 3 - Extract and Validate Solution
- If successful, iterate over variables to collect `x[i][j].solution_value()` and `y[i][j].solution_value()`.
- Compute actual constraint left-hand sides and compare against limits with tolerance.
- Output allocation summary, total cost, and activation counts.

### Step 4 - Manage Infeasibility
- On `INFEASIBLE` status, avoid repeated solving. Implement a feasibility checker (e.g., relax minimum delivery constraints) or compute infeasibility certificates if supported.
- Return a clear error message with diagnostic information.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... create variables, add constraints, set objective as per modeling stage

# solve with status / termination checks
solver.SetTimeLimit(30000)
status = solver.Solve()

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    obj_val = solver.Objective().Value()
    print(f"RESULT:{obj_val}")
    # ... extract variable values and verify constraints
else:
    # Handle failure
    status_map = {pywraplp.Solver.OPTIMAL: 'OPTIMAL',
                  pywraplp.Solver.FEASIBLE: 'FEASIBLE',
                  pywraplp.Solver.INFEASIBLE: 'INFEASIBLE',
                  pywraplp.Solver.UNBOUNDED: 'UNBOUNDED'}
    print(f"RESULT_JSON:{{'status': '{status_map.get(status, 'UNKNOWN')}'}}")
```

### Common Pitfalls
- Confusing OR-Tools status codes with Pyomo's termination conditions.
- Not checking for `FEASIBLE` status, missing good solutions when optimality isn't proven.
- Extracting variable values without checking solve status first, causing errors.
- Overlooking the need to set appropriate solver parameters (like time limit) for real-world use.
