import gurobipy as gp
from gurobipy import GRB

def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_stock = params["initial_stock"]
    initial_capital = params["initial_capital"]
    purchase_price = params["purchase_price"]   # list of length 3
    selling_price = params["selling_price"]     # list of length 3
    terminal_stock_requirement = params["terminal_stock_requirement"]

    # Months indexed 0,1,2 (Jan, Feb, Mar)
    T = 3

    model = gp.Model("grain_trading")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # buy[t]: units purchased in month t (arrives same month, can sell next month)
    # sell[t]: units sold in month t
    buy  = model.addVars(T, lb=0.0, name="buy")
    sell = model.addVars(T, lb=0.0, name="sell")

    # Stock at end of each month (after purchases arrive and sales depart)
    # sell[t] draws from stock that existed at the START of month t (before new purchases)
    # buy[t] arrives same month but can only be sold the FOLLOWING month
    # So: stock_end[t] = stock_end[t-1] - sell[t] + buy[t]
    # where stock_end[-1] = initial_stock

    # Capital at end of each month
    # capital_end[t] = capital_end[t-1] - buy[t]*purchase_price[t] + sell[t]*selling_price[t]
    # where capital_end[-1] = initial_capital

    # Note: sell[t] draws from the stock available at start of month t,
    # which is stock_end[t-1] (old stock only, since new purchases can't be sold yet).
    # So sell[t] <= stock_end[t-1], which is stock before buy[t] is added for selling purposes.

    # We introduce auxiliary stock variables for clarity
    # stock_before_buy[t] = stock available for selling in month t = stock_end[t-1]
    # stock_end[t] = stock_before_buy[t] - sell[t] + buy[t]

    stock_end = {}
    capital_end = {}

    for t in range(T):
        stock_before = initial_stock if t == 0 else stock_end[t - 1]
        cap_before   = initial_capital if t == 0 else capital_end[t - 1]

        stock_end[t]   = model.addVar(lb=0.0, name=f"stock_end_{t}")
        capital_end[t] = model.addVar(lb=0.0, name=f"capital_end_{t}")

        # Stock balance
        model.addConstr(
            stock_end[t] == stock_before - sell[t] + buy[t],
            name=f"stock_balance_{t}"
        )

        # Capital balance
        model.addConstr(
            capital_end[t] == cap_before
                              - buy[t]  * purchase_price[t]
                              + sell[t] * selling_price[t],
            name=f"capital_balance_{t}"
        )

        # Warehouse capacity: stock after purchases arrive
        model.addConstr(stock_end[t] <= warehouse_capacity, name=f"warehouse_{t}")

        # Can only sell what was in stock BEFORE this month's purchase
        model.addConstr(sell[t] <= stock_before, name=f"sell_limit_{t}")

        # Must have enough capital to pay for purchases
        model.addConstr(
            buy[t] * purchase_price[t] <= cap_before,
            name=f"capital_limit_{t}"
        )

    # Terminal stock requirement
    model.addConstr(stock_end[T - 1] >= terminal_stock_requirement, name="terminal_stock")

    # Objective: maximize total profit = final capital - initial capital
    # (profit = revenue from sales - cost of purchases)
    model.setObjective(capital_end[T - 1] - initial_capital, GRB.MAXIMIZE)

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