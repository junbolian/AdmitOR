# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3,4]},"params":{"preference[p,c]":"params['preference_p{p}'][c], binary","participant_capacity[p]":"params['participant_{p}_capacity'], nonnegative","car_capacity[c]":"params['car_{c}_capacity'], nonnegative","assignment_weight":"params['objective_weight_per_assignment'], real"},"variables":{"assignment[p,c]":"binary"},"constraints":["assignment[p,c] <= preference[p,c] for all p,c","sum(assignment[p,c] for c in C) <= participant_capacity[p] for all p","sum(assignment[p,c] for p in P) <= car_capacity[c] for all c"],"objective":"maximize assignment_weight * sum(assignment[p,c] for p in P,c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = (
        params["preference_p0"],
        params["preference_p1"],
        params["preference_p2"],
        params["preference_p3"],
        params["preference_p4"],
    )
    participant_capacities = (
        params["participant_0_capacity"],
        params["participant_1_capacity"],
        params["participant_2_capacity"],
        params["participant_3_capacity"],
        params["participant_4_capacity"],
    )
    car_capacities = (
        params["car_0_capacity"],
        params["car_1_capacity"],
        params["car_2_capacity"],
        params["car_3_capacity"],
        params["car_4_capacity"],
    )

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 4)
    model.cars = pyo.RangeSet(0, 4)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): preferences[participant][car]
            for participant in model.participants
            for car in model.cars
        },
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        model.participants,
        initialize={
            participant: participant_capacities[participant]
            for participant in model.participants
        },
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        model.cars,
        initialize={car: car_capacities[car] for car in model.cars},
        within=pyo.NonNegativeReals,
    )
    model.assignment_weight = pyo.Param(
        initialize=params["objective_weight_per_assignment"],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def preference_rule(current_model, participant, car):
        return (
            current_model.assignment[participant, car]
            <= current_model.preference[participant, car]
        )

    def participant_capacity_rule(current_model, participant):
        return (
            sum(
                current_model.assignment[participant, car]
                for car in current_model.cars
            )
            <= current_model.participant_capacity[participant]
        )

    def car_capacity_rule(current_model, car):
        return (
            sum(
                current_model.assignment[participant, car]
                for participant in current_model.participants
            )
            <= current_model.car_capacity[car]
        )

    model.preference_limits = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
    )
    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )
    model.car_limits = pyo.Constraint(
        model.cars, rule=car_capacity_rule
    )

    model.total_gain = pyo.Objective(
        expr=model.assignment_weight
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
        obj_val = float(pyo.value(model.total_gain))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}