# IR: {"sets":{"T":[0,1],"L":[0,1]},"params":["plane0_capacity","plane1_capacity","plane0_cost","plane1_cost","initial_planes_per_type","demand_period1","max_trips_plane0","max_trips_plane1"],"variables":{"trips[t,i,j]":"nonnegative integer","initial_idle[t,i]":"nonnegative integer","final_idle[t,i]":"nonnegative integer"},"constraints":["sum_i initial_idle[t,i] <= initial_planes_per_type for each t","sum_j trips[t,i,j] = initial_idle[t,i] for each t,i","sum_i trips[t,i,j] = final_idle[t,j] for each t,j","trips[t,0,1] = 0 for each t","trips[0,1,0] <= max_trips_plane0","trips[1,1,0] <= max_trips_plane1","plane0_capacity*trips[0,1,0] + plane1_capacity*trips[1,1,0] >= demand_period1"],"objective":"minimize sum_{i!=j}(plane0_cost*trips[0,i,j] + plane1_cost*trips[1,i,j])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.plane_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.locations = pyo.Set(initialize=[0, 1], ordered=True)

    model.capacity = pyo.Param(
        model.plane_types,
        initialize={
            0: params["plane0_capacity"],
            1: params["plane1_capacity"],
        },
        within=pyo.NonNegativeReals,
    )
    model.trip_cost = pyo.Param(
        model.plane_types,
        initialize={
            0: params["plane0_cost"],
            1: params["plane1_cost"],
        },
        within=pyo.NonNegativeReals,
    )
    model.fleet_limit = pyo.Param(
        initialize=params["initial_planes_per_type"],
        within=pyo.NonNegativeReals,
    )
    model.passenger_demand = pyo.Param(
        initialize=params["demand_period1"],
        within=pyo.NonNegativeReals,
    )
    model.route_trip_limit = pyo.Param(
        model.plane_types,
        initialize={
            0: params["max_trips_plane0"],
            1: params["max_trips_plane1"],
        },
        within=pyo.NonNegativeReals,
    )

    model.trips = pyo.Var(
        model.plane_types,
        model.locations,
        model.locations,
        domain=pyo.NonNegativeIntegers,
    )
    model.initial_idle = pyo.Var(
        model.plane_types,
        model.locations,
        domain=pyo.NonNegativeIntegers,
    )
    model.final_idle = pyo.Var(
        model.plane_types,
        model.locations,
        domain=pyo.NonNegativeIntegers,
    )

    def fleet_limit_rule(mdl, plane_type):
        return (
            sum(mdl.initial_idle[plane_type, loc] for loc in mdl.locations)
            <= mdl.fleet_limit
        )

    model.fleet_availability = pyo.Constraint(
        model.plane_types, rule=fleet_limit_rule
    )

    # A same-location transition represents a plane remaining idle.
    # Departure and arrival accounting jointly enforce fleet flow balance.
    def departure_rule(mdl, plane_type, origin):
        return (
            sum(
                mdl.trips[plane_type, origin, destination]
                for destination in mdl.locations
            )
            == mdl.initial_idle[plane_type, origin]
        )

    model.departure_accounting = pyo.Constraint(
        model.plane_types, model.locations, rule=departure_rule
    )

    def arrival_rule(mdl, plane_type, destination):
        return (
            sum(
                mdl.trips[plane_type, origin, destination]
                for origin in mdl.locations
            )
            == mdl.final_idle[plane_type, destination]
        )

    model.arrival_accounting = pyo.Constraint(
        model.plane_types, model.locations, rule=arrival_rule
    )

    def prohibited_route_rule(mdl, plane_type):
        return mdl.trips[plane_type, 0, 1] == 0

    model.prohibited_route = pyo.Constraint(
        model.plane_types, rule=prohibited_route_rule
    )

    def route_limit_rule(mdl, plane_type):
        return (
            mdl.trips[plane_type, 1, 0]
            <= mdl.route_trip_limit[plane_type]
        )

    model.route_limits = pyo.Constraint(
        model.plane_types, rule=route_limit_rule
    )

    model.demand_coverage = pyo.Constraint(
        expr=sum(
            model.capacity[plane_type] * model.trips[plane_type, 1, 0]
            for plane_type in model.plane_types
        )
        >= model.passenger_demand
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.trip_cost[plane_type]
            * model.trips[plane_type, origin, destination]
            for plane_type in model.plane_types
            for origin in model.locations
            for destination in model.locations
            if origin != destination
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions must propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError as exc:
        if "No value for uninitialized" not in str(exc):
            raise
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}