# IR: {"sets":{"modes":["truck","van","motorcycle","ev"]},"params":["demand","pollution_cap","min_truck_trips","capacity_truck","capacity_van","capacity_motorcycle","capacity_ev","pollution_truck","pollution_van","pollution_motorcycle","pollution_ev"],"derived":{"van_bound":"max(1,ceil(max(0,demand)/capacity_van))","ev_bound":"max(1,ceil(max(0,demand)/capacity_ev))"},"variables":{"trips[mode]":"nonnegative integer","choose_van":"binary; 1 permits vans, 0 permits electric vehicles"},"constraints":["sum(capacity[mode]*trips[mode]) >= demand","sum(pollution[mode]*trips[mode]) <= pollution_cap","trips[truck] >= min_truck_trips","trips[van] <= van_bound*choose_van","trips[ev] <= ev_bound*(1-choose_van)"],"objective":"minimize sum(pollution[mode]*trips[mode])"}
from math import ceil

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    pollution_cap = params["pollution_cap"]
    min_truck_trips = params["min_truck_trips"]

    capacities = {
        "truck": params["capacity_truck"],
        "van": params["capacity_van"],
        "motorcycle": params["capacity_motorcycle"],
        "ev": params["capacity_ev"],
    }
    pollution = {
        "truck": params["pollution_truck"],
        "van": params["pollution_van"],
        "motorcycle": params["pollution_motorcycle"],
        "ev": params["pollution_ev"],
    }

    if any(value <= 0 for value in capacities.values()):
        return {"objective": None, "status": "invalid_capacity"}
    if any(value < 0 for value in pollution.values()):
        return {"objective": None, "status": "invalid_pollution"}

    # These bounds preserve an optimal solution: trips beyond the number
    # sufficient to meet demand alone cannot improve minimum pollution.
    van_bound = max(1, ceil(max(0, demand) / capacities["van"]))
    ev_bound = max(1, ceil(max(0, demand) / capacities["ev"]))

    model = pyo.ConcreteModel()
    model.modes = pyo.Set(
        initialize=["truck", "van", "motorcycle", "ev"],
        ordered=True,
    )
    model.trips = pyo.Var(model.modes, domain=pyo.NonNegativeIntegers)
    model.choose_van = pyo.Var(domain=pyo.Binary)

    model.demand_requirement = pyo.Constraint(
        expr=sum(
            capacities[mode] * model.trips[mode]
            for mode in model.modes
        ) >= demand
    )
    model.pollution_limit = pyo.Constraint(
        expr=sum(
            pollution[mode] * model.trips[mode]
            for mode in model.modes
        ) <= pollution_cap
    )
    model.truck_requirement = pyo.Constraint(
        expr=model.trips["truck"] >= min_truck_trips
    )

    # At most one of the van and electric-vehicle options may have trips.
    model.van_selection_limit = pyo.Constraint(
        expr=model.trips["van"] <= van_bound * model.choose_van
    )
    model.ev_selection_limit = pyo.Constraint(
        expr=model.trips["ev"] <= ev_bound * (1 - model.choose_van)
    )

    model.total_pollution = pyo.Objective(
        expr=sum(
            pollution[mode] * model.trips[mode]
            for mode in model.modes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_pollution))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}