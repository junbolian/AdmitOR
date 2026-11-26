# IR: {"sets":{"centers":"0..3","stores":"0..7"},"params":{"opening_cost":"params['opening_cost'][i]","transport_cost":"params['transport_cost'][i][j]","demand":"params['demand'][j]","capacity":"params['capacity'][i]"},"variables":{"opened[i]":"binary","shipped[i,j]":"continuous, nonnegative"},"constraints":["For each store j: sum_i shipped[i,j] = demand[j]","For each center i: sum_j shipped[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipped[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 3)
    model.stores = pyo.RangeSet(0, 7)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={
            center: params["opening_cost"][center]
            for center in model.centers
        },
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (center, store): params["transport_cost"][center][store]
            for center in model.centers
            for store in model.stores
        },
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={
            store: params["demand"][store]
            for store in model.stores
        },
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={
            center: params["capacity"][center]
            for center in model.centers
        },
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
            == instance.demand[store]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, center):
        return (
            sum(
                instance.shipped[center, store]
                for store in instance.stores
            )
            <= instance.capacity[center] * instance.opened[center]
        )

    model.center_capacity = pyo.Constraint(
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

    # APPSI raises RuntimeError when a feasible solution cannot be loaded.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    # Determine success solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}