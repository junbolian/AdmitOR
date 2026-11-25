import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]                   # list of length 4
    holding_cost = params["holding_cost"]       # scalar
    grind_capacity = params["grind_capacity"]   # list of length 6
    grind_hours = params["grind_hours"]         # list of length 4
    drill_capacity = params["drill_capacity"]   # list of length 6 (or scalar)
    drill_hours = params["drill_hours"]         # list of length 4 (or scalar)
    bore_capacity = params["bore_capacity"]     # list of length 6
    bore_hours = params["bore_hours"]           # list of length 4 (or scalar)
    inv_capacity = params["inv_capacity"]       # scalar or list
    sales_limit = params["sales_limit"]         # 4x6 (product x period)
    final_inventory = params["final_inventory"] # list of length 4

    num_products = 4
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(num_products, num_periods, lb=0.0, name="produce")
    sell = model.addVars(num_products, num_periods, lb=0.0, name="sell")
    inv = model.addVars(num_products, num_periods, lb=0.0, name="inv")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inv[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sell[p, t] + inv[p, t],
                    name=f"balance_{p}_{t}"
                )
            else:
                model.addConstr(
                    inv[p, t - 1] + produce[p, t] == sell[p, t] + inv[p, t],
                    name=f"balance_{p}_{t}"
                )

    # Grinding capacity
    for t in periods:
        model.addConstr(
            gp.quicksum(grind_hours[p] * produce[p, t] for p in products) <= grind_capacity[t],
            name=f"grind_{t}"
        )

    # Drilling capacity
    for t in periods:
        dc = drill_capacity[t] if hasattr(drill_capacity, '__len__') else drill_capacity
        model.addConstr(
            gp.quicksum(
                (drill_hours[p] if hasattr(drill_hours, '__len__') else drill_hours) * produce[p, t]
                for p in products
            ) <= dc,
            name=f"drill_{t}"
        )

    # Boring capacity
    for t in periods:
        bc = bore_capacity[t] if hasattr(bore_capacity, '__len__') else bore_capacity
        model.addConstr(
            gp.quicksum(
                (bore_hours[p] if hasattr(bore_hours, '__len__') else bore_hours) * produce[p, t]
                for p in products
            ) <= bc,
            name=f"bore_{t}"
        )

    # Inventory capacity
    for p in products:
        for t in periods:
            ic = inv_capacity[p][t] if (hasattr(inv_capacity, '__len__') and hasattr(inv_capacity[0], '__len__')) \
                 else (inv_capacity[p] if hasattr(inv_capacity, '__len__') else inv_capacity)
            model.addConstr(inv[p, t] <= ic, name=f"inv_cap_{p}_{t}")

    # Sales limits
    for p in products:
        for t in periods:
            model.addConstr(sell[p, t] <= sales_limit[p][t], name=f"sales_lim_{p}_{t}")

    # Final inventory requirement (end of period 5)
    for p in products:
        model.addConstr(inv[p, num_periods - 1] == final_inventory[p], name=f"final_inv_{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}