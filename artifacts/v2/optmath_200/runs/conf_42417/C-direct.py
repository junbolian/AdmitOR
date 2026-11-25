import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    cap = params["cap"]

    n_origins = 7
    n_destinations = 6

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n_origins):
        for j in range(n_destinations):
            x[i, j] = model.addVar(lb=0.0, ub=cap[i][j], name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_origins) for j in range(n_destinations)),
        GRB.MINIMIZE
    )

    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_destinations)) <= supply[i],
            name=f"supply_{i}"
        )

    for j in range(n_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_origins)) >= demand[j],
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