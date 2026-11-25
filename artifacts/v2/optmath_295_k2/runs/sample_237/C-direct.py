import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    num_companies = 5
    num_markets = 4
    num_products = 2

    model = gp.Model("market_supply")
    model.setParam("OutputFlag", 0)

    # Decision variables: quantity supplied by company c to market m for product p
    x = {}
    for c in range(num_companies):
        for mkt in range(num_markets):
            for p in range(num_products):
                x[c, mkt, p] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                             name=f"x_{c}_{mkt}_{p}")

    # Objective: maximize total profit
    obj = gp.quicksum(
        profit[c][mkt][p] * x[c, mkt, p]
        for c in range(num_companies)
        for mkt in range(num_markets)
        for p in range(num_products)
    )
    model.setObjective(obj, GRB.MAXIMIZE)

    # Demand satisfaction constraints
    for mkt in range(num_markets):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[c, mkt, p] for c in range(num_companies)) == demand[mkt][p],
                name=f"demand_{mkt}_{p}"
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