# IR: {"sets":{"methods":["motorcycle","small_truck","large_truck"]},"params":["pollution_motorcycle","pollution_small_truck","pollution_large_truck","motorcycle_trip_cap","capacity_motorcycle","capacity_small_truck","capacity_large_truck","demand","total_trip_cap"],"variables":{"trips[methods]":"NonNegativeIntegers","selected[methods]":"Binary"},"constraints":["sum(selected[t] for t in methods) == 2","trips[t] >= selected[t] for t in methods","trips[t] <= total_trip_cap * selected[t] for t in methods","trips['motorcycle'] <= motorcycle_trip_cap","sum(capacity[t] * trips[t] for t in methods) >= demand","sum(trips[t] for t in methods) <= total_trip_cap"],"objective":"minimize sum(pollution[t] * trips[t] for t in methods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize pollution while using exactly two transportation methods."""
    model = pyo.ConcreteModel()

    model.methods = pyo.Set(
        initialize=["motorcycle", "small_truck", "large_truck"],
        ordered=True,
    )

    model.pollution = pyo.Param(
        model.methods,
        initialize={
            "motorcycle": params["pollution_motorcycle"],
            "small_truck": params["pollution_small_truck"],
            "large_truck": params["pollution_large_truck"],
        },
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.methods,
        initialize={
            "motorcycle": params["capacity_motorcycle"],
            "small_truck": params["capacity_small_truck"],
            "large_truck": params["capacity_large_truck"],
        },
        within=pyo.NonNegativeReals,
    )
    model.motorcycle_trip_cap = pyo.Param(
        initialize=params["motorcycle_trip_cap"],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        initialize=params["demand"],
        within=pyo.NonNegativeReals,
    )
    model.total_trip_cap = pyo.Param(
        initialize=params["total_trip_cap"],
        within=pyo.NonNegativeReals,
    )

    model.trips = pyo.Var(model.methods, domain=pyo.NonNegativeIntegers)
    model.selected = pyo.Var(model.methods, domain=pyo.Binary)

    model.two_methods = pyo.Constraint(
        expr=sum(model.selected[t] for t in model.methods) == 2
    )

    def minimum_usage_rule(instance, transport):
        return instance.trips[transport] >= instance.selected[transport]

    model.minimum_usage = pyo.Constraint(
        model.methods, rule=minimum_usage_rule
    )

    def maximum_usage_rule(instance, transport):
        return (
            instance.trips[transport]
            <= instance.total_trip_cap * instance.selected[transport]
        )

    model.maximum_usage = pyo.Constraint(
        model.methods, rule=maximum_usage_rule
    )

    model.motorcycle_limit = pyo.Constraint(
        expr=model.trips["motorcycle"] <= model.motorcycle_trip_cap
    )
    model.demand_requirement = pyo.Constraint(
        expr=sum(
            model.capacity[t] * model.trips[t] for t in model.methods
        ) >= model.demand
    )
    model.total_trip_limit = pyo.Constraint(
        expr=sum(model.trips[t] for t in model.methods)
        <= model.total_trip_cap
    )

    model.total_pollution = pyo.Objective(
        expr=sum(
            model.pollution[t] * model.trips[t] for t in model.methods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when its default solution loading finds no solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_pollution))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}