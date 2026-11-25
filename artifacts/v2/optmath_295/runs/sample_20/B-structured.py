# IR: {"sets":{"P":[0,1,2,3,4,5,6],"C":[0,1,2,3,4,5,6]},"params":{"preference_P0":"binary[C]","preference_P1":"binary[C]","preference_P2":"binary[C]","preference_P3":"binary[C]","preference_P4":"binary[C]","preference_P5":"binary[C]","preference_P6":"binary[C]"},"variables":{"x[P,C]":"binary"},"constraints":["x[p,c] <= preference_Pp[c] for all p in P, c in C","sum(x[p,c] for c in C) <= 1 for all p in P","sum(x[p,c] for p in P) <= 1 for all c in C"],"objective":"maximize sum(x[p,c] for p in P, c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = {
        0: params["preference_P0"],
        1: params["preference_P1"],
        2: params["preference_P2"],
        3: params["preference_P3"],
        4: params["preference_P4"],
        5: params["preference_P5"],
        6: params["preference_P6"],
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 6)
    model.cars = pyo.RangeSet(0, 6)

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

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.preference[participant, car]
        )

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_rule(instance, participant):
        return sum(
            instance.assignment[participant, car] for car in instance.cars
        ) <= 1

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_rule,
    )

    def car_rule(instance, car):
        return sum(
            instance.assignment[participant, car]
            for participant in instance.participants
        ) <= 1

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_rule,
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}