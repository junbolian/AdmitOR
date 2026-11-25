import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    n_participants = params["n_participants"]
    n_cars = params["n_cars"]
    objective_coeff = params["objective_coeff"]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_participants - 1)
    model.C = pyo.RangeSet(0, n_cars - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return objective_coeff * sum(
            preference[p][c] * m.x[p, c]
            for p in m.P
            for c in m.C
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= participant_capacity[p]

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        return sum(m.x[p, c] for p in m.P) <= car_capacity[c]

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    def pref_rule(m, p, c):
        if preference[p][c] == 1:
            return pyo.Constraint.Skip
        return m.x[p, c] == 0

    model.pref_con = pyo.Constraint(model.P, model.C, rule=pref_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}