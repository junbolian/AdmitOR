# IR: {"sets":{"centers":"1..5","stores":"1..9"},"params":{"opening_cost":"centers -> USD","transport_cost":"centers x stores -> USD/unit","demand":"stores -> units","capacity":"centers -> units"},"variables":{"opened[c]":"binary","shipped[c,s]":"nonnegative continuous"},"constraints":["For each store s: sum_c shipped[c,s] = demand[s]","For each center c: sum_s shipped[c,s] <= capacity[c] * opened[c]"],"objective":"Minimize sum_c opening_cost[c]*opened[c] + sum_c,s transport_cost[c,s]*shipped[c,s]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(data, position):
    """Read a zero-based sequence or a mapping keyed by 1-based indices."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 5)
    model.stores = pyo.RangeSet(1, 9)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda _, center: _indexed_value(opening_cost, center),
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda _, center, store: _indexed_value(
            _indexed_value(transport_cost, center), store
        ),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda _, store: _indexed_value(demand, store),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda _, center: _indexed_value(capacity, center),
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, store):
        return (
            sum(instance.shipped[center, store] for center in instance.centers)
            == instance.demand[store]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, center):
        return (
            sum(instance.shipped[center, store] for store in instance.stores)
            <= instance.capacity[center] * instance.opened[center]
        )

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[center] * model.opened[center]
                for center in model.centers
            )
            + sum(
                model.transport_cost[center, store]
                * model.shipped[center, store]
                for center in model.centers
                for store in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise RuntimeError when no feasible solution can be loaded.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    # Success depends solely on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}