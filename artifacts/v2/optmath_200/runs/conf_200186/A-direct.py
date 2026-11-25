import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    n_participants = len(preference_matrix)
    n_cars = len(preference_matrix[0]) if n_participants > 0 else 0

    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, n_participants - 1)
    model.cars = pyo.RangeSet(0, n_cars - 1)

    model.assign = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    for p in model.participants:
        for c in model.cars:
            if preference_matrix[p][c] == 0:
                model.assign[p, c].fix(0)

    def participant_limit_rule(m, p):
        return sum(m.assign[p, c] for c in m.cars) <= participant_capacity

    def car_limit_rule(m, c):
        return sum(m.assign[p, c] for p in m.participants) <= car_capacity

    model.participant_limit = pyo.Constraint(model.participants, rule=participant_limit_rule)
    model.car_limit = pyo.Constraint(model.cars, rule=car_limit_rule)

    model.obj = pyo.Objective(
        expr=assignment_value
        * sum(model.assign[p, c] for p in model.participants for c in model.cars),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or solve failure"}