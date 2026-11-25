import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_companies = 5
    num_markets = 4
    num_products = 2

    profit = {}
    for co in range(num_companies):
        for ma in range(num_markets):
            for pr in range(num_products):
                key = f"profit_co{co}_ma{ma}_pr{pr}"
                profit[(co, ma, pr)] = params[key]

    demand = {}
    for ma in range(num_markets):
        for pr in range(num_products):
            key = f"demand_ma{ma}_pr{pr}"
            demand[(ma, pr)] = params[key]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    supply = model.addVars(num_companies, num_markets, num_products, lb=0.0, name="supply")

    model.setObjective(
        gp.quicksum(
            profit[(co, ma, pr)] * supply[co, ma, pr]
            for co in range(num_companies)
            for ma in range(num_markets)
            for pr in range(num_products)
        ),
        GRB.MAXIMIZE
    )

    for ma in range(num_markets):
        for pr in range(num_products):
            model.addConstr(
                gp.quicksum(supply[co, ma, pr] for co in range(num_companies)) == demand[(ma, pr)],
                name=f"demand_ma{ma}_pr{pr}"
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