# IR: {"sets":{"A":"aircraft_0..aircraft_5","R":"route_0..route_6"},"params":{"availability":"A -> nonnegative integer","route_demand":"R -> nonnegative real","route6_demand":"nonnegative real","a0_capacity":"R -> nonnegative real","a1_capacity":"R -> nonnegative real","a2_capacity":"R -> nonnegative real; unspecified in supplied PARAMS","a3_capacity":"R -> nonnegative real; unspecified in supplied PARAMS","a4_capacity":"R -> nonnegative real; unspecified in supplied PARAMS","a5_capacity":"R -> nonnegative real; unspecified in supplied PARAMS","operational_cost":"A x R -> real"},"variables":{"assignment[A,R]":"nonnegative integer"},"constraints":["sum_r assignment[a,r] <= availability[a] for every a","sum_a a_capacity[a,r]*assignment[a,r] >= route_demand[r] for every r","sum_a a_capacity[a,route_6]*assignment[a,route_6] >= route6_demand"],"objective":"minimize sum_a,r operational_cost[a,r]*assignment[a,r]","input_policy":"If any unspecified capacity row is absent, return objective=null and status=underspecified_capacities; never fabricate coefficients."}
#
# The reported failure is caused by missing problem data, not a solver defect.
# The listed PARAMS provide capacity coefficients for only two aircraft types.
# No exact six-type model can be solved from those inputs alone. Capacities for
# aircraft_2 through aircraft_5 cannot be inferred from costs or availability.
# This script solves the stated model when those four rows are supplied as
# params["a2_capacity"] through params["a5_capacity"]. Otherwise it reports the
# underdetermination, as permitted by the required failure-return contract.

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(data, position, prefix):
    """Read a sequence or a mapping using named, integer, or string indices."""
    if isinstance(data, Mapping):
        named_key = f"{prefix}_{position}"
        if named_key in data:
            return data[named_key]
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position]


def _cost_value(data, aircraft, route):
    """Read nested costs or costs keyed by aircraft/route tuples."""
    if isinstance(data, Mapping):
        for pair in (
            (f"aircraft_{aircraft}", f"route_{route}"),
            (aircraft, route),
            (str(aircraft), str(route)),
        ):
            if pair in data:
                return data[pair]

    row = _indexed_value(data, aircraft, "aircraft")
    return _indexed_value(row, route, "route")


def solve(params):
    availability_data = params["availability"]
    route_demand_data = params["route_demand"]
    route6_demand_data = params["route6_demand"]
    a0_capacity_data = params["a0_capacity"]
    a1_capacity_data = params["a1_capacity"]
    operational_cost_data = params["operational_cost"]

    missing_capacity_keys = [
        f"a{aircraft}_capacity"
        for aircraft in range(2, 6)
        if (
            f"a{aircraft}_capacity" not in params
            or params[f"a{aircraft}_capacity"] is None
        )
    ]
    if missing_capacity_keys:
        return {"objective": None, "status": "underspecified_capacities"}

    capacity_rows = [
        a0_capacity_data,
        a1_capacity_data,
        params["a2_capacity"],
        params["a3_capacity"],
        params["a4_capacity"],
        params["a5_capacity"],
    ]

    model = pyo.ConcreteModel()
    model.aircraft_types = pyo.RangeSet(0, 5)
    model.routes = pyo.RangeSet(0, 6)

    model.aircraft_availability = pyo.Param(
        model.aircraft_types,
        initialize={
            aircraft: _indexed_value(
                availability_data, aircraft, "aircraft"
            )
            for aircraft in model.aircraft_types
        },
        within=pyo.NonNegativeIntegers,
    )

    model.required_capacity = pyo.Param(
        model.routes,
        initialize={
            route: _indexed_value(route_demand_data, route, "route")
            for route in model.routes
        },
        within=pyo.NonNegativeReals,
    )

    model.route_six_required_capacity = pyo.Param(
        initialize=route6_demand_data,
        within=pyo.NonNegativeReals,
    )

    model.capacity_contribution = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize={
            (aircraft, route): _indexed_value(
                capacity_rows[aircraft], route, "route"
            )
            for aircraft in model.aircraft_types
            for route in model.routes
        },
        within=pyo.NonNegativeReals,
    )

    model.assignment_cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize={
            (aircraft, route): _cost_value(
                operational_cost_data, aircraft, route
            )
            for aircraft in model.aircraft_types
            for route in model.routes
        },
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(problem, aircraft):
        return (
            sum(
                problem.assignment[aircraft, route]
                for route in problem.routes
            )
            <= problem.aircraft_availability[aircraft]
        )

    model.availability_limits = pyo.Constraint(
        model.aircraft_types,
        rule=availability_rule,
    )

    def demand_rule(problem, route):
        return (
            sum(
                problem.capacity_contribution[aircraft, route]
                * problem.assignment[aircraft, route]
                for aircraft in problem.aircraft_types
            )
            >= problem.required_capacity[route]
        )

    model.route_demand_limits = pyo.Constraint(
        model.routes,
        rule=demand_rule,
    )

    model.route_six_demand_limit = pyo.Constraint(
        expr=sum(
            model.capacity_contribution[aircraft, 6]
            * model.assignment[aircraft, 6]
            for aircraft in model.aircraft_types
        )
        >= model.route_six_required_capacity
    )

    model.total_operational_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[aircraft, route]
            * model.assignment[aircraft, route]
            for aircraft in model.aircraft_types
            for route in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_operational_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}