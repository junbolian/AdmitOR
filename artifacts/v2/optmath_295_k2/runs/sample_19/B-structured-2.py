# IR: {"sets":{"P":"range(num_participants)","C":"range(num_cars)"},"params":["num_participants","num_cars","preference_p0","preference_p1","preference_p2","preference_p3","preference_p4","preference_p5","preference_p6","preference_p7"],"variables":{"x[p,c]":"binary for (p,c) in P x C"},"constraints":["sum(x[p,c] for c in C) <= 1 for each p in P","sum(x[p,c] for p in P) <= 1 for each c in C","x[p,c] <= indicator(c in preference_p[p]) for each (p,c) in P x C"],"objective":"maximize sum(x[p,c] for (p,c) in P x C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preference_lists = (
        params["preference_p0"],
        params["preference_p1"],
        params["preference_p2"],
        params["preference_p3"],
        params["preference_p4"],
        params["preference_p5"],
        params["preference_p6"],
        params["preference_p7"],
    )
    preferences = {
        participant: set(preference_lists[participant])
        for participant in range(num_participants)
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.x = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_rule(current_model, participant):
        return (
            None,
            pyo.quicksum(
                current_model.x[participant, car]
                for car in current_model.cars
            ),
            1,
        )

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_rule
    )

    def car_rule(current_model, car):
        return (
            None,
            pyo.quicksum(
                current_model.x[participant, car]
                for participant in current_model.participants
            ),
            1,
        )

    model.car_limits = pyo.Constraint(model.cars, rule=car_rule)

    def preference_rule(current_model, participant, car):
        return current_model.x[participant, car] <= int(
            car in preferences[participant]
        )

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.x[participant, car]
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}