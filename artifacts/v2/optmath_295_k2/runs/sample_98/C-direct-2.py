import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    capacity_consumption = params["capacity_consumption"]

    n_products = len(demand)
    n_months = len(demand[0])

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = {}
    y = {}
    inv = {}

    for p in range(n_products):
        for t in range(n_months):
            x[p, t] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{p}_{t}")
            y[p, t] = model.addVar(vtype=GRB.BINARY, name=f"y_{p}_{t}")
            inv[p, t] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"inv_{p}_{t}")

    model.update()

    obj = gp.LinExpr()
    for p in range(n_products):
        for t in range(n_months):
            obj += production_cost[p][t] * x[p, t]
            obj += setup_cost[p][t] * y[p, t]
            obj += holding_cost[p] * inv[p, t]
    model.setObjective(obj, GRB.MINIMIZE)

    for p in range(n_products):
        for t in range(n_months):
            big_m = sum(demand[p][s] for s in range(t, n_months))
            model.addConstr(x[p, t] <= big_m * y[p, t], name=f"link_{p}_{t}")

    for t in range(n_months):
        model.addConstr(
            gp.quicksum(capacity_consumption[p] * x[p, t] for p in range(n_products))
            <= capacity[t],
            name=f"cap_{t}",
        )

    for p in range(n_products):
        for t in range(n_months):
            cum_prod = gp.quicksum(x[p, s] for s in range(t + 1))
            cum_dem = sum(demand[p][s] for s in range(t + 1))
            model.addConstr(cum_prod - inv[p, t] == cum_dem, name=f"bal_{p}_{t}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}