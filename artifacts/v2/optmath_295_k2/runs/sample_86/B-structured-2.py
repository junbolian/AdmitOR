# IR: {"sets":{"planes":[0,1],"locations":[0,1],"arcs":[[0,1],[1,0]],"idle_stages":["during","end"]},"params":["cost_p0_0to1","cost_p0_1to0","cost_p1_0to1","cost_p1_1to0","max_planes_p0","max_planes_p1","demand_0to1","capacity_p0","capacity_p1","max_ops_p0_0to1","max_ops_p1_0to1","max_ops_p0_1to0","max_ops_p1_1to0"],"variables":{"allocation[p,l]":"nonnegative integer; initial allocation","flights[p,i,j]":"nonnegative integer; planes operated during the single period","idle[p,l,s]":"nonnegative integer; idle during operations or available at period end"},"constraints":["sum_l allocation[p,l] <= fleet_limit[p] for each p","allocation[p,l] = idle[p,l,during] + sum_(l,j) flights[p,l,j] for each p,l","idle[p,l,end] = idle[p,l,during] + sum_(i,l) flights[p,i,l] for each p,l","sum_p capacity[p]*flights[p,0,1] >= demand_0to1","flights[p,i,j] <= route_limit[p,i,j] for each p,(i,j)"],"objective":"minimize sum_p sum_(i,j) cost[p,i,j]*flights[p,i,j]","assumptions":["One operating period is modeled because only first-period demand is supplied.","Initial allocations are decisions because no fixed location-specific allocations are supplied.","Each operated plane makes one trip during the period; arrivals become available at period end."]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_data = {
        (0, 0, 1): params["cost_p0_0to1"],
        (0, 1, 0): params["cost_p0_1to0"],
        (1, 0, 1): params["cost_p1_0to1"],
        (1, 1, 0): params["cost_p1_1to0"],
    }
    fleet_data = {
        0: params["max_planes_p0"],
        1: params["max_planes_p1"],
    }
    capacity_data = {
        0: params["capacity_p0"],
        1: params["capacity_p1"],
    }
    route_limit_data = {
        (0, 0, 1): params["max_ops_p0_0to1"],
        (1, 0, 1): params["max_ops_p1_0to1"],
        (0, 1, 0): params["max_ops_p0_1to0"],
        (1, 1, 0): params["max_ops_p1_1to0"],
    }

    model = pyo.ConcreteModel()
    model.planes = pyo.Set(initialize=[0, 1], ordered=True)
    model.locations = pyo.Set(initialize=[0, 1], ordered=True)
    model.arcs = pyo.Set(
        dimen=2, initialize=[(0, 1), (1, 0)], ordered=True
    )
    model.idle_stages = pyo.Set(
        initialize=["during", "end"], ordered=True
    )

    model.operating_cost = pyo.Param(
        model.planes, model.arcs, initialize=cost_data
    )
    model.fleet_limit = pyo.Param(
        model.planes, initialize=fleet_data
    )
    model.passenger_capacity = pyo.Param(
        model.planes, initialize=capacity_data
    )
    model.route_limit = pyo.Param(
        model.planes, model.arcs, initialize=route_limit_data
    )
    model.passenger_demand = pyo.Param(
        initialize=params["demand_0to1"]
    )

    model.allocation = pyo.Var(
        model.planes,
        model.locations,
        domain=pyo.NonNegativeIntegers,
    )
    model.flights = pyo.Var(
        model.planes,
        model.arcs,
        domain=pyo.NonNegativeIntegers,
    )
    model.idle = pyo.Var(
        model.planes,
        model.locations,
        model.idle_stages,
        domain=pyo.NonNegativeIntegers,
    )

    def fleet_rule(mdl, plane):
        return (
            sum(
                mdl.allocation[plane, location]
                for location in mdl.locations
            )
            <= mdl.fleet_limit[plane]
        )

    model.fleet_availability = pyo.Constraint(
        model.planes, rule=fleet_rule
    )

    def initial_balance_rule(mdl, plane, location):
        departures = sum(
            mdl.flights[plane, origin, destination]
            for origin, destination in mdl.arcs
            if origin == location
        )
        return (
            mdl.allocation[plane, location]
            == mdl.idle[plane, location, "during"] + departures
        )

    model.initial_balance = pyo.Constraint(
        model.planes, model.locations, rule=initial_balance_rule
    )

    def ending_balance_rule(mdl, plane, location):
        arrivals = sum(
            mdl.flights[plane, origin, destination]
            for origin, destination in mdl.arcs
            if destination == location
        )
        return (
            mdl.idle[plane, location, "end"]
            == mdl.idle[plane, location, "during"] + arrivals
        )

    model.ending_balance = pyo.Constraint(
        model.planes, model.locations, rule=ending_balance_rule
    )

    model.demand_coverage = pyo.Constraint(
        expr=sum(
            model.passenger_capacity[plane]
            * model.flights[plane, 0, 1]
            for plane in model.planes
        )
        >= model.passenger_demand
    )

    def route_limit_rule(mdl, plane, origin, destination):
        return (
            mdl.flights[plane, origin, destination]
            <= mdl.route_limit[plane, origin, destination]
        )

    model.route_restrictions = pyo.Constraint(
        model.planes, model.arcs, rule=route_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operating_cost[plane, origin, destination]
            * model.flights[plane, origin, destination]
            for plane in model.planes
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors are allowed to propagate.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}