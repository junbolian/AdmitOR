import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price = params["price"]           # list of 5 prices
    share_limit = params["share_limit"]  # list of 5 share limits
    payoff = params["payoff"]         # 5x5 matrix: rows=countries, cols=securities

    num_securities = 5
    num_countries = 5

    model = gp.Model("world_cup_securities")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of shares purchased for each security
    x = [
        model.addVar(lb=0, ub=share_limit[j], vtype=GRB.CONTINUOUS, name=f"x_{j}")
        for j in range(num_securities)
    ]

    # Auxiliary variable: worst-case revenue (minimum over all country outcomes)
    z = model.addVar(lb=-GRB.INFINITY, name="z")

    # Objective: maximize worst-case revenue minus cost
    cost = gp.quicksum(price[j] * x[j] for j in range(num_securities))
    model.setObjective(z - cost, GRB.MAXIMIZE)

    # For each country outcome, revenue must be >= z
    for i in range(num_countries):
        revenue_i = gp.quicksum(payoff[i][j] * x[j] for j in range(num_securities))
        model.addConstr(revenue_i >= z, name=f"worst_case_country_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}