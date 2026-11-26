import gurobipy as gp
from gurobipy import GRB

def solve(params):
    buy_price = params["buy_price"]        # list of 6 values (July–December)
    sell_price = params["sell_price"]      # list of 6 values (July–December)
    warehouse_capacity = params["warehouse_capacity"]
    initial_stock = params["initial_stock"]

    months = range(6)  # 0=July, 1=Aug, ..., 5=Dec

    model = gp.Model("purchase_sales_plan")
    model.setParam("OutputFlag", 0)

    # Decision variables
    buy = model.addVars(months, lb=0.0, name="buy")
    sell = model.addVars(months, lb=0.0, name="sell")
    inventory = model.addVars(months, lb=0.0, name="inventory")

    # Inventory balance: inventory[t] = prev_inv + buy[t] - sell[t]
    for t in months:
        prev_inv = initial_stock if t == 0 else inventory[t - 1]
        model.addConstr(
            inventory[t] == prev_inv + buy[t] - sell[t],
            name=f"balance_{t}"
        )

    # Warehouse capacity on ending inventory
    for t in months:
        model.addConstr(inventory[t] <= warehouse_capacity, name=f"cap_end_{t}")

    # Warehouse capacity immediately after purchasing (before selling)
    # prev_inv + buy[t] <= warehouse_capacity
    for t in months:
        prev_inv = initial_stock if t == 0 else inventory[t - 1]
        model.addConstr(
            prev_inv + buy[t] <= warehouse_capacity,
            name=f"cap_buy_{t}"
        )

    # Cannot sell more than is available after purchasing
    # sell[t] <= prev_inv + buy[t]  (redundant with inv[t]>=0 but explicit)
    for t in months:
        prev_inv = initial_stock if t == 0 else inventory[t - 1]
        model.addConstr(
            sell[t] <= prev_inv + buy[t],
            name=f"sell_limit_{t}"
        )

    # Objective: maximize total profit = revenue - cost
    model.setObjective(
        gp.quicksum(sell_price[t] * sell[t] - buy_price[t] * buy[t] for t in months),
        GRB.MAXIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    elif model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "inf_or_unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}