import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]      # list of length 7
    demand = params["demand"]      # list of length 6
    cost = params["cost"]          # 7x6 matrix
    capacity = params["capacity"]  # 7x6 matrix

    num_origins = 7
    num_destinations = 6
    origins = range(num_origins)
    destinations = range(num_destinations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {
        (i, j): model.addVar(lb=0.0, ub=capacity[i][j], name=f"x_{i}_{j}")
        for i in origins
        for j in destinations
    }

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in origins for j in destinations),
        GRB.MINIMIZE
    )

    for i in origins:
        model.addConstr(
            gp.quicksum(x[i, j] for j in destinations) <= supply[i],
            name=f"supply_{i}"
        )

    for j in destinations:
        model.addConstr(
            gp.quicksum(x[i, j] for i in origins) >= demand[j],
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