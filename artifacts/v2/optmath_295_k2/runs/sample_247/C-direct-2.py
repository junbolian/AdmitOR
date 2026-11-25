import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    holding_cost = params["holding_cost"]
    grind_capacity = params["grind_capacity"]
    grind_hours = params["grind_hours"]
    drill_capacity = params["drill_capacity"]
    drill_hours = params["drill_hours"]
    bore_capacity = params["bore_capacity"]
    bore_hours = params["bore_hours"]
    inv_capacity = params["inv_capacity"]
    sales_limit = params["sales_limit"]
    final_inventory = params["final_inventory"]

    num_products = 4
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    prod = model.addVars(products, periods, lb=0.0, name="prod")
    inv = model.addVars(products, periods, lb=0.0, name="inv")
    sales = model.addVars(products, periods, lb=0.0, name="sales")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inv[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(prod[p, t] == sales[p, t] + inv[p, t], name=f"balance_{p}_{t}")
            else:
                model.addConstr(inv[p, t-1] + prod[p, t] == sales[p, t] + inv[p, t], name=f"balance_{p}_{t}")

    # Grinding capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grind_hours[p] * prod[p, t] for p in products) <= grind_capacity[t],
            name=f"grind_{t}"
        )

    # Drilling capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(drill_hours[p] * prod[p, t] for p in products) <= drill_capacity[t],
            name=f"drill_{t}"
        )

    # Boring capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(bore_hours[p] * prod[p, t] for p in products) <= bore_capacity[t],
            name=f"bore_{t}"
        )

    # Inventory capacity constraints
    for p in products:
        for t in periods:
            model.addConstr(inv[p, t] <= inv_capacity, name=f"inv_cap_{p}_{t}")

    # Sales limit constraints
    for p in products:
        for t in periods:
            model.addConstr(sales[p, t] <= sales_limit[p][t], name=f"sales_lim_{p}_{t}")

    # Final inventory requirements
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