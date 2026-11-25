import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]                        # [product][week]
    production_cost = params["production_cost"]      # [product][week]
    setup_cost = params["setup_cost"]                # [product][week]
    holding_cost = params["holding_cost"]            # scalar or [product][week]
    resource_usage = params["resource_usage"]        # [product]
    resource_capacity = params["resource_capacity"]  # [week]
    production_limit = params["production_limit"]    # [product][week]

    num_products = 3
    num_weeks = 8
    products = range(num_products)
    weeks = range(num_weeks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x[p][t]: production quantity of product p in week t
    x = [[model.addVar(lb=0.0, name=f"x_{p}_{t}") for t in weeks] for p in products]
    # s[p][t]: binary setup variable
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{p}_{t}") for t in weeks] for p in products]
    # inv[p][t]: inventory at end of week t
    inv = [[model.addVar(lb=0.0, name=f"inv_{p}_{t}") for t in weeks] for p in products]

    # Objective: minimize total production cost + setup cost + holding cost
    obj = gp.LinExpr()
    for p in products:
        for t in weeks:
            obj += production_cost[p][t] * x[p][t]
            obj += setup_cost[p][t] * y[p][t]
            # holding_cost may be scalar or indexed
            if hasattr(holding_cost, '__getitem__'):
                try:
                    hc = holding_cost[p][t]
                except (TypeError, KeyError, IndexError):
                    try:
                        hc = holding_cost[p]
                    except (TypeError, KeyError, IndexError):
                        hc = holding_cost
            else:
                hc = holding_cost
            obj += hc * inv[p][t]

    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    for p in products:
        for t in weeks:
            d = demand[p][t]
            if t == 0:
                # Starting inventory is 0
                model.addConstr(x[p][t] - inv[p][t] == d, name=f"balance_{p}_{t}")
            else:
                model.addConstr(inv[p][t-1] + x[p][t] - inv[p][t] == d, name=f"balance_{p}_{t}")

    # Resource capacity constraints
    for t in weeks:
        model.addConstr(
            gp.quicksum(resource_usage[p] * x[p][t] for p in products) <= resource_capacity[t],
            name=f"resource_{t}"
        )

    # Production limit and setup linking constraints
    for p in products:
        for t in weeks:
            pl = production_limit[p][t]
            model.addConstr(x[p][t] <= pl * y[p][t], name=f"setup_link_{p}_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}