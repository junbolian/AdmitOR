import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_destinations = len(demand)

    model = gp.Model("transportation")

    x = model.addVars(
        n_origins, n_destinations, lb=0.0, vtype=GRB.CONTINUOUS, name="x"
    )

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(n_origins)
            for j in range(n_destinations)
        ),
        GRB.MINIMIZE,
    )

    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_destinations)) <= supply[i],
            name=f"supply_{i}",
        )

    for j in range(n_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_origins)) == demand[j],
            name=f"demand_{j}",
        )

    for i in range(n_origins):
        for j in range(n_destinations):
            model.addConstr(
                x[i, j] <= capacity[i][j],
                name=f"cap_{i}_{j}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}