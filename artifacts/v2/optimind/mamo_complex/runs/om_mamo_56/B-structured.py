# IR: {"sets":{"I":"1..7","J":"1..4"},"params":{"opening_cost":"I -> dollars","transport_cost":"I x J -> dollars/unit","demand":"J -> units","capacity":"I -> units"},"variables":{"opened[i]":"binary, i in I","shipped[i,j]":"continuous >= 0, (i,j) in I x J"},"constraints":["sum(shipped[i,j] for i in I) == demand[j], j in J","sum(shipped[i,j] for j in J) <= capacity[i]*opened[i], i in I"],"objective":"minimize sum(opening_cost[i]*opened[i] for i in I) + sum(transport_cost[i,j]*shipped[i,j] for i in I for j in J)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(data, position):
    """Read a one-based mapping or an ordinary zero-based sequence."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def solve(params):
    opening_data = params["opening_cost"]
    transport_data = params["transport_cost"]
    demand_data = params["demand"]
    capacity_data = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 7)
    model.stores = pyo.RangeSet(1, 4)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={
            i: _indexed_value(opening_data, i)
            for i in model.centers
        },
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): _indexed_value(_indexed_value(transport_data, i), j)
            for i in model.centers
            for j in model.stores
        },
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={
            j: _indexed_value(demand_data, j)
            for j in model.stores
        },
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={
            i: _indexed_value(capacity_data, i)
            for i in model.centers
        },
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return sum(
            instance.shipped[i, j] for i in instance.centers
        ) == instance.demand[j]

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return sum(
            instance.shipped[i, j] for j in instance.stores
        ) <= instance.capacity[i] * instance.opened[i]

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[i] * model.opened[i]
            for i in model.centers
        )
        + sum(
            model.transport_cost[i, j] * model.shipped[i, j]
            for i in model.centers
            for j in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}