import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]
    num_participants = len(preferences)
    num_cars = len(preferences[0])

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    allowed = [(i, j) for i in participants for j in cars if preferences[i][j] == 1]

    model = pyo.ConcreteModel()

    model.assign = pyo.Var(allowed, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.assign[i, j] for (i, j) in allowed),
        sense=pyo.maximize,
    )

    def participant_rule(m, i):
        terms = [m.assign[i, j] for j in cars if (i, j) in allowed]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= 1

    def car_rule(m, j):
        terms = [m.assign[i, j] for i in participants if (i, j) in allowed]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= 1

    model.each_participant = pyo.Constraint(participants, rule=participant_rule)
    model.each_car = pyo.Constraint(cars, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}