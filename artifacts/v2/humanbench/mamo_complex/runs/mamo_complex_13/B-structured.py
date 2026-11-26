# IR: {"sets":{"DC":"1..7","STORE":"1..6"},"params":{"opening_cost":"DC -> nonnegative real","transport_cost":"DC x STORE -> nonnegative real","demand":"STORE -> nonnegative real","capacity":"DC -> nonnegative real"},"variables":{"opened":"DC -> binary","shipment":"DC x STORE -> nonnegative real"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input sequences and a row-major cost matrix."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.DC = pyo.RangeSet(1, 7)
    model.STORE = pyo.RangeSet(1, 6)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize=lambda mdl, i: opening_cost[i - 1],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize=lambda mdl, i, j: transport_cost[i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize=lambda mdl, j: demand[j - 1],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize=lambda mdl, i: capacity[i - 1],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return sum(mdl.shipment[i, j] for i in mdl.DC) == mdl.demand[j]

    model.demand_balance = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.STORE)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.DC, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.opening_cost[i] * model.opened[i] for i in model.DC)
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}