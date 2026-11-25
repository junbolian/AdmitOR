# IR: {"sets":{"P":"range(params['participant_count'])","C":"range(params['car_count'])"},"params":{"participant_count":"participant index-set size","car_count":"car index-set size","preference[p,c]":"params[f'preference_p{p}_car{c}'] for p in P, c in C"},"variables":{"assignment[p,c]":"binary"},"constraints":["sum(assignment[p,c] for c in C) <= 1 for each p in P","sum(assignment[p,c] for p in P) <= 1 for each c in C","assignment[p,c] <= preference[p,c] for each (p,c) in P x C"],"objective":"maximize sum(assignment[p,c] for (p,c) in P x C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_count = params["participant_count"]
    car_count = params["car_count"]

    model = pyo.ConcreteModel()
    model.participants = pyo.Set(
        initialize=range(participant_count), ordered=True
    )
    model.cars = pyo.Set(initialize=range(car_count), ordered=True)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): params[f"preference_p{participant}_car{car}"]
            for participant in model.participants
            for car in model.cars
        },
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def participant_limit_rule(instance, participant):
        return (
            pyo.quicksum(
                instance.assignment[participant, car] for car in instance.cars
            )
            <= 1
        )

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(instance, car):
        return (
            pyo.quicksum(
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
        model.participants, model.cars, rule=preference_limit_rule
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