# IR: {"sets":{"participants":[0,1,2,3,4,5],"cars":[0,1,2,3,4,5]},"params":{"preference_matrix":"binary[participants,cars], read from params","unit_assignment_value":"real scalar, read from params"},"variables":{"assignment[p,c]":"binary"},"constraints":["sum(c,assignment[p,c]) <= 1 for each participant p","sum(p,assignment[p,c]) <= 1 for each car c","assignment[p,c] <= preference_matrix[p,c] for each participant p and car c"],"objective":"maximize unit_assignment_value * sum(p,c,assignment[p,c])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    unit_assignment_value = params["unit_assignment_value"]

    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 5)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): preference_matrix[participant][car]
            for participant in model.participants
            for car in model.cars
        },
        within=pyo.Binary,
    )
    model.assignment_value = pyo.Param(
        initialize=unit_assignment_value,
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_limit_rule(mdl, participant):
        return sum(
            mdl.assignment[participant, car] for car in mdl.cars
        ) <= 1

    model.participant_limit = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(mdl, car):
        return sum(
            mdl.assignment[participant, car]
            for participant in mdl.participants
        ) <= 1

    model.car_limit = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    def eligibility_rule(mdl, participant, car):
        return (
            mdl.assignment[participant, car]
            <= mdl.preference[participant, car]
        )

    model.eligibility = pyo.Constraint(
        model.participants,
        model.cars,
        rule=eligibility_rule,
    )

    model.total_assignment_value = pyo.Objective(
        expr=model.assignment_value
        * sum(
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
        obj_val = float(pyo.value(model.total_assignment_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}