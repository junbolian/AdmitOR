import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]  # 5x2 matrix
    demand = params["demand"]  # length-2 list

    num_companies = 5
    num_markets = 2

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: quantity supplied by company i to market j
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{j}")
          for j in range(num_markets)]
         for i in range(num_companies)]

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(profit[i][j] * x[i][j]
                    for i in range(num_companies)
                    for j in range(num_markets)),
        GRB.MAXIMIZE
    )

    # Demand satisfaction constraints
    for j in range(num_markets):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_companies)) == demand[j],
            name=f"demand_{j}"
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