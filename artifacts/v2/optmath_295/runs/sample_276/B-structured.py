# IR: {"sets":{"A":"aircraft_0..aircraft_6","R":"route_0..route_5"},"params":{"capacity_demand":"R -> nonnegative real","aircraft_availability":"A -> nonnegative real","capacity_contribution":"A x R -> nonnegative real","assignment_cost":"A x R -> real"},"variables":{"x[a,r]":"nonnegative integer"},"constraints":["For each r in R: sum(a in A, capacity_contribution[a,r]*x[a,r]) >= capacity_demand[r]","For each a in A: sum(r in R, x[a,r]) <= aircraft_availability[a]"],"objective":"minimize sum(a in A, r in R, assignment_cost[a,r]*x[a,r])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, label, position):
    """Read a vector entry from a sequence or a keyed mapping."""
    if isinstance(data, Mapping) and label in data:
        return data[label]
    return data[position]


def _matrix_entry(data, aircraft, route, aircraft_idx, route_idx):
    """Read a matrix entry from nested data or a tuple-keyed mapping."""
    if isinstance(data, Mapping):
        if (aircraft, route) in data:
            return data[aircraft, route]
        if (aircraft_idx, route_idx) in data:
            return data[aircraft_idx, route_idx]

    row = _entry(data, aircraft, aircraft_idx)
    return _entry(row, route, route_idx)


def solve(params):
    demand_input = params["capacity_demand"]
    availability_input = params["aircraft_availability"]
    contribution_input = params["capacity_contribution"]
    cost_input = params["assignment_cost"]

    aircraft_labels = tuple(f"aircraft_{idx}" for idx in range(7))
    route_labels = tuple(f"route_{idx}" for idx in range(6))

    demand_data = {
        route: _entry(demand_input, route, route_idx)
        for route_idx, route in enumerate(route_labels)
    }
    availability_data = {
        aircraft: _entry(availability_input, aircraft, aircraft_idx)
        for aircraft_idx, aircraft in enumerate(aircraft_labels)
    }
    contribution_data = {
        (aircraft, route): _matrix_entry(
            contribution_input, aircraft, route, aircraft_idx, route_idx
        )
        for aircraft_idx, aircraft in enumerate(aircraft_labels)
        for route_idx, route in enumerate(route_labels)
    }
    cost_data = {
        (aircraft, route): _matrix_entry(
            cost_input, aircraft, route, aircraft_idx, route_idx
        )
        for aircraft_idx, aircraft in enumerate(aircraft_labels)
        for route_idx, route in enumerate(route_labels)
    }

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft_labels, ordered=True)
    model.R = pyo.Set(initialize=route_labels, ordered=True)

    model.capacity_demand = pyo.Param(
        model.R, initialize=demand_data, within=pyo.NonNegativeReals
    )
    model.aircraft_availability = pyo.Param(
        model.A, initialize=availability_data, within=pyo.NonNegativeReals
    )
    model.capacity_contribution = pyo.Param(
        model.A,
        model.R,
        initialize=contribution_data,
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.A, model.R, initialize=cost_data, within=pyo.Reals
    )

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def capacity_rule(instance, route):
        return (
            sum(
                instance.capacity_contribution[aircraft, route]
                * instance.x[aircraft, route]
                for aircraft in instance.A
            )
            >= instance.capacity_demand[route]
        )

    model.capacity_requirement = pyo.Constraint(model.R, rule=capacity_rule)

    def availability_rule(instance, aircraft):
        return (
            sum(instance.x[aircraft, route] for route in instance.R)
            <= instance.aircraft_availability[aircraft]
        )

    model.availability_limit = pyo.Constraint(model.A, rule=availability_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[aircraft, route] * model.x[aircraft, route]
            for aircraft in model.A
            for route in model.R
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        # A solver exception does not bypass the required objective check.
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}