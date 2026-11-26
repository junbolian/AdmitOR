import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['A', 'B', 'C', 'D']
    n = len(cities)
    
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]
    
    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)
    
    # Binary decision variables: x[i,j] = 1 if travel from i to j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
    
    # MTZ subtour elimination variables
    u = {}
    for i in cities:
        u[i] = model.addVar(lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")
    
    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )
    
    # Each city is departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )
    
    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )
    
    # MTZ subtour elimination constraints
    # Fix one city as the starting point (city 'A') with u['A'] = 0
    model.addConstr(u['A'] == 0, name="u_start")
    
    non_start = [c for c in cities if c != 'A']
    for i in non_start:
        model.addConstr(u[i] >= 1, name=f"u_lb_{i}")
        model.addConstr(u[i] <= n - 1, name=f"u_ub_{i}")
    
    for i in cities:
        for j in non_start:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n * x[(i, j)] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}