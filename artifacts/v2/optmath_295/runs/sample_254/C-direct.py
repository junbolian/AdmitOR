import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    n_facilities = len(supply)
    n_centers = len(demand)

    model = gp.Model("transport")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_facilities):
        for j in range(n_centers):
            x[i, j] = model.addVar(lb=0.0, ub=limit[i][j], name=f"x_{i}_{j}")

    model.update()

    for i in range(n_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_centers)) <= supply[i],
            name=f"supply_{i}",
        )

    for j in range(n_centers):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_facilities)) >= demand[j],
            name=f"demand_{j}",
        )

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(n_facilities)
            for j in range(n_centers)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": "failed"}