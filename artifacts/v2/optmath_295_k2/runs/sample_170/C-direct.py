import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    num_aircraft = 5
    num_routes = 6
    aircraft_types = range(num_aircraft)
    routes = range(num_routes)

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of aircraft type i assigned to route j
    x = model.addVars(num_aircraft, num_routes, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in aircraft_types for j in routes),
        GRB.MINIMIZE
    )

    # Availability constraints: total aircraft of type i across all routes <= availability[i]
    for i in aircraft_types:
        model.addConstr(
            gp.quicksum(x[i, j] for j in routes) <= availability[i],
            name=f"avail_{i}"
        )

    # Demand constraints: combined capacity on route j >= demand[j]
    for j in routes:
        model.addConstr(
            gp.quicksum(capability[i][j] * x[i, j] for i in aircraft_types) >= demand[j],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}