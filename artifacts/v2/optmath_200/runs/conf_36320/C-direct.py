import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_plane0 = params["cost_plane0"]
    cost_plane1 = params["cost_plane1"]
    demand_0to1 = params["demand_0to1"]
    capacity_plane0 = params["capacity_plane0"]
    capacity_plane1 = params["capacity_plane1"]
    fleet_plane0 = params["fleet_plane0"]
    fleet_plane1 = params["fleet_plane1"]
    max_trips_plane0 = params["max_trips_plane0"]
    max_trips_plane1 = params["max_trips_plane1"]

    model = gp.Model("airline_dispatch")
    model.setParam("OutputFlag", 0)

    # Decision variables:
    # trips_p0_01: number of trips Plane 0 makes from Location 0 to Location 1
    # trips_p1_01: number of trips Plane 1 makes from Location 0 to Location 1
    # idle_p0_loc0: Plane 0 aircraft idle at Location 0
    # idle_p0_loc1: Plane 0 aircraft idle at Location 1
    # idle_p1_loc0: Plane 1 aircraft idle at Location 0
    # idle_p1_loc1: Plane 1 aircraft idle at Location 1

    trips_p0_01 = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_trips_plane0, name="trips_p0_01")
    trips_p1_01 = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_trips_plane1, name="trips_p1_01")

    idle_p0_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p0_loc0")
    idle_p0_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p0_loc1")
    idle_p1_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p1_loc0")
    idle_p1_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_p1_loc1")

    # Objective: minimize total operating cost
    model.setObjective(
        cost_plane0 * trips_p0_01 + cost_plane1 * trips_p1_01,
        GRB.MINIMIZE
    )

    # Demand constraint: total capacity must meet or exceed demand
    model.addConstr(
        capacity_plane0 * trips_p0_01 + capacity_plane1 * trips_p1_01 >= demand_0to1,
        name="demand_constraint"
    )

    # Fleet balance for Plane 0:
    # Total idle at both locations cannot exceed fleet size
    model.addConstr(
        idle_p0_loc0 + idle_p0_loc1 <= fleet_plane0,
        name="fleet_balance_p0"
    )

    # Fleet balance for Plane 1:
    model.addConstr(
        idle_p1_loc0 + idle_p1_loc1 <= fleet_plane1,
        name="fleet_balance_p1"
    )

    # Planes dispatched from Location 0 come from those initially at Location 0:
    # idle at loc0 = initially available at loc0 minus dispatched
    # Since planes only go 0->1 (no 1->0 trips), planes initially at loc0
    # either fly to loc1 or remain idle at loc0.
    # trips_p0_01 <= idle_p0_loc0 + trips_p0_01 is always true; we need:
    # trips dispatched + remaining idle = initial at loc0
    # But we don't have a separate "initial at loc0" variable.
    # The problem states: planes initially idle at each location = planes remaining idle + planes dispatched.
    # We interpret: for each plane type, the total planes used (dispatched + idle) <= fleet.
    # Dispatched planes come from loc0, so:
    model.addConstr(
        trips_p0_01 + idle_p0_loc0 <= fleet_plane0,
        name="p0_loc0_balance"
    )
    model.addConstr(
        trips_p1_01 + idle_p1_loc0 <= fleet_plane1,
        name="p1_loc0_balance"
    )

    # Idle at loc1: planes at loc1 are only idle (no trips from loc1 to loc0)
    model.addConstr(idle_p0_loc1 >= 0, name="p0_loc1_nonneg")
    model.addConstr(idle_p1_loc1 >= 0, name="p1_loc1_nonneg")

    # Total aircraft across both locations cannot exceed fleet
    model.addConstr(
        trips_p0_01 + idle_p0_loc0 + idle_p0_loc1 <= fleet_plane0,
        name="p0_total_fleet"
    )
    model.addConstr(
        trips_p1_01 + idle_p1_loc0 + idle_p1_loc1 <= fleet_plane1,
        name="p1_total_fleet"
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