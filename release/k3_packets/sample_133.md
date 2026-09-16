# sample_133

certified: 40.0
vault label: 41.0
relative gap: 0.024390243902439025
clique: ['A-direct', 'B-structured', 'C-direct']  informative: 6

## Classification (fill in)
[ ] (a) gate model defect: text states a constraint the
        clique's model drops or misreads
[ ] (b) label error: text has one reasonable reading and the
        clique's value is correct under it
[ ] (c) ambiguity: text supports multiple readings; clique's
        reading is legitimate but differs from the labeler's
notes:

## Problem text

Select exactly 2 facilities from 5 potential locations (Node 0, Node 1, Node 2, Node 3, and Node 4) to maximize the minimum distance between any two selected facilities. The selection of facilities is represented by binary variables, where each node is either selected (1) or not selected (0). For every pair of nodes, a binary pairwise selection variable indicates whether both nodes in the pair are selected. The minimum distance between any two selected facilities is constrained by the distances provided, which are incorporated into the constraints using a large constant (1e+06) multiplied by the pairwise selection variables. Specifically, for each pair of nodes, the minimum distance plus 1e+06 times the pairwise selection variable must be less than or equal to a value slightly larger than 1e+06, scaled by the distance between the nodes. Additionally, the pairwise selection variables are constrained by the facility selection variables: if a node is not selected, the pairwise selection variables involving that node must be 0, and if both nodes in a pair are selected, the pairwise selection variable for that pair must be 1. All facility selection and pairwise selection variables are binary, ensuring that the solution is a valid selection of facilities and pairs. The objective is to maximize the minimum distance between any two selected facilities while adhering to these constraints.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    distances = params["distances"]
    M = params["M"]
    k = params["k"]
    n = params["n"]
    
    # Validate dimensions
    if len(distances) != n or any(len(row) != n for row in distances):
        return {"objective": None, "status": "invalid distances matrix dimensions"}
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Sets
    model.N = pyo.RangeSet(0, n-1)
    model.P = pyo.Set(initialize=[(i, j) for i in model.N for j in model.N if i < j])
    
    # Variables
    model.x = pyo.Var(model.N, domain=pyo.Binary)  # facility selection
    model.y = pyo.Var(model.P, domain=pyo.Binary)  # pairwise selection
    
    # Objective: maximize minimum distance (represented by variable z)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)
    model.obj = pyo.Objective(expr=model.z, sense=pyo.maximize)
    
    # Constraint: select exactly k facilities
    model.select_k = pyo.Constraint(expr=sum(model.x[i] for i in model.N) == k)
    
    # Constraints linking y to x
    def link_y_rule(model, i, j):
        if i < j:
            return model.y[i, j] <= model.x[i]
        else:
            return pyo.Constraint.Skip
    model.link_y1 = pyo.Constraint(model.N, model.N, rule=link_y_rule)
    
    def link_y2_rule(model, i, j):
        if i < j:
            return model.y[i, j] <= model.x[j]
        else:
            return pyo.Constraint.Skip
    model.link_y2 = pyo.Constraint(model.N, model.N, rule=link_y2_rule)
    
    def link_y3_rule(model, i, j):
        if i < j:
            return model.y[i, j] >= model.x[i] + model.x[j] - 1
        else:
            return pyo.Constraint.Skip
    model.link_y3 = pyo.Constraint(model.N, model.N, rule=link_y3_rule)
    
    # Minimum distance constraints using big-M
    def min_dist_rule(model, i, j):
        if i < j:
            return model.z + M * model.y[i, j] <= M + distances[i][j]
        else:
            return pyo.Constraint.Skip
    model.min_dist = pyo.Constraint(model.N, model.N, rule=min_dist_rule)
    
    # Solve
    try:
        solver = Highs()
        results = solver.solve(model)
        
        # Check if solution exists and objective is retrievable
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except (ValueError, TypeError) as e:
        # This catches cases where pyo.value fails (infeasible/unbounded)
        return {"objective": None, "status": "infeasible or unbounded"}
```

## Clique member B-structured

```python
# {"sets":{"N":"nodes"},"params":["distances","M","k","n"],"vars":{"x":{"type":"Binary","index":"N"},"y":{"type":"Binary","index":"N×N"},"dmin":{"type":"NonNegativeReals"}},"constraints":["sum(x[i] for i in N) == k","y[i,j] <= x[i]","y[i,j] <= x[j]","y[i,j] >= x[i] + x[j] - 1","dmin + M*y[i,j] <= distances[i][j] + M for all i<j"],"objective":"maximize dmin"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distances = params["distances"]
    M = params["M"]
    k = params["k"]
    n = params["n"]

    model = pyo.ConcreteModel()
    model.N = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.N, model.N, domain=pyo.Binary)
    model.dmin = pyo.Var(domain=pyo.NonNegativeReals)

    def select_count_rule(model):
        return sum(model.x[i] for i in model.N) == k

    model.select_count = pyo.Constraint(rule=select_count_rule)

    def pair_upper_i_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return model.y[i, j] <= model.x[i]

    def pair_upper_j_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return model.y[i, j] <= model.x[j]

    def pair_lower_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return model.y[i, j] >= model.x[i] + model.x[j] - 1

    model.pair_upper_i = pyo.Constraint(model.N, model.N, rule=pair_upper_i_rule)
    model.pair_upper_j = pyo.Constraint(model.N, model.N, rule=pair_upper_j_rule)
    model.pair_lower = pyo.Constraint(model.N, model.N, rule=pair_lower_rule)

    def min_distance_rule(model, i, j):
        if i >= j:
            return pyo.Constraint.Skip
        return model.dmin + M * model.y[i, j] <= distances[i][j] + M

    model.min_distance = pyo.Constraint(model.N, model.N, rule=min_distance_rule)

    model.objective = pyo.Objective(expr=model.dmin, sense=pyo.maximize)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.objective))
    except Exception:
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distances = params["distances"]
    M = params["M"]
    k = params["k"]
    n = params["n"]
    
    model = gp.Model("facility_selection")
    model.Params.OutputFlag = 0
    
    # Decision variables
    # x[i] = 1 if facility i is selected
    x = model.addVars(n, vtype=GRB.BINARY, name="x")
    
    # y[i,j] = 1 if both facilities i and j are selected
    y = model.addVars(n, n, vtype=GRB.BINARY, name="y")
    
    # min_dist = minimum distance between any two selected facilities
    min_dist = model.addVar(vtype=GRB.CONTINUOUS, name="min_dist", lb=0)
    
    # Constraint: Select exactly k facilities
    model.addConstr(gp.quicksum(x[i] for i in range(n)) == k, name="select_k")
    
    # Constraints: Link y[i,j] to x[i] and x[j]
    for i in range(n):
        for j in range(i+1, n):
            # If both x[i] and x[j] are 1, then y[i,j] must be 1
            model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"link_y_{i}_{j}_lower")
            
            # If either x[i] or x[j] is 0, then y[i,j] must be 0
            model.addConstr(y[i, j] <= x[i], name=f"link_y_{i}_{j}_upper_i")
            model.addConstr(y[i, j] <= x[j], name=f"link_y_{i}_{j}_upper_j")
    
    # Constraints: min_dist must be <= distance between any two selected facilities
    for i in range(n):
        for j in range(i+1, n):
            # If both facilities i and j are selected (y[i,j] = 1), then min_dist <= distances[i][j]
            # min_dist <= distances[i][j] + M * (1 - y[i,j])
            model.addConstr(min_dist <= distances[i][j] + M * (1 - y[i, j]), 
                          name=f"min_dist_{i}_{j}")
    
    # Objective: Maximize the minimum distance
    model.setObjective(min_dist, GRB.MAXIMIZE)
    
    model.optimize()
    
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
    elif model.status == GRB.UNBOUNDED:
        return {
            "objective": None,
            "status": "unbounded"
        }
    else:
        return {
            "objective": None,
            "status": f"status_{model.status}"
        }
```
