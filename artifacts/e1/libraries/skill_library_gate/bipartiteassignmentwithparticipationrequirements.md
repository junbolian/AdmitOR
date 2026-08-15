---
name: BipartiteAssignmentWithParticipationRequirements
description: |
  Model bipartite assignment problems with minimum participation and quantity commitments using continuous-binary variable pairs, then solve with MIP solvers via OR-Tools or Pyomo.
---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
Model the problem as a Mixed-Integer Linear Program (MILP) using the OR-Tools CP-SAT or SCIP wrapper. The formulation pairs continuous flow variables with binary activation variables to enforce minimum quantity commitments and participation counts.

### Step 1 - Define Sets and Parameters
- Identify two distinct sets: `PRODUCERS` (sources) and `CONTRACTS` (destinations).
- Define parameters: `cost[producer][contract]`, `capacity[producer]`, `demand[contract]`, `min_delivery[producer]`, `min_producers[contract]`.

### Step 2 - Create Decision Variables
- Create continuous assignment variables `x[i][j] >= 0` for the quantity allocated from producer `i` to contract `j`.
- Create binary participation variables `y[i][j] ∈ {0,1}` indicating if producer `i` is assigned to contract `j`.

### Step 3 - Formulate Core Constraints
- **Capacity Limit**: For each producer `i`, sum of `x[i][j]` over all contracts `j` ≤ `capacity[i]`.
- **Demand Satisfaction**: For each contract `j`, sum of `x[i][j]` over all producers `i` ≥ `demand[j]`.
- **Minimum Participation Count**: For each contract `j`, sum of `y[i][j]` over all producers `i` ≥ `min_producers[j]`.
- **Minimum Assignment if Selected**: For each pair `(i,j)`, `x[i][j]` ≥ `min_delivery[i] * y[i][j]`.
- **Logical Upper Bound**: For each pair `(i,j)`, `x[i][j]` ≤ `capacity[i] * y[i][j]`.

### Step 4 - Define Objective
- Minimize total linear cost: Sum of `cost[i][j] * x[i][j]` over all producer-contract pairs.

### Formulation Template
```json
{
  "sets": ["PRODUCERS", "CONTRACTS"],
  "parameters": [
    "cost[PRODUCERS][CONTRACTS]",
    "capacity[PRODUCERS]",
    "demand[CONTRACTS]",
    "min_delivery[PRODUCERS]",
    "min_producers[CONTRACTS]"
  ],
  "decision_variables": [
    "x[PRODUCERS][CONTRACTS] (continuous, >=0)",
    "y[PRODUCERS][CONTRACTS] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in PRODUCERS for j in CONTRACTS)"
  },
  "constraints": [
    "sum(x[i][j] for j in CONTRACTS) <= capacity[i] for i in PRODUCERS",
    "sum(x[i][j] for i in PRODUCERS) >= demand[j] for j in CONTRACTS",
    "sum(y[i][j] for i in PRODUCERS) >= min_producers[j] for j in CONTRACTS",
    "x[i][j] >= min_delivery[i] * y[i][j] for i in PRODUCERS, j in CONTRACTS",
    "x[i][j] <= capacity[i] * y[i][j] for i in PRODUCERS, j in CONTRACTS"
  ]
}
```

### Common Pitfalls
- Using an arbitrarily large `M` in the logical upper bound constraint; use the natural `capacity[i]` for a tight formulation.
- Forgetting to enforce the minimum participation count constraint, leading to solutions with insufficient diversity.
- Not linking the binary variable to both the lower and upper bound, which can allow `x[i][j] > 0` while `y[i][j] = 0`.

## Solving stage

### Strategy Overview
Solve the MILP using the OR-Tools SCIP or CP-SAT solver. Configure solver parameters for performance and reproducibility, then extract and validate the solution.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Set a time limit (e.g., `solver.SetTimeLimit(30000)` for 30 seconds).
- Set the number of threads (e.g., `solver.SetNumThreads(4)`).
- For CP-SAT, set a deterministic seed (e.g., `cp_model.CpModel().AddHint` is not needed; use `model.parameters.random_seed = 42`).

### Step 2 - Build Model from Formulation
- Create variables `x` and `y` as dictionaries indexed by `(i,j)`.
- Add constraints using `solver.Add()` in loops corresponding to the formulation.
- Define the objective using `solver.Objective()` and `SetCoefficient()`.

### Step 3 - Solve and Check Status
- Call `solver.Solve()`.
- Check if the status is `OPTIMAL` or `FEASIBLE`. If not, handle the infeasible/error case.

### Step 4 - Extract and Validate Solution
- Extract variable values using `x[i,j].solution_value()` and `y[i,j].solution_value()`.
- Programmatically verify all constraints with a small tolerance (e.g., 1e-6): capacity, demand, participation counts, and minimum assignment rules.
- Summarize results: total cost, assignments per contract, and producer utilization.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

x = {}
y = {}
for i in PRODUCERS:
    for j in CONTRACTS:
        x[i, j] = solver.NumVar(0, solver.infinity(), f"x_{i}_{j}")
        y[i, j] = solver.BoolVar(f"y_{i}_{j}")

# Add constraints as per formulation
for i in PRODUCERS:
    solver.Add(solver.Sum(x[i, j] for j in CONTRACTS) <= capacity[i])
# ... add other constraints

objective = solver.Objective()
for i in PRODUCERS:
    for j in CONTRACTS:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    # Extract and validate solution
    for i in PRODUCERS:
        for j in CONTRACTS:
            x_val = x[i, j].solution_value()
            y_val = y[i, j].solution_value()
            # ... process values
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.
- Assuming `FEASIBLE` status implies all constraints are satisfied; always perform explicit verification.
- Extracting variable values without checking the solver status first, leading to errors.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling syntax, creating a clean separation between model definition and solver backend. Use the HiGHS or CBC solver via the Pyomo interface.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `model.PRODUCERS` and `model.CONTRACTS`.
- Define `Param` objects for `cost`, `capacity`, `demand`, `min_delivery`, and `min_producers`, indexed appropriately.

### Step 2 - Declare Variables with Domains
- Declare `model.x` as a `Var` indexed by `(PRODUCERS, CONTRACTS)` with domain `NonNegativeReals`.
- Declare `model.y` as a `Var` indexed by `(PRODUCERS, CONTRACTS)` with domain `Binary`.

### Step 3 - Construct Constraints via Rules
- Define a rule for the capacity constraint that sums `model.x[i,j]` over `j` for each `i`.
- Define a rule for the demand constraint that sums `model.x[i,j]` over `i` for each `j`.
- Define rules for the minimum participation, minimum assignment, and logical upper bound constraints using indexed `Constraint` declarations.

### Step 4 - Define Objective Expression
- Define `model.obj` as an `Objective` with `sense=minimize` and `expr=sum(cost[i,j] * model.x[i,j] for i in model.PRODUCERS for j in model.CONTRACTS)`.

### Formulation Template
```json
{
  "sets": ["PRODUCERS", "CONTRACTS"],
  "parameters": [
    "cost[PRODUCERS, CONTRACTS]",
    "capacity[PRODUCERS]",
    "demand[CONTRACTS]",
    "min_delivery[PRODUCERS]",
    "min_producers[CONTRACTS]"
  ],
  "decision_variables": [
    "x[PRODUCERS, CONTRACTS] (NonNegativeReals)",
    "y[PRODUCERS, CONTRACTS] (Binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in PRODUCERS for j in CONTRACTS)"
  },
  "constraints": [
    "sum(x[i,j] for j in CONTRACTS) <= capacity[i] for i in PRODUCERS",
    "sum(x[i,j] for i in PRODUCERS) >= demand[j] for j in CONTRACTS",
    "sum(y[i,j] for i in PRODUCERS) >= min_producers[j] for j in CONTRACTS",
    "x[i,j] >= min_delivery[i] * y[i,j] for (i,j) in PRODUCERS*CONTRACTS",
    "x[i,j] <= capacity[i] * y[i,j] for (i,j) in PRODUCERS*CONTRACTS"
  ]
}
```

### Common Pitfalls
- Using `concrete=True` without properly initializing all parameters, leading to instantiation errors.
- Defining constraint rules with incorrect indexing or using Python's `sum` inside Pyomo expressions without `pyo.summation`.
- Not using `pyo.value()` to extract numerical values from Pyomo components after solving.

## Solving stage

### Strategy Overview
Instantiate the Pyomo model with data, select a solver (HiGHS or CBC), configure solver options, solve, and then verify the solution using Pyomo's result inspection methods.

### Step 1 - Instantiate Model and Load Data
- Create a concrete model instance.
- Load parameter data into the model's `Param` objects (e.g., from dictionaries or dataframes).

### Step 2 - Select and Configure Solver
- Create a solver object using `SolverFactory('highs')` or `SolverFactory('cbc')`.
- Set solver options: `time_limit=30`, `mip_rel_gap=0.0` (or a small tolerance), and `threads=4`.

### Step 3 - Solve and Inspect Termination Condition
- Call `solver.solve(model, tee=False)`.
- Check the solver status (`model.solutions.status`) and termination condition (`model.solutions.termination_condition`). Accept `optimal` or `feasible`.

### Step 4 - Extract and Verify Solution
- Use `pyo.value(model.x[i,j])` and `pyo.value(model.y[i,j])` to get variable values.
- Programmatically verify all constraints with tolerance, similar to Workflow 1.
- Calculate and report the objective value and key metrics.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.PRODUCERS = pyo.Set(initialize=PRODUCERS_LIST)
model.CONTRACTS = pyo.Set(initialize=CONTRACTS_LIST)

model.cost = pyo.Param(model.PRODUCERS, model.CONTRACTS, initialize=cost_dict)
model.capacity = pyo.Param(model.PRODUCERS, initialize=capacity_dict)
# ... initialize other parameters

model.x = pyo.Var(model.PRODUCERS, model.CONTRACTS, domain=pyo.NonNegativeReals)
model.y = pyo.Var(model.PRODUCERS, model.CONTRACTS, domain=pyo.Binary)

def capacity_rule(m, i):
    return sum(m.x[i, j] for j in m.CONTRACTS) <= m.capacity[i]
model.capacity_con = pyo.Constraint(model.PRODUCERS, rule=capacity_rule)
# ... define other constraints

model.obj = pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for i in model.PRODUCERS for j in model.CONTRACTS), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = -1.0  # Use -1.0 to let solver default to its own gap, or set to 0.0 for optimality
results = solver.solve(model)

if model.solutions.status in [pyo.SolverStatus.ok, pyo.SolverStatus.warning] and \
   model.solutions.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    # Extract and validate solution
    for i in model.PRODUCERS:
        for j in model.CONTRACTS:
            x_val = pyo.value(model.x[i, j])
            y_val = pyo.value(model.y[i, j])
            # ... process values
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Setting `mip_rel_gap` to a negative value (other than -1.0) which may be invalid for some solvers; use `0.0` or a small positive number.
- Not checking both the solver status and termination condition, potentially accepting suboptimal or failed solutions.
- Using `tee=True` in production, which can clutter logs; reserve it for debugging.
