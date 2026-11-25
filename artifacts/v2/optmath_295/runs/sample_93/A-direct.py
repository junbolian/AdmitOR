import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    num_participants = len(preferences)
    num_cars = len(preferences[0]) if num_participants > 0 else 0

    participants = list(range(num_participants))
    cars = list(range(num_cars))
    eligible = [(p, c) for p in participants for c in cars if preferences[p][c] == 1]

    model = pyo.ConcreteModel()

    if eligible:
        model.x = pyo.Var(eligible, domain=pyo.Binary)
    else:
        model.x = pyo.Var([], domain=pyo.Binary)

    def participant_rule(m, p):
        expr = sum(m.x[p, c] for c in cars if (p, c) in m.x)
        return pyo.Constraint.Skip if expr is None else expr <= participant_capacity

    def car_rule(m, c):
        expr = sum(m.x[p, c] for p in participants if (p, c) in m.x)
        return expr <= car_capacity

    model.participant_constraint = pyo.Constraint(participants, rule=participant_rule)
    model.car_constraint = pyo.Constraint(cars, rule=car_rule)

    if eligible:
        model.obj = pyo.Objective(
            expr=sum(model.x[p, c] for (p, c) in eligible),
            sense=pyo.maximize,
        )
    else:
        model.obj = pyo.Objective(expr=0.0, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}