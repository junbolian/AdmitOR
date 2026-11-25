# IR: {"sets":{"K":[0,1],"L":[0,1]},"params":["plane0_capacity","plane1_capacity","plane0_cost","plane1_cost","initial_planes_per_type","demand_period1","max_trips_plane0","max_trips_plane1"],"variables":{"trips[k,i,j]":"nonnegative integer; diagonal entries represent planes remaining idle","initial_idle[k,i]":"nonnegative integer","final_idle[k,i]":"nonnegative integer"},"constraints":["For each k,i: sum_j trips[k,i,j] = initial_idle[k,i].","For each k,j: sum_i trips[k,i,j] = final_idle[k,j].","For each k: sum_i initial_idle[k,i] <= initial_planes_per_type.","For each k: trips[k,0,1] = 0.","trips[0,1,0] <= max_trips_plane0.","trips[1,1,0] <= max_trips_plane1.","plane0_capacity*trips[0,1,0] + plane1_capacity*trips[1,1,0] >= demand_period1."],"objective":"Minimize sum_{i != j} (plane0_cost*trips[0,i,j] + plane1_cost*trips[1,i,j])."}
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

    def departure_balance_rule(model, plane_type, origin):
        return (
            sum(
                model.trips[plane_type, origin, destination]
                for destination in model.locations
            )
            == model.initial_idle[plane_type, origin]
        )

    model.departure_balance = pyo.Constraint(
        model.plane_types,
        model.locations,
        rule=departure_balance_rule,
    )

    def arrival_balance_rule(model, plane_type, destination):
        return (
            sum(
                model.trips[plane_type, origin, destination]
                for origin in model.locations
            )
            == model.final_idle[plane_type, destination]
        )

    model.arrival_balance = pyo.Constraint(
        model.plane_types,
        model.locations,
        rule=arrival_balance_rule,
    )

    def fleet_availability_rule(model, plane_type):
        return (
            sum(
                model.initial_idle[plane_type, location]
                for location in model.locations
            )
            <= model.fleet_limit
        )

    model.fleet_availability = pyo.Constraint(
        model.plane_types,
        rule=fleet_availability_rule,
    )

    def prohibited_route_rule(model, plane_type):
        return model.trips[plane_type, 0, 1] == 0

    model.prohibited_route = pyo.Constraint(
        model.plane_types,
        rule=prohibited_route_rule,
    )

    def permitted_route_limit_rule(model, plane_type):
        return (
            model.trips[plane_type, 1, 0]
            <= model.route_trip_limit[plane_type]
        )

    model.permitted_route_limit = pyo.Constraint(
        model.plane_types,
        rule=permitted_route_limit_rule,
    )

    model.demand_satisfaction = pyo.Constraint(
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

    # HiGHS may raise RuntimeError when no solution can be loaded.
    # Objective retrieval alone determines whether to report success.
    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {
            "objective": None,
            "status": (
                "solver_failed" if solver_failed else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}