import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_destinations = len(demand)

    origins = list(range(n_origins))
    destinations = list(range(n_destinations))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for i in origins:
        for j in destinations:
            x[i, j] = model.addVar(lb=0.0, ub=capacity[i][j], name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in origins for j in destinations),
        GRB.MINIMIZE
    )

    for i in origins:
        model.addConstr(
            gp.quicksum(x[i, j] for j in destinations) == supply[i],
            name=f"supply_{i}"
        )

    for j in destinations:
        model.addConstr(
            gp.quicksum(x[i, j] for i in origins) == demand[j],
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