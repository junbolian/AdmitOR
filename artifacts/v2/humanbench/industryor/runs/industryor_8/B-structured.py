# IR: {"sets":{"modes":["motorcycle","small_truck","large_truck"]},"params":["motorcycle_pollution","small_truck_pollution","large_truck_pollution","motorcycle_product","small_truck_product","large_truck_product","motorcycle_max_trips","product_demand","max_total_trips"],"variables":{"trips[mode]":"NonNegativeIntegers","selected[mode]":"Binary"},"constraints":["sum(selected[mode] for mode in modes) == 2","trips[mode] >= selected[mode] for mode in modes","trips[mode] <= max_total_trips * selected[mode] for mode in modes","trips[motorcycle] <= motorcycle_max_trips","sum(product[mode] * trips[mode] for mode in modes) >= product_demand","sum(trips[mode] for mode in modes) <= max_total_trips"],"objective":"minimize sum(pollution[mode] * trips[mode] for mode in modes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pollution = {
        "motorcycle": params["motorcycle_pollution"],
        "small_truck": params["small_truck_pollution"],
        "large_truck": params["large_truck_pollution"],
    }
    product = {
        "motorcycle": params["motorcycle_product"],
        "small_truck": params["small_truck_product"],
        "large_truck": params["large_truck_product"],
    }
    motorcycle_max_trips = params["motorcycle_max_trips"]
    product_demand = params["product_demand"]
    max_total_trips = params["max_total_trips"]

    model = pyo.ConcreteModel()
    model.modes = pyo.Set(
        initialize=["motorcycle", "small_truck", "large_truck"],
        ordered=True,
    )

    model.trips = pyo.Var(model.modes, domain=pyo.NonNegativeIntegers)
    model.selected = pyo.Var(model.modes, domain=pyo.Binary)

    # Exactly two modes must each perform at least one trip.
    model.two_modes = pyo.Constraint(
        expr=sum(model.selected[mode] for mode in model.modes) == 2
    )
    model.selection_lower_link = pyo.Constraint(
        model.modes,
        rule=lambda mdl, mode: mdl.trips[mode] >= mdl.selected[mode],
    )
    model.selection_upper_link = pyo.Constraint(
        model.modes,
        rule=lambda mdl, mode: (
            mdl.trips[mode] <= max_total_trips * mdl.selected[mode]
        ),
    )

    model.motorcycle_trip_limit = pyo.Constraint(
        expr=model.trips["motorcycle"] <= motorcycle_max_trips
    )
    model.product_requirement = pyo.Constraint(
        expr=sum(
            product[mode] * model.trips[mode] for mode in model.modes
        ) >= product_demand
    )
    model.total_trip_limit = pyo.Constraint(
        expr=sum(model.trips[mode] for mode in model.modes) <= max_total_trips
    )

    model.total_pollution = pyo.Objective(
        expr=sum(
            pollution[mode] * model.trips[mode] for mode in model.modes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this expected error when no solution can be loaded.
        message = str(exc).lower()
        if (
            "a feasible solution was not found" in message
            and "no solution can be loaded" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_pollution))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}