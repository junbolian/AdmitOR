import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]
    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]
    max_inv = params["max_inventory_per_product"]
    sales_limits = {
        0: params["sales_limits_product0"],
        1: params["sales_limits_product1"],
        2: params["sales_limits_product2"],
    }
    target_inv = params["target_inventory_end_period4"]

    products = [0, 1, 2]
    periods = [0, 1, 2, 3, 4]

    model = gp.Model("factory_production")
    model.Params.OutputFlag = 0

    prod = model.addVars(products, periods, lb=0.0, name="prod")
    inv = model.addVars(products, periods, lb=0.0, name="inv")
    sales = model.addVars(products, periods, lb=0.0, name="sales")

    # Period 0 balance: production equals sales plus ending inventory
    for p in products:
        model.addConstr(prod[p, 0] == sales[p, 0] + inv[p, 0], name=f"balance_init_{p}")

    # Periods 1-4 balance: prior inventory plus production equals sales plus new inventory
    for p in products:
        for t in range(1, 5):
            model.addConstr(
                inv[p, t - 1] + prod[p, t] == sales[p, t] + inv[p, t],
                name=f"balance_{p}_{t}",
            )

    # Machine capacity constraints per period
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours[p] * prod[p, t] for p in products) <= grinder_cap[t],
            name=f"grinder_cap_{t}",
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * prod[p, t] for p in products) <= drill_cap[t],
            name=f"drill_cap_{t}",
        )
        model.addConstr(
            gp.quicksum(borer_hours[p] * prod[p, t] for p in products) <= borer_cap[t],
            name=f"borer_cap_{t}",
        )

    # Inventory capacity limits — max_inv is a single scalar applying to all products
    for p in products:
        for t in periods:
            if hasattr(max_inv, "__getitem__"):
                cap = max_inv[p]
            else:
                cap = max_inv
            model.addConstr(inv[p, t] <= cap, name=f"inv_cap_{p}_{t}")

    # Sales upper bounds
    for p in products:
        for t in periods:
            model.addConstr(sales[p, t] <= sales_limits[p][t], name=f"sales_lim_{p}_{t}")

    # Target ending inventory at end of Period 4
    for p in products:
        if hasattr(target_inv, "__getitem__"):
            tgt = target_inv[p]
        else:
            tgt = target_inv
        model.addConstr(inv[p, 4] == tgt, name=f"target_inv_{p}")

    # Objective: maximize revenue from sales minus holding cost
    revenue = gp.quicksum(profit_per_unit[p] * sales[p, t] for p in products for t in periods)
    holding_total = holding_cost * gp.quicksum(inv[p, t] for p in products for t in periods)
    model.setObjective(revenue - holding_total, GRB.MAXIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    reason_map = {
        GRB.INFEASIBLE: "infeasible",
        GRB.INF_OR_UNBD: "infeasible_or_unbounded",
        GRB.UNBOUNDED: "unbounded",
    }
    reason = reason_map.get(model.status, f"status_{model.status}")
    return {"objective": None, "status": reason}