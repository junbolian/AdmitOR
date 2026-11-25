import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    num_companies = 5
    num_products = 3
    num_markets = 3

    companies = range(num_companies)
    products = range(num_products)
    markets = range(num_markets)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[c, p, mk] = units of product p supplied by company c to market mk
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

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}