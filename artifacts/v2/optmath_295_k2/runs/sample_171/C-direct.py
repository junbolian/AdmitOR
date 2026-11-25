import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_origins = 6
    num_destinations = 8

    origins = range(num_origins)
    destinations = range(num_destinations)

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    x = model.addVars(origins, destinations, lb=0.0, name="x")

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

    for i in origins:
        for j in destinations:
            model.addConstr(x[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}