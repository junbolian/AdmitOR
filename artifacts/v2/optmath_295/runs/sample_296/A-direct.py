import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]

    n_participants = len(preferences)
    n_cars = len(preferences[0])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_participants - 1)
    model.C = pyo.RangeSet(0, n_cars - 1)

    # x[p, c] = 1 if participant p is assigned to car c
    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Only allow assignments where participant is interested
    def _respect_prefs_rule(m, p, c):
        if preferences[p][c] == 0:
            return m.x[p, c] == 0
        return pyo.Constraint.Skip

    model.respect_prefs = pyo.Constraint(model.P, model.C, rule=_respect_prefs_rule)

    # Each participant at most one car
    def _one_car_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= 1

    model.one_car_per_participant = pyo.Constraint(model.P, rule=_one_car_rule)

    # Each car at most one participant
    def _one_participant_rule(m, c):
        return sum(m.x[p, c] for p in m.P) <= 1

    model.one_participant_per_car = pyo.Constraint(model.C, rule=_one_participant_rule)

    # Objective: maximize total assignments
    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for p in model.P for c in model.C),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}