# IR: {"sets":{"modes":["car","truck","bus"]},"params":["pollution_per_car_trip","pollution_per_truck_trip","pollution_per_bus_trip","capacity_per_car_trip","capacity_per_truck_trip","capacity_per_bus_trip","min_products_required","max_truck_trips","bus_fraction_limit","max_total_trips","max_modes_selected"],"variables":{"trips[mode]":"nonnegative integer","selected[mode]":"binary"},"constraints":["sum(capacity[mode]*trips[mode]) >= min_products_required","trips[truck] <= max_truck_trips","trips[bus] <= bus_fraction_limit*sum(trips[mode])","sum(trips[mode]) <= max_total_trips","sum(selected[mode]) <= max_modes_selected","trips[mode] <= max_total_trips*selected[mode] for each mode","trips[mode] >= selected[mode] for each mode"],"objective":"minimize sum(pollution[mode]*trips[mode])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The stated instance is infeasible. A faithful implementation must
    # report failure for those inputs; changing the constraints would
    # change the problem.

    pollution = {
        "car": params["pollution_per_car_trip"],
        "truck": params["pollution_per_truck_trip"],
        "bus": params["pollution_per_bus_trip"],
    }
    capacity = {
        "car": params["capacity_per_car_trip"],
        "truck": params["capacity_per_truck_trip"],
        "bus": params["capacity_per_bus_trip"],
    }
    min_products_required = params["min_products_required"]
    max_truck_trips = params["max_truck_trips"]
    bus_fraction_limit = params["bus_fraction_limit"]
    max_total_trips = params["max_total_trips"]
    max_modes_selected = params["max_modes_selected"]

    model = pyo.ConcreteModel()
    model.modes = pyo.Set(initialize=("car", "truck", "bus"), ordered=True)

    model.trips = pyo.Var(model.modes, domain=pyo.NonNegativeIntegers)
    model.selected = pyo.Var(model.modes, domain=pyo.Binary)

    model.product_requirement = pyo.Constraint(
        expr=sum(
            capacity[mode] * model.trips[mode] for mode in model.modes
        ) >= min_products_required
    )

    model.truck_limit = pyo.Constraint(
        expr=model.trips["truck"] <= max_truck_trips
    )

    model.bus_share_limit = pyo.Constraint(
        expr=model.trips["bus"]
        <= bus_fraction_limit * sum(
            model.trips[mode] for mode in model.modes
        )
    )

    model.total_trip_limit = pyo.Constraint(
        expr=sum(model.trips[mode] for mode in model.modes)
        <= max_total_trips
    )

    model.mode_count_limit = pyo.Constraint(
        expr=sum(model.selected[mode] for mode in model.modes)
        <= max_modes_selected
    )

    model.trip_activation = pyo.Constraint(
        model.modes,
        rule=lambda mdl, mode: (
            mdl.trips[mode] <= max_total_trips * mdl.selected[mode]
        ),
    )

    model.selected_mode_usage = pyo.Constraint(
        model.modes,
        rule=lambda mdl, mode: (
            mdl.trips[mode] >= mdl.selected[mode]
        ),
    )

    model.total_pollution = pyo.Objective(
        expr=sum(
            pollution[mode] * model.trips[mode] for mode in model.modes
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        failure_reason = "no_feasible_solution"

    # Success depends exclusively on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_pollution))
    except ValueError:
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}