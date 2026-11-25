import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    participants = [0, 1, 2, 3, 4]
    cars = [0, 1, 2, 3, 4]

    pref = {
        (0, 0): params["pref_p0_c0"],
        (0, 1): params["pref_p0_c1"],
        (1, 4): params["pref_p1_c4"],
        (4, 0): params["pref_p4_c0"],
        (4, 2): params["pref_p4_c2"],
    }

    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.PC = pyo.Set(initialize=list(pref.keys()), dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[p, c] for (p, c) in m.PC)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        terms = [m.x[pp, c] for (pp, c) in m.PC if pp == p]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= participant_capacity

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        terms = [m.x[p, cc] for (p, cc) in m.PC if cc == c]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= car_capacity

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}