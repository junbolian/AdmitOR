import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    num_companies = 5
    num_markets = 3
    num_products = 3

    companies = range(num_companies)
    markets = range(num_markets)
    products = range(num_products)

    model = gp.Model("supply_allocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[c, p, mk] = units supplied by company c of product p to market mk
    x = model.addVars(companies, products, markets, lb=0.0, name="x")

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(
            profit[c][p][mk] * x[c, p, mk]
            for c in companies
            for p in products
            for mk in markets
        ),
        GRB.MAXIMIZE
    )

    # Demand satisfaction constraints
    for mk in markets:
        for p in products:
            model.addConstr(
                gp.quicksum(x[c, p, mk] for c in companies) == demand[mk][p],
                name=f"demand_mk{mk}_p{p}"
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