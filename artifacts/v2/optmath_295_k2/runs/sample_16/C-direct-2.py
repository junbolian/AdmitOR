import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    arc_capacity = params["arc_capacity"]

    n_origins = len(supply)
    n_destinations = len(demand)

    model = gp.Model("transport")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_origins):
        for j in range(n_destinations):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=arc_capacity[i][j],
                obj=cost[i][j],
                name=f"x_{i}_{j}",
            )

    model.modelSense = GRB.MINIMIZE

    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_destinations)) == supply[i],
            name=f"supply_{i}",
        )

    for j in range(n_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_origins)) == demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}

    return {"objective": None, "status": f"status_{model.status}"}