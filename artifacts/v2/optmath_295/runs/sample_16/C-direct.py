import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = 8
    n_destinations = 8

    origins = range(n_origins)
    destinations = range(n_destinations)

    # Build upper bounds for each (i, j) pair
    ub = {}
    for i in origins:
        for j in destinations:
            if (i, j) in capacity:
                ub[(i, j)] = capacity[(i, j)]
            else:
                ub[(i, j)] = min(supply[i], demand[j])

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x = model.addVars(
        origins, destinations,
        lb=0.0,
        name="x"
    )

    # Apply upper bounds
    for i in origins:
        for j in destinations:
            x[i, j].ub = ub[(i, j)]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in origins for j in destinations),
        GRB.MINIMIZE
    )

    # Supply constraints: all supply must be used
    for i in origins:
        model.addConstr(
            gp.quicksum(x[i, j] for j in destinations) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints: all demand must be met
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