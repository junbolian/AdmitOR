import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]  # list of length 5
    demand = params["demand"]              # list of length 6
    capacity = params["capacity"]          # 5x6 list of lists
    cost = params["cost"]                  # 5x6 list of lists

    num_aircraft = 5
    num_routes = 6
    aircraft_range = range(num_aircraft)
    route_range = range(num_routes)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = [[
        model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
        for j in route_range
    ] for i in aircraft_range]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j] for i in aircraft_range for j in route_range),
        GRB.MINIMIZE
    )

    # Availability constraints: total aircraft of type i across all routes <= availability[i]
    for i in aircraft_range:
        model.addConstr(
            gp.quicksum(x[i][j] for j in route_range) <= availability[i],
            name=f"avail_{i}"
        )

    # Demand constraints: total capacity on route j >= demand[j]
    for j in route_range:
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i][j] for i in aircraft_range) >= demand[j],
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