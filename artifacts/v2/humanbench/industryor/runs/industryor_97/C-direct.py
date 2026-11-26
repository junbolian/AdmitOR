import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_inventory = params["initial_inventory"]
    warehouse_capacity = params["warehouse_capacity"]
    purchase_price = params["purchase_price"]   # list of 3 values
    selling_price = params["selling_price"]     # list of 3 values

    months = range(3)

    model = gp.Model("procurement_sales")
    model.setParam("OutputFlag", 0)
    model.setParam("DualReductions", 0)

    buy = model.addVars(months, lb=0.0, name="buy")
    sell = model.addVars(months, lb=0.0, name="sell")
    inv = model.addVars(months, lb=0.0, name="inv")

    model.setObjective(
        gp.quicksum(selling_price[t] * sell[t] - purchase_price[t] * buy[t] for t in months),
        GRB.MAXIMIZE
    )

    # Inventory balance: end-of-month inventory
    model.addConstr(inv[0] == initial_inventory + buy[0] - sell[0], name="inv_balance_0")
    for t in range(1, 3):
        model.addConstr(inv[t] == inv[t - 1] + buy[t] - sell[t], name=f"inv_balance_{t}")

    # Warehouse capacity on end-of-month inventory
    for t in months:
        model.addConstr(inv[t] <= warehouse_capacity, name=f"capacity_end_{t}")

    # Warehouse capacity immediately after purchase (before sales)
    # stock after purchase = inv[t-1] + buy[t] for t>0, or initial_inventory + buy[0] for t=0
    model.addConstr(initial_inventory + buy[0] <= warehouse_capacity, name="capacity_post_buy_0")
    for t in range(1, 3):
        model.addConstr(inv[t - 1] + buy[t] <= warehouse_capacity, name=f"capacity_post_buy_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}