import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_participants = 7
    n_cars = 6
    participants = list(range(n_participants))
    cars = list(range(n_cars))

    prefs = {
        0: [2],
        1: [0],
        2: [0, 1],
        3: [1],
        4: [1],
        5: [],
        6: [3],
    }

    pairs = [(p, c) for p in participants for c in prefs[p]]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.PAIR_IDX = pyo.Set(initialize=list(range(len(pairs))), dimen=1)
    model.pair_list = pairs

    model.x = pyo.Var(model.PAIR_IDX, domain=pyo.Binary)

    # Objective: maximize number of assignments
    model.obj = pyo.Objective(
        expr=sum(model.x[i] for i in model.PAIR_IDX),
        sense=pyo.maximize,
    )

    pair_set = set(pairs)

    def participant_rule(m, p):
        idxs = [i for i, (pp, cc) in enumerate(m.pair_list) if pp == p]
        if not idxs:
            return pyo.Constraint.Feasible
        return sum(m.x[i] for i in idxs) <= 1

    def car_rule(m, c):
        idxs = [i for i, (pp, cc) in enumerate(m.pair_list) if cc == c]
        if not idxs:
            return pyo.Constraint.Feasible
        return sum(m.x[i] for i in idxs) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)
    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc)[:80] or "failed"}