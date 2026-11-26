import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    n = len(cities)
    
    # Build cost dictionary from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}{j}"]
    
    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)
    
    # Binary decision variables x[i,j] = 1 if travel from i to j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")
    
    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0)
    
    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )
    
    # Each city must be departed exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)
    
    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)
    
    # Subtour elimination using Miller-Tucker-Zemlin (MTZ) formulation
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")
    for i in cities:
        u[i].lb = 0
        u[i].ub = n - 1
    
    # Fix starting city position to break symmetry
    model.addConstr(u['E'] == 0)
    
    for i in cities:
        for j in cities:
            if i != j and j != 'E':
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}