import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_cost = params["production_cost"]
    holding_cost = params["holding_cost"]
    backlog_cost = params["backlog_cost"]
    setup_cost = params["setup_cost"]
    production_capacity = params["production_capacity"]
    demand = params["demand"]
    T = params["period_count"]

    periods = range(T)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    x = model.addVars(periods, lb=0.0, name="x")          # production quantity
    inv = model.addVars(periods, lb=0.0, name="inv")       # ending inventory
    b = model.addVars(periods, lb=0.0, name="b")           # ending backlog
    y = model.addVars(periods, vtype=GRB.BINARY, name="y") # setup binary

    # Objective
    model.setObjective(
        gp.quicksum(
            production_cost[t] * x[t]
            + holding_cost[t] * inv[t]
            + backlog_cost[t] * b[t]
            + setup_cost[t] * y[t]
            for t in periods
        ),
        GRB.MINIMIZE
    )

    # Inventory/backlog balance constraints
    for t in periods:
        prev_inv = inv[t - 1] if t > 0 else 0.0
        prev_b = b[t - 1] if t > 0 else 0.0
        # inv[t] - b[t] = prev_inv - prev_b + x[t] - demand[t]
        model.addConstr(
            inv[t] - b[t] == prev_inv - prev_b + x[t] - demand[t],
            name=f"balance_{t}"
        )

    # Production capacity constraint
    for t in periods:
        model.addConstr(x[t] <= production_capacity * y[t], name=f"capacity_{t}")

    # Zero ending inventory and backlog
    model.addConstr(inv[T - 1] == 0.0, name="end_inv")
    model.addConstr(b[T - 1] == 0.0, name="end_backlog")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}