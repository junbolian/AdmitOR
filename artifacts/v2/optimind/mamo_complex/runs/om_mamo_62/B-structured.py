# IR: {"sets":{"C":"1..params['num_centers']","S":"1..params['num_stores']"},"params":{"opening_costs":"nonnegative cost[C]","transport_costs":"nonnegative cost[C,S]","demands":"nonnegative demand[S]","capacities":"nonnegative capacity[C]","num_centers":"positive integer","num_stores":"positive integer"},"variables":{"opened[C]":"binary","shipment[C,S]":"nonnegative continuous"},"constraints":["For each s in S: sum(shipment[c,s] for c in C) == demands[s]","For each c in C: sum(shipment[c,s] for s in S) <= capacities[c]*opened[c]"],"objective":"minimize sum(opening_costs[c]*opened[c] for c in C) + sum(transport_costs[c,s]*shipment[c,s] for c in C for s in S)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed(data, position):
    """Accept zero-based sequences or mappings with one-based integer/string keys."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    num_centers = params["num_centers"]
    num_stores = params["num_stores"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, num_centers)
    model.stores = pyo.RangeSet(1, num_stores)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: _indexed(opening_costs, center),
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, center, store: _indexed(
            _indexed(transport_costs, center), store
        ),
        within=pyo.NonNegativeReals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, store: _indexed(demands, store),
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: _indexed(capacities, center),
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, store):
        return (
            sum(mdl.shipment[center, store] for center in mdl.centers)
            == mdl.store_demand[store]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, center):
        return (
            sum(mdl.shipment[center, store] for store in mdl.stores)
            <= mdl.center_capacity[center] * mdl.opened[center]
        )

    model.capacity_link = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[center] * model.opened[center]
            for center in model.centers
        )
        + sum(
            model.transport_cost[center, store] * model.shipment[center, store]
            for center in model.centers
            for store in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when no feasible solution can be loaded.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}