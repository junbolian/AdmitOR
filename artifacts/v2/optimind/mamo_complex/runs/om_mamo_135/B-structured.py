# IR: {"sets":{"centers":"1..4","stores":"1..6"},"params":{"opening_costs":"cost[center]","transport_costs":"cost[center,store]","demands":"demand[store]","capacities":"capacity[center]"},"variables":{"opened[center]":"Binary","shipped[center,store]":"NonNegativeReals"},"constraints":["For each store: sum_center shipped[center,store] = demands[store]","For each center: sum_store shipped[center,store] <= capacities[center]*opened[center]"],"objective":"Minimize sum_center opening_costs[center]*opened[center] + sum_center,store transport_costs[center,store]*shipped[center,store]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using arrays ordered by center/store, with zero-based input indices."""
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 4)
    model.stores = pyo.RangeSet(1, 6)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={center: opening_costs[center - 1] for center in model.centers},
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (center, store): transport_costs[center - 1][store - 1]
            for center in model.centers
            for store in model.stores
        },
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={store: demands[store - 1] for store in model.stores},
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={center: capacities[center - 1] for center in model.centers},
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(network, store):
        return (
            sum(network.shipped[center, store] for center in network.centers)
            == network.store_demand[store]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(network, center):
        return (
            sum(network.shipped[center, store] for store in network.stores)
            <= network.center_capacity[center] * network.opened[center]
        )

    model.capacity_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[center] * model.opened[center]
            for center in model.centers
        )
        + sum(
            model.transport_cost[center, store] * model.shipped[center, store]
            for center in model.centers
            for store in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}