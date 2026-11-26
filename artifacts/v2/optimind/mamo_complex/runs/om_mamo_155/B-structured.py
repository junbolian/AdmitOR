# IR: {"sets":{"C":"1..5","S":"1..9"},"params":{"opening_cost":"real[C]","transport_cost":"real[C,S]","demand":"nonnegative_real[S]","capacity":"nonnegative_real[C]"},"variables":{"opened":"binary[C]","shipment":"nonnegative_real[C,S]"},"constraints":["forall j in S: sum(i in C, shipment[i,j]) == demand[j]","forall i in C: sum(j in S, shipment[i,j]) <= capacity[i]*opened[i]"],"objective":"minimize sum(i in C, opening_cost[i]*opened[i]) + sum(i in C,j in S, transport_cost[i,j]*shipment[i,j])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position):
    """Read a one-based index from a mapping or a zero-based sequence."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def _matrix_entry(data, row, column):
    """Accept nested rows or mappings keyed by (row, column)."""
    if isinstance(data, Mapping) and (row, column) in data:
        return data[row, column]
    return _entry(_entry(data, row), column)


def solve(params):
    opening_cost_data = params["opening_cost"]
    transport_cost_data = params["transport_cost"]
    demand_data = params["demand"]
    capacity_data = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 5)
    model.stores = pyo.RangeSet(1, 9)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: _entry(opening_cost_data, i),
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, i, j: _matrix_entry(
            transport_cost_data, i, j
        ),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: _entry(demand_data, j),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: _entry(capacity_data, i),
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    model.demand_balance = pyo.Constraint(
        model.stores,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.centers
        ) == mdl.demand[j],
    )
    model.center_capacity = pyo.Constraint(
        model.centers,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.stores
        ) <= mdl.capacity[i] * mdl.opened[i],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[i] * model.opened[i]
            for i in model.centers
        ) + sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.centers
            for j in model.stores
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