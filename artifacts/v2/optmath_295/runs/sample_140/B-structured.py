# IR: {"sets":{"participants":[0,1,2,3,4,5],"cars":[0,1,2,3,4,5]},"params":{"assignment_value":"real","pref_p0_c5":"binary","pref_p1_c2":"binary","pref_p1_c3":"binary","pref_p2_c4":"binary","pref_zero_p3":"binary","pref_zero_p4":"binary","pref_zero_p5":"binary"},"derived":{"preference[p,c]":"pref_p0_c5 for (0,5); pref_p1_c2 for (1,2); pref_p1_c3 for (1,3); pref_p2_c4 for (2,4); pref_zero_p3 for p=3; pref_zero_p4 for p=4; pref_zero_p5 for p=5; 0 otherwise"},"variables":{"assignment[p,c]":"binary"},"constraints":["sum(c, assignment[p,c]) <= 1 for each participant p","sum(p, assignment[p,c]) <= 1 for each car c","assignment[p,c] <= preference[p,c] for every participant-car pair"],"objective":"maximize assignment_value * sum(p,c, assignment[p,c])"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 5)

    model.assignment_value = pyo.Param(
        initialize=params["assignment_value"],
        within=pyo.Reals,
    )

    preference_names = (
        "pref_p0_c5",
        "pref_p1_c2",
        "pref_p1_c3",
        "pref_p2_c4",
        "pref_zero_p3",
        "pref_zero_p4",
        "pref_zero_p5",
    )
    for parameter_name in preference_names:
        model.add_component(
            parameter_name,
            pyo.Param(
                initialize=params[parameter_name],
                within=pyo.Binary,
            ),
        )

    specific_preferences = {
        (0, 5): model.pref_p0_c5,
        (1, 2): model.pref_p1_c2,
        (1, 3): model.pref_p1_c3,
        (2, 4): model.pref_p2_c4,
    }
    participant_preferences = {
        3: model.pref_zero_p3,
        4: model.pref_zero_p4,
        5: model.pref_zero_p5,
    }

    def preference_rule(instance, participant, car):
        if participant in participant_preferences:
            return pyo.value(participant_preferences[participant])
        if (participant, car) in specific_preferences:
            return pyo.value(specific_preferences[participant, car])
        return 0

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=preference_rule,
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_capacity_rule(instance, participant):
        return sum(
            instance.assignment[participant, car]
            for car in instance.cars
        ) <= 1

    model.participant_capacity = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(instance, car):
        return sum(
            instance.assignment[participant, car]
            for participant in instance.participants
        ) <= 1

    model.car_capacity = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    def preference_limit_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.preference[participant, car]
        )

    model.preference_limit = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_limit_rule,
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_value * sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}