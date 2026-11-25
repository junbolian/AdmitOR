# IR {
#   "sets": {"P": [0, 1], "L": [0, 1], "R": [[0, 1], [1, 0]]},
#   "params": ["cost_P0_L0_to_L1", "cost_P0_L1_to_L0", "cost_P1_L0_to_L1", "cost_P1_L1_to_L0", "cost_idle", "max_planes_P0", "max_planes_P1", "demand_L0_to_L1_period1", "capacity_P0", "capacity_P1", "max_route_P0_L0_to_L1", "max_route_P1_L0_to_L1", "max_route_P0_L1_to_L0", "max_route_P1_L1_to_L0"],
#   "scope": "One operating period; initial allocation is optimized because no fixed allocation is supplied; flights arrive at period end.",
#   "variables": {"initial[p,l]": "nonnegative integer, initially allocated planes", "flight[p,i,j]": "nonnegative integer, planes flying route (i,j)", "idle[p,l]": "nonnegative integer, planes remaining idle throughout the period", "ending[p,l]": "nonnegative integer, planes present after arrivals"},
#   "constraints": [
#     "For each p,l: initial[p,l] = idle[p,l] + flight[p,l,1-l].",
#     "For each p,l: ending[p,l] = idle[p,l] + flight[p,1-l,l].",
#     "For each p: sum_l initial[p,l] <= max_planes[p].",
#     "For each p,(i,j): flight[p,i,j] <= max_route[p,i,j].",
#     "sum_p capacity[p] * flight[p,0,1] >= demand_L0_to_L1_period1."
#   ],
#   "objective": "Minimize sum_{p,(i,j)} cost[p,i,j]*flight[p,i,j] + cost_idle*sum_{p,l} idle[p,l]."
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.plane_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.locations = pyo.Set(initialize=[0, 1], ordered=True)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (1, 0)],
        ordered=True,
    )

    model.flight_cost = pyo.Param(
        model.plane_types,
        model.routes,
        initialize={
            (0, 0, 1): params["cost_P0_L0_to_L1"],
            (0, 1, 0): params["cost_P0_L1_to_L0"],
            (1, 0, 1): params["cost_P1_L0_to_L1"],
            (1, 1, 0): params["cost_P1_L1_to_L0"],
        },
        within=pyo.Reals,
    )
    model.idle_cost = pyo.Param(
        initialize=params["cost_idle"],
        within=pyo.Reals,
    )
    model.fleet_limit = pyo.Param(
        model.plane_types,
        initialize={
            0: params["max_planes_P0"],
            1: params["max_planes_P1"],
        },
        within=pyo.Reals,
    )
    model.passenger_capacity = pyo.Param(
        model.plane_types,
        initialize={
            0: params["capacity_P0"],
            1: params["capacity_P1"],
        },
        within=pyo.Reals,
    )
    model.route_limit = pyo.Param(
        model.plane_types,
        model.routes,
        initialize={
            (0, 0, 1): params["max_route_P0_L0_to_L1"],
            (1, 0, 1): params["max_route_P1_L0_to_L1"],
            (0, 1, 0): params["max_route_P0_L1_to_L0"],
            (1, 1, 0): params["max_route_P1_L1_to_L0"],
        },
        within=pyo.Reals,
    )
    model.passenger_demand = pyo.Param(
        initialize=params["demand_L0_to_L1_period1"],
        within=pyo.Reals,
    )

    model.initial = pyo.Var(
        model.plane_types,
        model.locations,
        domain=pyo.NonNegativeIntegers,
    )
    model.flight = pyo.Var(
        model.plane_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )
    model.idle = pyo.Var(
        model.plane_types,
        model.locations,
        domain=pyo.NonNegativeIntegers,
    )
    model.ending = pyo.Var(
        model.plane_types,
        model.locations,
        domain=pyo.NonNegativeIntegers,
    )

    def initial_balance_rule(model, plane, location):
        return (
            model.initial[plane, location]
            == model.idle[plane, location]
            + model.flight[plane, location, 1 - location]
        )

    model.initial_balance = pyo.Constraint(
        model.plane_types,
        model.locations,
        rule=initial_balance_rule,
    )

    def ending_balance_rule(model, plane, location):
        return (
            model.ending[plane, location]
            == model.idle[plane, location]
            + model.flight[plane, 1 - location, location]
        )

    model.ending_balance = pyo.Constraint(
        model.plane_types,
        model.locations,
        rule=ending_balance_rule,
    )

    def fleet_availability_rule(model, plane):
        return (
            sum(
                model.initial[plane, location]
                for location in model.locations
            )
            <= model.fleet_limit[plane]
        )

    model.fleet_availability = pyo.Constraint(
        model.plane_types,
        rule=fleet_availability_rule,
    )

    def route_restriction_rule(model, plane, origin, destination):
        return (
            model.flight[plane, origin, destination]
            <= model.route_limit[plane, origin, destination]
        )

    model.route_restriction = pyo.Constraint(
        model.plane_types,
        model.routes,
        rule=route_restriction_rule,
    )

    model.demand_coverage = pyo.Constraint(
        expr=sum(
            model.passenger_capacity[plane] * model.flight[plane, 0, 1]
            for plane in model.plane_types
        )
        >= model.passenger_demand
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.flight_cost[plane, origin, destination]
            * model.flight[plane, origin, destination]
            for plane in model.plane_types
            for origin, destination in model.routes
        )
        + model.idle_cost
        * sum(
            model.idle[plane, location]
            for plane in model.plane_types
            for location in model.locations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}