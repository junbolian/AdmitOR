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
    # Route: only Location 1 -> Location 0 is allowed (inter-location)
    # Variables: trips[p] = number of trips plane type p makes from loc1 to loc0

    model = gp.Model("plane_fleet")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of trips each plane type makes from loc1 to loc0
    trips0 = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_trips_plane0, name="trips0")
    trips1 = model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_trips_plane1, name="trips1")

    # Idle plane variables at each location, for each plane type, before and after period
    # idle_start[t][l]: idle planes of type t at location l at start of period
    # idle_end[t][l]: idle planes of type t at location l at end of period
    idle_start_0_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_start_0_loc0")
    idle_start_0_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_start_0_loc1")
    idle_start_1_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_start_1_loc0")
    idle_start_1_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_start_1_loc1")

    idle_end_0_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_end_0_loc0")
    idle_end_0_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_end_0_loc1")
    idle_end_1_loc0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_end_1_loc0")
    idle_end_1_loc1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="idle_end_1_loc1")

    # Total idle planes per type cannot exceed initial_planes_per_type
    model.addConstr(idle_start_0_loc0 + idle_start_0_loc1 <= initial_planes_per_type, "total_idle_start_type0")
    model.addConstr(idle_start_1_loc0 + idle_start_1_loc1 <= initial_planes_per_type, "total_idle_start_type1")

    # trips0 cannot exceed available planes at loc1 for type 0
    model.addConstr(trips0 <= idle_start_0_loc1, "avail_type0_loc1")
    # trips1 cannot exceed available planes at loc1 for type 1
    model.addConstr(trips1 <= idle_start_1_loc1, "avail_type1_loc1")

    # Flow balance for plane type 0:
    # loc0: idle_end = idle_start + arrivals from loc1 (trips0) - departures to loc1 (0, route not allowed)
    model.addConstr(idle_end_0_loc0 == idle_start_0_loc0 + trips0, "flow_type0_loc0")
    # loc1: idle_end = idle_start - trips0 (departed to loc0) + 0 (no arrivals from loc0)
    model.addConstr(idle_end_0_loc1 == idle_start_0_loc1 - trips0, "flow_type0_loc1")

    # Flow balance for plane type 1:
    model.addConstr(idle_end_1_loc0 == idle_start_1_loc0 + trips1, "flow_type1_loc0")
    model.addConstr(idle_end_1_loc1 == idle_start_1_loc1 - trips1, "flow_type1_loc1")

    # Demand satisfaction: total passengers >= demand_period1
    model.addConstr(
        trips0 * plane0_capacity + trips1 * plane1_capacity >= demand_period1,
        "demand"
    )

    # Objective: minimize total cost
    model.setObjective(trips0 * plane0_cost + trips1 * plane1_cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}