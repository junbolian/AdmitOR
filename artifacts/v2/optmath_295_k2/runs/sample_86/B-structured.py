# IR: {"sets":{"P":[0,1],"L":[0,1],"A":[[0,1],[1,0]],"T":[0,1]},"params":["cost_p0_0to1","cost_p0_1to0","cost_p1_0to1","cost_p1_1to0","max_planes_p0","max_planes_p1","demand_0to1","capacity_p0","capacity_p1","max_ops_p0_0to1","max_ops_p1_0to1","max_ops_p0_1to0","max_ops_p1_1to0"],"variables":{"flights[p,o,d]":"nonnegative integer; trips during the single operating period","idle[p,l]":"nonnegative integer; planes remaining idle during the period","inventory[p,l,t]":"nonnegative integer; initial inventory at t=0 and final inventory at t=1"},"constraints":["sum_l inventory[p,l,0] <= fleet[p] for each p","inventory[p,l,0] = idle[p,l] + flights[p,l,1-l] for each p,l","inventory[p,l,1] = idle[p,l] + flights[p,1-l,l] for each p,l","sum_p capacity[p]*flights[p,0,1] >= demand_0to1","flights[p,o,d] <= route_limit[p,o,d] for each p,(o,d)"],"objective":"minimize sum_{p,(o,d)} cost[p,o,d]*flights[p,o,d]","assumptions":["One operating period is modeled because only first-period demand is specified.","Initial allocation is optimized because no fixed allocation is supplied.","Flights arrive at the end of the operating period."]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.plane_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.locations = pyo.Set(initialize=[0, 1], ordered=True)
    model.routes = pyo.Set(
        initialize=[(0, 1), (1, 0)], dimen=2, ordered=True
    )
    model.time_points = pyo.Set(initialize=[0, 1], ordered=True)

    model.operating_cost = pyo.Param(
        model.plane_types,
        model.routes,
        initialize={
            (0, 0, 1): params["cost_p0_0to1"],
            (0, 1, 0): params["cost_p0_1to0"],
            (1, 0, 1): params["cost_p1_0to1"],
            (1, 1, 0): params["cost_p1_1to0"],
        },
        within=pyo.Reals,
    )

    model.fleet_limit = pyo.Param(
        model.plane_types,
        initialize={
            0: params["max_planes_p0"],
            1: params["max_planes_p1"],
        },
        within=pyo.NonNegativeReals,
    )

    model.passenger_capacity = pyo.Param(
        model.plane_types,
        initialize={
            0: params["capacity_p0"],
            1: params["capacity_p1"],
        },
        within=pyo.NonNegativeReals,
    )

    model.passenger_demand = pyo.Param(
        initialize=params["demand_0to1"],
        within=pyo.NonNegativeReals,
    )

    model.route_limit = pyo.Param(
        model.plane_types,
        model.routes,
        initialize={
            (0, 0, 1): params["max_ops_p0_0to1"],
            (1, 0, 1): params["max_ops_p1_0to1"],
            (0, 1, 0): params["max_ops_p0_1to0"],
            (1, 1, 0): params["max_ops_p1_1to0"],
        },
        within=pyo.NonNegativeReals,
    )

    model.flights = pyo.Var(
        model.plane_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )
    model.idle = pyo.Var(
        model.plane_types,
        model.locations,
        domain=pyo.NonNegativeIntegers,
    )
    model.inventory = pyo.Var(
        model.plane_types,
        model.locations,
        model.time_points,
        domain=pyo.NonNegativeIntegers,
    )

    def fleet_availability_rule(mod, plane_type):
        return (
            sum(
                mod.inventory[plane_type, location, 0]
                for location in mod.locations
            )
            <= mod.fleet_limit[plane_type]
        )

    model.fleet_availability = pyo.Constraint(
        model.plane_types,
        rule=fleet_availability_rule,
    )

    def initial_allocation_rule(mod, plane_type, location):
        return (
            mod.inventory[plane_type, location, 0]
            == mod.idle[plane_type, location]
            + mod.flights[plane_type, location, 1 - location]
        )

    model.initial_allocation_balance = pyo.Constraint(
        model.plane_types,
        model.locations,
        rule=initial_allocation_rule,
    )

    def final_inventory_rule(mod, plane_type, location):
        return (
            mod.inventory[plane_type, location, 1]
            == mod.idle[plane_type, location]
            + mod.flights[plane_type, 1 - location, location]
        )

    model.final_inventory_balance = pyo.Constraint(
        model.plane_types,
        model.locations,
        rule=final_inventory_rule,
    )

    model.demand_satisfaction = pyo.Constraint(
        expr=sum(
            model.passenger_capacity[plane_type]
            * model.flights[plane_type, 0, 1]
            for plane_type in model.plane_types
        )
        >= model.passenger_demand
    )

    def route_restriction_rule(mod, plane_type, origin, destination):
        return (
            mod.flights[plane_type, origin, destination]
            <= mod.route_limit[plane_type, origin, destination]
        )

    model.route_restrictions = pyo.Constraint(
        model.plane_types,
        model.routes,
        rule=route_restriction_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operating_cost[plane_type, origin, destination]
            * model.flights[plane_type, origin, destination]
            for plane_type in model.plane_types
            for origin, destination in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}