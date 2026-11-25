import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    n_products = 3
    n_periods = 4
    machine_caps = [grinder_capacity, drill_capacity, borer_capacity]

    if isinstance(inventory_capacity, (int, float)):
        inv_cap = [inventory_capacity] * n_products
    else:
        inv_cap = list(inventory_capacity)

    model = gp.Model("production_planning")
    model.Params.OutputFlag = 0

    prod = {}
    inv = {}
    sales = {}
    for t in range(n_periods):
        for p in range(n_products):
            prod[t, p] = model.addVar(lb=0, name=f"prod_{t}_{p}")
            inv[t, p] = model.addVar(lb=0, name=f"inv_{t}_{p}")
            sales[t, p] = model.addVar(lb=0, name=f"sales_{t}_{p}")
    model.update()

    obj = gp.LinExpr()
    for t in range(n_periods):
        for p in range(n_products):
            obj += profit_per_unit[p] * sales[t, p]
            obj -= holding_cost * inv[t, p]
    model.setObjective(obj, GRB.MAXIMIZE)

    for p in range(n_products):
        model.addConstr(prod[0, p] == sales[0, p] + inv[0, p])
        for t in range(1, n_periods):
            model.addConstr(prod[t, p] + inv[t - 1, p] == sales[t, p] + inv[t, p])

    for t in range(n_periods):
        for m_idx in range(3):
            cap = machine_caps[m_idx][t]
            expr = gp.LinExpr()
            for p in range(n_products):
                expr += machine_hours_per_unit[p][m_idx] * prod[t, p]
            model.addConstr(expr <= cap)

    for t in range(n_periods):
        for p in range(n_products):
            model.addConstr(inv[t, p] <= inv_cap[p])

    for t in range(n_periods):
        for p in range(n_products):
            model.addConstr(sales[t, p] <= sales_limit[t][p])

    for p in range(n_products):
        model.addConstr(inv[n_periods - 1, p] == target_inventory[p])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}