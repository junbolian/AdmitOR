import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    num_companies = len(profit)
    num_products = len(demand)
    num_markets = len(demand[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: quantity company c supplies of product p to market k
    x = {}
    for c in range(num_companies):
        for p in range(num_products):
            for k in range(num_markets):
                x[c, p, k] = model.addVar(lb=0.0, name=f"x_{c}_{p}_{k}")

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(
            profit[c][p][k] * x[c, p, k]
            for c in range(num_companies)
            for p in range(num_products)
            for k in range(num_markets)
        ),
        GRB.MAXIMIZE
    )

    # Demand constraints: total supply to each market for each product must equal demand
    for p in range(num_products):
        for k in range(num_markets):
            model.addConstr(
                gp.quicksum(x[c, p, k] for c in range(num_companies)) == demand[p][k],
                name=f"demand_{p}_{k}"
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
        return {"objective": None, "status": f"status_{status}"}