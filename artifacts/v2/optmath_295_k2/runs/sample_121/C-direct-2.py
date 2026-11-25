import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    num_origins = 14
    num_destinations = 12

    origins = range(num_origins)
    destinations = range(num_destinations)

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = model.addVars(origins, destinations, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in origins for j in destinations),
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