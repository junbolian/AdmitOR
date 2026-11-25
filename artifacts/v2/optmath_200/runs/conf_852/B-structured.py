# IR: {"sets":{"participants":[0,1,2,3,4,5,6],"cars":[0,1,2,3,4,5,6,7],"valid_pairs":[[0,1],[0,6],[0,7],[1,3],[2,1],[2,2],[2,4],[3,0],[4,2],[4,4],[4,5],[6,0],[6,1],[6,2],[6,3],[6,5]]},"params":{"objective_coefficient":"params['objective_coefficient']"},"variables":{"assignment[p,c]":"binary for (p,c) in valid_pairs"},"constraints":["For each participant p: sum(assignment[p,c] for valid (p,c)) <= 1","For each car c: sum(assignment[p,c] for valid (p,c)) <= 1"],"objective":"maximize objective_coefficient * sum(assignment[p,c] for (p,c) in valid_pairs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 6)
    model.cars = pyo.RangeSet(0, 7)
    model.valid_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (0, 1), (0, 6), (0, 7),
            (1, 3),
            (2, 1), (2, 2), (2, 4),
            (3, 0),
            (4, 2), (4, 4), (4, 5),
            (6, 0), (6, 1), (6, 2), (6, 3), (6, 5),
        ],
    )
    model.objective_coefficient = pyo.Param(
        initialize=params["objective_coefficient"],
        within=pyo.Reals,
    )
    model.assignment = pyo.Var(model.valid_pairs, domain=pyo.Binary)

    def participant_limit_rule(instance, participant):
        eligible_cars = [
            car for person, car in instance.valid_pairs
            if person == participant
        ]
        if not eligible_cars:
            return pyo.Constraint.Feasible
        return sum(
            instance.assignment[participant, car] for car in eligible_cars
        ) <= 1

    def car_limit_rule(instance, car):
        eligible_participants = [
            participant for participant, vehicle in instance.valid_pairs
            if vehicle == car
        ]
        if not eligible_participants:
            return pyo.Constraint.Feasible
        return sum(
            instance.assignment[participant, car]
            for participant in eligible_participants
        ) <= 1

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )
    model.car_limit = pyo.Constraint(model.cars, rule=car_limit_rule)

    model.total_value = pyo.Objective(
        expr=model.objective_coefficient * sum(
            model.assignment[participant, car]
            for participant, car in model.valid_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}