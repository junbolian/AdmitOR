# IR: {"sets":{"origins":"0..13","destinations":"0..11"},"params":{"supply":"nonnegative real[origins], from params['supply']","demand":"nonnegative real[destinations], from params['demand']","cost":"real[origins,destinations], from params['cost'][i][j]"},"variables":{"shipment[i,j]":"continuous nonnegative real"},"constraints":["sum_j shipment[i,j] <= supply[i] for each origin i","sum_i shipment[i,j] == demand[j] for each destination j"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 13)
    model.destinations = pyo.RangeSet(0, 11)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda model, i: params["supply"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda model, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda model, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.destinations)
            <= model.supply[i]
        )

    model.supply_limits = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.origins)
            == model.demand[j]
        )

    model.demand_requirements = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}