import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_ordering_cost = params["fixed_ordering_cost"]
    unit_purchase_cost = params["unit_purchase_cost"]
    holding_cost = params["holding_cost"]
    demand = params["demand"]
    order_limit = params["order_limit"]

    T = 25
    weeks = range(T)

    model = gp.Model("inventory_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables
    y = model.addVars(T, vtype=GRB.BINARY, name="order_placed")
    q = model.addVars(T, lb=0.0, name="order_quantity")
    inv = model.addVars(T + 1, lb=0.0, name="inventory")

    # Starting and ending inventory = 0
    model.addConstr(inv[0] == 0, name="start_inventory")
    model.addConstr(inv[T] == 0, name="end_inventory")

    # Demand fulfillment and inventory flow
    for t in weeks:
        model.addConstr(
            inv[t] + q[t] == demand[t] + inv[t + 1],
            name=f"balance_{t}"
        )

    # Order limits: if order placed, quantity <= order_limit; else quantity = 0
    for t in weeks:
        model.addConstr(q[t] <= order_limit * y[t], name=f"order_limit_{t}")

    # Objective
    obj = gp.quicksum(
        fixed_ordering_cost[t] * y[t]
        + unit_purchase_cost[t] * q[t]
        + holding_cost[t] * inv[t + 1]
        for t in weeks
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}