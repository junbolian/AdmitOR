import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price = params["price"]           # list of 5 prices
    share_limit = params["share_limit"]  # list of 5 share limits
    payoff = params["payoff"]         # 5x5 matrix: payoff[i][j] = payoff of security i under country j

    n_securities = 5
    n_countries = 5

    model = gp.Model("world_cup_securities")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of shares purchased for each security
    x = [
        model.addVar(lb=0, ub=share_limit[i], vtype=GRB.CONTINUOUS, name=f"x_{i}")
        for i in range(n_securities)
    ]

    # Auxiliary variable: worst-case revenue (minimum over all country outcomes)
    z = model.addVar(lb=-GRB.INFINITY, name="z")

    # Maximize worst-case revenue
    model.setObjective(z, GRB.MAXIMIZE)

    # For each country outcome, revenue = sum of payoffs - cost of portfolio
    # cost = sum_i price[i] * x[i]  (paid upfront, fixed)
    # revenue under country j = sum_i payoff[i][j] * x[i] - sum_i price[i] * x[i]
    # z <= revenue under each country j

    cost = gp.quicksum(price[i] * x[i] for i in range(n_securities))

    for j in range(n_countries):
        revenue_j = gp.quicksum(payoff[i][j] * x[i] for i in range(n_securities)) - cost
        model.addConstr(z <= revenue_j, name=f"worst_case_country_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}