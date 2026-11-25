import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinding_capacity = params["grinding_capacity"]
    grinding_hours_per_unit = params["grinding_hours_per_unit"]
    drilling_capacity = params["drilling_capacity"]
    drilling_hours_per_unit = params["drilling_hours_per_unit"]
    boring_capacity = params["boring_capacity"]
    boring_hours_per_unit = params["boring_hours_per_unit"]
    max_inventory = params["max_inventory"]
    sales_limit = params["sales_limit"]
    final_inventory = params["final_inventory"]

    P = 4
    T = 6

    model = gp.Model("factory")

    x = model.addVars(P, T, vtype=GRB.CONTINUOUS, lb=0, name="prod")
    s = model.addVars(P, T, vtype=GRB.CONTINUOUS, lb=0, name="sales")
    inv = model.addVars(P, T, vtype=GRB.CONTINUOUS, lb=0, name="inv")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * s[p, t] for p in range(P) for t in range(T))
        - holding_cost * gp.quicksum(inv[p, t] for p in range(P) for t in range(T)),
        GRB.MAXIMIZE,
    )

    for p in range(P):
        model.addConstr(x[p, 0] == s[p, 0] + inv[p, 0])
        for t in range(1, T):
            model.addConstr(inv[p, t - 1] + x[p, t] == s[p, t] + inv[p, t])

    for t in range(T):
        model.addConstr(
            gp.quicksum(grinding_hours_per_unit[p] * x[p, t] for p in range(P))
            <= grinding_capacity[t]
        )
        model.addConstr(
            gp.quicksum(drilling_hours_per_unit[p] * x[p, t] for p in range(P))
            <= drilling_capacity[t]
        )
        model.addConstr(
            gp.quicksum(boring_hours_per_unit[p] * x[p, t] for p in range(P))
            <= boring_capacity[t]
        )

    for p in range(P):
        for t in range(T):
            model.addConstr(inv[p, t] <= max_inventory)

    for p in range(P):
        for t in range(T):
            model.addConstr(s[p, t] <= sales_limit[p][t])

    for p in range(P):
        model.addConstr(inv[p, T - 1] == final_inventory[p])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "not_optimal"}