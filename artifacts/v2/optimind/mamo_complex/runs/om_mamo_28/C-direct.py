import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 4
    cities = list(range(1, n + 1))
    
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]
    
    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)
    
    # Binary decision variables x[i,j] = 1 if travel from i to j
    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )
    
    # Subtour elimination auxiliary variables (MTZ formulation)
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")
    
    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )
    
    # Each city must be departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )
    
    # Each city must be arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )
    
    # MTZ subtour elimination constraints
    # Fix starting city u[1] = 1
    model.addConstr(u[1] == 1, name="u_start")
    
    for i in cities:
        model.addConstr(u[i] >= 1, name=f"u_lb_{i}")
        model.addConstr(u[i] <= n, name=f"u_ub_{i}")
    
    for i in cities:
        for j in cities:
            if i != j and j != 1:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
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