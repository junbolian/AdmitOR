import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participants = ["participant_0", "participant_1", "participant_2", "participant_3"]
    cars = ["car_0", "car_1", "car_2", "car_3", "car_4"]

    interest = {
        ("participant_0", "car_2"): 1,
        ("participant_0", "car_4"): 1,
        ("participant_1", "car_0"): 0,
        ("participant_1", "car_1"): 0,
        ("participant_1", "car_2"): 0,
        ("participant_1", "car_3"): 0,
        ("participant_1", "car_4"): 0,
        ("participant_2", "car_0"): 1,
        ("participant_2", "car_4"): 1,
        ("participant_3", "car_0"): 1,
        ("participant_3", "car_4"): 1,
    }

    allowed = [(p, c) for p in participants for c in cars if interest.get((p, c), 0) == 1]
    allowed_set = set(allowed)

    # If no assignments are possible, the problem is trivially solved.
    if not allowed:
        return {"objective": 0.0, "status": "optimal"}

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.A = pyo.Set(initialize=allowed, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for (p, c) in model.A),
        sense=pyo.maximize,
    )

    def participant_rule(mdl, p):
        pairs = [(p, c) for c in cars if (p, c) in allowed_set]
        if not pairs:
            return pyo.Constraint.Skip
        return sum(mdl.x[p, c] for (p, c) in pairs) <= 1

    def car_rule(mdl, c):
        pairs = [(p, c) for p in participants if (p, c) in allowed_set]
        if not pairs:
            return pyo.Constraint.Skip
        return sum(mdl.x[p, c] for (p, c) in pairs) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)
    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}