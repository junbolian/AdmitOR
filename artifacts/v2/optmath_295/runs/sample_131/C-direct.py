import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = [float(x) for x in params["profit_per_unit"]]
    holding_cost = float(params["holding_cost"])
    grinder_capacity = float(params["grinder_capacity"])
    drill_capacity = float(params["drill_capacity"])
    borer_capacity = float(params["borer_capacity"])
    max_inventory = float(params["max_inventory"])
    max_sales_p0 = [float(x) for x in params["max_sales_p0"]]
    max_sales_p1 = [float(x) for x in params["max_sales_p1"]]
    max_sales_p2 = [float(x) for x in params["max_sales_p2"]]
    final_inventory_target = [float(x) for x in params["final_inventory_target"]]
    grinder_time_p0 = float(params["grinder_time_p0"])
    drill_time_p0 = float(params["drill_time_p0"])
    borer_time_p0 = float(params["borer_time_p0"])
    grinder_time_p1 = float(params["grinder_time_p1"])
    drill_time_p1 = float(params["drill_time_p1"])
    borer_time_p1 = float(params["borer_time_p1"])
    grinder_time_p2 = float(params["grinder_time_p2"])
    drill_time_p2 = float(params["drill_time_p2"])
    borer_time_p2 = float(params["borer_time_p2"])

    products = [0, 1, 2]
    periods = [0, 1, 2, 3]

    max_sales = {
        0: max_sales_p0,
        1: max_sales_p1,
        2: max_sales_p2,
    }

    grinder_time = [grinder_time_p0, grinder_time_p1, grinder_time_p2]
    drill_time   = [drill_time_p0,   drill_time_p1,   drill_time_p2]
    borer_time   = [borer_time_p0,   borer_time_p1,   borer_time_p2]

    borer_cap = {t: (0.0 if t == 2 else borer_capacity) for t in periods}

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    produce = model.addVars(products, periods, lb=0.0, name="produce")
    sell    = model.addVars(products, periods, lb=0.0, name="sell")
    inv     = model.addVars(products, periods, lb=0.0, name="inv")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inv[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(produce[p, t] == sell[p, t] + inv[p, t],
                                name=f"balance_p{p}_t{t}")
            else:
                model.addConstr(inv[p, t-1] + produce[p, t] == sell[p, t] + inv[p, t],
                                name=f"balance_p{p}_t{t}")

    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_time[p] * produce[p, t] for p in products) <= grinder_capacity,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(drill_time[p] * produce[p, t] for p in products) <= drill_capacity,
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(borer_time[p] * produce[p, t] for p in products) <= borer_cap[t],
            name=f"borer_t{t}"
        )

    for p in products:
        for t in periods:
            model.addConstr(inv[p, t] <= max_inventory, name=f"inv_cap_p{p}_t{t}")

    for t in periods:
        model.addConstr(sell[0, t] <= max_sales[0][t], name=f"sales_p0_t{t}")
        model.addConstr(sell[1, t] <= max_sales[1][t], name=f"sales_p1_t{t}")
        model.addConstr(sell[2, t] <= max_sales[2][t], name=f"sales_p2_t{t}")

    for p in products:
        model.addConstr(inv[p, 3] == final_inventory_target[p], name=f"final_inv_p{p}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}