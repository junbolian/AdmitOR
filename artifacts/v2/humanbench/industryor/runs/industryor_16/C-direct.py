import gurobipy as gp
from gurobipy import GRB

def solve(params):
    storage_capacity = params["storage_capacity"]  # max warehouse capacity (10,000 m^3)
    a = params["storage_cost_a"]                   # storage cost constant term
    b = params["storage_cost_b"]                   # storage cost per-quarter rate
    buy_price = params["buy_price"]                # list of 4 buying prices [winter, spring, summer, autumn]
    sell_price = params["sell_price"]              # list of 4 selling prices
    max_sales = params["max_sales"]                # list of 4 max sales volumes

    # Quarters: 0=Winter, 1=Spring, 2=Summer, 3=Autumn
    quarters = range(4)

    model = gp.Model("wood_storage")
    model.setParam("OutputFlag", 0)

    # Decision variables:
    # x[i] = amount purchased in quarter i (10,000 m^3)
    # s[i] = amount sold in quarter i (10,000 m^3)
    # inv[i] = inventory at end of quarter i (10,000 m^3)
    #   (inventory stored from quarter i to be sold later)

    x = model.addVars(4, lb=0.0, name="buy")
    s = model.addVars(4, lb=0.0, name="sell")
    # inv[i][j]: amount purchased in quarter i that is sold in quarter j (j >= i)
    # To track storage costs correctly, we need to know how long each batch is stored.
    # Let y[i][j] = volume bought in quarter i and sold in quarter j (j >= i)
    # Storage cost for y[i][j]: stored for (j - i) quarters, cost = (a + b*(j-i)) per m^3

    y = {}
    for i in quarters:
        for j in quarters:
            if j >= i:
                y[i, j] = model.addVar(lb=0.0, name=f"y_{i}_{j}")

    # Constraints:
    # 1. Total purchased in quarter i = sum of y[i][j] for j >= i
    for i in quarters:
        model.addConstr(x[i] == gp.quicksum(y[i, j] for j in quarters if j >= i),
                        name=f"buy_alloc_{i}")

    # 2. Total sold in quarter j = sum of y[i][j] for i <= j
    for j in quarters:
        model.addConstr(s[j] == gp.quicksum(y[i, j] for i in quarters if i <= j),
                        name=f"sell_alloc_{j}")

    # 3. Sales cannot exceed projected maximum
    for j in quarters:
        model.addConstr(s[j] <= max_sales[j], name=f"max_sales_{j}")

    # 4. Warehouse capacity constraint: inventory at end of each quarter <= storage_capacity
    # Inventory at end of quarter q = wood purchased in quarters 0..q that hasn't been sold yet
    # = sum over i<=q, j>q of y[i][j]
    for q in quarters:
        inventory_at_end_q = gp.quicksum(
            y[i, j] for i in quarters for j in quarters
            if i <= q and j > q
        )
        model.addConstr(inventory_at_end_q <= storage_capacity, name=f"capacity_{q}")

    # 5. All inventory sold by end of autumn (quarter 3): no wood carried beyond autumn
    # This is implicitly enforced since y[i][j] only defined for j <= 3.
    # Explicitly: sum of y[i][3] for all i must cover everything bought that hasn't been sold earlier.
    # Already handled by the structure (j only goes up to 3).

    # Objective: maximize profit = revenue - purchase cost - storage cost
    # Revenue from selling y[i][j] in quarter j: sell_price[j] * y[i][j]
    # Purchase cost of y[i][j]: buy_price[i] * y[i][j]
    # Storage cost of y[i][j]: stored for (j - i) quarters at (a + b*(j-i)) per unit
    #   Cost = (a + b*(j-i)) * y[i][j]
    # Note: if j == i, storage duration = 0 quarters, so storage cost = a * y[i][i]
    # Wait - re-read problem: storage cost is (a + b*u) yuan per m^3 where u is storage time in quarters
    # If sold same quarter as purchased (u=0): cost = a per m^3
    # If stored 1 quarter: cost = (a + b) per m^3, etc.

    profit = gp.quicksum(
        (sell_price[j] - buy_price[i] - (a + b * (j - i))) * y[i, j]
        for i in quarters for j in quarters if j >= i
    )

    model.setObjective(profit, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}