# IR: {"sets":{"DC":[1,2,3,4,5],"STORE":[1,2,3,4,5,6]},"params":{"opening_cost":"DC -> real","transport_cost":"DC x STORE -> real","demand":"STORE -> nonnegative real","capacity":"DC -> nonnegative real"},"variables":{"open_dc":"DC -> binary","shipment":"DC x STORE -> nonnegative real"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each DC i: sum_j shipment[i,j] <= capacity[i] * open_dc[i]"],"objective":"Minimize sum_i opening_cost[i]*open_dc[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed(data, position):
    """Read a one-based mapping or a zero-based sequence."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def _matrix_entry(data, row, column):
    """Support nested sequences/mappings and tuple-keyed mappings."""
    if isinstance(data, Mapping) and (row, column) in data:
        return data[(row, column)]
    return _indexed(_indexed(data, row), column)


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.DC = pyo.RangeSet(1, 5)
    model.STORE = pyo.RangeSet(1, 6)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize=lambda mdl, dc: _indexed(opening_cost, dc),
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize=lambda mdl, dc, store: _matrix_entry(
            transport_cost, dc, store
        ),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize=lambda mdl, store: _indexed(demand, store),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize=lambda mdl, dc: _indexed(capacity, dc),
        within=pyo.NonNegativeReals,
    )

    model.open_dc = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, store):
        return (
            sum(mdl.shipment[dc, store] for dc in mdl.DC)
            == mdl.demand[store]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(mdl, dc):
        return (
            sum(mdl.shipment[dc, store] for store in mdl.STORE)
            <= mdl.capacity[dc] * mdl.open_dc[dc]
        )

    model.capacity_limit = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[dc] * model.open_dc[dc]
                for dc in model.DC
            )
            + sum(
                model.transport_cost[dc, store]
                * model.shipment[dc, store]
                for dc in model.DC
                for store in model.STORE
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}