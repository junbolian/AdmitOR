import gurobipy as gp
from gurobipy import GRB

def solve(params):
    motorcycle_pollution = params["motorcycle_pollution"]
    small_truck_pollution = params["small_truck_pollution"]
    large_truck_pollution = params["large_truck_pollution"]
    motorcycle_product = params["motorcycle_product"]
    small_truck_product = params["small_truck_product"]
    large_truck_product = params["large_truck_product"]
    motorcycle_max_trips = params["motorcycle_max_trips"]
    product_demand = params["product_demand"]
    max_total_trips = params["max_total_trips"]

    model = gp.Model("transport_pollution")
    model.setParam("OutputFlag", 0)

    # Continuous trip variables
    x_m = model.addVar(lb=0, name="x_motorcycle")
    x_s = model.addVar(lb=0, name="x_small_truck")
    x_l = model.addVar(lb=0, name="x_large_truck")

    # Binary variables indicating whether each mode is used
    y_m = model.addVar(vtype=GRB.BINARY, name="y_motorcycle")
    y_s = model.addVar(vtype=GRB.BINARY, name="y_small_truck")
    y_l = model.addVar(vtype=GRB.BINARY, name="y_large_truck")

    # Objective: minimize total pollution
    model.setObjective(
        motorcycle_pollution * x_m + small_truck_pollution * x_s + large_truck_pollution * x_l,
        GRB.MINIMIZE
    )

    # Exactly two modes of transportation chosen
    model.addConstr(y_m + y_s + y_l == 2, name="two_modes")

    # Big-M linking: trips only allowed if mode is selected
    big_M = max_total_trips
    model.addConstr(x_m <= big_M * y_m, name="link_motorcycle")
    model.addConstr(x_s <= big_M * y_s, name="link_small_truck")
    model.addConstr(x_l <= big_M * y_l, name="link_large_truck")

    # Motorcycle trip limit
    model.addConstr(x_m <= motorcycle_max_trips, name="motorcycle_max")

    # Product demand constraint
    model.addConstr(
        motorcycle_product * x_m + small_truck_product * x_s + large_truck_product * x_l >= product_demand,
        name="product_demand"
    )

    # Total trips constraint
    model.addConstr(x_m + x_s + x_l <= max_total_trips, name="max_trips")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}