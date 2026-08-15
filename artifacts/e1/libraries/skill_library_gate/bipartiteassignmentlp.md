---
name: BipartiteAssignmentLP
description: |
  Model and solve linear assignment problems with supply limits, demand requirements, and per-pair capacity constraints using continuous flow variables.

---

# Workflow 1 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
Model the problem as a bipartite flow network using OR-Tools' linear solver API. Define continuous variables with explicit bounds, build constraints via coefficient accumulation, and structure the model for direct solver input.

### Step 1 - Define Data Structures
- Represent supply nodes, demand nodes, and assignment pairs as lists or ranges.
- Store parameters (availability, requirement, cost, max_per_assignment) in nested dictionaries or 2D lists for O(1) access during model building.

### Step 2 - Create Decision Variables
- Instantiate a continuous variable for each supply-demand pair using `solver.NumVar(lb, ub, name)`.
- Set the upper bound (`ub`) directly to `max_per_assignment[i][j]` to enforce individual assignment limits.

### Step 3 - Formulate Supply Constraints
- For each supply node `i`, create a constraint object: `solver.Constraint(-inf, availability[i])`.
- For each demand node `j` connected to `i`, add the variable's coefficient (1.0) using `constraint.SetCoefficient(var, 1.0)`.

### Step 4 - Formulate Demand Constraints
- For each demand node `j`, create a constraint object: `solver.Constraint(requirement[j], inf)`.
- For each supply node `i` connected to `j`, add the variable's coefficient (1.0) to the constraint.

### Step 5 - Define Linear Objective
- Create the objective object: `solver.Objective()`.
- For each variable, set its coefficient to `cost_per_unit[i][j]` using `objective.SetCoefficient(var, cost)`.
- Set the objective sense to minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "supply_nodes",
    "demand_nodes"
  ],
  "parameters": [
    "availability[supply_nodes]",
    "requirement[demand_nodes]",
    "cost_per_unit[supply_nodes][demand_nodes]",
    "max_per_assignment[supply_nodes][demand_nodes]"
  ],
  "decision_variables": [
    "assignment_quantity[supply_nodes][demand_nodes] (continuous, bounded)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_per_unit[i][j] * assignment_quantity[i][j] for i in supply_nodes, j in demand_nodes)"
  },
  "constraints": [
    "supply_limit[i]: sum(assignment_quantity[i][j] for j in demand_nodes) <= availability[i]",
    "demand_satisfaction[j]: sum(assignment_quantity[i][j] for i in supply_nodes) >= requirement[j]",
    "assignment_limit[i][j]: assignment_quantity[i][j] <= max_per_assignment[i][j] (enforced as variable bound)"
  ]
}
```

### Common Pitfalls
- Forgetting to set the objective sense, leaving it as default (minimization).
- Using infinite bounds (`solver.infinity()`) incorrectly, causing unbounded constraints.
- Not pre-checking total supply vs. total demand, which can lead to infeasibility without clear diagnostics.

## Solving stage

### Strategy Overview
Solve the built model using an appropriate OR-Tools linear solver backend (GLOP for LP, CBC/SCIP for MIP). Perform rigorous solution verification, cross-validate with alternative solvers, and output a structured assignment breakdown.

### Step 1 - Select Solver and Solve
- For pure LP, instantiate the solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Call `solver.Solve()` and capture the result status.

### Step 2 - Check Solver Status
- Evaluate `result_status = solver.Solve()`.
- Map the status to user-friendly messages (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNBOUNDED`).

### Step 3 - Extract and Verify Solution
- If status is `OPTIMAL` or `FEASIBLE`, retrieve the objective value: `solver.Objective().Value()`.
- For each variable, get its solution value: `var.solution_value()`.
- Implement a verification function that recalculates constraint left-hand sides and compares them against limits with a numerical tolerance (e.g., `1e-6`).

### Step 4 - Cross-Validate (Optional)
- Solve the same model with a different backend (e.g., CBC) to confirm optimality and solution stability.
- Compare objective values and key variable values across solvers.

### Step 5 - Report Structured Results
- Print non-zero assignments with their cost contributions.
- Summarize supply utilization percentages and demand fulfillment rates.
- Output the total cost and solver status for auditability.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (build variables, constraints, objective as per modeling stage)

# solve with status / termination checks
result_status = solver.Solve()
if result_status == solver.OPTIMAL or result_status == solver.FEASIBLE:
    print(f'Objective value =', solver.Objective().Value())
    # Extract and verify variable values
    for i in supply_nodes:
        for j in demand_nodes:
            var = assignment_vars[i][j]
            val = var.solution_value()
            if val > 1e-6:
                print(f'  x[{i},{j}] = {val}')
    # Call verification function
    verify_solution(assignment_vars, availability, requirement, max_per_assignment)
else:
    print('The problem does not have an optimal solution.')
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; always check for `OPTIMAL` if global optimum is required.
- Not handling numerical precision when checking variable bounds or constraint satisfaction, leading to false infeasibility reports.
- Omitting solver time limits for large instances, potentially causing hangs.

---

# Workflow 2 (PuLP Modeling Library)

## Modeling stage

### Strategy Overview
Model the assignment problem using PuLP's high-level, algebraic syntax. Leverage its built-in constraint and objective builders, and rely on its robust integration with open-source solvers like CBC for reliable solving.

### Step 1 - Initialize Problem and Sets
- Create a PuLP problem instance: `pulp.LpProblem("Assignment", pulp.LpMinimize)`.
- Define index sets for supply and demand as Python lists.

### Step 2 - Create Variables with Bounds
- Use dictionary comprehension to create a variable for each pair: `pulp.LpVariable(f"x_{i}_{j}", lowBound=0, upBound=max_capacity[i][j])`.
- Store variables in a dictionary keyed by `(i, j)` tuple.

### Step 3 - Add Demand Satisfaction Constraints
- For each demand node `j`, add a constraint: `prob += pulp.lpSum(x[(i, j)] for i in supply_nodes) >= requirement[j]`.

### Step 4 - Add Supply Limit Constraints
- For each supply node `i`, add a constraint: `prob += pulp.lpSum(x[(i, j)] for j in demand_nodes) <= availability[i]`.

### Step 5 - Set Linear Cost Objective
- Define the objective using `pulp.lpSum`: `prob += pulp.lpSum(cost[i][j] * x[(i, j)] for (i, j) in x.keys())`.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "tasks"
  ],
  "parameters": [
    "availability[resources]",
    "requirement[tasks]",
    "cost[resources][tasks]",
    "max_capacity[resources][tasks]"
  ],
  "decision_variables": [
    "assignment_quantity[resources][tasks] (continuous, bounded)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * assignment_quantity[i][j] for i in resources, j in tasks)"
  },
  "constraints": [
    "supply_limit[i]: sum(assignment_quantity[i][j] for j in tasks) <= availability[i]",
    "demand_satisfaction[j]: sum(assignment_quantity[i][j] for i in resources) >= requirement[j]",
    "pairwise_capacity[i][j]: assignment_quantity[i][j] <= max_capacity[i][j] (enforced as variable bound)"
  ]
}
```

### Common Pitfalls
- Using `==` for demand constraints when `>=` is correct, which may make a feasible problem infeasible.
- Not pre-computing `max_capacity` bounds, leading to variables with incorrect or missing upper bounds.
- Defining variables inside constraint loops, which is inefficient and can cause scoping issues.

## Solving stage

### Strategy Overview
Solve the PuLP model using the CBC solver via PuLP's default command. Implement a systematic solution verification routine and handle solver statuses properly to ensure robust output.

### Step 1 - Invoke Solver with Options
- Call `prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=30))` to solve silently with a time limit.
- Consider setting `gapRel` or `gapAbs` for optimality tolerance if needed.

### Step 2 - Check Solution Status
- Evaluate `pulp.LpStatus[prob.status]`. Accept `['Optimal', 'Feasible']` as successful outcomes.
- For other statuses (`'Infeasible'`, `'Unbounded'`, `'Undefined'`), implement appropriate error handling and reporting.

### Step 3 - Extract and Validate Variable Values
- If status is acceptable, iterate through variables: `pulp.value(var)` to get the solution.
- Store non-zero assignments in a list or dictionary for reporting.
- Recalculate total allocation per resource and per task to verify constraint satisfaction within a tolerance.

### Step 4 - Perform Comprehensive Verification
- Build a separate function that checks all three constraint types against the extracted solution.
- Print warnings for any violations exceeding a small epsilon (e.g., `1e-5`).

### Step 5 - Output Detailed Results
- Print a table of assignments showing resource, task, quantity, and cost contribution.
- Report summary metrics: total cost, supply utilization percentage, demand fulfillment percentage.
- Include the solver status and solution time in the output for reproducibility.

### Code Usage
```python
# build model from formulation
import pulp
prob = pulp.LpProblem("ResourceAssignment", pulp.LpMinimize)
x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", lowBound=0, upBound=max_capacity[i][j])
     for i in resources for j in tasks}
prob += pulp.lpSum(cost[i][j] * x[(i, j)] for (i, j) in x.keys())
for j in tasks:
    prob += pulp.lpSum(x[(i, j)] for i in resources) >= requirement[j]
for i in resources:
    prob += pulp.lpSum(x[(i, j)] for j in tasks) <= availability[i]

# solve with status / termination checks
prob.solve(pulp.PULP_CBC_CMD(msg=False))
status = pulp.LpStatus[prob.status]
if status in ['Optimal', 'Feasible']:
    print(f"Success: {status}")
    print(f"Total Cost: {pulp.value(prob.objective)}")
    # Extract non-zero flows
    for (i, j), var in x.items():
        val = pulp.value(var)
        if val > 1e-6:
            print(f"  Assign {val} from {i} to {j}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not silencing solver output (`msg=False`) in automated scripts, leading to cluttered logs.
- Misinterpreting `'Feasible'` status as optimal; for minimization, the solution may not be globally optimal.
- Forgetting to convert `pulp.value(var)` to a float before numerical comparisons, causing type errors.
