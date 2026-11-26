import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    p_poll_car = params["pollution_per_car_trip"]
    p_poll_truck = params["pollution_per_truck_trip"]
    p_poll_bus = params["pollution_per_bus_trip"]
    cap_car = params["capacity_per_car_trip"]
    cap_truck = params["capacity_per_truck_trip"]
    cap_bus = params["capacity_per_bus_trip"]
    min_products = params["min_products_required"]
    max_truck = params["max_truck_trips"]
    bus_frac = params["bus_fraction_limit"]
    max_total = params["max_total_trips"]
    max_modes = params["max_modes_selected"]

    modes = ["car", "truck", "bus"]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(modes, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(modes, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=model.x["car"] * p_poll_car
        + model.x["truck"] * p_poll_truck
        + model.x["bus"] * p_poll_bus,
        sense=pyo.minimize,
    )

    model.capacity = pyo.Constraint(
        expr=model.x["car"] * cap_car
        + model.x["truck"] * cap_truck
        + model.x["bus"] * cap_bus
        >= min_products
    )

    model.truck_limit = pyo.Constraint(expr=model.x["truck"] <= max_truck)

    model.bus_fraction = pyo.Constraint(
        expr=model.x["bus"]
        <= bus_frac * (model.x["car"] + model.x["truck"] + model.x["bus"])
    )

    model.total_limit = pyo.Constraint(
        expr=model.x["car"] + model.x["truck"] + model.x["bus"] <= max_total
    )

    model.total_lower = pyo.Constraint(
        expr=model.x["car"] + model.x["truck"] + model.x["bus"] >= 1
    )

    model.modes_limit = pyo.Constraint(
        expr=model.y["car"] + model.y["truck"] + model.y["bus"] <= max_modes
    )

    big_m = max_total if max_total >= 1 else 1

    def link_rule(m, mode):
        return m.x[mode] <= big_m * m.y[mode]

    model.link = pyo.Constraint(modes, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}