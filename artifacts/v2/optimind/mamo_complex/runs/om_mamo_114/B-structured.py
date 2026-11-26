# IR: {"sets":{"I":"1..6","J":"1..8"},"params":{"opening_cost":"f[i], i in I","transport_cost":"c[i,j], (i,j) in I x J","demand":"d[j], j in J","capacity":"u[i], i in I"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["sum(shipment[i,j] for i in I) == d[j], for each j in J","sum(shipment[i,j] for j in J) <= u[i]*opened[i], for each i in I"],"objective":"minimize sum(f[i]*opened[i] for i in I) + sum(c[i,j]*shipment[i,j] for i in I for j in J)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position):
    """Accept ordered sequences or dictionaries keyed by one-based indices."""
    if isinstance(data, Mapping):
        return data[position]
    return data[position - 1]


def _matrix_entry(data, center, store):
    """Also accept a dictionary keyed by (center, store) tuples."""
    if isinstance(data, Mapping) and (center, store) in data:
        return data[(center, store)]
    return _entry(_entry(data, center), store)


def solve(params):
    """Build and solve the capacitated distribution-center location model."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(1, 6)
    model.stores = pyo.RangeSet(1, 8)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: _entry(opening_cost, center),
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, center, store: _matrix_entry(
            transport_cost, center, store
        ),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, store: _entry(demand, store),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: _entry(capacity, center),
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, store):
        return (
            sum(mdl.shipment[center, store] for center in mdl.centers)
            == mdl.demand[store]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, center):
        return (
            sum(mdl.shipment[center, store] for store in mdl.stores)
            <= mdl.capacity[center] * mdl.opened[center]
        )

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[center] * model.opened[center]
            for center in model.centers
        )
        + sum(
            model.transport_cost[center, store]
            * model.shipment[center, store]
            for center in model.centers
            for store in model.stores
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