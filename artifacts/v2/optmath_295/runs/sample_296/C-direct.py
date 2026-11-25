import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preferences = params["preferences"]

    n_participants = 6
    n_cars = 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n_participants):
        for j in range(n_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(x[i, j] for i in range(n_participants) for j in range(n_cars)),
        GRB.MAXIMIZE
    )

    for i in range(n_participants):
        for j in range(n_cars):
            model.addConstr(x[i, j] <= preferences[i][j])

    for i in range(n_participants):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_cars)) <= 1)

    for j in range(n_cars):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n_participants)) <= 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}