import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participants = list(range(6))
    cars = list(range(7))

    prefs = {}
    for p in participants:
        for c in cars:
            key = "preference_%d_%d" % (p, c)
            if key in params:
                prefs[(p, c)] = params[key]

    allowed = [(p, c) for (p, c) in prefs if prefs[(p, c)] >= 0.5]

    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.AC = pyo.Set(dimen=2, initialize=allowed)

    model.x = pyo.Var(model.AC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[p, c] for (p, c) in m.AC)

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_limit(m, p):
        pairs = [(p, c) for c in m.C if (p, c) in m.AC]
        if not pairs:
            return pyo.Constraint.Feasible
        return sum(m.x[p, c] for (p, c) in pairs) <= participant_capacity

    model.participant_limit = pyo.Constraint(model.P, rule=participant_limit)

    def car_limit(m, c):
        pairs = [(p, c) for p in m.P if (p, c) in m.AC]
        if not pairs:
            return pyo.Constraint.Feasible
        return sum(m.x[p, c] for (p, c) in pairs) <= car_capacity

    model.car_limit = pyo.Constraint(model.C, rule=car_limit)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}