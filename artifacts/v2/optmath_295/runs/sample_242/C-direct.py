import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]                      # 3 x 8
    prod_cost = params["prod_cost"]                # 3 x 8
    setup_cost = params["setup_cost"]              # 3 x 8
    hold_cost = params["hold_cost"]                # scalar
    res_usage = params["res_usage"]                # length 3
    res_capacity = params["res_capacity"]          # length 8
    prod_max = params["prod_max"]                  # 3 x 8
    initial_inventory = params["initial_inventory"]  # length 3

    P = 3  # products
    W = 8  # weeks

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    x = model.addVars(P, W, lb=0.0, name="x")          # production quantity
    inv = model.addVars(P, W, lb=0.0, name="inv")       # ending inventory
    y = model.addVars(P, W, vtype=GRB.BINARY, name="y") # setup binary

    # Objective
    obj = gp.quicksum(
        prod_cost[p][w] * x[p, w]
        + setup_cost[p][w] * y[p, w]
        + hold_cost * inv[p, w]
        for p in range(P) for w in range(W)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    for p in range(P):
        for w in range(W):
            start_inv = initial_inventory[p] if w == 0 else inv[p, w - 1]
            model.addConstr(
                start_inv + x[p, w] - inv[p, w] == demand[p][w],
                name=f"balance_p{p}_w{w}"
            )

    # Resource capacity constraints
    for w in range(W):
        model.addConstr(
            gp.quicksum(res_usage[p] * x[p, w] for p in range(P)) <= res_capacity[w],
            name=f"resource_w{w}"
        )

    # Production limit: x[p,w] <= prod_max[p][w] * y[p,w]
    for p in range(P):
        for w in range(W):
            model.addConstr(
                x[p, w] <= prod_max[p][w] * y[p, w],
                name=f"setup_link_p{p}_w{w}"
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