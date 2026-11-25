import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]  # 3 products x 3 markets
    profit = params["profit"]  # 5 companies x 3 products x 3 markets

    num_companies = 5
    num_products = 3
    num_markets = 3

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[c, p, m] = units supplied by company c of product p to market m
    x = model.addVars(num_companies, num_products, num_markets, lb=0.0, name="x")

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(
            profit[c][p][m] * x[c, p, m]
            for c in range(num_companies)
            for p in range(num_products)
            for m in range(num_markets)
        ),
        GRB.MAXIMIZE
    )

    # Demand satisfaction constraints
    for p in range(num_products):
        for m in range(num_markets):
            model.addConstr(
                gp.quicksum(x[c, p, m] for c in range(num_companies)) == demand[p][m],
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