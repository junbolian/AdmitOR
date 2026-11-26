import gurobipy as gp
from gurobipy import GRB

def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    initial_funds = params["initial_funds"]
    purchase_price = params["purchase_price"]   # list of 3 values, Jan–Mar
    selling_price = params["selling_price"]     # list of 3 values, Jan–Mar
    terminal_inventory_requirement = params["terminal_inventory_requirement"]

    # Months indexed 0,1,2 → January, February, March
    months = range(3)

    model = gp.Model("grain_trading")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # buy[t]: amount of grain purchased in month t
    # sell[t]: amount of grain sold in month t
    #   (grain bought in month t can only be sold starting month t+1)
    buy = model.addVars(months, lb=0.0, name="buy")
    sell = model.addVars(months, lb=0.0, name="sell")

    # Inventory at end of month t
    # inv[0] = initial_inventory + buy[0] - sell[0]
    # But sell[t] can only come from inventory that existed before month t's purchase,
    # i.e. grain bought in month t cannot be sold in month t.
    # So effectively: inv[t] = inv[t-1] + buy[t] - sell[t]
    # and sell[t] is bounded by inv[t-1] (inventory before this month's purchase).
    inv = model.addVars(months, lb=0.0, name="inv")

    # Inventory dynamics
    # Month 0 (January):
    #   inv[0] = initial_inventory + buy[0] - sell[0]
    #   sell[0] is limited to initial_inventory (can't sell what was just bought)
    model.addConstr(inv[0] == initial_inventory + buy[0] - sell[0], name="inv_balance_0")
    model.addConstr(sell[0] <= initial_inventory, name="sell_limit_0")

    for t in range(1, 3):
        model.addConstr(inv[t] == inv[t-1] + buy[t] - sell[t], name=f"inv_balance_{t}")
        # Can only sell what was in stock at end of previous month (before this month's purchase)
        model.addConstr(sell[t] <= inv[t-1], name=f"sell_limit_{t}")

    # Warehouse capacity: inventory at end of each month cannot exceed capacity
    for t in months:
        model.addConstr(inv[t] <= warehouse_capacity, name=f"capacity_{t}")

    # Terminal inventory requirement
    model.addConstr(inv[2] >= terminal_inventory_requirement, name="terminal_inv")

    # Cash flow constraints: must have enough funds to pay for purchases each month
    # Funds at end of month t = funds at end of month t-1
    #                           + revenue from sales in month t
    #                           - cost of purchases in month t
    funds = model.addVars(months, lb=0.0, name="funds")

    # Month 0:
    model.addConstr(
        funds[0] == initial_funds
                   + selling_price[0] * sell[0]
                   - purchase_price[0] * buy[0],
        name="funds_balance_0"
    )

    for t in range(1, 3):
        model.addConstr(
            funds[t] == funds[t-1]
                       + selling_price[t] * sell[t]
                       - purchase_price[t] * buy[t],
            name=f"funds_balance_{t}"
        )

    # Objective: maximize total profit = total revenue - total purchase cost
    # (funds[2] - initial_funds) gives net cash gain, which equals total profit
    revenue = gp.quicksum(selling_price[t] * sell[t] for t in months)
    cost = gp.quicksum(purchase_price[t] * buy[t] for t in months)
    model.setObjective(revenue - cost, GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}