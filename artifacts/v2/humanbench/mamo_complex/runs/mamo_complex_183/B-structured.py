# IR: {"sets":{"centers":"1..6","stores":"1..9"},"params":{"opening_costs":"params['opening_costs'][center]","transport_costs":"params['transport_costs'][center][store]","demands":"params['demands'][store]","capacities":"params['capacities'][center]"},"variables":{"opened[center]":"binary","shipped[center,store]":"nonnegative continuous"},"constraints":["For each store: sum_center shipped[center,store] = demands[store].","For each center: sum_store shipped[center,store] <= capacities[center] * opened[center]."],"objective":"Minimize sum_center opening_costs[center]*opened[center] + sum_center,store transport_costs[center,store]*shipped[center,store]."}

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


def solve(params):
    """
    Solve the capacitated distribution-center location problem.

    Inputs may use ordinary sequences in center/store order or mappings
    keyed by one-based integer indices (or their string equivalents).
    transport_costs must contain one nested row per center.
    """
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 6)
    model.stores = pyo.RangeSet(1, 9)

    model.fixed_cost = pyo.Param(
        model.centers,
        initialize={
            center: _indexed(opening_costs, center)
            for center in model.centers
        },
    )
    model.shipping_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (center, store): _indexed(
                _indexed(transport_costs, center), store
            )
            for center in model.centers
            for store in model.stores
        },
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={
            store: _indexed(demands, store)
            for store in model.stores
        },
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={
            center: _indexed(capacities, center)
            for center in model.centers
        },
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, store):
        return (
            sum(
                instance.shipped[center, store]
                for center in instance.centers
            )
            == instance.store_demand[store]
        )

    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, center):
        return (
            sum(
                instance.shipped[center, store]
                for store in instance.stores
            )
            <= instance.center_capacity[center] * instance.opened[center]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[center] * model.opened[center]
                for center in model.centers
            )
            + sum(
                model.shipping_cost[center, store]
                * model.shipped[center, store]
                for center in model.centers
                for store in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    # APPsi HiGHS can raise RuntimeError when no feasible solution loads.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}