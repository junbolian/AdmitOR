import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    pollution_cap = params["pollution_cap"]
    min_truck_trips = params["min_truck_trips"]
    capacity_truck = params["capacity_truck"]
    capacity_van = params["capacity_van"]
    capacity_motorcycle = params["capacity_motorcycle"]
    capacity_ev = params["capacity_ev"]
    pollution_truck = params["pollution_truck"]
    pollution_van = params["pollution_van"]
    pollution_motorcycle = params["pollution_motorcycle"]
    pollution_ev = params["pollution_ev"]

    model = gp.Model("transport_pollution")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of trips for each vehicle type
    x_truck = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_truck")
    x_van = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_van")
    x_motorcycle = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_motorcycle")
    x_ev = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_ev")

    # Binary variables to select at most one of van or EV
    y_van = model.addVar(vtype=GRB.BINARY, name="y_van")
    y_ev = model.addVar(vtype=GRB.BINARY, name="y_ev")

    # Objective: minimize total pollution
    model.setObjective(
        pollution_truck * x_truck + pollution_van * x_van +
        pollution_motorcycle * x_motorcycle + pollution_ev * x_ev,
        GRB.MINIMIZE
    )

    # Demand constraint: total product transported >= demand
    model.addConstr(
        capacity_truck * x_truck + capacity_van * x_van +
        capacity_motorcycle * x_motorcycle + capacity_ev * x_ev >= demand,
        name="demand_constraint"
    )

    # Pollution cap constraint
    model.addConstr(
        pollution_truck * x_truck + pollution_van * x_van +
        pollution_motorcycle * x_motorcycle + pollution_ev * x_ev <= pollution_cap,
        name="pollution_cap_constraint"
    )

    # Minimum truck trips constraint
    model.addConstr(x_truck >= min_truck_trips, name="min_truck_trips_constraint")

    # Only one of van or EV can be used (choose at most one)
    model.addConstr(y_van + y_ev <= 1, name="van_or_ev_choice")

    # Big-M constraints to link binary selection to trip counts
    # Use a reasonable big-M based on demand / min capacity
    big_m = demand  # upper bound on trips (conservative)

    model.addConstr(x_van <= big_m * y_van, name="van_trips_bounded_by_selection")
    model.addConstr(x_ev <= big_m * y_ev, name="ev_trips_bounded_by_selection")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}