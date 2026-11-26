# IR: {"sets":{"DC":"0..5","STORE":"0..4"},"params":{"opening_cost":"DC vector","transport_cost":"DC x STORE matrix","demand":"STORE vector","capacity":"DC vector"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each j: sum_i shipment[i,j] = demand[j]","For each i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the distribution network problem using zero-based input sequences."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.DC = pyo.RangeSet(0, 5)
    model.STORE = pyo.RangeSet(0, 4)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize={i: opening_cost[i] for i in model.DC},
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.DC
            for j in model.STORE
        },
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize={j: demand[j] for j in model.STORE},
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize={i: capacity[i] for i in model.DC},
    )

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(current_model, j):
        return (
            sum(current_model.shipment[i, j] for i in current_model.DC)
            == current_model.demand[j]
        )

    model.demand_met = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(current_model, i):
        return (
            sum(current_model.shipment[i, j] for j in current_model.STORE)
            <= current_model.capacity[i] * current_model.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.DC, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.DC
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.DC
                for j in model.STORE
            )
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