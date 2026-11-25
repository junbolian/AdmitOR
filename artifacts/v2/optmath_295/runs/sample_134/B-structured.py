# IR: {"sets":{"A":["aircraft_0","...","aircraft_6"],"R":["route_0","...","route_6"]},"params":{"aircraft_availability":"A -> real","route_demand":"R -> real","capability":"A x R -> real","operational_cost":"A x R -> real"},"variables":{"x[a,r]":"nonnegative integer"},"constraints":["forall a in A: sum(r in R, x[a,r]) <= aircraft_availability[a]","forall r in R: sum(a in A, capability[a,r]*x[a,r]) >= route_demand[r]"],"objective":"minimize sum(a in A, r in R, operational_cost[a,r]*x[a,r])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _vector_value(data, position, label):
    """Accept a sequence, an integer-keyed mapping, or a label-keyed mapping."""
    if isinstance(data, Mapping):
        return data[position] if position in data else data[label]
    return data[position]


def _matrix_value(data, aircraft_pos, route_pos):
    """Accept nested data or a mapping keyed by index/label pairs."""
    aircraft_label = f"aircraft_{aircraft_pos}"
    route_label = f"route_{route_pos}"

    if isinstance(data, Mapping):
        integer_pair = (aircraft_pos, route_pos)
        label_pair = (aircraft_label, route_label)
        if integer_pair in data:
            return data[integer_pair]
        if label_pair in data:
            return data[label_pair]

    row = _vector_value(data, aircraft_pos, aircraft_label)
    return _vector_value(row, route_pos, route_label)


def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capability = params["capability"]
    operational_cost = params["operational_cost"]

    model = pyo.ConcreteModel()

    model.aircraft_types = pyo.RangeSet(0, 6)
    model.routes = pyo.RangeSet(0, 6)

    model.availability = pyo.Param(
        model.aircraft_types,
        within=pyo.Reals,
        initialize={
            aircraft_pos: _vector_value(
                aircraft_availability,
                aircraft_pos,
                f"aircraft_{aircraft_pos}",
            )
            for aircraft_pos in model.aircraft_types
        },
    )
    model.demand = pyo.Param(
        model.routes,
        within=pyo.Reals,
        initialize={
            route_pos: _vector_value(
                route_demand, route_pos, f"route_{route_pos}"
            )
            for route_pos in model.routes
        },
    )
    model.capability_units = pyo.Param(
        model.aircraft_types,
        model.routes,
        within=pyo.Reals,
        initialize={
            (aircraft_pos, route_pos): _matrix_value(
                capability, aircraft_pos, route_pos
            )
            for aircraft_pos in model.aircraft_types
            for route_pos in model.routes
        },
    )
    model.assignment_cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        within=pyo.Reals,
        initialize={
            (aircraft_pos, route_pos): _matrix_value(
                operational_cost, aircraft_pos, route_pos
            )
            for aircraft_pos in model.aircraft_types
            for route_pos in model.routes
        },
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(current_model, aircraft_pos):
        return (
            sum(
                current_model.x[aircraft_pos, route_pos]
                for route_pos in current_model.routes
            )
            <= current_model.availability[aircraft_pos]
        )

    model.availability_limits = pyo.Constraint(
        model.aircraft_types, rule=availability_rule
    )

    def demand_rule(current_model, route_pos):
        return (
            sum(
                current_model.capability_units[aircraft_pos, route_pos]
                * current_model.x[aircraft_pos, route_pos]
                for aircraft_pos in current_model.aircraft_types
            )
            >= current_model.demand[route_pos]
        )

    model.demand_requirements = pyo.Constraint(
        model.routes, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[aircraft_pos, route_pos]
            * model.x[aircraft_pos, route_pos]
            for aircraft_pos in model.aircraft_types
            for route_pos in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}