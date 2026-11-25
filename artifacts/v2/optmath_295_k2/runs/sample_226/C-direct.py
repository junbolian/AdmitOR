import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = {
        (0, 0): params["demand_p0_m0"],
        (1, 0): params["demand_p1_m0"],
        (0, 1): params["demand_p0_m1"],
        (1, 1): params["demand_p1_m1"],
        (0, 2): params["demand_p0_m2"],
        (1, 2): params["demand_p1_m2"],
        (0, 3): params["demand_p0_m3"],
        (1, 3): params["demand_p1_m3"],
    }

    profit = params["profit"]

    companies = range(4)
    products = range(2)
    markets = range(4)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(companies, products, markets, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(
            profit[c][p][m] * x[c, p, m]
            for c in companies
            for p in products
            for m in markets
        ),
        GRB.MAXIMIZE
    )

    for p in products:
        for m in markets:
            model.addConstr(
                gp.quicksum(x[c, p, m] for c in companies) == demand[(p, m)],
                name=f"demand_p{p}_m{m}"
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