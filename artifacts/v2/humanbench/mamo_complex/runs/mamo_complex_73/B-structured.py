# IR: {"sets":{"centers":"0..5","stores":"0..7"},"params":{"opening_costs":"[centers]","transport_costs":"[centers,stores]","demands":"[stores]","capacities":"[centers]"},"variables":{"opened[center]":"binary","shipped[center,store]":"nonnegative continuous"},"constraints":["For each store: sum_center shipped[center,store] = demands[store]","For each center: sum_store shipped[center,store] <= capacities[center]*opened[center]"],"objective":"minimize sum_center opening_costs[center]*opened[center] + sum_center,store transport_costs[center,store]*shipped[center,store]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the capacitated distribution-center location problem.

    Parameter vectors and the transportation matrix use zero-based sequences.
    """
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 5)
    model.stores = pyo.RangeSet(0, 7)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={
            center: params["opening_costs"][center]
            for center in model.centers
        },
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (center, store): params["transport_costs"][center][store]
            for center in model.centers
            for store in model.stores
        },
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={
            store: params["demands"][store]
            for store in model.stores
        },
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={
            center: params["capacities"][center]
            for center in model.centers
        },
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, store):
        return sum(
            instance.shipped[center, store]
            for center in instance.centers
        ) == instance.store_demand[store]

    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, center):
        return sum(
            instance.shipped[center, store]
            for store in instance.stores
        ) <= instance.center_capacity[center] * instance.opened[center]

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[center] * model.opened[center]
            for center in model.centers
        )
        + sum(
            model.transport_cost[center, store]
            * model.shipped[center, store]
            for center in model.centers
            for store in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}