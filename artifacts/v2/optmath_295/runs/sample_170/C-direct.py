import gurobipy as gp
from gurobipy import GRB

def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capacity_coeff = params["capacity_coeff"]
    operational_cost = params["operational_cost"]

    num_aircraft = 5
    num_routes = 6
    aircraft_types = range(num_aircraft)
    routes = range(num_routes)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = [[model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
          for j in routes]
         for i in aircraft_types]

    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(operational_cost[i][j] * x[i][j]
                    for i in aircraft_types for j in routes),
        GRB.MINIMIZE
    )

    # Availability constraints: total aircraft of type i across all routes <= availability[i]
    for i in aircraft_types:
        model.addConstr(
            gp.quicksum(x[i][j] for j in routes) <= aircraft_availability[i],
            name=f"avail_{i}"
        )

    # Demand constraints: total capacity on route j >= demand[j]
    for j in routes:
        model.addConstr(
            gp.quicksum(capacity_coeff[i][j] * x[i][j] for i in aircraft_types) >= route_demand[j],
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