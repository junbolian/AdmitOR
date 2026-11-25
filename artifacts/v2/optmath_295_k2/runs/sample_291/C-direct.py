import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    num_companies = 5
    num_markets = 2

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_companies, num_markets, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(profit[i][j] * x[i, j] for i in range(num_companies) for j in range(num_markets)),
        GRB.MAXIMIZE
    )

    for j in range(num_markets):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_companies)) == demand[j],
            name=f"demand_{j}"
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