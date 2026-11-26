import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    pollution_budget = params["pollution_budget"]
    pollution_per_horse_trip = params["pollution_per_horse_trip"]
    pollution_per_bicycle_trip = params["pollution_per_bicycle_trip"]
    pollution_per_handcart_trip = params["pollution_per_handcart_trip"]
    min_horse_trips = params["min_horse_trips"]
    capacity_horse = params["capacity_horse"]
    capacity_bicycle = params["capacity_bicycle"]
    capacity_handcart = params["capacity_handcart"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    horse = model.addVar(vtype=GRB.INTEGER, lb=0, name="horse")
    bicycle = model.addVar(vtype=GRB.INTEGER, lb=0, name="bicycle")
    handcart = model.addVar(vtype=GRB.INTEGER, lb=0, name="handcart")
    # Binary variable: use_bicycle=1 means bicycles chosen, use_bicycle=0 means hand carts chosen
    use_bicycle = model.addVar(vtype=GRB.BINARY, name="use_bicycle")

    # Objective: minimize total trips (or any reasonable objective; problem doesn't specify one explicitly)
    # Minimizing total trips is a natural objective
    model.setObjective(horse + bicycle + handcart, GRB.MINIMIZE)

    # Demand constraint
    model.addConstr(
        capacity_horse * horse + capacity_bicycle * bicycle + capacity_handcart * handcart >= demand,
        name="demand"
    )

    # Pollution constraint
    model.addConstr(
        pollution_per_horse_trip * horse + pollution_per_bicycle_trip * bicycle + pollution_per_handcart_trip * handcart <= pollution_budget,
        name="pollution"
    )

    # Minimum horse trips
    model.addConstr(horse >= min_horse_trips, name="min_horse")

    # Mutual exclusivity: only one of bicycle or handcart can be used
    # Big-M approach: if use_bicycle=1, bicycle can be nonzero; if use_bicycle=0, bicycle=0
    # Similarly, if use_bicycle=0, handcart can be nonzero; if use_bicycle=1, handcart=0
    big_m = demand  # upper bound on trips for either mode
    model.addConstr(bicycle <= big_m * use_bicycle, name="bicycle_choice")
    model.addConstr(handcart <= big_m * (1 - use_bicycle), name="handcart_choice")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}