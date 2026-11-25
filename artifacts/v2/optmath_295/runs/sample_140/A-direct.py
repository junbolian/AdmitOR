import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participants = [0, 1, 2, 3, 4, 5]
    cars = [0, 1, 2, 3, 4, 5]

    assignment_value = params["assignment_value"]

    allowed = []
    if params["pref_p0_c5"]:
        allowed.append((0, 5))
    if params["pref_p1_c2"]:
        allowed.append((1, 2))
    if params["pref_p1_c3"]:
        allowed.append((1, 3))
    if params["pref_p2_c4"]:
        allowed.append((2, 4))
    for p, key in [(3, "pref_zero_p3"), (4, "pref_zero_p4"), (5, "pref_zero_p5")]:
        if params[key]:
            for c in cars:
                allowed.append((p, c))

    model = pyo.ConcreteModel()
    model.allowed = pyo.Set(initialize=allowed, dimen=2)

    model.x = pyo.Var(model.allowed, domain=pyo.Binary)

    def obj_rule(mod):
        return assignment_value * sum(mod.x[a] for a in mod.allowed)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Track which participants/cars actually appear in the allowed set
    allowed_participants = set(p for (p, c) in allowed)
    allowed_cars = set(c for (p, c) in allowed)

    def participant_rule(mod, p):
        terms = [mod.x[p, c] for c in cars if (p, c) in mod.allowed]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    def car_rule(mod, c):
        terms = [mod.x[p, c] for p in participants if (p, c) in mod.allowed]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_constraint = pyo.Constraint(participants, rule=participant_rule)
    model.car_constraint = pyo.Constraint(cars, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}