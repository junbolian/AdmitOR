# IR: {"sets":{"P":"range(num_participants)","C":"range(num_cars)"},"params":["assignment_value","preference_p0_c5","preference_p1_c2","preference_p1_c3","preference_p2_c4","preference_p3_any","preference_p4_any","preference_p5_any","num_participants","num_cars"],"derived":{"preference[p,c]":"preference_p0_c5 at (0,5); preference_p1_c2 at (1,2); preference_p1_c3 at (1,3); preference_p2_c4 at (2,4); preference_p3_any for p=3; preference_p4_any for p=4; preference_p5_any for p=5; otherwise 0"},"variables":{"x[p,c]":"binary"},"constraints":["For each p: sum(c in C, x[p,c]) <= 1","For each c: sum(p in P, x[p,c]) <= 1","For each (p,c): x[p,c] <= preference[p,c]"],"objective":"maximize assignment_value * sum(p in P, c in C, x[p,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_value = params["assignment_value"]
    preference_p0_c5 = params["preference_p0_c5"]
    preference_p1_c2 = params["preference_p1_c2"]
    preference_p1_c3 = params["preference_p1_c3"]
    preference_p2_c4 = params["preference_p2_c4"]
    preference_p3_any = params["preference_p3_any"]
    preference_p4_any = params["preference_p4_any"]
    preference_p5_any = params["preference_p5_any"]
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]

    pair_preferences = {
        (0, 5): preference_p0_c5,
        (1, 2): preference_p1_c2,
        (1, 3): preference_p1_c3,
        (2, 4): preference_p2_c4,
    }
    participant_preferences = {
        3: preference_p3_any,
        4: preference_p4_any,
        5: preference_p5_any,
    }

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=range(num_participants), ordered=True)
    model.C = pyo.Set(initialize=range(num_cars), ordered=True)

    model.assignment_weight = pyo.Param(
        initialize=assignment_value,
        within=pyo.Reals,
    )

    def preference_rule(instance, participant, car):
        if participant in participant_preferences:
            return participant_preferences[participant]
        return pair_preferences.get((participant, car), 0)

    model.preference = pyo.Param(
        model.P,
        model.C,
        initialize=preference_rule,
        within=pyo.Binary,
    )
    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def participant_limit_rule(instance, participant):
        return sum(
            instance.x[participant, car] for car in instance.C
        ) <= 1

    model.participant_limit = pyo.Constraint(
        model.P,
        rule=participant_limit_rule,
    )

    def car_limit_rule(instance, car):
        return sum(
            instance.x[participant, car] for participant in instance.P
        ) <= 1

    model.car_limit = pyo.Constraint(
        model.C,
        rule=car_limit_rule,
    )

    def preference_limit_rule(instance, participant, car):
        return (
            instance.x[participant, car]
            <= instance.preference[participant, car]
        )

    model.preference_limit = pyo.Constraint(
        model.P,
        model.C,
        rule=preference_limit_rule,
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_weight
        * sum(
            model.x[participant, car]
            for participant in model.P
            for car in model.C
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
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}