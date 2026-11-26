import gurobipy as gp
from gurobipy import GRB

def solve(params):
    truck_capacity = params["truck_capacity"]
    van_capacity = params["van_capacity"]
    motorcycle_capacity = params["motorcycle_capacity"]
    ev_capacity = params["ev_capacity"]
    truck_pollution = params["truck_pollution"]
    van_pollution = params["van_pollution"]
    motorcycle_pollution = params["motorcycle_pollution"]
    ev_pollution = params["ev_pollution"]
    pollution_budget = params["pollution_budget"]
    truck_min_trips = params["truck_min_trips"]
    demand_required = params["demand_required"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: number of trips for each vehicle type
    x_truck = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_truck")
    x_van = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_van")
    x_moto = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_moto")
    x_ev = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_ev")

    # Binary variable: y=0 means use vans only, y=1 means use EVs only
    # We model the exclusive choice: exactly one of van or EV is allowed
    y_van = model.addVar(vtype=GRB.BINARY, name="y_van")
    y_ev = model.addVar(vtype=GRB.BINARY, name="y_ev")

    # Exactly one of van or EV must be chosen
    model.addConstr(y_van + y_ev == 1, name="choose_one")

    # Big-M to enforce: if y_van=0 then x_van=0, if y_ev=0 then x_ev=0
    big_m = 100000
    model.addConstr(x_van <= big_m * y_van, name="van_active")
    model.addConstr(x_ev <= big_m * y_ev, name="ev_active")

    # Minimum truck trips
    model.addConstr(x_truck >= truck_min_trips, name="truck_min")

    # Pollution constraint
    model.addConstr(
        truck_pollution * x_truck
        + van_pollution * x_van
        + motorcycle_pollution * x_moto
        + ev_pollution * x_ev
        <= pollution_budget,
        name="pollution"
    )

    # Demand constraint
    model.addConstr(
        truck_capacity * x_truck
        + van_capacity * x_van
        + motorcycle_capacity * x_moto
        + ev_capacity * x_ev
        >= demand_required,
        name="demand"
    )

    # Objective: minimize total pollution
    model.setObjective(
        truck_pollution * x_truck
        + van_pollution * x_van
        + motorcycle_pollution * x_moto
        + ev_pollution * x_ev,
        GRB.MINIMIZE
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