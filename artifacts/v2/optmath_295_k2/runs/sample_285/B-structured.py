# IR: {"sets":{"participants":"0..5","cars":"0..6"},"params":{"preference":"binary matrix from params['preference']"},"variables":{"assignment[i,j]":"binary"},"constraints":["sum_j assignment[i,j] <= 1 for each participant i","sum_i assignment[i,j] <= 1 for each car j","assignment[i,j] <= preference[i,j] for each participant i and car j"],"objective":"maximize sum_i sum_j assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 6)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, i, j: preference[i][j],
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    model.participant_limit = pyo.Constraint(
        model.participants,
        rule=lambda mdl, i: sum(
            mdl.assignment[i, j] for j in mdl.cars
        ) <= 1,
    )

    model.car_limit = pyo.Constraint(
        model.cars,
        rule=lambda mdl, j: sum(
            mdl.assignment[i, j] for i in mdl.participants
        ) <= 1,
    )

    model.preference_limit = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda mdl, i, j: (
            mdl.assignment[i, j] <= mdl.preference[i, j]
        ),
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[i, j]
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