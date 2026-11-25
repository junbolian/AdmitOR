# IR: {"sets":{"I":"0..6","J":"0..5"},"params":{"supply":"supply[i]","demand":"demand[j]","cost":"cost[i][j]","cap":"cap[i][j]"},"variables":{"x[i,j]":"nonnegative continuous"},"constraints":["sum(j in J, x[i,j]) <= supply[i] for i in I","sum(i in I, x[i,j]) == demand[j] for j in J","x[i,j] <= cap[i][j] for i in I, j in J"],"objective":"minimize sum(i in I, j in J, cost[i][j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    cap = params["cap"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 6)
    model.J = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.I, initialize=lambda mdl, i: supply[i]
    )
    model.demand = pyo.Param(
        model.J, initialize=lambda mdl, j: demand[j]
    )
    model.cost = pyo.Param(
        model.I, model.J, initialize=lambda mdl, i, j: cost[i][j]
    )
    model.cap = pyo.Param(
        model.I, model.J, initialize=lambda mdl, i, j: cap[i][j]
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    model.supply_limits = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: (
            sum(mdl.x[i, j] for j in mdl.J) <= mdl.supply[i]
        ),
    )
    model.demand_requirements = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.x[i, j] for i in mdl.I) == mdl.demand[j]
        ),
    )
    model.transport_limits = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.cap[i, j],
    )

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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}