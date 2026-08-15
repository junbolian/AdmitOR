---
name: Max-Min Distance Selection
description: |
  Select a fixed-size subset of elements to maximize the minimum pairwise distance, using MILP formulations with binary selection and pairwise logic variables.

---

# Workflow 1 (MILP with Big-M Constraints)

## Modeling stage

### Strategy Overview
This workflow models the problem as a Mixed-Integer Linear Program (MILP) using binary selection variables, auxiliary pairwise selection variables, and a big-M constraint to link the minimum distance variable to selected pairs. It is a direct, general-purpose formulation suitable for most MILP solvers.

### Step 1 - Define Core Selection Variables
- Create a binary decision variable `x[i]` for each element `i` in the candidate set `I`. `x[i] = 1` indicates the element is selected.
- Create a continuous variable `z` with a lower bound of 0 to represent the minimum pairwise distance among selected elements, which will be maximized.

### Step 2 - Enforce Selection Cardinality
- Add a linear constraint to select exactly `K` elements: `sum_{i in I} x[i] == K`.

### Step 3 - Linearize Pairwise Selection Logic
- For each ordered pair `(i,j)` in a relevant pair set `P` (e.g., `i < j`), create a binary variable `y[i,j]`.
- Add constraints to enforce `y[i,j] = 1` if and only if both `x[i] = 1` and `x[j] = 1`:
    - `y[i,j] <= x[i]`
    - `y[i,j] <= x[j]`
    - `y[i,j] >= x[i] + x[j] - 1`

### Step 4 - Link Minimum Distance to Selected Pairs
- For each pair `(i,j)` in `P`, add a big-M constraint: `z <= d[i,j] + M * (1 - y[i,j])`.
- Here, `d[i,j]` is the distance parameter, and `M` is a sufficiently large constant (e.g., `max_{i,j} d[i,j]`). This forces `z` to be less than or equal to the distance of every selected pair.

### Step 5 - Set Objective
- Set the objective to maximize the continuous variable `z`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of candidate elements.",
    "P: Set of ordered pairs (i,j) where i < j, or all relevant pairs."
  ],
  "parameters": [
    "K: Integer, number of elements to select.",
    "d[i,j]: Distance between elements i and j for (i,j) in P.",
    "M: Large constant, e.g., max_{i,j in P} d[i,j]."
  ],
  "decision_variables": [
    "x[i] ∈ {0,1} for i in I. 1 if element i is selected.",
    "y[i,j] ∈ {0,1} for (i,j) in P. 1 if both i and j are selected.",
    "z ≥ 0. Represents the minimum distance to maximize."
  ],
  "objective": {
    "sense": "max",
    "expression": "z"
  },
  "constraints": [
    "cardinality: sum_{i in I} x[i] == K",
    "logic_upper1: y[i,j] <= x[i] for (i,j) in P",
    "logic_upper2: y[i,j] <= x[j] for (i,j) in P",
    "logic_lower: y[i,j] >= x[i] + x[j] - 1 for (i,j) in P",
    "distance_link: z <= d[i,j] + M * (1 - y[i,j]) for (i,j) in P"
  ]
}
```

### Common Pitfalls
- Using an arbitrarily large `M` value without justification, which can cause numerical instability. Set `M` based on the maximum distance parameter.
- Defining symmetric pairs `(i,j)` and `(j,i)` in `P`, which creates duplicate constraints and variables. Use an ordered set like `i < j`.
- Omitting verification that the solved `z` equals the actual minimum distance among selected elements.

## Solving stage

### Strategy Overview
Solve the MILP model using a dedicated MILP solver via a low-level API (e.g., OR-Tools). The focus is on direct model construction, solver configuration, and robust solution extraction.

### Step 1 - Initialize Solver and Model
- Instantiate a MILP solver (e.g., SCIP, CBC) via its API wrapper.
- Create a model/solver object and set optional parameters like time limit and number of threads.

### Step 2 - Build Model from Formulation
- Declare all variables (`x`, `y`, `z`) with their correct types and bounds.
- Add the cardinality constraint using summation.
- Add the three linear constraints for each `y[i,j]` variable.
- Add the big-M distance linking constraint for each pair.
- Set the objective to maximize `z`.

### Step 3 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the result status. Accept both `OPTIMAL` and `FEASIBLE` statuses as valid solutions.

### Step 4 - Extract and Validate Solution
- Retrieve the value of `z` from the solver.
- For each `i` in `I`, check if `x[i].solution_value() > 0.5` to determine selected elements.
- (Optional) For each `(i,j)` in `P`, check `y[i,j].solution_value() > 0.5` to confirm selected pairs.
- Perform a post-solve verification: compute the actual minimum distance among the selected elements and compare it to the solver's `z` value.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... (Variable and constraint creation as per formulation)
solver.Maximize(z)

# solve with status / termination checks
status = solver.Solve()
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    selected = [i for i in I if x[i].solution_value() > 0.5]
    # ... (extract and verify)
else:
    # Handle no solution found
```

### Common Pitfalls
- Not checking for `FEASIBLE` status in addition to `OPTIMAL`, which may miss good solutions from early termination.
- Using a fixed, overly aggressive time limit for small problems, wasting resources.
- Failing to verify the solution, potentially missing model or solver errors.

---

# Workflow 2 (Pyomo-based Declarative Modeling)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling to declaratively define the same MILP structure. It emphasizes separation of model, data, and solver, improving modularity and reuse for different problem instances.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for the element set `model.I` and the pair set `model.P`.
- Declare `Param` objects for `K`, the distance dictionary `model.d`, and the big-M constant `model.M`.

### Step 2 - Define Decision Variables
- Declare `Var` objects: `model.x` (binary, indexed by `I`), `model.y` (binary, indexed by `P`), and `model.z` (non-negative continuous).

### Step 3 - Define Objective and Constraints Declaratively
- Define the objective rule: `maximize model.z`.
- Define constraint rules for:
    1. Cardinality: `sum(model.x[i] for i in model.I) == model.K`.
    2. Pairwise logic upper bounds: `model.y[i,j] <= model.x[i]` and `model.y[i,j] <= model.x[j]`.
    3. Pairwise logic lower bound: `model.y[i,j] >= model.x[i] + model.x[j] - 1`.
    4. Distance linking: `model.z <= model.d[i,j] + model.M * (1 - model.y[i,j])`.

### Step 4 - Instantiate Model with Data
- Create a data dictionary or `DataPortal` containing the actual sets and parameters.
- Use this data to create a model instance.

### Formulation Template
```json
{
  "sets": [
    "I: Abstract set of candidate elements.",
    "P: Abstract set of ordered pairs (i,j)."
  ],
  "parameters": [
    "K: Integer parameter, number to select.",
    "d: Parameter dictionary d[i,j] for (i,j) in P.",
    "M: Scalar parameter for big-M."
  ],
  "decision_variables": [
    "x: Indexed binary variable over I.",
    "y: Indexed binary variable over P.",
    "z: Scalar continuous variable (>=0)."
  ],
  "objective": {
    "sense": "max",
    "expression": "z"
  },
  "constraints": [
    "cardinality: sum(x[i] for i in I) == K",
    "logic_upper1: y[i,j] <= x[i] for (i,j) in P",
    "logic_upper2: y[i,j] <= x[j] for (i,j) in P",
    "logic_lower: y[i,j] >= x[i] + x[j] - 1 for (i,j) in P",
    "distance_link: z <= d[i,j] + M * (1 - y[i,j]) for (i,j) in P"
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's `AbstractModel` and `ConcreteModel` paradigms. Choose one based on whether data is separated from structure.
- Forgetting to create a model instance with data before solving when using an `AbstractModel`.
- Defining constraints with incorrect index rules, leading to missing or extra constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external solver interface (e.g., HiGHS, SCIP). Leverage Pyomo's solver manager to handle communication, and focus on status checking and structured result output.

### Step 1 - Select Solver and Set Options
- Instantiate a solver object (e.g., `SolverFactory('highs')`).
- Configure solver options such as time limit, relative gap tolerance, and thread count.

### Step 2 - Solve and Inspect Termination
- Call `solver.solve(model)`.
- Check both the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract Solution to Structured Output
- Access the objective value via `pyo.value(model.z)` or `pyo.value(model.obj)`.
- Extract selected elements by iterating over `model.x` and filtering values above a threshold (e.g., 0.5).
- Compile results (status, objective value, selected list) into a structured format like a dictionary or JSON.

### Step 4 - Validate and Report
- Recompute the minimum distance from the selected elements as a sanity check.
- Log or return the structured results.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=I_data)
model.P = pyo.Set(initialize=P_data, dimen=2)
# ... (define parameters, variables, constraints, objective)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model, options={'time_limit': 60})
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    # ... (extract and structure results)
```

### Common Pitfalls
- Relying solely on the solver status without checking the termination condition, which may indicate suboptimal or incomplete solutions.
- Not setting an appropriate `mip_rel_gap` (e.g., to 0.0 or a small tolerance) when an optimal solution is required.
- Extracting variable values without using `pyo.value()`, which returns the underlying object, not the numeric solution.
