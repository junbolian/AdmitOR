import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    profit_margin = params["profit_margin"]

    n_markets = len(demand)

    model = gp.Model("market_allocation")
    model.setParam("OutputFlag", 0)

    supply = model.addVars(n_markets, lb=0.0, name="supply")

    model.setObjective(
        gp.quicksum(profit_margin[i] * supply[i] for i in range(n_markets)),
        GRB.MAXIMIZE
    )

    for i in range(n_markets):
        model.addConstr(supply[i] == demand[i], name=f"demand_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}