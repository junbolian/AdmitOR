# IR: {"sets":{"P":"range(params['participant_count'])","C":"range(params['car_count'])"},"params":{"participant_count":"participant index-set size","car_count":"car index-set size","preference[p,c]":"params[f'preference_p{p}_car{c}'] for p in P, c in C"},"variables":{"x[p,c]":"binary, for p in P, c in C"},"constraints":["sum(x[p,c] for c in C) <= 1 for each p in P","sum(x[p,c] for p in P) <= 1 for each c in C","x[p,c] <= preference[p,c] for each (p,c) in P x C"],"objective":"maximize sum(x[p,c] for p in P, c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_count = params["participant_count"]
    car_count = params["car_count"]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=range(participant_count), ordered=True)
    model.C = pyo.Set(initialize=range(car_count), ordered=True)

    model.preference = pyo.Param(
        model.P,
        model.C,
        initialize={
            (participant, car): params[f"preference_p{participant}_car{car}"]
            for participant in model.P
            for car in model.C
        },
        within=pyo.Binary,
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def participant_limit_rule(instance, participant):
        if not len(instance.C):
            return pyo.Constraint.Feasible
        return sum(instance.x[participant, car] for car in instance.C) <= 1

    model.participant_limit = pyo.Constraint(
        model.P, rule=participant_limit_rule
    )

    def car_limit_rule(instance, car):
        if not len(instance.P):
            return pyo.Constraint.Feasible
        return sum(instance.x[participant, car] for participant in instance.P) <= 1

    model.car_limit = pyo.Constraint(model.C, rule=car_limit_rule)

    def preference_limit_rule(instance, participant, car):
        return instance.x[participant, car] <= instance.preference[participant, car]

    model.preference_limit = pyo.Constraint(
        model.P, model.C, rule=preference_limit_rule
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
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
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}