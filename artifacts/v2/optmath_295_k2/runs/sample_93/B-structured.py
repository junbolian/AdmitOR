# IR: {"sets":{"participants":"0..7","cars":"0..6"},"params":{"preferences":"binary[participants,cars], read from params['preferences']"},"variables":{"x":"binary[participants,cars]"},"constraints":["x[i,j] <= preferences[i,j] for each participant i and car j","sum_j x[i,j] <= 1 for each participant i","sum_i x[i,j] <= 1 for each car j"],"objective":"maximize sum_i sum_j x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 7)
    model.cars = pyo.RangeSet(0, 6)

    model.preferences = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda model, i, j: preferences[i][j],
        within=pyo.Binary,
    )

    model.x = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda model, i, j: model.x[i, j] <= model.preferences[i, j],
    )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=lambda model, i: sum(
            model.x[i, j] for j in model.cars
        ) <= 1,
    )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=lambda model, j: sum(
            model.x[i, j] for i in model.participants
        ) <= 1,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.x[i, j]
            for i in model.participants
            for j in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}