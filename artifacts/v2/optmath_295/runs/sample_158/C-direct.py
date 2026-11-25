import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    num_companies = 3
    num_markets = 4
    num_products = 2

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[c][j][p] = units of product p supplied by company c to market j
    x = [
        [
            [
                model.addVar(lb=0.0, name=f"x_{c}_{j}_{p}")
                for p in range(num_products)
            ]
            for j in range(num_markets)
        ]
        for c in range(num_companies)
    ]

    # Objective: maximize total profit
    obj = gp.quicksum(
        profit[c][j][p] * x[c][j][p]
        for c in range(num_companies)
        for j in range(num_markets)
        for p in range(num_products)
    )
    model.setObjective(obj, GRB.MAXIMIZE)

    # Demand satisfaction constraints
    for j in range(num_markets):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[c][j][p] for c in range(num_companies)) == demand[j][p],
                name=f"demand_{j}_{p}"
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