# IR: {"sets":{"P":"range(params['num_participants'])","C":"range(params['num_cars'])"},"params":{"num_participants":"participant count","num_cars":"car count","preference_p0":"allowed cars for participant 0","preference_p1":"allowed cars for participant 1","preference_p2":"allowed cars for participant 2","preference_p3":"allowed cars for participant 3","preference_p4":"allowed cars for participant 4","preference_p5":"allowed cars for participant 5","preference_p6":"allowed cars for participant 6","preference_p7":"allowed cars for participant 7"},"variables":{"assignment[p,c]":"Binary for (p,c) in P x C"},"constraints":["For each p in P: sum(assignment[p,c] for c in C) <= 1","For each c in C: sum(assignment[p,c] for p in P) <= 1","For each (p,c) in P x C: assignment[p,c] <= indicator(c in preference[p])"],"objective":"maximize sum(assignment[p,c] for (p,c) in P x C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]

    preferences = {
        0: set(params["preference_p0"]),
        1: set(params["preference_p1"]),
        2: set(params["preference_p2"]),
        3: set(params["preference_p3"]),
        4: set(params["preference_p4"]),
        5: set(params["preference_p5"]),
        6: set(params["preference_p6"]),
        7: set(params["preference_p7"]),
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def participant_limit_rule(instance, participant):
        return (
            None,
            pyo.quicksum(
                instance.assignment[participant, car]
                for car in instance.cars
            ),
            1,
        )

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(instance, car):
        return (
            None,
            pyo.quicksum(
                instance.assignment[participant, car]
                for participant in instance.participants
            ),
            1,
        )

    model.car_limit = pyo.Constraint(
        model.cars, rule=car_limit_rule
    )

    def preference_limit_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= int(car in preferences[participant])
        )

    model.preference_limit = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_limit_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
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