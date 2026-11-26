# IR: {"sets":{"V":["truck","van","motorcycle","ev"],"E":["van","ev"]},"params":["truck_capacity","van_capacity","motorcycle_capacity","ev_capacity","truck_pollution","van_pollution","motorcycle_pollution","ev_pollution","pollution_budget","truck_min_trips","demand_required"],"derived":{"U[v]":"max(1,ceil(demand_required/capacity[v])) if capacity[v]>0 else 1, for v in E"},"variables":{"trips[v in V]":"nonnegative integer","selected[v in E]":"binary"},"constraints":["sum(capacity[v]*trips[v] for v in V)>=demand_required","sum(pollution[v]*trips[v] for v in V)<=pollution_budget","trips[truck]>=truck_min_trips","sum(selected[v] for v in E)==1","trips[v]>=selected[v] for v in E","trips[v]<=U[v]*selected[v] for v in E"],"objective":"minimize sum(trips[v] for v in V)"}
# Objective assumption: minimize total trips, since no objective was specified.
# Exactly one of vans and electric vehicles must make at least one trip.
# The derived bounds preserve an optimum: additional trips beyond U[v]
# cannot improve demand satisfaction or the objective with nonnegative data.

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = {
        "truck": float(params["truck_capacity"]),
        "van": float(params["van_capacity"]),
        "motorcycle": float(params["motorcycle_capacity"]),
        "ev": float(params["ev_capacity"]),
    }
    pollution = {
        "truck": float(params["truck_pollution"]),
        "van": float(params["van_pollution"]),
        "motorcycle": float(params["motorcycle_pollution"]),
        "ev": float(params["ev_pollution"]),
    }
    pollution_budget = float(params["pollution_budget"])
    truck_min_trips = float(params["truck_min_trips"])
    demand_required = float(params["demand_required"])

    numeric_values = (
        list(capacities.values())
        + list(pollution.values())
        + [pollution_budget, truck_min_trips, demand_required]
    )
    if any(
        not math.isfinite(value) or value < 0
        for value in numeric_values
    ):
        return {"objective": None, "status": "invalid_parameters"}

    exclusive_options = ("van", "ev")
    trip_bounds = {
        vehicle: (
            max(1, math.ceil(demand_required / capacities[vehicle]))
            if capacities[vehicle] > 0
            else 1
        )
        for vehicle in exclusive_options
    }

    model = pyo.ConcreteModel()

    model.V = pyo.Set(
        initialize=("truck", "van", "motorcycle", "ev"),
        ordered=True,
    )
    model.E = pyo.Set(initialize=exclusive_options, ordered=True)

    model.capacity = pyo.Param(
        model.V, initialize=capacities, within=pyo.NonNegativeReals
    )
    model.pollution = pyo.Param(
        model.V, initialize=pollution, within=pyo.NonNegativeReals
    )
    model.pollution_budget = pyo.Param(
        initialize=pollution_budget, within=pyo.NonNegativeReals
    )
    model.truck_min_trips = pyo.Param(
        initialize=truck_min_trips, within=pyo.NonNegativeReals
    )
    model.demand_required = pyo.Param(
        initialize=demand_required, within=pyo.NonNegativeReals
    )
    model.trip_bound = pyo.Param(
        model.E, initialize=trip_bounds, within=pyo.PositiveIntegers
    )

    model.trips = pyo.Var(model.V, domain=pyo.NonNegativeIntegers)
    model.selected = pyo.Var(model.E, domain=pyo.Binary)

    model.demand_constraint = pyo.Constraint(
        expr=sum(
            model.capacity[vehicle] * model.trips[vehicle]
            for vehicle in model.V
        ) >= model.demand_required
    )
    model.pollution_constraint = pyo.Constraint(
        expr=sum(
            model.pollution[vehicle] * model.trips[vehicle]
            for vehicle in model.V
        ) <= model.pollution_budget
    )
    model.truck_minimum_constraint = pyo.Constraint(
        expr=model.trips["truck"] >= model.truck_min_trips
    )
    model.exclusive_choice_constraint = pyo.Constraint(
        expr=sum(model.selected[vehicle] for vehicle in model.E) == 1
    )

    def selected_usage_rule(instance, vehicle):
        return instance.trips[vehicle] >= instance.selected[vehicle]

    def selected_bound_rule(instance, vehicle):
        return (
            instance.trips[vehicle]
            <= instance.trip_bound[vehicle] * instance.selected[vehicle]
        )

    model.selected_usage_constraint = pyo.Constraint(
        model.E, rule=selected_usage_rule
    )
    model.selected_bound_constraint = pyo.Constraint(
        model.E, rule=selected_bound_rule
    )

    model.total_trips = pyo.Objective(
        expr=sum(model.trips[vehicle] for vehicle in model.V),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_trips))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}