# IR: {"sets":{"I":"aircraft_0,...,aircraft_5","J":"route_0,...,route_6"},"params":{"availability":"params['availability'][i], required for every i","demand":"params['demand'][j], required for every j","capacity":"params['capacity'][i,j], required for every pair; unknown entries cannot be inferred","cost":"params['cost'][i,j], required for every pair; unknown entries cannot be inferred"},"variables":{"x[i,j]":"nonnegative integer"},"constraints":["sum(x[i,j] for j in J) <= availability[i] for each i in I","sum(capacity[i,j]*x[i,j] for i in I) >= demand[j] for each j in J"],"objective":"minimize sum(cost[i,j]*x[i,j] for i in I for j in J)"}

import ast
import json
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


class MissingDataError(Exception):
    """A required parameter entry is absent or explicitly unknown."""


def _require_value(value):
    if value is None:
        raise MissingDataError
    if isinstance(value, str):
        if value.strip().lower() in {
            "", "?", "unknown", "none", "null", "nan", "n/a"
        }:
            raise MissingDataError
    return value


def _vector_entry(data, position, label):
    """Read labeled, integer-keyed, string-integer-keyed, or sequence data."""
    if data is None:
        raise MissingDataError

    if isinstance(data, Mapping):
        for key in (label, position, str(position)):
            if key in data:
                return _require_value(data[key])
        raise MissingDataError

    try:
        return _require_value(data[position])
    except IndexError as exc:
        raise MissingDataError from exc


def _coordinate_keys(row_position, column_position, row_label, column_label):
    return (
        (row_label, column_label),
        (row_position, column_position),
        (str(row_position), str(column_position)),
    )


def _normalize_matrix_keys(data):
    """Recognize flat tuple keys serialized as JSON arrays or Python tuples."""
    if not isinstance(data, Mapping):
        return data

    normalized = dict(data)
    for key, value in data.items():
        if not isinstance(key, str):
            continue

        text = key.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                coordinates = json.loads(text)
            except json.JSONDecodeError:
                continue
        elif text.startswith("(") and text.endswith(")"):
            try:
                coordinates = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                continue
        else:
            continue

        if (
            isinstance(coordinates, (list, tuple))
            and len(coordinates) == 2
            and all(isinstance(item, (str, int)) for item in coordinates)
        ):
            normalized.setdefault(tuple(coordinates), value)

    return normalized


def _matrix_entry(data, row_position, column_position, row_label, column_label):
    """Read nested matrices or flat coordinate-keyed mappings."""
    if data is None:
        raise MissingDataError

    if isinstance(data, Mapping):
        for key in _coordinate_keys(
            row_position, column_position, row_label, column_label
        ):
            if key in data:
                return _require_value(data[key])

        for row_key, column_key in (
            (row_label, column_label),
            (str(row_position), str(column_position)),
        ):
            for separator in (",", ", ", "|", ":"):
                key = f"{row_key}{separator}{column_key}"
                if key in data:
                    return _require_value(data[key])

    row = _vector_entry(data, row_position, row_label)
    return _vector_entry(row, column_position, column_label)


def solve(params):
    aircraft = tuple(f"aircraft_{idx}" for idx in range(6))
    routes = tuple(f"route_{idx}" for idx in range(7))

    # All coefficients must come from params. If only the first two aircraft
    # rows are supplied, the full six-type problem is under-specified.
    # Missing rows must not be guessed, zero-filled, or silently excluded.
    try:
        availability_data = params["availability"]
        demand_data = params["demand"]
        capacity_data = _normalize_matrix_keys(params["capacity"])
        cost_data = _normalize_matrix_keys(params["cost"])
    except KeyError:
        return {"objective": None, "status": "missing_parameter"}

    try:
        availability_values = {
            label: _vector_entry(availability_data, idx, label)
            for idx, label in enumerate(aircraft)
        }
    except MissingDataError:
        return {"objective": None, "status": "incomplete_availability"}

    try:
        demand_values = {
            label: _vector_entry(demand_data, idx, label)
            for idx, label in enumerate(routes)
        }
    except MissingDataError:
        return {"objective": None, "status": "incomplete_demand"}

    try:
        capacity_values = {
            (aircraft_label, route_label): _matrix_entry(
                capacity_data,
                aircraft_idx,
                route_idx,
                aircraft_label,
                route_label,
            )
            for aircraft_idx, aircraft_label in enumerate(aircraft)
            for route_idx, route_label in enumerate(routes)
        }
    except MissingDataError:
        return {"objective": None, "status": "incomplete_capacity"}

    try:
        cost_values = {
            (aircraft_label, route_label): _matrix_entry(
                cost_data,
                aircraft_idx,
                route_idx,
                aircraft_label,
                route_label,
            )
            for aircraft_idx, aircraft_label in enumerate(aircraft)
            for route_idx, route_label in enumerate(routes)
        }
    except MissingDataError:
        return {"objective": None, "status": "incomplete_cost"}

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=aircraft, ordered=True)
    model.J = pyo.Set(initialize=routes, ordered=True)

    model.availability = pyo.Param(
        model.I, initialize=availability_values, within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.J, initialize=demand_values, within=pyo.NonNegativeReals
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize=capacity_values,
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I, model.J, initialize=cost_values, within=pyo.Reals
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)

    def availability_rule(problem, aircraft_label):
        return (
            sum(
                problem.x[aircraft_label, route_label]
                for route_label in problem.J
            )
            <= problem.availability[aircraft_label]
        )

    model.availability_limit = pyo.Constraint(
        model.I, rule=availability_rule
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

    model.demand_requirement = pyo.Constraint(
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

    # Appsi HiGHS raises RuntimeError when no feasible solution can be loaded.
    # Regardless of that exception, success depends only on objective retrieval.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}