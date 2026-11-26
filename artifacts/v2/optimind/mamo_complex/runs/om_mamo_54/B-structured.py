# IR: {"sets":{"centers":"0..8","stores":"0..6"},"params":{"opening_cost":"nonnegative real[centers] from params","transport_cost":"nonnegative real[centers,stores] from params","demand":"nonnegative real[stores] from params","capacity":"nonnegative real[centers] from params"},"variables":{"opened":"binary[centers]","shipment":"nonnegative real[centers,stores]"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i]*opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 8)
    model.stores = pyo.RangeSet(0, 6)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={i: params["opening_cost"][i] for i in model.centers},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): params["transport_cost"][i][j]
            for i in model.centers
            for j in model.stores
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={j: params["demand"][j] for j in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={i: params["capacity"][i] for i in model.centers},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return sum(mdl.shipment[i, j] for i in mdl.centers) == mdl.demand[j]

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.supply_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
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