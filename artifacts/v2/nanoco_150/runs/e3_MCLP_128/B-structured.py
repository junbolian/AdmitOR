# IR: {"sets":{"I":"0..20","J":"0..14","E":"{(i,j): travel_times[i][j] <= coverage_radius}"},"params":{"demands":"params['demands'], indexed by I, nonnegative","coverage_radius":"params['coverage_radius']","travel_times":"params['travel_times'], indexed by I x J"},"variables":{"x[j]":"binary; depot j activated","y[i]":"binary; community i served"},"constraints":["sum(x[j] for j in J) == 4","y[i] <= sum(x[j] for j with (i,j) in E), for each i in I","y[i] >= x[j], for each (i,j) in E"],"objective":"maximize sum(demands[i] * y[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    coverage_radius = params["coverage_radius"]
    travel_times = params["travel_times"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 20)
    model.J = pyo.RangeSet(0, 14)

    covering_depots = {
        i: tuple(
            j for j in model.J
            if travel_times[i][j] <= coverage_radius
        )
        for i in model.I
    }

    model.E = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.I
            for j in covering_depots[i]
        ],
    )

    model.demand_weight = pyo.Param(
        model.I,
        initialize={i: demands[i] for i in model.I},
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.J, domain=pyo.Binary)
    model.y = pyo.Var(model.I, domain=pyo.Binary)

    model.depot_limit = pyo.Constraint(
        expr=sum(model.x[j] for j in model.J) == 4
    )

    def coverage_upper_rule(model, i):
        return model.y[i] <= sum(
            model.x[j] for j in covering_depots[i]
        )

    model.coverage_upper = pyo.Constraint(
        model.I, rule=coverage_upper_rule
    )

    def coverage_lower_rule(model, i, j):
        return model.y[i] >= model.x[j]

    model.coverage_lower = pyo.Constraint(
        model.E, rule=coverage_lower_rule
    )

    model.total_served = pyo.Objective(
        expr=sum(
            model.demand_weight[i] * model.y[i]
            for i in model.I
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Other, unexpected runtime errors propagate to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_served))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}