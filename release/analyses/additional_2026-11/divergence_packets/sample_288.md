# sample_288

Decision: ACCEPT, clique ['A-direct', 'B-structured'], informative [0, 1, 2, 3, 4, 5], label 3.0

## Problem text

Minimize the total number of distribution centers used to allocate six resources, each with specific weights: Resource 1 (37 units), Resource 2 (37 units), Resource 3 (33 units), Resource 4 (40 units), Resource 5 (38 units), and Resource 6 (37 units). Each distribution center has a uniform capacity of 100 units. A distribution center is considered used if at least one resource is assigned to it. Each resource must be assigned to exactly one distribution center, and the total weight of resources assigned to any distribution center must not exceed its capacity. The goal is to minimize the number of distribution centers used while ensuring all resources are allocated without violating capacity constraints.

## Values and statuses per instance

| Candidate | inst 0 | inst 1 | inst 2 | inst 3 | inst 4 | inst 5 |
|---|---|---|---|---|---|---|
| A-direct | 3.0 (optimal) | 2.0 (optimal) | 3.0 (optimal) | 2.0 (optimal) | 5.0 (optimal) | 3.0 (optimal) |
| B-structured | 3.0 (optimal) | 2.0 (optimal) | 3.0 (optimal) | 2.0 (optimal) | 5.0 (optimal) | 3.0 (optimal) |
| C-direct | 3.0 (optimal) | None (crash:File "src/gurobipy) | None (crash:File "src/gurobipy) | None (crash:File "src/gurobipy) | None (crash:File "src/gurobipy) | None (crash:File "src/gurobipy) |

## Sampled parameters per instance

instance 0: `{"resource_weights": [37, 37, 33, 40, 38, 37], "center_capacity": 100}`
instance 1: `{"resource_weights": [40.09527492576502, 26.455238765943204, 28.545580503708557, 33.35705771557174, 43.391543682939485, 40.92272862078863], "center_capacity": 139}`
instance 2: `{"resource_weights": [27.83004208437304, 35.266664397013, 23.689984944873792, 33.24731139528648, 38.122100568756665, 26.489098526981774], "center_capacity": 70}`
instance 3: `{"resource_weights": [40.32743451870542, 37.99770086939141, 27.464724316405793, 42.14237641302181, 45.05501441225445, 26.044272464852952], "center_capacity": 131}`
instance 4: `{"resource_weights": [41.398694568738634, 33.45356146669942, 26.178494096273276, 50.97311373296275, 34.27435562856789, 27.958957723039283], "center_capacity": 60}`
instance 5: `{"resource_weights": [44.71437493291361, 39.30271789634499, 39.08113981083273, 45.513562880651634, 38.82600048516718, 47.50316996034203], "center_capacity": 88}`

## Extracted specification

```json
{
 "resource_weights": {
  "base": [
   37,
   37,
   33,
   40,
   38,
   37
  ],
  "perturb": {
   "mode": "rel",
   "r": 0.3
  }
 },
 "center_capacity": {
  "base": 100,
  "perturb": {
   "mode": "abs",
   "lo": 50.0,
   "hi": 150.0,
   "integer": true
  }
 }
}
```

## Program A-direct

```python
import pyomo.environ as pyo

def solve(params):
    # Extract parameters
    resource_weights = params["resource_weights"]  # list of 6 weights
    center_capacity = params["center_capacity"]    # scalar capacity

    # Problem dimensions
    n_resources = 6
    # We need an upper bound on number of centers. Since each center can hold at most 100 units,
    # and total weight is sum(resource_weights), we can compute a safe upper bound.
    total_weight = sum(resource_weights)
    max_centers = (total_weight + center_capacity - 1) // center_capacity  # ceiling division
    # But to be safe for feasibility, we can set max_centers = n_resources (each resource in its own center)
    max_centers = n_resources

    # Create model
    model = pyo.ConcreteModel()

    # Sets
    model.R = pyo.RangeSet(0, n_resources - 1)          # resources indexed 0..5
    model.C = pyo.RangeSet(0, max_centers - 1)          # potential centers

    # Variables
    # x[r,c] = 1 if resource r assigned to center c
    model.x = pyo.Var(model.R, model.C, domain=pyo.Binary)
    # y[c] = 1 if center c is used
    model.y = pyo.Var(model.C, domain=pyo.Binary)

    # Objective: minimize number of centers used
    model.obj = pyo.Objective(expr=sum(model.y[c] for c in model.C), sense=pyo.minimize)

    # Constraints
    # Each resource assigned to exactly one center
    def assign_rule(model, r):
        return sum(model.x[r, c] for c in model.C) == 1
    model.assign_con = pyo.Constraint(model.R, rule=assign_rule)

    # Capacity constraint per center
    def capacity_rule(model, c):
        return sum(resource_weights[r] * model.x[r, c] for r in model.R) <= center_capacity * model.y[c]
    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    # Linking: if any resource assigned to center c, y[c] must be 1
    # This is already enforced by capacity constraint (if any x[r,c]=1, sum>0 => y[c]>=sum/center_capacity>0 => y[c]=1)
    # But to tighten, we can add: x[r,c] <= y[c] for all r,c
    def link_rule(model, r, c):
        return model.x[r, c] <= model.y[c]
    model.link_con = pyo.Constraint(model.R, model.C, rule=link_rule)

    # Symmetry breaking: centers must be used in order (y[c] >= y[c+1])
    def symmetry_rule(model, c):
        if c < max_centers - 1:
            return model.y[c] >= model.y[c + 1]
        return pyo.Constraint.Skip
    model.symmetry_con = pyo.Constraint(model.C, rule=symmetry_rule)

    # Solve
    try:
        from pyomo.contrib.appsi.solvers.highs import Highs
        solver = Highs()
        result = solver.solve(model)
    except Exception as e:
        # If solver fails during solve call
        return {"objective": None, "status": f"solver error: {str(e)}"}

    # Check if solution is available
    try:
        obj_val = float(pyo.value(model.obj))
        # Verify that all constraints are satisfied (by checking variable values)
        # If objective is retrievable, we assume optimal
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        # Infeasible or other failure
        return {"objective": None, "status": "infeasible or no solution"}
```

## Program B-structured

```python
# IR: {"sets":{"R":"resources 1..6","C":"candidate_centers 1..6"},"params":{"resource_weights":"weight of each resource from params['resource_weights']","center_capacity":"capacity of each center from params['center_capacity']"},"vars":{"assign[R,C]":"Binary, 1 if resource r assigned to center c","use_center[C]":"Binary, 1 if center c is used"},"constraints":["each resource assigned exactly once: sum_c assign[r,c] = 1 for all r","capacity/linking: sum_r resource_weights[r]*assign[r,c] <= center_capacity*use_center[c] for all c"],"objective":"minimize sum_c use_center[c]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    resource_weights = params["resource_weights"]
    center_capacity = params["center_capacity"]

    model = pyo.ConcreteModel()

    model.R = pyo.RangeSet(1, 6)
    model.C = pyo.RangeSet(1, 6)

    def weight_init(model, resource):
        return resource_weights[resource - 1]

    model.resource_weight = pyo.Param(model.R, initialize=weight_init, within=pyo.Reals)
    model.center_capacity = pyo.Param(initialize=center_capacity, within=pyo.Reals)

    model.assign = pyo.Var(model.R, model.C, domain=pyo.Binary)
    model.use_center = pyo.Var(model.C, domain=pyo.Binary)

    def assign_once_rule(model, resource):
        return sum(model.assign[resource, center] for center in model.C) == 1

    model.assign_once = pyo.Constraint(model.R, rule=assign_once_rule)

    def capacity_rule(model, center):
        return (
            sum(model.resource_weight[resource] * model.assign[resource, center] for resource in model.R)
            <= model.center_capacity * model.use_center[center]
        )

    model.capacity_limit = pyo.Constraint(model.C, rule=capacity_rule)

    model.objective_component = pyo.Objective(
        expr=sum(model.use_center[center] for center in model.C),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.objective_component))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Program C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    resource_weights = params["resource_weights"]
    center_capacity = params["center_capacity"]
    
    # Number of resources
    num_resources = len(resource_weights)
    
    # Upper bound on number of centers needed
    total_weight = sum(resource_weights)
    max_centers = (total_weight + center_capacity - 1) // center_capacity
    
    # Create model
    model = gp.Model("distribution_center_allocation")
    model.Params.OutputFlag = 0
    
    # Decision variables
    # x[i, j] = 1 if resource i is assigned to center j
    x = model.addVars(num_resources, max_centers, vtype=GRB.BINARY, name="x")
    
    # y[j] = 1 if center j is used
    y = model.addVars(max_centers, vtype=GRB.BINARY, name="y")
    
    # Objective: minimize number of centers used
    model.setObjective(gp.quicksum(y[j] for j in range(max_centers)), GRB.MINIMIZE)
    
    # Constraint: each resource assigned to exactly one center
    for i in range(num_resources):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(max_centers)) == 1,
            name=f"assign_resource_{i}"
        )
    
    # Constraint: capacity limit for each center
    for j in range(max_centers):
        model.addConstr(
            gp.quicksum(resource_weights[i] * x[i, j] for i in range(num_resources)) <= center_capacity * y[j],
            name=f"capacity_{j}"
        )
    
    # Solve
    model.optimize()
    
    # Return results
    if model.status == GRB.OPTIMAL:
        return {
            "objective": model.objVal,
            "status": "optimal"
        }
    elif model.status == GRB.INFEASIBLE:
        return {
            "objective": None,
            "status": "infeasible"
        }
    elif model.status == GRB.INF_OR_UNBD:
        return {
            "objective": None,
            "status": "infeasible_or_unbounded"
        }
    elif model.status == GRB.UNBOUNDED:
        return {
            "objective": None,
            "status": "unbounded"
        }
    else:
        return {
            "objective": None,
            "status": "not_solved"
        }
```
