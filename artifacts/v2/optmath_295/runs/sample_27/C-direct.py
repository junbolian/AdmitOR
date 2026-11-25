import gurobipy as gp
from gurobipy import GRB

def solve(params):
    plane0_capacity = params["plane0_capacity"]
    plane0_trip_cost = params["plane0_trip_cost"]
    plane0_same_loc_cost = params["plane0_same_loc_cost"]
    plane1_capacity = params["plane1_capacity"]
    plane1_trip_cost = params["plane1_trip_cost"]
    plane1_same_loc_cost = params["plane1_same_loc_cost"]
    initial_idle_plane0 = params["initial_idle_plane0"]
    initial_idle_plane1 = params["initial_idle_plane1"]
    max_idle_plane0 = params["max_idle_plane0"]
    max_idle_plane1 = params["max_idle_plane1"]
    demand_1_to_0 = params["demand_1_to_0"]
    max_trips_plane0_1to0 = params["max_trips_plane0_1to0"]
    max_trips_plane1_1to0 = params["max_trips_plane1_1to0"]

    model = gp.Model("fleet_management")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of trips each plane type makes on each route
    # Routes: (from_loc, to_loc) in {(0,0), (0,1), (1,0), (1,1)}
    # Problem states planes cannot be used for trips from Location 0 to Location 1,
    # so trips_p0_0to1 = trips_p1_0to1 = 0 (we simply won't create those variables
    # or fix them to 0).

    # trips from loc 0 to loc 0 (same location, zero cost)
    t0_00 = model.addVar(vtype=GRB.INTEGER, lb=0, name="t0_00")
    # trips from loc 1 to loc 0
    t0_10 = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_trips_plane0_1to0, name="t0_10")
    # trips from loc 1 to loc 1 (same location, zero cost)
    t0_11 = model.addVar(vtype=GRB.INTEGER, lb=0, name="t0_11")

    t1_00 = model.addVar(vtype=GRB.INTEGER, lb=0, name="t1_00")
    t1_10 = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_trips_plane1_1to0, name="t1_10")
    t1_11 = model.addVar(vtype=GRB.INTEGER, lb=0, name="t1_11")

    # Idle planes at each location at end of period
    # idle0_loc[l] = idle planes of type 0 at location l after period
    idle0_0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle0_0")
    idle0_1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle0_1")
    idle1_0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle1_0")
    idle1_1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle1_1")

    # Initial idle distribution variables (must sum to total initial idle)
    init0_0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="init0_0")
    init0_1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="init0_1")
    init1_0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="init1_0")
    init1_1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="init1_1")

    # Initial distribution sums
    model.addConstr(init0_0 + init0_1 == initial_idle_plane0, name="init0_sum")
    model.addConstr(init1_0 + init1_1 == initial_idle_plane1, name="init1_sum")

    # Flow balance for plane type 0:
    # idle_end[l] = idle_start[l] + arrivals_at_l - departures_from_l
    # Trips from loc 0: t0_00 (stays at 0), no t0_01
    # Trips from loc 1: t0_10 (goes to 0), t0_11 (stays at 1)
    # At location 0: arrives t0_00 + t0_10, departs t0_00 (same loc counts as depart+arrive)
    # For same-location trips, the plane departs and arrives at the same location,
    # so net flow is zero. Only cross-location trips change location inventory.
    # Flow balance at loc 0 for plane 0:
    #   idle0_0 = init0_0 - (trips departing loc0 going elsewhere) + (trips arriving at loc0 from elsewhere)
    #   No trips from 0->1 allowed, so departures from loc0 to other locations = 0
    #   Arrivals at loc0 from loc1 = t0_10
    model.addConstr(idle0_0 == init0_0 + t0_10, name="flow0_loc0")
    # Flow balance at loc 1 for plane 0:
    #   departures from loc1 to loc0 = t0_10, arrivals at loc1 from elsewhere = 0
    model.addConstr(idle0_1 == init0_1 - t0_10, name="flow0_loc1")

    # Flow balance for plane type 1:
    model.addConstr(idle1_0 == init1_0 + t1_10, name="flow1_loc0")
    model.addConstr(idle1_1 == init1_1 - t1_10, name="flow1_loc1")

    # Maximum total idle planes constraint
    model.addConstr(idle0_0 + idle0_1 <= max_idle_plane0, name="max_idle0")
    model.addConstr(idle1_0 + idle1_1 <= max_idle_plane1, name="max_idle1")

    # Demand satisfaction: passengers carried from loc 1 to loc 0 >= demand
    model.addConstr(
        t0_10 * plane0_capacity + t1_10 * plane1_capacity >= demand_1_to_0,
        name="demand_1to0"
    )

    # Objective: minimize total trip costs
    # Same-location trips use same_loc_cost, cross-location trips use trip_cost
    obj = (
        plane0_same_loc_cost * t0_00 +
        plane0_trip_cost * t0_10 +
        plane0_same_loc_cost * t0_11 +
        plane1_same_loc_cost * t1_00 +
        plane1_trip_cost * t1_10 +
        plane1_same_loc_cost * t1_11
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}