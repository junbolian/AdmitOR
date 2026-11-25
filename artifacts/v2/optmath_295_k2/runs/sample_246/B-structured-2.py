# IR: {"sets":{"participants":["participant_0","participant_1","participant_2","participant_3"],"cars":["car_0","car_1","car_2","car_3","car_4"],"preferred_pairs":[["participant_0","car_2"],["participant_0","car_4"],["participant_2","car_0"],["participant_2","car_4"],["participant_3","car_0"],["participant_3","car_4"]]},"params":{"assignment_value":"real, read from params","preference[p,c]":"binary structural constant: 1 for preferred_pairs, otherwise 0"},"variables":{"assignment[p,c]":"binary"},"constraints":["assignment[p,c] <= preference[p,c] for every participant and car","sum_c assignment[p,c] <= 1 for every participant","sum_p assignment[p,c] <= 1 for every car"],"objective":"maximize assignment_value * sum_{p,c} assignment[p,c]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=[
            "participant_0",
            "participant_1",
            "participant_2",
            "participant_3",
        ],
        ordered=True,
    )
    model.cars = pyo.Set(
        initialize=["car_0", "car_1", "car_2", "car_3", "car_4"],
        ordered=True,
    )

    preferred_pairs = {
        ("participant_0", "car_2"),
        ("participant_0", "car_4"),
        ("participant_2", "car_0"),
        ("participant_2", "car_4"),
        ("participant_3", "car_0"),
        ("participant_3", "car_4"),
    }

    model.assignment_value = pyo.Param(
        initialize=params["assignment_value"],
        within=pyo.Reals,
    )
    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): int((participant, car) in preferred_pairs)
            for participant in model.participants
            for car in model.cars
        },
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(mdl, participant, car):
        return (
            mdl.assignment[participant, car]
            <= mdl.preference[participant, car]
        )

    model.preference_limit = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_capacity_rule(mdl, participant):
        return sum(
            mdl.assignment[participant, car] for car in mdl.cars
        ) <= 1

    model.participant_capacity = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(mdl, car):
        return sum(
            mdl.assignment[participant, car]
            for participant in mdl.participants
        ) <= 1

    model.car_capacity = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    model.total_value = pyo.Objective(
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
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}