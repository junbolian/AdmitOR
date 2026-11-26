import gurobipy as gp
from gurobipy import GRB

def solve(params):
    security_price = params["security_price"]   # list of 5 prices
    share_limit    = params["share_limit"]       # list of 5 share limits
    payoff         = params["payoff"]            # 5x5 matrix: payoff[i][j]

    num_securities = 5
    num_countries  = 5

    model = gp.Model("world_cup_securities")
    model.setParam("OutputFlag", 0)

    # x[i] = number of shares purchased of security i
    x = model.addVars(num_securities, lb=0.0, name="x")

    # Enforce share limits
    for i in range(num_securities):
        model.addConstr(x[i] <= share_limit[i], name=f"share_limit_{i}")

    # z = worst-case revenue (net payoff minus cost) across all country outcomes
    z = model.addVar(lb=-GRB.INFINITY, name="z")

    # Total cost of purchasing shares
    total_cost = gp.quicksum(security_price[i] * x[i] for i in range(num_securities))

    # For each country outcome j, revenue = sum_i payoff[i][j] * x[i] - total_cost
    # z <= revenue for every outcome j
    for j in range(num_countries):
        revenue_j = gp.quicksum(payoff[i][j] * x[i] for i in range(num_securities))
        model.addConstr(z <= revenue_j - total_cost, name=f"worst_case_country_{j}")

    # Maximize worst-case revenue
    model.setObjective(z, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}