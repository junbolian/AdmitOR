import gurobipy as gp
from gurobipy import GRB

def solve(params):
    plane0_capacity = params["plane0_capacity"]
    plane1_capacity = params["plane1_capacity"]
    plane0_cost = params["plane0_cost"]
    plane1_cost = params["plane1_cost"]
    initial_planes_per_type = params["initial_planes_per_type"]
    demand_period1 = params["demand_period1"]
    max_trips_plane0 = params["max_trips_plane0"]
    max_trips_plane1 = params["max_trips_plane1"]

    # Locations: 0 and 1
    # Plane types: 0 and 1
    # Period: 1 (single period)
    # Route: only Location 1 -> Location 0 is allowed (no trips from 0 -> 1)

    model = gp.Model("fleet_management")
    model.setParam("OutputFlag", 0)

    # Decision variables:
    # trips[p] = number of trips plane type p makes from Location 1 to Location 0
    trips0 = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_trips_plane0, name="trips0")
    trips1 = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_trips_plane1, name="trips1")

    # idle[p][loc] = number of idle planes of type p at location loc at start of period
    idle0_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle0_loc0")
    idle0_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle0_loc1")
    idle1_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle1_loc0")
    idle1_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle1_loc1")

    # idle_end[p][loc] = number of idle planes of type p at location loc at end of period
    idle0_loc0_end = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle0_loc0_end")
    idle0_loc1_end = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle0_loc1_end")
    idle1_loc0_end = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle1_loc0_end")
    idle1_loc1_end = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle1_loc1_end")

    # Total idle planes per type cannot exceed initial_planes_per_type
    model.addConstr(idle0_loc0 + idle0_loc1 <= initial_planes_per_type, name="total_idle0_start")
    model.addConstr(idle1_loc0 + idle1_loc1 <= initial_planes_per_type, name="total_idle1_start")

    # Trips require planes available at Location 1
    model.addConstr(trips0 <= idle0_loc1, name="avail0_loc1")
    model.addConstr(trips1 <= idle1_loc1, name="avail1_loc1")

    # Flow balance for plane type 0:
    # At Location 0 end: start idle + arrivals from loc1 (trips) - departures to loc1 (0, no route)
    model.addConstr(idle0_loc0_end == idle0_loc0 + trips0, name="flow0_loc0")
    # At Location 1 end: start idle - trips to loc0 + arrivals from loc0 (0, no route)
    model.addConstr(idle0_loc1_end == idle0_loc1 - trips0, name="flow0_loc1")

    # Flow balance for plane type 1:
    model.addConstr(idle1_loc0_end == idle1_loc0 + trips1, name="flow1_loc0")
    model.addConstr(idle1_loc1_end == idle1_loc1 - trips1, name="flow1_loc1")

    # Total idle planes per type at end cannot exceed initial_planes_per_type
    model.addConstr(idle0_loc0_end + idle0_loc1_end <= initial_planes_per_type, name="total_idle0_end")
    model.addConstr(idle1_loc0_end + idle1_loc1_end <= initial_planes_per_type, name="total_idle1_end")

    # Demand satisfaction: total passengers carried >= demand
    model.addConstr(
        trips0 * plane0_capacity + trips1 * plane1_capacity >= demand_period1,
        name="demand"
    )

    # Objective: minimize total cost
    model.setObjective(
        trips0 * plane0_cost + trips1 * plane1_cost,
        GRB.MINIMIZE
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.status}"}