import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = 4
    n_destinations = 5
    n_products = 2

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n_origins):
        for j in range(n_destinations):
            for p in range(n_products):
                x[i, j, p] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}_{p}")

    model.update()

    for i in range(n_origins):
        for p in range(n_products):
            model.addConstr(
                gp.quicksum(x[i, j, p] for j in range(n_destinations)) == supply[i][p],
                name=f"supply_{i}_{p}",
            )

    for j in range(n_destinations):
        for p in range(n_products):
            model.addConstr(
                gp.quicksum(x[i, j, p] for i in range(n_origins)) == demand[j][p],
                name=f"demand_{j}_{p}",
            )

    for i in range(n_origins):
        for j in range(n_destinations):
            model.addConstr(
                gp.quicksum(x[i, j, p] for p in range(n_products)) <= capacity[i][j],
                name=f"capacity_{i}_{j}",
            )

    model.setObjective(
        gp.quicksum(
            cost[i][j][p] * x[i, j, p]
            for i in range(n_origins)
            for j in range(n_destinations)
            for p in range(n_products)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}