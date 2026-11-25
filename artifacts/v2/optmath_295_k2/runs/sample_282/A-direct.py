import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_participants = int(params["participant_count"])
    n_cars = int(params["car_count"])

    participants = range(n_participants)
    cars = range(n_cars)

    preference = {}
    for p in participants:
        for c in cars:
            preference[(p, c)] = float(params[f"preference_p{p}_car{c}"])

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(participants))
    model.C = pyo.Set(initialize=list(cars))

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Only allow assignments to preferred cars
    def prefer_rule(model, p, c):
        if preference[(p, c)] <= 0:
            return model.x[p, c] == 0
        return pyo.Constraint.Skip

    model.prefer_con = pyo.Constraint(model.P, model.C, rule=prefer_rule)

    # Each participant at most one car
    def participant_rule(model, p):
        return sum(model.x[p, c] for c in model.C) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    # Each car at most one participant
    def car_rule(model, c):
        return sum(model.x[p, c] for p in model.P) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for p in model.P for c in model.C),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}