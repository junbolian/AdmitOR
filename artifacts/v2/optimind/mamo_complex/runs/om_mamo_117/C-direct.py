import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_cost = params["opening_cost"]  # list of 8
    transport_cost = params["transport_cost"]  # 8x9 matrix
    demand = params["demand"]  # list of 9
    capacity = params["capacity"]  # list of 8

    n_centers = len(opening_cost)
    n_stores = len(demand)

    centers = range(n_centers)
    stores = range(n_stores)

    model = gp.Model("supply_chain")
    model.Params.OutputFlag = 0

    y = model.addVars(centers, vtype=GRB.BINARY, name="y")
    x = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0, name="x")

    # Meet each store's demand
    model.addConstrs(
        (gp.quicksum(x[c, s] for c in centers) == demand[s] for s in stores),
        name="demand",
    )

    # Capacity limits, active only if center is open
    model.addConstrs(
        (gp.quicksum(x[c, s] for s in stores) <= capacity[c] * y[c] for c in centers),
        name="capacity",
    )

    # Shipments only from open centers
    model.addConstrs(
        (x[c, s] <= demand[s] * y[c] for c in centers for s in stores),
        name="link",
    )

    model.setObjective(
        gp.quicksum(opening_cost[c] * y[c] for c in centers)
        + gp.quicksum(
            transport_cost[c][s] * x[c, s] for c in centers for s in stores
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    return {"objective": None, "status": "no_optimal_solution"}