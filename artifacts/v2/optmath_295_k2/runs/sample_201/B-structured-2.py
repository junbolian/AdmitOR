# IR: {"sets":{"I":"aircraft_0..aircraft_5","J":"route_0..route_6"},"params":{"availability":"nonnegative real[I], from params['availability']","demand":"nonnegative real[J], from params['demand']","capacity":"nonnegative real[I,J], all entries required from params['capacity']","cost":"real[I,J], all entries required from params['cost']"},"variables":{"x[I,J]":"nonnegative integer"},"constraints":["For each i in I: sum(x[i,j] for j in J) <= availability[i]","For each j in J: sum(capacity[i,j]*x[i,j] for i in I) >= demand[j]"],"objective":"minimize sum(cost[i,j]*x[i,j] for i in I for j in J)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


class MissingParameterError(Exception):
    """An essential input coefficient is absent."""


def _lookup(data, position, label):
    """Read a sequence or mapping with label, integer, or string-index keys."""
    if isinstance(data, Mapping):
        for key in (label, position, str(position)):
            if key in data:
                return data[key]
        raise KeyError(label)

    return data[position]


def _matrix_lookup(data, row_position, column_position, row_label, column_label):
    """Accept nested matrices, tuple-keyed mappings, or flat row-major arrays."""
    if isinstance(data, Mapping):
        candidate_keys = (
            (row_label, column_label),
            (row_position, column_position),
            (str(row_position), str(column_position)),
        )
        for key in candidate_keys:
            if key in data:
                return data[key]
    elif len(data) == 6 * 7:
        return data[row_position * 7 + column_position]

    row = _lookup(data, row_position, row_label)
    return _lookup(row, column_position, column_label)


def _read_vector(data, labels, parameter_name):
    result = {}
    for position, label in enumerate(labels):
        try:
            value = _lookup(data, position, label)
        except (KeyError, IndexError):
            raise MissingParameterError(
                f"missing_{parameter_name}_{label}"
            ) from None

        if value is None:
            raise MissingParameterError(f"missing_{parameter_name}_{label}")

        result[label] = value
    return result


def _read_matrix(data, aircraft, routes, parameter_name):
    result = {}
    for aircraft_position, aircraft_label in enumerate(aircraft):
        for route_position, route_label in enumerate(routes):
            try:
                value = _matrix_lookup(
                    data,
                    aircraft_position,
                    route_position,
                    aircraft_label,
                    route_label,
                )
            except (KeyError, IndexError):
                raise MissingParameterError(
                    f"missing_{parameter_name}_{aircraft_label}_{route_label}"
                ) from None

            if value is None:
                raise MissingParameterError(
                    f"missing_{parameter_name}_{aircraft_label}_{route_label}"
                )

            result[aircraft_label, route_label] = value
    return result


def solve(params):
    aircraft = tuple(f"aircraft_{position}" for position in range(6))
    routes = tuple(f"route_{position}" for position in range(7))

    # Unknown coefficients cannot be reconstructed from the problem statement.
    # All 42 capacity entries and all 42 cost entries must be supplied.
    # Missing entries are never replaced with zero or invented values.
    for parameter_name in ("availability", "demand", "capacity", "cost"):
        if parameter_name not in params or params[parameter_name] is None:
            return {
                "objective": None,
                "status": f"missing_{parameter_name}",
            }

    try:
        availability = _read_vector(
            params["availability"], aircraft, "availability"
        )
        demand = _read_vector(params["demand"], routes, "demand")
        capacity = _read_matrix(
            params["capacity"], aircraft, routes, "capacity"
        )
        cost = _read_matrix(params["cost"], aircraft, routes, "cost")
    except MissingParameterError as error:
        return {"objective": None, "status": str(error)}

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=aircraft, ordered=True)
    model.J = pyo.Set(initialize=routes, ordered=True)

    model.availability = pyo.Param(
        model.I,
        initialize=availability,
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize=demand,
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize=capacity,
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=cost,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.I,
        model.J,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(problem, aircraft_label):
        return (
            sum(
                problem.x[aircraft_label, route_label]
                for route_label in problem.J
            )
            <= problem.availability[aircraft_label]
        )

    def demand_rule(problem, route_label):
        return (
            sum(
                problem.capacity[aircraft_label, route_label]
                * problem.x[aircraft_label, route_label]
                for aircraft_label in problem.I
            )
            >= problem.demand[route_label]
        )

    model.availability_limits = pyo.Constraint(
        model.I, rule=availability_rule
    )
    model.demand_requirements = pyo.Constraint(
        model.J, rule=demand_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[aircraft_label, route_label]
            * model.x[aircraft_label, route_label]
            for aircraft_label in model.I
            for route_label in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this specific error when it cannot load a solution.
        # Other runtime errors are unexpected and must propagate.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}