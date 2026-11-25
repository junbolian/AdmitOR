import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])

    prefs = []
    for i in range(num_participants):
        prefs.append(list(params["preference_p" + str(i)]))

    pairs = [(i, j) for i in range(num_participants) for j in prefs[i]]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)
    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[i, j] for (i, j) in pairs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, i):
        return sum(m.x[i, j] for j in prefs[i]) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, j):
        return sum(m.x[i, j] for i in range(num_participants) if j in prefs[i]) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}