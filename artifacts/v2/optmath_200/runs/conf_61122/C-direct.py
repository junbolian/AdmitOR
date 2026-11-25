import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]  # shape: (5 markets, 2 products)
    profit = params["profit"]  # shape: (4 companies, 5 markets, 2 products)

    num_companies = 4
    num_markets = 5
    num_products = 2

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: quantity supplied by company c to market j for product p
    x = {}
    for c in range(num_companies):
        for j in range(num_markets):
            for p in range(num_products):
                x[c, j, p] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS)

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(profit[c][j][p] * x[c, j, p]
                    for c in range(num_companies)
                    for j in range(num_markets)
                    for p in range(num_products)),
        GRB.MAXIMIZE
    )

    # Demand satisfaction constraints
    for j in range(num_markets):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[c, j, p] for c in range(num_companies)) == demand[j][p]
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