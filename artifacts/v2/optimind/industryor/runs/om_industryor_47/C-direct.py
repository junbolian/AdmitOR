import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
    }
    price = {
        1: params["price_1month"],
        2: params["price_2month"],
        3: params["price_3month"],
        4: params["price_4month"],
    }

    # Enumerate all valid (start_month, duration) contract types
    # start t in {1,2,3,4}, duration k in {1,2,3,4}, t + k - 1 <= 4
    contracts = [(t, k) for t in range(1, 5) for k in range(1, 5) if t + k - 1 <= 4]

    model = gp.Model("warehouse_rental")
    model.setParam("OutputFlag", 0)

    # Decision variable: area rented under contract (t, k)
    x = {}
    for (t, k) in contracts:
        x[(t, k)] = model.addVar(lb=0.0, name=f"x_{t}_{k}")

    # Objective: minimize total cost
    # Cost of contract (t,k): price[k] * k * x[(t,k)]  (rate per m² per month * months * area)
    model.setObjective(
        gp.quicksum(price[k] * k * x[(t, k)] for (t, k) in contracts),
        GRB.MINIMIZE
    )

    # Demand constraints: for each month m, sum of active contracts >= demand[m]
    for m in range(1, 5):
        active = [(t, k) for (t, k) in contracts if t <= m <= t + k - 1]
        model.addConstr(
            gp.quicksum(x[(t, k)] for (t, k) in active) >= demand[m],
            name=f"demand_month_{m}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}