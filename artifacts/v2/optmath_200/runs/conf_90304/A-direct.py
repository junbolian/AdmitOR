import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference = params["preference"]
    assignment_value = params["assignment_value"]

    n_participants = len(preference)
    n_cars = len(preference[0])

    participants = list(range(n_participants))
    cars = list(range(n_cars))

    feasible_pairs = [(p, c) for p in participants for c in cars if preference[p][c] == 1]

    model = pyo.ConcreteModel()

    model.ASSIGN = pyo.Var(feasible_pairs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(assignment_value * model.ASSIGN[p, c] for (p, c) in feasible_pairs),
        sense=pyo.maximize,
    )

    def participant_rule(m, p):
        return sum(m.ASSIGN[p, c] for c in cars if (p, c) in feasible_pairs) <= participant_capacity

    def car_rule(m, c):
        return sum(m.ASSIGN[p, c] for p in participants if (p, c) in feasible_pairs) <= car_capacity

    model.participant_limit = pyo.Constraint(participants, rule=participant_rule)
    model.car_limit = pyo.Constraint(cars, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}