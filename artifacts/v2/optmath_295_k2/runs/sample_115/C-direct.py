import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_origins = len(supply)
    n_dest = len(demand)

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_origins):
        for j in range(n_dest):
            x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_origins) for j in range(n_dest)),
        GRB.MINIMIZE,
    )

    for i in range(n_origins):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_dest)) == supply[i])

    for j in range(n_dest):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n_origins)) == demand[j])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}