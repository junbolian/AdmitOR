# IR: {"sets":{"I":"0..4","J":"0..5","P":"0..1"},"params":{"supply":"[I,P]","demand":"[J,P]","transport_cost":"[I,J,P]","shipping_capacity":"[I,J]"},"variables":{"x[I,J,P]":"nonnegative continuous"},"constraints":["sum_j x[i,j,p] <= supply[i,p] for each i,p","sum_i x[i,j,p] == demand[j,p] for each j,p","sum_p x[i,j,p] <= shipping_capacity[i,j] for each i,j"],"objective":"minimize sum_i,j,p transport_cost[i,j,p] * x[i,j,p]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 4)
    model.J = pyo.RangeSet(0, 5)
    model.P = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.I,
        model.P,
        initialize=lambda mdl, i, p: params["supply"][i][p],
    )
    model.demand = pyo.Param(
        model.J,
        model.P,
        initialize=lambda mdl, j, p: params["demand"][j][p],
    )
    model.transport_cost = pyo.Param(
        model.I,
        model.J,
        model.P,
        initialize=lambda mdl, i, j, p: params["transport_cost"][i][j][p],
    )
    model.shipping_capacity = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: params["shipping_capacity"][i][j],
    )

    model.x = pyo.Var(model.I, model.J, model.P, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i, p):
        return sum(mdl.x[i, j, p] for j in mdl.J) <= mdl.supply[i, p]

    model.supply_limit = pyo.Constraint(model.I, model.P, rule=supply_rule)

    def demand_rule(mdl, j, p):
        return sum(mdl.x[i, j, p] for i in mdl.I) == mdl.demand[j, p]

    model.demand_requirement = pyo.Constraint(
        model.J, model.P, rule=demand_rule
    )

    def capacity_rule(mdl, i, j):
        return (
            sum(mdl.x[i, j, p] for p in mdl.P)
            <= mdl.shipping_capacity[i, j]
        )

    model.route_capacity = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j, p] * model.x[i, j, p]
            for i in model.I
            for j in model.J
            for p in model.P
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