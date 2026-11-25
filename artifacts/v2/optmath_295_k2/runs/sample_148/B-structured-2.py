# IR: {"sets":{"A":"aircraft_0..aircraft_4","R":"route_0..route_5","E":"(a,r) pairs with both capacity and cost supplied; assignments are permitted only on these fully specified pairs"},"params":{"availability":"nonnegative integer[A], from params['availability']","demand":"nonnegative real[R], from params['demand']","capacity":"nonnegative real[E], from params['capacity']","cost":"real[E], from params['cost']"},"variables":{"x[a,r]":"nonnegative integer for (a,r) in E"},"constraints":["sum((a,r) in E, x[a,r]) <= availability[a] for each a in A","sum((a,r) in E, capacity[a,r]*x[a,r]) >= demand[r] for each r in R"],"objective":"minimize sum((a,r) in E, cost[a,r]*x[a,r])"}

from collections.abc import Mapping
from math import isfinite

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


class _MissingData(Exception):
    pass


class _InvalidData(Exception):
    pass


def _entry(container, label, position):
    """Read a labeled mapping, an integer-keyed mapping, or a sequence."""
    if container is None:
        raise _MissingData

    if isinstance(container, Mapping):
        for key in (label, position, str(position)):
            if key in container:
                value = container[key]
                if value is None:
                    raise _MissingData
                return value
        raise _MissingData

    try:
        value = container[position]
    except (IndexError, KeyError):
        raise _MissingData from None

    if value is None:
        raise _MissingData
    return value


def _matrix_entry(container, aircraft, route, aircraft_pos, route_pos):
    """Read a nested matrix or a tuple-keyed mapping."""
    if isinstance(container, Mapping):
        for key in (
            (aircraft, route),
            (aircraft_pos, route_pos),
            (str(aircraft_pos), str(route_pos)),
        ):
            if key in container:
                value = container[key]
                if value is None:
                    raise _MissingData
                return value

    row = _entry(container, aircraft, aircraft_pos)
    return _entry(row, route, route_pos)


def _number(value, *, nonnegative=False, integer=False):
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        raise _InvalidData from None

    if not isfinite(result):
        raise _InvalidData
    if nonnegative and result < 0:
        raise _InvalidData
    if integer:
        if not result.is_integer():
            raise _InvalidData
        return int(result)
    return result


def solve(params):
    aircraft_types = tuple(f"aircraft_{idx}" for idx in range(5))
    routes = tuple(f"route_{idx}" for idx in range(6))

    try:
        availability_input = params["availability"]
        demand_input = params["demand"]
        capacity_input = params["capacity"]
        cost_input = params["cost"]
    except KeyError:
        return {"objective": None, "status": "missing_data"}

    try:
        availability = {
            aircraft: _number(
                _entry(availability_input, aircraft, aircraft_pos),
                nonnegative=True,
                integer=True,
            )
            for aircraft_pos, aircraft in enumerate(aircraft_types)
        }
        demand = {
            route: _number(
                _entry(demand_input, route, route_pos),
                nonnegative=True,
            )
            for route_pos, route in enumerate(routes)
        }
    except _MissingData:
        return {"objective": None, "status": "missing_data"}
    except _InvalidData:
        return {"objective": None, "status": "invalid_data"}

    # Sparse matrices are allowed. Unknown coefficients are not fabricated:
    # only pairs with both coefficients supplied become assignment options.
    capacity = {}
    cost = {}
    for aircraft_pos, aircraft in enumerate(aircraft_types):
        for route_pos, route in enumerate(routes):
            try:
                capacity_value = _matrix_entry(
                    capacity_input,
                    aircraft,
                    route,
                    aircraft_pos,
                    route_pos,
                )
                cost_value = _matrix_entry(
                    cost_input,
                    aircraft,
                    route,
                    aircraft_pos,
                    route_pos,
                )
            except _MissingData:
                continue

            try:
                capacity[aircraft, route] = _number(
                    capacity_value, nonnegative=True
                )
                cost[aircraft, route] = _number(cost_value)
            except _InvalidData:
                return {"objective": None, "status": "invalid_data"}

    assignment_pairs = tuple(capacity)
    routes_by_aircraft = {
        aircraft: tuple(
            route for route in routes if (aircraft, route) in capacity
        )
        for aircraft in aircraft_types
    }
    aircraft_by_route = {
        route: tuple(
            aircraft for aircraft in aircraft_types
            if (aircraft, route) in capacity
        )
        for route in routes
    }

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=aircraft_types, ordered=True)
    model.R = pyo.Set(initialize=routes, ordered=True)
    model.E = pyo.Set(
        dimen=2,
        within=model.A * model.R,
        initialize=assignment_pairs,
        ordered=True,
    )

    # Mutable parameters keep empty-sum constraints symbolic.
    model.availability = pyo.Param(
        model.A,
        initialize=availability,
        within=pyo.NonNegativeIntegers,
        mutable=True,
    )
    model.demand = pyo.Param(
        model.R,
        initialize=demand,
        within=pyo.NonNegativeReals,
        mutable=True,
    )
    model.capacity = pyo.Param(
        model.E,
        initialize=capacity,
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.E,
        initialize=cost,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.E, domain=pyo.NonNegativeIntegers)

    def availability_rule(block, aircraft):
        return (
            sum(
                block.x[aircraft, route]
                for route in routes_by_aircraft[aircraft]
            )
            <= block.availability[aircraft]
        )

    model.aircraft_limits = pyo.Constraint(
        model.A, rule=availability_rule
    )

    def demand_rule(block, route):
        return (
            sum(
                block.capacity[aircraft, route] * block.x[aircraft, route]
                for aircraft in aircraft_by_route[route]
            )
            >= block.demand[route]
        )

    model.route_coverage = pyo.Constraint(
        model.R, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[aircraft, route] * model.x[aircraft, route]
            for aircraft, route in model.E
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}