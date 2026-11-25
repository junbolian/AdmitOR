# IR: {"sets":{"I":["aircraft_0","aircraft_1","aircraft_2","aircraft_3","aircraft_4"],"J":["route_0","route_1","route_2","route_3","route_4","route_5","route_6"]},"params":{"availability":"nonnegative real[I], from params","demand":"nonnegative real[J], from params","cost":"real[I,J], from params","capacity":"nonnegative real[I,J], from params"},"variables":{"x":"nonnegative integer[I,J]"},"constraints":["forall i in I: sum(j in J, x[i,j]) <= availability[i]","forall j in J: sum(i in I, capacity[i,j]*x[i,j]) >= demand[j]"],"objective":"minimize sum(i in I, j in J, cost[i,j]*x[i,j])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, label):
    """Accept positional sequences or dictionaries keyed by label or position."""
    if isinstance(data, Mapping):
        if label in data:
            return data[label]
        return data[position]
    return data[position]


def _matrix_entry(data, row_position, row_label, col_position, col_label):
    """Accept nested matrices or dictionaries keyed by index pairs."""
    if isinstance(data, Mapping):
        if (row_label, col_label) in data:
            return data[row_label, col_label]
        if (row_position, col_position) in data:
            return data[row_position, col_position]
    row = _entry(data, row_position, row_label)
    return _entry(row, col_position, col_label)


def solve(params):
    aircraft = tuple(f"aircraft_{i}" for i in range(5))
    routes = tuple(f"route_{j}" for j in range(7))

    availability_data = params["availability"]
    demand_data = params["demand"]
    cost_data = params["cost"]
    capacity_data = params["capacity"]

    availability = {
        label: _entry(availability_data, i, label)
        for i, label in enumerate(aircraft)
    }
    demand = {
        label: _entry(demand_data, j, label)
        for j, label in enumerate(routes)
    }
    cost = {
        (aircraft_label, route_label): _matrix_entry(
            cost_data, i, aircraft_label, j, route_label
        )
        for i, aircraft_label in enumerate(aircraft)
        for j, route_label in enumerate(routes)
    }
    capacity = {
        (aircraft_label, route_label): _matrix_entry(
            capacity_data, i, aircraft_label, j, route_label
        )
        for i, aircraft_label in enumerate(aircraft)
        for j, route_label in enumerate(routes)
    }

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=aircraft, ordered=True)
    model.J = pyo.Set(initialize=routes, ordered=True)

    model.availability = pyo.Param(
        model.I, initialize=availability, within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.J, initialize=demand, within=pyo.NonNegativeReals
    )
    model.cost = pyo.Param(
        model.I, model.J, initialize=cost, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.I, model.J, initialize=capacity, within=pyo.NonNegativeReals
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)

    def availability_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) <= mdl.availability[i]

    model.availability_limits = pyo.Constraint(
        model.I, rule=availability_rule
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.capacity[i, j] * mdl.x[i, j] for i in mdl.I)
            >= mdl.demand[j]
        )

    model.demand_requirements = pyo.Constraint(model.J, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
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
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}