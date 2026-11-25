# IR: {"sets":{"A":["aircraft_0","aircraft_1","aircraft_2","aircraft_3","aircraft_4"],"R":["route_0","route_1","route_2","route_3","route_4","route_5"],"E":"Pairs (a,r) with both capacity[a,r] and cost[a,r] provided and non-null"},"params":{"availability":"Required nonnegative availability[a] from params['availability']","demand":"Required nonnegative demand[r] from params['demand']","capacity":"Nonnegative capacity[a,r] from params['capacity'], for (a,r) in E","cost":"Real cost[a,r] from params['cost'], for (a,r) in E"},"decision_variables":{"x[a,r]":"Nonnegative integer, for (a,r) in E"},"constraints":["For each a in A: sum(x[a,r] for (a,r) in E) <= availability[a]","For each r in R: sum(capacity[a,r]*x[a,r] for (a,r) in E) >= demand[r]"],"objective":"Minimize sum(cost[a,r]*x[a,r] for (a,r) in E)","missing_data_policy":"Treat pairs lacking capacity or cost as unavailable assignments; do not impute coefficients. Return missing_data only for absent required top-level parameters, availability entries, or demand entries."}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


_MISSING = object()


def _vector_entry(data, label, position):
    """Read a labeled or positional vector, allowing sparse mappings."""
    if data is None:
        return _MISSING

    if isinstance(data, Mapping):
        for key in (label, position, str(position)):
            if key in data:
                return data[key]
        return _MISSING

    try:
        return data[position]
    except (IndexError, KeyError):
        return _MISSING


def _matrix_entry(data, aircraft, route, aircraft_position, route_position):
    """Read a sparse pair-keyed mapping or nested rows."""
    if data is None:
        return _MISSING

    if isinstance(data, Mapping):
        for key in (
            (aircraft, route),
            (aircraft_position, route_position),
            (str(aircraft_position), str(route_position)),
        ):
            if key in data:
                return data[key]

    row = _vector_entry(data, aircraft, aircraft_position)
    if row is _MISSING or row is None:
        return _MISSING

    return _vector_entry(row, route, route_position)


def solve(params):
    aircraft_types = [f"aircraft_{position}" for position in range(5)]
    routes = [f"route_{position}" for position in range(6)]

    try:
        availability_data = params["availability"]
        demand_data = params["demand"]
        capacity_data = params["capacity"]
        cost_data = params["cost"]
    except KeyError:
        return {"objective": None, "status": "missing_data"}

    availability = {
        aircraft: _vector_entry(availability_data, aircraft, position)
        for position, aircraft in enumerate(aircraft_types)
    }
    demand = {
        route: _vector_entry(demand_data, route, position)
        for position, route in enumerate(routes)
    }

    if any(
        value is _MISSING or value is None
        for collection in (availability, demand)
        for value in collection.values()
    ):
        return {"objective": None, "status": "missing_data"}

    capacity = {}
    cost = {}

    # Sparse-data convention: only fully specified assignments are allowed.
    for aircraft_position, aircraft in enumerate(aircraft_types):
        for route_position, route in enumerate(routes):
            capacity_value = _matrix_entry(
                capacity_data,
                aircraft,
                route,
                aircraft_position,
                route_position,
            )
            cost_value = _matrix_entry(
                cost_data,
                aircraft,
                route,
                aircraft_position,
                route_position,
            )

            if (
                capacity_value is _MISSING
                or capacity_value is None
                or cost_value is _MISSING
                or cost_value is None
            ):
                continue

            capacity[aircraft, route] = capacity_value
            cost[aircraft, route] = cost_value

    assignment_pairs = list(capacity)
    routes_by_aircraft = {
        aircraft: [
            route
            for candidate_aircraft, route in assignment_pairs
            if candidate_aircraft == aircraft
        ]
        for aircraft in aircraft_types
    }
    aircraft_by_route = {
        route: [
            aircraft
            for aircraft, candidate_route in assignment_pairs
            if candidate_route == route
        ]
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

    model.availability = pyo.Param(
        model.A,
        initialize=availability,
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.R,
        initialize=demand,
        within=pyo.NonNegativeReals,
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

    def availability_rule(instance, aircraft):
        assigned = pyo.quicksum(
            instance.x[aircraft, route]
            for route in routes_by_aircraft[aircraft]
        )
        # Tuple form also supports aircraft with no allowed assignments.
        return (None, assigned, instance.availability[aircraft])

    def demand_rule(instance, route):
        supplied = pyo.quicksum(
            instance.capacity[aircraft, route] * instance.x[aircraft, route]
            for aircraft in aircraft_by_route[route]
        )
        # An uncovered route with positive demand correctly makes this infeasible.
        return (instance.demand[route], supplied, None)

    model.availability_constraints = pyo.Constraint(
        model.A, rule=availability_rule
    )
    model.demand_constraints = pyo.Constraint(
        model.R, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.cost[aircraft, route] * model.x[aircraft, route]
            for aircraft, route in model.E
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}