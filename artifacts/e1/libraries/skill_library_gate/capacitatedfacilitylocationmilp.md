---
name: CapacitatedFacilityLocationMILP
description: |
  Model and solve capacitated facility location problems with fixed costs and linear transportation costs using mixed-integer linear programming.

---

# Workflow 1 (OR-Tools / SCIP)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Linear Program (MILP) using the OR-Tools Python library. It leverages the `pywraplp` interface to construct a model with binary facility opening variables and continuous flow variables, linking them through capacity constraints.

### Step 1 - Define Data Structures
- Organize input data into clear lists and dictionaries for facilities, customers, and their associated parameters.
- Use Python dictionaries for costs, capacities, and demands, keyed by facility or customer indices for easy reference.

### Step 2 - Create Decision Variables
- Instantiate binary variables `y[i]` for each facility `i` using `solver.IntVar(0, 1, ...)`.
- Instantiate continuous, non-negative flow variables `x[i][j]` for each facility-customer pair using `solver.NumVar(0, solver.infinity(), ...)`.

### Step 3 - Formulate Objective Function
- Construct the objective to minimize total cost: sum of fixed costs (`fixed_cost[i] * y[i]`) plus linear transportation costs (`transport_cost[i][j] * x[i][j]`).
- Use `solver.Objective()` and `SetCoefficient()` to add each term.

### Step 4 - Add Constraints
- **Demand Satisfaction**: For each customer `j`, add a constraint `sum(x[i][j] for i) == demand[j]`.
- **Capacity & Activation Linking**: For each facility `i`, add a constraint `sum(x[i][j] for j) <= capacity[i] * y[i]`. This ensures flow is zero if the facility is closed (`y[i]=0`).

### Formulation Template
```json
{
  "sets": [
    "facilities: list of facility identifiers",
    "customers: list of customer identifiers"
  ],
  "parameters": [
    "fixed_cost: dict[facility] -> cost",
    "capacity: dict[facility] -> maximum units",
    "demand: dict[customer] -> required units",
    "transport_cost: dict[facility, customer] -> cost per unit"
  ],
  "decision_variables": [
    "y: binary, 1 if facility is open",
    "x: continuous, non-negative flow from facility to customer"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i]) + sum(transport_cost[i][j] * x[i][j])"
  },
  "constraints": [
    "demand_satisfaction: for each customer j, sum(x[i][j]) == demand[j]",
    "capacity_linking: for each facility i, sum(x[i][j]) <= capacity[i] * y[i]"
  ]
}
```

### Common Pitfalls
- Forgetting to set an upper bound on flow variables, which can lead to unbounded models. Always define them as `NumVar(lb, ub, ...)`.
- Incorrectly implementing the linking constraint as separate constraints per flow, which is less efficient than the aggregated form.
- Not verifying that total facility capacity meets total demand before solving, which can lead to infeasibility.

## Solving stage

### Strategy Overview
Solve the MILP using the SCIP solver via OR-Tools. Configure solver parameters for performance, execute the solve, and implement robust status checking and solution extraction.

### Step 1 - Initialize Solver and Set Parameters
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Configure performance settings: set a time limit (`solver.SetTimeLimit()`) and number of threads (`solver.SetNumThreads()`).

### Step 2 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:`.
- If the status is not acceptable, handle the failure (e.g., print diagnostics, adjust model).

### Step 3 - Extract and Validate Solution
- Extract variable values using `.solution_value()` for `y[i]` and `x[i][j]`.
- Validate the solution by checking that all demand constraints are satisfied and no capacity constraints are violated.
- Calculate and report key metrics: total cost, list of open facilities, facility utilization rates.

### Code Usage
```python
# build model from formulation
# ... (model building steps as per Modeling stage)
# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL or status == solver.FEASIBLE:
    print(f"Objective value: {solver.Objective().Value()}")
    # Extract solution
    open_facilities = [i for i in facilities if y[i].solution_value() > 0.5]
    # Validate constraints
    # ... (verification logic)
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Failing to check solver status before extracting variable values, which can cause runtime errors.
- Not setting a MIP gap tolerance, potentially leading to long solve times for large instances.
- Omitting solution verification, which can miss subtle constraint violations due to numerical tolerances.

# Workflow 2 (Pyomo / Highs)

## Modeling stage

### Strategy Overview
This workflow models the problem using the Pyomo modeling language, providing a declarative and solver-agnostic interface. The model is solved using the Highs open-source MILP solver, which is integrated via the `highs` Pyomo solver factory.

### Step 1 - Define Abstract Sets and Parameters
- Use Pyomo `Set` components to define the index sets for facilities and customers.
- Use Pyomo `Param` components or plain dictionaries to store `fixed_cost`, `capacity`, `demand`, and `transport_cost`.

### Step 2 - Declare Decision Variables
- Declare binary variables `model.y` indexed by facilities, with domain `pyo.Binary`.
- Declare continuous variables `model.x` indexed by facility-customer pairs, with domain `pyo.NonNegativeReals`.

### Step 3 - Construct Objective Rule
- Define an `Objective` rule that returns the expression: `sum(fixed_cost[i] * model.y[i]) + sum(transport_cost[i,j] * model.x[i,j])`.
- Set the sense to `minimize`.

### Step 4 - Define Constraint Rules
- **Demand Rule**: Create a constraint `model.demand_con` indexed by customers, where the rule returns `sum(model.x[i,j] for i) == demand[j]`.
- **Capacity Rule**: Create a constraint `model.capacity_con` indexed by facilities, where the rule returns `sum(model.x[i,j] for j) <= capacity[i] * model.y[i]`.

### Formulation Template
```json
{
  "sets": [
    "F: set of facilities",
    "C: set of customers"
  ],
  "parameters": [
    "fixed_cost: param F",
    "capacity: param F",
    "demand: param C",
    "transport_cost: param F, C"
  ],
  "decision_variables": [
    "y: Var(F, domain=Binary)",
    "x: Var(F, C, domain=NonNegativeReals)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i] for i in F) + sum(transport_cost[i,j] * x[i,j] for i in F, j in C)"
  },
  "constraints": [
    "demand_satisfaction: for j in C, sum(x[i,j] for i in F) == demand[j]",
    "capacity_linking: for i in F, sum(x[i,j] for j in C) <= capacity[i] * y[i]"
  ]
}
```

### Common Pitfalls
- Using mutable objects (like lists) inside Pyomo rule functions, which can lead to unexpected behavior. Use model components or passed parameters.
- Not deactivating constraints or objectives when experimenting with model modifications, leading to incorrect formulations.
- Confusing Pyomo's `value()` function for evaluating expressions with variable values before the solution is loaded.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the Highs solver. Implement systematic error handling by checking solver status and termination condition before loading results. Extract and verify the solution.

### Step 1 - Instantiate Solver and Set Options
- Create the solver object: `solver = pyo.SolverFactory("highs")`.
- Configure solver options if needed, such as time limit (`time_limit`) or MIP gap (`mip_rel_gap`).

### Step 2 - Execute Solve and Inspect Results
- Call `results = solver.solve(model, tee=False)` (set `tee=True` for solver log).
- Inspect `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `ok` and termination condition is `optimal` or `feasible`.

### Step 3 - Load Solution and Perform Verification
- Use `model.solutions.load_from(results)` to load the solution into the model variables.
- Extract variable values using `pyo.value(model.y[i])` and `pyo.value(model.x[i,j])`.
- Programmatically verify that demand and capacity constraints are satisfied within a small numerical tolerance.

### Code Usage
```python
# build model from formulation
# ... (Pyomo model building steps)
# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Load results
    # model.solutions.load_from(results) # May be required depending on Pyomo version/setup
    obj_val = pyo.value(model.obj)
    # Extract and verify solution
    # ... (verification logic)
else:
    print("Solver failed:", results.solver.termination_condition)
```

### Common Pitfalls
- Assuming the solution is automatically loaded into the model; some Pyomo interfaces require an explicit `load_from` call.
- Not handling the case where the solver finds a feasible but not optimal solution, which may still be acceptable.
- Ignoring numerical precision when verifying constraints; use a tolerance (e.g., `1e-6`) for comparisons.
