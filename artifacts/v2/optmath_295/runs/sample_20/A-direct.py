import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participants = list(range(7))
    cars = list(range(7))

    prefs = {}
    for p in participants:
        prefs[p] = list(params[f"preference_P{p}"])

    allowed = [(p, c) for p in participants for c in cars if int(prefs[p][c]) == 1]

    model = pyo.ConcreteModel()

    if allowed:
        model.assign = pyo.Var(allowed, domain=pyo.Binary)
    else:
        model.assign = pyo.Var([], domain=pyo.Binary)

    def one_car_rule(m, p):
        terms = [m.assign[p, c] for (pp, c) in allowed if pp == p]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    def one_participant_rule(m, c):
        terms = [m.assign[p, cc] for (p, cc) in allowed if cc == c]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.one_car_per_participant = pyo.Constraint(participants, rule=one_car_rule)
    model.one_participant_per_car = pyo.Constraint(cars, rule=one_participant_rule)

    if allowed:
        model.obj = pyo.Objective(
            expr=sum(model.assign[p, c] for (p, c) in allowed),
            sense=pyo.maximize,
        )
    else:
        model.obj = pyo.Objective(expr=0, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}