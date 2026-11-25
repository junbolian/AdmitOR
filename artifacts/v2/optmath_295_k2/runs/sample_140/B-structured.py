# IR: {"sets":{"P":"range(params['num_participants'])","C":"range(params['num_cars'])"},"params":{"assignment_value":"params['assignment_value']","preference_p0_c5":"params['preference_p0_c5']","preference_p1_c2":"params['preference_p1_c2']","preference_p1_c3":"params['preference_p1_c3']","preference_p2_c4":"params['preference_p2_c4']","preference_p3_any":"params['preference_p3_any']","preference_p4_any":"params['preference_p4_any']","preference_p5_any":"params['preference_p5_any']","num_participants":"params['num_participants']","num_cars":"params['num_cars']"},"derived":{"preference[p,c]":"specified preference for (0,5),(1,2),(1,3),(2,4); preference_p3_any, preference_p4_any, preference_p5_any for rows 3,4,5 respectively; zero otherwise"},"variables":{"assignment[p,c]":"Binary"},"constraints":["sum(c in C, assignment[p,c]) <= 1 for p in P","sum(p in P, assignment[p,c]) <= 1 for c in C","assignment[p,c] <= preference[p,c] for (p,c) in P x C"],"objective":"maximize assignment_value * sum((p,c) in P x C, assignment[p,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]

    specified_preferences = {
        (0, 5): params["preference_p0_c5"],
        (1, 2): params["preference_p1_c2"],
        (1, 3): params["preference_p1_c3"],
        (2, 4): params["preference_p2_c4"],
    }
    uniform_preferences = {
        3: params["preference_p3_any"],
        4: params["preference_p4_any"],
        5: params["preference_p5_any"],
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.assignment_value = pyo.Param(
        initialize=params["assignment_value"],
        within=pyo.Reals,
    )

    def preference_rule(instance, participant, car):
        if participant in uniform_preferences:
            return uniform_preferences[participant]
        return specified_preferences.get((participant, car), 0)

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

    def participant_limit_rule(instance, participant):
        return (
            sum(
                instance.assignment[participant, car]
                for car in instance.cars
            )
            <= 1
        )

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(instance, car):
        return (
            sum(
                instance.assignment[participant, car]
                for participant in instance.participants
            )
            <= 1
        )

    model.car_limit = pyo.Constraint(model.cars, rule=car_limit_rule)

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
    except RuntimeError as error:
        # HiGHS may raise before loading values when no solution exists.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}