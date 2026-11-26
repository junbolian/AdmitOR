import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pollution_per_car_trip = params["pollution_per_car_trip"]
    pollution_per_truck_trip = params["pollution_per_truck_trip"]
    pollution_per_bus_trip = params["pollution_per_bus_trip"]
    capacity_per_car_trip = params["capacity_per_car_trip"]
    capacity_per_truck_trip = params["capacity_per_truck_trip"]
    capacity_per_bus_trip = params["capacity_per_bus_trip"]
    min_products_required = params["min_products_required"]
    max_truck_trips = params["max_truck_trips"]
    bus_fraction_limit = params["bus_fraction_limit"]
    max_total_trips = params["max_total_trips"]
    max_modes_selected = params["max_modes_selected"]

    model = gp.Model("transport_pollution")
    model.setParam("OutputFlag", 0)

    # Integer trip variables
    x_car = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_car")
    x_truck = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_truck")
    x_bus = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_bus")

    # Binary variables: 1 if mode is selected
    y_car = model.addVar(vtype=GRB.BINARY, name="y_car")
    y_truck = model.addVar(vtype=GRB.BINARY, name="y_truck")
    y_bus = model.addVar(vtype=GRB.BINARY, name="y_bus")

    # Objective: minimize total pollution
    model.setObjective(
        pollution_per_car_trip * x_car +
        pollution_per_truck_trip * x_truck +
        pollution_per_bus_trip * x_bus,
        GRB.MINIMIZE
    )

    # At most max_modes_selected modes can be used
    model.addConstr(y_car + y_truck + y_bus <= max_modes_selected, name="max_modes")

    # Big-M linking: trips only allowed if mode is selected
    # Safe upper bound: a single mode could use all max_total_trips trips
    M = max_total_trips
    model.addConstr(x_car <= M * y_car, name="link_car")
    model.addConstr(x_truck <= M * y_truck, name="link_truck")
    model.addConstr(x_bus <= M * y_bus, name="link_bus")

    # Minimum products transported
    model.addConstr(
        capacity_per_car_trip * x_car +
        capacity_per_truck_trip * x_truck +
        capacity_per_bus_trip * x_bus >= min_products_required,
        name="min_products"
    )

    # Max truck trips
    model.addConstr(x_truck <= max_truck_trips, name="max_trucks")

    # Bus trips <= bus_fraction_limit * total trips
    # Rearranged to avoid nonlinearity: x_bus <= bus_fraction_limit * (x_car + x_truck + x_bus)
    # => x_bus * (1 - bus_fraction_limit) <= bus_fraction_limit * (x_car + x_truck)
    model.addConstr(
        x_bus * (1.0 - bus_fraction_limit) <= bus_fraction_limit * (x_car + x_truck),
        name="bus_fraction"
    )

    # Max total trips
    model.addConstr(x_car + x_truck + x_bus <= max_total_trips, name="max_total_trips")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}