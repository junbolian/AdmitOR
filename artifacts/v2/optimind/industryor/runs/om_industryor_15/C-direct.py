import gurobipy as gp
from gurobipy import GRB

def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    purchase_price = params["purchase_price"]  # list of length 3
    selling_price = params["selling_price"]    # list of length 3

    months = range(3)

    model = gp.Model("quarterly_plan")
    model.setParam("OutputFlag", 0)

    # Decision variables
    buy = model.addVars(months, lb=0.0, name="buy")
    sell = model.addVars(months, lb=0.0, name="sell")
    inventory = model.addVars(months, lb=0.0, ub=warehouse_capacity, name="inventory")

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum((selling_price[t] - purchase_price[t]) * sell[t]
                    - purchase_price[t] * (buy[t] - sell[t])
                    for t in months),
        GRB.MAXIMIZE
    )

    # Simpler equivalent objective: revenue - cost
    # revenue = sum selling_price[t] * sell[t]
    # cost    = sum purchase_price[t] * buy[t]
    model.setObjective(
        gp.quicksum(selling_price[t] * sell[t] - purchase_price[t] * buy[t]
                    for t in months),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    # inventory[0] = initial_inventory + buy[0] - sell[0]
    model.addConstr(inventory[0] == initial_inventory + buy[0] - sell[0], name="inv_balance_0")
    for t in range(1, 3):
        model.addConstr(inventory[t] == inventory[t-1] + buy[t] - sell[t],
                        name=f"inv_balance_{t}")

    # Cannot sell more than available at start of month (before purchase arrives)
    # Available to sell in month t = inventory at end of previous month + buy[t]
    # i.e., sell[t] <= inventory[t-1] + buy[t]  which is equivalent to inventory[t] >= 0 (already enforced by lb)

    # Warehouse capacity: inventory after purchase but before selling
    # Goods are purchased at the beginning, so warehouse must hold initial + buy
    # but typically the capacity applies to inventory held (end-of-month)
    # inventory[t] ub=warehouse_capacity already set above

    # Also enforce capacity on stock right after purchase (beginning of month)
    # stock after purchase in month 0: initial_inventory + buy[0] <= warehouse_capacity
    model.addConstr(initial_inventory + buy[0] <= warehouse_capacity, name="cap_after_buy_0")
    for t in range(1, 3):
        model.addConstr(inventory[t-1] + buy[t] <= warehouse_capacity,
                        name=f"cap_after_buy_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}