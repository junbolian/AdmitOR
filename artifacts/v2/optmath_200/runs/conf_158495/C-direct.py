import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    # Determine index ranges from the structure (lists or dicts)
    n_origins = len(supply)
    n_destinations = len(demand)
    n_products = len(demand[0]) if isinstance(demand[0], (list,)) else len(list(demand[0].values()))

    origins = range(n_origins)
    destinations = range(n_destinations)
    products = range(n_products)

    model = gp.Model("multi_commodity_transport")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[o, d, p] = units of product p shipped from origin o to destination d
    x = {}
    for o in origins:
        for d in destinations:
            for p in products:
                x[o, d, p] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{o}_{d}_{p}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[o][d][p] * x[o, d, p] for o in origins for d in destinations for p in products),
        GRB.MINIMIZE
    )

    # Supply constraints: total shipped from origin o for product p == supply[o][p]
    for o in origins:
        for p in products:
            model.addConstr(
                gp.quicksum(x[o, d, p] for d in destinations) == supply[o][p],
                name=f"supply_{o}_{p}"
            )

    # Demand constraints: total received at destination d for product p == demand[d][p]
    for d in destinations:
        for p in products:
            model.addConstr(
                gp.quicksum(x[o, d, p] for o in origins) == demand[d][p],
                name=f"demand_{d}_{p}"
            )

    # Capacity constraints: total units (all products) from origin o to destination d <= capacity[o][d]
    for o in origins:
        for d in destinations:
            model.addConstr(
                gp.quicksum(x[o, d, p] for p in products) <= capacity[o][d],
                name=f"capacity_{o}_{d}"
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