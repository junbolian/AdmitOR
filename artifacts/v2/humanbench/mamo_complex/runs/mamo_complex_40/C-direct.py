import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_centers = int(params["num_centers"])
    num_stores = int(params["num_stores"])
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    centers = range(num_centers)
    stores = range(num_stores)

    total_demand = sum(demand[s] for s in stores)
    if total_demand > sum(capacity[c] for c in centers):
        return {"objective": None, "status": "infeasible"}

    model = gp.Model("distribution")
    model.Params.OutputFlag = 0

    open_center = model.addVars(centers, vtype=GRB.BINARY, name="open_center")
    ship = model.addVars(centers, stores, lb=0, vtype=GRB.CONTINUOUS, name="ship")

    model.setObjective(
        gp.quicksum(opening_cost[c] * open_center[c] for c in centers)
        + gp.quicksum(
            transport_cost[c][s] * ship[c, s] for c in centers for s in stores
        ),
        GRB.MINIMIZE,
    )

    for s in stores:
        model.addConstr(
            gp.quicksum(ship[c, s] for c in centers) == demand[s],
            name=f"demand_{s}",
        )

    for c in centers:
        model.addConstr(
            gp.quicksum(ship[c, s] for s in stores) <= capacity[c] * open_center[c],
            name=f"capacity_{c}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.Status}"}