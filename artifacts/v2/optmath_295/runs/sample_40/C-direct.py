import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    profit_company0 = params["profit_company0"]
    profit_company1 = params["profit_company1"]

    n_markets = 4
    n_products = 3
    n_companies = 2

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[c, m, p] = units supplied by company c to market m of product p
    x = model.addVars(n_companies, n_markets, n_products, lb=0.0, name="x")

    def get_profit(c, m, p):
        if c == 0:
            return profit_company0[m][p]
        else:
            return profit_company1[m][p]

    model.setObjective(
        gp.quicksum(
            get_profit(c, m, p) * x[c, m, p]
            for c in range(n_companies)
            for m in range(n_markets)
            for p in range(n_products)
        ),
        GRB.MAXIMIZE
    )

    for m in range(n_markets):
        for p in range(n_products):
            model.addConstr(
                gp.quicksum(x[c, m, p] for c in range(n_companies)) == demand[m][p],
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