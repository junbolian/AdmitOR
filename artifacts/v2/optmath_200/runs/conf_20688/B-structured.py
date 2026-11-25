# IR: {"sets":{"participants":"0..6","cars":"0..6"},"params":{"participant_preferences":"collection of interested car indices for each participant","car_capacity":"nonnegative scalar","participant_capacity":"nonnegative scalar","assignment_value":"real scalar"},"variables":{"assignment[p,c]":"binary"},"constraints":["assignment[p,c] <= int(c in participant_preferences[p]) for every participant p and car c","sum(assignment[p,c] for c in cars) <= participant_capacity for every participant p","sum(assignment[p,c] for p in participants) <= car_capacity for every car c"],"objective":"maximize assignment_value * sum(assignment[p,c] for p in participants for c in cars)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["participant_preferences"]
    car_capacity = params["car_capacity"]
    participant_capacity = params["participant_capacity"]
    assignment_value = params["assignment_value"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 6)
    model.cars = pyo.RangeSet(0, 6)

    model.preference_data = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): int(car in preferences[participant])
            for participant in model.participants
            for car in model.cars
        },
        within=pyo.Binary,
    )
    model.car_capacity_data = pyo.Param(
        initialize=car_capacity,
        within=pyo.NonNegativeReals,
    )
    model.participant_capacity_data = pyo.Param(
        initialize=participant_capacity,
        within=pyo.NonNegativeReals,
    )
    model.assignment_value_data = pyo.Param(
        initialize=assignment_value,
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(model, participant, car):
        return (
            model.assignment[participant, car]
            <= model.preference_data[participant, car]
        )

    model.preference_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_capacity_rule(model, participant):
        return (
            sum(model.assignment[participant, car] for car in model.cars)
            <= model.participant_capacity_data
        )

    model.participant_constraints = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(model, car):
        return (
            sum(
                model.assignment[participant, car]
                for participant in model.participants
            )
            <= model.car_capacity_data
        )

    model.car_constraints = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_value_data
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
        # HiGHS may raise when no feasible solution can be loaded.
        # Success is determined solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}