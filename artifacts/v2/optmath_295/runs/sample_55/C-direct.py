import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_origins = len(supply)
    n_destinations = len(demand)

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_origins):
        for j in range(n_destinations):
            x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(
            transport_cost[i][j] * x[i, j]
            for i in range(n_origins)
            for j in range(n_destinations)
        ),
        GRB.MINIMIZE,
    )

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
    return {"objective": None, "status": f"status_{model.status}"}