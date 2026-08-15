---
name: Multi-Supplier Allocation with Minimum Delivery
description: |
  Model and solve allocation problems with minimum delivery per active supplier, multiple suppliers per demand, and linear costs using MILP formulations.

---

# Workflow 1 (MILP with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using a direct, solver-agnostic approach suitable for open-source solvers like SCIP or CBC. The core is linking continuous allocation variables to binary activation variables via Big-M constraints.

### Step 1 - Define Core Variables
- Create continuous `allocation_amount[i,j]` variables representing the quantity supplied from source `i` to demand `j`.
- Create binary `binary_assignment[i,j]` variables indicating whether source `i` is active for demand `j`.
- Use zero lower bounds and appropriate upper bounds (e.g., `solver.infinity()` or `capacity[i]`) for continuous variables.

### Step 2 - Formulate Linking and Activation Constraints
- Enforce `allocation_amount[i,j] >= min_delivery[i] * binary_assignment[i,j]` to ensure minimum delivery if active.
- Add an upper-linking constraint: `allocation_amount[i,j] <= capacity[i] * binary_assignment[i,j]` to force the allocation to zero if inactive.
- This pair of constraints fully couples the continuous and binary decisions.

### Step 3 - Impose Supply and Demand Constraints
- Add supply capacity constraints: `sum_j allocation_amount[i,j] <= capacity[i]` for each source `i`.
- Add demand requirement constraints: `sum_i allocation_amount[i,j] >= demand[j]` for each demand `j`.

### Step 4 - Enforce Multiple Supplier Requirement
- For each demand `j`, add a constraint requiring a minimum number of active suppliers: `sum_i binary_assignment[i,j] >= K`, where `K` is a parameter (e.g., 2).

### Formulation Template
```json
{
  "sets": [
    "I: set of supply sources",
    "J: set of demand points"
  ],
  "parameters": [
    "capacity[i]: maximum total output from source i",
    "demand[j]: required quantity for demand j",
    "min_delivery[i]: minimum quantity to supply if source i is active for a demand",
    "cost[i,j]: unit cost of supplying from i to j",
    "K: minimum number of active suppliers per demand point"
  ],
  "decision_variables": [
    "x[i,j]: continuous, allocation amount from i to j",
    "y[i,j]: binary, 1 if i supplies j, else 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_i sum_j cost[i,j] * x[i,j]"
  },
  "constraints": [
    "supply_capacity[i]: sum_j x[i,j] <= capacity[i]",
    "demand_requirement[j]: sum_i x[i,j] >= demand[j]",
    "minimum_delivery_if_active[i,j]: x[i,j] >= min_delivery[i] * y[i,j]",
    "upper_linking[i,j]: x[i,j] <= capacity[i] * y[i,j]",
    "multiple_suppliers_per_demand[j]: sum_i y[i,j] >= K"
  ]
}
```

### Common Pitfalls
- Using an overly large Big-M value in the upper-linking constraint, which weakens the LP relaxation; use the tightest valid bound (e.g., `capacity[i]`).
- Forgetting to add the upper-linking constraint, which can lead to solutions where `x[i,j] > 0` but `y[i,j] = 0`.
- Setting `K` higher than the number of available suppliers for a demand, causing infeasibility.

## Solving stage

### Strategy Overview
Solve the MILP using the OR-Tools wrapper, configuring the solver for performance and reliability, then rigorously extract and validate the solution.

### Step 1 - Initialize Solver and Variables
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Create variable dictionaries `x` and `y` by looping over all `(i,j)` pairs.
- Set appropriate variable bounds (e.g., `x[i,j] = solver.NumVar(0, capacity[i], ...)`).

### Step 2 - Add Constraints and Objective
- Add all constraints from the formulation using nested loops and `solver.Add()`.
- Build the objective function by setting coefficients for each `x[i,j]` variable.
- Call `solver.Minimize(objective)`.

### Step 3 - Configure and Execute Solve
- Set a time limit: `solver.SetTimeLimit(timeout_ms)`.
- Optionally set the number of threads: `solver.SetNumThreads(num_threads)`.
- Call `status = solver.Solve()` and check for `OPTIMAL` or `FEASIBLE`.

### Step 4 - Extract and Verify Solution
- Retrieve solution values: `x_val = x[i,j].solution_value()`, `y_val = round(y[i,j].solution_value())`.
- Store allocations where `x_val > tolerance` and `y_val == 1`.
- Programmatically recompute constraint sums (capacity, demand, supplier counts) to verify feasibility within a small tolerance (e.g., 1e-6).

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... create variables, constraints, objective
solver.SetTimeLimit(30000)  # 30 seconds

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    # Extract solution
    for i in I:
        for j in J:
            if x[i,j].solution_value() > 1e-6:
                print(f"Allocation {i}->{j}: {x[i,j].solution_value()}")
    # Verification checks
    for i in I:
        total_supply = sum(x[i,j].solution_value() for j in J)
        assert total_supply <= capacity[i] + 1e-6, f"Capacity violation for {i}"
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially missing good solutions.
- Using raw `y[i,j].solution_value()` without rounding for binary checks, leading to false positives due to solver tolerances.
- Omitting post-solve verification, which can mask subtle constraint violations.

# Workflow 2 (Pyomo with Commercial Solver)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling framework, separating problem specification from solver details. This approach facilitates integration with powerful commercial solvers like Gurobi or CPLEX, leveraging their advanced presolve and cut generation.

### Step 1 - Declare Model Components
- Define Pyomo Sets `model.I` and `model.J` for sources and demands.
- Define Pyomo Parameters for `capacity`, `demand`, `min_delivery`, `cost`, and `K`.
- Use `pyo.Param` within a rule or initialize with a dictionary.

### Step 2 - Define Variables with Clear Domains
- Declare continuous variable `model.x` indexed over `(I,J)` with a lower bound of 0.
- Declare binary variable `model.y` indexed over `(I,J)`.
- This clean separation aligns with the mathematical formulation.

### Step 3 - Construct Constraints via Rules
- Implement supply capacity constraint as a rule: `def supply_rule(model, i): return sum(model.x[i,j] for j in model.J) <= model.capacity[i]`.
- Implement demand requirement, minimum delivery linking, upper linking, and multiple supplier constraints similarly with indexed rules.
- The rule-based approach enhances readability and maintainability.

### Step 4 - Set Linear Objective
- Define the objective: `model.obj = pyo.Objective(expr=sum(model.cost[i,j]*model.x[i,j] for i in model.I for j in model.J), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of supply sources",
    "J: set of demand points"
  ],
  "parameters": [
    "capacity: dict over I",
    "demand: dict over J",
    "min_delivery: dict over I",
    "cost: dict over (I,J)",
    "K: scalar"
  ],
  "decision_variables": [
    "x[i,j]: continuous, >=0",
    "y[i,j]: binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i,j] * x[i,j] for i in I, j in J )"
  },
  "constraints": [
    "supply_capacity[i]: sum_j x[i,j] <= capacity[i]",
    "demand_requirement[j]: sum_i x[i,j] >= demand[j]",
    "minimum_delivery_if_active[i,j]: x[i,j] >= min_delivery[i] * y[i,j]",
    "upper_linking[i,j]: x[i,j] <= capacity[i] * y[i,j]",
    "multiple_suppliers_per_demand[j]: sum_i y[i,j] >= K"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters within constraint rules, leading to `KeyError`.
- Forgetting to initialize all parameters before solving, resulting in an incomplete model.
- Using mutable default arguments (like lists) in Pyomo rule functions.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured commercial solver instance, focusing on optimality guarantees and advanced parameter tuning for large-scale instances.

### Step 1 - Instantiate Solver with Options
- Create a solver object: `solver = pyo.SolverFactory('gurobi')`.
- Set solver options via `options` dict or keyword arguments: e.g., `solver.options['MIPGap'] = 0.001`, `solver.options['TimeLimit'] = 30`.

### Step 2 - Execute Solve and Capture Results
- Call `results = solver.solve(model, tee=True)` to solve and print log.
- The `tee=True` flag provides real-time progress output.

### Step 3 - Inspect Termination Condition
- Check `results.solver.termination_condition` for `optimal`, `feasible`, or `infeasible`.
- Check `results.solver.status` for `ok`.
- Handle non-optimal statuses by analyzing the model or relaxing parameters.

### Step 4 - Extract and Validate Solution
- Access variable values: `model.x[i,j].value` and `model.y[i,j].value`.
- Perform a full constraint check: compute sums for capacity, demand, and active supplier counts, comparing against limits with tolerance.
- Output a structured summary of allocations and key metrics.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_list)
model.J = pyo.Set(initialize=J_list)
# ... define parameters, variables, constraints, objective

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 30
results = solver.solve(model, tee=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    for i in model.I:
        for j in model.J:
            if model.x[i,j].value > 1e-6:
                print(f"Allocation {i}->{j}: {model.x[i,j].value:.2f}")
    # Verification
    for j in model.J:
        active_count = sum(1 for i in model.I if model.y[i,j].value > 0.5)
        assert active_count >= K, f"Supplier count violation for demand {j}"
else:
    print(f"Solver terminated with condition: {results.solver.termination_condition}")
```

### Common Pitfalls
- Assuming `model.y[i,j].value` is exactly 0 or 1; always use a tolerance (e.g., `> 0.5`) for binary checks.
- Not checking both `termination_condition` and `solver.status`, which can miss warnings or errors.
- Over-tuning solver parameters for small problems, which can introduce unnecessary overhead.
