import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pollution_motorcycle = params["pollution_motorcycle"]
    pollution_small_truck = params["pollution_small_truck"]
    pollution_large_truck = params["pollution_large_truck"]
    motorcycle_trip_cap = params["motorcycle_trip_cap"]
    capacity_motorcycle = params["capacity_motorcycle"]
    capacity_small_truck = params["capacity_small_truck"]
    capacity_large_truck = params["capacity_large_truck"]
    demand = params["demand"]
    total_trip_cap = params["total_trip_cap"]

    model = gp.Model("transport_pollution")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of trips for each vehicle type
    x_m = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_motorcycle")
    x_s = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_small_truck")
    x_l = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_large_truck")

    # Binary variables: 1 if vehicle type is used (chosen)
    y_m = model.addVar(vtype=GRB.BINARY, name="y_motorcycle")
    y_s = model.addVar(vtype=GRB.BINARY, name="y_small_truck")
    y_l = model.addVar(vtype=GRB.BINARY, name="y_large_truck")

    # Objective: minimize total pollution
    model.setObjective(
        pollution_motorcycle * x_m + pollution_small_truck * x_s + pollution_large_truck * x_l,
        GRB.MINIMIZE
    )

    # Exactly 2 out of 3 transportation methods must be chosen
    model.addConstr(y_m + y_s + y_l == 2, name="exactly_two_methods")

    # Big-M linking: trips only allowed if the method is chosen
    # Upper bound for big-M: total_trip_cap is a safe upper bound for any single type
    M = total_trip_cap
    model.addConstr(x_m <= M * y_m, name="link_motorcycle")
    model.addConstr(x_s <= M * y_s, name="link_small_truck")
    model.addConstr(x_l <= M * y_l, name="link_large_truck")

    # Motorcycle trip cap
    model.addConstr(x_m <= motorcycle_trip_cap, name="motorcycle_cap")

    # Demand constraint: total products transported >= demand
    model.addConstr(
        capacity_motorcycle * x_m + capacity_small_truck * x_s + capacity_large_truck * x_l >= demand,
        name="demand"
    )

    # Total trips constraint
    model.addConstr(x_m + x_s + x_l <= total_trip_cap, name="total_trips")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}