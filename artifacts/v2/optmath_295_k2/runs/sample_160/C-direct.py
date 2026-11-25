import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_cost = params["fixed_cost"]
    shipping_cost = params["shipping_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = len(fixed_cost)       # 7 distribution centers
    n_stores = len(demand)       # 8 retail stores

    model = gp.Model("distribution_network")
    model.Params.OutputFlag = 0

    # y[i] = 1 if DC i is opened
    y = model.addVars(n_dc, vtype=GRB.BINARY, name="y")
    # x[i, j] = units shipped from DC i to store j
    x = model.addVars(n_dc, n_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: fixed opening costs + variable shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in range(n_dc))
        + gp.quicksum(
            shipping_cost[i][j] * x[i, j]
            for i in range(n_dc)
            for j in range(n_stores)
        ),
        GRB.MINIMIZE,
    )

    # Each store must receive exactly its demand
    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_dc)) == demand[j],
            name=f"demand_{j}",
        )

    # Each DC can ship only if opened, and only up to its capacity
    for i in range(n_dc):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_stores)) <= capacity[i] * y[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}