# IR: {"sets":{"centers":"0..5","stores":"0..6"},"params":{"opening_cost":"params['opening_cost'][i]","transport_cost":"params['transport_cost'][i][j]","demand":"params['demand'][j]","capacity":"params['capacity'][i]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["sum_i shipment[i,j] == demand[j] for each store j","sum_j shipment[i,j] <= capacity[i]*opened[i] for each center i"],"objective":"minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 5)
    model.stores = pyo.RangeSet(0, 6)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={
            i: params["opening_cost"][i]
            for i in model.centers
        },
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): params["transport_cost"][i][j]
            for i in model.centers
            for j in model.stores
        },
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={
            j: params["demand"][j]
            for j in model.stores
        },
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={
            i: params["capacity"][i]
            for i in model.centers
        },
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.centers)
            == mdl.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.stores,
        rule=demand_rule,
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers,
        rule=capacity_rule,
    )

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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}