# IR: {"sets":{"participants":"0..7","cars":"0..7"},"params":{"preference_matrix":"binary[8][8]","participant_capacity":"nonnegative scalar or length-8 array indexed by participant","car_capacity":"nonnegative scalar or length-8 array indexed by car"},"variables":{"assignment[participant,car]":"Binary"},"constraints":["assignment[participant,car] <= preference_matrix[participant][car] for every participant,car","sum(assignment[participant,car] for car) <= participant_capacity[participant] for every participant (broadcast scalar capacity)","sum(assignment[participant,car] for participant) <= car_capacity[car] for every car (broadcast scalar capacity)"],"objective":"maximize sum(assignment[participant,car] for every participant,car)"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    def capacity_at(capacity, position):
        if isinstance(capacity, Number):
            return capacity
        return capacity[position]

    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 7)
    model.cars = pyo.RangeSet(0, 7)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, participant, car: preference_matrix[participant][car],
        within=pyo.Binary,
    )
    model.participant_limit = pyo.Param(
        model.participants,
        initialize=lambda mdl, participant: capacity_at(
            participant_capacity, participant
        ),
        within=pyo.NonNegativeReals,
    )
    model.car_limit = pyo.Param(
        model.cars,
        initialize=lambda mdl, car: capacity_at(car_capacity, car),
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(mdl, participant, car):
        return mdl.assignment[participant, car] <= mdl.preference[participant, car]

    model.preference_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_capacity_rule(mdl, participant):
        return (
            sum(mdl.assignment[participant, car] for car in mdl.cars)
            <= mdl.participant_limit[participant]
        )

    model.participant_constraints = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(mdl, car):
        return (
            sum(
                mdl.assignment[participant, car]
                for participant in mdl.participants
            )
            <= mdl.car_limit[car]
        )

    model.car_constraints = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
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