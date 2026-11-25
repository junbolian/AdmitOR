# IR: {"sets":{"I":"0..28","J":"0..9","N[i]":"{j in J: distance_matrix[i][j] <= coverage_radius}"},"params":{"demand":"params['demand'][i], nonnegative","coverage_radius":"params['coverage_radius'], nonnegative","num_stations":"params['num_stations'], nonnegative integer","distance_matrix":"params['distance_matrix'][i][j], nonnegative"},"variables":{"x[j]":"binary; station j activated","y[i]":"binary; center i covered"},"constraints":["sum(x[j] for j in J) == num_stations","y[i] <= sum(x[j] for j in N[i]) for each i in I","y[i] >= x[j] for each i in I and j in N[i]"],"objective":"maximize sum(demand[i]*y[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    coverage_radius = params["coverage_radius"]
    num_stations = params["num_stations"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 28)
    model.J = pyo.RangeSet(0, 9)

    model.demand = pyo.Param(
        model.I,
        initialize=lambda mdl, i: demand[i],
        within=pyo.NonNegativeReals,
    )
    model.coverage_radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.num_stations = pyo.Param(
        initialize=num_stations,
        within=pyo.NonNegativeIntegers,
    )
    model.distance_matrix = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.N = pyo.Set(
        model.I,
        within=model.J,
        initialize=lambda mdl, i: [
            j
            for j in mdl.J
            if pyo.value(mdl.distance_matrix[i, j])
            <= pyo.value(mdl.coverage_radius)
        ],
    )
    model.coverage_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.I
            for j in model.N[i]
        ],
    )

    model.x = pyo.Var(model.J, domain=pyo.Binary)
    model.y = pyo.Var(model.I, domain=pyo.Binary)

    model.station_count = pyo.Constraint(
        expr=sum(model.x[j] for j in model.J) == model.num_stations
    )

    def coverage_upper_rule(mdl, i):
        return mdl.y[i] <= sum(mdl.x[j] for j in mdl.N[i])

    model.coverage_upper = pyo.Constraint(
        model.I,
        rule=coverage_upper_rule,
    )

    def coverage_lower_rule(mdl, i, j):
        return mdl.y[i] >= mdl.x[j]

    model.coverage_lower = pyo.Constraint(
        model.coverage_pairs,
        rule=coverage_lower_rule,
    )

    model.total_covered_demand = pyo.Objective(
        expr=sum(model.demand[i] * model.y[i] for i in model.I),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_covered_demand))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}