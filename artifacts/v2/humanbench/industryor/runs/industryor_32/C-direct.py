import gurobipy as gp
from gurobipy import GRB

def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory  = params["initial_inventory"]
    purchase_prices    = params["purchase_prices"]   # list of 6 values, July–December
    sale_prices        = params["sale_prices"]        # list of 6 values, July–December

    n_months = 6  # structural constant: July through December

    model = gp.Model("purchasing_selling_plan")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # buy[t]  : units purchased at the beginning of month t
    # sell[t] : units sold during month t
    buy  = model.addVars(n_months, lb=0.0, name="buy")
    sell = model.addVars(n_months, lb=0.0, name="sell")

    # Inventory after transactions in month t
    # inv[t] = inventory at end of month t
    inv = model.addVars(n_months, lb=0.0, name="inv")

    # Inventory balance constraints
    for t in range(n_months):
        prev_inv = initial_inventory if t == 0 else inv[t - 1]
        # At start of month: receive buy[t], then sell sell[t]
        # End-of-month inventory
        model.addConstr(inv[t] == prev_inv + buy[t] - sell[t],
                        name=f"balance_{t}")

    # Warehouse capacity: inventory after purchasing but before selling
    # must not exceed capacity; also end-of-month inventory ≤ capacity
    for t in range(n_months):
        prev_inv = initial_inventory if t == 0 else inv[t - 1]
        # inventory right after purchasing (before selling)
        model.addConstr(prev_inv + buy[t] <= warehouse_capacity,
                        name=f"capacity_{t}")

    # Objective: total revenue = sales revenue - purchase costs
    revenue = gp.quicksum(sale_prices[t] * sell[t] - purchase_prices[t] * buy[t]
                          for t in range(n_months))
    model.setObjective(revenue, GRB.MAXIMIZE)

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