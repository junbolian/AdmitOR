# IR: {"sets":{"participants":"0..5","cars":"0..6"},"params":{"preference":"binary matrix from params['preference']"},"variables":{"assignment[p,c]":"binary"},"constraints":["For each participant p: sum_c assignment[p,c] <= 1","For each car c: sum_p assignment[p,c] <= 1","For each participant p and car c: assignment[p,c] <= preference[p,c]"],"objective":"maximize sum_p sum_c assignment[p,c]"}

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
        initialize=lambda mdl, participant, car: preference[participant][car],
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def participant_limit_rule(mdl, participant):
        return sum(
            mdl.assignment[participant, car] for car in mdl.cars
        ) <= 1

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(mdl, car):
        return sum(
            mdl.assignment[participant, car]
            for participant in mdl.participants
        ) <= 1

    model.car_limit = pyo.Constraint(model.cars, rule=car_limit_rule)

    def preference_limit_rule(mdl, participant, car):
        return (
            mdl.assignment[participant, car]
            <= mdl.preference[participant, car]
        )

    model.preference_limit = pyo.Constraint(
        model.participants, model.cars, rule=preference_limit_rule
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}