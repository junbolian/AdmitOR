# IR: {"sets":{"I":"0..5","J":"0..7"},"params":{"supply":"nonnegative real[I], from params['supply']","demand":"nonnegative real[J], from params['demand']","cost_matrix":"real[I,J], from params['cost_matrix']"},"variables":{"ship[i,j]":"nonnegative continuous, i in I, j in J"},"constraints":["sum(ship[i,j] for j in J) == supply[i], for each i in I","sum(ship[i,j] for i in I) == demand[j], for each j in J"],"objective":"minimize sum(cost_matrix[i,j] * ship[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.I,
        initialize={i: supply[i] for i in model.I},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: demand[j] for j in model.J},
        within=pyo.NonNegativeReals,
    )
    model.cost_matrix = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): cost_matrix[i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )

    model.ship = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.ship[i, j] for j in mdl.J) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.ship[i, j] for i in mdl.I) == mdl.demand[j]

    model.supply_constraints = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_constraints = pyo.Constraint(model.J, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_matrix[i, j] * model.ship[i, j]
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}