import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]                      # [product][week]
    production_cost = params["production_cost"]    # [product][week]
    setup_cost = params["setup_cost"]              # [product][week]
    holding_cost = params["holding_cost"]          # scalar or [product][week] or [product]
    resource_usage = params["resource_usage"]      # [product]
    resource_capacity = params["resource_capacity"] # [week]
    production_limit = params["production_limit"]  # [product][week]

    num_products = 3
    num_weeks = 8
    products = range(num_products)
    weeks = range(num_weeks)

    # Normalize holding_cost to a 2D structure [product][week]
    def get_holding_cost(p, t):
        if isinstance(holding_cost, (int, float)):
            return holding_cost
        hc = holding_cost
        # Try indexing by product first
        try:
            val = hc[p]
        except (TypeError, KeyError, IndexError):
            return hc
        # If the product-level value is also indexable by week
        if isinstance(val, (int, float)):
            return val
        try:
            return val[t]
        except (TypeError, KeyError, IndexError):
            return val

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    x = model.addVars(num_products, num_weeks, lb=0.0, name="x")       # production quantity
    inv = model.addVars(num_products, num_weeks, lb=0.0, name="inv")   # ending inventory
    y = model.addVars(num_products, num_weeks, vtype=GRB.BINARY, name="y")  # setup binary

    # Objective: minimize production cost + setup cost + holding cost
    obj = gp.quicksum(
        production_cost[p][t] * x[p, t] +
        setup_cost[p][t] * y[p, t] +
        get_holding_cost(p, t) * inv[p, t]
        for p in products for t in weeks
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    for p in products:
        for t in weeks:
            if t == 0:
                model.addConstr(x[p, t] - inv[p, t] == demand[p][t], name=f"balance_{p}_{t}")
            else:
                model.addConstr(inv[p, t-1] + x[p, t] - inv[p, t] == demand[p][t], name=f"balance_{p}_{t}")

    # Resource capacity constraints
    for t in weeks:
        model.addConstr(
            gp.quicksum(resource_usage[p] * x[p, t] for p in products) <= resource_capacity[t],
            name=f"resource_{t}"
        )

    # Production limit: x[p,t] <= production_limit[p][t] * y[p,t]
    for p in products:
        for t in weeks:
            model.addConstr(x[p, t] <= production_limit[p][t] * y[p, t], name=f"setup_{p}_{t}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}