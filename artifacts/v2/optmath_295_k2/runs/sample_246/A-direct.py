import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_value = params["assignment_value"]

    participants = ["participant_0", "participant_1", "participant_2", "participant_3"]
    cars = ["car_0", "car_1", "car_2", "car_3", "car_4"]

    preference = {
        "participant_0": ["car_2", "car_4"],
        "participant_1": [],
        "participant_2": ["car_0", "car_4"],
        "participant_3": ["car_0", "car_4"],
    }

    allowed_pairs = [
        (p, c) for p in participants for c in cars if c in preference[p]
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.AC = pyo.Set(initialize=allowed_pairs, dimen=2)

    model.x = pyo.Var(model.AC, domain=pyo.Binary)

    def obj_rule(m):
        return assignment_value * sum(m.x[p, c] for (p, c) in m.AC)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        pairs = [(pp, c) for (pp, c) in m.AC if pp == p]
        if not pairs:
            return pyo.Constraint.Skip
        return sum(m.x[pp, c] for (pp, c) in pairs) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        pairs = [(p, cc) for (p, cc) in m.AC if cc == c]
        if not pairs:
            return pyo.Constraint.Skip
        return sum(m.x[p, cc] for (p, cc) in pairs) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}