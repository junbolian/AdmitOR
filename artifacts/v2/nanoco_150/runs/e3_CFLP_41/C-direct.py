import gurobipy as gp
from gurobipy import GRB


def solve(params):
    station_x = params["station_x"]
    station_y = params["station_y"]
    vehicle_x = params["vehicle_x"]
    vehicle_y = params["vehicle_y"]
    installation_cost = params["installation_cost"]
    station_capacity = params["station_capacity"]
    vehicle_demand = params["vehicle_demand"]
    access_cost = params["access_cost"]
    num_stations = params["num_stations"]
    num_vehicles = params["num_vehicles"]

    S = range(num_stations)
    V = range(num_vehicles)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: build station j
    build = model.addVars(S, vtype=GRB.BINARY, name="build")

    # Binary: assign vehicle i to station j
    assign = model.addVars(V, S, vtype=GRB.BINARY, name="assign")

    # Objective: installation costs + access costs
    model.setObjective(
        gp.quicksum(installation_cost[j] * build[j] for j in S)
        + gp.quicksum(access_cost[i][j] * assign[i, j] for i in V for j in S),
        GRB.MINIMIZE,
    )

    # Each vehicle assigned to exactly one station
    for i in V:
        model.addConstr(
            gp.quicksum(assign[i, j] for j in S) == 1,
            name=f"single_source_{i}",
        )

    # Capacity: total demand at station j <= capacity[j]
    for j in S:
        model.addConstr(
            gp.quicksum(vehicle_demand[i] * assign[i, j] for i in V)
            <= station_capacity[j] * build[j],
            name=f"capacity_{j}",
        )

    # Can only assign to a built station
    for i in V:
        for j in S:
            model.addConstr(
                assign[i, j] <= build[j],
                name=f"link_{i}_{j}",
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