import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]

    participants = sorted(preferences.keys())
    assignments = [(p, c) for p in participants for c in preferences[p]]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.A = pyo.Set(initialize=assignments, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[a] for a in m.A)

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        return sum(m.x[p, c] for c in preferences[p] if (p, c) in m.A) <= 1

    model.participant_limit = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        return sum(m.x[p, c] for p in participants if (p, c) in m.A) <= 1

    model.car_limit = pyo.Constraint(participants, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))

    return {"objective": obj_val, "status": "optimal"}