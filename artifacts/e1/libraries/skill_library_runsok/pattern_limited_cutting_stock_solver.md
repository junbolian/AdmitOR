---
name: Pattern-Limited Cutting Stock Solver
description: |
  Solves cutting stock problems with predefined patterns and usage limits via integer programming, minimizing total resource consumption while satisfying demand constraints.
---

# Workflow 1 (SCIP via OR-Tools)

## Modeling stage

### Strategy Overview
Model the problem as an integer linear program using the OR-Tools CP-SAT or MPSolver interface, focusing on efficient variable and constraint construction with explicit upper bounds.

### Step 1 - Define Data Structures
- Organize pattern yields as a 2D list `pattern_yield[pattern_index][width_index]`.
- Store demand requirements as a list `demand[width_index]`.
- Store pattern usage limits as a list `usage_limit[pattern_index]`.

### Step 2 - Create Integer Variables
- For each pattern, create an integer variable `x[p]` with lower bound 0 and upper bound `usage_limit[p]`.
- Use `solver.IntVar(lower_bound, upper_bound, name)` to define the variable.

### Step 3 - Formulate Demand Constraints
- For each product width, create a linear constraint: sum over patterns of `(pattern_yield[p][w] * x[p]) >= demand[w]`.
- Use `solver.Constraint(demand_value, solver.infinity())` and set coefficients via `SetCoefficient()`.

### Step 4 - Set Objective Function
- Define the objective to minimize total rolls: sum over all pattern variables `x[p]`.
- Use `objective = solver.Objective()` and set coefficients to 1 for each variable, then call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "P: set of patterns",
    "W: set of product widths"
  ],
  "parameters": [
    "yield_pw: yield of width w from pattern p",
    "demand_w: required units of width w",
    "limit_p: maximum usage of pattern p"
  ],
  "decision_variables": [
    "x_p: integer, non-negative, number of times pattern p is used"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{p in P} x_p"
  },
  "constraints": [
    "demand_satisfaction_w: sum_{p in P} yield_pw * x_p >= demand_w, for all w in W",
    "usage_limit_p: x_p <= limit_p, for all p in P"
  ]
}
```

### Common Pitfalls
- Forgetting to set upper bounds on integer variables, leading to unbounded or inefficient search.
- Mismatching indices between pattern yield matrix and demand array, causing incorrect constraint coefficients.
- Using floating-point values for integer coefficients, which can cause precision issues in the solver.

## Solving stage

### Strategy Overview
Solve the model using the SCIP solver via OR-Tools wrapper, configure performance settings, and implement robust solution extraction and verification.

### Step 1 - Configure Solver and Solve
- Create solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Set time limit: `solver.SetTimeLimit(time_limit_millis)`.
- Set number of threads: `solver.SetNumThreads(num_threads)`.
- Call `solver.Solve()`.

### Step 2 - Check Solver Status and Extract Solution
- Check status: `if solver.ResultStatus() == pywraplp.Solver.OPTIMAL` or `FEASIBLE`.
- Extract variable values: `x[p].solution_value()`.
- Compute objective value: `solver.Objective().Value()`.

### Step 3 - Verify Solution Feasibility
- Recalculate total production per width from extracted variable values and compare to demand.
- Verify each pattern usage is within its specified limit.
- Log any constraint violations for debugging.

### Step 4 - (Optional) Verify Optimality
- Add a new constraint: sum of all pattern variables `<= (current_best_objective - 1)`.
- Attempt to solve again; infeasibility confirms the original solution's optimality.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... variable and constraint creation ...
objective = solver.Objective()
for p in patterns:
    objective.SetCoefficient(x[p], 1)
objective.SetMinimization()

# solve with status / termination checks
result_status = solver.Solve()
if result_status == pywraplp.Solver.OPTIMAL:
    obj_value = objective.Value()
    solution = [x[p].solution_value() for p in patterns]
    # ... verification steps ...
elif result_status == pywraplp.Solver.FEASIBLE:
    # handle feasible but not optimal
    pass
else:
    # handle infeasible or error
    pass
```

### Common Pitfalls
- Not checking solver status before accessing solution values, leading to runtime errors.
- Omitting time limits for large instances, potentially causing indefinite runtimes.
- Failing to verify the solution against original constraints, which may miss solver numerical errors.

# Workflow 2 (CBC/Highs via Pyomo)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model syntax, leveraging set-based indexing for clarity and ease of maintenance, targeting open-source MILP solvers.

### Step 1 - Define Model and Sets
- Create a Pyomo ConcreteModel or AbstractModel.
- Define sets: `model.P` for patterns and `model.W` for widths.

### Step 2 - Define Parameters
- Load pattern yield as a parameter `model.yield_pw` indexed by `(p, w)`.
- Load demand as a parameter `model.demand_w` indexed by `w`.
- Load pattern usage limit as a parameter `model.limit_p` indexed by `p`.

### Step 3 - Define Decision Variables
- Define integer, non-negative variables `model.x[p]` with domain `pyo.NonNegativeIntegers`.
- Optionally set explicit bounds: `model.x[p].setlb(0); model.x[p].setub(model.limit[p])`.

### Step 4 - Formulate Constraints and Objective
- Demand satisfaction: `model.demand_constraint[w] = sum(model.yield_pw[p, w] * model.x[p] for p in model.P) >= model.demand_w`.
- Objective: `model.obj = pyo.Objective(expr=sum(model.x[p] for p in model.P), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "P: set of patterns",
    "W: set of product widths"
  ],
  "parameters": [
    "yield_pw: yield of width w from pattern p",
    "demand_w: required units of width w",
    "limit_p: maximum usage of pattern p"
  ],
  "decision_variables": [
    "x_p: integer, non-negative, number of times pattern p is used"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{p in P} x_p"
  },
  "constraints": [
    "demand_satisfaction_w: sum_{p in P} yield_pw * x_p >= demand_w, for all w in W",
    "usage_limit_p: x_p <= limit_p, for all p in P"
  ]
}
```

### Common Pitfalls
- Using abstract models without properly initializing parameters before instantiation, causing data errors.
- Neglecting to set variable upper bounds within Pyomo, relying solely on separate constraints, which can reduce solver presolve effectiveness.
- Inefficiently iterating over large sets within rule functions, impacting model construction time.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or Highs solver via SolverFactory, configure optimality gap and time limits, and implement detailed solution validation.

### Step 1 - Select and Configure Solver
- Create solver instance: `solver = pyo.SolverFactory('cbc')` or `pyo.SolverFactory('highs')`.
- Set solver options: `options={'seconds': time_limit, 'ratio': 0.0, 'threads': num_threads}`.

### Step 2 - Solve and Check Termination Conditions
- Call `results = solver.solve(model, tee=False, options=options)`.
- Check termination condition: `results.solver.termination_condition` for `optimal` or `feasible`.
- Check solver status: `results.solver.status` should be `ok`.

### Step 3 - Extract and Validate Solution
- Extract variable values: `model.x[p].value`.
- Compute total rolls from extracted values.
- Programmatically verify all demand and usage limit constraints are satisfied.

### Step 4 - Perform Optimality Assurance
- If termination condition is `feasible`, note the optimality gap.
- To test optimality, add a constraint `sum(model.x[p] for p in model.P) <= (current_best - 1)` and resolve; handle infeasibility detection.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... set, parameter, variable, constraint, objective definition ...

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, options={'seconds': 30, 'ratio': 0.0})
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    obj_value = pyo.value(model.obj)
    solution = [pyo.value(model.x[p]) for p in model.P]
    # ... verification steps ...
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    # handle feasible solution
    pass
else:
    # handle infeasible or error
    pass
```

### Common Pitfalls
- Confusing solver status (`status`) with termination condition (`termination_condition`), leading to incorrect interpretation of results.
- Not setting `ratio` (optimality gap) to 0.0 when an exact integer solution is required.
- Accessing `.value` of variables before checking solver status, which may be undefined.
