import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_cost = params["opening_cost"]      # list of 9 floats
    transport_cost = params["transport_cost"]  # 9x9 matrix, rows=centers, cols=stores
    demand = params["demand"]                  # list of 9 floats
    capacity = params["capacity"]              # list of 9 floats

    n_centers = len(opening_cost)
    n_stores = len(demand)

    model = gp.Model("distribumax")
    model.Params.OutputFlag = 0

    open_c = model.addVars(n_centers, vtype=GRB.BINARY, name="open")
    ship = model.addVars(n_centers, n_stores, vtype=GRB.CONTINUOUS, lb=0, name="ship")

    # Meet every store's demand
    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_centers)) == demand[j],
            name=f"demand_{j}",
        )

    # Center capacity, only if open
    for i in range(n_centers):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_stores)) <= capacity[i] * open_c[i],
            name=f"capacity_{i}",
        )

    model.setObjective(
        gp.quicksum(opening_cost[i] * open_c[i] for i in range(n_centers))
        + gp.quicksum(
            transport_cost[i][j] * ship[i, j]
            for i in range(n_centers)
            for j in range(n_stores)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed (status {model.Status})"}