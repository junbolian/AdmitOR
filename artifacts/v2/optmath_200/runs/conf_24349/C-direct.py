import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_destinations = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n_origins):
        for j in range(n_destinations):
            x[i, j] = model.addVar(lb=0.0, ub=capacity[i][j], vtype=GRB.CONTINUOUS)

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_origins) for j in range(n_destinations)),
        GRB.MINIMIZE
    )

    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_destinations)) <= supply[i]
        )

    for j in range(n_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_origins)) >= demand[j]
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