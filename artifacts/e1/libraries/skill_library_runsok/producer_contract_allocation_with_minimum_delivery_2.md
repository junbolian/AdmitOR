---
name: Producer-Contract Allocation with Minimum Delivery
description: |
  Formulate and solve mixed-integer linear programs for allocating flows from producers to contracts with minimum delivery per selection and minimum supplier counts, using either Pyomo with open-source solvers or direct solver APIs.

---

# Workflow 1 (Pyomo with Open-Source Backend)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to create a portable MILP formulation, decoupling model logic from solver choice. It is designed for flexibility and ease of validation, suitable for environments where open-source solvers like CBC or SCIP are preferred.

### Step 1 - Define Sets and Parameters
- Declare sets for producers and contracts as model components.
- Load or define all necessary parameters: capacity, demand, minimum producers per contract, minimum delivery per producer, and unit cost matrix.

### Step 2 - Create Decision Variables
- Define continuous flow variables for each producer-contract pair, representing allocated quantity.
- Define binary assignment variables for each producer-contract pair, indicating selection.

### Step 3 - Formulate Objective Function
- Construct a linear objective to minimize total cost, summing the product of flow variables and their unit costs.

### Step 4 - Implement Core Constraints
- Add supply capacity constraints limiting total outflow from each producer.
- Add demand satisfaction constraints ensuring each contract's total inflow meets its requirement.
- Add minimum supplier constraints requiring a minimum number of selected producers per contract.

### Step 5 - Link Variables and Enforce Minimum Delivery
- Use Big-M constraints to force flow to zero if the binary assignment is zero (`x <= capacity * y`).
- Enforce a minimum delivery threshold when a producer is selected for a contract (`x >= min_delivery * y`).

### Formulation Template
```json
{
  "sets": ["producers", "contracts"],
  "parameters": [
    "capacity[producers]",
    "demand[contracts]",
    "min_producers[contracts]",
    "min_delivery[producers]",
    "unit_cost[producers, contracts]"
  ],
  "decision_variables": [
    "x[producers, contracts] : continuous, non-negative",
    "y[producers, contracts] : binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( unit_cost[i,j] * x[i,j] for i in producers for j in contracts )"
  },
  "constraints": [
    "supply_capacity[i]: sum( x[i,j] for j in contracts ) <= capacity[i] for i in producers",
    "demand_requirement[j]: sum( x[i,j] for i in producers ) >= demand[j] for j in contracts",
    "min_suppliers[j]: sum( y[i,j] for i in producers ) >= min_producers[j] for j in contracts",
    "linking_upper[i,j]: x[i,j] <= capacity[i] * y[i,j] for i in producers, j in contracts",
    "min_delivery_if_selected[i,j]: x[i,j] >= min_delivery[i] * y[i,j] for i in producers, j in contracts"
  ]
}
```

### Common Pitfalls
- Using an overly large Big-M value in linking constraints, which weakens the LP relaxation and slows solving.
- Misinterpreting minimum delivery as a total per producer instead of a per-contract-per-producer requirement.
- Forgetting to index parameters correctly, leading to silent constraint errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory, focusing on robust configuration, status checking, and solution validation. This approach ensures reliability and clear diagnostics.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver object (e.g., `SolverFactory('cbc')`).
- Configure key parameters: time limit, optimality gap tolerance, thread count, and random seed for reproducibility.

### Step 2 - Solve and Check Status
- Execute the solve command on the model instance.
- Interrogate both the solver status and termination condition to distinguish between optimal, feasible, and failed solves.

### Step 3 - Extract and Validate Solution
- If the solve was successful, retrieve variable values using `pyo.value()`.
- Programmatically verify that all model constraints are satisfied within a small tolerance.
- Calculate derived metrics like producer utilization and contract coverage.

### Step 4 - Handle Infeasibility or Timeouts
- For infeasible solves, use solver conflict refiner or analyze relaxed constraints to diagnose issues.
- If time limit is reached, extract and report the best feasible solution found.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (using sets 'P' and 'C', parameters, variables, objective, constraints)
model = create_pyomo_model(producers, contracts, data)

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 60
solver.options['ratio'] = 1e-6
solver.options['threads'] = 4

results = solver.solve(model)

# Check status
if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimal solution found.")
    elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
        print("Feasible solution found (not proven optimal).")
    else:
        print(f"Solver stopped with condition: {results.solver.termination_condition}")
    # Proceed to extract solution
    solution = extract_solution(model)
    validate_solution(solution, data)
else:
    print("Solver failed. Status:", results.solver.status)
```

### Common Pitfalls
- Assuming `solver.status == ok` means optimality; must also check `termination_condition`.
- Not setting a time limit, risking excessively long runs on large instances.
- Extracting variable values without checking if a feasible solution exists, leading to errors.

# Workflow 2 (Direct Solver API with SCIP)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., PySCIPOpt or ortools) to build the model natively, offering fine-grained control over constraints and solver parameters. It is suited for performance-critical applications or when leveraging advanced solver features.

### Step 1 - Initialize Model and Add Variables
- Create a new solver model object.
- Directly add continuous and binary variables, naming them systematically.

### Step 2 - Set Objective Function
- Define the objective sense (minimization) and set the linear cost expression using the solver's native methods.

### Step 3 - Add Constraints Efficiently
- Add supply capacity constraints as linear expressions.
- Add demand satisfaction constraints.
- Add minimum supplier count constraints using sums of binary variables.
- Implement linking and minimum delivery constraints using the solver's `addCons` method with appropriate coefficients.

### Step 4 - Add Optional Performance Enhancements
- Introduce symmetry-breaking constraints (e.g., order binary variables by cost).
- Set variable priorities or branching rules if supported by the solver.

### Formulation Template
```json
{
  "sets": ["producers", "contracts"],
  "parameters": [
    "capacity[producers]",
    "demand[contracts]",
    "min_producers[contracts]",
    "min_delivery[producers]",
    "unit_cost[producers, contracts]"
  ],
  "decision_variables": [
    "x[producers, contracts] : continuous, >= 0",
    "y[producers, contracts] : binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( unit_cost[i][j] * x[i][j] for i in producers for j in contracts )"
  },
  "constraints": [
    "supply_capacity[i]: sum_j x[i][j] <= capacity[i]",
    "demand_requirement[j]: sum_i x[i][j] >= demand[j]",
    "min_suppliers[j]: sum_i y[i][j] >= min_producers[j]",
    "linking_upper[i][j]: x[i][j] - capacity[i] * y[i][j] <= 0",
    "min_delivery_if_selected[i][j]: x[i][j] - min_delivery[i] * y[i][j] >= 0"
  ]
}
```

### Common Pitfalls
- Incorrectly ordering coefficients when building linear expressions, leading to wrong constraints.
- Neglecting to set upper bounds on continuous variables, which can be implicitly defined via linking constraints.
- Creating duplicate constraints due to nested loops, wasting memory and slowing model construction.

## Solving stage

### Strategy Overview
Directly control the solver's optimization process, configure advanced parameters, and extract detailed solution information. This allows for iterative solving and custom solution analysis.

### Step 1 - Configure Solver Parameters
- Set limits: time, node count, or gap tolerance.
- Enable or disable specific heuristics and cuts.
- Set output verbosity for debugging.

### Step 2 - Execute Optimization
- Call the solver's optimize method.
- Monitor progress through callback functions or printed output if enabled.

### Step 3 - Analyze Solution and Status
- Query the solver's status code to determine if optimal, feasible, infeasible, or unbounded.
- If feasible, retrieve variable values and objective value.
- Compute constraint slack values to verify satisfaction.

### Step 4 - Implement Iterative Refinement
- If the solution violates any intended logic (e.g., minimum delivery), add cutting planes or constraints and re-solve.
- For ambiguous requirements, solve alternative formulations and compare results.

### Code Usage
```python
# Example using PySCIPOpt
from pyscipopt import Model

# build model from formulation
model = Model("ProducerContractAllocation")

# Create variables
x_vars = {}
y_vars = {}
for i in producers:
    for j in contracts:
        x_vars[(i,j)] = model.addVar(name=f"x_{i}_{j}", vtype="C", lb=0)
        y_vars[(i,j)] = model.addVar(name=f"y_{i}_{j}", vtype="B")

# Set objective
model.setObjective(
    sum(unit_cost[i][j] * x_vars[(i,j)] for i in producers for j in contracts),
    sense="minimize"
)

# Add constraints (example: supply capacity)
for i in producers:
    model.addCons(
        sum(x_vars[(i,j)] for j in contracts) <= capacity[i],
        name=f"cap_{i}"
    )
# ... add other constraints similarly

# solve with status / termination checks
model.setRealParam("limits/time", 60)
model.setRealParam("limits/gap", 1e-6)
model.optimize()

status = model.getStatus()
if status == "optimal":
    print("Optimal solution found.")
elif status == "timelimit":
    print("Time limit reached, best solution found.")
    # Still may have a feasible solution
elif status == "infeasible":
    print("Model is infeasible.")
    # Perform infeasibility analysis
    return

if model.getNSols() > 0:
    sol = model.getBestSol()
    total_cost = model.getObjVal()
    # Extract variable values from sol
```

### Common Pitfalls
- Not checking if a solution exists (`getNSols() > 0`) before trying to access solution values.
- Misinterpreting solver status codes (e.g., "timelimit" may still have a feasible incumbent).
- Forgetting to set a gap tolerance, causing the solver to run indefinitely seeking optimality.
