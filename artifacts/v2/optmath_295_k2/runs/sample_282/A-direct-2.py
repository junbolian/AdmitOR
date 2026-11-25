import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    P = int(params["participant_count"])
    C = int(params["car_count"])

    pref = {}
    for p in range(P):
        for c in range(C):
            pref[(p, c)] = int(params["preference_p%d_car%d" % (p, c)])

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, P - 1)
    model.C = pyo.RangeSet(0, C - 1)
    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def assign_limit(m, p):
        return sum(m.x[p, c] for c in m.C) <= 1
    model.participant_limit = pyo.Constraint(model.P, rule=assign_limit)

    def car_limit(m, c):
        return sum(m.x[p, c] for p in m.P) <= 1
    model.car_limit = pyo.Constraint(model.C, rule=car_limit)

    def pref_only(m, p, c):
        if pref[(p, c)] == 0:
            return m.x[p, c] == 0
        return pyo.Constraint.Skip
    model.pref_con = pyo.Constraint(model.P, model.C, rule=pref_only)

    def obj_rule(m):
        return sum(pref[(p, c)] * m.x[p, c] for p in m.P for c in m.C)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}