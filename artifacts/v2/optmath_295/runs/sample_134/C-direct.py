import gurobipy as gp
from gurobipy import GRB

def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capability = params["capability"]
    operational_cost = params["operational_cost"]

    num_aircraft = len(aircraft_availability)
    num_routes = len(route_demand)

    aircraft_types = list(range(num_aircraft))
    routes = list(range(num_routes))

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of aircraft type i assigned to route j
    x = model.addVars(aircraft_types, routes, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(operational_cost[i][j] * x[i, j] for i in aircraft_types for j in routes),
        GRB.MINIMIZE
    )

    # Availability constraints: total aircraft of type i across all routes <= availability[i]
    for i in aircraft_types:
        model.addConstr(
            gp.quicksum(x[i, j] for j in routes) <= aircraft_availability[i],
            name=f"availability_{i}"
        )

    # Demand constraints: total capability for route j >= demand[j]
    for j in routes:
        model.addConstr(
            gp.quicksum(capability[i][j] * x[i, j] for i in aircraft_types) >= route_demand[j],
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