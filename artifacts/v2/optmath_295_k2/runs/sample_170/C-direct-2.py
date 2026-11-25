import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    num_aircraft = 5
    num_routes = 6
    aircraft_range = range(num_aircraft)
    route_range = range(num_routes)

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_aircraft, num_routes, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in aircraft_range for j in route_range),
        GRB.MINIMIZE
    )

    for i in aircraft_range:
        model.addConstr(
            gp.quicksum(x[i, j] for j in route_range) <= availability[i],
            name=f"avail_{i}"
        )

    for j in route_range:
        model.addConstr(
            gp.quicksum(capability[i][j] * x[i, j] for i in aircraft_range) >= demand[j],
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