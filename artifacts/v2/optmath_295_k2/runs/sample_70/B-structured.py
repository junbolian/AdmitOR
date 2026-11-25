# IR: {"sets":{"I":"0..12","J":"0..11"},"params":{"supply":"params['supply'][i], i in I","demand":"params['demand'][j], j in J","cost":"params['cost'][i][j], (i,j) in I x J"},"variables":{"x[i,j]":{"type":"continuous","domain":"nonnegative"}},"constraints":["sum(x[i,j] for j in J) == supply[i], for each i in I","sum(x[i,j] for i in I) == demand[j], for each j in J"],"objective":{"sense":"minimize","expression":"sum(cost[i,j]*x[i,j] for i in I for j in J)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 12)
    model.J = pyo.RangeSet(0, 11)

    model.supply = pyo.Param(
        model.I,
        initialize={i: params["supply"][i] for i in model.I},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: params["demand"][j] for j in model.J},
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.I) == mdl.demand[j]

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
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