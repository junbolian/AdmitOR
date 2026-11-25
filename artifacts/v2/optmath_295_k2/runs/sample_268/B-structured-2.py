# IR: {"sets":{"I":"0..4 (origin_i)","J":"0..5 (destination_j)"},"params":{"supply":"supply[i]","demand":"demand[j]","cost":"cost[i,j]","capacity":"capacity[i,j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum_j shipment[i,j] = supply[i] for each i","sum_i shipment[i,j] = demand[j] for each j","shipment[i,j] <= capacity[i,j] for each i,j"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, label):
    """Accept sequences, integer-keyed mappings, or labeled mappings."""
    if isinstance(data, Mapping):
        if label in data:
            return data[label]
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position]


def _matrix_entry(data, origin, destination):
    """Accept nested matrices or mappings keyed by route tuples."""
    origin_label = f"origin_{origin}"
    destination_label = f"destination_{destination}"
    if isinstance(data, Mapping):
        if (origin_label, destination_label) in data:
            return data[origin_label, destination_label]
        if (origin, destination) in data:
            return data[origin, destination]
    row = _entry(data, origin, origin_label)
    return _entry(row, destination, destination_label)


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 4)
    model.destinations = pyo.RangeSet(0, 5)

    model.stock = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: _entry(supply, i, f"origin_{i}"),
    )
    model.requirement = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: _entry(demand, j, f"destination_{j}"),
    )
    model.unit_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: _matrix_entry(cost, i, j),
    )
    model.route_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: _matrix_entry(capacity, i, j),
    )

    model.shipment = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.destinations
        ) == mdl.stock[i],
    )
    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.origins
        ) == mdl.requirement[j],
    )
    model.capacity_limit = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: (
            mdl.shipment[i, j] <= mdl.route_capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
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