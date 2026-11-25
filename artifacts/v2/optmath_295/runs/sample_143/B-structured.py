# IR: {"sets":{"I":"0..7","J":"0..6"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"x[i,j]":{"type":"continuous","lower_bound":0}},"constraints":["sum_j x[i,j] = supply[i] for i in I","sum_i x[i,j] = demand[j] for j in J","x[i,j] <= capacity[i,j] for (i,j) in I x J"],"objective":{"sense":"minimize","expression":"sum_i sum_j cost[i,j] * x[i,j]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 7)
    model.J = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.I,
        initialize=lambda mdl, i: params["supply"][i],
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda mdl, j: params["demand"][j],
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: params["cost"][i][j],
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: params["capacity"][i][j],
    )

    model.x = pyo.Var(
        model.I,
        model.J,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: (
            sum(mdl.x[i, j] for j in mdl.J) == mdl.supply[i]
        ),
    )

    model.demand_balance = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.x[i, j] for i in mdl.I) == mdl.demand[j]
        ),
    )

    model.route_capacity = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.capacity[i, j],
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}