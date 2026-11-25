import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    profit_c0 = params["profit_c0"]
    profit_c1 = params["profit_c1"]

    num_products = 3
    num_markets = 4
    products = range(num_products)
    markets = range(num_markets)
    companies = range(2)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[c, m, p] = units supplied by company c to market m of product p
    x = model.addVars(companies, markets, products, lb=0.0, name="x")

    # Objective: maximize total profit
    profit = [profit_c0, profit_c1]
    model.setObjective(
        gp.quicksum(
            profit[c][m][p] * x[c, m, p]
            for c in companies
            for m in markets
            for p in products
        ),
        GRB.MAXIMIZE
    )

    # Demand satisfaction constraints
    for m in markets:
        for p in products:
            model.addConstr(
                gp.quicksum(x[c, m, p] for c in companies) == demand[m][p],
                name=f"demand_m{m}_p{p}"
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