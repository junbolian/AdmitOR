# IR: {"sets":{"centers":[0,1,2,3,4],"stores":[0,1,2,3,4]},"params":{"opening_cost":"vector[centers]","transport_cost":"matrix[centers,stores]","demand":"vector[stores]","capacity":"vector[centers]"},"variables":{"opened[center]":"binary","shipped[center,store]":"nonnegative continuous"},"constraints":["For each store: sum(shipped[center,store] for center in centers) = demand[store]","For each center: sum(shipped[center,store] for store in stores) <= capacity[center] * opened[center]"],"objective":"minimize sum(opening_cost[center] * opened[center] for center in centers) + sum(transport_cost[center,store] * shipped[center,store] for center in centers for store in stores)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=range(5), ordered=True)
    model.stores = pyo.Set(initialize=range(5), ordered=True)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={center: opening_cost[center] for center in model.centers},
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (center, store): transport_cost[center][store]
            for center in model.centers
            for store in model.stores
        },
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={store: demand[store] for store in model.stores},
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={center: capacity[center] for center in model.centers},
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(model, store):
        return (
            sum(model.shipped[center, store] for center in model.centers)
            == model.demand[store]
        )

    model.demand_constraints = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(model, center):
        return (
            sum(model.shipped[center, store] for store in model.stores)
            <= model.capacity[center] * model.opened[center]
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
            model.transport_cost[center, store] * model.shipped[center, store]
            for center in model.centers
            for store in model.stores
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