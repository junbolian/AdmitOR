import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    num_participants = len(preference)
    num_cars = len(preference[0])

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    allowed_pairs = {
        i: [j for j in cars if preference[i][j] == 1] for i in participants
    }

    model = pyo.ConcreteModel()
    model.x = pyo.Var(
        [(i, j) for i in participants for j in allowed_pairs[i]],
        domain=pyo.Binary,
    )

    model.obj = pyo.Objective(
        expr=sum(
            assignment_value * model.x[i, j]
            for i in participants
            for j in allowed_pairs[i]
        ),
        sense=pyo.maximize,
    )

    def participant_rule(m, i):
        return sum(m.x[i, j] for j in allowed_pairs[i]) <= participant_capacity

    model.participant_limit = pyo.Constraint(participants, rule=participant_rule)

    def car_rule(m, j):
        return sum(
            m.x[i, j] for i in participants if j in allowed_pairs[i]
        ) <= car_capacity

    model.car_limit = pyo.Constraint(cars, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}