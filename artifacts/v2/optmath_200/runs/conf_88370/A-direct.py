import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])

    pref = []
    for p in range(num_participants):
        pref.append(list(params["preference_" + str(p)]))

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)

    def _bounds(m, p, c):
        return (0, int(pref[p][c]))

    model.x = pyo.Var(model.P, model.C, bounds=_bounds, within=pyo.Binary)

    model.participant_limit = pyo.Constraint(
        model.P, rule=lambda m, p: sum(m.x[p, c] for c in m.C) <= 1
    )
    model.car_limit = pyo.Constraint(
        model.C, rule=lambda m, c: sum(m.x[p, c] for p in m.P) <= 1
    )

    model.total = pyo.Objective(
        expr=sum(model.x[p, c] for p in model.P for c in model.C),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total))
    return {"objective": obj_val, "status": "optimal"}