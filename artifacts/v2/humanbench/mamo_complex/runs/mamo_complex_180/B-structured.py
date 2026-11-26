# IR: {"sets":{"centers":"1..9","stores":"1..6"},"params":{"opening_cost":"center-indexed","transport_cost":"center/store-indexed","demand":"store-indexed","capacity":"center-indexed"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i]*opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from collections.abc import Mapping
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed(data, index):
    """Accept zero-based sequences or mappings keyed by 1-based integers/strings."""
    if isinstance(data, Mapping):
        return data[index] if index in data else data[str(index)]
    return data[index - 1]


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 9)
    model.stores = pyo.RangeSet(1, 6)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: _indexed(opening_cost, center),
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, center, store: _indexed(
            _indexed(transport_cost, center), store
        ),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, store: _indexed(demand, store),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: _indexed(capacity, center),
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
        expr=(
            sum(
                model.opening_cost[center] * model.opened[center]
                for center in model.centers
            )
            + sum(
                model.transport_cost[center, store]
                * model.shipment[center, store]
                for center in model.centers
                for store in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}