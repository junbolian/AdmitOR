import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = 6
    n_stores = 5

    model = gp.Model("distribution_network")

    open_dc = model.addVars(n_centers, vtype=GRB.BINARY, name="open_dc")
    ship = model.addVars(n_centers, n_stores, vtype=GRB.CONTINUOUS, lb=0, name="ship")

    model.setObjective(
        gp.quicksum(opening_cost[i] * open_dc[i] for i in range(n_centers))
        + gp.quicksum(
            transport_cost[i][j] * ship[i, j]
            for i in range(n_centers)
            for j in range(n_stores)
        ),
        GRB.MINIMIZE,
    )

    model.addConstrs(
        (
            gp.quicksum(ship[i, j] for i in range(n_centers)) >= demand[j]
            for j in range(n_stores)
        ),
        name="demand",
    )

    model.addConstrs(
        (
            gp.quicksum(ship[i, j] for j in range(n_stores)) <= capacity[i] * open_dc[i]
            for i in range(n_centers)
        ),
        name="capacity",
    )

    model.Params.OutputFlag = 0
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}