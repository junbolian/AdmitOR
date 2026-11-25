# IR: {"sets":{"aircraft":"0..5","routes":"0..5"},"params":{"availability":"params['availability'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"x[i,j]":"nonnegative integer"},"constraints":["For each aircraft i: sum_j x[i,j] <= availability[i]","For each route j: sum_i capacity[i,j]*x[i,j] >= demand[j]"],"objective":"minimize sum_i sum_j cost[i,j]*x[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexable vectors and aircraft-by-route matrices in params."""
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, 5)
    model.routes = pyo.RangeSet(0, 5)

    model.availability = pyo.Param(
        model.aircraft,
        initialize={i: availability[i] for i in model.aircraft},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.routes,
        initialize={j: demand[j] for j in model.routes},
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.aircraft,
        model.routes,
        initialize={
            (i, j): cost[i][j]
            for i in model.aircraft
            for j in model.routes
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.aircraft,
        model.routes,
        initialize={
            (i, j): capacity[i][j]
            for i in model.aircraft
            for j in model.routes
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.aircraft,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.routes)
            <= mdl.availability[i]
        )

    model.availability_limits = pyo.Constraint(
        model.aircraft, rule=availability_rule
    )

    def demand_rule(mdl, j):
        return (
            sum(
                mdl.capacity[i, j] * mdl.x[i, j]
                for i in mdl.aircraft
            )
            >= mdl.demand[j]
        )

    model.route_coverage = pyo.Constraint(
        model.routes, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.aircraft
            for j in model.routes
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