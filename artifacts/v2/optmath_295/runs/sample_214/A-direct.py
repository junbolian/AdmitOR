import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participants = list(range(6))
    cars = list(range(7))

    pref = {}
    pref[(0, 0)] = params["pref_0_0"]
    pref[(0, 6)] = params["pref_0_6"]
    pref[(1, 5)] = params["pref_1_5"]
    pref[(2, 3)] = params["pref_2_3"]
    pref[(2, 6)] = params["pref_2_6"]
    pref[(3, 3)] = params["pref_3_3"]
    pref[(3, 6)] = params["pref_3_6"]
    pref[(4, 1)] = params["pref_4_1"]
    pref[(4, 2)] = params["pref_4_2"]
    pref[(4, 3)] = params["pref_4_3"]
    pref[(5, 1)] = params["pref_5_1"]
    pref[(5, 2)] = params["pref_5_2"]
    pref[(5, 4)] = params["pref_5_4"]
    pref[(5, 5)] = params["pref_5_5"]

    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    allowed = [(p, c) for (p, c), v in pref.items() if v == 1]

    model = pyo.ConcreteModel()

    model.assign = pyo.Var(allowed, domain=pyo.Binary)

    def obj_rule(m):
        return assignment_value * sum(m.assign[p, c] for (p, c) in allowed)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.participant_limit = pyo.ConstraintList()
    for p in participants:
        model.participant_limit.add(
            sum(model.assign[p, c] for (pp, c) in allowed if pp == p)
            <= participant_capacity
        )

    model.car_limit = pyo.ConstraintList()
    for c in cars:
        model.car_limit.add(
            sum(model.assign[p, cc] for (p, cc) in allowed if cc == c)
            <= car_capacity
        )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}