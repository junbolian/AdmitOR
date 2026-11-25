import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    pair_capacity = params["pair_capacity"]

    n_origins = 8
    n_destinations = 8
    origins = range(n_origins)
    destinations = range(n_destinations)

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = {
        (i, j): model.addVar(lb=0.0, ub=pair_capacity[i][j], name=f"x_{i}_{j}")
        for i in origins
        for j in destinations
    }

    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in origins for j in destinations),
        GRB.MINIMIZE,
    )

    for i in origins:
        model.addConstr(
            gp.quicksum(x[i, j] for j in destinations) == supply[i],
            name=f"supply_{i}",
        )

    for j in destinations:
        model.addConstr(
            gp.quicksum(x[i, j] for i in origins) == demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}