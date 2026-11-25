import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_aircraft = 5
    num_routes = 7
    aircraft_types = range(num_aircraft)
    routes = range(num_routes)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_aircraft, num_routes, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in aircraft_types for j in routes),
        GRB.MINIMIZE
    )

    for i in aircraft_types:
        model.addConstr(
            gp.quicksum(x[i, j] for j in routes) <= availability[i],
            name=f"avail_{i}"
        )

    for j in routes:
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i, j] for i in aircraft_types) >= demand[j],
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