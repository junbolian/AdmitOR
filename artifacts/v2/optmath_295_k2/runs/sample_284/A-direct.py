import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = 5
    num_cars = 4

    preferences = [
        [1, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 0],
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Preference constraints: cannot assign if not interested
    def pref_rule(m, p, c):
        return m.x[p, c] <= preferences[p][c]

    model.pref_con = pyo.Constraint(model.P, model.C, rule=pref_rule)

    # One car per participant
    def one_car_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= 1

    model.one_car_con = pyo.Constraint(model.P, rule=one_car_rule)

    # One participant per car
    def one_part_rule(m, c):
        return sum(m.x[p, c] for p in m.P) <= 1

    model.one_part_con = pyo.Constraint(model.C, rule=one_part_rule)

    # Objective: maximize total assignments
    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for p in model.P for c in model.C),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}