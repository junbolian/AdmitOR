# IR: {"sets":{"participants":"0..5","cars":"0..6"},"params":{"preference":"binary matrix read from params['preference']"},"variables":{"assigned[i,j]":"binary for each participant i and car j"},"constraints":["For each participant i: sum_j assigned[i,j] <= 1","For each car j: sum_i assigned[i,j] <= 1","For each pair (i,j): assigned[i,j] <= preference[i,j]"],"objective":"maximize sum_i sum_j assigned[i,j]"}

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
        initialize={
            (i, j): preference[i][j]
            for i in model.participants
            for j in model.cars
        },
        within=pyo.Binary,
    )

    model.assigned = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_limit_rule(model, i):
        return sum(model.assigned[i, j] for j in model.cars) <= 1

    model.participant_limit = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(model, j):
        return sum(model.assigned[i, j] for i in model.participants) <= 1

    model.car_limit = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    def preference_limit_rule(model, i, j):
        return model.assigned[i, j] <= model.preference[i, j]

    model.preference_limit = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_limit_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assigned[i, j]
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