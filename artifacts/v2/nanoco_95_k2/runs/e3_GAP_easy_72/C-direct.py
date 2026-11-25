import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = {
        0: params["capacity_DC1"],
        1: params["capacity_DC2"],
        2: params["capacity_DC3"],
    }

    storage = {
        0: params["storage_DC1"],
        1: params["storage_DC2"],
        2: params["storage_DC3"],
    }

    cost = {
        0: params["cost_DC1"],
        1: params["cost_DC2"],
        2: params["cost_DC3"],
    }

    num_orders = 7
    num_dcs = 3
    orders = range(num_orders)
    dcs = range(num_dcs)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_orders, num_dcs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[dc][order] * x[order, dc] for order in orders for dc in dcs),
        GRB.MINIMIZE,
    )

    # Each order assigned to exactly one DC
    for order in orders:
        model.addConstr(gp.quicksum(x[order, dc] for dc in dcs) == 1, name=f"assign_{order}")

    # Capacity constraints
    for dc in dcs:
        model.addConstr(
            gp.quicksum(storage[dc][order] * x[order, dc] for order in orders) <= capacity[dc],
            name=f"capacity_{dc}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}