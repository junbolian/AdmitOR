import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]

    P = list(range(6))
    C = list(range(7))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=P)
    model.C = pyo.Set(initialize=C)
    model.PC = pyo.Set(initialize=[(p, c) for p in P for c in C])

    model.x = pyo.Var(model.PC, domain=pyo.Binary)

    # Each participant assigned to at most one car
    def participant_rule(m, p):
        return sum(m.x[p, c] for c in C) <= 1

    model.participant_limit = pyo.Constraint(model.P, rule=participant_rule)

    # Each car assigned to at most one participant
    def car_rule(m, c):
        return sum(m.x[p, c] for p in P) <= 1

    model.car_limit = pyo.Constraint(model.C, rule=car_rule)

    # Only allow assignments where participant is interested
    def interest_rule(m, p, c):
        if preference[p][c] == 0:
            return m.x[p, c] == 0
        return pyo.Constraint.Skip

    model.interest = pyo.Constraint(model.PC, rule=interest_rule)

    def obj_rule(m):
        return sum(m.x[p, c] for p in P for c in C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}